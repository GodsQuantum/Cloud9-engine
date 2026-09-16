# Installation

## Requirements

Cloud9 Engine targets Linux with a working Vulkan driver. You need: Git, Python 3, CMake, a C/C++ compiler, Vulkan headers/loader, `glslc`, and preferably `ccache`. A recent Mesa/RADV stack is recommended for AMD RDNA.

Examples:

```bash
# Arch / CachyOS
sudo pacman -S --needed base-devel git cmake ninja ccache vulkan-headers vulkan-icd-loader shaderc

# Ubuntu / Debian family
sudo apt update
sudo apt install -y build-essential git cmake ninja-build ccache libvulkan-dev glslc
```

Verify the GPU first:

```bash
vulkaninfo --summary
```

## User install

```bash
git clone https://github.com/GodsQuantum/cloud9-engine.git
cd cloud9-engine
./scripts/install.sh
cloud9-engine doctor
cloud9-engine build
```

The default state directory is `~/.local/share/cloud9-engine`. Override it with `CLOUD9_ENGINE_HOME`.

## First hardware gate

Use a model representative of your real workload:

```bash
cloud9-engine gate /models/model.gguf
cloud9-engine status
```

The gate promotes versioned candidates through symlinks only after they successfully load and serve inference. The generated local routing profile is not committed to Git.

## Running

```bash
cloud9-llama-server -m /models/model.gguf -ngl 99 -c 32768 -fa on
```

Everything after `cloud9-llama-server` is passed to the selected llama-server backend.
