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

- **Two good engines, one stable entry point** — current upstream for fresh model/Vulkan support, Atomic for mature TurboQuant and speculative paths.
- **RDNA-first validation** — the reference machine is Radeon 780M / RADV (`gfx1103` class hardware), not CUDA.
- **TurboQuant on current upstream** — Cloud9 patches add TQ2/TQ3/TQ4 KV support, Vulkan `SET_ROWS`, FlashAttention decode and benchmark plumbing where upstream still lacks it.
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

`CLOUD9_ENGINE_BACKEND=auto` is the default. The promoted **upstream+Cloud9** build handles normal requests so you get current llama.cpp model and Vulkan support. MTP/NextN-style speculative requests prefer the promoted **Atomic** build when the local hardware gate says it is faster. Either path can be forced explicitly.

```bash
CLOUD9_ENGINE_BACKEND=upstream cloud9-llama-server ...
CLOUD9_ENGINE_BACKEND=atomic   cloud9-llama-server ...
```

The wrapper never downloads a model and never uploads prompts or model data.

## 📊 Why not just use one fork?

On the reference Radeon 780M, there was no honest universal winner on 16 Sep 2026:

| Same host / same model | Atomic 1.6.0 | older Cloud9 champion | current upstream + Cloud9 |
|---|---:|---:|---:|
| Raw prefill, 512-token bench | ~301 t/s | **~342 t/s** | ~335 t/s |
| Raw generation | ~21.67 t/s | **~21.91 t/s** | ~21.56 t/s |
| MTP, 3×256 median decode | **~33.26 t/s** | ~31.29 t/s | ~31.90 t/s |

Atomic remained better for this longer MTP workload, while newer upstream code delivered substantially stronger Vulkan prefill. Cloud9 Engine therefore keeps **both advantages** instead of hiding that trade-off. Full protocol and limitations: [Benchmarks](docs/benchmarks.md).

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
