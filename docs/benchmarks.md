# Benchmark notes

These numbers are **hardware-specific measurements, not universal performance claims**.

Reference platform: AMD Ryzen 7 8845HS, Radeon 780M / RADV (Phoenix/Hawk Point RDNA3 UMA), Linux, 16 Sep 2026. Model: local Qwen3.6-35B-A3B Pym Q2 with its matching MTP sidecar.

## RDNA runtime autotuning

The old production profile used `b=2048`, `ub=512` and `--no-host`. On this APU that was suboptimal for decode. The validated balanced profile uses `b=1024`, `ub=1024`, 8 threads, `poll=100`, `poll-batch=0`, FlashAttention on, host buffers enabled, lazy loading off, and `RADV_PERFTEST=nogttspill`.

With the same MTP2 workload (3×256 completion tokens), tuned upstream+Cloud9 reached **34.40 t/s median** versus **32.99 t/s** for tuned Atomic 1.6.0: about **+4.3%** on this host.

## RDNA3 UMA sparse-MoE kernel

Cloud9 adds a high-aspect 128×32 `MUL_MAT_ID` large tile only for AMD RDNA3 + UMA + RADV + KHR cooperative matrix. Other vendors/drivers keep upstream behavior. Vulkan correctness: **921/921 MUL_MAT_ID tests passed**.

| Prompt test | Upstream+Cloud9 baseline | + RDNA MMID tile | Gain |
|---|---:|---:|---:|
| pp512, first A/B | 337.19 | 393.03 | +16.6% |
| pp2048, first A/B | 360.95 | 387.25 | +7.3% |
| pp4096, first A/B | 352.66 | 373.74 | +6.0% |
| pp512, reverse-order 5-run | 342.40 | 362.49 | +5.9% |
| pp2048, reverse-order 5-run | 378.83 | 391.56 | +3.4% |
| pp512, production chat profile | 337.14 | 397.50 | +17.9% |
| pp2048, production chat profile | 381.72 | 404.61 | +6.0% |

Decode-only reverse-order 7-run A/B was **22.504 vs 22.633 t/s**, showing no measurable decode regression from the MMID tile.

## Reproduce

Use `cloud9-engine build` followed by `cloud9-engine gate MODEL`. For a focused prefill run, use `CLOUD9_ENGINE_RDNA_PROFILE=prefill`. Thermal state, Mesa/RADV version, model quantization and MoE routing shape can materially change results, so publish your own A/B when reporting another GPU.
