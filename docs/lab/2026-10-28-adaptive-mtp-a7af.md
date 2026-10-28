# Cloud9 native adaptive MTP — Vulkan and source candidate

**Source pin:** `ggml-org/llama.cpp` master `a7af149a2a7768d4b1f6f02c6ce26a17fba11376` (verified live 28 Oct 2026 ~10:00 Paris; re-verify before any GPU A/B).

**Donor:** `stew675/llama-cpp-rdna-boosts` v15-6050b467c-r158, annotated release tag deref `9db917203e7afe4aeb34c06e377f5fa69ec0db9d`, MIT license (verify before publish), adaptive MTP controller and tests in block 02. This is a *selective source port* to a newer upstream, not all 15 RDNA patches applied to old base6050b467c.

**Feature:** `CLOUD9_MTP_ADAPTIVE=1` enables an MTP draft-depth controller using target accept feedback for **single-sequence contexts only**. The implementation fails closed for parallel `n_seq > 1` until the donor verifier-batch alignment optimization can be selectively ported and independently validated. Max-depth initial value ensures unchanged first few tokens in Pym MTP2/Flash-Next MTP3; controller moves down after failed accept and up after sustained success. Without exact opt-in, fixed MTP draft behavior and model/quality paths remain upstream. No GPU shaders or production router touched. Existing RDNA controller tests plus Cloud9 Pym/FlashNext profile randomized ASAN/UBSAN tests included.

**Source QA:** original donor `tests/test-speculative-adaptive.cpp` GCC ASAN/UBSAN PASS; Cloud9 standalone 500,000 deterministic randomized acceptance rounds ASAN/UBSan PASS; static integration anchors 10/10. CMake configured for Vulkan ON, Release, tests ON, native CPU flags OFF. Full latest upstream Vulkan baseline compile PASS, CPU quant test PASS. Patched Vulkan build (CLI, benchmark, server, CTest, backend ops) PASS; original donor controller CTest 1/1 PASS, plus ASAN+UBSAN unit and 500000 randomized Cloud9 rounds PASS. Candidate native source git `c33f400880a13fdd414e83bccbd61815813a20a5` and CLI SHA-256 `3ec8352c7ab1400083431863a43923abd4a5e122030d0503318da464fab55431`. These results certify CPU/source builds only, not hardware acceleration correctness or gain.

**Hardware gate:** GPU lab remains blocked due previous AMD driver hang. No speedups claimed. CT410 original Atomic1.6 unchanged. Prior comparable HOF Pym Q2 MTP2 historical max 37.20t/s, Flash-Next AD-4.27 17.878t/s, different GGUF/models and protocols. Only same model+quant+prompt+length and safety-admitted Radeon780M real A/B can qualify a promotion.

**Apply / rollback (laboratory only):** `git checkout a7af149a2a7768d4b1f6f02c6ce26a17fba11376` then `git am patches/lab-a7af/0001-cloud9-native-adaptive-MTP-r158-a7af.patch`; rollback `git reset --hard a7af149` in a disposable clone **only**, never production or a dirty worktree. Avoid applying to any newer master without rebase/revalidation.

**Deployment:** NOT PROMOTED. No model build/hardware tests performed yet.
