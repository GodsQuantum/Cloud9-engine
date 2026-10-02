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


## October 2, 2026 bake-off — model-specific routing

The October bake-off intentionally stopped treating one llama-server configuration as optimal for every architecture.
All figures below were measured on the same Ryzen 7 PRO 8845HS / Radeon 780M Cloud9 host. They are local
engineering measurements, not claims about other hardware.

### Small-model shortlist

| Cloud9 model | Model / quant | Backend profile | Context | Decode | AutoPublisher | Agentic |
|---|---|---|---:|---:|---:|---:|
| Cloud9-MiniCPM5-2B-DSpark | MiniCPM5-2B Heretic Q6_K + official 2.6B DSpark drafter | upstream-next + DSpark | 16K | 47.73 t/s (historical run ~51.3) | 75/100 | 100/100 |
| Cloud9-Ling3-Tiny-Uncensored | Ling-3.0-tiny abliterated APEX I-Balanced | upstream-next | 16K | 44.41 t/s (historical run ~48.3) | 85/100 | 100/100 |
| Cloud9-LFM2.5-2.6B-Uncensored | LFM2.5-2.6B uncensored Q4_K_M | upstream-latest | 16K | 34.98 t/s (screen ~38.6) | 75/100 | 100/100 |
| Cloud9-Qwen3.8-4B-Heretic | Qwen3.5-4B target distilled from Qwen3.8, Heretic, Q4_K_M, inline MTP | upstream-latest + MTP2 | 16K | 25.81 t/s; best short run 28.35 | 95/100 | 100/100 |

For the selected Qwen3.8-distilled 4B MTP model, the real DPAFM48 AutoPublisher prompt (~11K tokens)
measured ~398.9 prompt tokens/s and ~22.9 generated tokens/s. The bounded structured-output gate produced a
159-character caption, six grounded chapters and valid JSON.

Spark-X2.5-4B uncensored Q4_K_M remains in the laboratory pool. It reached ~22.62 t/s and 85/100 on the strict
editorial gate, but failed the current two-step tool-calling probe, so it was not selected among the four
production small models. Q6_K was slower on this APU.

### Large / MoE / ternary shortlist

| Cloud9 model | Backend profile | Context | Measured behavior | AutoPublisher | Agentic |
|---|---|---:|---|---:|---:|
| Cloud9-Pym-35B-A3B-MTP | upstream-pym (37b53) + inline MTP2 | 8K | 30.87 t/s median (3 runs); historical best 34.40 | — | — |
| Cloud9-Qwen3.6-35B-A3B-Heretic | upstream-fast + inline MTP2 | 16K | real long-prompt ~228.4 prompt t/s / ~10.3 decode t/s | 95/100 | 100/100 |
| Cloud9-Gemma4-26B-A4B-MTP | upstream-fast + external Q8 MTP drafter | 16K | ~25.79 t/s | 90/100 | 100/100 |
| Cloud9-Bonsai2-27B-Ternary-Abliterated | Prism 79971a, PTQ1_0 | 16K | ~8.59 t/s bake-off; isolated A/B 7.50 t/s | 90/100 | 100/100 |

Bonsai 2 must use PTQ1_0 on the current Radeon/Vulkan path. PQ2_0 was deliberately removed from the Vulkan
comparison because the relevant Prism path does not provide the same optimized Vulkan kernels. An isolated A/B
on the exact PTQ1_0 model measured Prism 79971a at 7.50 t/s / 17.03 prefill t/s versus Prism 88c4bc at
7.43 t/s / 15.36 prefill t/s, so the older validated Prism runtime remains promoted.

### Why Pym numbers differ so much

Context size is a first-order tuning parameter on this APU. Pym at the production/gate 8K context still reaches
~26–31 t/s in recent repeat runs, while generic 16K bake-off runs can fall near 9–11 t/s. The historical
34.40 t/s figure used the tuned 8K MTP2 profile. For this reason the production model router carries a context
and backend profile per model instead of imposing a global 16K server.

### Runtime selection on October 2

- **upstream-pym** — older upstream+Cloud9 release retained specifically because it remains fastest for Pym.
- **upstream-fast** — validated upstream+Cloud9 release for Qwen3.6 / Gemma4 and compatible mature models.
- **upstream-latest** — newer llama.cpp/Cloud9 path used where current model support and measurements win
  (Qwen3.8-derived models, LFM2.5-2.6B and other recent architectures). Flash-Next is not a production route on the reference 780M.
- **upstream-next** — intermediate validated release that currently wins for MiniCPM5+DSpark, Ling-3 and some
  small-model families.
- **Prism** — specialized ternary backend for Bonsai PTQ formats.
- **Atomic** — laboratory-only. Atomic 1.7.0 reproduced AMD Vulkan allocation/device-loss failures on the 780M
  during the October 2 gate and is never selected automatically.

The public Cloud9 endpoint remains one logical engine. The model router selects the runtime, context and
speculative-decoding profile internally and keeps at most one LLM worker resident.

### AutoPublisher quality protocol

The DPAFM48 fixture is a frozen transcript excerpt/pack from the real AutoPublisher pipeline. The strict gate
requires schema-constrained JSON with exactly six chronological grounded chapters, bounded title/caption fields,
no invented guests/URLs/facts and a short French caption. A separate two-step tool probe requires the model to
call `search_transcript(DPAFM48)` and then `create_social_draft(..., platform=Instagram)`.

Raw per-run JSON and server logs are retained under `bench/results/2026-10-02/`; the production-facing summary
is the model catalog in `config/model-catalog.json`.
