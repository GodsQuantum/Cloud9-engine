#!/usr/bin/env python3
import argparse,json,statistics,time,urllib.request
ap=argparse.ArgumentParser(); ap.add_argument('--port',type=int,required=True); ap.add_argument('--prompt',required=True); ap.add_argument('--runs',type=int,default=3); ap.add_argument('--tokens',type=int,default=128)
a=ap.parse_args(); prompt=open(a.prompt).read(); rows=[]
for i in range(a.runs):
    body={'model':'cloud9-engine','messages':[{'role':'user','content':prompt}],'temperature':0,'seed':42,'max_tokens':a.tokens,'cache_prompt':False}
    req=urllib.request.Request(f'http://127.0.0.1:{a.port}/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    t=time.time()
    with urllib.request.urlopen(req,timeout=600) as resp: d=json.load(resp)
    tm=d.get('timings',{}); rows.append({'decode_tps':tm.get('predicted_per_second',0.0),'prefill_tps':tm.get('prompt_per_second',0.0),'wall_s':time.time()-t,'draft_n':tm.get('draft_n'),'draft_accepted':tm.get('draft_n_accepted')})
out={'runs':rows,'median_decode_tps':statistics.median(x['decode_tps'] for x in rows),'median_wall_s':statistics.median(x['wall_s'] for x in rows)}
print(json.dumps(out))
