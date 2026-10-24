# 25 October 2026 - Cloud9 native chimera certification progress
No production-default switch or interruption of PBS/VoiceStudio/AutoSubs/embeddings.

## C08 actual Qwen4 Vulkan 8K
- Master9ae fused source, context allocated 8704, reused historical deterministic five-marker fixture, Qwen4 Heretic Q4_K_M with native MTP2 and f16 KV.
- Two actual seeded repetitions both consumed 8026 tokens and returned JSON containing all 5 correct markers. Pass count 2/3 in one LAB run; attempted third stopped under host PSI memory full 2.31, not attempted.
- First repetition prefill 325.19 tokens/s, decode 8.035 tokens/s. Second prefill 273.62, decode 8.622 tokens/s. The earlier independent first run was also 5/5 but repeats the first seed, so it cannot replace the missing third seed.
- Measured 8K throughput is markedly slower than the 2K short-tool 33.76 tokens/s; do not advertise 33.76 tokens/s at 8K.
- Evidence JSON with SHA in certification registry: Sources/Worklogs/2026-10-25_CHIMERA_MASTER9AE_8K_2OF3_VERIFIED.json. A separate earlier 1/3 proof also preserved. C08 PARTIAL, not release-certified. 16K on current binary NOT RUN.
- Current LAB script tools/chimera/lab_chimera_existing_five_needles.py has a safe --rep-start 3 --rep-end 3 mode: rerun only the missing seed when official GPU guardian admits, not the two proven cases.

## C09 current Qwen4 native tool benchmark
- Read-only simulated Proxmox fixture pve-ct300-mount: selected exactly one correct pve.get_ct_config tool, strict JSON, no unsafe call, 805 prompt tokens prefill 403.42 tok/s, 32 generated at 34.58 tok/s, wall 6.659 seconds including load.
- After this first case host PSI-full rose to 0.65, benchmark saved and stopped. Thus 1/36 correct, 35 not executed. Do not claim 36/36.
- The existing tools/local_agents/bench_native_agent_tools.py was enhanced with opt-in --allow-lab-load, --resume, immutable fixture hash, case-id and repetition checkpoints, no duplicate replay, safe non-preemption, native guard before new loads and survival pressure checks after load. A 20-second transient PSI decay window avoids unnecessary repeated model loads.
- Evidence: Sources/Worklogs/2026-10-25_CHIMERA_C09_CHECKPOINT_1OF36.json. Active checkpoint remains in CT410 LAB .../local-agent-readiness-20261024/chimera_C09_checkpointed_12x3_20261025.json, and can be resumed with --execute --allow-lab-load --resume.
- New safety/unit tests cover checkpoint idempotency, partial resume, dangerous tool abortion, guardian deny and worker preservation. 221 total Python tests PASS.

## Safety and project integrity
- Host swap nearly 19 GiB out of 19.52 GiB; fluctuating memory PSI refuses many GPU start attempts. No guard relaxed, no swapoff, no forced cache drops, no reboot or service stop. PBS job cloud9-daily-pbs enabled=1 / 00:30.
- HALL_OF_FAME.json updated via the existing native --append-stdin (190 -> 192 records), validated 1344 evidence refs. Partial status clearly marked in new records.
- Canonical release registry C08 PARTIAL and C09 PARTIAL; 6 production gates remain, full universal feature gates still not closed.
