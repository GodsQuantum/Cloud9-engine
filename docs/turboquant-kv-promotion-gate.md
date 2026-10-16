# Optional TurboQuant KV — qualification gate (2026-10-17)

TurboQuant on Radeon 780M is a **memory optimization**, not automatically a faster agent runtime.

The existing multi-runtime router remains the production default. Atomic TurboQuant is a separately pinned candidate; no automatic replacement of a backend, cache quantization or model alias is allowed.

## Promotion contract

Use the **same** GGUF bytes/SHA, runtime commit, GPU, context, batch size, sampling parameters, identical prompts and three or more complete repetitions. A workload must exercise at least 8K input tokens at 32K context and a read-only tool call with a typed ISO date. Capture the full outputs; reject malformed function-call arguments, missing data, KV corruption, OOM and device-loss.

Invoke the fail-closed gate against a private evidence JSON:

`python3 scripts/turboquant_kv_gate.py evidence.json --candidate q8k-turbo4v --json`

The gate rejects a baseline or candidate with any failing repetition, over 5% latency regression on long retrieval, over 15% on read-only tools, or less than 20% **isolated KV allocation** savings. RSS alone and systemwide GTT readings are not proof of KV savings because they include other allocations.

Recommended quality-first profiles to *compare*, not blindly deploy:
- F16/F16 baseline.
- K=q8_0, V=turbo4: keeps attention keys higher-precision.
- K=q8_0, V=turbo3: greater V compression but potentially worse accuracy.

This codec choice is not compatible with every backend or model. Do not relax the shared GPU memory guard, alter bind mounts, delete model files or publish private operational evidence.

## Release requirements after an eligible gate

Only after true hardware A/B and CI pass: add an **opt-in model specialization** referencing a versioned, SHA-verified runtime. Preserve all existing OmniRoute choices and IDs. Validate actual full chat and typed-tool round trips through ordinary restricted client credentials, rollback and restart behaviour. A positive synthetic test is not proof of end-to-end agent reliability.

A failed candidate belongs in the single historical Hall of Fame as rejected/unpromoted, without setting a speed or quality podium.
