# Cloud9 Engine - matrice canonique de certification

Date du registre: 2026-10-25

Moteur disponible sur demande: Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB
Hall of Fame: 192 records; 78 raw proofs mirrored with SHA on GitHub.

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
| C11 | Host memory/GPU sharing/PBS stability reboot proof | BLOCKED_RESOURCE | 26 Oct new LIVE PBS policies: prune daily20:30 3last14daily8weekly12monthly3yearly active; verify-new false, one weekly verified Sat12 with1read1verify and30day overdue recheck; GC Sun04 preserved. Real CT110 metadata dual backup 69s first then10s second with99.7pct data reuse; phase1 native PVE daily09:00 CT110/120/200/9500/9600, prior daily00:30 keeps ten remaining with no overlap. Phase2 must migrate heavy LXC cautiously, 80pct datastore used, ~745GB free. Cloud host backups already native metadata (no duplicate). Host timers zfsrehab5sec=>120s, ops8=>30s, PBS check15min=>3h, finished one-time scrub transition disabled; verified no production service restart. PBS GC last18h warnings2 removed-bad12 unresolved; xfs_scrub and GC on Sunday may overlap, investigate; no disabling backups or native monthly verification. Cloud9 still ~25GiB MemAvailable, CT400 CloakBrowser3.1GiB/Hindsight1.8GiB, need safe session TTL/cgroup optimization to release enough memory for full Pym bench without violating guardian. Full details certification/CLOUD9_FIVE_PRIORITIES_PBS_MOE_20261026.md. |
| C12 | Feature speed parity and Turbo KV real backend GPU | PARTIAL | Same exact Pym35B Q2 MTP remains primary, FlashNext original distinct second. LAB Pym partial loaded 2.405s but stopped by official watchdog at MemAvailable18.57 GiB after PBS verify pause; no decoded result. Active old production LLM worker null, embedding service separately active ~0.8GiB. Need ~10GiB real freed RAM to permit full GPU 8K; do NOT turn off VM HAOS/PBS, interrupt agents CT400 or weaken guard. Atomic2 Zen4/LTO compiled and staged but gain unproven. Reproduce features of Hall of Fame winners across engines at same GGUF; 8->128K context and quality gates still pending. |
| C13 | Four role-selected models and FlashNext >20 t/s | PARTIAL | User priority Flash-Next original AD-4.27bpw-Q4_K_M-M64 + Q8 FR-Spec, historic safe17.878t/s with Cloud9 RDNA b10738 MTP3 TurboQuant SET_ROWS CPU-WHT GDN OFF. Exact original weights absent locally; existing GSQ-RCO IQ1M coder 58.4GB distinct model/format and cannot be substituted. Public quant publisher mk2878d has 92.9GB overall with ~54.5GB resident and draft publisher drluoto has Q8 FR-Spec sidecar. Reacquire only when RAM/disk/guardian permits, never in shared loaded production with 25GiB MemAvailable. Pym baseline first. |
| C14 | OmniRoute Dify n8n Paperclip end-to-end | PARTIAL | Static native provider/agent services healthy, but live authenticated OmniRoute model enumeration: Chimera Qwen4 LAB NOT visible to Omniroute Master, N8N, IA CLI (HTTP200, 2541 IDs, 21 existing Cloud9 IDs). Must publish opt-in model via supported native provider-model management API (not SQLite), then validate OpenAI-compatible direct call via OmniRoute and real Dify/n8n/Paperclip multi-step workflows, permissions, fallback, rollback. Preserve existing 4-model Cloud9-Engine stable combo. |
| C15 | Controlled v1 release default / rollback and live monitoring | NOT_RUN | No LLM production promotion; native backup/policy/timer fixes are in production and verified, stage1 migration backup union exact. Cloud9 persistent five-priority handoff updated, Git evidence hashes mirrored. Complete stage2 native PVE LXC metadata rollout, run first automatic phase1 09:00, inspect prune20:30, GC warnings and PBS verification completion; verify restore samples; then resource audit and true Pym/Flash A/B only with eligible guard, full tool/code/concurrency/long-context/canary/rollback. |

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
