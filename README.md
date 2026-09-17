<p align="center">
  <img src="docs/assets/logo.svg" width="132" alt="Cloud9 Engine logo">
</p>

<h1 align="center">Cloud9 Engine</h1>

<p align="center"><strong>Adaptive llama.cpp runtime for AMD RDNA. Benchmark first. Promote second.</strong></p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.fr.md">Français</a> · <a href="README.zh-CN.md">简体中文</a>
</p>

Cloud9 Engine is a small control layer for people running local LLMs on AMD RDNA GPUs through Vulkan. Instead of betting your server on one fork forever, it tracks **llama.cpp upstream** and **Atomic TurboQuant**, builds both, applies the Cloud9 RDNA patchset where it is still missing upstream, then lets the actual machine decide what gets promoted.

## ☁️ Why Cloud9 Engine?

- **RDNA-tuned Vulkan, not just another wrapper** — a Phoenix/Hawk Point high-aspect `MUL_MAT_ID` kernel accelerates sparse MoE prompt processing on validated RDNA3 UMA hardware.
- **Hardware autotuning** — Cloud9 selects measured RADV batch/ubatch, polling, FlashAttention and memory-placement defaults while preserving any flags you explicitly pass.
- **TurboQuant on current upstream** — TQ2/TQ3/TQ4 KV support, Vulkan `SET_ROWS`, FlashAttention decode and benchmark plumbing stay available on a much newer llama.cpp Vulkan tree.
- **Two engines, one stable entry point** — current upstream+Cloud9 is the default; Atomic remains a tracked fallback/donor and can still win on different hardware or future revisions.
- **RDNA-first validation** — the reference machine is Radeon 780M / RADV (`gfx1103` class hardware), not CUDA.
- **Hardware-gated promotion** — updates are candidates until they load a real model and survive an on-device benchmark.
- **Safe automatic tracking** — GitHub watches both source trees; a source update becomes a PR, not an invisible production `git pull`.
- **Drop-in server command** — `cloud9-llama-server` routes to the promoted backend and still accepts normal llama-server arguments.

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

`CLOUD9_ENGINE_BACKEND=auto` is the default. A local hardware gate benchmarks both candidates with a production-like MTP workload and writes the measured winner into a local profile. On the reference Radeon 780M, the current **upstream + Cloud9** backend wins both general and MTP routing after RDNA tuning. Atomic remains available as an explicit fallback.

```bash
CLOUD9_ENGINE_BACKEND=upstream cloud9-llama-server ...
CLOUD9_ENGINE_BACKEND=atomic   cloud9-llama-server ...
CLOUD9_ENGINE_RDNA_PROFILE=prefill cloud9-llama-server ...
```

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

1. `.github/workflows/source-watch.yml` checks llama.cpp and Atomic daily.
2. New source SHAs are proposed in an automated PR.
3. CI proves the Cloud9 patchset still applies and Vulkan binaries still compile.
4. Your server's optional systemd timer pulls merged updates and builds **candidates**.
5. A configured real model runs the local hardware gate. Only then are `current/atomic` and `current/upstream` promoted.

If a patch stops applying, production stays on the previous known-good binaries. That failure is information, not an excuse to force a merge.

## 🧩 What is actually Cloud9 code?

Cloud9 Engine does not pretend to own llama.cpp or Atomic. The public `patches/upstream/` series contains the small RDNA/TurboQuant delta currently required on top of the pinned upstream revision. The rest is orchestration, reproducible builds, routing and hardware promotion logic. Source provenance is kept explicit in [`sources.lock`](sources.lock).

## 🛠 Commands

```text
cloud9-engine doctor          check local Vulkan/build prerequisites
cloud9-engine build           build locked Atomic + upstream/Cloud9 candidates
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
- [Français](README.fr.md)
- [简体中文](README.zh-CN.md)

## 🤝 Upstream projects

Cloud9 Engine exists because of [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) and [AtomicBot-ai/atomic-llama-cpp-turboquant](https://github.com/AtomicBot-ai/atomic-llama-cpp-turboquant). Please star and support the upstream projects if this tool is useful to you.

## 📄 License

Cloud9 Engine's original scripts and documentation are MIT licensed. Upstream source trees keep their own licenses and notices.
