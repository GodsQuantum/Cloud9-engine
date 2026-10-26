# Cloud9 Engine - matrice canonique de certification

Date du registre: 2026-10-25

Moteur disponible sur demande: Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB
Hall of Fame: 192 records; 100 raw proofs mirrored with SHA on GitHub.

Historique valide != validation du nouveau binaire. C01-C03 ne doivent pas être rejoués sur leurs anciens exécutables.

| ID | Résultat exact | État | Nouvelle étape requise |
|---|---|---|---|
| C01 | Historique: noyau Vulkan MUL_MAT_ID 921/921 | HISTORICAL_VALID | Do not re-run old 921 cases unless exact kernel touched |
| C02 | Historique: cinq aiguilles 8K réelles 3/3 | HISTORICAL_VALID | Only port fixture to current chimera; never rebuild the historic test |
| C03 | Historique: cinq aiguilles 16K réelles 3/3 | HISTORICAL_VALID | Only certify current chimera relevant context; keep 16330-token source benchmark |
| C04 | CI chimera native MMB MTP Turbo source / backend guard | CURRENT_PASS_LIMITED | Atomic2 native Vulkan Zen4+LTO compiler-tuned 11 ELFs deployed LAB ONLY in CT410; source cda0f925 unchanged, RPATH $ORIGIN patched in isolated binaries and ldd/--version/MTP adaptive flag PASS. No unqualified runtime performance claim; GPU correctness/prefill+decode comparisons need same exact Pym35B model and resource admission. Stable production unchanged. |
| C05 | CT410 router safe nonpreemptive, stable services | CURRENT_PASS_LIMITED | Current CT410 router source caught up from live deployed 29KB native Python and deployed patched SHA87c959b41cda. Fixed embedding_busy() wrong localhost:8091 bind; now uses configurable actual192.168.1.219:8091, fail-closed on API error/malformed slots. 25 targeted router tests PASS, restart only when router worker idle and zero connections, embedding service remained active with 4 processing slots. Remaining: real exclusive preemption/rollback test ONLY during idle maintenance, not while real embedding tasks running. |
| C06 | Chimera native Qwen4 real GPU 2K + strict read-only tool | CURRENT_PASS_LIMITED | Tool quality is only 1 case; incorrect technical suggestions in chat observed |
| C07 | OpenBMB MiniCPM5+DSpark live speed and tool | CURRENT_PASS_LIMITED | Not 3/3 scenario suite nor untouched OpenBMB weights |
| C08 | Current chimera long effective context 8K 16K and maximum useful | PARTIAL | Native GGUF advertises 262144 max; target agentic product 128K. Current 8K five-marker 3/3 PASS. 16K f16 strict PSI watchdog FAIL, 16K q8 no quality. Native LAB 32K 64K 128K q8_0 both caches gated and 3 preflights BLOCKED before GPU. Need genuine full-prompt 3x5-marker passes plus long-context agent tool performance and fallback before full production. |
| C09 | Functional agentic JSON tools coding and French regression | CURRENT_PASS_LIMITED | Chimera native strict simulated diagnostic tool selection 36/36 correct/0 unsafe. Atomic2 original Vulkan Qwen4 now 3/36 correct/0unsafe on IDENTICAL suite, then own-LAB watchdog correctly stopped at host PSI full2.20; native checkpoint preserved and resume supports immutable attempt logs, no duplicates, bound 20s transient PSI recovery. Atomic historical separate creative benchmark JSON3/9 tool6/9 code0/9 FR7/9 still fails general agentic QA. Complete same-suite and quality only after PBS storage contention resolved. |
| C10 | Multi-agent concurrency and performance envelope | CURRENT_PASS_LIMITED | C10 client queue 42/42 for fan-outs 1,2,4 across 3 repetitions; 21/21 safe tool selection, 21/21 streaming, p95 total 9.0427s, p95 first stream fragment 6.5728s. Native llama worker has ONLY one decoding slot, so real 2/4 GPU parallel decode, exact ITL and long soak remain. Test explicit native --parallel N safely before claiming full multiagent GPU production. |
| C11 | Host memory/GPU sharing/PBS stability reboot proof | BLOCKED_RESOURCE | 26 Oct service-only audit now covers 14 LXC (12 active,2 stopped), VM100/900 (HAOS no QGA), host and ~165 Docker containers. NEW actual fixes CT300 broken DaVinci PathChanged storm to native30m service timer (service test PASS), host completed ZFS rehab collector disabled (720 SMART+journal polling/day gone), native DaVinci GPU timer5->10sec (8640 starts/day less). Compose source health intervals Redis Netbox x2 CT1101s->15s, Dify PostgreSQL CT4001s->15s, DaVinci PostgreSQL CT3005s->15s VALIDATED but not applied to running Docker without targeted service recreation. Pending CT410 ComfyUI/Docling failed sockets and CT700 stale preview units, no unsafe kills. CT400 WAS accidentally stopped by stale shutdown job; restarted 09:11, all key apps confirmed healthy. NEVER STOP WHOLE LXC/VM FOR BENCHMARK. Full sanitized audit certification/CLOUD9_SERVICE_AUDIT_20261026.md and proofs. CT300 DaVinci native asset refresh timer now daily 06:15 (formerly 30min); tested active. Both davinci-agent-node and davinci-render-node have existing ExecStartPre davinci-render-preflight.sh, which invokes assets-refresh.sh --prestart; this does NOT prove every new queued job in an already-running Resolve node, for which Resolve21 native Deliver Trigger Script at Start is available but not yet attached. |
| C12 | Feature speed parity and Turbo KV real backend GPU | PARTIAL | Real Pym35B-A3B Q2 MTP same physical model run SUCCESS: Atomic2 stock partial_min ngl4 cpu-moe41 no MTP 2K ctx f16 KV, 768 tokens x3: maths8.974t/s correct 925, code6.956t/s text only, French8.598t/s text only, load2.516sec, 0 watchdog, 3/3 visible. This is strictly NOT historical Pym fullGPU MTP2 34.56 median/37.20math comparable or proven code quality. New matched192 trials: upstream MTP2 and base crash guarded PSI, Atomic2 Zen4/LTO base loaded7.496sec then paused PSI, stock192 denied preflight; unable to rank engines under current shared workloads. No production LLM worker switched, router&embedding healthy. Guard must NOT be bypassed, do not shutdown CT400 or any LXC; need safe memory/IO service-level improvement and genuine matched A/B quality/code/JSON 128K. Exact Pym35B Q2 Vulkan Atomic2 partial_min 2K ctx, same seed/prompts/tokens192: MTP2 math11.082/code10.726/French11.168 tok/s, 3/3 visible and 925 math; MTP3 math12.382/code11.117/French9.681, also 3/3 visible. MTP3 mean+0.61pct but French performance regressed, MTP2 balanced default pending repeated quality. Upstream b11844 MTP2 latest retry failed guardian before inference; Atomic2 MTP1+adaptive preflight blocked by host IO PSI from other workloads. No exact fullGPU 128K or agent QA. HOF now 203. |
| C13 | Four role-selected models and FlashNext >20 t/s | PARTIAL | User priority Flash-Next original AD-4.27bpw-Q4_K_M-M64 + Q8 FR-Spec, historic safe17.878t/s with Cloud9 RDNA b10738 MTP3 TurboQuant SET_ROWS CPU-WHT GDN OFF. Exact original weights absent locally; existing GSQ-RCO IQ1M coder 58.4GB distinct model/format and cannot be substituted. Public quant publisher mk2878d has 92.9GB overall with ~54.5GB resident and draft publisher drluoto has Q8 FR-Spec sidecar. Reacquire only when RAM/disk/guardian permits, never in shared loaded production with 25GiB MemAvailable. Pym baseline first. |
| C14 | OmniRoute Dify n8n Paperclip end-to-end | PARTIAL | Static native provider/agent services healthy, but live authenticated OmniRoute model enumeration: Chimera Qwen4 LAB NOT visible to Omniroute Master, N8N, IA CLI (HTTP200, 2541 IDs, 21 existing Cloud9 IDs). Must publish opt-in model via supported native provider-model management API (not SQLite), then validate OpenAI-compatible direct call via OmniRoute and real Dify/n8n/Paperclip multi-step workflows, permissions, fallback, rollback. Preserve existing 4-model Cloud9-Engine stable combo. |
| C15 | Controlled v1 release default / rollback and live monitoring | NOT_RUN | FAIL-CLOSED: no production promotion of any LLM. Pym true3/3 768-token base partial measurement on Atomic2 stock, actual comparative upstream/Atomic2 LTO at192 blocked due guardian memory PSI, no matched quality context >2K. Existing OmniRoute choices unchanged. Native timer/Compose source fixes documented; CT400 healthy after involuntary stop; explicit no whole-LXC shutdown rule. Revisit only when 780M safe coexistence, then canary24h rollback exact tasks. See sanitized service audit. No LLM prod promotion; incumbent router and embeddings remained running. Actual Pym MTP2/MTP3 192token 3 prompts measured; upstream watchguard and MTP1/adaptive IO PSI block. |

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
