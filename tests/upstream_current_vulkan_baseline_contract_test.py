#!/usr/bin/env python3
import json,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class LatestUpstreamVulkan(unittest.TestCase):
 def test_current_source_and_isolation(self):
  s=(R/'.github/workflows/lab-latest-upstream-master062-vulkan.yml').read_text()
  pin=json.loads((R/'tools/benchmarks/latest_engine_sources_20261023.json').read_text())['github_repositories']['upstream']
  self.assertEqual(pin['commit'],'06230cb8775899cceef146c19cd447a947ecac5b')
  self.assertEqual(json.loads((R/'tools/benchmarks/latest_engine_sources_20261023.json').read_text())['lab_candidate_binary_sha256']['upstream-master-4b'], 'acd2f8c69eb384c7643d3963e3946f28932138193a4c6b8b59ca9510272c20da')
  for required in ('upstream-master-4b','-DGGML_VULKAN=ON','latest-upstream-master062-vulkan','NOT_GPU_QUALIFIED.txt','git ls-remote','sha256sum'):
   self.assertIn(required,s)
  self.assertNotIn('rdna-r114',s)
if __name__=='__main__':unittest.main(verbosity=2)
