# Handoff automatique Cloud9 Engine

Registre mis à jour: 2026-10-25

Moteur disponible: Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB

SHA routeur: 2ce83aed1f1a54a7e14e295838d34f7d05d1fc7dac4554341e34d296fdc31262
SHA catalogue: 82581f2315ef7e95ab5cf6937cc0781a5531d89fdb4a00734dbb0502a3a2a288
GitHub evidence snapshot count: 6; SHA validated without a running Cloud9 host.
Maintenir les combos OmniRoute actuels. Ne pas promouvoir ce LAB en défaut avant les gates restants.

## Certifié dans sa portée et A NE PAS REFAIRE

- C01 (HISTORICAL_VALID) Historique: noyau Vulkan MUL_MAT_ID 921/921: Cloud9 Engine 534cda00; NOT current master9ae chimera
- C02 (HISTORICAL_VALID) Historique: cinq aiguilles 8K réelles 3/3: Atomic TurboQuant 2.0.0 Qwen4 Q4_K_M Vulkan Q8K Turbo3V
- C03 (HISTORICAL_VALID) Historique: cinq aiguilles 16K réelles 3/3: Atomic TurboQuant 2.0.0 Qwen4 Q4_K_M Vulkan Q8K Turbo3V
- C04 (CURRENT_PASS_LIMITED) CI chimera native MMB MTP Turbo source / backend guard: Cloud9 chimera master9ae source Vulkan/HIP CPU build, NOT GPU TurboQuant
- C05 (CURRENT_PASS_LIMITED) CT410 router safe nonpreemptive, stable services: active 2026-10-25 CT410 guarded 9-model catalog; only one worker
- C06 (CURRENT_PASS_LIMITED) Chimera native Qwen4 real GPU 2K + strict read-only tool: opt-in Qwen4 Q4_K_M, MTP draft, Vulkan, f16 KV, ctx2048, threads6 batch256
- C07 (CURRENT_PASS_LIMITED) OpenBMB MiniCPM5+DSpark live speed and tool: MiniCPM5-2B Heretic derivative Q6_K and separate DSpark 2.6B, ctx16384 in catalog

## Restant et ordonné

- C08 (PARTIAL) On master9ae Qwen4 Vulkan (ctx8704), 8K five markers correct in both seeded repeats 1 and 2, both consumed 8026 input tokens. Third repeat stopped when memory PSI reached 2.31; 16K on current chimera still not tested. Preserve proofs and run ONLY seeded rep 3 when GPU-safe, then 16K.. Réussite: same exact GGUF, 5 marker extraction / no shift, GTT/PSI guarded, tokens actually consumed
- C09 (PARTIAL) Chimera current opt-in Qwen4 completed 1/36 read-only strict native tool scenario, correct pve.get_ct_config JSON; GPU runtime PSI caused checkpointed pause. New native test harness supports --resume without duplicating completed cases; finish 35 remaining when admitted, add code/FR regressions.. Réussite: no dangerous tool; >=95% correct safe tool calls and mandatory zero unsafe, no critical code corruption
- C10 (NOT_RUN) Existing server cannot simply be called multiworker; benchmark slots 1/2/4 and use real router queue/reloads; native llama server supports parallel decoding. Réussite: p95 TTFT and ITL thresholds, no lost requests, no worker preemption, no duplicate tool calls
- C11 (BLOCKED_RESOURCE) PBS backup 25-Oct interrupted by user authorization and full PVE schedule restored; GPU 8K still drops host available memory below 24GiB, even without a vzdump process. Need stable >=27GiB prelaunch for 8K, cure PBS I/O pressure safely and verify no regression across sustained agent workloads; do not change guardian threshold.. Réussite: stability across realistic workloads and after authorized reboot, guard admission stable, 0 PBS/ZFS service disruptions
- C12 (NOT_RUN) Compare same GGUF, prompts, quant, context+flags and MTP on/off with upstream; GPU KV Turbo3 Q/V is blocked until numerical+accuracy correct; no fake win. Réussite: hardware guard, lossless/known error budget, reproducible non-inferiority + meaningful gain
- C13 (PARTIAL) Qualify four representative model roles exact quant / hashes and actual FlashNext >20 if GPU fitting works; do not confuse 35B/Pym with Qwen4. Réussite: per role latency, quality and useful context proven on the target device
- C14 (PARTIAL) Test Dify/n8n/Paperclip agents in read-only realistic tasks, 2 separate identities/profile constraints; ensure no repeated model switch. Réussite: real 2-3 step agent tasks and concurrent operation, explicit tool profiles and API privileges
- C15 (NOT_RUN) Only after C08-14 relevant gates, shadow/canary, versioned rollback and measured 24h safe operation; no service restart without warning. Réussite: published tag/release, observable health/p95, canary auto rollback, user can select it natively

## Règle de reprise future

1. Lire certification_registry.json + CURRENT_STATUS.md, puis HALL_OF_FAME.json dans le projet Cloud9.
2. Vérifier les fichiers de preuve SHA256 si l'accès SentinelX au projet est disponible.
3. Ne jamais recommencer C01/C02/C03 sur l'ancien runtime: fixtures historiques réutilisables.
4. Après tout changement touchant au moteur/benchmark/router: mettre à jour le JSON, régénérer ces deux documents, committer et pousser. GitHub Actions vérifie qu'ils concordent.
5. Ne pas annoncer 36 tests, 128K ni FlashNext >20 tok/s avant les nouveaux résultats.
