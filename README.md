<p align="center">
  <img src="docs/assets/logo.svg" width="132" alt="Cloud9 Engine logo">
</p>

<h1 align="center">Cloud9 Engine</h1>

<p align="center"><strong>Adaptive llama.cpp runtime for AMD RDNA. Benchmark first. Promote second.</strong></p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.fr.md">Français</a> · <a href="README.zh-CN.md">简体中文</a>
</p>

Cloud9 Engine is a small control layer for local LLMs on AMD RDNA GPUs. Production is **llama.cpp upstream + Cloud9 RDNA patches**, with several validated upstream revisions kept side by side when different model families benchmark best on different revisions. **Prism** is used only for ternary/PTQ models. **Atomic TurboQuant** remains tracked as a laboratory/donor backend, but is never selected automatically on the reference Radeon 780M after Atomic 1.7 reproduced Vulkan allocation/device-loss failures.

## ☁️ Why Cloud9 Engine?

- **RDNA-tuned Vulkan, not just another wrapper** — a Phoenix/Hawk Point high-aspect `MUL_MAT_ID` kernel accelerates sparse MoE prompt processing on validated RDNA3 UMA hardware.
- **Hardware autotuning** — Cloud9 selects measured RADV batch/ubatch, polling, FlashAttention and memory-placement defaults while preserving any flags you explicitly pass.
- **Feature union, not fork lock-in** — current llama.cpp features stay available on the latest compatibility runtime while proven faster upstream revisions can remain selected for specific model families.
- **One stable API, model-specific runtimes** — the model router can select `upstream-pym`, `upstream-fast`, `upstream-next`, `upstream-latest` or Prism per model while exposing one OpenAI-compatible endpoint. Atomic is lab-only on the reference 780M.
- **RDNA-first validation** — the reference machine is Radeon 780M / RADV (`gfx1103` class hardware), not CUDA.
- **Hardware-gated promotion** — updates are candidates until they load a real model and survive an on-device benchmark.
- **Oversize-model fuse** — ordinary model files above 40 GiB are refused by default on the reference 780M after a Flash-Next lab load exhausted GTT. A separate typed `ngram-on-disk` policy may be used only for validated formats whose resident estimate is <=30 GiB and whose runtime explicitly receives `--ngram-on-disk`; the generic laboratory override remains explicit.
- **Safe automatic tracking** — GitHub watches llama.cpp, Atomic and Prism; source changes become reviewable candidates, never invisible production `git pull`s.
- **Drop-in server command** — `cloud9-llama-server` routes to the promoted backend and still accepts normal llama-server arguments.
- **Multi-machine ready** — upstream-derived builds include llama.cpp RPC. A second Cloud9 node can expose its accelerator with `cloud9-engine rpc-worker`; the coordinator defaults to conservative layer split and can opt into tensor split only after hardware A/B. RPC stays loopback-only until explicitly enabled.

## ⚡ Quick start

```bash
git clone https://github.com/GodsQuantum/cloud9-engine.git
cd cloud9-engine
./scripts/install.sh

cloud9-engine doctor
cloud9-engine build
cloud9-engine gate /path/to/a-compatible-model.gguf

cloud9-llama-server -m /path/to/model.gguf -ngl 99 -c 32768 -fa on
```

You need a C/C++ toolchain, CMake, Git, Vulkan development files, `glslc`, and preferably `ccache`. See [Installation](docs/installation.md).

## 🧠 How routing works

Normal production traffic goes through `cloud9-model-router`. Its versioned catalog selects a validated backend, context size and speculative-decoding profile per model. Direct `cloud9-llama-server` use still supports `CLOUD9_ENGINE_BACKEND=auto`, whose generic fallback is `upstream-fast`.

```bash
CLOUD9_ENGINE_BACKEND=upstream-fast   cloud9-llama-server ...
CLOUD9_ENGINE_BACKEND=upstream-latest cloud9-llama-server ...
CLOUD9_ENGINE_BACKEND=prism           cloud9-llama-server ...
# Atomic is an explicit laboratory override only:
CLOUD9_ENGINE_BACKEND=atomic          cloud9-llama-server ...
```

