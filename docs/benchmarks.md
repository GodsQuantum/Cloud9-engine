# Benchmark notes

These numbers explain the routing design; they are **not universal performance claims**.

Reference platform: AMD Ryzen 7 8845HS with Radeon 780M, Mesa/RADV Vulkan, Linux, September 16 2026. Same local Qwen 3.6 35B-A3B Pym Q2/MTP model and matching runtime parameters were used for the comparisons below.

## Raw llama-bench

| Engine | Prefill | Generation |
|---|---:|---:|
| Atomic 1.6.0 | ~301.0 t/s | ~21.67 t/s |
| previous Cloud9 champion | **~341.8 t/s** | **~21.91 t/s** |
| current upstream + Cloud9 patches | ~334.6 t/s | ~21.56 t/s |

## MTP chat, 3 × 256 completion tokens

| Engine | Median decode | Median wall time |
|---|---:|---:|
| Atomic 1.6.0 | **~33.26 t/s** | **~8.51 s** |
| previous Cloud9 champion | ~31.29 t/s | ~9.05 s |
| current upstream + Cloud9 patches | ~31.90 t/s | ~9.00 s |

Atomic wins this longer MTP protocol, while the much newer upstream Vulkan tree wins strongly on prefill. A shorter 128-token MTP probe favored the upstream+Cloud9 candidate, which is another reason not to hard-code one global winner.

## Reproduce

Use `cloud9-engine build` followed by `cloud9-engine gate MODEL`. The public gate deliberately uses a generic prompt; for production you should gate with a model and context shape representative of your own traffic.
