#!/usr/bin/env python3
"""Exploratory CT410 GPU A/B on NVMe while USB NFS is stalled. Never production-certified."""
import argparse,hashlib,json,os,select,signal,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parent))
from cloud9_prod4b_exact16k_ct410_tournament import (MODEL,PROD,VULKAN,HIP,CANDIDATES,EXPECTED_SHA,ROOT,CT,FLAGS,env_for,ct410_path,host_state,official_gpu_check,production_clients,backup_running,parse_llama_timing,stop_own)
def official_gpu_check_4g():
    # Same authoritative arbiter, smaller real reservation than the 7 GiB 16K tournament.
    # This 2K fixture used only 1.934 GiB of GTT on exact production reference.
    cmd=('import socket,json;'
         's=socket.create_connection(("192.168.1.200",19755),3);'
         's.sendall(b"CHECK coexist-light 4.0\\n");'
         'print(s.recv(8192).decode());s.close()')
    from cloud9_prod4b_exact16k_ct410_tournament import shell
    return json.loads(shell(CT+['410','--','python3','-c',cmd],timeout=9))

PROMPT=('En français, écris dix conseils numérotés très concrets pour comparer '
        'deux moteurs LLM locaux. Une phrase détaillée par conseil, sans abréviation.')
FLAGS2=('-c','2048','-b','512','-ub','512')+FLAGS[6:]
def check():
    h=host_state();gpu=official_gpu_check_4g()
    failures=[]
    if not gpu.get('allow'):failures.append('OFFICIAL_GPU_REJECT')
    if h['available_gib']<24:failures.append('RAM_BELOW_24')
    if h['memory_psi_full_avg10']>=.35:failures.append('MEMORY_PSI')
    if h['gtt_gib']>=1:failures.append('GPU_BUSY')
    if h['tctl_c']>=73:failures.append('TEMP')
    if h['swap_percent']>=80:failures.append('SWAP')
    if production_clients():failures.append('PROD_CLIENT')
    if backup_running():failures.append('BACKUP_STARTED')
    return {'allow':not failures,'reasons':failures,'host':h,'official':gpu}
def monitor_bad(h):
    if h['available_gib']<18:return 'MEMORY_RESERVE'
    if h['memory_psi_full_avg10']>=4.0:return 'SEVERE_MEMORY_PRESSURE'
    # Temporary USB writeback stalls create brief PSI spikes; ordinary
    # pressure is handled with two consecutive samples, just like 16K guard.
    if h['gtt_gib']>4:return 'GTT_LIMIT'
    if h['tctl_c']>=77:return 'THERMAL'
    if h['swap_percent']>=87:return 'SWAP'
