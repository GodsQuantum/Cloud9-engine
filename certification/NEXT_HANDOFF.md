# Handoff automatique Cloud9 Engine

Registre mis à jour: 2026-10-25

Moteur disponible: Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB

SHA routeur: 2ce83aed1f1a54a7e14e295838d34f7d05d1fc7dac4554341e34d296fdc31262
SHA catalogue: 82581f2315ef7e95ab5cf6937cc0781a5531d89fdb4a00734dbb0502a3a2a288
GitHub evidence snapshot count: 54; SHA validated without a running Cloud9 host.
Maintenir les combos OmniRoute actuels. Ne pas promouvoir ce LAB en défaut avant les gates restants.

## Certifié dans sa portée et A NE PAS REFAIRE

- C01 (HISTORICAL_VALID) Historique: noyau Vulkan MUL_MAT_ID 921/921: Cloud9 Engine 534cda00; NOT current master9ae chimera
- C02 (HISTORICAL_VALID) Historique: cinq aiguilles 8K réelles 3/3: Atomic TurboQuant 2.0.0 Qwen4 Q4_K_M Vulkan Q8K Turbo3V
- C03 (HISTORICAL_VALID) Historique: cinq aiguilles 16K réelles 3/3: Atomic TurboQuant 2.0.0 Qwen4 Q4_K_M Vulkan Q8K Turbo3V
- C04 (CURRENT_PASS_LIMITED) CI chimera native MMB MTP Turbo source / backend guard: Cloud9 chimera master9ae source Vulkan/HIP CPU build, NOT GPU TurboQuant
- C05 (CURRENT_PASS_LIMITED) CT410 router safe nonpreemptive, stable services: active 2026-10-25 CT410 guarded 9-model catalog; only one worker
- C06 (CURRENT_PASS_LIMITED) Chimera native Qwen4 real GPU 2K + strict read-only tool: opt-in Qwen4 Q4_K_M, MTP draft, Vulkan, f16 KV, ctx2048, threads6 batch256
- C07 (CURRENT_PASS_LIMITED) OpenBMB MiniCPM5+DSpark live speed and tool: MiniCPM5-2B Heretic derivative Q6_K and separate DSpark 2.6B, ctx16384 in catalog
- C09 (CURRENT_PASS_LIMITED) Functional agentic JSON tools coding and French regression: new chimera has 1/1 correct read-only tool, older engine has distinct 36-case trials
- C10 (CURRENT_PASS_LIMITED) Multi-agent concurrency and performance envelope: current native router and experimental Qwen4 chimera, 1 active model-worker

## Restant et ordonné

