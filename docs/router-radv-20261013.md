# Cloud9 Router — RDNA/RADV flag source audit (13 October 2026)

**Important:** The prior Cloud9 `scripts/model-bakeoff.py`, `scripts/hardware-gate.sh`, and `scripts/fresh-run-bench.py` candidate patches stopped silently applying `RADV_PERFTEST=nogttspill`. The **actual production router source** `bin/cloud9-model-router.py` nevertheless still appended `nogttspill` to **every** launched model worker, even if no `RADV_PERFTEST` was configured. That is a separate, potentially serious source of lost inference performance on Cloud9's Radeon 780M and misleading benchmark-vs-production comparisons.

This DEV-only change removes that implicit mutation. A new function `model_env(source_env, model)` returns a copy of inherited environment, optionally honoring an explicit per-model `radv_perftest` string from the model catalog (empty string removes inherited RADV). It does not silently append `nogttspill`, and the worker's existing log header now records the effective RADV setting. If production's service unit **explicitly** defines `RADV_PERFTEST`, this is preserved unless overridden per-model.

Actual performance difference is **NOT MEASURED** by this source audit. The historical Hall of Fame reports that `nogttspill` degraded the older Pym MoE in one environment, but same-backend, same-GGUF, same context/cache/MTP, p50/p95, quality and long-prompt hardware A/B will be required before promoting these changes. The host Radeon GPU is still wedged in two `D` kernel tasks; do not restart the production router for this source-only patch.

Six unit tests run the **exact production `model_env` AST** in isolation, verify default/inherited/explicit set/explicit empty/type rejection and that the actual worker calls it, with no daemon, GPU or real model. All pass on Cloud9 CPU; one `bin/cloud9-model-router.py` compile passes.

To validate on a development source tree only:

```bash
python3 -B tests/router-radv-contract-test.py
python3 -B tests/radv-no-implicit-test.py
python3 -B tests/host-gpu-preflight-test.py
```

At production rollout after hardware recovery, inspect any systemd `Environment=RADV_PERFTEST` and catalog `radv_perftest`, then compare with actual `/proc/<worker PID>/environ` and recorded process logs. Never introduce `nogttspill` as a baseline default based on one prior result. Preserve all wins/losses in **ONE** canonical `../../HALL_OF_FAME.json`.
