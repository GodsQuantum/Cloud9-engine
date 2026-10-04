#!/usr/bin/env bash
set -Eeuo pipefail

CTID=${CLOUD9_ENGINE_CTID:-410}
WORKTREE=${CLOUD9_ENGINE_RUNTIME_WORKTREE:-/srv/lxc/ia-compute/data/worktrees/cloud9-engine-lab}
MAX_START_TCTL=${CLOUD9_BENCH_START_MAX_TCTL:-72}
MAX_LOAD1=${CLOUD9_BENCH_MAX_LOAD1:-8}
MAX_IO_PSI_FULL=${CLOUD9_BENCH_MAX_IO_PSI_FULL:-2.0}
MIN_HOST_AVAIL_KB=${CLOUD9_BENCH_MIN_HOST_AVAIL_KB:-25165824}
MIN_CT_AVAIL_KB=${CLOUD9_BENCH_MIN_CT_AVAIL_KB:-16777216}
WATCH_MAX_TCTL=${CLOUD9_BENCH_WATCH_MAX_TCTL:-80}
WATCH_MAX_GTT_BYTES=${CLOUD9_BENCH_WATCH_MAX_GTT_BYTES:-34359738368}
WATCH_MIN_HOST_AVAIL_KB=${CLOUD9_BENCH_WATCH_MIN_HOST_AVAIL_KB:-20971520}

tctl() {
  sensors 2>/dev/null | awk '/Tctl:/ {gsub(/[+°C]/,"",$2); printf "%.0f\n",$2; exit}'
}
load1() { awk '{print $1}' /proc/loadavg; }
host_avail() { awk '/MemAvailable:/{print $2}' /proc/meminfo; }
ct_avail() { pct exec "$CTID" -- awk '/MemAvailable:/{print $2}' /proc/meminfo | tail -1; }
gtt_used() { cat /sys/class/drm/card0/device/mem_info_gtt_used 2>/dev/null || echo 0; }
io_full_avg10() { awk '/^full /{for(i=1;i<=NF;i++) if($i ~ /^avg10=/){split($i,a,"="); print a[2]}}' /proc/pressure/io; }
swap_io_clean() {
  local line
  line=$(vmstat 1 2 | tail -1)
  awk '{exit !($7==0 && $8==0)}' <<<"$line"
}

temp=$(tctl); temp=${temp:-999}
l1=$(load1)
ha=$(host_avail)
ca=$(ct_avail)
io=$(io_full_avg10); io=${io:-999}

awk -v x="$l1" -v m="$MAX_LOAD1" 'BEGIN{exit !(x<=m)}' ||
  { echo "REFUSE: load1=$l1 > $MAX_LOAD1" >&2; exit 4; }
(( temp < MAX_START_TCTL )) ||
  { echo "REFUSE: Tctl=${temp}C >= ${MAX_START_TCTL}C" >&2; exit 4; }
(( ha >= MIN_HOST_AVAIL_KB && ca >= MIN_CT_AVAIL_KB )) ||
  { echo "REFUSE: memory host_kb=$ha ct_kb=$ca" >&2; exit 4; }
awk -v x="$io" -v m="$MAX_IO_PSI_FULL" 'BEGIN{exit !(x<=m)}' ||
  { echo "REFUSE: io PSI full avg10=$io > $MAX_IO_PSI_FULL" >&2; exit 4; }
swap_io_clean || { echo "REFUSE: active swap I/O" >&2; exit 4; }
pgrep -af 'proxmox-backup-client backup' >/dev/null &&
  { echo "REFUSE: active PBS backup" >&2; exit 4; }

echo "Cloud9 bakeoff gate OK: Tctl=${temp}C load1=$l1 io_full_avg10=$io host_avail_kb=$ha ct_avail_kb=$ca"

set +e
pct exec "$CTID" -- /usr/local/sbin/cloud9-exclusive-gpu-run   python3 "$WORKTREE/scripts/model-bakeoff.py" "$@" &
runner=$!
set -e

trip=""
peak_gtt=0
max_temp=$temp
while kill -0 "$runner" 2>/dev/null; do
  t=$(tctl); t=${t:-999}
  g=$(gtt_used)
  h=$(host_avail)
  (( g > peak_gtt )) && peak_gtt=$g || true
  (( t > max_temp )) && max_temp=$t || true
  if (( t >= WATCH_MAX_TCTL )); then trip=TEMP; break; fi
  if (( g > WATCH_MAX_GTT_BYTES )); then trip=GTT; break; fi
  if (( h < WATCH_MIN_HOST_AVAIL_KB )); then trip=HOST_MEM; break; fi
  sleep 2
done

if [[ -n "$trip" ]]; then
  echo "WATCHDOG_TRIP=$trip max_tctl=$max_temp peak_gtt=$peak_gtt" >&2
  pct exec "$CTID" -- bash -lc 'pkill -TERM -f "scripts/model-bakeoff.py" 2>/dev/null || true; pkill -TERM -x llama-server 2>/dev/null || true; sleep 3; pkill -KILL -x llama-server 2>/dev/null || true' || true
fi

set +e
wait "$runner"; rc=$?
set -e

echo "bakeoff_rc=$rc watchdog=${trip:-none} max_tctl=$max_temp peak_gtt=$peak_gtt"

# The inner arbiter owns restoration. Verify the important public services after it exits.
for url in http://192.168.1.219:8091/health http://192.168.1.219:8005/health; do
  for _ in $(seq 1 30); do
    curl -fsS --max-time 2 "$url" >/dev/null && { echo "health OK $url"; break; }
    sleep 1
  done
done

[[ -z "$trip" ]] || exit 125
exit "$rc"
