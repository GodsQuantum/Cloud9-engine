# Cloud9 Native NextN Vulkan CI and CT410 Inactive LAB Staging - 25 Oct 2026

## Exact build evidence
- Source base llama.cpp 9ae73e68f; chimera combined source with five-line NextN scheduler re-reserve revert, Git tree d122b09e38c4e5397601c1ade0c3c6cc3aea39cc. EXPERIMENTAL: may cause graph allocation hazards, must not be promoted.
- GitHub Actions run 40144538324 SUCCESS; source SHA validation, Vulkan compile, native speculative-adaptive and fail-closed turbo unit tests PASS. Artifacts uploaded.
- Immutable original tar.gz sha256 7c52d34ddfdd735139d60fc4db577ad7fa028129232f79d4465b779fa28fc6c0, 12/12 archive real-file sha checks passed.
- GitHub runner absolute RUNPATH made initial ELF loader fail; corrected ALL 12 REAL ELF files in a copied candidate using native patchelf --set-rpath $ORIGIN. Preserved original tar/manifest. New SHA256SUMS_RELOCATED SHA256 97ab4aff7f6edcad84ebf592b3db65a7ba55eef81ea7d3921d2ce8a92b802b03
- CT410 staged exclusively in lab-releases/chimera-master9ae-nextn-revert-vulkan-20261025. No live symlink, model route, or default combo changed.
- Inactive native llama-server executable SHA256 25e2d4560ecceeda57a9c6fa88bfd8b440c46f5bac5dfc71204002a1f798ed63.
- CT410 host checks PASS: loader --version and ldd no missing libraries, native MTP adaptive tests, TurboQuant GPU backend fail-closed 20/20, quant functions normal exit.

## Proof boundaries and next experiments
- This certifies source reproduction, compiler and binary ABI only; real 2K/8K/16K GPU inference on the NextN reverted candidate was NOT performed.
- At 02:07 host ZRAM swap was 19.184/19.519GiB = 98.28%, PSI sometimes above GPU guardian admission threshold. Never force GPU loads under this resource state.
- Existing native five-needle LAB runner supports exact server selection baseline|nextn-revert with pinned binary SHA; cache K=f16 or q8_0, V=f16 or turbo3, batch=256 or 512, and distinct immutable proof names.
- On safe admission, run same GGUF, same context, same seed and same quant config to compare baseline and NextN reverted; validate no scheduler realloc crashes, markers 5/5 and repeatable improvement.
- Historical Atomic2 same-Qwen4 8K median decode 35.21tok/s K q8_0 V turbo3 batch512 is NOT directly comparable with current chimera f16 KV 8K 8.0-8.6tok/s.
- No reboot, swapoff, host cache purge, PBS stop or production engine restart. PBS daily schedule remains enabled at 00:30.

## Continuation
- Read certification/CURRENT_STATUS.md and this worklog, then confirm resource headroom. Source code and binary are already assembled: do not compile them again without a meaningful source change.
- C08 8K two of three passes, C09 one of 36, C12 source/compiler PARTIAL. All release gates still unclosed.
