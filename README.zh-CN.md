<p align="center"><img src="docs/assets/logo.svg" width="132" alt="Cloud9 Engine 标志"></p>
<h1 align="center">Cloud9 Engine</h1>
<p align="center"><strong>面向 AMD RDNA 的自适应 llama.cpp 运行时：先基准测试，再升级生产。</strong></p>
<p align="center"><a href="README.md">English</a> · <a href="README.fr.md">Français</a> · <a href="README.zh-CN.md">简体中文</a></p>

Cloud9 Engine 是一个面向 AMD RDNA + Vulkan 本地推理的小型控制层。它不会永久绑定某一个 fork，而是同时跟踪 **llama.cpp upstream** 与 **Atomic TurboQuant**，构建两套候选后端，并把仍未进入 upstream 的 Cloud9 RDNA/TurboQuant 补丁应用到最新 upstream，再由真实硬件基准决定生产版本。

## ☁️ 核心特点
- **两个后端，一个稳定入口**：最新 upstream 负责新模型与新 Vulkan 能力，Atomic 负责成熟的 TurboQuant / speculative 路径。
- **RDNA 优先验证**：参考平台是 Radeon 780M / RADV，而不是 CUDA。
- **硬件门禁**：新版先作为 candidate，加载真实模型并通过本机测试后才 promotion。
- **安全自动更新**：GitHub 自动监控 upstream；更新通过 PR + CI，不会直接在生产机上盲目 `git pull`。
- **兼容 llama-server**：`cloud9-llama-server` 只负责选择已验证后端，其余参数保持正常 llama-server 用法。

## ⚡ 快速开始
```bash
git clone https://github.com/GodsQuantum/cloud9-engine.git
cd cloud9-engine
./scripts/install.sh
cloud9-engine doctor
cloud9-engine build
cloud9-engine gate /path/to/model.gguf
cloud9-llama-server -m /path/to/model.gguf -ngl 99 -c 32768 -fa on
```

## 🧠 自动路由
默认 `auto` 模式下，普通请求优先使用 **upstream + Cloud9**，以获得最新 llama.cpp/Vulkan 支持；MTP/NextN 类型任务可在本机 gate 证明更快时使用 **Atomic**。也可以通过 `CLOUD9_ENGINE_BACKEND=upstream` 或 `atomic` 强制选择。

## 📊 为什么不只用 Atomic？
2026-09-16 的 Radeon 780M 实测没有“全场冠军”：Atomic 在较长 MTP 生成中更快（约 33.26 t/s），而更新的 upstream + Cloud9 在 Vulkan prefill 上明显更快（约 335 t/s，对比 Atomic 约 301 t/s）。Cloud9 Engine 的目标就是保留两边优势，而不是隐藏这个取舍。

## 🔄 更新策略
GitHub 定时检查 llama.cpp 与 Atomic，更新 `sources.lock` 并创建 PR。CI 验证补丁仍可应用且 Vulkan 构建正常。服务器只构建 candidate；只有本机真实模型 gate 通过后才切换生产 symlink。

更多信息：[架构](docs/architecture.md)、[基准测试](docs/benchmarks.md)、[安装](docs/installation.md)、[安全更新](docs/updates.md)。

## 📄 许可证
Cloud9 Engine 自有脚本与文档采用 MIT；upstream 源码保留各自许可证。
