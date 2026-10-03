#!/usr/bin/env bash
set -Eeuo pipefail

[[ $# -gt 0 ]] || { echo "Usage: $0 COMMAND [ARG...]" >&2; exit 2; }

# This MUST be the same lock used by cloud9-model-router.
LOCK_FILE=${CLOUD9_GPU_LOCK:-/run/cloud9-gpu.lock}
RENDER_DEV=${CLOUD9_ENGINE_RENDER_DEVICE:-/dev/dri/renderD128}
ROUTER_SOCKET=cloud9-engine-router-proxy.socket
ROUTER_PROXY=cloud9-engine-router-proxy.service
ROUTER=cloud9-engine-router.service
EMBED=cloud9-embedding.service
LEMOND=lemond.service
SPEACHES=speaches
VOICESTUDIO=voicestudio
FRONT_SOCKETS=(comfyui-proxy.socket autopublisher-image-proxy.socket)
FRONT_PROXIES=(comfyui-proxy.service autopublisher-image-proxy.service)
USER_GPU_SERVICES=(comfyui.service autopublisher-image.service)

exec 9>"$LOCK_FILE"
flock -n 9 || { echo "Cloud9 GPU is already reserved by another engine/request ($LOCK_FILE)." >&2; exit 4; }

declare -a RESTORE_SOCKETS=()
declare -a RESTORE_SERVICES=()
was_router_socket=0
was_speaches=0
was_voicestudio=0

systemctl is-active --quiet "$ROUTER_SOCKET" && was_router_socket=1 || true
docker inspect -f '{{.State.Running}}' "$SPEACHES" 2>/dev/null | grep -qx true && was_speaches=1 || true
docker inspect -f '{{.State.Running}}' "$VOICESTUDIO" 2>/dev/null | grep -qx true && was_voicestudio=1 || true
for u in "$EMBED" "$LEMOND"; do
  systemctl is-active --quiet "$u" && RESTORE_SERVICES+=("$u")
done
for u in "${FRONT_SOCKETS[@]}"; do
  systemctl is-active --quiet "$u" && RESTORE_SOCKETS+=("$u")
done

restore_units() {
  local rc=$?
  trap - EXIT INT TERM
  if (( was_speaches )); then docker start "$SPEACHES" >/dev/null 2>&1 || true; fi
  if (( was_voicestudio )); then docker start "$VOICESTUDIO" >/dev/null 2>&1 || true; fi
  for u in "${RESTORE_SERVICES[@]}"; do
    systemctl thaw "$u" >/dev/null 2>&1 || true
    systemctl start "$u" >/dev/null 2>&1 || true
    systemctl thaw "$u" >/dev/null 2>&1 || true
  done
  if (( was_router_socket )); then systemctl start "$ROUTER_SOCKET" >/dev/null 2>&1 || true; fi
  for u in "${RESTORE_SOCKETS[@]}"; do systemctl start "$u" >/dev/null 2>&1 || true; done
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

# Never interrupt a user-visible GPU workload.
for u in "${USER_GPU_SERVICES[@]}"; do
  if systemctl is-active --quiet "$u"; then
    unit_pid=$(systemctl show -p MainPID --value "$u" 2>/dev/null || echo 0)
    [ "$unit_pid" = "$$" ] && continue
    echo "$u is active; refusing to interrupt an image job." >&2
    exit 4
  fi
done
if systemctl is-active --quiet "$EMBED" && slot_busy http://127.0.0.1:8091/slots; then
  echo "Embedding Engine is processing a request; refusing GPU preemption." >&2
  exit 4
fi
if (( was_speaches )) && speaches_has_established_clients; then
  echo "Speaches has an established transcription client; refusing GPU preemption." >&2
  exit 4
fi
if (( was_voicestudio )) && voicestudio_has_established_clients; then
  echo "VoiceStudio has an established client; refusing GPU preemption." >&2
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
systemctl stop "$ROUTER_SOCKET" "$ROUTER_PROXY" >/dev/null 2>&1 || true
systemctl stop "$ROUTER" >/dev/null 2>&1 || true
for _ in $(seq 1 80); do
  systemctl is-active --quiet "$ROUTER" || break
  sleep 0.25
done

systemctl stop "$EMBED" "$LEMOND" >/dev/null 2>&1 || true
if (( was_speaches )); then docker stop --time 20 "$SPEACHES" >/dev/null 2>&1 || true; fi
if (( was_voicestudio )); then docker stop --time 20 "$VOICESTUDIO" >/dev/null 2>&1 || true; fi

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
"$@"
