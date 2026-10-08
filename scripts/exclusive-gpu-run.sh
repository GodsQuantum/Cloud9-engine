#!/usr/bin/env bash
set -Eeuo pipefail

[[ $# -gt 0 ]] || { echo "Usage: $0 COMMAND [ARG...]" >&2; exit 2; }

# This MUST be the same lock used by cloud9-model-router.
LOCK_FILE=${CLOUD9_GPU_LOCK:-/run/cloud9-gpu.lock}
RENDER_DEV=${CLOUD9_ENGINE_RENDER_DEVICE:-/dev/dri/renderD128}
ROUTER=cloud9-engine-router.service
EMBED=cloud9-embedding.service
LEMOND=lemond.service
SPEACHES=speaches
VOICESTUDIO=voicestudio
CHATTERBOX=chatterbox-vc
DOCLING=docling-serve
FRONT_SOCKETS=(comfyui-proxy.socket autopublisher-image-proxy.socket)
FRONT_PROXIES=(comfyui-proxy.service autopublisher-image-proxy.service)
USER_GPU_SERVICES=(comfyui.service autopublisher-image.service)

# Arbitration profiles:
# - exclusive: strict zero-user GPU window (benchmarks/Strata/unsafe loads)
# - coexist-light: heavy jobs remain mutually exclusive while Embedding + Speaches stay available
MODE=${CLOUD9_GPU_MODE:-exclusive}
case "$MODE" in
  exclusive|coexist-light) ;;
  *) echo "Unknown CLOUD9_GPU_MODE=$MODE (expected exclusive or coexist-light)" >&2; exit 2 ;;
esac
STOP_LIGHT=1
if [[ "$MODE" == "coexist-light" ]]; then
  min_avail_mib=${CLOUD9_GPU_COEXIST_MIN_AVAILABLE_MIB:-12288}
  max_gtt_mib=${CLOUD9_GPU_COEXIST_MAX_GTT_MIB:-8192}
  avail_mib=$(awk '/MemAvailable:/ {print int($2/1024)}' /proc/meminfo)
  gtt_bytes=$(cat /sys/class/drm/card0/device/mem_info_gtt_used 2>/dev/null || echo 0)
  gtt_mib=$((gtt_bytes/1024/1024))
  if (( avail_mib < min_avail_mib || gtt_mib > max_gtt_mib )); then
    echo "coexist-light preflight not safe (MemAvailable=${avail_mib}MiB, GTT=${gtt_mib}MiB); falling back to exclusive." >&2
    MODE=exclusive
  else
    STOP_LIGHT=0
    echo "coexist-light preflight OK (MemAvailable=${avail_mib}MiB, GTT=${gtt_mib}MiB)."
  fi
fi

exec 9>"$LOCK_FILE"
flock -n 9 || { echo "Cloud9 GPU is already reserved by another engine/request ($LOCK_FILE)." >&2; exit 4; }

declare -a RESTORE_SOCKETS=()
declare -a RESTORE_SERVICES=()
was_speaches=0
was_voicestudio=0
was_chatterbox=0
was_docling=0

docker inspect -f '{{.State.Running}}' "$SPEACHES" 2>/dev/null | grep -qx true && was_speaches=1 || true
docker inspect -f '{{.State.Running}}' "$VOICESTUDIO" 2>/dev/null | grep -qx true && was_voicestudio=1 || true
docker inspect -f '{{.State.Running}}' "$CHATTERBOX" 2>/dev/null | grep -qx true && was_chatterbox=1 || true
docker inspect -f '{{.State.Running}}' "$DOCLING" 2>/dev/null | grep -qx true && was_docling=1 || true
# Lemonade remains in the heavy/legacy class. Embedding stays live in coexist-light.
for u in "$LEMOND"; do
  systemctl is-active --quiet "$u" && RESTORE_SERVICES+=("$u")
done
if (( STOP_LIGHT )); then
  # Restore Embedding before Router: Router may rely on the embedding backend
  # and shutdown ordering intentionally stops Router first.
  systemctl is-active --quiet "$EMBED" && RESTORE_SERVICES+=("$EMBED")
fi
# Router is stopped for every exclusive/coexist window, so preserve its
# pre-window state explicitly. Older versions only tracked the legacy proxy
# socket and could leave :8090 down after a benchmark or an early command
# failure once that socket unit no longer existed.
systemctl is-active --quiet "$ROUTER" && RESTORE_SERVICES+=("$ROUTER")
for u in "${FRONT_SOCKETS[@]}"; do
  systemctl is-active --quiet "$u" && RESTORE_SOCKETS+=("$u")
done

