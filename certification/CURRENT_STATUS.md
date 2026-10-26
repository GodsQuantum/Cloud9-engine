# Cloud9 Engine - matrice canonique de certification

Date du registre: 2026-10-25

Moteur disponible sur demande: Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB
Hall of Fame: 192 records; 68 raw proofs mirrored with SHA on GitHub.

Historique valide != validation du nouveau binaire. C01-C03 ne doivent pas être rejoués sur leurs anciens exécutables.

| ID | Résultat exact | État | Nouvelle étape requise |
|---|---|---|---|
| C01 | Historique: noyau Vulkan MUL_MAT_ID 921/921 | HISTORICAL_VALID | Do not re-run old 921 cases unless exact kernel touched |
| C02 | Historique: cinq aiguilles 8K réelles 3/3 | HISTORICAL_VALID | Only port fixture to current chimera; never rebuild the historic test |
| C03 | Historique: cinq aiguilles 16K réelles 3/3 | HISTORICAL_VALID | Only certify current chimera relevant context; keep 16330-token source benchmark |
| C04 | CI chimera native MMB MTP Turbo source / backend guard | CURRENT_PASS_LIMITED | Need separate GPU Turbo K/V validation before claim TurboQuant runtime production |
| C05 | CT410 router safe nonpreemptive, stable services | CURRENT_PASS_LIMITED | Current CT410 router source caught up from live deployed 29KB native Python and deployed patched SHA87c959b41cda. Fixed embedding_busy() wrong localhost:8091 bind; now uses configurable actual192.168.1.219:8091, fail-closed on API error/malformed slots. 25 targeted router tests PASS, restart only when router worker idle and zero connections, embedding service remained active with 4 processing slots. Remaining: real exclusive preemption/rollback test ONLY during idle maintenance, not while real embedding tasks running. |
| C06 | Chimera native Qwen4 real GPU 2K + strict read-only tool | CURRENT_PASS_LIMITED | Tool quality is only 1 case; incorrect technical suggestions in chat observed |
| C07 | OpenBMB MiniCPM5+DSpark live speed and tool | CURRENT_PASS_LIMITED | Not 3/3 scenario suite nor untouched OpenBMB weights |
| C08 | Current chimera long effective context 8K 16K and maximum useful | PARTIAL | Native GGUF advertises 262144 max; target agentic product 128K. Current 8K five-marker 3/3 PASS. 16K f16 strict PSI watchdog FAIL, 16K q8 no quality. Native LAB 32K 64K 128K q8_0 both caches gated and 3 preflights BLOCKED before GPU. Need genuine full-prompt 3x5-marker passes plus long-context agent tool performance and fallback before full production. |
| C09 | Functional agentic JSON tools coding and French regression | CURRENT_PASS_LIMITED | Chimera native strict simulated diagnostic tool selection 36/36 correct/0 unsafe. Atomic2 original Vulkan Qwen4 now 3/36 correct/0unsafe on IDENTICAL suite, then own-LAB watchdog correctly stopped at host PSI full2.20; native checkpoint preserved and resume supports immutable attempt logs, no duplicates, bound 20s transient PSI recovery. Atomic historical separate creative benchmark JSON3/9 tool6/9 code0/9 FR7/9 still fails general agentic QA. Complete same-suite and quality only after PBS storage contention resolved. |
| C10 | Multi-agent concurrency and performance envelope | CURRENT_PASS_LIMITED | C10 client queue 42/42 for fan-outs 1,2,4 across 3 repetitions; 21/21 safe tool selection, 21/21 streaming, p95 total 9.0427s, p95 first stream fragment 6.5728s. Native llama worker has ONLY one decoding slot, so real 2/4 GPU parallel decode, exact ITL and long soak remain. Test explicit native --parallel N safely before claiming full multiagent GPU production. |
| C11 | Host memory/GPU sharing/PBS stability reboot proof | BLOCKED_RESOURCE | Cloud9 shared RAM baseline24-27GiB available for 96GiB host, heavy swap17-18GiB, CT400 IA Studio16GiB, HAOS and PBS guests plus CT410 embeddings3GiB. Four embeddings slots repeatedly busy, PBS VM900 backup/verify IO pressure. LFM compact Q4 GPU trial host PSI peak2.05-2.35 and memory21-22G; own watchdog correctly killed only LAB child. Do not preempt busy embeddings or stop HAOS/PBS/CT400 to win synthetic speeds. No Pym13.22GB fair full GPU run under this RAM/PSI. |
| C12 | Feature speed parity and Turbo KV real backend GPU | PARTIAL | Real native SAME LFM2.5-8B-A1B Q4 model SHA pinned, same prompt 256tokens c1536 b128 ub32 FA f16KV: upstream b11844 math38.975t/s; Atomic2 math47.601t/s (+22.13%), code44.512, FR39.973 t/s. All completion visible outputs EMPTY because 256 tokens spent on reasoning, thus not agentic-quality qualified and not an engine WIN. Native reasoning-budget0 and expanded 768 output prepared, but real subsequent QA attempts both stopped by official host PSI watchdog during load. Pym 35B historical MTP2 median34.56 math peak37.20, Flash-Next tuned 17.878 remain distinct models; do not infer MoE model quality from LFM. IMPORTANT EVIDENCE CORRECTION: 256-token trials have empty content, but raw reasoning_content and finish_reason NOT recorded. Thinking truncation is plausible, NOT proved. In one cold start math case Atomic load+request21.502s vs upstream12.484s despite hot decode advantage; cannot certify start latency/quality based on single trial. |
| C13 | Four role-selected models and FlashNext >20 t/s | PARTIAL | Model provenance verified: Pym historic Q2-MTP / Flash-Next historic AD-FRspec different from local GSQ IQ1M, and LFM2.5-8B-A1B official Q4 5.16GB is a distinct compact MoE fallback for engine A/B. Must complete identical inference on upstream and Atomic2, quality JSON/tools/code, then high capability Pym/Flash matching GGUF whenever host RAM/PSI safely permits. |
| C14 | OmniRoute Dify n8n Paperclip end-to-end | PARTIAL | Static native provider/agent services healthy, but live authenticated OmniRoute model enumeration: Chimera Qwen4 LAB NOT visible to Omniroute Master, N8N, IA CLI (HTTP200, 2541 IDs, 21 existing Cloud9 IDs). Must publish opt-in model via supported native provider-model management API (not SQLite), then validate OpenAI-compatible direct call via OmniRoute and real Dify/n8n/Paperclip multi-step workflows, permissions, fallback, rollback. Preserve existing 4-model Cloud9-Engine stable combo. |
| C15 | Controlled v1 release default / rollback and live monitoring | NOT_RUN | FAIL CLOSED. Atomic2 +22.13pct math decode against upstream on exact LFM Q4 at c1536, BUT generated 0 visible final answers in both engines at 256token cap. At native reasoning-budget0 full QA both guard stopped before inference due host memory PSI, so NO agentic/coding/JSON winner certified. Require same-model full final responses, exact tools and coding quality, context32/64/128K and 24h canary before production promotion. Production 4 OmniRoute combos unchanged, current router safety fix installed. |

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
