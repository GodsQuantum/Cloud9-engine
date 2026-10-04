#!/usr/bin/env bash
set -Eeuo pipefail

gpu_items=()
for item in "$@"; do
  kind="${item%%:*}"
  name="${item#*:}"
  if [[ "$kind" == "systemd" && "$name" == *.socket ]]; then
    systemctl start "$name" >/dev/null 2>&1 || true
  else
    gpu_items+=("$item")
  fi
done

(("${#gpu_items[@]}" == 0)) && exit 0

exec 9>/run/cloud9-gpu.lock
flock -w 1800 9 || exit 0

for item in "${gpu_items[@]}"; do
  kind="${item%%:*}"
  name="${item#*:}"
  case "$kind" in
    docker)
      docker inspect "$name" >/dev/null 2>&1 || continue
      docker start "$name" >/dev/null 2>&1 || true
      ;;
    systemd)
      systemctl thaw "$name" >/dev/null 2>&1 || true
      systemctl start "$name" >/dev/null 2>&1 || true
      systemctl thaw "$name" >/dev/null 2>&1 || true
      ;;
  esac
done
