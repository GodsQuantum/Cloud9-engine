# Hugging Face 2026-10-17 — lightweight Flash-Next & newest Qwen3.8 4B

**Independent model survey and lab measurements; no production model promotion.** Values listed for other hardware are **model-author claims**, not reproduced on a Radeon 780M. This note complements the engine benchmark using the same Qwen 4B SHA.

## Flash-Next size/feature shortlist

| Model | Total GGUF on disk | Key technical distinction | Local inference |
|---|---:|---|---|
| [Niwaki v2.4 102B-A5B UD-Q3K](https://huggingface.co/neopolita/Qwen3.8-Flash-Next-102B-A5B-Niwaki-v2.4-3bit-gguf) | **43.849 GB** | Expert pruning + recovery, ~5.3B active; **requires Neopolita llama.cpp fork with Vulkan**; ordinary upstream cannot load. | Not tested |
| [Niwaki v2.4 119B-A5B UD-Q3K](https://huggingface.co/neopolita/Qwen3.8-Flash-Next-119B-A5B-Niwaki-v2.4-3bit-gguf) | **51.008 GB** | ~5.6B active; author reports improved perplexity versus 102B; special fork required. | Not tested |
| [Hybrid 352E abliterated](https://huggingface.co/shefowl/Qwen3.8-Flash-Next-GSQ-RCO-abliterated-Hybrid-352E-4050-16GB-Generalist-GGUF) | **56.547 GB** | 352 of 512 experts; 27.747 GB transformer shard plus 28.800 GB PLE/n-gram table; reduced general knowledge by author's own tests. | Not tested |
| [ISTA-DASLab GSQ-RCO Coder](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF) | **58.408 GB** | Standard qwen4exp GGUF; 256 of 512 experts; 29.608 GB transformer shard and 28.800 GB disk-mappable PLE; code/agentic-targeted pruning. | Not tested |
| [AgentionAI Gyro-S TQ1](https://huggingface.co/agentionai/Qwen3.8-Flash-Next-Gyro-GGUF) | **58.487 GB** | Full expert pool retained in rotor-coded low-bit weights (~27.64 GiB GPU weights by author); **needs AgentionAI Vulkan llama.cpp fork**; its Strata AMD path is experimental. | Not tested |
| [ISTA-DASLab unpruned GSQ Q2_0](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF) | **66.424 GB** | All 512 routed experts; 37.624 GB transformer shard and 28.800 GB PLE, heavy but useful quality control. | Not tested |

**Size on disk is not RSS**: disk-mappable PLE still causes I/O and page-cache pressure; resident transformer, scratch, KV and concurrent services need additional memory. No unsupported inference on hardware compatibility or maximum useful context from GGUF metadata. With limited available host memory and high swap usage, these huge candidates were intentionally **not loaded** in this phase. Do not reduce production safety thresholds to fit them.

Only engine performance may be compared directly on the **same GGUF SHA**. Comparing a pruned coder, rotor quant, or Niwaki to another model is a **model-level task benchmark**, using each best working runtime.

## Actual local Vulkan measurements: Qwen 4B, 3 repetitions/case

Cloud9 APU Radeon 780M RADV, llama.cpp upstream 9d1878a, 8192 allocated context, FlashAttention ON, GPU offload, F16 KV, same short JSON/tool/calendar/code-repair tasks. Strict code JSON requires both syntax and correct semantics; none of these 4B variants passed this test.

| Qwen 4B variant | GGUF size | Strict JSON | Tool calls | Strict code | Median tool wall | Median tool decode |
|---|---:|---:|---:|---:|---:|---:|
| Distill Heretic MTP Q4_K_M (older baseline) | 2.790 GB | 3/3 | 3/3 | 0/3 | 2.403 s | 22.13 t/s |
| Distill Heretic i1 IQ4_XS | 2.514 GB | 3/3 | 3/3 | 0/3 | 2.219 s | 23.63 t/s |
| Heretic i1 IQ4_XS (October 10 revision) | 2.514 GB | 3/3 | 3/3 | 0/3 | 2.235 s | 23.63 t/s |
| Empero FullStack IQ4_XS (October 12 revision) | 2.594 GB | 3/3 | 3/3 | 0/3 | 2.243 s | 23.49 t/s |
| **Heretic i1 IQ3_XXS** (same source repo as Heretic i1 IQ4) | **1.904 GB** | 3/3 | 3/3 | 0/3 | **2.214 s** | **28.84 t/s** |

The IQ3_XXS variant uses 24% less storage than IQ4_XS and decodes tool requests ~22% faster on these short tests. **Do not call quality equivalent** until creative French, long context, multi-step code/agent tests and repeatable multi-seed evaluation pass. The different model variants and quants cannot be used alone to attribute all gains to quantization.

For evidence, SHA and the original JSON results, consult the private canonical Cloud9 local Hall of Fame and dated tournament worklog. Raw application logs, personally identifiable paths and infrastructure details are intentionally omitted from this public report.

## Other up-to-date shortlisted models

- [Qwen3.8 9B uncen-heretic i1 IQ4_XS](https://huggingface.co/mradermacher/Qwen3.8-9B-Distill-uncen-heretic-i1-GGUF), 5.326 GB, updated October 16. Compared with the existing 5.780 GB 9B Q4, **quality and speed not yet tested**.
- [Qwen3.8 9B Hermes function/tool-use IQ4_XS](https://huggingface.co/mradermacher/qwen3.8-9b-hermes-fc-tooluse-GGUF), 5.357 GB, relevant to agent tool calling, **not yet tested**.
- [Qwen3.8 9B Pro-Writer Uncensored IQ4_XS](https://huggingface.co/mradermacher/Qwen3.8-9B-Distill-SLERP-F451-Pro-Writer-Uncensored-GGUF), 5.358 GB, creative writing, **not yet tested**.
- [Gemma4 26B-A4B Heretic AntiSlop IQ4_XS](https://huggingface.co/mradermacher/Gemma-4-26B-A4B-it-heretic-antislop-GGUF), 14.064 GB, October 17, promising high-parameter MoE fitting a constrained RAM budget, **not tested**.
- [Gemma4 26B-A4B pruned88 IQ3_M](https://huggingface.co/fcreait/gemma-4-26B-A4B-it-pruned88-GGUF), 8.896 GB, October 16; needs cognitive degradation test before consideration.

**Required next gates:** compare all engines at identical SHA; shortlist Pareto models by speed and correct tools, explore maximum useful context per model without a fixed upper ceiling (128K only minimum aspiration), and only then make selective winning-engine composites.