def trial(binary,name,out):
    cmd=CT+['410','--','runuser','-u','arezki','--','env',*env_for(binary,name if name in CANDIDATES else 'vulkan9ff'),
        ct410_path(binary),'-m',str(MODEL),'-p',PROMPT,'-n','96','--seed','472649','--temp','0',
        '--simple-io','--no-display-prompt','--perf',*FLAGS2]
    start=time.monotonic();reason=None;samples=[];proc=None;pressure_streak=0
    try:
        with out.open('x') as f:
            proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            while proc.poll() is None:
                h=host_state();samples.append(h)
                reason=monitor_bad(h)
                pressure_streak=(pressure_streak+1 if h['memory_psi_full_avg10']>=1.5 else 0)
                if not reason and pressure_streak>=2:reason='SUSTAINED_MEMORY_PRESSURE'
                if not reason and backup_running():reason='BACKUP_ACTIVE'
                if not reason and production_clients():reason='PROD_CLIENT'
                if not reason and time.monotonic()-start>115:reason='TIMEOUT'
                if reason:
                    stop_own(binary)
                    try:os.killpg(proc.pid,signal.SIGTERM)
                    except ProcessLookupError:pass
                    try:proc.wait(timeout=6)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=5)
                    break
                time.sleep(.7)
        parsed=parse_llama_timing(out.read_text(errors='replace'))
        return {'name':name,'pass':proc.returncode==0 and not reason and parsed['timings_parseable'],
            'reason':reason,'return_code':proc.returncode,'wall_seconds':round(time.monotonic()-start,2),
            **parsed,'min_memory_gib':min([h['available_gib'] for h in samples],default=None),
            'max_gtt_gib':max([h['gtt_gib'] for h in samples],default=None),
            'max_temp_c':max([h['tctl_c'] for h in samples],default=None),
            'max_memory_psi_full_avg10':max([h['memory_psi_full_avg10'] for h in samples],default=None),
            'max_io_psi_full_avg10':max([h['io_psi_full_avg10'] for h in samples],default=None),
            'sha256_log':hashlib.sha256(out.read_bytes()).hexdigest(),'log':str(out)}
    finally:
        if proc and proc.poll() is None:
            stop_own(binary)
            try:os.killpg(proc.pid,signal.SIGTERM)
            except ProcessLookupError:pass
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true')
    parser.add_argument('--candidate-only',action='store_true',
                        help='Measure selected challenger alone, never re-run production')
    parser.add_argument('--challenger',choices=('vulkan9ff','hipoff','hipon','hipf32'),
                        default='vulkan9ff',help='Pinned 9ff Vulkan or r120 HIP ablation on the same GGUF and short flags')
    parser.add_argument('--challenger-first',action='store_true',
                        help='Counterbalance thermal/cache order: run challenger before production')
    args=parser.parse_args();ad=check()
    print('ADMISSION',json.dumps(ad),flush=True)
    if not args.execute:return
    if not ad['allow']:raise SystemExit(3)
    selected=((args.challenger,CANDIDATES[args.challenger]),) if args.candidate_only else (
        ((args.challenger,CANDIDATES[args.challenger]),('production',PROD))
        if args.challenger_first else
        (('production',PROD),(args.challenger,CANDIDATES[args.challenger])))
    for name,binary in selected:
        if not binary.is_file() or hashlib.sha256(binary.read_bytes()).hexdigest()!=EXPECTED_SHA[name]:
            raise RuntimeError('BINARY_PIN_BAD_'+name)
    if not MODEL.is_file() or MODEL.stat().st_size!=2790000800:
        raise RuntimeError('MODEL_WRONG')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder=ROOT/'Sources/Benchmarks/Engine-Tournament/2026-10-24'/('nvme-lite-'+stamp)
    folder.mkdir(parents=True,exist_ok=False)
    record={'status':'STARTED','rows':[],'admission':ad,'max_ctx_tokens':2048,'production_changed':False,
            'qualification':'EXPLORATORY_ONLY_NOT_PRODUCTION_ELIGIBLE',
            'nvme_model_read':str(MODEL),'global_io_psi_ignored_because_USB_NFS_STALL':True,
            'authoritative_GPU_reservation_gib':4.0,
            'note':'Global USB filesystem stalls confound run; only compare as exploratory',
            'candidate_only':args.candidate_only,'challenger':args.challenger,
            'challenger_first':args.challenger_first,'actual_run_order':[name for name,_ in selected]}
    evidence=folder/'results.json';evidence.write_text(json.dumps(record,indent=2)+'\n')
    lock=None
    try:
        lock=subprocess.Popen(CT+['410','--','flock','-n','/run/cloud9-gpu.lock',
             'bash','-lc','echo GPU_ISOLATED; read -r _'],
             stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        ready,_,_=select.select([lock.stdout],[],[],8)
        if not ready or lock.stdout.readline().strip()!='GPU_ISOLATED':raise RuntimeError('NO_GPU_LOCK')
        for name,binary in selected:
            gate=check()
            if not gate['allow']:
                record.update(status='ADMISSION_LOST',last_gate=gate);break
            row=trial(binary,name,folder/(name+'.log'));record['rows'].append(row)
            record['status']='PARTIAL'
            evidence.write_text(json.dumps(record,indent=2)+'\n')
            print('TRIAL',json.dumps({k:row.get(k) for k in ('name','pass','speed_tps','token_counts','reason','wall_seconds')}),flush=True)
            if not row['pass']:record['status']='ABORTED';break
        else:record['status']='COMPLETE_EXPLORATORY'
    finally:
        if lock and lock.poll() is None:
            try:lock.stdin.write('release\n');lock.stdin.flush();lock.wait(timeout=5)
            except Exception:lock.terminate()
        evidence.write_text(json.dumps(record,indent=2)+'\n')
        print('EVIDENCE',str(evidence),'RESULT',record['status'],flush=True)
if __name__=='__main__':main()
