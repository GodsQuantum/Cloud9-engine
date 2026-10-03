#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CTID=${CLOUD9_ENGINE_CTID:-410}
ENGINE_HOME=${CLOUD9_ENGINE_HOME:-/srv/lxc/ia-compute/data/cloud9-engine-runtime}
CATALOG_SRC=${CLOUD9_ENGINE_CATALOG_SOURCE:-$ROOT/config/model-catalog.json}
CATALOG_DST=${CLOUD9_ENGINE_CATALOG_DEST:-$ENGINE_HOME/model-catalog.json}

python3 -m json.tool "$CATALOG_SRC" >/dev/null

# The data tree is a host-owned bind mount into an unprivileged LXC.
# Update the catalog from the Proxmox host to avoid uid-map / inode replacement issues.
cp -f "$CATALOG_SRC" "$CATALOG_DST"
chmod 0664 "$CATALOG_DST"

# Install executable components inside CT410.
pct exec "$CTID" -- install -m 0755 "$ROOT/bin/cloud9-model-router.py" /usr/local/bin/cloud9-model-router
pct exec "$CTID" -- install -m 0755 "$ROOT/bin/cloud9-llama-server" /usr/local/bin/cloud9-llama-server

echo "Cloud9 router deployment complete:"
echo "  CT:      $CTID"
echo "  router:  /usr/local/bin/cloud9-model-router"
echo "  wrapper: /usr/local/bin/cloud9-llama-server"
echo "  catalog: $CATALOG_DST"
