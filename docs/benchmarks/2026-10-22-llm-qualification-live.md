# Cloud9 inference engines — live qualification, 22 October 2026

**LAB ONLY. Do not deploy or promote any candidate yet.** The single canonical Hall of Fame is the parent project HALL_OF_FAME.json (not this Git repository). It now has 182 records; new records must use Sources/Tools/refresh_hall_of_fame.py --append-stdin and --validate. Preserve historical IDs and original sources.

## Actual production inventory (read-only inspection)

CT410 did not have an active generative llama.cpp worker on 22 October at 10:37. Its cloud9-engine-router.service answers catalog discovery requests and consumes ~3.4MiB. The only active llama-server is cloud9-embedding.service running Qwen3-Embedding-0.6B for other production apps; it must NOT be stopped to free imaginary generative-model memory. Speaches/VoiceStudio and other protected services remain active. No production service, VM or mount was stopped; no reboot or ZFS ARC change.

Host usable RAM ~92GiB is shared with PBS and HAOS VMs (~15GiB), CT400 (~11GiB), CT210 (~6GiB), CT220 (~5GiB), CT410 (~4GiB), plus ZFS ARC (~9.8GiB), other guests and swap. The CT410 official GPU arbiter preserves a host reserve of 18GiB. A plan for one resident LLM does not itself free that memory.

## Real 9B + native MTP2 benchmark (15 requests)

- Engine: Codespaces-built llama.cpp b11798 upstream source commit 9febe63d5a379f8568bae7116a5b2ba844a4a4a6, Vulkan RADV Radeon780M gfx1103, binary SHA256 e0daa467846605c60d38e41e8723c13e802db0ecf4131d51247fd8a72f802696.
- Exact model: Qwen3.8-9B-Distill-Heretic-Uncensored-MTP-Q4_K_M.gguf; size 5780090624 bytes, SHA256 694cd96557f5b68cd00f0759ef26b75a67f275d717b5d124e8252d15c8eeb58c.
- Native MTP: draft-mtp, n-max=2, accepted 321 / 492 draft tokens = 65.244%; F16 KV, context allocated 8192, no production clients, CT410 GPU lock acquired and released. Cold model load 4.544 s.
- Three independent repeated requests per case, synthetic read-only OpenAI API. JSON exact: 3/3 (median 22.41 tok/s). Tool-call exact: 3/3 (22.21 tok/s). Strict one-line corrected code: 0/3 (20.65 tok/s); the model repaired the arithmetic semantically but returned the entire function statement instead of the requested single line. French creative formal constraints: 3/3 (15.05 tok/s); human editorial quality NOT graded. 2236-token prompt marker: 3/3 (20.80 tok/s). Therefore this is not a production winner or a proof of useful 8K+ context.
- Evidence: Sources/Benchmarks/Engine-Tournament/2026-10-22/llama-b11798-Qwen3.8-9B-Di-ncensored-MTP-Q4_K_M-all-spec-mtp2-v2-20261019.json; Sources/Worklogs/2026-10-22_1051_LLAMA_B11798_9B_MTP2_FULL_QUALITY_GUARDED.log.
- Canonical Hall ID: 2026-10-22:llama-b11798:qwen38-9b-mtp-q4:agentic15, status experimental_not_promoted.

## Failure records — never call them inference benchmarks

- Hall ID 2026-10-22:llama-b11798:9b-mtp2-context8192:guard-denied. Official coexist memory request 8GiB failed, safe GTT only ~7.5GiB. Model never started for long-context testing.
- Hall ID 2026-10-22:magnitude-0210:qwen35dense-4b-mtp:vulkan-resource-stop. Magnitude 0.2.10 release Vulkan Qwen4B with native MTP proposals=2 passed admission request6GiB, but the engine worker consumed ~6-7GiB resident and host MemAvailable dropped to 18GiB before engine ready. The watchdog interrupted at 16.64s; NO inference output, MTP acceptance, quality or TPS measurement. The candidate left orphaned worker PID336851. It was terminated only after exact command, owner and PGID checks; RAM returned and GPU lease was released. The first attempt was a trivial invalid tuning-budget=0; corrected to positive 2 in the second. Current branch remains unpromoted.
- Atomic TurboQuant 4B 8192 five-position proof was refused before GPU lock or model load because host memory PSI full avg10 was ~12%, despite safe GTT >5GiB. Not a failed context retrieval or an AMD compatibility result. Source: Sources/Worklogs/2026-10-22_1137_ATOMIC_TURBO3_4B_MTP2_CONTEXT_8192_GUARDED.log.

## Actual Strata 0.2.2 deployment readiness

