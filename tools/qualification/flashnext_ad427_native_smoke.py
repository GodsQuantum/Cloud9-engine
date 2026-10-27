#!/usr/bin/env python3
"""Bounded one-shot native Qwen4Exp AD4.27 + FR-Spec -md GPU smoke.

Never modifies running services or guardian limits. A refused admission is NOT a
benchmark. On every exit the tester terminates only its own child process.
"""
import argparse,fcntl,json,os,signal,subprocess,threading,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path
import moe_upstream_bakeoff as gate

ROOT=Path('/srv/storage/nvme/shared/ai-models/llm/gguf/FlashNext-AD427')
TARGET=ROOT/'Qwen3.8-Flash-Next-AD-4.27bpw-Q4_K_M-M64/Qwen3.8-Flash-Next-AD-4.27bpw-Q4_K_M-M64-00001-of-00033.gguf'
DRAFT=ROOT/'MTP/mtp-Qwen3.8-Flash-Next-Q8_0-frspec-65k.gguf'
BIN=Path('/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/atomic2-frspec65k-native-lab-20261026/bin/llama-server')
LAB=Path('/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/local-agent-readiness-20261024')
URL='http://127.0.0.1:18148'

# The GGUF's 35.763GiB per_layer_token_embd is demand-paged from CPU mmap.
# 47.168GiB experts remain CPU-mapped. 5.10GiB main core plus ~3.39GiB
# draft offloaded to the Radeon GPU, with real GTT guard >= 12.5GiB.
COMMAND=[str(BIN),'-m',str(TARGET),'-md',str(DRAFT),'-ngl','99',
         '--n-cpu-moe','48','-ot',r'per_layer_token_embd\.weight=CPU',
         '--spec-type','draft-mtp','--spec-draft-n-max','3',
         '--spec-draft-p-min','0','--no-spec-draft-backend-sampling',
         '--moe-cache','off','--tensor-read-lazy','on','--load-mode','mmap','--fit','off',
         '-c','1024','-np','1','-b','128','-ub','64','-t','8','-tb','8',
         '-fa','on','--no-warmup','--no-cache-prompt',
         '--reasoning','off','--host','127.0.0.1','--port','18148',
         '--no-webui','--alias','FlashNext-AD427-FRSpec65K-LAB']

def readonly_preflight():
    shards=sorted(TARGET.parent.glob('Qwen3.8-Flash-Next-AD-4.27bpw-Q4_K_M-M64-*-of-00033.gguf'))
    actual=sum(f.stat().st_size for f in shards)
    reasons=[]
    if len(shards)!=33 or actual!=94525394976:reasons.append('TARGET_33_SHARDS_INCOMPLETE')
    if not DRAFT.is_file() or DRAFT.stat().st_size!=3639245152:reasons.append('FRSPEC_DRAFT_MISSING_OR_CHANGED')
    if not BIN.is_file():reasons.append('ISOLATED_NATIVE_ELF_MISSING')
    health=gate.guardian(12.5)
    if not health.get('allow'):reasons.append('OFFICIAL_GPU_GUARD_DENIED')
    if health.get('mem_available_gib',0)<30:reasons.append('HOST_AVAILABLE_RAM_BELOW_30GIB')
    if health.get('psi_memory_full_avg10',99)>=1.5:reasons.append('HOST_MEMORY_PSI')
    io=gate.psi_io_full()
    if io is None or io>=9:reasons.append('HOST_IO_PSI')
    temp=gate.host_temp()
    if temp is None or temp>=76:reasons.append('HOST_TEMPERATURE')
    if gate.embeddings_busy():reasons.append('EMBEDDINGS_ACTIVE_OR_UNKNOWN')
    try:
        if gate.fetch(gate.ROUTER,timeout=3).get('worker_model') is not None:reasons.append('ROUTER_WORKER_ACTIVE')
    except Exception:reasons.append('ROUTER_UNAVAILABLE')
    try:
        a=gate.fetch(gate.AUTOSUBS,timeout=3)
        if a.get('status')!='ok' or a.get('loaded_models')!=[]:reasons.append('AUTOSUBS_BUSY_OR_UNREACHABLE')
    except Exception:reasons.append('AUTOSUBS_UNREACHABLE')
    return {'allow':not reasons,'reasons':reasons,'gpu_guardian':health,'host_io_psi_full10':io,'temp_c':temp,'main_model_bytes':actual,'draft_bytes':DRAFT.stat().st_size if DRAFT.is_file() else -1}

