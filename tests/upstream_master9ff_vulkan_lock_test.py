#!/usr/bin/env python3
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Master9ffVulkanContract(unittest.TestCase):
 def test_source_attested_and_not_production(self):
  m=json.loads((ROOT/'tools/benchmarks/upstream-master9ff-vulkan-lock.json').read_text())
  self.assertEqual(m['source_commit'],'9ff0d7e90f0faaa7c16017e6dcf9cf91c50a100e')
  self.assertEqual(m['source_tree'],'60bf42018da47404b7260ee2bebd108b6c1b511f')
  self.assertFalse(m['compiled']);self.assertFalse(m['on_device_verified']);self.assertFalse(m['production_approved'])
 def test_distinct_source_lock_and_no_old_baseline_relabel(self):
  s=(ROOT/'.github/workflows/lab-latest-upstream-master9ff-vulkan.yml').read_text()
  self.assertIn('master9ff-vulkan',s)
  self.assertIn('upstream-master9ff-vulkan-lock.json',s)
  self.assertIn('UPSTREAM_MOVED_REPIN_REQUIRED',s)
  self.assertIn('GGML_VULKAN=ON',s)
  self.assertIn('NOT_GPU_QUALIFIED.txt',s)
  self.assertNotIn('06230cb',s)
  self.assertNotIn('latest_engine_sources_20261023.json',s)
if __name__=='__main__':unittest.main(verbosity=2)
