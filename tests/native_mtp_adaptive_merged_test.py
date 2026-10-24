from pathlib import Path
import importlib.util
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("adaptive_port",ROOT/"tools/chimera/verify_native_mtp_adaptive.py")
port=importlib.util.module_from_spec(spec)
spec.loader.exec_module(port)

class AdaptiveMergedSourceTest(unittest.TestCase):
 def test_true_source_and_pinning(self):
  m,p=port.verify()
  self.assertEqual(m["source_upstream"]["commit"],"9ae73e68f5a78933c0d988bbd17bf4647ad6a0b2")
  self.assertGreater(p.stat().st_size,300000)
  self.assertGreater(m["port"]["files_changed"],50)
 def test_separate_from_production(self):
  m,p=port.verify()
  self.assertFalse(m["qualification"]["production"])
  self.assertFalse(m["qualification"]["gpu_execution"])
  self.assertTrue(m["qualification"]["adaptive_native_ctest"])
 def test_native_mtp_interfaces(self):
  m,p=port.verify()
  delta=p.read_text()
  for marker in ("common_speculative_accept_partial","draft-mtp-adaptive","set_embeddings_nextn_from","n_min_adaptive"):
   self.assertIn(marker,delta)

if __name__=="__main__":unittest.main()
