#include "speculative-adaptive.h"
#undef NDEBUG
#include <cassert>
#include <cstdio>
#include <cstdint>
#include <algorithm>

static void test_profile(int ceiling, int floor) {
  common_speculative_adaptive ctrl;
  // Cloud9 opts into max-depth startup to preserve existing MTP2/MTP3 throughput before feedback.
  ctrl.reset(ceiling, floor, ceiling);
  assert(ctrl.n_cur == ceiling);
  for (int i = 0; i < 1000; ++i) {
    ctrl.update(0, ceiling, floor); // bad/novel content, no drafts accepted
    assert(ctrl.n_cur >= floor && ctrl.n_cur <= ceiling);
    assert(ctrl.n_bucket >= 0);
  }
  assert(ctrl.n_cur == floor);
  for (int i = 0; i < 3000; ++i) {
    ctrl.update(ctrl.n_cur, ceiling, floor); // exact repeated / high-acceptance text
    assert(ctrl.n_cur >= floor && ctrl.n_cur <= ceiling);
    assert(ctrl.n_bucket >= 0);
  }
  assert(ctrl.n_cur == ceiling);
  ctrl.reset(ceiling, floor, ceiling);
  assert(ctrl.n_cur == ceiling);
}

int main() {
  test_profile(2, 1); // exact Pym MTP2 profile
  test_profile(3, 1); // Flash-Next MTP3 profile
  test_profile(8, 1); // potential long draft with nonchain layers
  test_profile(12, 3); // RDNA r158 larger speculative range
  common_speculative_adaptive seq0,seq1;
  seq0.reset(3,1,3);seq1.reset(3,1,3);
  for(int i=0;i<200;++i) {seq0.update(0,3,1);seq1.update(seq1.n_cur,3,1);}
  assert(seq0.n_cur==1 && seq1.n_cur==3);
  uint32_t seed=0x534c4c4d;
  common_speculative_adaptive fuzz;
  for (int ceiling : {2,3,4,8,12}) {
    fuzz.reset(ceiling,1,ceiling);
    for(int i=0;i<100000;++i){
      seed=1664525U*seed+1013904223U;
      int accepted=int(seed%unsigned(fuzz.n_cur+1));
      fuzz.update(accepted,ceiling,1);
      assert(fuzz.n_cur>=1 && fuzz.n_cur<=ceiling);
      assert(fuzz.n_bucket>=0 && fuzz.n_bucket<=fuzz.bucket_cap());
    }
  }
  std::puts("PASS: profiles MTP2, MTP3, MTP8, MTP12, two independent sequences; 500000 deterministic acceptance fuzz rounds under ASAN+UBSAN");
}
