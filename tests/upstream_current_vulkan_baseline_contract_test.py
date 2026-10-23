#!/usr/bin/env python3
import json,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class LatestUpstreamVulkan(unittest.TestCase):
 def test_current_source_and_isolation(self):
  s=(R/'.github/workflows/lab-latest-upstream-masterf502-vulkan.yml').read_text()
  pin=json.loads((R/'tools/benchmarks/latest_engine_sources_20261023.json').read_text())['github_repositories']['upstream']
  self.assertEqual(pin['commit'],'f5027fb21307eb264aed483242603d68c87b0fe3')
  self.assertEqual(json.loads((R/'tools/benchmarks/latest_engine_sources_20261023.json').read_text())['lab_candidate_binary_sha256']['upstream-master-4b'], '9ac70a0399d0e0375dd4a68a4c5d835f5bdda9b4589ff8156fabd1d025ecc39c')
  for required in ('upstream-master-4b','-DGGML_VULKAN=ON','latest-upstream-masterf502-vulkan','NOT_GPU_QUALIFIED.txt','git ls-remote','sha256sum'):
   self.assertIn(required,s)
  self.assertNotIn('rdna-r114',s)
if __name__=='__main__':unittest.main(verbosity=2)
