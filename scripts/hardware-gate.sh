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

exec 9>"$ENGINE_HOME/state/hardware-gate.lock"
flock -n 9 || { echo 'Hardware gate already running; refusing concurrent benchmark.' >&2; exit 4; }

port_in_use() {
  ss -H -ltn "sport = :$1" 2>/dev/null | grep -q .
}
for port in 19881 19882; do
  port_in_use "$port" && { echo "Hardware gate port $port is already in use; refusing dirty benchmark." >&2; exit 4; }
done
if pgrep -x llama-server >/dev/null 2>&1; then
  echo 'A llama-server process is already running; unload it before the hardware gate.' >&2
  exit 4
fi
render_dev=${CLOUD9_ENGINE_RENDER_DEVICE:-/dev/dri/renderD128}
if [[ -e "$render_dev" ]]; then
  python3 - "$render_dev" <<'PY' || { echo "GPU render device $render_dev cannot be opened; refusing hardware gate." >&2; exit 5; }
import os,sys
fd=os.open(sys.argv[1], os.O_RDWR)
os.close(fd)
PY
fi

cleanup_server() {
  local pid=$1 name=$2
  if ! kill -0 "$pid" 2>/dev/null; then wait "$pid" 2>/dev/null || true; return 0; fi
  kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 1 10); do kill -0 "$pid" 2>/dev/null || { wait "$pid" 2>/dev/null || true; return 0; }; sleep 0.2; done
  kill -KILL "$pid" 2>/dev/null || true
  for _ in $(seq 1 10); do kill -0 "$pid" 2>/dev/null || { wait "$pid" 2>/dev/null || true; return 0; }; sleep 0.2; done
  echo "FATAL: $name gate server PID $pid survived SIGKILL; refusing to start another backend." >&2
  return 1
}

run_mtp(){
  local name=$1 dir=$2 port=$3 mode=${4:-}
  local log="$ENGINE_HOME/state/${name}-gate.log" out="$ENGINE_HOME/state/${name}-mtp.json" tmp="$ENGINE_HOME/state/${name}-mtp.json.tmp"
  local pid rc=0 healthy=0
  rm -f "$log" "$out" "$tmp"
  local -a extra_args=(--poll 100 --poll-batch 0)
  local -a env_args=()
  if [[ "$mode" == upstream ]]; then
    extra_args+=(--lazy-mode off)
    env_args+=(env RADV_PERFTEST="${RADV_PERFTEST:+$RADV_PERFTEST,}nogttspill")
  fi
  "${env_args[@]}" "$dir/bin/llama-server" -m "$MODEL" -ngl 99 -c 8192 -np 1 -b 1024 -ub 1024 -t "${CLOUD9_ENGINE_THREADS:-8}" -tb "${CLOUD9_ENGINE_THREADS:-8}" -fa on -ctk f16 -ctv f16 --fit off --jinja --reasoning off --reasoning-budget 0 --spec-type draft-mtp --spec-draft-n-max 2 --spec-draft-p-min 0 --no-spec-draft-backend-sampling -lm mmap "${extra_args[@]}" --host 127.0.0.1 --port "$port" --no-warmup >"$log" 2>&1 &
  pid=$!
  for _ in $(seq 1 120); do
    kill -0 "$pid" 2>/dev/null || break
    if curl -sf "http://127.0.0.1:$port/health" | grep -q '"status":"ok"'; then healthy=1; break; fi
    sleep 1
  done
  if (( ! healthy )); then
    rc=1
  elif ! python3 "$ROOT/scripts/bench_client.py" --port "$port" --prompt "$PROMPT" --runs "${CLOUD9_ENGINE_GATE_RUNS:-3}" --tokens "${CLOUD9_ENGINE_GATE_TOKENS:-256}" > "$tmp"; then
    rc=$?
    (( rc == 0 )) && rc=1
  fi
  if ! cleanup_server "$pid" "$name"; then rm -f "$tmp"; return 125; fi
  if (( rc != 0 )); then rm -f "$tmp"; return "$rc"; fi
  mv "$tmp" "$out"
}

AT_OK=0; UP_OK=0
if run_mtp atomic "$ATOMIC" 19881 atomic; then AT_OK=1; else rc=$?; (( rc == 125 )) && exit 125; fi
if run_mtp upstream "$UPSTREAM" 19882 upstream; then UP_OK=1; else rc=$?; (( rc == 125 )) && exit 125; fi
(( AT_OK || UP_OK )) || { echo 'Hardware gate failed for both candidates.' >&2; exit 3; }
(( AT_OK )) && ln -sfn "$ATOMIC" "$ENGINE_HOME/current/atomic"
(( UP_OK )) && ln -sfn "$UPSTREAM" "$ENGINE_HOME/current/upstream"
general=atomic
(( UP_OK )) && general=upstream
mtp=atomic
if (( AT_OK && UP_OK )); then
  mtp=$(python3 - "$ENGINE_HOME/state/atomic-mtp.json" "$ENGINE_HOME/state/upstream-mtp.json" <<'PYSEL'
import json,sys
a=json.load(open(sys.argv[1]))['median_decode_tps']; u=json.load(open(sys.argv[2]))['median_decode_tps']; print('atomic' if a>=u else 'upstream')
PYSEL
)
elif (( UP_OK )); then mtp=upstream; fi
cat > "$ENGINE_HOME/profiles.local.env" <<EOF2
CLOUD9_ENGINE_GENERAL_BACKEND=$general
CLOUD9_ENGINE_MTP_BACKEND=$mtp
EOF2
echo "Promoted. General=$general, MTP=$mtp"
for b in atomic upstream; do [[ -f "$ENGINE_HOME/state/$b-mtp.json" ]] && echo "$b: $(cat "$ENGINE_HOME/state/$b-mtp.json")"; done
exit 0
