#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ENGINE_HOME=${CLOUD9_ENGINE_HOME:-/srv/lxc/ia-compute/data/cloud9-engine-runtime}
ROUTER_BINDIR=${CLOUD9_ENGINE_ROUTER_BINDIR:-/usr/local/bin}
CATALOG_SRC=${CLOUD9_ENGINE_CATALOG_SOURCE:-$ROOT/config/model-catalog.json}
CATALOG_DST=${CLOUD9_ENGINE_CATALOG_DEST:-$ENGINE_HOME/model-catalog.json}
CATALOG_USER=${CLOUD9_ENGINE_CATALOG_USER:-arezki}

python3 -m json.tool "$CATALOG_SRC" >/dev/null
install -m 0755 "$ROOT/bin/cloud9-model-router.py" "$ROUTER_BINDIR/cloud9-model-router"
install -m 0755 "$ROOT/bin/cloud9-llama-server" "$ROUTER_BINDIR/cloud9-llama-server"

if [[ -w "$CATALOG_DST" || ( ! -e "$CATALOG_DST" && -w "$(dirname "$CATALOG_DST")" ) ]]; then
  cat "$CATALOG_SRC" > "$CATALOG_DST"
elif id "$CATALOG_USER" >/dev/null 2>&1; then
  cat "$CATALOG_SRC" | runuser -u "$CATALOG_USER" -- tee "$CATALOG_DST" >/dev/null
else
  echo "Cannot update $CATALOG_DST: not writable and user $CATALOG_USER is unavailable." >&2
  exit 4
fi

echo "Cloud9 model router deployed:"
echo "  router:  $ROUTER_BINDIR/cloud9-model-router"
echo "  wrapper: $ROUTER_BINDIR/cloud9-llama-server"
echo "  catalog: $CATALOG_DST"