restore_units() {
  local rc=$?
  trap - EXIT INT TERM
  if (( STOP_LIGHT && was_speaches )); then docker start "$SPEACHES" >/dev/null 2>&1 || true; fi
  if (( was_voicestudio )); then docker start "$VOICESTUDIO" >/dev/null 2>&1 || true; fi
  if (( was_chatterbox )); then docker start "$CHATTERBOX" >/dev/null 2>&1 || true; fi
  if (( was_docling )); then docker start "$DOCLING" >/dev/null 2>&1 || true; fi
  for u in "${RESTORE_SERVICES[@]}"; do
    systemctl thaw "$u" >/dev/null 2>&1 || true
    systemctl start "$u" >/dev/null 2>&1 || true
    systemctl thaw "$u" >/dev/null 2>&1 || true
  done
  for u in "${RESTORE_SOCKETS[@]}"; do systemctl start "$u" >/dev/null 2>&1 || true; done

  # Delayed restore outside this systemd cgroup avoids teardown races.
  restore_items=()
  (( STOP_LIGHT && was_speaches )) && restore_items+=("docker:$SPEACHES")
  (( was_voicestudio )) && restore_items+=("docker:$VOICESTUDIO")
  (( was_chatterbox )) && restore_items+=("docker:$CHATTERBOX")
  (( was_docling )) && restore_items+=("docker:$DOCLING")
  for u in "${RESTORE_SERVICES[@]}"; do restore_items+=("systemd:$u"); done
  for u in "${RESTORE_SOCKETS[@]}"; do restore_items+=("systemd:$u"); done
  if (("${#restore_items[@]}")); then
    systemd-run --quiet --collect \
      --unit="cloud9-gpu-restore-${BASHPID}-$(date +%s)" \
      --on-active=3s /usr/local/sbin/cloud9-gpu-second-chance-restore \
      "${restore_items[@]}" >/dev/null 2>&1 || true
  fi
  exit "$rc"
}
trap restore_units EXIT INT TERM

slot_busy() {
  local url=$1 slots
  slots=$(curl -fsS --max-time 1 "$url" 2>/dev/null || true)
  [[ -n "$slots" ]] && grep -Eq '"is_processing"[[:space:]]*:[[:space:]]*true|"state"[[:space:]]*:[[:space:]]*"processing"' <<<"$slots"
}
router_has_established_clients() {
  ss -Htn state established 2>/dev/null | awk '
    $4 ~ /:(8090|18090|18091)$/ || $5 ~ /:(8090|18090|18091)$/ { found=1 }
    END { exit !found }'
}
speaches_has_established_clients() {
  ss -Htn state established 2>/dev/null | awk '
    $4 ~ /:8005$/ || $5 ~ /:8005$/ { found=1 }
    END { exit !found }'
}
voicestudio_has_established_clients() {
  ss -Htn state established 2>/dev/null | awk '
    $4 ~ /:(3900|7443)$/ || $5 ~ /:(3900|7443)$/ { found=1 }
    END { exit !found }'
}
chatterbox_has_established_clients() {
  ss -Htn state established 2>/dev/null | awk '
    $4 ~ /:3901$/ || $5 ~ /:3901$/ { found=1 }
    END { exit !found }'
}
docling_has_established_clients() {
  ss -Htn state established 2>/dev/null | awk '
    $4 ~ /:15001$/ || $5 ~ /:15001$/ { found=1 }
    END { exit !found }'
}

# Never interrupt a user-visible GPU workload.
for u in "${USER_GPU_SERVICES[@]}"; do
  if systemctl is-active --quiet "$u"; then
    unit_pid=$(systemctl show -p MainPID --value "$u" 2>/dev/null || echo 0)
    [ "$unit_pid" = "$$" ] && continue
    echo "$u is active; refusing to interrupt an image job." >&2
    exit 4
  fi
done
if (( STOP_LIGHT )) && systemctl is-active --quiet "$EMBED" && slot_busy http://127.0.0.1:8091/slots; then
  echo "Embedding Engine is processing a request; refusing exclusive GPU preemption." >&2
  exit 4
fi
if (( STOP_LIGHT && was_speaches )) && speaches_has_established_clients; then
  echo "Speaches has an established transcription client; refusing exclusive GPU preemption." >&2
  exit 4
fi
if (( was_voicestudio )) && voicestudio_has_established_clients; then
  echo "VoiceStudio has an established client; refusing GPU preemption." >&2
  exit 4
fi
if (( was_chatterbox )) && chatterbox_has_established_clients; then
  echo "Chatterbox VC has an established client; refusing media preemption." >&2
  exit 4
fi
if (( was_docling )) && docling_has_established_clients; then
  echo "Docling has an established client; refusing media preemption." >&2
  exit 4
fi
if systemctl is-active --quiet "$ROUTER"; then
  router_has_established_clients && { echo "Cloud9 LLM router has an established client/proxy connection; refusing GPU preemption." >&2; exit 4; }
  slot_busy http://127.0.0.1:18091/slots && { echo "Cloud9 LLM router worker is processing a request; refusing GPU preemption." >&2; exit 4; }
