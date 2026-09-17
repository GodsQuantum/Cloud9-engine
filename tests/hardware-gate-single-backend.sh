#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/home/state" "$T/upstream/bin" "$T/fakebin"
: > "$T/model.gguf"
cat > "$T/home/candidates.env" <<EOC
UPSTREAM=$T/upstream
EOC
cat > "$T/upstream/bin/llama-server" <<'EOC'
#!/usr/bin/env bash
sleep 30
EOC
cat > "$T/fakebin/curl" <<'EOC'
#!/usr/bin/env bash
echo '{"status":"ok"}'
EOC
cat > "$T/fakebin/python3" <<'EOC'
#!/usr/bin/env bash
if [[ "${1:-}" == *bench_client.py ]]; then
  echo '{"median_decode_tps":42.0}'
  exit 0
fi
exec /usr/bin/python3 "$@"
EOC
chmod +x "$T/upstream/bin/llama-server" "$T/fakebin/"*
if ! PATH="$T/fakebin:$PATH" CLOUD9_ENGINE_HOME="$T/home" CLOUD9_ENGINE_RENDER_DEVICE=/nonexistent \
  CLOUD9_ENGINE_GATE_BACKENDS=upstream timeout 8 bash "$ROOT/scripts/hardware-gate.sh" "$T/model.gguf" >"$T/out" 2>"$T/err"; then
  echo "single-backend gate unexpectedly failed:" >&2
  cat "$T/out" "$T/err" >&2
  exit 1
fi
grep -qx 'CLOUD9_ENGINE_GENERAL_BACKEND=upstream' "$T/home/profiles.local.env"
grep -qx 'CLOUD9_ENGINE_MTP_BACKEND=upstream' "$T/home/profiles.local.env"
[[ "$(readlink "$T/home/current/upstream")" == "$T/upstream" ]]
[[ ! -e "$T/home/current/atomic" ]]
echo 'hardware-gate single-backend test: PASS'
