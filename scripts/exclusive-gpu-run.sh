#!/usr/bin/env bash
set -Eeuo pipefail

[[ $# -gt 0 ]] || { echo "Usage: $0 COMMAND [ARG...]" >&2; exit 2; }

LOCK_FILE=${CLOUD9_GPU_LOCK:-/run/cloud9-gpu-exclusive.lock}
RENDER_DEV=${CLOUD9_ENGINE_RENDER_DEVICE:-/dev/dri/renderD128}
FRONT_SOCKETS=(comfyui-proxy.socket autopublisher-image-proxy.socket)
FRONT_PROXIES=(comfyui-proxy.service autopublisher-image-proxy.service)
USER_GPU_SERVICES=(comfyui.service autopublisher-image.service)
MANAGED_SERVICES=(cloud9-engine-router.service cloud9-embedding.service lemond.service)
MANAGED_CONTAINERS=(speaches)

exec 9>"$LOCK_FILE"
flock -n 9 || { echo "Another exclusive GPU job already holds $LOCK_FILE" >&2; exit 4; }

for u in "${USER_GPU_SERVICES[@]}"; do
  if systemctl is-active --quiet "$u"; then
    echo "$u is active; refusing to interrupt an image job." >&2
    exit 4
  fi
done

declare -a RESTORE_SOCKETS=()
declare -a RESTORE_SERVICES=()
declare -a RESTORE_CONTAINERS=()
for c in "${MANAGED_CONTAINERS[@]}"; do
  docker ps --format '{{.Names}}' 2>/dev/null | grep -Fxq "$c" && RESTORE_CONTAINERS+=("$c")
done
for u in "${FRONT_SOCKETS[@]}"; do
  systemctl is-active --quiet "$u" && RESTORE_SOCKETS+=("$u")
done
for u in "${MANAGED_SERVICES[@]}"; do
  systemctl is-active --quiet "$u" && RESTORE_SERVICES+=("$u")
done
restore_units() {
  local rc=$?
  trap - EXIT INT TERM
  for c in "${RESTORE_CONTAINERS[@]}"; do
    docker start "$c" >/dev/null 2>&1 || true
  done
  for u in "${RESTORE_SERVICES[@]}"; do
    systemctl start "$u" || true
  done
  for u in "${RESTORE_SOCKETS[@]}"; do
    systemctl start "$u" || true
  done
  exit "$rc"
}
trap restore_units EXIT INT TERM

# Close socket-activation front doors first so no new image workload can race us.
systemctl stop "${FRONT_SOCKETS[@]}" 2>/dev/null || true
systemctl stop "${FRONT_PROXIES[@]}" 2>/dev/null || true

for u in "${USER_GPU_SERVICES[@]}"; do
  if systemctl is-active --quiet "$u"; then
    echo "$u became active while acquiring exclusivity; refusing benchmark." >&2
    exit 4
  fi
done

# Stop ordinary inference residents; their original active state is restored on exit.
systemctl stop "${MANAGED_SERVICES[@]}" 2>/dev/null || true
for c in "${RESTORE_CONTAINERS[@]}"; do
  docker stop -t 20 "$c" >/dev/null 2>&1 || true
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

users=$(gpu_users || true)
if [[ -n "$users" ]]; then
  echo "GPU is still in use after managed services were stopped:" >&2
  printf '%s\n' "$users" >&2
  exit 4
fi

echo "Cloud9 GPU exclusive window acquired."
"$@"
