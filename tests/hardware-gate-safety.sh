#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
mk_fixture() {
  T=$(mktemp -d)
  mkdir -p "$T/home/state" "$T/atomic/bin" "$T/upstream/bin" "$T/fakebin"
  : > "$T/model.gguf"
  cat > "$T/home/candidates.env" <<EOC
ATOMIC=$T/atomic
UPSTREAM=$T/upstream
EOC
  cat > "$T/fakebin/curl" <<'EOC'
#!/usr/bin/env bash
echo '{"status":"ok"}'
EOC
  cat > "$T/fakebin/python3" <<'EOC'
#!/usr/bin/env bash
if [[ "${1:-}" == *bench_client.py ]]; then echo '{"median_decode_tps":10.0}'; exit 0; fi
exec /usr/bin/python3 "$@"
EOC
  chmod +x "$T/fakebin/"*
}
cleanup(){ [[ -n "${T:-}" ]] && rm -rf "$T"; }
trap cleanup EXIT

# 1. A second gate must fail before starting any candidate.
mk_fixture
cat > "$T/atomic/bin/llama-server" <<EOC
#!/usr/bin/env bash
touch "$T/atomic-started"; sleep 30
EOC
cp "$T/atomic/bin/llama-server" "$T/upstream/bin/llama-server"; chmod +x "$T/atomic/bin/llama-server" "$T/upstream/bin/llama-server"
exec 9>"$T/home/state/hardware-gate.lock"; flock -n 9
set +e
PATH="$T/fakebin:$PATH" CLOUD9_ENGINE_HOME="$T/home" timeout 5 bash "$ROOT/scripts/hardware-gate.sh" "$T/model.gguf" >/dev/null 2>&1
rc=$?
set -e
[[ $rc -ne 0 ]] || { echo "lock test: gate unexpectedly succeeded" >&2; exit 1; }
[[ ! -e "$T/atomic-started" ]] || { echo "lock test: candidate started despite held lock" >&2; exit 1; }
exec 9>&-
rm -rf "$T"; T=

# 2. An occupied benchmark port must fail before starting candidates.
mk_fixture
cat > "$T/atomic/bin/llama-server" <<EOC
#!/usr/bin/env bash
touch "$T/atomic-started"; sleep 30
EOC
cp "$T/atomic/bin/llama-server" "$T/upstream/bin/llama-server"; chmod +x "$T/atomic/bin/llama-server" "$T/upstream/bin/llama-server"
/usr/bin/python3 -m http.server 19881 --bind 127.0.0.1 >"$T/http.log" 2>&1 & hp=$!
trap 'kill ${hp:-0} 2>/dev/null || true; cleanup' EXIT
sleep 0.3
set +e
PATH="$T/fakebin:$PATH" CLOUD9_ENGINE_HOME="$T/home" timeout 5 bash "$ROOT/scripts/hardware-gate.sh" "$T/model.gguf" >/dev/null 2>&1
rc=$?
set -e
kill "$hp" 2>/dev/null || true; wait "$hp" 2>/dev/null || true; hp=
[[ $rc -ne 0 ]] || { echo "port test: gate unexpectedly succeeded" >&2; exit 1; }
[[ ! -e "$T/atomic-started" ]] || { echo "port test: candidate started on dirty gate" >&2; exit 1; }
rm -rf "$T"; T=
trap cleanup EXIT

# 3. Cleanup must be bounded even if a server ignores SIGTERM.
mk_fixture
cat > "$T/atomic/bin/llama-server" <<'EOC'
#!/usr/bin/env bash
trap '' TERM
sleep 30
EOC
cat > "$T/upstream/bin/llama-server" <<'EOC'
#!/usr/bin/env bash
exit 1
EOC
chmod +x "$T/atomic/bin/llama-server" "$T/upstream/bin/llama-server"
set +e
PATH="$T/fakebin:$PATH" CLOUD9_ENGINE_HOME="$T/home" timeout 8 bash "$ROOT/scripts/hardware-gate.sh" "$T/model.gguf" >/dev/null 2>&1
rc=$?
set -e
[[ $rc -eq 0 ]] || { echo "cleanup test: gate did not complete cleanly (rc=$rc)" >&2; exit 1; }
echo "hardware-gate safety tests: PASS"
