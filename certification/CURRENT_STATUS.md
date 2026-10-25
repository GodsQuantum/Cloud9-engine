# Cloud9 Engine - matrice canonique de certification

Date du registre: 2026-10-25

Moteur disponible sur demande: Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB
Hall of Fame: 192 records; 17 raw proofs mirrored with SHA on GitHub.

Historique valide != validation du nouveau binaire. C01-C03 ne doivent pas être rejoués sur leurs anciens exécutables.

| ID | Résultat exact | État | Nouvelle étape requise |
|---|---|---|---|
| C01 | Historique: noyau Vulkan MUL_MAT_ID 921/921 | HISTORICAL_VALID | Do not re-run old 921 cases unless exact kernel touched |
| C02 | Historique: cinq aiguilles 8K réelles 3/3 | HISTORICAL_VALID | Only port fixture to current chimera; never rebuild the historic test |
| C03 | Historique: cinq aiguilles 16K réelles 3/3 | HISTORICAL_VALID | Only certify current chimera relevant context; keep 16330-token source benchmark |
| C04 | CI chimera native MMB MTP Turbo source / backend guard | CURRENT_PASS_LIMITED | Need separate GPU Turbo K/V validation before claim TurboQuant runtime production |
| C05 | CT410 router safe nonpreemptive, stable services | CURRENT_PASS_LIMITED | Prove stress and crash recovery and no interruptions under concurrent agent traffic |
| C06 | Chimera native Qwen4 real GPU 2K + strict read-only tool | CURRENT_PASS_LIMITED | Tool quality is only 1 case; incorrect technical suggestions in chat observed |
| C07 | OpenBMB MiniCPM5+DSpark live speed and tool | CURRENT_PASS_LIMITED | Not 3/3 scenario suite nor untouched OpenBMB weights |
| C08 | Current chimera long effective context 8K 16K and maximum useful | PARTIAL | 8K Qwen4 master9ae seeded repeats 1 and 2 each 5/5 correct (8026 prompt tokens), no third success; a new rep3-only attempt 25 Oct 02:13 loaded successfully but failed guard BEFORE inference, MemAvailable 22.681 GiB and full PSI 2.32. Run only seeded rep3 after stable resource margin; then 16K current chimera. Do not repeat historical Atomic 8K/16K. |
| C09 | Functional agentic JSON tools coding and French regression | PARTIAL | Read-only native Qwen4 C09 now 2/36 strict correct; second case pbs-task-integrity 11.433 seconds. Remaining 34 distinct case/repetitions untested. Resume original immutable fixture+mutable CT410 checkpoint, skipping first two, only when GPU/memory guard permits; add FR/code regression. |
| C10 | Multi-agent concurrency and performance envelope | NOT_RUN | Existing server cannot simply be called multiworker; benchmark slots 1/2/4 and use real router queue/reloads; native llama server supports parallel decoding |
| C11 | Host memory/GPU sharing/PBS stability reboot proof | BLOCKED_RESOURCE | PBS backup 25-Oct interrupted by user authorization and full PVE schedule restored; GPU 8K still drops host available memory below 24GiB, even without a vzdump process. Need stable >=27GiB prelaunch for 8K, cure PBS I/O pressure safely and verify no regression across sustained agent workloads; do not change guardian threshold. |
| C12 | Feature speed parity and Turbo KV real backend GPU | PARTIAL | NextN LAB artifact CI native loaded and CPU/backend passes, but no GPU A/B. Turbo3 Kq8_0/Vturbo3 Vulkan proved quality FAIL at 8K (3.51 t/s, 5/5 extraction criterion failed (per-marker wrong count not recorded)). Never promote or replay known failure. Use only safety-guarded f16 matched baseline/NextN, then separately certify quality before performance. |
| C13 | Four role-selected models and FlashNext >20 t/s | PARTIAL | Qualify four representative model roles exact quant / hashes and actual FlashNext >20 if GPU fitting works; do not confuse 35B/Pym with Qwen4 |
| C14 | OmniRoute Dify n8n Paperclip end-to-end | PARTIAL | OmniRoute llama-cpp provider active, Cloud9-Engine has exactly four stable model entries and CT410 catalog has nine; chimera is deliberately NOT in default combo. Require authorized real end-to-end tool workflows through OmniRoute+Dify+n8n+Paperclip, with identity/profile boundaries and fallback tests, before production promotion. |
| C15 | Controlled v1 release default / rollback and live monitoring | NOT_RUN | Only after C08-14 relevant gates, shadow/canary, versioned rollback and measured 24h safe operation; no service restart without warning |

## Voie production minimale, modèle local Qwen4

C08, C09, C10, C11, C14, C15

## Voie produit complet, plusieurs modèles dont FlashNext

C08, C09, C10, C11, C12, C13, C14, C15

## Preuves numériques à conserver

- C01: {"cases_total": 921, "kernel_correctness_cases_passed": 921, "limitations": "Old 534cda kernel only", "runtime": "2026-09-16 old Cloud9 engine"}
- C02: {"engine": "Atomic TurboQuant 2.0.0", "five_markers_exact_retrieval": "3/3", "prompt_tokens_consumed": 8026}
- C03: {"engine": "Atomic TurboQuant 2.0.0", "five_markers_exact_retrieval": "3/3", "prompt_tokens_consumed": 16330}
- C04: {"ci": "last relevant CI success 5cf4e66; newest b855a12 in progress during audit", "python_tests_passed": 202}
- C06: {"decode_tps": 33.756523992721654, "prefill_tps": 394.8046352198254, "strict_tool_correct": "1/1", "wall_seconds": 5.369}
- C07: {"decode_tps": 22.155087239728633, "historical_catalog_decode_tps_not_repeated": 47.73, "tool_strict_correct": "1/1"}

## Interdictions de fausse certification

- Compilation et tests de kernels ne valent pas inférence sur GPU avec les poids actuels.
- 2K ne prouve ni 8K ni 16K; les succès Atomic 8K/16K conservent leurs propres hashes.
- Ne jamais réécrire un ancien benchmark avec les nouveaux nombres.
- Le gardien GPU et le verrou restent obligatoires; pas de pause PBS, swapoff, reboot automatique ou arrêt VoiceStudio.
- Tout changement de code/champs de configuration exige une vérification des gates affectés; ne refaire que ces gates.
