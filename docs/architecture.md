# Architecture

Cloud9 Engine separates **source freshness**, **hardware truth**, and **production stability**.

```text
llama.cpp upstream ─┐
                    ├─ build candidates ── hardware gate ── current/upstream
Cloud9 patchset ────┘

Atomic TurboQuant ───── build candidate ── hardware gate ── current/atomic
                                                        │
                                                        ▼
                                               cloud9-llama-server
                                                        │
                                         auto / upstream / atomic
```

## Upstream + Cloud9 profile

The upstream profile starts from the exact commit recorded in `sources.lock` and applies the mail patches in `patches/upstream/`. The current patchset carries the TurboQuant KV types and the Vulkan plumbing still missing from the tested upstream revision: CPU/WHT contract, Vulkan `SET_ROWS`, FlashAttention decode, and llama-bench cache-type support.

## Atomic profile

Atomic is built from its locked source without pretending those features are Cloud9 inventions. It currently provides mature TurboQuant/speculative paths that can outperform the newer upstream path on some longer MTP workloads.

## Routing

The production wrapper defaults to the freshest validated upstream build for ordinary inference and to the locally selected MTP backend for MTP/NextN-style requests. `CLOUD9_ENGINE_BACKEND` can override routing per process.

## Failure model

A failed patch application, build, model load, or hardware benchmark does **not** change production symlinks. Versioned releases remain on disk until an operator or retention policy removes superseded builds.
