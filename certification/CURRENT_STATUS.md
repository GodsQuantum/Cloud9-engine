# Cloud9 Engine - matrice canonique de certification

Date du registre: 2026-10-25

Moteur disponible sur demande: Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB
Hall of Fame: 192 records; 54 raw proofs mirrored with SHA on GitHub.

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
| C08 | Current chimera long effective context 8K 16K and maximum useful | PARTIAL | Native GGUF advertises 262144 max; target agentic product 128K. Current 8K five-marker 3/3 PASS. 16K f16 strict PSI watchdog FAIL, 16K q8 no quality. Native LAB 32K 64K 128K q8_0 both caches gated and 3 preflights BLOCKED before GPU. Need genuine full-prompt 3x5-marker passes plus long-context agent tool performance and fallback before full production. |
| C09 | Functional agentic JSON tools coding and French regression | CURRENT_PASS_LIMITED | Chimera native strict simulated diagnostic tool selection 36/36 correct/0 unsafe. Atomic2 original Vulkan Qwen4 now 3/36 correct/0unsafe on IDENTICAL suite, then own-LAB watchdog correctly stopped at host PSI full2.20; native checkpoint preserved and resume supports immutable attempt logs, no duplicates, bound 20s transient PSI recovery. Atomic historical separate creative benchmark JSON3/9 tool6/9 code0/9 FR7/9 still fails general agentic QA. Complete same-suite and quality only after PBS storage contention resolved. |
| C10 | Multi-agent concurrency and performance envelope | CURRENT_PASS_LIMITED | C10 client queue 42/42 for fan-outs 1,2,4 across 3 repetitions; 21/21 safe tool selection, 21/21 streaming, p95 total 9.0427s, p95 first stream fragment 6.5728s. Native llama worker has ONLY one decoding slot, so real 2/4 GPU parallel decode, exact ITL and long soak remain. Test explicit native --parallel N safely before claiming full multiagent GPU production. |
| C11 | Host memory/GPU sharing/PBS stability reboot proof | BLOCKED_RESOURCE | Host backup PBS VM900 is saturated with six native verification tasks still reported running after task-stop accepted; attempts to read four individual task logs time out 11s each. Host IO PSI full often >10, PBS VM900 IO full around20%. No forced VM shutdown, backup schedule change or disk eject. Requires separate integrity-preserving maintenance to diagnose stuck verifier workers and IO, before heavy GPU 128K qualification. |
| C12 | Feature speed parity and Turbo KV real backend GPU | PARTIAL | MoE priority clarified. Sep14 Pym Q2 MTP2 recorded 34.56t/s median, 37.20t/s math peak under Cloud9 Vulkan, exact source commit not logged; cannot claim pure upstream. Stock upstream Oct18 9d1878a same model vs S1 exists with corrected strict JSON0/3 each, semantic code3/3 each. New Vulkan upstream b11840 and b11844 binaries MTP/native MoE controls OK, but 3 guarded Pym full-offload attempts stopped BEFORE GPU load due host RAM, GTT and PSI; current new tg speed unmeasured. Model exact file available. Requires safe ~14GiB GTT + host MemAvailable >=model 12.31GiB+23GiB for fair Pym 8192 context, then same-prompt base/MTP2/Atomic2 comparison and 128K quality. |
| C13 | Four role-selected models and FlashNext >20 t/s | PARTIAL | Flash-Next historic 17.878t/s on RDNA Vulkan b10738 commit53f34cfaa was deliberately tuned MTP3 TurboQuant SET_ROWS FlashAttention CPU-WHT GDN fusion OFF (NOT plain stock). The local available two-shard GSQ-RCO IQ1_M model is 58.4GB and NOT historical AD-4.27+FR-Spec, so cannot A/B against 17.878; current source GGUF missing, no actual new Flash inference. Need exact matched model and memory/admission or external faithful bench, not quietly substitute quantization. |
| C14 | OmniRoute Dify n8n Paperclip end-to-end | PARTIAL | Static native provider/agent services healthy, but live authenticated OmniRoute model enumeration: Chimera Qwen4 LAB NOT visible to Omniroute Master, N8N, IA CLI (HTTP200, 2541 IDs, 21 existing Cloud9 IDs). Must publish opt-in model via supported native provider-model management API (not SQLite), then validate OpenAI-compatible direct call via OmniRoute and real Dify/n8n/Paperclip multi-step workflows, permissions, fallback, rollback. Preserve existing 4-model Cloud9-Engine stable combo. |
| C15 | Controlled v1 release default / rollback and live monitoring | NOT_RUN | No all-purpose hardware winner from 26-Oct new tests: upstream Pym exact models 3 fail-closed preflights before GPU inference and Flash original AD+FRspec not installed. Historical Pym 34.56 median MTP2, math peak37.20, Atomic1.6 Pym f16 MTP2 36.28 (unmatched historical) and Flash-Next 17.878 tuned. Do not switch production from 4 stable OmniRoute models before matched real Qwen3.6 Pym upstream b11844/Atomic2, >=128K multi-marker QA, agentic strict JSON/tool/code, rollback and soak. |

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
