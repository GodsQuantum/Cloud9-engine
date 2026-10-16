# Cloud9 inference backend qualification — 2026-10-16

**No unvalidated promotion.** This file records source-only release choices, not
a deployed runtime change. Production stays pinned to the best Hall of Fame
per-model backend until quality, latency, GPU safety and rollback all pass.

| Backend | Source and commit | Cloud9 Radeon 780M evidence | Decision |
|---|---|---|---|
| Existing Cloud9 multi-runtime router | current versioned backends | 8 specialist models in OmniRoute; real OpenAI-compatible chat, JSON and tool-call tests | Retain |
| ggml-org/llama.cpp | v0.7.0 `620d2225` + RDNA3 patch | 9/9 synthetic tool/JSON; 3/3 exact long retrieval; long prefill 332 versus 435 tok/s current production, same Q4_K_M MTP model | Not promoted: long-context regression |
| Atomic TurboQuant llama.cpp | b10298-2.0.0 `cda0f925` | Vulkan SET_ROWS 343/343; same Qwen3.8 4B GGUF FR F16 and Turbo3 each 4/4 correct, Turbo3 prefill 304 versus F16 318 tok/s | Candidate only; 16K/32K KV RAM savings unmeasured |
| Strata gfx1103 HIP | v0.1.44.1 fork | PLE table / 333 GPU experts initialized, but **no final generated token**; host memory guard terminated 125B runs under pressure | Lab only, do not bypass host guard |
| ZINC | `29bc350` | 9/9 synthetic tasks with MTP disabled; MTP enabled returned corrupted output | Lab only: slower complete answers |
| Xenolith | `88e8661` | Intel Level Zero only; incompatible with Cloud9 AMD vendor 0x1002 | Not deployable |

**Atomic Chat is the desktop app**, not the runtime. Its separate fork
`AtomicBot-ai/atomic-llama-cpp-turboquant` is pinned in `sources.lock`.
Do not transplant that complete, older ggml base into newer upstream without
ABI validation; selectively port features only when measured. TurboQuant KV
quantization is a memory optimization that can cost compute time; it is
**not** an automatic tokens/s improvement. Atomic `--moe-cache` and official
v0.7 `--moe-cache-mib` are different APIs: never silently intermix them.

## Required gates before changing production

1. Verify upstream official release, exact SHA, build flags, patches, CI and
   HIP/Vulkan support. No personal data, transcripts, credentials, addresses
   or private filesystem paths in this public source repository.
2. Respect the host GPU memory guard. Its **start preflight may refuse**
   experiments when MemAvailable is below its floor. Never weaken that guard
   to manufacture a benchmark.
3. Compare exact GGUF SHA, quantization, context, cache settings, prompts,
   thread count, token budgets and 3+ repetitions. Record cold start,
   prefill, decode, end-to-end wall time, GTT/RAM and output correctness.
4. Require real OpenAI-compatible tool calls plus follow-up messages, JSON
   schema checks and read-only agent integrations. Date arguments must have
   `{"type":"string","format":"date"}` with ISO `YYYY-MM-DD`
   examples; arbitrary natural-language dates failed earlier tests.
5. Preserve rollback, production model names, four restricted OmniRoute
   client profiles and Embedding 1024-dimensional vector compatibility.
   Archive every failed candidate in the **single** Hall of Fame but do
   not promote the failed candidate to its production podium.

Full measurements and SHA evidence remain in the private canonical Cloud9
project worklogs. This document deliberately excludes machine paths and
personal data.
