# Handoff automatique Cloud9 Engine

Registre mis à jour: 2026-10-25

Moteur disponible: Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB

SHA routeur: 2ce83aed1f1a54a7e14e295838d34f7d05d1fc7dac4554341e34d296fdc31262
SHA catalogue: 82581f2315ef7e95ab5cf6937cc0781a5531d89fdb4a00734dbb0502a3a2a288
GitHub evidence snapshot count: 93; SHA validated without a running Cloud9 host.
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
- C11 (BLOCKED_RESOURCE) 26 Oct service-only audit now covers 14 LXC (12 active,2 stopped), VM100/900 (HAOS no QGA), host and ~165 Docker containers. NEW actual fixes CT300 broken DaVinci PathChanged storm to native30m service timer (service test PASS), host completed ZFS rehab collector disabled (720 SMART+journal polling/day gone), native DaVinci GPU timer5->10sec (8640 starts/day less). Compose source health intervals Redis Netbox x2 CT1101s->15s, Dify PostgreSQL CT4001s->15s, DaVinci PostgreSQL CT3005s->15s VALIDATED but not applied to running Docker without targeted service recreation. Pending CT410 ComfyUI/Docling failed sockets and CT700 stale preview units, no unsafe kills. CT400 WAS accidentally stopped by stale shutdown job; restarted 09:11, all key apps confirmed healthy. NEVER STOP WHOLE LXC/VM FOR BENCHMARK. Full sanitized audit certification/CLOUD9_SERVICE_AUDIT_20261026.md and proofs.. Réussite: stability across realistic workloads and after authorized reboot, guard admission stable, 0 PBS/ZFS service disruptions
- C12 (PARTIAL) Real Pym35B-A3B Q2 MTP same physical model run SUCCESS: Atomic2 stock partial_min ngl4 cpu-moe41 no MTP 2K ctx f16 KV, 768 tokens x3: maths8.974t/s correct 925, code6.956t/s text only, French8.598t/s text only, load2.516sec, 0 watchdog, 3/3 visible. This is strictly NOT historical Pym fullGPU MTP2 34.56 median/37.20math comparable or proven code quality. New matched192 trials: upstream MTP2 and base crash guarded PSI, Atomic2 Zen4/LTO base loaded7.496sec then paused PSI, stock192 denied preflight; unable to rank engines under current shared workloads. No production LLM worker switched, router&embedding healthy. Guard must NOT be bypassed, do not shutdown CT400 or any LXC; need safe memory/IO service-level improvement and genuine matched A/B quality/code/JSON 128K.. Réussite: hardware guard, lossless/known error budget, reproducible non-inferiority + meaningful gain
- C13 (PARTIAL) User priority Flash-Next original AD-4.27bpw-Q4_K_M-M64 + Q8 FR-Spec, historic safe17.878t/s with Cloud9 RDNA b10738 MTP3 TurboQuant SET_ROWS CPU-WHT GDN OFF. Exact original weights absent locally; existing GSQ-RCO IQ1M coder 58.4GB distinct model/format and cannot be substituted. Public quant publisher mk2878d has 92.9GB overall with ~54.5GB resident and draft publisher drluoto has Q8 FR-Spec sidecar. Reacquire only when RAM/disk/guardian permits, never in shared loaded production with 25GiB MemAvailable. Pym baseline first.. Réussite: per role latency, quality and useful context proven on the target device
- C14 (PARTIAL) Static native provider/agent services healthy, but live authenticated OmniRoute model enumeration: Chimera Qwen4 LAB NOT visible to Omniroute Master, N8N, IA CLI (HTTP200, 2541 IDs, 21 existing Cloud9 IDs). Must publish opt-in model via supported native provider-model management API (not SQLite), then validate OpenAI-compatible direct call via OmniRoute and real Dify/n8n/Paperclip multi-step workflows, permissions, fallback, rollback. Preserve existing 4-model Cloud9-Engine stable combo.. Réussite: real 2-3 step agent tasks and concurrent operation, explicit tool profiles and API privileges
- C15 (NOT_RUN) FAIL-CLOSED: no production promotion of any LLM. Pym true3/3 768-token base partial measurement on Atomic2 stock, actual comparative upstream/Atomic2 LTO at192 blocked due guardian memory PSI, no matched quality context >2K. Existing OmniRoute choices unchanged. Native timer/Compose source fixes documented; CT400 healthy after involuntary stop; explicit no whole-LXC shutdown rule. Revisit only when 780M safe coexistence, then canary24h rollback exact tasks. See sanitized service audit.. Réussite: published tag/release, observable health/p95, canary auto rollback, user can select it natively

## Règle de reprise future

1. Lire certification_registry.json + CURRENT_STATUS.md, puis HALL_OF_FAME.json dans le projet Cloud9.
2. Vérifier les fichiers de preuve SHA256 si l'accès SentinelX au projet est disponible.
3. Ne jamais recommencer C01/C02/C03 sur l'ancien runtime: fixtures historiques réutilisables.
4. Après tout changement touchant au moteur/benchmark/router: mettre à jour le JSON, régénérer ces deux documents, committer et pousser. GitHub Actions vérifie qu'ils concordent.
5. Ne pas annoncer 36 tests, 128K ni FlashNext >20 tok/s avant les nouveaux résultats.
