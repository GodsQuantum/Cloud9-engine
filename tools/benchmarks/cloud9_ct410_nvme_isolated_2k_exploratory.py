#!/usr/bin/env python3
"""Exploratory CT410 GPU A/B on NVMe while USB NFS is stalled. Never production-certified."""
import argparse,hashlib,json,os,select,signal,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parent))
from cloud9_prod4b_exact16k_ct410_tournament import (MODEL,PROD,VULKAN,EXPECTED_SHA,ROOT,CT,FLAGS,env_for,ct410_path,host_state,official_gpu_check,production_clients,backup_running,parse_llama_timing,stop_own)
PROMPT=('En français, écris dix conseils numérotés très concrets pour comparer '
        'deux moteurs LLM locaux. Une phrase détaillée par conseil, sans abréviation.')
FLAGS2=('-c','2048','-b','512','-ub','512')+FLAGS[6:]
def check():
    h=host_state();gpu=official_gpu_check()
    failures=[]
    if not gpu.get('allow'):failures.append('OFFICIAL_GPU_REJECT')
    if h['available_gib']<23:failures.append('RAM_BELOW_23')
    if h['memory_psi_full_avg10']>=.35:failures.append('MEMORY_PSI')
    if h['gtt_gib']>=1:failures.append('GPU_BUSY')
    if h['tctl_c']>=73:failures.append('TEMP')
    if h['swap_percent']>=80:failures.append('SWAP')
    if production_clients():failures.append('PROD_CLIENT')
    if backup_running():failures.append('BACKUP_STARTED')
    return {'allow':not failures,'reasons':failures,'host':h,'official':gpu}
def monitor_bad(h):
    if h['available_gib']<18:return 'MEMORY_RESERVE'
    if h['memory_psi_full_avg10']>=1.5:return 'MEMORY_PRESSURE'
    if h['gtt_gib']>7:return 'GTT_LIMIT'
    if h['tctl_c']>=77:return 'THERMAL'
    if h['swap_percent']>=87:return 'SWAP'
def trial(binary,name,out):
    cmd=CT+['410','--','runuser','-u','arezki','--','env',*env_for(binary,'vulkan9ff'),
        ct410_path(binary),'-m',str(MODEL),'-p',PROMPT,'-n','96','--seed','472649','--temp','0',
        '--simple-io','--no-display-prompt','--perf',*FLAGS2]
    start=time.monotonic();reason=None;samples=[];proc=None
    try:
        with out.open('x') as f:
            proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            while proc.poll() is None:
                h=host_state();samples.append(h)
                reason=monitor_bad(h)
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
            'sha256_log':hashlib.sha256(out.read_bytes()).hexdigest(),'log':str(out)}
    finally:
        if proc and proc.poll() is None:
            stop_own(binary)
            try:os.killpg(proc.pid,signal.SIGTERM)
            except ProcessLookupError:pass
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true')
    args=parser.parse_args();ad=check()
    print('ADMISSION',json.dumps(ad),flush=True)
    if not args.execute:return
    if not ad['allow']:raise SystemExit(3)
    for name,binary in (('production',PROD),('vulkan9ff',VULKAN)):
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
            'note':'Global USB filesystem stalls confound run; only compare as exploratory'}
    evidence=folder/'results.json';evidence.write_text(json.dumps(record,indent=2)+'\n')
    lock=None
    try:
        lock=subprocess.Popen(CT+['410','--','flock','-n','/run/cloud9-gpu.lock',
             'bash','-lc','echo GPU_ISOLATED; read -r _'],
             stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        ready,_,_=select.select([lock.stdout],[],[],8)
        if not ready or lock.stdout.readline().strip()!='GPU_ISOLATED':raise RuntimeError('NO_GPU_LOCK')
        for name,binary in (('production',PROD),('vulkan9ff',VULKAN)):
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
