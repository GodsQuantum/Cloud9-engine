#!/usr/bin/env python3
"""Read-only GGUF metadata: exact disk bytes by expert / n-gram / other."""
import json,struct
from pathlib import Path

ROOT=Path('/srv/storage/nvme/shared/ai-models/llm/gguf/FlashNext-AD427/Qwen3.8-Flash-Next-AD-4.27bpw-Q4_K_M-M64')
PREFIX='Qwen3.8-Flash-Next-AD-4.27bpw-Q4_K_M-M64-'

def tensor_table(path):
    with path.open('rb') as file:
        def u32():return struct.unpack('<I',file.read(4))[0]
        def u64():return struct.unpack('<Q',file.read(8))[0]
        def string():
            n=u64()
            if n>25_000_000:raise ValueError('GGUF key/string too big')
            return file.read(n).decode('utf-8','replace')
        def skip(t):
            sizes={0:1,1:1,2:2,3:2,4:4,5:4,6:4,7:1,10:8,11:8,12:8}
            if t in sizes:file.seek(sizes[t],1);return
            if t==8:file.seek(u64(),1);return
            if t==9:
                etype=u32();n=u64()
                if n>100_000_000:raise ValueError('Oversized GGUF metadata array')
                if etype in sizes:file.seek(sizes[etype]*n,1)
                else:
                    for i in range(n):skip(etype)
                return
            raise ValueError('Unsupported GGUF metadata type '+str(t))
        if file.read(4)!=b'GGUF':raise ValueError('Not a GGUF')
        version=u32();nt=u64();nk=u64();alignment=32
        if version!=3:raise ValueError('Unexpected GGUF version')
        for _ in range(nk):
            name=string();kind=u32()
            if name=='general.alignment' and kind==4:alignment=u32()
            else:skip(kind)
        tensor_metadata=[]
        for _ in range(nt):
            name=string();dims=u32();shape=[u64() for i in range(dims)];kind=u32();offset=u64()
            tensor_metadata.append((name,shape,kind,offset))
        data_start=((file.tell()+alignment-1)//alignment)*alignment
    out=[]
    for i,(name,shape,kind,offset) in enumerate(tensor_metadata):
        following=tensor_metadata[i+1][3] if i+1<len(tensor_metadata) else path.stat().st_size-data_start
        size=following-offset
        if size<0:raise ValueError('Bad GGUF tensor offsets')
        typ='ngram_table' if name=='per_layer_token_embd.weight' else ('MoE_expert_weights' if '_exps.weight' in name else 'other_weights')
        out.append({'name':name,'category':typ,'bytes':size,'shape':shape,'type':kind,'shard':path.name})
    return out

def analyze():
    files=sorted(ROOT.glob(PREFIX+'*-of-00033.gguf'))
    if len(files)!=33 or sum(f.stat().st_size for f in files)!=94525394976:
        raise RuntimeError('AD4.27 target shards missing or changed')
    rows=[]
    for file in files:rows.extend(tensor_table(file))
    totals={}
    for r in rows:
        a=totals.setdefault(r['category'],{'bytes':0,'tensors':0})
        a['bytes']+=r['bytes'];a['tensors']+=1
    for a in totals.values():a['GiB']=round(a['bytes']/2**30,3)
    return {'status':'GGUF_METADATA_INSPECTED_ONLY_NOT_MODEL_BENCHMARK',
            'source_files':len(files),'source_bytes':sum(f.stat().st_size for f in files),
            'total_tensors':len(rows),'classes':totals,
            'n_gram_tensor':next({'name':r['name'],'bytes':r['bytes'],'shape':r['shape'],'type':r['type']} for r in rows if r['category']=='ngram_table'),
            'exact_quantization_preserved':True,'GPU_execution_performed':False}

if __name__=='__main__':
    print(json.dumps(analyze(),indent=2))
