# Cloud9 chimera opt-in Vulkan on CT410 — 2026-10-24

Deployment is real and verified on the existing native route: CT410 http://192.168.1.219:8090/v1/models exposes Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB alongside eight original models. OmniRoute Cloud9 llama-cpp provider points to that same API. User must explicitly select the new ID: it is NOT part of default Cloud9-Engine combo.

Native engine build is lab-releases/chimera-master9ae-turbo-policy-vulkan-20261024/native-adaptive-vulkan-lab, CI archive SHA 2245285096919f4f638ca92ed549fc3744cb1743b9755760668bfb97b00c8ccc. LAB ELF binaries use native $ORIGIN RUNPATH rather than a wrapper or global LD_LIBRARY_PATH.

Native route SHA 2ce83aed1f1a54a7e14e295838d34f7d05d1fc7dac4554341e34d296fdc31262. Model catalog SHA 82581f2315ef7e95ab5cf6937cc0781a5531d89fdb4a00734dbb0502a3a2a288.

Only the opt-in chimera profile uses threads=6, threads_batch=6, batch=256, ubatch=256, context=2048, inline MTP, f16 KV. Eight existing models retain threads8 and their current batch settings. The native router source change uses m.get to select per-model threads, with previous defaults unchanged.

Measured real routed single-tool benchmark: 777 input tokens prefill at 394.8046 tok/s, 32 generated tokens at 33.7565 tok/s, 5.369s wall (includes cold load), correct read-only pve.get_ct_config with strict JSON and no real tool execution. Previous non-tuned router model delivered 8.872 tok/s. Compiled MMB+TurboQuant components are not claimed GPU QA-certified; the runtime uses f16 KV and MTP.

Rollback copies: CT410 lab-releases/router-official-guardian-20261024/cloud9-model-router.backup-pre-threads-20261024 and model-catalog.backup-pre-threads-20261024.json. For removing only the opt-in model, edit catalog on the PVE HOST using atomic replacement, preserve all other entries, remove only its model ID and backend symlink and restart only cloud9-engine-router.service. The CT410 data mount is idmapped ZFS: atomic catalog rename inside the CT returned EOVERFLOW; never use the broken CT-local installation path. Use host filesystem for catalog atomic writes.

Keep full PVE gpu-memory-guard checks, VoiceStudio/AutoSubs idle coexist safety and the GPU file lock. Do not automatically move agents onto the opt-in route until broader tool/8K/concurrent workload QA. Evidence in Sources/Worklogs/2026-10-24_2358_CHIMERA_ENGINE_OPENBMB_LIVE.md and seven JSON files in Sources/Benchmarks/Engine-Tournament/2026-10-24/Cloud9_Chimera_OpenBMB.
