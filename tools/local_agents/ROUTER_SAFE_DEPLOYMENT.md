# Cloud9 model router - official guard and non-preemption patch

**LAB tested, not automatically promoted.** Source baseline copied from CT410 on October 24, 2026: cloud9-model-router-pre-guard-20261024.py, SHA256 7396e7a72840c0ecf16854537c30e2300cee61699b0b0020054986ebf4fabdba.
Proposed replacement: cloud9-model-router-safe-lab-20261024.py.

The current runtime is native cloud9-engine-router.service in CT410, 192.168.1.219:8090. No extra proxy or wrapper.

## Behavior
- Official PVE guard 192.168.1.200:19755 is checked before any model eviction and again before the GPU lock.
- A denied/unreachable guardian returns HTTP 503; no model load.
- Coexist-light never escalates implicitly to exclusive.
- Exclusive models require an explicit maintenance opt-in environment flag; prevent shutdowns of embeddings and Speaches in ordinary agent routes.
- Running VoiceStudio is not stopped for coexistence requests.
- Same-model requests continue to reuse a loaded worker.
- Conservative GTT request: model GGUF + separate draft GGUF + 1.5 GiB KV/scratch. Guardian remains authoritative.

## Release gates
- Unit tests: guardian allow/deny/offline, exclusive refusal, draft size, unknown mode, eviction order, no fallback, VoiceStudio protection.
- Loopback HTTP smoke with fake tiny model, nonexistent backend, and exclusive GPU request: /health and /v1/models work; HTTP 503, no worker started.
- Deployment only after active router SHA matches baseline and worker_model is null. Preserve a timestamped rollback copy, stage the new script, restart ONLY cloud9-engine-router.service, test router+embedding+OmniRoute health. Roll back immediately if any check fails.
- Not an actual Radeon 780M inference certification. The official GPU guardian may continue denying 4B due RAM, PSI or GTT. Never disable the guard.

Do not enable CLOUD9_ENGINE_ALLOW_SERVICE_PREEMPTION=1 without a protected maintenance window.