Codespaces HIP ROCm 10.1 build targeted gfx1103 with successful native compilation, CT700 CLI smoke and SHA checks. strata --families reports qwen4exp AND qwen35moe. The target is specifically Qwen3.6-35B-A3B-Pym-Q2-MTP.gguf (13222476000 bytes), not a dense 4B/9B comparison. Original model is still too large for official safe host memory budget for an exclusive 14.5GiB admission. No true MTP generation or quality benchmark has run on this Strata binary.

## Long context and KV compression

- TurboQuant is NOT an engine-agnostic feature. The Atomic llama.cpp fork supports KV turbo3/turbo4 with dedicated code. Strata has separate INT8, Q4, K8V4 and KV streaming. Magnitude 0.2.10 exposes dense/affine-k8v4, not a drop-in TurboQuant kernel.
- Qwen35 GGUF metadata claims 262144 trained context capacity. Neither 128K, 256K nor a million tokens is certified until the runtime has REALLY ingested that number of tokens with no truncation AND recovered multiple markers at separated positions. Quantization saves KV RAM but does not make untrained context windows magically accurate or remove prefill compute/thermal costs.
- The three scripts under tools/benchmarks are experimental harnesses, never production services. The five-needle witness checks token count via the live tokenizer, five position markers, repeated JSON retrieval and thermal/cgroup admission. They MUST run with CT410 arbiter and watchdog externally and have NOT passed long context on Cloud9 as of this report.
- Keep no more than one LLM engine loaded simultaneously; never compare Strata --bench-tg (without native MTP) against llama.cpp native MTP; use real accepted draft counts, quality, TTFT, prefill, decode and useful context.

## What qualifies the winner

For each engine/model/quant SHA, run real native MTP/speculative generation with 3+ trials, read-only function calls, JSON, realistic coding, French creative human rubric, paced multi-position context retrieval 8K,16K,32K,64K,128K,256K and above ONLY if thermally safe. Log peak host RAM, GTT, PSI, temperature, time-to-correct-action and failures. No new winner without green guard and actual model tests. Do NOT stop embedding, PBS, HAOS or critical family services, and do not modify the official GPU safety guard.


## Extended 12-case protocol (offline checked, NO GPU run yet)

The new tools/benchmarks/one_engine_quality_protocol_20261022.py defines three strict JSON, three fictional read-only tool calls, three realistic line-level code fixes and three French creative/professional/technical requests. Run each three times for 36 total responses per engine/model under native MTP. JSON/arguments/code are machine-gradeable; French constraints are only a mechanical precheck. Editorial originality, scientific correctness and humor must be judged separately on anonymized outputs before promotion. Missing or duplicate evidence fails closed. Tests/quality_protocol_contract_test.py has 7 passing offline tests. This is a BENCHMARK SPECIFICATION, not 36 real completed inference responses.


## First independently verified useful contexts — 22 October 11:34 CEST

- Exact GGUF model Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf, 2,790,000,800 bytes, SHA256 7b95847ce1684f98d96f13bad2daaeffcfd2f95ea2ff3821ee68943590a10159.
- Atomic TurboQuant 2.0.0 native draft-MTP n-max2, Vulkan Radeon780M; K cache q8_0, V cache turbo3. Five fictional markers at separate prompt positions, checked as exact JSON with actual server-reported input tokens; three real repetitions per size. No production interruptions.

| Requested approximate | Actual ingested | Five-marker retrieval | Median PP tok/s | Median decode tok/s | Peak Tctl (C) | Evidence SHA256 |
|---|---:|---:|---:|---:|---:|---|
| 8192 | 8026 | 3/3 attempts | 326.71 | 35.21 | 68.25 | d764aa5749cdaf5ee12cb295ef5f2890e34145df351712930cdda03788a97f65 |
| 16384 | 16330 | 3/3 attempts | 298.25 | 30.66 | 70.875 | e4fd8c4bea478652185be8661c41651f10dc6a8c0718844c42cff0dc303be4fa |

- Canonical Hall entries: 2026-10-22:atomic-turboquant2:qwen4b-mtp2-turbo3:five-needle8k and 2026-10-22:atomic-turboquant2:qwen4b-mtp2-turbo3:five-needle16k. Both validated_in_source, original JSONs plus host guard logs under Sources/Benchmarks/Engine-Tournament/2026-10-22 and Sources/Worklogs.
- Scope: synthetic document retrieval only, not creativity/coding quality or certified 32K,128K,256K,1M. KV compression cannot eliminate context prefill heat and host PSI. Escalation conditional on official GTT/memory/thermal admission.
