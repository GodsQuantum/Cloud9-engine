# Cloud9 GPU coexistence — VoiceStudio ROCm idle driver fd / router HTTP 503

**Discovered on Cloud9 after full updates, 2026-10-13 17:50 Europe/Paris.**

After Proxmox 7.0.14-23-pve kernel reboot, GTT around 202 MiB, no D-state tasks and host GPU preflight PASS. Cloud9 Engine router :8090 /health was HTTP 200 but its first real `/v1/chat/completions` request for MiniCPM5 or Ling3 returned HTTP **503** after ~20 s. Error body:

`GPU render device has incompatible users for coexist-light: [(1257, 'python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 3900', '0::/system.slice/docker-9f57523...scope')]`

CT410 Docker container **voicestudio**, image `cloud9/voicestudio:gfx1103-rocm7141-vulkanfixed` is healthy and maintains `/dev/dri/renderD128` open even after **its voice model was unloaded at 15:36:19**. Logs report `Idle timeout reached. Unloading VoiceStudio model to free VRAM`. Four other API services remain HTTP 200. A render FD alone does not mean VoiceStudio is actively inferring.

**Local LAB router fix, not a general GPU relaxation:** for **coexist-light** only, whitelist only the exact healthy running Docker container id of `voicestudio` if the host iGPU GTT reading is **less than 512 MiB** *and* `ss state established sport=:3900` returns **success with zero established connections**. Unknown users, failures to inspect Docker/ss, active voice calls, model-loaded GTT >=512 MiB, and **exclusive GPU modes** still FAIL CLOSED. The existing embeddings and Speaches whitelists are preserved.

Code: `bin/cloud9-model-router.py`: `idle_voicestudio_gpu_id()`, `light_gpu_user(...,voicestudio_id)`, live GPU scan repeated during await. **11 isolated Python unit tests PASS** in `tests/router-voicestudio-idle-coexist-test.py`. Running validation on AMD 780M is still necessary, as is verifying that VoiceStudio serves its voice API after LLM unload. These source changes are added to DRAFT Cloud9 Engine PR #17, not merged automatically.

**Production deployment policy:** make a backup of the current 23,877-byte `/usr/local/bin/cloud9-model-router` in the protected canonical admin directory. Apply only the few needed lines to production, **never wholesale overwrite** with a DEV branch containing other unreviewed runtime changes. Validate Python syntax, restart ONLY the router (no stop of embedding, Speaches, VoiceStudio, Proxmox guest, Docker), verify all four existing endpoints + `:3900/health`, then do a capped short Ling3 3x inference JSON smoke with host preflight before each round. If any model load errors, restore original script and restart router; record exact error in a private benchmark and Hall of Fame source path. Avoid Pym35/long GPU bakeoffs until small tests pass and peak GTT is recorded.

This patch is not a complete global GPU arbitration mechanism. VoiceStudio may receive a new request after admission, so explicit live workload coordination and memory throttling should be investigated separately for high-concurrency/hardware tests. Code only permits a **small idle start-window** and preserves RAM/GTT safeguards.
