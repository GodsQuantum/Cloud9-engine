#!/usr/bin/env bash
set -Eeuo pipefail

CTID=${CLOUD9_ENGINE_CTID:-410}
target=${1:-}
case "$target" in
  whittle|gyro) ;;
  *) echo "Usage: $0 {whittle|gyro}" >&2; exit 64 ;;
esac

MAX_TCTL=${CLOUD9_FETCH_MAX_TCTL:-72}
MAX_LOAD1=${CLOUD9_FETCH_MAX_LOAD1:-8}
MAX_IO_FULL=${CLOUD9_FETCH_MAX_IO_FULL:-2.0}

tctl=$(sensors 2>/dev/null | awk '/Tctl:/ {gsub(/[+°C]/,"",$2); print int($2); exit}')
load1=$(awk '{print $1}' /proc/loadavg)
iofull=$(awk '/^full /{for(i=1;i<=NF;i++) if($i ~ /^avg10=/){split($i,a,"="); print a[2]}}' /proc/pressure/io)
[[ -n "$tctl" ]] || tctl=999
[[ -n "$iofull" ]] || iofull=999
awk -v x="$load1" -v m="$MAX_LOAD1" 'BEGIN{exit !(x<=m)}' || { echo "REFUSE: load1=$load1 > $MAX_LOAD1" >&2; exit 4; }
(( tctl < MAX_TCTL )) || { echo "REFUSE: Tctl=${tctl}C >= ${MAX_TCTL}C" >&2; exit 4; }
awk -v x="$iofull" -v m="$MAX_IO_FULL" 'BEGIN{exit !(x<=m)}' || { echo "REFUSE: io full avg10=$iofull > $MAX_IO_FULL" >&2; exit 4; }
pgrep -af 'proxmox-backup-client backup' >/dev/null && { echo "REFUSE: active PBS backup" >&2; exit 4; }

if [[ "$target" == whittle ]]; then
  hf_repo='logic65/Whittle-Qwen-3.8-35B-A3B-GGUF'
  file='Whittle-Qwen-3.8-35B-A3B-Q4_K_M.gguf'
  dest='/srv/lxc/ia-compute/data/models/bakeoff-20261005/whittle-q38-35b-a3b-q4'
  size=21281827744
  sha='a9c3669333d54de6932f1c793d5d163bbb138c216228322af0b9a2dccc39c42e'
else
  hf_repo='agentionai/Qwen3.8-Flash-Next-Gyro-GGUF'
  file='Qwen3.8-Flash-Next-Gyro-S-TQ1_0.gguf'
  dest='/srv/lxc/ia-compute/data/models/bakeoff-20261005/flashnext-gyro'
  size=58487015808
  sha='250a778eaa818b85a8165d0f35fe3360608456e952cb574b0cd0a15b5efee098'
fi

url="https://huggingface.co/$hf_repo/resolve/main/$file?download=true"
echo "Cloud9 challenger fetch: $hf_repo / $file"
echo "Expected bytes=$size sha256=$sha"

pct exec "$CTID" -- bash -lc "
set -Eeuo pipefail
mkdir -p '$dest'
part='$dest/$file.part'
final='$dest/$file'
if [[ -f \"\$final\" ]]; then
  got_size=\$(stat -c %s \"\$final\")
  if [[ \"\$got_size\" == '$size' ]] && echo '$sha  '\"\$final\" | sha256sum -c -; then
    echo 'already verified'
    exit 0
  fi
  echo 'existing final file failed verification; refusing to overwrite automatically' >&2
  exit 5
fi
curl -fL --retry 8 --retry-delay 5 --retry-all-errors -C - -o \"\$part\" '$url'
got_size=\$(stat -c %s \"\$part\")
[[ \"\$got_size\" == '$size' ]] || { echo \"size mismatch: \$got_size != $size\" >&2; exit 6; }
echo '$sha  '\"\$part\" | sha256sum -c -
mv \"\$part\" \"\$final\"
sync -f \"\$final\" 2>/dev/null || true
echo 'VERIFIED:' \"\$final\"
"
