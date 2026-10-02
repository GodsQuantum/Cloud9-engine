# Safe updates

Cloud9 Engine uses three layers: **source discovery**, **CI compatibility**, and **local hardware/model promotion**.

## GitHub source watch

The scheduled source watch tracks llama.cpp upstream, Atomic TurboQuant and Prism. A source change updates the proposed `sources.lock` only after the declared Cloud9 patchset still applies. CI then verifies patch compatibility and Vulkan builds.

A source change is therefore information, not an instruction to replace production.

## Local candidates

`cloud9-engine build` creates versioned candidate releases. A build lock prevents two backend builds from compiling into the same release directory concurrently.

Known-good `current/*` links remain untouched during candidate construction.

## Hardware and model-family promotion

A local gate must load a real model and complete repeated inference before a runtime can be promoted. The gate refuses to run while another process owns the render device. It also treats a failed reference run as a hard stop rather than comparing against stale benchmark JSON.

Production may intentionally retain multiple upstream releases at once because a new llama.cpp revision can improve one architecture while regressing another. The model catalog records which validated runtime wins for each production model.

## Rollback

Runtime links point to immutable versioned release directories. Rollback is therefore a symlink change, not a rebuild. Keep each release that is still referenced by the production model catalog; remove only superseded, unreferenced builds.

## Atomic and Prism

Atomic is laboratory-only on the reference Radeon 780M after Atomic 1.7 reproduced Vulkan allocation/device-loss failures on 2026-10-02. Prism is promoted only for ternary/PTQ models that require it and is benchmarked independently from upstream llama.cpp.
