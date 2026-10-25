# Handoff automatique Cloud9 Engine

Registre mis à jour: 2026-10-25

Moteur disponible: Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB

SHA routeur: 2ce83aed1f1a54a7e14e295838d34f7d05d1fc7dac4554341e34d296fdc31262
SHA catalogue: 82581f2315ef7e95ab5cf6937cc0781a5531d89fdb4a00734dbb0502a3a2a288
GitHub evidence snapshot count: 23; SHA validated without a running Cloud9 host.
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

- C08 (PARTIAL) 8K Qwen4 chimera 2/3 valid; run seed3 only when LAB preflight 27GiB available, swap<95%, PSI<0.35 and official guardian allows. 16K current chimera requires 30GiB prelaunch. Use unique trial ID, never redo historical C02/C03.. Réussite: same exact GGUF, 5 marker extraction / no shift, GTT/PSI guarded, tokens actually consumed
- C09 (PARTIAL) C09 native opt-in Qwen4 28/36 correct strict tool JSON; zero unsafe. Reps [12,12,4] complete. Resource guard paused after 28, only final eight cases in THIRD repetition remain. Resume same native CT410 checkpoint/fixture SHA with --execute --resume --allow-lab-load under official GPU guard; never redo completed 28. Then add FR+coding integrity regression and report exact final pass rate.. Réussite: no dangerous tool; >=95% correct safe tool calls and mandatory zero unsafe, no critical code corruption
- C10 (NOT_RUN) C10 remains NOT_RUN on real GPU. New LAB-only C10 harness has 10 passing static unit tests + CT410 dry-run, hashes synced. After C09 36/36, run only under guardian with exact existing idle worker, verify native slots then 1/2/4 client concurrency, streamed TTFT and inter-chunk timings. No service changes and never mistake client queuing for native decoding parallelism.. Réussite: p95 TTFT and ITL thresholds, no lost requests, no worker preemption, no duplicate tool calls
- C11 (BLOCKED_RESOURCE) C11 remains BLOCKED_RESOURCE: ZRAM >95% full during GPU qualification, sdc ZFS and sdg USB PBS backup datastore simultaneously showed >2.8s busy time per 3s observation, IO PSI full elevated; one D-state find process persists. Busy disks do NOT prove failure. Preserve services; qualify under sustainable RAM/IO load and after only user-authorized reboot.. Réussite: stability across realistic workloads and after authorized reboot, guard admission stable, 0 PBS/ZFS service disruptions
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