On the reference 780M, production currently keeps four upstream+Cloud9 revisions because the fastest revision depends on the model family; Prism is reserved for ternary Bonsai/PTQ models.

The default `balanced` RDNA profile is only injected on AMD/RADV and only for options you did not already specify. Set `CLOUD9_ENGINE_RDNA_TUNING=off` to pass through untouched llama-server defaults. The wrapper never downloads a model and never uploads prompts or model data.

## 📊 Measured RDNA performance

Reference platform: Ryzen 7 8845HS / Radeon 780M (RADV), Qwen3.6-35B-A3B Pym Q2 + MTP2, September 16 2026. These are **hardware-specific measurements, not universal claims**.

| Test | Comparison | Result |
|---|---|---:|
| MTP 3×256 median decode | Atomic 1.6.0 tuned → Cloud9 tuned | **32.99 → 34.40 t/s (+4.3%)** |
| MoE pp512, reverse-order 5-run A/B | same upstream build, kernel off → on | **342.4 → 362.5 t/s (+5.9%)** |
| MoE pp2048, reverse-order 5-run A/B | same upstream build, kernel off → on | **378.8 → 391.6 t/s (+3.4%)** |
| MoE pp512, production chat profile | same upstream build, kernel off → on | **337.1 → 397.5 t/s (+17.9%)** |
| Decode-only 7-run reverse A/B | kernel off → on | **22.50 → 22.63 t/s (no regression)** |

The Vulkan `MUL_MAT_ID` gate also passes **921/921** backend correctness cases on the reference 780M. See [Benchmarks](docs/benchmarks.md) for protocol, variance and limitations.

## 🔄 Updates without roulette

1. `.github/workflows/source-watch.yml` checks llama.cpp, Atomic and Prism daily.
2. New source SHAs are proposed only after the declared Cloud9 patchset still applies.
3. CI verifies patch compatibility and Vulkan builds.
4. The server builds isolated **candidates**; the known-good runtime links remain untouched.
5. Real local models run hardware gates and family-specific A/B benchmarks before any production runtime link changes.

If a patch stops applying, production stays on the previous known-good binaries. That failure is information, not an excuse to force a merge.

## 🧩 What is actually Cloud9 code?

Cloud9 Engine does not pretend to own llama.cpp, Prism or Atomic. The current `patches/upstream-latest/` series contains only the Cloud9 RDNA delta still useful on current upstream; the older TurboQuant-heavy patchset is retained as legacy provenance rather than force-rebased onto every new llama.cpp HEAD. The rest is orchestration, reproducible builds, model-aware routing and hardware promotion logic. Source provenance is explicit in [`sources.lock`](sources.lock).

## 🛠 Commands

```text
cloud9-engine doctor          check local Vulkan/build prerequisites
cloud9-engine build           build locked upstream/Cloud9 + Atomic + Prism candidates
cloud9-engine gate MODEL      benchmark candidates and promote known-good builds
cloud9-engine status          show promoted versions and routing profile
cloud9-engine server ...      run through the adaptive server wrapper
```

`cloud9-llama-server ...` is the shorter drop-in entry point.

## 📚 Documentation

- [Installation](docs/installation.md)
- [Architecture](docs/architecture.md)
- [Benchmarks](docs/benchmarks.md)
- [Updating safely](docs/updates.md)
- [Distributed / multi-machine](docs/distributed.md)
- [Français](README.fr.md)
- [简体中文](README.zh-CN.md)

## 🤝 Upstream projects

Cloud9 Engine builds on [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp), [PrismML-Eng/llama.cpp](https://github.com/PrismML-Eng/llama.cpp) and [AtomicBot-ai/atomic-llama-cpp-turboquant](https://github.com/AtomicBot-ai/atomic-llama-cpp-turboquant). Please support the upstream projects if this tool is useful to you.

## 📄 License

Cloud9 Engine's original scripts and documentation are MIT licensed. Upstream source trees keep their own licenses and notices.
