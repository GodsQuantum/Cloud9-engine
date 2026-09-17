#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/home" "$tmp/atomic/bin" "$tmp/upstream/bin" "$tmp/fakebin"
: > "$tmp/model.gguf"
mkdir -p "$tmp/home/state"
echo '{"median_decode_tps":999.0}' > "$tmp/home/state/upstream-mtp.json"
cat > "$tmp/home/candidates.env" <<EOF
ATOMIC=$tmp/atomic
UPSTREAM=$tmp/upstream
EOF
cat > "$tmp/atomic/bin/llama-server" <<'EOF'
#!/usr/bin/env bash
sleep 30
EOF
cat > "$tmp/upstream/bin/llama-server" <<'EOF'
#!/usr/bin/env bash
exit 1
EOF
chmod +x "$tmp/atomic/bin/llama-server" "$tmp/upstream/bin/llama-server"
cat > "$tmp/fakebin/curl" <<'EOF'
#!/usr/bin/env bash
case "$*" in *19881*) echo '{"status":"ok"}'; exit 0;; *) exit 7;; esac
EOF
chmod +x "$tmp/fakebin/curl"
cat > "$tmp/fakebin/python3" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == *bench_client.py ]]; then
  echo '{"median_decode_tps":10.0}'
  exit 0
fi
exec /usr/bin/python3 "$@"
EOF
chmod +x "$tmp/fakebin/python3"
if ! PATH="$tmp/fakebin:$PATH" CLOUD9_ENGINE_HOME="$tmp/home" \
  bash "$ROOT/scripts/hardware-gate.sh" "$tmp/model.gguf" >"$tmp/gate.out" 2>"$tmp/gate.err"; then
  cat "$tmp/gate.out" "$tmp/gate.err" >&2
  exit 98
fi
grep -qx 'CLOUD9_ENGINE_GENERAL_BACKEND=atomic' "$tmp/home/profiles.local.env"
grep -qx 'CLOUD9_ENGINE_MTP_BACKEND=atomic' "$tmp/home/profiles.local.env"
[[ "$(readlink "$tmp/home/current/atomic")" == "$tmp/atomic" ]]
[[ ! -e "$tmp/home/current/upstream" ]]
[[ ! -e "$tmp/home/state/upstream-mtp.json" ]]
echo 'hardware-gate fallback test: PASS'
