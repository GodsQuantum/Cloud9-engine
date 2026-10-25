# Cloud9 Engine C09 — 25 October 2026, 21:15 Europe/Paris
## Objective and scope
Resumed exact checkpoint from 2/36 through the CT410 native GPU router, Qwen4 MTP Vulkan LAB, simulated read-only tools. No agent infrastructure operations were executed.
- Completed 28 of 36 unique (rep,fixture) cases: first rep 12/12, second rep 12/12, third rep 4/12; strict JSON 28/28, expected tool selected 28/28; unsafe tool selected 0/28.
- Remaining eight fixtures in THIRD repetition only, starting next from omniroute-admin-mcp rep3. Do not repeat any of the first 28.
- Median API response latency 2.320 seconds, maximum 11.433 seconds across observed 28. These are per-call numbers; do NOT extrapolate to p95 36-case production service performance.
- PAUSED_RESOURCE_PRESSURE on guardian after the 28th success: MemAvailable approx 20.926 GiB at stop, hard conservative guard rejects preemptive continuation; after worker exit 25.123 GiB and PSI memory low. Do not lower guard / drop caches / swapoff / suspend PBS or HAOS.
- Native checkpoint remains at CT410 lab-releases/local-agent-readiness-20261024/chimera_C09_checkpointed_12x3_20261025.json and is resumable via --execute --resume --allow-lab-load. Exact fixture SHA256 validated against the file on CT410; no replay.
- Snapshot: Sources/Worklogs/2026-10-25_CHIMERA_C09_CHECKPOINT_28OF36_VERIFIED.json. Git mirror SHA256 locked.
## Distinct gates
C09 still PARTIAL until 36/36 full third repetition and FR/coding regression. C08 still 8K 2/3 without successful seed3. C10 1/2/4-worker native concurrency not yet certified. C12 experimental NextN A/B has no matched GPU quality result.
## Runtime change
None. Production router returned to idle and all model services untouched; no PVE restarts or threshold changes.
