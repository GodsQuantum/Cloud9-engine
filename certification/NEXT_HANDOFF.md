# Handoff automatique Cloud9 Engine

Registre mis à jour: 2026-10-25

Moteur disponible: Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB

SHA routeur: 2ce83aed1f1a54a7e14e295838d34f7d05d1fc7dac4554341e34d296fdc31262
SHA catalogue: 82581f2315ef7e95ab5cf6937cc0781a5531d89fdb4a00734dbb0502a3a2a288
GitHub evidence snapshot count: 27; SHA validated without a running Cloud9 host.
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

## Restant et ordonné

- C08 (PARTIAL) Qwen4 8K current chimera still 2/3 proven. The LAB-only 8K seed3 guard conditionally permits min24.6GiB MemAvailable when verified live native zram2>=4GiB, host swap total>=23GiB, <83% usage, full memory PSI<0.10 and GTT>=7.2GiB, AND official guardian permits. Otherwise strict 27GiB, 16K remains 30GiB. Execute seed3 only as immutable trial with full five-marker extraction and watchdog, then 16K, no C02/C03 replay.. Réussite: same exact GGUF, 5 marker extraction / no shift, GTT/PSI guarded, tokens actually consumed
- C09 (CURRENT_PASS_LIMITED) 36/36 native simulated diagnostic tools Qwen4 completed, no unsafe; full C09 native tool-call selection gate PASS. Separately qualify real coding/FR regression and C14 Dify/n8n/Paperclip live task workflows/permissions before full production promotion.. Réussite: no dangerous tool; >=95% correct safe tool calls and mandatory zero unsafe, no critical code corruption
- C10 (NOT_RUN) C10 remains NOT_RUN on real GPU. New LAB-only C10 harness has 10 passing static unit tests + CT410 dry-run, hashes synced. After C09 36/36, run only under guardian with exact existing idle worker, verify native slots then 1/2/4 client concurrency, streamed TTFT and inter-chunk timings. No service changes and never mistake client queuing for native decoding parallelism.. Réussite: p95 TTFT and ITL thresholds, no lost requests, no worker preemption, no duplicate tool calls
- C11 (BLOCKED_RESOURCE) Host native systemd-zram-generator additive zram2 active 4GiB lz4 low priority60 resident cap2GiB, preserving zram0/1; reduced swap utilization ratio 97->80% at addition. Sustained 8K+16K under PBS disk I/O + VM services and safe latency/recovery still required. No reboot validation. Never confuse swap capacity addition with physical RAM availability.. Réussite: stability across realistic workloads and after authorized reboot, guard admission stable, 0 PBS/ZFS service disruptions
- C12 (PARTIAL) NextN LAB artifact CI native loaded and CPU/backend passes, but no GPU A/B. Turbo3 Kq8_0/Vturbo3 Vulkan proved quality FAIL at 8K (3.51 t/s, 5/5 extraction criterion failed (per-marker wrong count not recorded)). Never promote or replay known failure. Use only safety-guarded f16 matched baseline/NextN, then separately certify quality before performance.. Réussite: hardware guard, lossless/known error budget, reproducible non-inferiority + meaningful gain
- C13 (PARTIAL) Qualify four representative model roles exact quant / hashes and actual FlashNext >20 if GPU fitting works; do not confuse 35B/Pym with Qwen4. Réussite: per role latency, quality and useful context proven on the target device
- C14 (PARTIAL) OmniRoute llama-cpp provider active, Cloud9-Engine has exactly four stable model entries and CT410 catalog has nine; chimera is deliberately NOT in default combo. Require authorized real end-to-end tool workflows through OmniRoute+Dify+n8n+Paperclip, with identity/profile boundaries and fallback tests, before production promotion.. Réussite: real 2-3 step agent tasks and concurrent operation, explicit tool profiles and API privileges
- C15 (NOT_RUN) Only after C08-14 relevant gates, shadow/canary, versioned rollback and measured 24h safe operation; no service restart without warning. Réussite: published tag/release, observable health/p95, canary auto rollback, user can select it natively

## Règle de reprise future

1. Lire certification_registry.json + CURRENT_STATUS.md, puis HALL_OF_FAME.json dans le projet Cloud9.
2. Vérifier les fichiers de preuve SHA256 si l'accès SentinelX au projet est disponible.
3. Ne jamais recommencer C01/C02/C03 sur l'ancien runtime: fixtures historiques réutilisables.
4. Après tout changement touchant au moteur/benchmark/router: mettre à jour le JSON, régénérer ces deux documents, committer et pousser. GitHub Actions vérifie qu'ils concordent.
5. Ne pas annoncer 36 tests, 128K ni FlashNext >20 tok/s avant les nouveaux résultats.
