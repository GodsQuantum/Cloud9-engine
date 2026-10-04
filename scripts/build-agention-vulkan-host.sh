#!/usr/bin/env bash
set -Eeuo pipefail

CTID=${CLOUD9_ENGINE_CTID:-410}
SHA=${AGENTION_LLAMA_SHA:-03eb38248b10a8a629603e698d3f3f1cdab7953e}
SHORT=${SHA:0:9}
REPO=/srv/lxc/ia-compute/data/repos/agention-llama.cpp
RUNTIME=/srv/lxc/ia-compute/data/cloud9-engine-runtime/releases/agention-main-${SHORT}-vulkan

MAX_TCTL=${CLOUD9_BUILD_MAX_TCTL:-72}
MAX_LOAD1=${CLOUD9_BUILD_MAX_LOAD1:-8}
MAX_IO_FULL=${CLOUD9_BUILD_MAX_IO_FULL:-2.0}

tctl=$(sensors 2>/dev/null | awk '/Tctl:/ {gsub(/[+°C]/,"",$2); print int($2); exit}')
load1=$(awk '{print $1}' /proc/loadavg)
iofull=$(awk '/^full /{for(i=1;i<=NF;i++) if($i ~ /^avg10=/){split($i,a,"="); print a[2]}}' /proc/pressure/io)
[[ -n "$tctl" ]] || tctl=999
[[ -n "$iofull" ]] || iofull=999
awk -v x="$load1" -v m="$MAX_LOAD1" 'BEGIN{exit !(x<=m)}' || { echo "REFUSE: load1=$load1 > $MAX_LOAD1" >&2; exit 4; }
(( tctl < MAX_TCTL )) || { echo "REFUSE: Tctl=${tctl}C >= ${MAX_TCTL}C" >&2; exit 4; }
awk -v x="$iofull" -v m="$MAX_IO_FULL" 'BEGIN{exit !(x<=m)}' || { echo "REFUSE: io full avg10=$iofull > $MAX_IO_FULL" >&2; exit 4; }
pgrep -af 'proxmox-backup-client backup' >/dev/null && { echo "REFUSE: active PBS backup" >&2; exit 4; }

pct exec "$CTID" -- bash -lc "
set -Eeuo pipefail
if [[ ! -d '$REPO/.git' ]]; then
  git clone --filter=blob:none https://github.com/agentionai/llama.cpp.git '$REPO'
fi
git -C '$REPO' fetch --filter=blob:none origin '$SHA'
git -C '$REPO' checkout --detach '$SHA'
test \"\$(git -C '$REPO' rev-parse HEAD)\" = '$SHA'
rm -rf '$RUNTIME'
cmake -S '$REPO' -B '$RUNTIME' -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_VULKAN=ON \
  -DGGML_NATIVE=ON \
  -DLLAMA_BUILD_TESTS=OFF
cmake --build '$RUNTIME' --target llama-server llama-cli llama-bench -j8
'$RUNTIME/bin/llama-server' --version
'$RUNTIME/bin/llama-bench' --list-devices
echo '$SHA' > '$RUNTIME/CLOUD9_SOURCE_SHA'
"
echo "Agention Vulkan candidate built at $RUNTIME"
