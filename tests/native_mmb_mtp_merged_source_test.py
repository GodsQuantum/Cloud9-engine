import importlib.util
from pathlib import Path
import unittest

R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("native",R/"tools/chimera/verify_native_mmb_mtp_port.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class SourceTest(unittest.TestCase):
 def test_immutable_tree_sha(self):
  m,p=mod.verify()
  self.assertEqual(m["base"]["commit"],"9ae73e68f5a78933c0d988bbd17bf4647ad6a0b2")
  self.assertGreater(p.stat().st_size,200000)
  self.assertEqual(len(m["donor"]["patches"]),4)
 def test_opt_in_no_promotion(self):
  m,p=mod.verify()
  d=p.read_text()
  self.assertIn("tail > 0 ?",d)
  self.assertIn("ubatch.type",d)
  self.assertIn("LLAMA_MTP_INGEST_TAIL",d)
  self.assertIn("GGML_CUDA_MMB",d)
  self.assertTrue(all(not v for v in m["qualification"].values()))

if __name__=="__main__":unittest.main()
