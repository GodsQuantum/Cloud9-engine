#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ENGINE_HOME=${CLOUD9_ENGINE_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/cloud9-engine}
MODEL=${1:-${CLOUD9_ENGINE_GATE_MODEL:-}}
[[ -n "$MODEL" && -f "$MODEL" ]] || { echo 'Usage: cloud9-engine gate /path/model.gguf' >&2; exit 2; }
[[ -r "$ENGINE_HOME/candidates.env" ]] || { echo 'No candidates. Run cloud9-engine build first.' >&2; exit 2; }
# shellcheck source=/dev/null
source "$ENGINE_HOME/candidates.env"
mkdir -p "$ENGINE_HOME/state" "$ENGINE_HOME/current"
PROMPT=${CLOUD9_ENGINE_GATE_PROMPT:-$ROOT/bench/prompt.txt}
run_mtp(){
  local name=$1 dir=$2 port=$3 mode=${4:-}
  local log="$ENGINE_HOME/state/${name}-gate.log" out="$ENGINE_HOME/state/${name}-mtp.json"
  local -a extra_args=()
  [[ "$mode" == upstream ]] && extra_args+=(--lazy-mode off)
  "$dir/bin/llama-server" -m "$MODEL" -ngl 99 -c 8192 -np 1 -b 2048 -ub 512 -t "${CLOUD9_ENGINE_THREADS:-8}" -tb "${CLOUD9_ENGINE_THREADS:-8}" -fa on -ctk f16 -ctv f16 --fit off --jinja --reasoning off --reasoning-budget 0 --spec-type draft-mtp --spec-draft-n-max 2 --spec-draft-p-min 0 --no-spec-draft-backend-sampling --no-host -lm mmap "${extra_args[@]}" --host 127.0.0.1 --port "$port" --no-warmup >"$log" 2>&1 &
  local pid=$!; trap 'kill $pid 2>/dev/null || true' RETURN
  for _ in $(seq 1 120); do curl -sf "http://127.0.0.1:$port/health" | grep -q '"status":"ok"' && break; kill -0 "$pid" 2>/dev/null || return 1; sleep 1; done
  curl -sf "http://127.0.0.1:$port/health" | grep -q '"status":"ok"' || return 1
  python3 "$ROOT/scripts/bench_client.py" --port "$port" --prompt "$PROMPT" --runs "${CLOUD9_ENGINE_GATE_RUNS:-3}" --tokens "${CLOUD9_ENGINE_GATE_TOKENS:-128}" > "$out"
  kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; trap - RETURN
}
AT_OK=0; UP_OK=0
run_mtp atomic "$ATOMIC" 19881 atomic && AT_OK=1 || true
run_mtp upstream "$UPSTREAM" 19882 upstream && UP_OK=1 || true
(( AT_OK || UP_OK )) || { echo 'Hardware gate failed for both candidates.' >&2; exit 3; }
ln -sfn "$ATOMIC" "$ENGINE_HOME/current/atomic"
ln -sfn "$UPSTREAM" "$ENGINE_HOME/current/upstream"
mtp=atomic
if (( AT_OK && UP_OK )); then
  mtp=$(python3 - "$ENGINE_HOME/state/atomic-mtp.json" "$ENGINE_HOME/state/upstream-mtp.json" <<'PYSEL'
import json,sys
a=json.load(open(sys.argv[1]))['median_decode_tps']; u=json.load(open(sys.argv[2]))['median_decode_tps']; print('atomic' if a>=u else 'upstream')
PYSEL
)
elif (( UP_OK )); then mtp=upstream; fi
cat > "$ENGINE_HOME/profiles.local.env" <<EOF
CLOUD9_ENGINE_GENERAL_BACKEND=upstream
CLOUD9_ENGINE_MTP_BACKEND=$mtp
EOF
echo "Promoted. General=upstream, MTP=$mtp"
for b in atomic upstream; do [[ -f "$ENGINE_HOME/state/$b-mtp.json" ]] && echo "$b: $(cat "$ENGINE_HOME/state/$b-mtp.json")"; done
