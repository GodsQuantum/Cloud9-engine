# Cloud9-engine — 25 October 2026 17:33 Paris
## C09 — real opt-in agent tools
Resumed the existing C09 checkpoint (1/36) with the native CT410 harness, simulated read-only tools, guarded model route and no replay.
- Added `pbs-task-integrity` rep1, strict correct function, no unsafe execution, latency 11.433s.
- Checkpoint now 2/36 complete and 2/2 correct; remaining 34 untested.
- Next case stopped because post-load guardian observed memory pressure. Do not mark C09 complete. Never rerun the two prior cases; resume from the same CT410 checkpoint.
- Frozen exact checkpoint proof: Sources/Worklogs/2026-10-25_CHIMERA_C09_CHECKPOINT_2OF36_VERIFIED.json
## C12 — experimental Turbo3 negative result
- Verified existing real 8K record 2026-10-25_CHIMERA_QWEN4_8K_TURBO3_VULKAN_FAILED.json: K q8_0/V turbo3/batch512, prompt 8026, decode3.51 t/s, five-marker quality FAIL. Do NOT promote. Keep historical Atomic TurboQuant2 results distinct; wrong outputs cannot qualify as a speed win.
- Existing uncommitted opt-in runner quality block for turbo3 is preserved as-is (owned by other checkpoint); do not reset, stash, or blindly commit.
- Alternative K/V q8_0 also has an incomplete attempt, not proof of correctness or speed; do not automatically retry.
## C08
- Current Qwen4 8K remains 2/3; seed3 stopped after load at 02:13 with no inference. Avoid duplicate 1/3 and 2/3 tests.
## Nemotron candidates (official NVIDIA/Hugging Face data; NOT Cloud9 benchmarks)
- NVIDIA Nemotron 3.5 Bolt 74B-A9B 24GB, released 2026-10-15. LatentMoE hybrid Mamba-2/Transformer; 74B total, 9B active, IQ2 24GB packed, multimodal and 256K advertised max. Official source: https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB
- The official stated >=80 tok/s target concerns NVIDIA RTX/DGX Spark, NOT Radeon780M. Its 24GB packed weights would consume nearly all current ~24-25 GiB MemAvailable before context and buffers, so fails conservative LAB admission. No download/compilation/inference.
- NVIDIA Nemotron 3.5 Bolt E4B 4GB, released 2026-10-23. Derived from Gemma 4 E4B, 8B total/4B effective, Q4_K_M Hugging Face displayed GGUF 6.18GB (marketing model name '4GB' is not reliable as literal RAM requirement), text only, ctx max 64K. https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-4GB
- Consider E4B as candidate for 4B voice/device/agent comparison only AFTER validating actual GGUF, llama.cpp format support, 780M memory preflight and 36-case functional quality. Do not add to OmniRoute defaults or claim TPS without real measurements.
## Rules
- PVE/zpool/VMs/PBS/OmniRoute untouched; runtime LLM worker unloaded after C09. Keep all GPU/memory guardians.
- ZFS pools currently healthy, but sustained nontrivial host IO PSI and fluctuating memory PSI complicate measurements.
