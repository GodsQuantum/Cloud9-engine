# Architecture

Cloud9 Engine separates **source freshness**, **model-family performance**, **hardware truth**, and **production stability**.

```text
                           ┌─ upstream-pym     (known-fast Pym/MTP revision)
llama.cpp upstream + ──────┼─ upstream-fast    (mature Qwen3.6 / Gemma4)
Cloud9 RDNA patches        ├─ upstream-next    (MiniCPM5+DSpark / Ling winners)
                           └─ upstream-latest  (new architectures / compatibility)
                                      │
Prism ternary/PTQ ────────────────────┤
                                      ▼
                              cloud9-model-router
                                      │
                         one OpenAI-compatible endpoint

Atomic TurboQuant ── lab/donor only; never an automatic Radeon 780M route
```

## Production upstream profiles

The runtime may keep several **validated upstream+Cloud9 releases** at once. This is deliberate: on the reference Radeon 780M, different model families benchmark best on different llama.cpp revisions. A newer commit is not promoted globally merely because it is newer.

- **upstream-pym**: retained specifically for the fastest validated Pym/MTP path.
- **upstream-fast**: stable optimized path for mature Qwen3.6/Gemma4 workloads.
- **upstream-next**: intermediate validated revision currently winning on MiniCPM5+DSpark, Ling-3 and some small-model families.
- **upstream-latest**: compatibility path for newer architectures such as Qwen3.8-derived models and Spark-X2.5. Flash-Next remains research-only on the reference gfx1103/780M after an oversized local smoke test exhausted GTT and required a power-cycle.
- **Prism**: specialized backend for ternary/PTQ formats such as Bonsai 2 PTQ1_0.

The current upstream patchset is declared by `sources.lock["patchset"]`. Current HEADs receive only the Cloud9 RDNA delta that still applies cleanly. The older TurboQuant-heavy patch series is retained as legacy provenance rather than force-rebased onto every new upstream commit.

## Model router

Production traffic goes through `cloud9-model-router` and `config/model-catalog.json`. Each catalog entry defines:

- model path and aliases;
- validated backend runtime;
- context size;
- batch/ubatch and KV overrides when needed;
- MTP/DSpark draft configuration;
- benchmark metadata.

The router exposes one OpenAI-compatible API, keeps at most one LLM worker resident, acquires the shared GPU lock, refuses to preempt a busy embedding request, unloads idle LLMs, and restores the embedding service after the worker exits. It also rejects model files larger than 40 GiB by default; an explicit `CLOUD9_ENGINE_ALLOW_OVERSIZE=1` laboratory override is required to bypass that guard.

## Atomic policy

Atomic remains tracked because it can contribute useful ideas and may improve on other hardware or future releases. It is **not** an automatic fallback on the reference Radeon 780M. Atomic 1.7 reproduced Vulkan allocation/device-loss failures during the 2026-10-02 gate, so it requires an explicit laboratory override.

## Hardware gates

A candidate must not replace a known-good runtime merely because it builds. Gates verify GPU exclusivity, a real model load, repeated inference, and performance against an appropriate reference. Reference failure aborts promotion. Mixed GPU workloads are refused.

## Failure model

A failed patch application, build, model load, benchmark, or source refresh does **not** change production runtime links. Versioned releases remain available for rollback and family-specific routing.
