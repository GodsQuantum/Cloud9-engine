#!/usr/bin/env python3
"""Cloud9 16K Qwen4B tournament: genuine CT410 production copy vs pinned Vulkan9ff/HIP9ff.

Read-only preflight is always the default. --execute explicitly enables
sequential, identical-GGUF/flags GPU tests with CT410's authoritative arbiter,
exclusive flock, PBS/client checks and thermal/memory/IO watchdog.
Never changes the production model catalog, services or global symlinks.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import statistics
import subprocess
import time

ROOT = Path('/srv/storage/nvme/DEV/Projets/HomeLab/Moteurs IA')  # HOST filesystem; binaries live in CT700 with translated path
MODEL = Path('/srv/lxc/ia-compute/data/models/bakeoff-20261002/qwen38distill-qwen35-4b-mtp/Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf')
STAGE = Path('/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases')
PROD = STAGE/'production-copy-upstream-2bb-20261023/llama-cli'
VULKAN = STAGE/'upstream-master9ff-vulkan-gfx1103-20261023/llama-cli'
HIP = STAGE/'chimera-mmb-r120-master9ff-hip-20261023/llama-cli'
CANDIDATES = {'vulkan9ff':VULKAN,'hipoff':HIP,'hipon':HIP,'hipf32':HIP}
EXPECTED_SHA = {'production':'b102daad6ca5cf8734c48c207bbc84580f18fe3054db2122bc69d8a0e64f1dca',
                'vulkan9ff':'f45b3fe2f742326d76cb1729e7b4b5256ff8579f2d8508b7eecb778218562fb1',
                'hipoff':'0cd75021d858cc0d9dab83f41c29726e6c058b802766e8af61be96b2a6574ed7',
                'hipon':'0cd75021d858cc0d9dab83f41c29726e6c058b802766e8af61be96b2a6574ed7',
                'hipf32':'0cd75021d858cc0d9dab83f41c29726e6c058b802766e8af61be96b2a6574ed7'}
HIP_ENVS = {
 'hipoff':{'GGML_CUDA_MMB':'0','GGML_CUDA_MMB_RDNA3':'1','GGML_CUDA_MMF32':'0'},
 'hipon':{'GGML_CUDA_MMB':'1','GGML_CUDA_MMB_RDNA3':'1','GGML_CUDA_MMF32':'0'},
 'hipf32':{'GGML_CUDA_MMB':'1','GGML_CUDA_MMB_RDNA3':'1','GGML_CUDA_MMF32':'1'},
}
CT = ['sudo', '-n', 'pct', 'exec']
FLAGS = ('-c', '16384', '-b', '1024', '-ub', '1024', '-t', '8', '-tb', '8',
         '-ngl', '99', '--flash-attn', 'on', '-ctk', 'f16', '-ctv', 'f16',
         '--spec-type', 'draft-mtp', '--spec-draft-n-max', '2',
         '--spec-draft-p-min', '0', '--no-spec-draft-backend-sampling',
         '--lazy-mode', 'off', '--poll', '100', '--poll-batch', '0',
         '--fit', 'off', '--no-warmup', '--reasoning', 'off')
PROMPTS = {
    'short': 'Calcule 117 + 285 puis réponds en français, en une phrase.',
    'long': ('Voici un texte entièrement fictif. Lis-le avant de répondre.\n'
             + '\n'.join(
                 f'Ligne {i:04d} : la rivière bleue traverse le village ; une cloche sonne dans la tour.'
                 for i in range(140))
             + '\nDonne seulement la somme 117 + 285, avec le résultat en français.'),
}

def ct410_path(path):
    path=Path(path)
    if not path.is_relative_to(STAGE):
        raise ValueError('BAD_CT410_STAGE_PATH')
    return str(path)

def env_for(binary, challenger):
    env=['LD_LIBRARY_PATH='+str(binary.parent)+':'+str(binary.parent/'rocm-10.1/lib')]
    if binary==HIP:
        env += [k+'='+v for k,v in sorted(HIP_ENVS[challenger].items())]
    return env

def shell(args, timeout=9):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError('COMMAND_FAILED '+repr(args[:6])+' '+p.stderr[-180:])
    return p.stdout

def parse_telemetry(meminfo, psi_mem, psi_io, gtt_bytes, tctl):
    def mem(name):
        match = re.search(r'^'+re.escape(name)+r':\s*(\d+)', meminfo, re.M)
        if not match:
            raise ValueError('MISSING_MEMINFO_'+name)
        return int(match.group(1))
    def pressure(text):
        match = re.search(r'^full avg10=([0-9.]+)', text, re.M)
        if not match:
            raise ValueError('MISSING_PSI_FULL')
        return float(match.group(1))
    sw_total = mem('SwapTotal')
    if not sw_total:
        raise ValueError('MISSING_SWAP')
    return {
        'available_gib': round(mem('MemAvailable') / 1048576, 3),
        'swap_percent': round(100*(1-mem('SwapFree')/sw_total), 2),
        'memory_psi_full_avg10': pressure(psi_mem),
        'io_psi_full_avg10': pressure(psi_io),
        'gtt_gib': round(gtt_bytes/(1024**3), 3),
        'tctl_c': tctl,
    }

def host_state():
    t = shell(['sensors'])
    c = re.search(r'^Tctl:\s*\+([0-9.]+)\s*°C', t, re.M)
    if not c:
        raise RuntimeError('NO_TCTL_SENSOR')
    return parse_telemetry(
        Path('/proc/meminfo').read_text(),
        Path('/proc/pressure/memory').read_text(),
        Path('/proc/pressure/io').read_text(),
        int(Path('/sys/class/drm/card0/device/mem_info_gtt_used').read_text()),
        float(c.group(1)),
    )

def official_gpu_check():
    cmd = ('import socket,json;'
           's=socket.create_connection(("192.168.1.200",19755),3);'
           's.sendall(b"CHECK coexist-light 7.0\\n");'
           'print(s.recv(8192).decode());s.close()')
    return json.loads(shell(CT+['410','--','python3','-c',cmd], timeout=9))

def production_clients():
    ss = shell(CT + ['410','--','ss','-Htn','state','established'])
    return [line for line in ss.splitlines()
            if re.search(r':(?:8005|8007|8010|3900|7443|8090|18091)\b', line)]

def backup_running():
    return subprocess.run(
        ['pgrep','-f','^proxmox-backup-client backup'],
        capture_output=True, timeout=5).returncode == 0

def admission():
    t=host_state()
    official=official_gpu_check()
    clients=production_clients()
    why=[]
    if not official.get('allow'): why.append('OFFICIAL_GPU_REJECTION')
    if t['available_gib'] < 32: why.append('RAM_BELOW_32_GIB')
    if t['swap_percent'] >= 80: why.append('SWAP_GE_80_PERCENT')
    if t['memory_psi_full_avg10'] >= .35: why.append('MEMORY_PSI_GE_0.35')
    if t['io_psi_full_avg10'] >= 5: why.append('IO_PSI_GE_5')
    if t['gtt_gib'] >= 1: why.append('GPU_ALREADY_BUSY')
    if t['tctl_c'] >= 73: why.append('CPU_TOO_HOT')
    if clients: why.append('PRODUCTION_CLIENTS_CONNECTED')
    if backup_running(): why.append('BACKUP_ACTIVE')
    return {'allow':not why,'reasons':why,'host':t,'official':official,
            'prod_clients':len(clients)}

def watchdog_bad(t):
    return (t['available_gib'] < 23
            or t['swap_percent'] >= 90
            or t['memory_psi_full_avg10'] >= 1.5
            or t['io_psi_full_avg10'] >= 12
            or t['gtt_gib'] > 7.5
            or t['tctl_c'] >= 78)

def stop_own(executable):
    script = (
        "import os,signal,sys\n"
        "for pid in os.listdir('/proc'):\n"
        " if not pid.isdigit():continue\n"
        " try:\n"
        "  args=open('/proc/'+pid+'/cmdline','rb').read().split(b'\\0')\n"
        "  if args and args[0].decode(errors='replace')==sys.argv[1] and b'--spec-type' in args:\n"
        "   os.kill(int(pid),signal.SIGTERM)\n"
        " except (OSError,ValueError):pass\n"
    )
    return subprocess.run(
        CT+['410','--','python3','-c',script,ct410_path(executable)],
        capture_output=True,text=True,timeout=9).stdout.strip()

def run_trial(binary,label,case,rep,folder,challenger):
    logpath=folder/f'{label}-{case}-{rep}.log'
    cli=[ct410_path(binary),'-m',str(MODEL),'-p',PROMPTS[case],
         '-n','128','--seed','23','--temp','0','--simple-io',
         '--no-display-prompt','--perf',*FLAGS]
    run_command=CT+['410','--','runuser','-u','arezki','--','env',
                    *env_for(binary,challenger),*cli]
    proc=None;abort=None;samples=[];start=time.monotonic()
    try:
        with logpath.open('x') as stdout:
            proc=subprocess.Popen(run_command,stdout=stdout,stderr=subprocess.STDOUT,
                                  start_new_session=True)
            consecutive=0
            while proc.poll() is None and time.monotonic()-start<160:
                t=host_state();samples.append(t)
                consecutive=consecutive+1 if watchdog_bad(t) else 0
                if consecutive>=2:abort='WATCHDOG_RESOURCE_LIMIT'
                if backup_running():abort='BACKUP_STARTED'
                if production_clients():abort='PROD_CLIENT_RACE'
                if abort:
                    stop_own(binary)
                    break
                time.sleep(.85)
            if proc.poll() is None:
                abort=abort or 'TRIAL_TIMEOUT'
                stop_own(binary)
                os.killpg(proc.pid,signal.SIGTERM)
                try:proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL)
                    proc.wait(timeout=4)
        output=logpath.read_text(errors='replace')
        speed={}
        for key,pattern in (('pp',r'Prompt:\s*([0-9.]+) t/s'),
                            ('tg',r'Generation:\s*([0-9.]+) t/s')):
            match=re.search(pattern,output,re.I)
            if match:speed[key]=float(match.group(1))
        return {'backend':label,'case':case,'rep':rep,
                'pass':proc.returncode==0 and not abort and len(speed)==2,
                'exit_code':proc.returncode,'abort_reason':abort,
                'wall_s':round(time.monotonic()-start,3),'speed_tps':speed,
                'mentions_expected_402':'402' in output,
                'telemetry':samples,
                'raw_log_sha256':hashlib.sha256(logpath.read_bytes()).hexdigest()}
    finally:
        if proc and proc.poll() is None:
            try:
                stop_own(binary)
                os.killpg(proc.pid,signal.SIGTERM)
                proc.wait(timeout=6)
            except Exception:pass

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true',
                   help='Explicitly request a guarded GPU test; default does NOT load a model')
    p.add_argument('--reps',type=int,default=3)
    p.add_argument('--challenger',choices=sorted(CANDIDATES),default='vulkan9ff',
                   help='Same CT410, same production GGUF/flags, isolated LAB backend')
    args=p.parse_args()
    if not 1<=args.reps<=3:p.error('reps must be 1, 2, or 3')
    a=admission()
    latest=CANDIDATES[args.challenger]
    if not args.execute or not a['allow']:
        print(json.dumps({'status':'PREFLIGHT_ONLY' if not args.execute else 'GPU_BLOCKED',
                          'admission':a,'challenger':args.challenger},indent=2))
        if args.execute and not a['allow']:
            raise SystemExit(3)  # requested run REFUSED, never a successful benchmark
        return
    for path in (MODEL,PROD,latest):
        if not path.is_file():raise RuntimeError('MISSING_REQUIRED_FILE '+str(path))
    if MODEL.stat().st_size!=2790000800:raise RuntimeError('WRONG_GGUF')
    # Version attestation before SHA-bound comparatives.
    for binary,commit in ((PROD,'2bb27e5de'),(latest,'9ff0d7e90')):
        label='production' if binary==PROD else args.challenger
        actual_sha=hashlib.sha256(binary.read_bytes()).hexdigest()
        if actual_sha!=EXPECTED_SHA[label]:
            raise RuntimeError('STAGED_BINARY_SHA_MISMATCH '+str(binary))
        banner=shell(CT+['410','--','runuser','-u','arezki','--',
                         'env',*env_for(binary,args.challenger),ct410_path(binary),'--version'],timeout=15)
        if commit not in banner:raise RuntimeError('UNEXPECTED_BINARY_VERSION '+str(binary))
    folder=ROOT/'Sources/Benchmarks/Engine-Tournament/2026-10-23'
    folder.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    outfile=folder/f'4b-production-vs-{args.challenger}-16k-{stamp}.json'
    with MODEL.open('rb') as model_file:
        model_sha256 = hashlib.file_digest(model_file,'sha256').hexdigest()
    record={'status':'STARTED','production_changed':False,'production_eligible':False,
            'flags_identical':list(FLAGS),'model':str(MODEL),
            'model_size_bytes':MODEL.stat().st_size,'model_sha256':model_sha256,
            'sha256':{'reference':hashlib.sha256(PROD.read_bytes()).hexdigest(),
                      'latest':hashlib.sha256(latest.read_bytes()).hexdigest()},
            'prompts_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in PROMPTS.items()},
            'admission':a,'challenger':args.challenger,'lab_stage_only':True,'runs':[]}
    lock=None
    try:
        lock=subprocess.Popen(CT+['410','--','flock','-n','/run/cloud9-gpu.lock',
              'bash','-lc','echo EXACT16K_EXCLUSIVE_LOCK; read -r _'],
              stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        ready,_,_=select.select([lock.stdout],[],[],8)
        if not ready or lock.stdout.readline().strip()!='EXACT16K_EXCLUSIVE_LOCK':
            raise RuntimeError('GPU_LOCK_BUSY')
        for rep in range(1,args.reps+1):
            backends=[('prod_reference',PROD),(args.challenger,latest)]
            if rep%2==0:backends.reverse()
            for case in ('short','long'):
                for label,binary in backends:
                    check=admission()
                    if not check['allow']:
                        record.update(status='INCOMPLETE_ADMISSION_LOST',reason=check['reasons'])
                        return
                    row=run_trial(binary,label,case,rep,folder,args.challenger)
                    record['runs'].append(row)
                    record['status']='PARTIAL'
                    outfile.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
                    if not row['pass']:
                        record['status']='INTERRUPTED'
                        return
        record['status']='COMPLETE_EXPLORATORY_REVIEW_PENDING'
    finally:
        if lock and lock.poll() is None:
            try:
                lock.stdin.write('release\n')
                lock.stdin.flush()
                lock.wait(timeout=6)
            except Exception:lock.terminate()
        outfile.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({'status':record['status'],
                          'trials':len(record['runs']),'evidence':str(outfile)}))

if __name__=='__main__':
    main()
