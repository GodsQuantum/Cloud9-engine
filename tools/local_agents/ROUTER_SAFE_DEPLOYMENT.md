# Cloud9 model router - official guard and non-preemption patch

**DEPLOYED 2026-10-24 after LAB qualification with rollback preserved.** Source baseline copied from CT410 on October 24, 2026: cloud9-model-router-pre-guard-20261024.py, SHA256 7396e7a72840c0ecf16854537c30e2300cee61699b0b0020054986ebf4fabdba.
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


## CT410 production deployment verification

- CT410 /usr/local/bin/cloud9-model-router SHA256 ce876feae4e95f71bb0d8dad2c9521cc1149fe223e00a2fd6800318e96c1dd92.
- CT410 LAB rollback file lab-releases/router-official-guardian-20261024/cloud9-model-router.rollback SHA256 7396e7a72840c0ecf16854537c30e2300cee61699b0b0020054986ebf4fabdba.
- Only cloud9-engine-router.service restarted; embeddings remained active. CT400 OmniRoute active, eight model identifiers unchanged.
- Live POST Pym 35B returned HTTP 503 exclusive-maintenance-opt-in; no GPU worker loaded, no service preemption.
- DEV 194 Python unit tests PASS; same binary copied CT410 LAB and 12/12 tests PASS. Not a GPU inference certification.


## GPU pinned-service coexistence LAB extension

VoiceStudio retains renderD128 while idle, and AutoSubs Aligner GPU also retains
it even with no loaded ASR models. Neither service is stopped for lightweight
coexistence models. Revised source: cloud9-model-router-idle-coexist-20261024.py.

Native coexist-light rules:
- VoiceStudio may share only with no established 3900/7443 connections; never stopped.
- AutoSubs Aligner may share only if native health reports status ok with an
  empty loaded_models list, with no established request on port 8007.
- Both must have their full Docker IDs matched in proc cgroups. Unknown
  processes remain blocked. Embeddings and Speaches are already recognized.
- Guardian checks for RAM/GTT/PSI happen twice; GPU lock remains mandatory.
- Exclusive GPU mode still requires explicit maintenance opt-in.

Five unit tests for safe idle/known process matching plus an isolated HTTP
smoke pass on CT410. New GPU sharing is NOT yet an inference certification.
If a service regresses, restore prior router source and restart only the router.
