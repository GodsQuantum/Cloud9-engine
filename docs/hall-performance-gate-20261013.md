# Cloud9 Engine — immutable Hall of Fame performance gate (13 Oct 2026)

**Purpose**: protect against benchmark regressions from new llama.cpp, Atomic, Prism or Strata releases, new GGUF/Strata quants, MoE caches, MTP/speculative, Vulkan and ROCm settings. **This is a CPU-only, fully offline comparison tool, not a live GPU benchmark or deployment tool.** No routes, runtime binaries, Proxmox/LXC, mounts or n8n workflows are changed.

Canonical Hall of Fame stays **ONE file** at `/srv/storage/cloud/arezki/Projets/HomeLab/Moteurs IA/HALL_OF_FAME.json`. This script reads it; it never creates another performance ledger. Source: `scripts/hall-performance-gate.py`, tests `tests/hall-performance-gate-test.py` (14 Python tests PASS).

## Comparing a recorded candidate (read-only)

```bash
python3 "Cloud9 Engine/scripts/hall-performance-gate.py" \
  --hall HALL_OF_FAME.json \
  --candidate /path/to/new-benchmark-record.json
```

Return codes: `0` means **only that the numeric parity gate is eligible for further separate hardware and workflow gates**; **it NEVER approves promotion**. `2` means a measured speed, memory, latency, or quality regression. `3` means incomparable/insufficient evidence. `4` indicates invalid input. Output is JSON without logging user transcript or private contact details. `--relative-tolerance 0.05` defaults to 5% on decode/prefill/wall/GTT medians; editorial quality score can fall **at most 2 absolute points**. For actual model promotion the quality threshold should be tuned per use case (e.g., zero regression on personal writing style and tool correctness).

Candidate **and** baseline record must contain:
- `validation="validated_in_source"`;
- `configuration.base_weights_fingerprint`: **real SHA256 of shared original model weights**, not the model name or arbitrary hash. Changing quant can change output/quality even with same base weights.
- `configuration.quantization_scheme`: exact comparable encoding/settings, not just advertised bpw. Cross-engine comparison is permitted only if base weight fingerprint and quantization scheme are genuinely comparable across engines. Strata converted pack weights and GGUF files are not inherently identical.
- `context.benchmark_protocol_id`, `fixture_sha256`, and `context_tokens` all equal.
- `metrics.repeated_runs`: minimum **three** independently measured successful entries; each must include `status:ok`, `decode_tps`, `prefill_tps`, `wall_s`, `quality_score` (0–100), `peak_gtt_bytes`. Any missing, NaN, failed, or nonpositive speed value blocks comparison.
- `sources`: point to original machine evidence preserved privately; avoid copying podcast transcripts or private mail information to public GitHub.

The tool selects the **fastest eligible matching baseline**, rather than quietly comparing against the slowest historical run. It takes medians of the three or more real repeated runs, compares **all five dimensions** and reports each regression explicitly. Even a numerically better result only returns `eligible_for_separate_hardware_and_agent_gates` with `eligible_for_promotion=false`, because a full host test (GPU reset/stability, text quality, correct tool calls, real AutoPublisher V22/Archie dry-run, RAM/GTT impact, concurrency, cold reload, p95) is still necessary.

**Current historic Cloud9 records do not contain all required SHA256 and repeat/quality counters**. The gate therefore correctly answers `incomparable` for these records; the old measured speed data remain valuable in the Hall, but **cannot be transformed into a pass for a brand-new engine automatically**. A correctly repeated same-GGUF benchmark with complete fingerprints can be compared going forward.

## Comparison safeguards

- Never compare a Strata kernel in microseconds to llama.cpp in tokens/second, or WhisperX word timing against ASR WER/RTF.
- Never compare Pym Q2-MTP2 with Heretic I-Compact or Qwen3.8 Distill Q4 by only matching the parent family name.
- Never mix short test with 14,811-token transcript, warm-cache with no-cache, different contexts/temps, batch/ubatch/MTP2 vs MTP3 or output schema.
- Preserve old passes, failures, device-loss errors, and changes to UMA/GTT or memory pressure. GTT cannot be understated by checking only effective VRAM.
- On the wedged Cloud9 GPU host, the real benchmark shall **not run**: host preflight refuses with D-state PID 2625774 and 2683546, GTT >8GiB idle ceiling. This software-only comparison does not reset or circumvent that gate.

## Current status

As of 13 October 2026, **14 unit tests** passed offline, and feeding an existing real historical Qwen3.8 Heretic run (missing new required fingerprints) produced a correct **`incomparable`** result. The new script and tests are on Cloud9 Engine **DRAFT PR #17**, while the Source Watch safe PR #19 is merged on `main`. Neither this gate nor the Source Watch changes runtime symlinks or n8n.
