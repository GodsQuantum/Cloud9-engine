# Cloud9 Engine - matrice canonique de certification

Date du registre: 2026-10-25

Moteur disponible sur demande: Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB
Hall of Fame: 192 records; 35 raw proofs mirrored with SHA on GitHub.

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
| C08 | Current chimera long effective context 8K 16K and maximum useful | PARTIAL | Native current chimera Qwen4 8K EXACT 3/3 five-marker retrieval PASSED f16 KV at 8026 prompt tokens, latest seed3 8.4806 tok/s and zero watchdog. C08 still PARTIAL for current chimera 16K (three seeded runs) and larger useful context; do not replay historic Atomic proofs or promote NextN/Turbo3. |
| C09 | Functional agentic JSON tools coding and French regression | CURRENT_PASS_LIMITED | 36/36 native simulated diagnostic tools Qwen4 completed, no unsafe; full C09 native tool-call selection gate PASS. Separately qualify real coding/FR regression and C14 Dify/n8n/Paperclip live task workflows/permissions before full production promotion. |
| C10 | Multi-agent concurrency and performance envelope | CURRENT_PASS_LIMITED | C10 client queue 42/42 for fan-outs 1,2,4 across 3 repetitions; 21/21 safe tool selection, 21/21 streaming, p95 total 9.0427s, p95 first stream fragment 6.5728s. Native llama worker has ONLY one decoding slot, so real 2/4 GPU parallel decode, exact ITL and long soak remain. Test explicit native --parallel N safely before claiming full multiagent GPU production. |
| C11 | Host memory/GPU sharing/PBS stability reboot proof | BLOCKED_RESOURCE | Host native systemd-zram-generator additive zram2 active 4GiB lz4 low priority60 resident cap2GiB, preserving zram0/1; reduced swap utilization ratio 97->80% at addition. Sustained 8K+16K under PBS disk I/O + VM services and safe latency/recovery still required. No reboot validation. Never confuse swap capacity addition with physical RAM availability. |
| C12 | Feature speed parity and Turbo KV real backend GPU | PARTIAL | NextN LAB artifact CI native loaded and CPU/backend passes, but no GPU A/B. Turbo3 Kq8_0/Vturbo3 Vulkan proved quality FAIL at 8K (3.51 t/s, 5/5 extraction criterion failed (per-marker wrong count not recorded)). Never promote or replay known failure. Use only safety-guarded f16 matched baseline/NextN, then separately certify quality before performance. |
| C13 | Four role-selected models and FlashNext >20 t/s | PARTIAL | Qualify four representative model roles exact quant / hashes and actual FlashNext >20 if GPU fitting works; do not confuse 35B/Pym with Qwen4 |
| C14 | OmniRoute Dify n8n Paperclip end-to-end | PARTIAL | Read-only 25-Oct healthy native OmniRoute llama-cpp provider and four stable Cloud9 combo models in SQLite/catalog; Omniroute,Dify,n8n,MCPProxy,OpenWebUI,Papercip systemd,router,embeddings processes healthy. STILL require real end-to-end 2/3-step agent/tool workflows with profile isolation/permissions/fallback and no unauthorized tools. Static health is NOT workflow certification. |
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
