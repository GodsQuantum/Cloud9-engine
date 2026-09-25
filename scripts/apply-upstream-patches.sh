#!/usr/bin/env bash
set -euo pipefail

repo=${1:?repository path required}
patch_dir=${2:?patch directory required}

git -C "$repo" am --abort >/dev/null 2>&1 || true

for patch in "$patch_dir"/*.patch; do
  if git -C "$repo" am "$patch"; then
    continue
  fi

  git -C "$repo" am --abort >/dev/null 2>&1 || true
  echo "Strict patch application failed for $(basename "$patch"); retrying with 3-way merge."

  if git -C "$repo" am --3way "$patch"; then
    continue
  fi

  git -C "$repo" am --abort >/dev/null 2>&1 || true
  echo "Patch $(basename "$patch") is incompatible even with 3-way merge." >&2
  exit 1
done
