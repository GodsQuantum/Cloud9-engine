# Cloud9 Vulkan same-GGUF S1 v61 engine tournament — 18 October 2026

This is public-safe **experimental** measurement and scorer code. It is NOT a chimera, production build, context-128K certification or an inference deployment. Run the backend only in an isolated development environment with a separate external GPU admission arbiter and host thermal watchdog. The script's CLOUD9_GPU_COEXIST_ADMITTED environment variable **does not implement the lease**, do not set it manually without the actual host-side lock.

Identical GGUF SHA, KV F16/F16, ctx8192, Vulkan RADV Radeon780M, speculative decoding OFF, flash attention ON, three repetitions per scenario. Each same-weight pair compared S1 20abe83b vs upstream llama.cpp 9d1878a, both separately built on Cloud9. Pym Q2 GGUF model size 13.22 GB requires resource admission before launch.

| Benchmark | Upstream llama.cpp | S1 v61 |
| --- | ---: | ---: |
| Qwen3.8 4B IQ3 tool latency, median | **2.325s** | 3.029s |
| Qwen3.8 4B IQ3 tool prefill | **318.005 tok/s** | 211.552 tok/s |
| Qwen3.8 4B IQ3 tool decode | 27.191 tok/s | 27.188 tok/s |
| Pym Qwen3.6-35B-A3B Q2 tool latency | **3.092s** | 4.277s |
| Pym Qwen3.6-35B-A3B Q2 tool prefill | **221.799 tok/s** | 136.282 tok/s |
| Pym Qwen3.6-35B-A3B Q2 tool decode | **21.506 tok/s** | 20.694 tok/s |
| Correct read-only tool call / JSON simple (each model) | 6/6 | 6/6 |
| Code semantically correct, Pym | 3/3 | 3/3 |
| Code as literal strict JSON, Pym | 0/3 | 0/3 |

**Scoring correction**: The initial Python code scorer stripped triple-backtick Markdown fences, so its permissive 2/3 upstream vs 0/3 S1 score was NOT a measure of *literal strict JSON*. All raw responses were audited offline without regenerating: both engines correctly fixed the maths (3/3), but neither followed the required raw JSON format (0/3). The corrected audit file is included; older historical raw evidence remains private on Cloud9.

The v61 fork's large-context QSA/GDN/MTP work on Flash-Next and Qwen35 at depth 32K/72K remains **untested locally**. No overall winner selected, no four final models chosen. More fork, Strata, memory/coexistence and long-context work remains.

Files: three curated JSON summaries, and benchmark scorer source (with configuration environment overrides). **Do not publish** host watchdog scripts with internal addresses, tokens, raw logs, private handoff or model files.

Upstream source: https://github.com/vahpetr/llama.cpp-s1-fork
Technical thread: https://github.com/ggml-org/llama.cpp/discussions/30282
