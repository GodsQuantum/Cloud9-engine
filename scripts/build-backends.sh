#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ENGINE_HOME=${CLOUD9_ENGINE_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/cloud9-engine}
SRC="$ENGINE_HOME/src"; RELEASES="$ENGINE_HOME/releases"; CAND="$ENGINE_HOME/candidates"
mkdir -p "$SRC" "$RELEASES" "$CAND"
BUILD_LOCK="${CLOUD9_ENGINE_BUILD_LOCK:-$ENGINE_HOME/build-backends.lock}"
exec 9>"$BUILD_LOCK"
flock -n 9 || { echo "Another Cloud9 Engine backend build is already running." >&2; exit 4; }

REQUESTED=${CLOUD9_ENGINE_BUILD_BACKENDS:-atomic,upstream,prism}
want_backend() { [[ ",$REQUESTED," == *",$1,"* ]]; }

read_lock(){ python3 - "$ROOT/sources.lock" "$1" <<'PYLOCK'
import json,sys
j=json.load(open(sys.argv[1])); cur=j
for k in sys.argv[2].split('.'): cur=cur[k]
print(cur)
PYLOCK
}
UP_REPO=$(read_lock upstream.repository); UP_SHA=$(read_lock upstream.commit); UP_PATCHSET=$(read_lock patchset)
AT_REPO=$(read_lock atomic.repository); AT_SHA=$(read_lock atomic.commit)
PR_REPO=$(read_lock prism.repository); PR_SHA=$(read_lock prism.commit)

clone_or_fetch(){
  local repo=$1 dir=$2
  if [[ ! -d "$dir/.git" ]]; then
    [[ ${CLOUD9_ENGINE_OFFLINE:-0} == 1 ]] && { echo "Offline build requested but source clone is missing: $dir" >&2; exit 5; }
    git clone --filter=blob:none "$repo" "$dir"
  elif [[ ${CLOUD9_ENGINE_OFFLINE:-0} != 1 ]]; then
    git -C "$dir" fetch --all --tags --prune --force
  fi
}
build_one(){
  local src=$1 out=$2
  cmake -S "$src" -B "$out" -DCMAKE_BUILD_TYPE=Release -DGGML_VULKAN=ON -DGGML_NATIVE=ON -DGGML_CCACHE=ON -DBUILD_SHARED_LIBS=ON -DLLAMA_CURL=OFF -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF
  cmake --build "$out" -j "${CLOUD9_ENGINE_JOBS:-$(nproc)}" --target llama-server llama-cli llama-bench
}

AT_SHORT=${AT_SHA:0:12}; AT_OUT="$RELEASES/atomic-$AT_SHORT"
UP_SHORT=${UP_SHA:0:12}; UP_OUT="$RELEASES/upstream-$UP_SHORT-cloud9"
PR_SHORT=${PR_SHA:0:12}; PR_OUT="$RELEASES/prism-$PR_SHORT"

if want_backend atomic; then
  clone_or_fetch "$AT_REPO" "$SRC/atomic"
  git -C "$SRC/atomic" reset --hard "$AT_SHA"; git -C "$SRC/atomic" clean -fdx
  [[ -x "$AT_OUT/bin/llama-server" ]] || build_one "$SRC/atomic" "$AT_OUT"
  ln -sfn "$AT_OUT" "$CAND/atomic"
fi

if want_backend upstream; then
  clone_or_fetch "$UP_REPO" "$SRC/upstream"
  git -C "$SRC/upstream" am --abort >/dev/null 2>&1 || true
  git -C "$SRC/upstream" reset --hard "$UP_SHA"; git -C "$SRC/upstream" clean -fdx
  "$ROOT/scripts/apply-upstream-patches.sh" "$SRC/upstream" "$ROOT/$UP_PATCHSET"
  [[ -x "$UP_OUT/bin/llama-server" ]] || build_one "$SRC/upstream" "$UP_OUT"
  ln -sfn "$UP_OUT" "$CAND/upstream"
fi

if want_backend prism; then
  clone_or_fetch "$PR_REPO" "$SRC/prism"
  git -C "$SRC/prism" reset --hard "$PR_SHA"; git -C "$SRC/prism" clean -fdx
  [[ -x "$PR_OUT/bin/llama-server" ]] || build_one "$SRC/prism" "$PR_OUT"
  ln -sfn "$PR_OUT" "$CAND/prism"
fi

resolve_cand(){
  local name=$1 fallback=$2
  readlink -f "$CAND/$name" 2>/dev/null || readlink -f "$ENGINE_HOME/current/$fallback" 2>/dev/null || true
}
AT_CAND=$(resolve_cand atomic atomic)
UP_CAND=$(resolve_cand upstream upstream)
PR_CAND=$(resolve_cand prism prism)
printf 'ATOMIC=%q\nUPSTREAM=%q\nPRISM=%q\n' "$AT_CAND" "$UP_CAND" "$PR_CAND" > "$ENGINE_HOME/candidates.env"

echo "Candidate set:"
echo "  atomic   ${AT_CAND:-unavailable}"
echo "  upstream ${UP_CAND:-unavailable}"
echo "  prism    ${PR_CAND:-unavailable}"
echo "Requested build backends: $REQUESTED"