fi

# Close all socket-activation front doors first.
systemctl stop "${FRONT_SOCKETS[@]}" >/dev/null 2>&1 || true
systemctl stop "${FRONT_PROXIES[@]}" >/dev/null 2>&1 || true

# Router shutdown may restore embedding. Stop it FIRST and wait for it to be gone,
# then stop embedding. This ordering removes the old shutdown race.
systemctl stop "$ROUTER" >/dev/null 2>&1 || true
for _ in $(seq 1 80); do
  systemctl is-active --quiet "$ROUTER" || break
  sleep 0.25
done

systemctl stop "$LEMOND" >/dev/null 2>&1 || true
if (( STOP_LIGHT )); then
  systemctl stop "$EMBED" >/dev/null 2>&1 || true
  if (( was_speaches )); then docker stop --time 20 "$SPEACHES" >/dev/null 2>&1 || true; fi
fi
if (( was_voicestudio )); then docker stop --time 20 "$VOICESTUDIO" >/dev/null 2>&1 || true; fi
if (( was_chatterbox )); then docker stop --time 20 "$CHATTERBOX" >/dev/null 2>&1 || true; fi
if (( was_docling )); then docker stop --time 20 "$DOCLING" >/dev/null 2>&1 || true; fi

# Re-check user services after closing the front doors.
for u in "${USER_GPU_SERVICES[@]}"; do
  if systemctl is-active --quiet "$u"; then
    unit_pid=$(systemctl show -p MainPID --value "$u" 2>/dev/null || echo 0)
    [ "$unit_pid" = "$$" ] && continue
    echo "$u became active while acquiring exclusivity; refusing benchmark." >&2
    exit 4
  fi
done

gpu_users() {
  python3 - "$RENDER_DEV" <<'PYGPU'
import glob, os, sys
target = os.path.realpath(sys.argv[1])
seen = set()
for proc in glob.glob("/proc/[0-9]*"):
    pid = proc.rsplit("/", 1)[-1]
    for fd in glob.glob(proc + "/fd/*"):
        try:
            if os.path.realpath(fd) != target:
                continue
        except OSError:
            continue
        if pid in seen:
            break
        seen.add(pid)
        try:
            comm = open(proc + "/comm").read().strip()
        except Exception:
            comm = "?"
        try:
            cmd = open(proc + "/cmdline", "rb").read().replace(b"\x00", b" ").decode(errors="replace").strip()
        except Exception:
            cmd = ""
        print(f"{pid}\t{comm}\t{cmd}")
        break
PYGPU
}

blocked_gpu_users() {
  local speaches_id
  speaches_id=$(docker inspect -f '{{.Id}}' "$SPEACHES" 2>/dev/null || true)
  python3 - "$RENDER_DEV" "$speaches_id" <<'PYGPU'
import glob, os, sys
target = os.path.realpath(sys.argv[1])
speaches_id = sys.argv[2]
for proc in glob.glob("/proc/[0-9]*"):
    pid = proc.rsplit("/", 1)[-1]
    hit = False
    for fd in glob.glob(proc + "/fd/*"):
        try:
            if os.path.realpath(fd) == target:
                hit = True
                break
        except OSError:
            pass
    if not hit:
        continue
    try:
        cg = open(proc + "/cgroup").read()
    except Exception:
        cg = ""
    if "cloud9-embedding.service" in cg or (speaches_id and speaches_id in cg):
        continue
    try:
        cmd = open(proc + "/cmdline", "rb").read().replace(b"\x00", b" ").decode(errors="replace").strip()
    except Exception:
        cmd = ""
    print(f"{pid}\t{cmd}")
PYGPU
}

if (( STOP_LIGHT )); then
  for _ in $(seq 1 80); do
    users=$(gpu_users || true)
    [[ -z "$users" ]] && break
    sleep 0.25
  done
  users=$(gpu_users || true)
  if [[ -n "$users" ]]; then
    echo "GPU is still in use after managed services were stopped:" >&2
    printf '%s\n' "$users" >&2
    exit 4
  fi
  echo "Cloud9 GPU exclusive window acquired."
else
  for _ in $(seq 1 80); do
    blocked=$(blocked_gpu_users || true)
    [[ -z "$blocked" ]] && break
    sleep 0.25
  done
  blocked=$(blocked_gpu_users || true)
  if [[ -n "$blocked" ]]; then
    echo "coexist-light refused: an unclassified GPU user remains:" >&2
    printf '%s\n' "$blocked" >&2
    exit 4
  fi
  echo "Cloud9 GPU coexist-light window acquired; Embedding + Speaches remain online."
fi

"$@"
