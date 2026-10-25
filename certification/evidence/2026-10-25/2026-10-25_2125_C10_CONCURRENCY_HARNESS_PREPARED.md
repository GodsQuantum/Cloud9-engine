# Cloud9 Engine C10 – 25 October 2026 21:25 Europe/Paris

New benchmark: tools/local_agents/c10_multiagent_capacity.py. Staged copy CT410 lab-releases/local-agent-readiness-20261024/c10_multiagent_capacity.py has identical SHA256.

Scope: DRY-RUN only. Ten new CPU/unit tests pass, local CT410 dry-run returns dry_run_only; NO concurrent GPU test executed and native slot count not claimed. C10 remains NOT_RUN.

Qualification plan: exact preloaded Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB only; official GPU guard; reject busy worker or another active model; get native decoding slots from worker endpoint; measure 1/2/4 clients over 3 repetitions, simulated read-only tool selection, stream TTFT and inter-chunk intervals. Native parallelism is explicitly NOT proven by client concurrency alone. No model loading, wrapper, custom route, service restart or real tool execution.

Never execute while C09 or any live model requests are in flight. Use --execute --output /fresh/unique/lab/path.json on CT410 only when the model is already active, idle and guard authorizes. Report partial if guard refuses; do not modify the production router.

C09 checkpoint currently at 28/36; 8 remaining cases take priority over C10 GPU sampling. C08 2/3 still.
