#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PREFIX=${CLOUD9_ENGINE_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/cloud9-engine}
BINDIR=${CLOUD9_ENGINE_BINDIR:-$HOME/.local/bin}
mkdir -p "$PREFIX" "$BINDIR"
ln -sfn "$ROOT/bin/cloud9-engine" "$BINDIR/cloud9-engine"
ln -sfn "$ROOT/bin/cloud9-llama-server" "$BINDIR/cloud9-llama-server"
[[ -f "$PREFIX/config.env" ]] || cp "$ROOT/config/cloud9-engine.env.example" "$PREFIX/config.env"
echo "Installed command links in $BINDIR"
echo 'Next: cloud9-engine doctor && cloud9-engine build'
