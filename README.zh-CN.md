<p align="center"><img src="docs/assets/logo.svg" width="132" alt="Cloud9 Engine 标志"></p>
<h1 align="center">Cloud9 Engine</h1>
<p align="center"><strong>面向 AMD RDNA 的自适应、高性能 llama.cpp 运行时：先实测，再进入生产。</strong></p>
<p align="center"><a href="README.md">English</a> · <a href="README.fr.md">Français</a> · <a href="README.zh-CN.md">简体中文</a></p>

Cloud9 Engine 面向 AMD RDNA + Vulkan 本地推理。它同时跟踪 **llama.cpp upstream** 与 **Atomic TurboQuant**，把 upstream 尚未包含的 Cloud9 优化应用到最新代码，并在真实机器上自动调优 RADV 参数。只有通过正确性和性能门禁的构建才会进入生产。

## ☁️ 为什么选择 Cloud9 Engine？
- **真正的 RDNA Vulkan 优化**：针对 Phoenix/Hawk Point RDNA3 UMA 的 128×32 `MUL_MAT_ID` tile 加速稀疏 MoE prompt processing。
- **硬件自动调优**：根据实测调整 batch/ubatch、polling、FlashAttention 与内存策略，同时尊重用户显式传入的参数。
- **在最新 llama.cpp 上保留 TurboQuant**：TQ2/TQ3/TQ4 KV、Vulkan `SET_ROWS`、FlashAttention 与 benchmark 支持继续可用。
- **两个后端，一个稳定入口**：当前参考硬件默认使用 upstream+Cloud9；Atomic 继续作为 fallback 与 feature donor。
- **安全更新**：更新先作为 candidate，通过本机 gate 后才 promotion。

## ⚡ 快速开始
```bash
git clone https://github.com/GodsQuantum/cloud9-engine.git
cd cloud9-engine
./scripts/install.sh
cloud9-engine doctor
cloud9-engine build
cloud9-engine gate /path/to/model.gguf
cloud9-llama-server -m /path/to/model.gguf -ngl 99 -c 32768
```

## 🧠 路由与 RDNA profile
`auto` 模式使用本机 hardware gate 选出的后端。在参考 Radeon 780M 上，当前 **upstream + Cloud9** 在普通推理和 MTP 中都胜出。仍可用 `CLOUD9_ENGINE_BACKEND=atomic` 强制 Atomic。

默认 `balanced` profile 只在 AMD/RADV 上生效，并且不会覆盖用户已经指定的 llama-server 参数。大规模 prompt ingestion 可使用 `CLOUD9_ENGINE_RDNA_PROFILE=prefill`；完全关闭自动调优则设 `CLOUD9_ENGINE_RDNA_TUNING=off`。

## 📊 Radeon 780M 实测
参考平台：Ryzen 7 8845HS / Radeon 780M RADV，Qwen3.6-35B-A3B Pym Q2 + MTP2，2026-09-16。以下数据**不是对所有 GPU 的通用承诺**。

| 测试 | 基线 → Cloud9 | 提升 |
|---|---:|---:|
| MTP 3×256，调优 Atomic → 调优 Cloud9 | 32.99 → **34.40 t/s** | **+4.3%** |
| MoE pp512，反向顺序 5-run A/B | 342.4 → **362.5 t/s** | **+5.9%** |
| MoE pp2048，反向顺序 5-run A/B | 378.8 → **391.6 t/s** | **+3.4%** |
| MoE pp512，生产 chat profile | 337.1 → **397.5 t/s** | **+17.9%** |

该 kernel 通过 **921/921 个 Vulkan `MUL_MAT_ID` 正确性测试**；纯 decode 没有可测回退（22.50 → 22.63 t/s）。详情见 [benchmarks](docs/benchmarks.md)。

## 🔄 更新策略
GitHub 定时检查 llama.cpp 与 Atomic，更新 `sources.lock` 并创建 PR。CI 验证补丁和 Vulkan 构建；服务器只构建 candidate，只有本机真实模型 gate 通过后才切换生产 symlink。

更多信息：[架构](docs/architecture.md)、[基准测试](docs/benchmarks.md)、[安装](docs/installation.md)、[安全更新](docs/updates.md)。

## 📄 许可证
Cloud9 Engine 自有脚本与文档采用 MIT；upstream 源码保留各自许可证。