- C08 (PARTIAL) Native GGUF advertises 262144 max; target agentic product 128K. Current 8K five-marker 3/3 PASS. 16K f16 strict PSI watchdog FAIL, 16K q8 no quality. Native LAB 32K 64K 128K q8_0 both caches gated and 3 preflights BLOCKED before GPU. Need genuine full-prompt 3x5-marker passes plus long-context agent tool performance and fallback before full production.. Réussite: same exact GGUF, 5 marker extraction / no shift, GTT/PSI guarded, tokens actually consumed
- C09 (CURRENT_PASS_LIMITED) Chimera native strict simulated diagnostic tool selection 36/36 correct/0 unsafe. Atomic2 original Vulkan Qwen4 now 3/36 correct/0unsafe on IDENTICAL suite, then own-LAB watchdog correctly stopped at host PSI full2.20; native checkpoint preserved and resume supports immutable attempt logs, no duplicates, bound 20s transient PSI recovery. Atomic historical separate creative benchmark JSON3/9 tool6/9 code0/9 FR7/9 still fails general agentic QA. Complete same-suite and quality only after PBS storage contention resolved.. Réussite: no dangerous tool; >=95% correct safe tool calls and mandatory zero unsafe, no critical code corruption
- C10 (CURRENT_PASS_LIMITED) C10 client queue 42/42 for fan-outs 1,2,4 across 3 repetitions; 21/21 safe tool selection, 21/21 streaming, p95 total 9.0427s, p95 first stream fragment 6.5728s. Native llama worker has ONLY one decoding slot, so real 2/4 GPU parallel decode, exact ITL and long soak remain. Test explicit native --parallel N safely before claiming full multiagent GPU production.. Réussite: p95 TTFT and ITL thresholds, no lost requests, no worker preemption, no duplicate tool calls
- C11 (BLOCKED_RESOURCE) Host backup PBS VM900 is saturated with six native verification tasks still reported running after task-stop accepted; attempts to read four individual task logs time out 11s each. Host IO PSI full often >10, PBS VM900 IO full around20%. No forced VM shutdown, backup schedule change or disk eject. Requires separate integrity-preserving maintenance to diagnose stuck verifier workers and IO, before heavy GPU 128K qualification.. Réussite: stability across realistic workloads and after authorized reboot, guard admission stable, 0 PBS/ZFS service disruptions
- C12 (PARTIAL) MoE priority clarified. Sep14 Pym Q2 MTP2 recorded 34.56t/s median, 37.20t/s math peak under Cloud9 Vulkan, exact source commit not logged; cannot claim pure upstream. Stock upstream Oct18 9d1878a same model vs S1 exists with corrected strict JSON0/3 each, semantic code3/3 each. New Vulkan upstream b11840 and b11844 binaries MTP/native MoE controls OK, but 3 guarded Pym full-offload attempts stopped BEFORE GPU load due host RAM, GTT and PSI; current new tg speed unmeasured. Model exact file available. Requires safe ~14GiB GTT + host MemAvailable >=model 12.31GiB+23GiB for fair Pym 8192 context, then same-prompt base/MTP2/Atomic2 comparison and 128K quality.. Réussite: hardware guard, lossless/known error budget, reproducible non-inferiority + meaningful gain
- C13 (PARTIAL) Flash-Next historic 17.878t/s on RDNA Vulkan b10738 commit53f34cfaa was deliberately tuned MTP3 TurboQuant SET_ROWS FlashAttention CPU-WHT GDN fusion OFF (NOT plain stock). The local available two-shard GSQ-RCO IQ1_M model is 58.4GB and NOT historical AD-4.27+FR-Spec, so cannot A/B against 17.878; current source GGUF missing, no actual new Flash inference. Need exact matched model and memory/admission or external faithful bench, not quietly substitute quantization.. Réussite: per role latency, quality and useful context proven on the target device
- C14 (PARTIAL) Static native provider/agent services healthy, but live authenticated OmniRoute model enumeration: Chimera Qwen4 LAB NOT visible to Omniroute Master, N8N, IA CLI (HTTP200, 2541 IDs, 21 existing Cloud9 IDs). Must publish opt-in model via supported native provider-model management API (not SQLite), then validate OpenAI-compatible direct call via OmniRoute and real Dify/n8n/Paperclip multi-step workflows, permissions, fallback, rollback. Preserve existing 4-model Cloud9-Engine stable combo.. Réussite: real 2-3 step agent tasks and concurrent operation, explicit tool profiles and API privileges
- C15 (NOT_RUN) No all-purpose hardware winner from 26-Oct new tests: upstream Pym exact models 3 fail-closed preflights before GPU inference and Flash original AD+FRspec not installed. Historical Pym 34.56 median MTP2, math peak37.20, Atomic1.6 Pym f16 MTP2 36.28 (unmatched historical) and Flash-Next 17.878 tuned. Do not switch production from 4 stable OmniRoute models before matched real Qwen3.6 Pym upstream b11844/Atomic2, >=128K multi-marker QA, agentic strict JSON/tool/code, rollback and soak.. Réussite: published tag/release, observable health/p95, canary auto rollback, user can select it natively

## Règle de reprise future

1. Lire certification_registry.json + CURRENT_STATUS.md, puis HALL_OF_FAME.json dans le projet Cloud9.
2. Vérifier les fichiers de preuve SHA256 si l'accès SentinelX au projet est disponible.
3. Ne jamais recommencer C01/C02/C03 sur l'ancien runtime: fixtures historiques réutilisables.
4. Après tout changement touchant au moteur/benchmark/router: mettre à jour le JSON, régénérer ces deux documents, committer et pousser. GitHub Actions vérifie qu'ils concordent.
5. Ne pas annoncer 36 tests, 128K ni FlashNext >20 tok/s avant les nouveaux résultats.
