#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/state/current/upstream-latest/bin"

cat > "$tmp/state/current/upstream-latest/bin/llama-server" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "--help" ]]; then
  echo "--rpc --split-mode --tensor-split"
  exit 0
fi
printf '%q ' "$@"
printf '\n'
EOF
chmod +x "$tmp/state/current/upstream-latest/bin/llama-server"

cat > "$tmp/state/current/upstream-latest/bin/ggml-rpc-server" <<'EOF'
#!/usr/bin/env bash
printf '%q ' "$@"
printf '\n'
EOF
chmod +x "$tmp/state/current/upstream-latest/bin/ggml-rpc-server"

echo "1..6"

out=$(CLOUD9_ENGINE_HOME="$tmp/state" CLOUD9_ENGINE_BACKEND=upstream-latest CLOUD9_ENGINE_RDNA_TUNING=off \
      CLOUD9_ENGINE_RPC_PEERS=10.10.10.2:50052 "$ROOT/bin/cloud9-llama-server" -m /nonexistent.gguf -c 4096)
grep -q -- "--rpc 10.10.10.2:50052" <<<"$out" && grep -q -- "--split-mode layer" <<<"$out"
echo "ok 1 - coordinator defaults RPC to layer split"

out=$(CLOUD9_ENGINE_HOME="$tmp/state" CLOUD9_ENGINE_BACKEND=upstream-latest CLOUD9_ENGINE_RDNA_TUNING=off \
      CLOUD9_ENGINE_RPC_PEERS=10.10.10.2:50052 CLOUD9_ENGINE_RPC_SPLIT_MODE=tensor CLOUD9_ENGINE_TENSOR_SPLIT=3,2 \
      "$ROOT/bin/cloud9-llama-server" -m /nonexistent.gguf)
grep -Fq -- "--split-mode tensor" <<<"$out" && grep -Fq -- "--tensor-split 3\\,2" <<<"$out"
echo "ok 2 - tensor mode and split require explicit configuration"

if CLOUD9_ENGINE_HOME="$tmp/state" CLOUD9_ENGINE_RPC_BACKEND=upstream-latest CLOUD9_RPC_HOST=10.10.10.2 \
   "$ROOT/bin/cloud9-rpc-server" >/dev/null 2>"$tmp/err"; then
  echo "not ok 3 - remote worker bind should be refused" >&2; exit 1
fi
grep -q "CLOUD9_RPC_ALLOW_REMOTE=1" "$tmp/err"
echo "ok 3 - remote worker bind is refused by default"

out=$(CLOUD9_ENGINE_HOME="$tmp/state" CLOUD9_ENGINE_RPC_BACKEND=upstream-latest CLOUD9_RPC_HOST=10.10.10.2 \
      CLOUD9_RPC_ALLOW_REMOTE=1 CLOUD9_RPC_CACHE=1 "$ROOT/bin/cloud9-rpc-server")
grep -q -- "-H 10.10.10.2" <<<"$out" && grep -q -- "-p 50052" <<<"$out" && grep -q -- "-c" <<<"$out"
echo "ok 4 - explicit private worker bind includes cache"

if CLOUD9_ENGINE_HOME="$tmp/state" CLOUD9_ENGINE_RPC_BACKEND=upstream-latest \
   "$ROOT/bin/cloud9-rpc-server" -H 0.0.0.0 >/dev/null 2>"$tmp/err-cli"; then
  echo "not ok 5 - CLI remote bind should be refused" >&2; exit 1
fi
grep -q "CLOUD9_RPC_ALLOW_REMOTE=1" "$tmp/err-cli"
echo "ok 5 - direct CLI host override cannot bypass remote-bind guard"

out=$(CLOUD9_ENGINE_HOME="$tmp/state" "$ROOT/scripts/distributed-doctor.sh")
grep -q "rpc worker: upstream-latest" <<<"$out" && grep -q "coordinator --rpc: yes" <<<"$out"
echo "ok 6 - distributed doctor detects RPC capabilities"
