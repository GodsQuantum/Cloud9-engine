#!/usr/bin/env python3
"""Evidence-backed, unqualified Cloud9 CT410 2K LAB scoreboard."""
from __future__ import annotations
import argparse,hashlib,json,statistics
from pathlib import Path
from datetime import datetime,timezone
DEFAULT_BASE=Path('/srv/storage/nvme/DEV/Projets/HomeLab/Moteurs IA/Sources/Benchmarks/Engine-Tournament/2026-10-24')
DEFAULT_OUTPUT=DEFAULT_BASE.parents[2]/'Worklogs'
NAMES=('production','vulkan9ff','hipoff','hipon','hipf32')
def build(base):
    grouped={n:[] for n in NAMES};excluded=[];paired=[]
    files=sorted(base.glob('nvme-lite-*/results.json'))
    for file in files:
        doc=json.loads(file.read_text())
        accepted={}
        for row in doc.get('rows',[]):
            name=row.get('name')
            if name not in NAMES:
                excluded.append({'file':str(file),'backend':name,'why':'UNKNOWN_BACKEND'});continue
            speed=row.get('speed_tps') or {}
            log=Path(row.get('log') or '')
            valid=(row.get('pass') is True and row.get('return_code')==0
              and row.get('reason') is None
              and all(isinstance(speed.get(k),(float,int)) and speed[k]>0 for k in ('pp','tg'))
              and log.parent.resolve()==file.parent.resolve() and log.is_file()
              and len(row.get('sha256_log',''))==64
              and hashlib.sha256(log.read_bytes()).hexdigest()==row['sha256_log'])
            if not valid:
                excluded.append({'file':str(file),'backend':name,
                    'why':row.get('reason') or 'INVALID_PROVENANCE_OR_INCOMPLETE'})
                continue
            v={'name':name,'prefill_tps':float(speed['pp']),'generate_tps':float(speed['tg']),
                'trial_json':str(file),'raw_log_path':str(log),'raw_log_sha256':row['sha256_log'],
                'peak_temperature_c':row.get('max_temp_c'),
                'max_memory_psi':row.get('max_memory_psi_full_avg10')}
            grouped[name].append(v);accepted[name]=v
        if 'production' in accepted:
            prod=accepted['production']
            for name,v in accepted.items():
                if name=='production':continue
                paired.append({'challenger':name,'trial_json':str(file),
                   'production_tg':prod['generate_tps'],'challenger_tg':v['generate_tps'],
                   'generation_delta_pct':round(100*(v['generate_tps']/prod['generate_tps']-1),2),
                   'production_pp':prod['prefill_tps'],'challenger_pp':v['prefill_tps'],
                   'prefill_delta_pct':round(100*(v['prefill_tps']/prod['prefill_tps']-1),2)})
    summaries=[]
    for name in NAMES:
        vals=grouped[name]
        if not vals:continue
        tg=[v['generate_tps'] for v in vals];pp=[v['prefill_tps'] for v in vals]
        summaries.append({'engine':name,'samples':len(vals),
          'prefill_median':round(statistics.median(pp),2),
          'prefill_range':[min(pp),max(pp)],
          'generate_median':round(statistics.median(tg),2),
          'generate_range':[min(tg),max(tg)],'trials':vals})
    return {'title':'Cloud9 2K exploratory Qwen4B LAB scorecard',
      'generated_utc':datetime.now(timezone.utc).isoformat(),
      'production_eligible':False,'certified':False,'full_16k_qualified':False,
      'five_needle_qualified':False,'flash_next_gt20_qualified':False,
      'hall_of_fame_unchanged':True,
      'caveats':['Only 2048 context capacity; not 16K prompt ingestion',
      'GPU benchmark is exposed to concurrent USB/NFS scrub I/O stalls',
      'Prefill strongly affected by cold/warm cache and test order',
      'Accepted rows are exited-zero with raw logs hash matching and no watchdog abort',
      'CLI timing output lacks reliable observed token counts',
      'No 36-scenario JSON/tool/code/French quality QA and no production promotion'],
      'files':len(files),'valid_runs':sum(len(v) for v in grouped.values()),
      'excluded_runs':len(excluded),'summaries':summaries,
      'paired':paired,'excluded':excluded}
def markdown(j):
    lines=['# Qwen4B 2K benchmark — LAB only', '',
      '**NOT CERTIFIED — production unchanged.**','',
      '| Engine | Passed runs | PP median tok/s | TG median tok/s |',
      '|---|---:|---:|---:|']
    for v in j['summaries']:
        lines.append(f"| {v['engine']} | {v['samples']} | {v['prefill_median']} | {v['generate_median']} |")
    lines+=['','## Same-session pairs']
    for p in j['paired']:
        lines.append(f"- {p['challenger']}: PP {p['prefill_delta_pct']:+.2f}%, TG {p['generation_delta_pct']:+.2f}% compared with production; {p['trial_json']}")
    lines+=['','## Caveats']
    for s in j['caveats']:lines.append('- '+s)
    lines+=['','## SHA-bound log evidence']
    for row in j['summaries']:
        for v in row['trials']:
            lines.append(f"- {v['name']}: pp={v['prefill_tps']}, tg={v['generate_tps']}, SHA256={v['raw_log_sha256']}, log={v['raw_log_path']}")
    lines+=['',f"{j['valid_runs']} clean samples; {j['excluded_runs']} rejected; {j['files']} session files."]
    return '\n'.join(lines)+'\n'
def main():
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,default=DEFAULT_BASE)
    p.add_argument('--output-dir',type=Path,default=DEFAULT_OUTPUT,
                   help='Write to CT700 DEV worklogs, never root-owned benchmark run directory')
    p.add_argument('--write',action='store_true')
    a=p.parse_args();doc=build(a.base)
    print(json.dumps({'valid':doc['valid_runs'],'excluded':doc['excluded_runs'],
      'summary':[{k:v for k,v in row.items() if k!='trials'} for row in doc['summaries']],
      'paired':doc['paired']},indent=2))
    if a.write:
        if not a.output_dir.is_dir():
            raise RuntimeError('OUTPUT_DIR_NOT_FOUND '+str(a.output_dir))
        (a.output_dir/'2026-10-24_LAB_2K_SCORECARD.json').write_text(
            json.dumps(doc,indent=2,ensure_ascii=False)+'\n')
        (a.output_dir/'2026-10-24_LAB_2K_SCORECARD.md').write_text(markdown(doc))
if __name__=='__main__':main()
