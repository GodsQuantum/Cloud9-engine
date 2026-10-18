# Cloud9 Vulkan — Qwen3.8 9B models and IQ3/IQ4 comparison, 18 October 2026

**Experimental, not a production qualification.** These benchmarks run identical task prompts at context allocation 8,192, llama.cpp upstream commit 9d1878a on AMD Radeon780M RADV Vulkan, KV F16/F16, -ngl99, seed42 and temperature0, with production GPU admission reserved externally by a host GPU lock/watchdog. The public Python benchmark **DOES NOT** acquire such a lease; do not manually bypass resource admissions.

Model comparator measures *different models* at identical tasks, NOT same-weights engine comparison. Quantization comparison uses the same parent Heretic i1 source revision with distinct QGGUF SHAs.

| Model | GGUF size | Native tools | Strict simple JSON | Exact corrected_line | Tool median latency | Tool decode |
|---|---:|---:|---:|---:|---:|---:|
| Hermes FC Tooluse IQ4_XS | 5.36 GB | 3/3 | 1/3 | 0/3 | 3.967s | 12.766 tok/s |
| Distill Heretic i1 IQ4_XS | 5.33 GB | 3/3 | 3/3 | 0/3 | **3.645s** | 14.036 tok/s |
| Distill Heretic i1 IQ3_M | 4.52 GB | 3/3 | 3/3 | 0/3 | 4.236s | **14.54 tok/s** |

All three semantically correct the arithmetic example in 3/3 responses, but all fail the stricter exact single-line JSON value. Hermes output sometimes repeated assistant and thinking delimiters; do not assume a model limitation before ruling out chat template / stopping issue. Model author cautions that older Hermes synthetic tool-use results were not using the real OpenAI tools path. This suite uses actual native tool calls.

The IQ3_M quant saves about 15% storage versus IQ4_XS but slows prefill and end-to-end tool calls on this iGPU. IQ4_XS provisionally preferred for this model at short context; not a final four-model choice.

**Creative pilot incomplete**: one 4B small model produced three repetitive and over-short monologues that failed word and lexical constraints (0/3). The 9B returned two scripts (1/2 constraints) before a thermal guard stopped the third attempt; no 9B overall creative score or winner. Do not treat this small lexical test as a human humor/craft evaluation.

**Thermal long-depth evidence**: another same-weight S1/upstream Pym35 depth attempt did NOT reach 8K/32K/72K under the <80C Cloud9 goal; host watchdog stopped S1 at Tctl80.4C, upstream local limit at79.375C, GPU lock freed. No context maximum can be inferred. Do not raise power or fan policy, remove mounts or disturb production to retry.

Full raw outputs and owner-private infrastructure logs remain in the CT700 canonical lab project, not in this public repo. No engine or model was promoted to OmniRoute in this lot.

Useful sources:
- https://huggingface.co/mradermacher/Qwen3.8-9B-Distill-uncen-heretic-i1-GGUF
- https://huggingface.co/mradermacher/qwen3.8-9b-hermes-fc-tooluse-GGUF
- https://huggingface.co/JamieBradfield/qwen3.8-9b-hermes-fc-clean-restraint
- https://github.com/ggml-org/llama.cpp/discussions/24222
- https://github.com/vahpetr/llama.cpp-s1-fork
