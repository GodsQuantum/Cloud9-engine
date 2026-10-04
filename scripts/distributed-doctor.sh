#!/usr/bin/env bash
set -euo pipefail

ENGINE_HOME=${CLOUD9_ENGINE_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/cloud9-engine}
peer=${1:-${CLOUD9_ENGINE_RPC_PEERS:-}}

echo "Cloud9 Engine distributed doctor"
echo "  state: $ENGINE_HOME"

rpc_bin=""
for b in upstream upstream-latest upstream-fast upstream-next upstream-pym; do
  if [[ -x "$ENGINE_HOME/current/$b/bin/ggml-rpc-server" ]]; then
    rpc_bin="$ENGINE_HOME/current/$b/bin/ggml-rpc-server"
    echo "  rpc worker: $b ($rpc_bin)"
    break
  fi
done
[[ -n "$rpc_bin" ]] || echo "  rpc worker: not built/promoted yet (requires GGML_RPC=ON)"

server=""
for b in upstream-latest upstream-fast upstream-next upstream-pym upstream; do
  [[ -x "$ENGINE_HOME/current/$b/bin/llama-server" ]] && { server="$ENGINE_HOME/current/$b/bin/llama-server"; break; }
done
if [[ -n "$server" ]]; then
  help=$("$server" --help 2>&1 || true)
  grep -q -- "--rpc" <<<"$help" && echo "  coordinator --rpc: yes" || echo "  coordinator --rpc: no"
  grep -q -- "--split-mode" <<<"$help" && echo "  split-mode: yes" || echo "  split-mode: no"
  grep -q -- "--tensor-split" <<<"$help" && echo "  tensor-split: yes" || echo "  tensor-split: no"
else
  echo "  coordinator: no promoted llama-server"
fi

if [[ -n "$peer" ]]; then
  first=${peer%%,*}
  host=${first%:*}
  port=${first##*:}
  python3 - "$host" "$port" <<'PY'
import socket,sys,time
host,port=sys.argv[1],int(sys.argv[2])
t=time.monotonic()
try:
    with socket.create_connection((host,port),timeout=2):
        dt=(time.monotonic()-t)*1000
        print(f"  peer {host}:{port}: TCP reachable ({dt:.1f} ms connect)")
except Exception as e:
    print(f"  peer {host}:{port}: UNREACHABLE ({e})")
    raise SystemExit(4)
PY
  if [[ -n "$server" ]]; then
    echo "  RPC protocol/device probe:"
    if rpc_devices=$("$server" --rpc "$peer" --list-devices 2>&1); then
      sed 's/^/    /' <<<"$rpc_devices"
    else
      sed 's/^/    /' <<<"$rpc_devices" >&2
      echo "  RPC protocol/device probe: FAILED" >&2
      exit 5
    fi
  fi
fi

if command -v ip >/dev/null; then
  echo "  candidate high-speed links:"
  ip -br link 2>/dev/null | awk '$1 ~ /thunderbolt|usb|enx|enp/ {print "    "$0}' || true
fi
