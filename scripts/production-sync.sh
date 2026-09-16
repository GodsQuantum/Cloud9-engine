#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
git fetch origin main --quiet
git merge --ff-only origin/main
"$ROOT/scripts/build-backends.sh"
if [[ -n "${CLOUD9_ENGINE_GATE_MODEL:-}" ]]; then
  "$ROOT/scripts/hardware-gate.sh" "$CLOUD9_ENGINE_GATE_MODEL"
else
  echo 'Built candidates only; CLOUD9_ENGINE_GATE_MODEL is unset, so production was not promoted.'
fi
