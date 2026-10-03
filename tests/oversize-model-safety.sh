#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
model="$tmp/oversize.gguf"
truncate -s 2097152 "$model"
set +e
out=$(CLOUD9_ENGINE_HOME="$tmp/engine" CLOUD9_ENGINE_MAX_MODEL_BYTES=1048576 \
  "$ROOT/bin/cloud9-llama-server" -m "$model" --version 2>&1)
rc=$?
set -e
[[ $rc -eq 4 ]] || { echo "expected rc=4, got $rc" >&2; exit 1; }
grep -q "refusing oversized model" <<<"$out"
echo "oversize model safety test: PASS"
