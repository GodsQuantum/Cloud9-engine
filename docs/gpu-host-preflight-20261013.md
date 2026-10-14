# Cloud9 GPU fail-closed host preflight — laboratoire 2026-10-13

## Motivation

After Pym / llama.cpp `cbe28bb3` cold reload, the Radeon 780M has two uninterruptible kernel waits: a CT700 `llama-server` stuck in `drm_suballoc_new` and a host debugfs read stuck in `ttm_bo_evict_first`. GTT usage continues increasing despite a previous successful GPU reset. GPU arbitration `flock` alone does **not** certify a healthy driver.

Do **not** reboot Cloud9, hot-unbind AMDGPU, run `amdgpu_evict_gtt` again, kill other CT workloads, change NFS/mount/idmaps or run heavy GPU benchmarks while this condition persists.

## Lab branch

`lab/gpu-preflight-failclosed-20261013` (CT700 DEV clone; not production).

Changes:

- `scripts/host-gpu-preflight.py`: read-only checks from the **Proxmox host**, before any LXC preemption:
  - sysfs GTT, threshold 8 GiB idle;
  - host available memory, threshold 16 GiB;
  - 10-second I/O and memory PSI full pressure;
  - short swap I/O rate;
  - all host-visible GPU-related D-state processes, including those in other containers;
  - recent kernel AMDGPU submission/reset errors.
- `scripts/host-exclusive-bakeoff.sh`: call the gate first and exit code 4 on refusal, before `pct exec` or other changes. Existing CPU/performance gates remain in force.
- `scripts/model-bakeoff.py`: do not force `RADV_PERFTEST=nogttspill`; allow explicit per-model `radv_perftest` option, and record effective value in per-run results.
- Offline tests: `tests/host-gpu-preflight-test.py`, `tests/bench-env-test.py`.

## Validation in this checkpoint

12/12 CPU-only simulated tests PASS (seven GPU safety fixtures, five RADV environment fixtures).
Python syntax / shell syntax / `git diff --check` PASS.
Live read-only host gate at ~02:10 **REFUSE**:
- GTT ~14.2 GiB and increasing;
- host RAM available <16 GiB;
- both D-state GPU tasks remain;
- recent kernel submission errors.
The complete host benchmark wrapper also returns **4 before any LXC action**. API endpoints `:8090`, `:8091`, `:8005` remained HTTP 200.

## Scope and promotion discipline

No kernel recovery attempted, no heavy benchmark, no service restart, no production files or canonical source modified. This is a safety/code-correctness gate, **not** a new engine/performance certification. Keep this branch outside production until CT700 attachment recovers and integrated validation can be performed.

During a future clean GPU window, validate a refusal while `cloud9-engine-router` is serving a request and a successful clean preflight without accidentally stopping other managed services. The wrapper is intentionally conservative: a busy host means no benchmark, not forced preemption.

Do not accept a latest llama.cpp runtime for Pym solely from a first warm decode result. Repeat cold load/unload and watch GTT and model correctness. Keep Pym on `upstream-37b53fd45458-cloud9` until local A/B supports change.

## Sources checked

- Cloud9: `Sources/Worklogs/2026-10-13_0200_GPU_GTT_HALT_AND_SOURCE_RECHECK.md` and `HANDOFF_CURRENT.md`.
- llama.cpp Vulkan device loss / mmap workaround after #26081: https://github.com/ggml-org/llama.cpp/issues/29455
- Radeon 780M Vulkan startup hangs on several models: https://github.com/ggml-org/llama.cpp/issues/24664
- Official AMDGPU debugfs: https://docs.kernel.org/next/gpu/amdgpu/debugfs.html


## Follow-up: no hidden RADV flags in secondary benchmark scripts

A later source audit revealed **two additional implicit `RADV_PERFTEST=nogttspill` activations** which were not covered by the original `model-bakeoff.py` fix:

- `scripts/hardware-gate.sh` forced the flag only for the upstream/MTP candidate.
- `scripts/fresh-run-bench.py` unconditionally appended the flag to the environment for every subprocess.

Both have been removed **on this DEV branch**, with explicit inherited `RADV_PERFTEST` settings preserved. The `fresh-run-bench.py` result JSON now records the effective inherited RADV value for scientific reproducibility. A new `tests/radv-no-implicit-test.py` proves all three entrypoints default to no forced `nogttspill`. This prevents an undocumented setting from confounding Cloud9's upstream/fork comparison.

Static/CPU tests at 2026-10-13 ~11:55 CEST: 7 GPU preflight tests + 5 manifest env tests + 3 new RADV tests passed; shell hardware-gate safety, fallback, and oversize policy passed. AST, bash syntax, git diff check passed. Actual host read-only preflight **REFUSE/4** because two cross-CT AMDGPU tasks still remain in uninterruptible kernel state and GTT exceeds idle 8GiB. **No GPU benchmark nor build has been run by these edits.**

Additional upstream context: ggml-org/llama.cpp issue #27998 (https://github.com/ggml-org/llama.cpp/issues/27998) traced another Radeon 780M/TTM stall to `ttm.pages_limit`, but Cloud9 currently has 18,874,368 kernel TTM pages × 4,096 bytes ≈ 72GiB and idle GTT ~10.64GiB. This *does not prove* the same cause on Cloud9. Do not change the kernel TTM parameter or mounts based on a different machine's success.

**Next release gate**: read host and production health; do not merge/activate a new GPU runtime until both D-state processes are gone, host preflight PASS, CT700 attach and toolchain are healthy, all original hardware correctness/performance fixtures succeed, and measured improvement beats the stable multi-runtime baseline.
