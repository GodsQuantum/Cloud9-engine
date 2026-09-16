# Safe updates

Cloud9 Engine uses two update layers.

## GitHub source watch

The scheduled `Source watch` workflow reads the `master` heads of llama.cpp and Atomic. If either moves, it updates `sources.lock` in `bot/source-sync` and opens a pull request. CI then attempts to apply the Cloud9 patchset to the new upstream and compile Vulkan targets.

If upstream changed an API touched by the patchset, CI fails and the PR stays visible for a deliberate rebase. Production is unaffected.

## Local hardware promotion

A server can enable the provided systemd user timer. `production-sync.sh` fast-forwards the Cloud9 Engine repo, builds the locked candidates and, only when `CLOUD9_ENGINE_GATE_MODEL` is configured, runs the local hardware gate before updating `current/*`.

This intentionally separates **automatic discovery/building** from **automatic production promotion**. A green generic CI build is not proof that a new Vulkan path is correct or faster on your RDNA GPU.

## Rollback

`current/atomic` and `current/upstream` are symlinks to versioned release directories. Rollback is therefore a symlink change, not a rebuild. Keep at least the last known-good pair until the replacement has handled real workloads successfully.
