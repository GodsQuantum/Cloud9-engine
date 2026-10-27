#!/usr/bin/env python3
"""MoE upstream on-device benchmark; aborts BEFORE model load if coexistence is unsafe."""
from __future__ import annotations
import argparse,fcntl,hashlib,json,os,pathlib,socket,subprocess,threading,time,urllib.request,urllib.error
from pathlib import Path

MODELS={
 "pym":Path("/srv/lxc/ia-compute/data/models/qwen36-pym-q2-mtp/Qwen3.6-35B-A3B-Pym-Q2-MTP.gguf"),
 "flash_alternate":Path("/srv/lxc/ia-compute/data/models/strata/coder-iq1m/Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00001-of-00002.gguf"),
 "flash_ad427":Path("/srv/storage/nvme/shared/ai-models/llm/gguf/FlashNext-AD427/Qwen3.8-Flash-Next-AD-4.27bpw-Q4_K_M-M64/Qwen3.8-Flash-Next-AD-4.27bpw-Q4_K_M-M64-00001-of-00033.gguf"),
 "lfm_official_q4":Path("/srv/lxc/ia-compute/data/models/lab-candidates/lfm25-a1b-official-q4/LFM2.5-8B-A1B-Q4_K_M.gguf"),
 "pym_heretic":Path("/srv/lxc/ia-compute/data/models/variants-20260914/heretic-mtp-icompact/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-Compact.gguf"),
}
BINARIES={
 "atomic16":Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/releases/atomic-044dff242d78/bin/llama-server"),
 "atomic17":Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/releases/atomic-99279d982f77/bin/llama-server"),
 "upstream_b11840":Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/upstream-master36e-vulkan-gfx1103-20261023/bin/llama-server"),
 "upstream_b11844":Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/upstream-master062-vulkan-gfx1103-20261023/llama-server"),
 "atomic2":Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/atomic2-vulkan-lab-20261025/bin/llama-server"),
 "atomic2_zen4_lto":Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/atomic2-zen4-lto-lab-20261026/bin/llama-server"),
}
GUARD=("192.168.1.200",19755)
LOCK=Path("/run/cloud9-gpu.lock")
URL="http://127.0.0.1:18139"
ROUTER="http://192.168.1.219:8090/health"
AUTOSUBS="http://192.168.1.219:8007/health"
LAB=Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/local-agent-readiness-20261024")
EMBED_SLOTS="http://192.168.1.219:8091/slots"
PROMPTS=[
 ("math","Calcule 25 × 37, puis explique en français différentes méthodes de vérification, étape par étape, avec exemples complémentaires."),
 ("code","Écris une fonction Python déterministe qui fusionne plusieurs itérateurs déjà triés et fournis des tests unitaires pour entrées vides, doublons et nombres négatifs."),
 ("fr","Explique en français comment une équipe peut diagnostiquer une panne intermittente sur un serveur, sans commander d'actions destructives, avec hypothèses et tests en lecture seule."),
]
def fetch(url,payload=None,timeout=4):
 body=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
 with urllib.request.urlopen(urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"} if body else {}),timeout=timeout) as r:
  return json.load(r)

def guardian(gib):
 # Host-only launch binds to loopback (official guard allows 127.0.0.1).
 # CT410 launches keep the natural 192.168.1.219 source. Never change guard ACL.
 source=os.environ.get("CLOUD9_GUARD_SOURCE_IP","")
 if source not in ("","127.0.0.1"):raise ValueError("UNAUTHORIZED_GUARD_SOURCE")
 with socket.create_connection(GUARD,timeout=4,source_address=("127.0.0.1",0) if source else None) as s:
  s.settimeout(4);s.sendall(f"CHECK coexist-light {gib:.2f}\n".encode());return json.loads(s.recv(16000))

def embeddings_busy():
 # Unlike the old router bug, any unknown/invalid slot state must fail CLOSED.
 try:
  slots=fetch(EMBED_SLOTS,timeout=3)
  if not isinstance(slots,list) or not slots:return True
  for slot in slots:
   if not isinstance(slot,dict):return True
   if slot.get("is_processing") is True or slot.get("state")=="processing":return True
   if "is_processing" not in slot and slot.get("state") not in ("idle","available"):return True
  return False
 except (OSError,ValueError,TypeError,KeyError):
  return True

def host_temp():
 best=[]
 for name in Path("/sys/class/hwmon").glob("hwmon*/name"):
  if name.read_text().strip() not in ("k10temp","amdgpu"):continue
  root=name.parent
  for p in root.glob("temp*_input"):
   try:best.append(float(p.read_text())/1000)
   except Exception:pass
 return max(best) if best else None

def psi_io_full():
 import re
 found=__import__("re").search(r"full avg10=([\d.]+)",Path("/proc/pressure/io").read_text())
 return float(found.group(1)) if found else None

def preflight(model_key,engine,mode,profile="full",preset="explore",parity_load_mode="mmap",owner_fullgpu=False,kv_type="f16"):
 # Hardware fail-closed: Native -lm none led to RADV vk::Queue::submit
 # ErrorDeviceLost while loading Pym 35B fullGPU on Oct26; not retry.
 # This is not a performance score and is no basis for ranking Atomic2.
 if preset==PARITY_PRESET and model_key=="pym" and parity_load_mode=="none":
  return {"admitted":False,
          "reasons":["PYM_FULL_GPU_NOMMAP_RADV_DEVICE_LOST_20261026_DO_NOT_RETRY"],
          "historical_parity_comparable":False,
          "native_mmap_preserved":False}
 p=MODELS[model_key];b=BINARIES[engine]
 assert p.is_file() and b.is_file()
 if mode in ("mtp1","mtp2","mtp3","mtp4","mtp6","mtp_adaptive") and model_key not in ("pym","pym_heretic"):
  return {"admitted":False,"reasons":["NON_PYM_INLINE_MTP_UNVERIFIED"]}
 if mode=="mtp_adaptive" and not engine.startswith("atomic2"):
  return {"admitted":False,"reasons":["ADAPTIVE_MTP_NOT_SUPPORTED_UPSTREAM"]}
 if model_key=="lfm_official_q4":
  # Inference proceeds ONLY after the download was pinned by SHA256.
  if p.stat().st_size!=5155564768:
   return {"admitted":False,"reasons":["MODEL_DOWNLOAD_INCOMPLETE_OR_UNVERIFIED"]}
 if model_key=="flash_ad427":
  # Exact historic TARGET weights found on read-only shared NVMe, not CT410's
  # different GSQ-RCO IQ1_M. This is a metadata-only admission, never GPU.
  # A historical 17.878 t/s recreation requires the separate Q8 FR-Spec
  # draft and a high-memory native launch policy; neither is configured yet.
  directory=p.parent
  draft=directory.parent/"MTP"/"mtp-Qwen3.8-Flash-Next-Q8_0-frspec-65k.gguf"
  draft_bytes=draft.stat().st_size if draft.is_file() else 0
  # Provenance pinned to drluoto HF revision ac875a98; full SHA-256 was
  # independently verified on 2026-10-26. No 3.64GB rehash per preflight.
  draft_expected_sha256="c9c505c1f68f008827a29733d5d2fe40a8170c324c676168831798b05217df4f"
  shards=sorted(directory.glob("Qwen3.8-Flash-Next-AD-4.27bpw-Q4_K_M-M64-*-of-00033.gguf"))
  indices={int(x.name.rsplit("-of-",1)[0][-5:]) for x in shards}
  complete=(len(shards)==33 and indices==set(range(1,34)) and
            sum(x.stat().st_size for x in shards)==94525394976)
  return {"admitted":False,"reasons":([] if complete else ["FLASH_AD427_SHARDS_INCOMPLETE"])+[
          "FLASH_AD427_QWEN4EXP_D2T_SCATTER_UNSUPPORTED_IN_ATOMIC2", "FLASH_AD427_MEMORY_NOT_ADMITTED"],
          "historic_target_gguf_found":complete,"historical_17_878_tps_comparable":False,
          "actual_sharded_bytes":sum(x.stat().st_size for x in shards),
          "expected_sharded_bytes":94525394976,"expected_shards":33,
          "sha256_verified":False,
          "fr_spec_sidecar_present":draft.is_file(),
          "fr_spec_sidecar_size_verified":draft_bytes==3639245152,
          "fr_spec_sidecar_bytes":draft_bytes,
          "fr_spec_draft_vocab":65536,
          "fr_spec_trunk_vocab":248320,
          "fr_spec_d2t_mapping_entries":65536,
          "qwen4exp_d2t_native_support_qualified":False,
          "fr_spec_sidecar_expected_sha256":draft_expected_sha256,
          "fr_spec_sidecar_revision":"ac875a98457a8effe8fb83de8f3701421f507a24",
          "note":"Full SHA of 33/33 shards verified separately 2026-10-26; draft's 65K d2t mapping vs 248320 trunk vocab is not supported by native Qwen4Exp code in current Atomic2 b10298. Requires native compatibility patch and QA, then 54-56GB resident RAM admission. Zero GPU runs."}
 if model_key=="flash_alternate":
  # Strata GSQ-RCO IQ1_M is NOT the historical AD-4.27 + FR-Spec GGUF:
  # refusing a falsely matched benchmark, regardless of available RAM.
  shards=sorted(p.parent.glob("Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-*-of-00002.gguf"))
  assert len(shards)==2
  return {"admitted":False,"reasons":["FLASH_UNMATCHED_HISTORICAL_MODEL"],
          "actual_sharded_bytes":sum(x.stat().st_size for x in shards),
          "historical_17_878_tps_comparable":False,
          "note":"Separate GSQ-RCO/Strata quantization is not historical Flash-Next AD-4.27+FR-Spec"}
 gguf_gib=p.stat().st_size/(1024**3)
 # These are policy projections, not measured GPU allocations.
 # Partial: mmap CPU experts with very limited GPU layers. The official
 # guardian still mandates its 24GiB minimum, and runtime watchdog stays on.
 if model_key=="lfm_official_q4":
  # Tiny-context candidate is scored only against itself on both binaries.
  # Same official GPU guardian, thermal/PSI watchdog and exclusive lock.
  floor=25.0 if profile=="compact" else max(25.6,round(gguf_gib+20.5,2))
  required_gtt=5.5 if profile=="compact" else 6.5
 else:
  # Historical FULL GPU strict parity: don't DOUBLE reserve the weight size
  # and 23 extra GiB: the official GPU guardian already accounts for its
  # host_reserve_gib=18.0 and independently admits/rejects GTT allocation.
  # Keep the older ultra-conservative rule for exploratory profiles.
  if profile=="full" and preset==PARITY_PRESET:
   # Prior Pym35B load dropped MemAvailable 31.7 -> 23.7 GiB,
   # host PSI.full=4.61 before decode: require real spare load margin.
   floor=max(round(gguf_gib+18.0,2),round(gguf_gib+25.0,2))
  else:
   floor=round(gguf_gib+23.0,2) if profile=="full" else 24.4
  if profile=="partial_mid":
   floor=max(floor,29.0)
  if profile=="partial_high":
   floor=max(floor,30.5)
  required_gtt={"full":14.0,"partial":6.0,"partial_mid":10.0,"partial_high":12.0,"partial_min":2.75}[profile]
  if owner_fullgpu and profile=="full" and model_key=="pym":
   # Opt-in from user, native GPU guardian retains independent veto.
   # Do not double-reserve model GGUF and GPU host-reserve; safety comes
   # from native 18-GiB host reserve, 20.5GiB runtime floor, 95% swap.
   floor=max(29.0,round(gguf_gib+16.0,2))
   required_gtt={"f16":13.5,"q8_0":13.0,"turbo2":12.5,"turbo3":12.7,"turbo4":12.5}.get(kv_type,14.0)
 g=guardian(required_gtt)
 io=psi_io_full()
 t=host_temp()
 why=[]
 if not g.get("allow"):why.append("OFFICIAL_GPU_GUARD_DENIED")
 if g.get("mem_available_gib",0)<floor:
  why.append("PYM_PRIOR_PSI_LOAD_HEADROOM" if preset==PARITY_PRESET and model_key=="pym" and profile=="full" else "MODEL_SIZE_PLUS_PRODUCTION_RAM_RESERVE")
 if g.get("safe_total_gtt_gib",0)<required_gtt:why.append("INSUFFICIENT_GTT_FOR_MATCHED_FULL_OFFLOAD")
 if g.get("psi_memory_full_avg10",99)>=(1.5 if owner_fullgpu else 0.30):why.append("HOST_MEMORY_PSI")
 if io is None or io>=9:why.append("HOST_IO_PSI")
 if t is None or t>=76:why.append("TEMPERATURE_PREFLIGHT")
 try:
  if fetch(ROUTER,timeout=3).get("worker_model") is not None:why.append("ROUTER_WORKER_ACTIVE")
 except Exception:why.append("ROUTER_HEALTH_UNREACHABLE")
 if embeddings_busy():why.append("EMBEDDINGS_ACTIVE_OR_UNKNOWN")
 try:
  autosubs=fetch(AUTOSUBS,timeout=3)
  if autosubs.get("status")!="ok" or autosubs.get("loaded_models")!=[]:why.append("AUTOSUBS_GPU_IN_USE_OR_HEALTH_UNKNOWN")
 except Exception:why.append("AUTOSUBS_GPU_HEALTH_UNREACHABLE")
 return {"admitted":not why,"reasons":why,"model_bytes":p.stat().st_size,"model_name":p.name,
         "binary_sha256":hashlib.sha256(b.read_bytes()).hexdigest(),
         "min_available_gib":floor,"required_gtt_gib":required_gtt,"profile":profile,
         "guardian":{k:g.get(k) for k in ("allow","mem_available_gib","psi_memory_full_avg10","swap_used_percent","safe_total_gtt_gib","reasons")},
         "host_io_full_avg10":io,"max_host_gpu_temp_c":t,
         "note":"Flash GSQ-RCO is NOT the historical AD-4.27 + FR-Spec; invalid historical speed comparison"}

# PHASE ZERO: historic winning feature cocktail MUST be kept before tuning engines.
# Atomic1.6 binary is available: build10709 c044dff24. Its historical
# 2026-09-11 benchmark command is not fully archived; 2026-10-02 upstream
# fast fullGPU precise flags are used for a SHARED reconstructed protocol.
# Atomic1.6 2026-09-11 HOF only specifies Pym Q2 + MTP2 + f16 KV, not its full CLI.
# Exact October-02 fully documented upstream full-GPU command supplies launcher
# optimization flags: ngl99/c16384/b1024/ub1024/t8/poll100/poll-batch0.
# This is a RECONSTRUCTED parity preset, NOT a claim of exact Atomic1.6 CLI.
PARITY_PRESET="atomic16-mtp2-f16-fullgpu"
HOF_PYM_KV_ORDER=("f16","turbo4","q8_0","turbo3")
HOF_PYM_TPS={"f16":36.28,"turbo4":35.20,"q8_0":35.07,"turbo3":34.40}
PARITY_FEATURES=("GPU_full_99","CPU_MoE_off_0","inline_MTP2",
                 "KV_f16_both","FlashAttention_on","mmap",
                 "batch1024","ubatch1024","threads8",
                 "poll100_batch0","spec_pmin_zero","no_backend_sampling",
                 "prompt_cache_off","no_warmup","reasoning_off")
PARITY_REQUIRED_HELP=("--poll", "--poll-batch", "--spec-draft-p-min",
                      "--no-spec-draft-backend-sampling", "--n-cpu-moe",
                      "--spec-type", "--spec-draft-n-max", "--no-cache-prompt")
def parity_extra_flags(engine,help_text=None,load_mode="mmap"):
 if engine not in BINARIES:raise ValueError("Unknown engine")
 if load_mode not in ("mmap","none"):raise ValueError("Unsupported load mode")
 if help_text is not None:
  unavailable=[flag for flag in PARITY_REQUIRED_HELP if flag not in help_text]
  if unavailable:raise ValueError("PARITY_FEATURE_MISSING:"+",".join(unavailable))
 # All 3 binaries support native same-function flags; upstream additionally
 # requires explicit lazy-mode off; Atomic2 has no lazy-mode flag, so no
 # unsupported synthetic knob is passed.
 extra=["-lm",load_mode,"--poll","100","--poll-batch","0",
        "--no-cache-prompt","--spec-draft-p-min","0",
        "--no-spec-draft-backend-sampling","--reasoning-budget","0",
        "--jinja"]
 if engine.startswith("upstream"):
  if help_text is not None and "--lazy-mode" not in help_text:
   raise ValueError("PARITY_UPSTREAM_LAZY_MODE_FLAG_MISSING")
  extra.extend(["--lazy-mode","off"])
 return extra

def stop_own(proc):
 if proc is None or proc.poll() is not None:return
 proc.terminate()
 try:proc.wait(timeout=4)
 except subprocess.TimeoutExpired:
  proc.kill();proc.wait(timeout=6)

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--engine",choices=sorted(BINARIES),required=True)
 ap.add_argument("--model",choices=sorted(MODELS),required=True)
 ap.add_argument("--mode",choices=["base","mtp1","mtp2","mtp3","mtp4","mtp6","mtp_adaptive"],required=True)
 ap.add_argument("--profile",choices=["full","partial","partial_mid","partial_high","partial_min","compact"],default="full")
 ap.add_argument("--preset",choices=["explore",PARITY_PRESET],default="explore",
                 help="Baseline copied to ALL engines before feature ablation; requires fullGPU Pym MTP2")
 ap.add_argument("--parity-context",type=int,choices=[8192,16384],default=16384,
                 help="16K documented Oct02 baseline; 8K secondary fallback CHANGING ONLY context on every engine")
 ap.add_argument("--parity-load-mode",choices=["mmap","none"],default="mmap",
                 help="Baseline mmap. Phase1 native ablation: none, same option across every compared engine.")
 ap.add_argument("--parity-kv",choices=HOF_PYM_KV_ORDER,default="f16",
                 help="Same GGUF Pym MTP2 HOF: f16=36.28, turbo4=35.20, q8_0=35.07, turbo3=34.40 (historical Atomic1.6)")

 ap.add_argument("--run-id",required=True)
 ap.add_argument("--max-output-tokens",type=int,choices=[128,192,256,384,768],default=768,
                 help="Fix equal output cap for a cross-engine Pym matched protocol")
 ap.add_argument("--thinking-budget",type=int,choices=[0,128,256],default=256,
                 help="Native LFM reasoning budget (same for both engines); 0 tests short-response agent tool suitability")
 ap.add_argument("--tune-kv",choices=["f16","q8_0","turbo2","turbo3","turbo4"],default="f16",
                 help="A/B both KV buffers on Atomic2 for Pym; strict single-variable trials")
 ap.add_argument("--tune-moe-cache",choices=["default","off","auto","soft","on"],default="default",
                 help="Native Atomic2 CPU MoE expert cache optimization")
 ap.add_argument("--tune-gdn-replay",action="store_true",
                 help="Atomic2 native GDN replay opt-in with quality verification")
 ap.add_argument("--tune-spec-chain",type=int,choices=[0,2,3],default=0)
 ap.add_argument("--owner-fullgpu",action="store_true",help="User authorized Pym35 full-GPU benchmark, with native GPU guardian and OOM watchdog intact")
 ap.add_argument("--owner-load-mode",choices=["mmap","dio"],default="mmap")
 ap.add_argument("--tune-hof-native-flags",action="store_true",help="Native polling + speculative backend sampling off from HOF")
 ap.add_argument("--owner-kv-unified",action="store_true")
 ap.add_argument("--owner-no-repack",action="store_true")
 ap.add_argument("--owner-ubatch",type=int,choices=[128,512,1024],default=128)
 ap.add_argument("--owner-affinity",choices=["none","0-7","8-15"],default="none")
 ap.add_argument("--owner-priority",type=int,choices=[0,1],default=0)
 ap.add_argument("--owner-draft-p-min",type=float,choices=[0.0,0.5,0.75,0.9],default=0.0,help="Native GPU inline MTP minimum draft confidence threshold")
 ap.add_argument("--owner-vulkan-kernel",choices=["auto","force_mmvq","disable_mmvq","no_coopmat","no_async"],default="auto",help="Native ggml Vulkan env kernel A/B in isolated owner fullGPU trial")
 ap.add_argument("--execute",action="store_true")
 ap.add_argument("--tasks",default="math,code,fr",
                 help="Comma-separated subset of original immutable prompts; e.g. code,fr resumes an interrupted parity baseline")
 a=ap.parse_args()
 if a.tune_hof_native_flags and a.owner_draft_p_min!=0.0:
  ap.error("HOF p-min=0 cannot be combined with confidence ablation")
 if a.tune_hof_native_flags and not a.owner_fullgpu:
  ap.error("HOF native ablation only with owner approved fullGPU")
 if not a.owner_fullgpu and (a.owner_kv_unified or a.owner_no_repack or a.owner_ubatch!=128 or a.owner_affinity!="none" or a.owner_priority!=0 or a.owner_draft_p_min!=0.0 or a.owner_vulkan_kernel!="auto"):
  ap.error("GPU ablation requires owner fullGPU")
 if a.owner_load_mode=="dio":
  ap.error("GPUVM device lost in DirectIO Pym35 native Vulkan, blocked")
 if a.owner_load_mode!="mmap" and not a.owner_fullgpu:
  ap.error("DirectIO only in owner-authorized full GPU")
 if a.owner_fullgpu and not (a.engine in ("atomic2","atomic2_zen4_lto","atomic16","atomic17","upstream_b11844") and a.model=="pym" and a.mode in ("mtp1","mtp2","mtp3","mtp4","mtp6","mtp_adaptive","base") and a.profile=="full"):
  ap.error("Owner fullGPU approval is specific to Pym35 Atomic2 MTP2")
 if a.tune_gdn_replay:
  ap.error("GDN replay only supports CPU/CUDA, not the CT410 Vulkan runtime")
 if a.tune_spec_chain and (a.engine not in ("atomic2","atomic2_zen4_lto") or a.model not in ("pym","pym_heretic") or a.mode not in ("mtp2","mtp3") or a.preset==PARITY_PRESET):
  ap.error("Spec-chain only tested on exploratory Atomic2 Pym MTP2/3")
 if a.engine not in ("atomic2", "atomic2_zen4_lto", "atomic16") and ((a.tune_kv not in ("f16","q8_0") or a.tune_kv=="q8_0" and a.engine not in ("atomic17","upstream_b11844")) or a.tune_moe_cache!="default" or a.tune_gdn_replay):
  ap.error("Atomic2 native feature ablations are not certified on another engine")
 if a.preset==PARITY_PRESET and (a.tune_kv!="f16" or a.tune_moe_cache!="default" or a.tune_gdn_replay):
  ap.error("Historical parity features must remain untouched; use separate exploratory runs")
 if a.model not in ("pym","pym_heretic") and (a.profile in ("partial_mid","partial_high") or a.tune_kv!="f16" or a.tune_moe_cache!="default" or a.tune_gdn_replay):
  ap.error("Feature matrix restricted to actual Pym MoE models")
 if not a.tasks or any(x not in {"math","code","fr"} for x in a.tasks.split(",")) or len(set(a.tasks.split(",")))!=len(a.tasks.split(",")):
  ap.error("tasks must be a unique subset of math,code,fr")
 selected_prompts=[x for x in PROMPTS if x[0] in a.tasks.split(",")]
 if a.preset==PARITY_PRESET and not (a.model=="pym" and a.mode=="mtp2" and a.profile=="full"):
  ap.error("Historic feature-parity preset requires --model pym --mode mtp2 --profile full")
 if a.preset!=PARITY_PRESET and a.parity_kv!="f16":
  ap.error("--parity-kv requires HOF feature-parity preset")
 if a.preset!="atomic16-mtp2-f16-fullgpu" and a.parity_context!=16384:
  ap.error("--parity-context only applies to the identical-features historical parity preset")
 if a.preset!=PARITY_PRESET and a.parity_load_mode!="mmap":
  ap.error("--parity-load-mode only applies to a historical fullGPU parity trial")
 if not(1<=len(a.run_id)<=45 and all(c.isalnum() or c in "-_" for c in a.run_id)):ap.error("invalid immutable run-id")
 report=LAB/("moe_upstream_"+a.run_id+".json")
 logfile=LAB/("moe_upstream_"+a.run_id+".log")
 if report.exists() or logfile.exists():ap.error("REFUSE_OVERWRITE_IMMUTABLE_TRIAL")
 result={"run_id":a.run_id,"engine":a.engine,"model":a.model,"mode":a.mode,"executed":False,
         "default_production_unchanged":True,"profile":a.profile,"thinking_budget":a.thinking_budget,
         "max_output_tokens":a.max_output_tokens,"preset":a.preset,"owner_fullgpu":a.owner_fullgpu,"owner_load_mode":a.owner_load_mode,"tune_hof_native_flags":a.tune_hof_native_flags,"owner_kv_unified":a.owner_kv_unified,"owner_no_repack":a.owner_no_repack,"owner_ubatch":a.owner_ubatch,"owner_affinity":a.owner_affinity,"owner_priority":a.owner_priority,"owner_draft_p_min":a.owner_draft_p_min,"owner_vulkan_kernel":a.owner_vulkan_kernel,
         "spec_chain":a.tune_spec_chain,
         "native_feature_ablation":{"kv_type":a.tune_kv,"moe_cache":a.tune_moe_cache,"gdn_replay":a.tune_gdn_replay},
         "parity_context":a.parity_context if a.preset==PARITY_PRESET else None,
         "parity_load_mode":a.parity_load_mode if a.preset==PARITY_PRESET else None,
         "parity_kv":a.parity_kv if a.preset==PARITY_PRESET else None,
         "hof_atomic16_reference_tps":HOF_PYM_TPS.get(a.parity_kv) if a.preset==PARITY_PRESET else None,
         "selected_tasks":[x[0] for x in selected_prompts],"rows":[]}
 def save():report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
 try:
  start=preflight(a.model,a.engine,a.mode,a.profile,a.preset,a.parity_load_mode,a.owner_fullgpu,(a.parity_kv if a.preset==PARITY_PRESET else a.tune_kv))
  result["preflight"]=start
  result["status"]="blocked_preflight" if not start["admitted"] else "eligible_not_executed"
  if not a.execute or not start["admitted"]:
   save();print(json.dumps({"status":result["status"],"reasons":start.get("reasons"),"path":str(report)}));return
  fd=os.open(str(LOCK),os.O_CREAT|os.O_RDWR,0o660);child=None;flag=threading.Event();watcher=None
  try:
   try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:
    result["status"]="gpu_lock_busy";save();return
   second=preflight(a.model,a.engine,a.mode,a.profile,a.preset,a.parity_load_mode,a.owner_fullgpu,(a.parity_kv if a.preset==PARITY_PRESET else a.tune_kv))
   result["second_preflight"]=second
   if not second["admitted"]:
    result["status"]="blocked_after_lock";save();return
   bin=BINARIES[a.engine];model=MODELS[a.model]
   if a.profile=="compact" and a.model!="lfm_official_q4":
    raise ValueError("compact LFM profile cannot be applied to Pym without new admission")
   layers={"full":"99","partial":"8","partial_mid":"16","partial_high":"24","partial_min":"4","compact":"99"}[a.profile]
   experts={"full":"0","partial":"40","partial_mid":"36","partial_high":"32","partial_min":"41","compact":"0"}[a.profile]
   context=str(a.parity_context) if a.preset==PARITY_PRESET else ("8192" if a.profile=="full" else "2048")
   if a.model=="lfm_official_q4":
    context="1536" if a.profile=="compact" else "4096"
   bsize="1024" if a.preset==PARITY_PRESET else ("128" if a.profile in ("partial_min","compact") else "512")
   ubsize="1024" if a.preset==PARITY_PRESET else ("32" if a.profile=="compact" else ("64" if a.profile=="partial_min" else "128"))
   if a.owner_fullgpu and a.owner_ubatch!=128:ubsize=str(a.owner_ubatch)
   cmd=[str(bin),"-m",str(model),"-ngl",layers,"--n-cpu-moe",experts,"--fit","off","-c",context,
        "-np","1","-fa","on","-b",bsize,"-ub",ubsize,"-t","8","-tb","8",
        "-ctk",(a.parity_kv if a.preset==PARITY_PRESET else a.tune_kv),"-ctv",(a.parity_kv if a.preset==PARITY_PRESET else a.tune_kv),
        "--host","127.0.0.1","--port","18139","--no-webui",
        "--no-warmup","--reasoning",("on" if a.model=="lfm_official_q4" else "off"),"--alias","Cloud9-MoE-Upstream-LAB"]
   if a.tune_moe_cache!="default":
    cmd+=["--moe-cache",a.tune_moe_cache]
   if a.tune_gdn_replay:
    cmd+=["--gdn-replay"]
   if a.model=="lfm_official_q4":
    # Native llama.cpp reasoning controls: prevent a 256-token thinking-only
    # completion from incorrectly appearing to be a successful agent response.
    # Both upstream and Atomic use identical settings for this A/B profile.
    cmd += ["--reasoning-budget",str(a.thinking_budget),"--reasoning-format","deepseek"]
   if a.preset==PARITY_PRESET:
    support=subprocess.run([str(bin),"--help"],capture_output=True,text=True,timeout=18)
    if support.returncode!=0:raise RuntimeError("Unable to validate candidate native feature support")
    help_text=support.stdout+support.stderr
    if a.parity_kv.startswith("turbo") and a.parity_kv not in help_text:
     raise RuntimeError("PARITY_KV_UNSUPPORTED_BY_BINARY")
    cmd+=parity_extra_flags(a.engine,help_text,a.parity_load_mode)
    result["parity_features"]=[("KV_"+a.parity_kv+"_both" if f=="KV_f16_both" else ("load_mode_"+a.parity_load_mode if f=="mmap" else f)) for f in PARITY_FEATURES]
    result["changed_from_historical_baseline"]=(["load_mode: mmap -> none"] if a.parity_load_mode=="none" else []) + (["KV: f16 -> "+a.parity_kv] if a.parity_kv!="f16" else [])
    result["hof_exact_cli_not_archived"]=True
    result["parity_source"]={
      "atomic16_20260911":"model Qwen3.6-35B-A3B Pym Q2-MTP; inline MTP2; KV f16; median 36.28t/s (other flags not recorded)",
      "upstream_20261002":"Pym same GGUF ngl99 c16384 np1 b1024 ub1024 t8 tb8 FAon mmap poll100 pollbatch0 f16 KV, inline MTP2",
      "not_exact_atomic16_cli":True,
      "features_ported_first":True,
      "addon_tuning_already_tested":False}
   if a.owner_affinity!="none":cmd+=["--cpu-range",a.owner_affinity,"--cpu-range-batch",a.owner_affinity,"--cpu-strict","1","--cpu-strict-batch","1"]
   if a.owner_priority:cmd+=["--prio",str(a.owner_priority)]
   if a.owner_draft_p_min:cmd+=["--spec-draft-p-min",str(a.owner_draft_p_min)]
   if a.owner_kv_unified:cmd+=["--kv-unified"]
   if a.owner_no_repack:cmd+=["--no-repack"]
   if a.tune_hof_native_flags:
    cmd += ["--poll","100","--poll-batch","0","--spec-draft-p-min","0",
            "--no-spec-draft-backend-sampling","--no-cache-prompt"]
   if a.owner_load_mode=="dio":
    cmd+=["--load-mode","dio"]
   if a.tune_spec_chain:
    cmd+=["--spec-chain",str(a.tune_spec_chain)]
   if a.mode in ("mtp1","mtp2","mtp3","mtp4","mtp6"):
    cmd+=["--spec-type","draft-mtp","--spec-draft-n-max",a.mode[-1]]
   elif a.mode=="mtp_adaptive":
    cmd+=["--spec-type","draft-mtp-adaptive","--spec-draft-n-max","3"]
   result["cli_flags"]=cmd[1:][::] # distinct partial vs full profile, no secrets
   with logfile.open("x") as log:
    vulkan_env=os.environ.copy()
    vulkan_overrides={"force_mmvq":"GGML_VK_FORCE_MMVQ","disable_mmvq":"GGML_VK_DISABLE_MMVQ","no_coopmat":"GGML_VK_DISABLE_COOPMAT","no_async":"GGML_VK_DISABLE_ASYNC"}
    if a.owner_vulkan_kernel!="auto":vulkan_env[vulkan_overrides[a.owner_vulkan_kernel]]="1"
    child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=vulkan_env)
    result["status"]="loading";save()
    guard_events=[]
    mem_floor=(20.0 if a.owner_fullgpu else 20.5)
    def watch():
     while not flag.wait(2):
      try:
       if embeddings_busy():
        guard_events.append({"reason":"EMBEDDINGS_BECAME_BUSY_OR_UNKNOWN"});stop_own(child);return
       g=guardian(0);t=host_temp()
       if g.get("psi_memory_full_avg10",99)>=(12.0 if a.owner_fullgpu else 1.8) or g.get("mem_available_gib",0)<mem_floor or g.get("swap_used_percent",100)>95 or t is None or t>=80:
        guard_events.append({"reason":"RUNTIME_PRESSURE","guardian":g,"temp_c":t});stop_own(child);return
      except Exception as e:
       guard_events.append({"reason":"GUARD_UNAVAILABLE","error_type":type(e).__name__});stop_own(child);return
    watcher=threading.Thread(target=watch,daemon=True);watcher.start()
    ready=False;ts=time.monotonic()
    for _ in range(100):
     if child.poll() is not None or guard_events:break
     try:
      if fetch(URL+"/health",timeout=1).get("status")=="ok":ready=True;break
     except Exception:pass
     time.sleep(.6)
    result["load_s"]=round(time.monotonic()-ts,3)
    if not ready:
     result["status"]="failed_load_or_guard";result["guard_events"]=guard_events;save();return
    result["executed"]=True;result["status"]="running";save()
    for name,prompt in selected_prompts:
     # A brief PSI cooldown allows the GPU to settle after weight paging.
     # Neither the official pre-load guard nor emergency limits are bypassed:
     # the 2-second watchdog still terminates this OWN worker on hard pressure.
     psi_soft=(6.0 if a.owner_fullgpu else .5)
     for cooldown in range(8):
      if guard_events or child.poll() is not None:break
      if embeddings_busy():
       result["status"]="paused_embeddings_active";result["guard_events"]=guard_events;save();return
      g=guardian(0);temp=host_temp()
      result["latest_runtime_guard"]={k:g.get(k) for k in ("allow","mem_available_gib","psi_memory_full_avg10","swap_used_percent","safe_total_gtt_gib","reasons")}
      result["latest_runtime_temp_c"]=temp
      if g.get("psi_memory_full_avg10",99)<psi_soft and g.get("mem_available_gib",0)>=mem_floor and temp is not None and temp<78:
       break
      if g.get("psi_memory_full_avg10",99)>=(12.0 if a.owner_fullgpu else 1.8) or g.get("mem_available_gib",0)<mem_floor or temp is None or temp>=80:
       break
      if cooldown<7:time.sleep(2)
     if guard_events or child.poll() is not None or embeddings_busy() or g.get("psi_memory_full_avg10",99)>=psi_soft or g.get("mem_available_gib",0)<mem_floor or temp is None or temp>=78:
      result["status"]="paused_runtime_pressure";result["guard_events"]=guard_events;save();return
     ts=time.monotonic()
     payload={"model":"Cloud9-MoE-Upstream-LAB","temperature":0.2,"top_k":80,
              "repeat_penalty":1.05,"seed":42,
              "stream":False,"max_tokens":a.max_output_tokens,"messages":[{"role":"user","content":prompt}]}
     try:reply=fetch(URL+"/v1/chat/completions",payload,timeout=180)
     except Exception as e:
      result["status"]="failed_request";result["error_type"]=type(e).__name__;save();return
     usage=reply.get("usage") or {}
     timings=reply.get("timings") or {}
     choice=(reply.get("choices") or [{}])[0]
     msg=choice.get("message") or {}
     visible=msg.get("content") or ""
     visible=visible if isinstance(visible,str) else str(visible)
     reasoning=msg.get("reasoning_content") or ""
     result["rows"].append({"task":name,"wall_s":round(time.monotonic()-ts,3),
                           "prompt_tokens":usage.get("prompt_tokens"),"completion_tokens":usage.get("completion_tokens"),
                           "timings":timings,"finish_reason":choice.get("finish_reason"),
                           "message_fields":sorted(msg),
                           "reasoning_present":bool(str(reasoning).strip()),
                           "final_text_excerpt":visible[:1200],"final_text_sha256":hashlib.sha256(visible.encode()).hexdigest(),
                           "nonempty":bool(visible.strip()),
                           "math_answer_contains_925":("925" in visible) if name=="math" else None})
     save()
    math_rows=[x for x in result["rows"] if x["task"]=="math"]
    result["status"]="complete" if (len(result["rows"])==len(selected_prompts) and all(x["nonempty"] for x in result["rows"]) and
                             all(x["math_answer_contains_925"] for x in math_rows)) else "failed_quality"
    result["guard_events"]=guard_events;save()
  finally:
   flag.set();stop_own(child)
   if watcher:watcher.join(timeout=3)
   fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)
   if 'guard_events' in locals() and guard_events:
    result["status"]="failed_watchdog";result["guard_events"]=guard_events;save()
 except Exception as e:
  result["status"]="failed_exception";result["error_type"]=type(e).__name__;save();raise

if __name__=="__main__":main()
