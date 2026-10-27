#!/usr/bin/env python3
"""A/B expert-pool Vulkan trunk-only laboratory; NOT a FR-Spec benchmark.

Reuses Cloud9's guarded AD4.27 runner, GPU lock, shutdown and JSON evidence.
Only the test process, never production, is launched on loopback.
"""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
import flashnext_ad427_native_smoke as lab

BIN=Path('/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/llama-moe-expert-pool-20261027/bin/llama-server')
COMMAND=[str(BIN),'-m',str(lab.TARGET),'-ngl','99','--n-cpu-moe','48',
         '--moe-expert-cache','0','-ot',r'per_layer_token_embd\.weight=CPU',
         '--load-mode','mmap','--fit','off','-c','1024','-np','1','-b','128','-ub','64',
         '-t','8','-tb','8','-fa','on','--no-warmup','--no-cache-prompt',
         '--reasoning','off','--host','127.0.0.1','--port','18148','--no-webui',
         '--alias','FlashNext-AD427-EXPERT-POOL-LAB']

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run-id',required=True)
    ap.add_argument('--slots',type=int,choices=[0,16,32,64],required=True)
    ap.add_argument('--execute',action='store_true')
    ap.add_argument('--max-load-s',type=int,default=180)
    a=ap.parse_args()
    if not (1<=len(a.run_id)<=45 and all(c.isalnum() or c in '_-' for c in a.run_id)):ap.error('invalid run ID')
    path=lab.LAB/('flashnext_ad427_'+a.run_id+'.json')
    if path.exists() or (lab.LAB/('flashnext_ad427_'+a.run_id+'.log')).exists():ap.error('immutable result already exists')
    lab.BIN=BIN
    cmd=COMMAND.copy();cmd[cmd.index('--moe-expert-cache')+1]=str(a.slots)
    result={'run_id':a.run_id,'date':datetime.now(timezone.utc).isoformat(),'status':'preflight',
            'engine':'memoriaru llama.cpp moe-expert-pool 555d1ec, isolated Qwen4Exp lazy mmap',
            'main_model':'exact AD4.27 33 shards','draft_model':None,
            'FRSpec_MTP_used':False,'full_FRSpec_qualification':False,
            'quantization_unchanged':True,'expert_slots':a.slots,'n_cpu_moe':48,
            'command':cmd[1:],'rows':[],'guard_events':[],'production_untouched':True}
    try:
        pre=lab.readonly_preflight(48);result['preflight']=pre
        if not pre['allow']:result['status']='blocked_preflight'
        elif not a.execute:result['status']='admitted_not_executed'
        else:lab.load_and_generate(result,path,a.max_load_s,cmd)
    except Exception as e:
        result['status']='internal_error';result['error']=type(e).__name__+': '+str(e)[:240]
    finally:
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'run_id':a.run_id,'status':result['status'],'slots':a.slots,
                          'rates':[(r['task'],r.get('timings',{}).get('predicted_per_second')) for r in result['rows']],
                          'preflight_reasons':result.get('preflight',{}).get('reasons',[])}))

if __name__=='__main__':main()
