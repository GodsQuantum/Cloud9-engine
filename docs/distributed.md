# Distributed Cloud9 Engine

Cloud9 Engine can use the current llama.cpp RPC backend to combine a coordinator
with one or more worker machines while keeping the normal OpenAI-compatible
`llama-server` endpoint on the coordinator.

## Safety model

Nothing is exposed remotely after installation. `cloud9-rpc-server` binds to
`127.0.0.1` unless a private bind address is explicitly configured and
`CLOUD9_RPC_ALLOW_REMOTE=1` is set.

The upstream ggml RPC protocol is not authenticated or encrypted. Never bind it
to the public internet. Use a dedicated point-to-point link, trusted LAN/VLAN,
WireGuard/Tailscale, or another private transport.

## Build

Cloud9 upstream-derived builds enable `GGML_RPC=ON`, producing both:

- `llama-server` with the RPC backend;
- `ggml-rpc-server` for worker nodes.

Atomic and Prism remain local specialist backends; distributed execution uses
the upstream-derived Cloud9 runtime unless separately validated.

## Worker node

After installing Cloud9 Engine on the worker, configure a private link address:

```bash
CLOUD9_RPC_HOST=192.168.50.2 \
CLOUD9_RPC_ALLOW_REMOTE=1 \
CLOUD9_RPC_CACHE=1 \
cloud9-engine rpc-worker
```

The tensor cache is enabled by default by the Cloud9 wrapper. It prevents large
tensors from being retransferred each time the same model is loaded.

To expose only one accelerator:

```bash
CLOUD9_RPC_DEVICE=Vulkan0 cloud9-engine rpc-worker
```

## Coordinator

Configure one or more private worker endpoints:

```bash
export CLOUD9_ENGINE_RPC_PEERS=192.168.50.2:50052
cloud9-llama-server -m /models/model.gguf -ngl all -c 32768
```

Cloud9 injects `--rpc` and defaults to `--split-mode layer`.

For asymmetric devices, tune placement only after an A/B:

```bash
export CLOUD9_ENGINE_TENSOR_SPLIT=3,2
```

This controls placement proportions. It does not enable tensor-parallel mode.
To test tensor parallelism explicitly:

```bash
export CLOUD9_ENGINE_RPC_SPLIT_MODE=tensor
```

Tensor mode is experimental and performs cross-device reductions within each
layer. It therefore needs a lower-latency/higher-bandwidth interconnect than
layer split and is unavailable for several MoE/hybrid architectures.

## USB4 host-to-host on Linux Ryzen

Use the USB4/Thunderbolt networking interface as a private IP link and point
RPC at that IP. Current llama.cpp Linux RDMA support targets RoCEv2/libibverbs
devices; the documented Thunderbolt RDMA path is macOS/Apple Silicon specific.
Cloud9 must therefore assume TCP over the Linux USB4 network link unless the
host actually exposes a supported verbs/RDMA device.

Recommended first-pass policy:

1. private point-to-point addressing;
2. `cloud9-engine distributed-doctor WORKER_IP:50052`;
3. worker tensor cache enabled;
4. `layer` split first;
5. benchmark explicit placement ratios;
6. test `tensor` only after a layer baseline and reject it if TTFT, decode,
   memory/GTT, thermals or correctness regress.

## Workload policy

- Large LLMs that do not fit comfortably on one node: RPC layer split can add
  memory and, on a sufficiently fast link, sometimes throughput.
- Small LLMs: keep one request on one node; replicas usually beat sharding.
- Embeddings/STT/TTS: request-level routing/replicas are normally better than
  splitting a small model across machines.
- Strata: its optimized layer split is currently intra-host. Run Strata locally
  per machine and route complete requests between replicas until upstream gains
  a multi-host transport.

## Diagnostics

```bash
cloud9-engine distributed-doctor
cloud9-engine distributed-doctor 192.168.50.2:50052
```

The doctor checks for an RPC worker binary and coordinator flags, then tests TCP
reachability if a peer is supplied.
