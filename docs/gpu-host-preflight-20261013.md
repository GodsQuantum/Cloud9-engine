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