def load_and_generate(result,path,max_load_s,launch_cmd):
    fd=os.open(str(gate.LOCK),os.O_CREAT|os.O_RDWR,0o660)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            result['status']='gpu_lock_busy';return
        double=readonly_preflight();result['second_preflight']=double
        if not double['allow']:result['status']='blocked_after_lock';return
        child=None;exiting=threading.Event();events=[]
        logfile=LAB/('flashnext_ad427_'+result['run_id']+'.log')
        with logfile.open('x') as out:
            env=os.environ.copy();env['LD_LIBRARY_PATH']=str(BIN.parent)
            # Force line-buffered startup diagnostics before an emergency
            # shutdown; otherwise the native stdout logger can lose the
            # stage where the 88GiB GGUF begins faulting memory pages.
            child=subprocess.Popen(['stdbuf','-oL','-eL',*launch_cmd],stdout=out,stderr=subprocess.STDOUT,env=env)
            result['status']='loading';path.write_text(json.dumps(result,indent=2)+'\n')
            def watch():
                while not exiting.wait(2):
                    try:
                        g=gate.guardian(0);temp=gate.host_temp();io=gate.psi_io_full()
                        # CHECK is an admission decision for NEW jobs; after admission,
                        # follow the owner-authorized full-GPU Pym runtime PSI 12.0/temperature watchdog
                        # rather than terminating an existing job at transient PSI 0.5.
                        danger=(g.get('mem_available_gib',0)<20 or g.get('psi_memory_full_avg10',99)>=12.0 or
                                g.get('swap_used_percent',100)>90 or temp is None or temp>=80 or
                                io is None or io>24 or gate.embeddings_busy())
                        if danger:
                            events.append({'reason':'RUNTIME_SAFETY_STOP','guardian':g,'io':io,'temp':temp})
                            gate.stop_own(child);return
                    except Exception as e:
                        events.append({'reason':'GUARD_UNAVAILABLE','error':type(e).__name__})
                        gate.stop_own(child);return
            worker=threading.Thread(target=watch,daemon=True);worker.start()
            try:
                start=time.monotonic();ready=False
                while time.monotonic()-start<max_load_s:
                    if child.poll() is not None or events:break
                    try:
                        if gate.fetch(URL+'/health',timeout=2).get('status')=='ok':ready=True;break
                    except Exception:pass
                    time.sleep(1)
                result['model_load_seconds']=round(time.monotonic()-start,3)
                if not ready:
                    result['status']='failed_load_or_safety';return
                result['status']='ready'
                prompts=[('math','Calcule 25 × 37. Réponds avec le résultat entier.'),
                         ('fr','En une phrase, explique ce qu’est un processeur graphique.'),
                         ('code','Écris une fonction Python qui renvoie le carré d’un entier.')]
                for task,prompt in prompts:
                    if events or child.poll() is not None:break
                    payload={'prompt':prompt,'n_predict':32,'temperature':0,'cache_prompt':False}
                    try:
                        x=gate.fetch(URL+'/completion',payload,timeout=100)
                        timings=x.get('timings',{})
                        text=x.get('content','')
                        row={'task':task,'text':text[:600],'timings':timings,'num_predicted_tokens':x.get('tokens_predicted'),'correct_math':('925' in text) if task=='math' else None}
                        result['rows'].append(row)
                        result['status']='generating'
                        path.write_text(json.dumps(result,indent=2)+'\n')
                    except Exception as e:
                        result['request_error']=type(e).__name__+': '+str(e)[:200]
                        break
                result['status']='complete' if len(result['rows'])==3 and result['rows'][0].get('correct_math') else 'failed_quality_or_runtime'
            finally:
                exiting.set();gate.stop_own(child);worker.join(timeout=5)
                result['guard_events']=events
    finally:
        os.close(fd)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--execute',action='store_true');ap.add_argument('--max-load-s',type=int,default=210);ap.add_argument('--moe-cache',choices=['off','soft','auto','4096'],default='off')
    a=ap.parse_args()
    if not (1<=len(a.run_id)<=45 and all(c.isalnum() or c in '_-' for c in a.run_id)):ap.error('Invalid run id')
    path=LAB/('flashnext_ad427_'+a.run_id+'.json')
    if path.exists() or (LAB/('flashnext_ad427_'+a.run_id+'.log')).exists():ap.error('Refuse overwrite immutable trial')
    launch_cmd=COMMAND.copy();launch_cmd[launch_cmd.index('--moe-cache')+1]=a.moe_cache
    result={'moe_cache_mode':a.moe_cache,'run_id':a.run_id,'utc':datetime.now(timezone.utc).isoformat(),'target':'Qwen3.8-Flash-Next AD4.27 33GGUF','draft':'FRSpec65k Q8','engine':'isolated Atomic2 patched3df182b0','model_quantization_unchanged':True,'n_cpu_moe':48,'gpu_layers':99,'ngram_cpu_mmap':True,'draft_depth':3,'status':'preflight','rows':[],'guard_events':[],'production_untouched':True,'command':launch_cmd[1:]}
    try:
        preflight=readonly_preflight();result['preflight']=preflight
        if not preflight['allow']:result['status']='blocked_preflight'
        elif not a.execute:result['status']='admitted_not_executed'
        else:load_and_generate(result,path,a.max_load_s,launch_cmd)
    except Exception as e:
        result['status']='internal_error';result['error']=type(e).__name__+': '+str(e)[:300]
    finally:
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'status':result['status'],'reasons':result.get('preflight',{}).get('reasons'),'rows':[{'task':r['task'],'tps':r.get('timings',{}).get('predicted_per_second')} for r in result['rows']],'output':str(path)}))

if __name__=='__main__':main()
