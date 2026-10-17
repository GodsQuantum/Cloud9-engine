# Cloud9 RDNA3 Vulkan engine tournament — 2026-10-17

**Status: lab results only. NOT a production promotion.**

This benchmark isolates the **runtime comparison** from the **model comparison** on Cloud9 Ryzen 7 8845HS with Radeon 780M RADV Vulkan. The same Qwen 4B Q4_K_M GGUF and SHA were tested on upstream llama.cpp `9d1878a`, Atomic TurboQuant 2.0 `cda0f92`, and Atomic development `3cde9e4`. Competing models (Agents-A1, Sharp-Spark, Qwen 9B) are **not** evidence that one runtime is better than another with identical weights. The scoreboard has timings and task-quality classifications.

Files:
- `vulkan_engines_atomic_dev.py` — source for repeatable JSON, read-only tool, Python code repair, French creative and prefilling tests, with response scoring.
- `TOURNOI_CLOUD9_ETAPE1_SCOREBOARD.md` and `.json` — summary, incomplete trials explicitly marked, evidence filenames referring to the **local private Hall of Fame**, not reproduced in this public repository.

**Safety**: Execute only on authorized Cloud9 CT700 under a **real external PVE GPU admission guard and CT410 GPU arbiter lease**. The `CLOUD9_GPU_COEXIST_ADMITTED` environment check in the script does **not** acquire a lock; never set it alone. The host runner polls Tctl and GTT, terminates only its own worker at safety thresholds, and refuses concurrent production GPU clients. This repository intentionally does not publish Cloud9's internal addresses, tokens, credentials, worklogs or private deployment state. Never launch production writes from the public benchmark.

Optional environment overrides: `CLOUD9_MOTEURS_ROOT` and `CLOUD9_GGUF_ROOT`; the default paths reference the pre-existing canonical CT700/host layout.

Results exclude full-depth context; 8K was the allocated context capacity and most prompts were short. **128K is a lower bound goal, not a ceiling**, and future gates should find each finalist's maximum verified useful context with multi-position retrieval, tool calling, prefill, memory and thermal constraints.

No binaries, GGUF weights, secret logs or raw private handoffs are committed here.
