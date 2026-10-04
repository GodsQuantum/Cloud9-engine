#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CTID=${CLOUD9_ENGINE_CTID:-410}
ENGINE_HOME=${CLOUD9_ENGINE_HOME:-/srv/lxc/ia-compute/data/cloud9-engine-runtime}
CATALOG_SRC=${CLOUD9_ENGINE_CATALOG_SOURCE:-$ROOT/config/model-catalog.json}
CATALOG_DST=${CLOUD9_ENGINE_CATALOG_DEST:-$ENGINE_HOME/model-catalog.json}

python3 -m json.tool "$CATALOG_SRC" >/dev/null

# Data tree is a host-owned bind mount into the unprivileged LXC.
cp -f "$CATALOG_SRC" "$CATALOG_DST"
chmod 0664 "$CATALOG_DST"

# Canonical sources live on the Proxmox host and are not mounted at the same
# path inside CT410. Use pct push rather than an in-container install from $ROOT.
pct push "$CTID" "$ROOT/bin/cloud9-model-router.py" /usr/local/bin/cloud9-model-router --perms 0755 --user root --group root
pct push "$CTID" "$ROOT/bin/cloud9-llama-server" /usr/local/bin/cloud9-llama-server --perms 0755 --user root --group root
pct push "$CTID" "$ROOT/scripts/exclusive-gpu-run.sh" /usr/local/sbin/cloud9-exclusive-gpu-run --perms 0755 --user root --group root
pct push "$CTID" "$ROOT/scripts/gpu-second-chance-restore.sh" /usr/local/sbin/cloud9-gpu-second-chance-restore --perms 0755 --user root --group root

pct exec "$CTID" -- mkdir -p /etc/systemd/system/autopublisher-image.service.d /etc/systemd/system/comfyui.service.d
pct push "$CTID" "$ROOT/systemd/autopublisher-image.service.d/20-gpu-arbiter.conf" /etc/systemd/system/autopublisher-image.service.d/20-gpu-arbiter.conf --perms 0644 --user root --group root
pct push "$CTID" "$ROOT/systemd/comfyui.service.d/40-memory-safety.conf" /etc/systemd/system/comfyui.service.d/40-memory-safety.conf --perms 0644 --user root --group root
pct exec "$CTID" -- systemctl daemon-reload

echo "Cloud9 router/GPU arbitration deployment complete:"
echo "  CT:       $CTID"
echo "  router:   /usr/local/bin/cloud9-model-router"
echo "  wrapper:  /usr/local/bin/cloud9-llama-server"
echo "  arbiter:  /usr/local/sbin/cloud9-exclusive-gpu-run"
echo "  restore:  /usr/local/sbin/cloud9-gpu-second-chance-restore"
echo "  catalog:  $CATALOG_DST"
echo "  images:   coexist-light (Embedding + Cloud9-Speaches stay online)"
