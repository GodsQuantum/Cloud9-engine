#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ENGINE_HOME=${CLOUD9_ENGINE_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/cloud9-engine}
SRC="$ENGINE_HOME/src"; RELEASES="$ENGINE_HOME/releases"; CAND="$ENGINE_HOME/candidates"
mkdir -p "$SRC" "$RELEASES" "$CAND"
read_lock(){ python3 - "$ROOT/sources.lock" "$1" <<'PYLOCK'
import json,sys
j=json.load(open(sys.argv[1])); cur=j
for k in sys.argv[2].split('.'): cur=cur[k]
print(cur)
PYLOCK
}
UP_REPO=$(read_lock upstream.repository); UP_SHA=$(read_lock upstream.commit)
AT_REPO=$(read_lock atomic.repository); AT_SHA=$(read_lock atomic.commit)
clone_or_fetch(){ local repo=$1 dir=$2; if [[ ! -d "$dir/.git" ]]; then git clone --filter=blob:none "$repo" "$dir"; else git -C "$dir" fetch --all --tags --prune; fi; }
build_one(){ local src=$1 out=$2; cmake -S "$src" -B "$out" -DCMAKE_BUILD_TYPE=Release -DGGML_VULKAN=ON -DGGML_NATIVE=ON -DGGML_CCACHE=ON -DBUILD_SHARED_LIBS=ON -DLLAMA_CURL=OFF; cmake --build "$out" -j "${CLOUD9_ENGINE_JOBS:-$(nproc)}" --target llama-server llama-cli llama-bench; }
clone_or_fetch "$AT_REPO" "$SRC/atomic"
git -C "$SRC/atomic" reset --hard "$AT_SHA"; git -C "$SRC/atomic" clean -fdx
AT_SHORT=${AT_SHA:0:12}; AT_OUT="$RELEASES/atomic-$AT_SHORT"
[[ -x "$AT_OUT/bin/llama-server" ]] || build_one "$SRC/atomic" "$AT_OUT"
clone_or_fetch "$UP_REPO" "$SRC/upstream"
git -C "$SRC/upstream" am --abort >/dev/null 2>&1 || true
git -C "$SRC/upstream" reset --hard "$UP_SHA"; git -C "$SRC/upstream" clean -fdx
for patch in "$ROOT"/patches/upstream/*.patch; do git -C "$SRC/upstream" am "$patch"; done
UP_SHORT=${UP_SHA:0:12}; UP_OUT="$RELEASES/upstream-$UP_SHORT-cloud9"
[[ -x "$UP_OUT/bin/llama-server" ]] || build_one "$SRC/upstream" "$UP_OUT"
ln -sfn "$AT_OUT" "$CAND/atomic"; ln -sfn "$UP_OUT" "$CAND/upstream"
printf 'ATOMIC=%q\nUPSTREAM=%q\n' "$AT_OUT" "$UP_OUT" > "$ENGINE_HOME/candidates.env"
echo "Built candidates:"; echo "  atomic   $AT_OUT"; echo "  upstream $UP_OUT"; echo 'Run cloud9-engine gate MODEL to validate and promote.'
