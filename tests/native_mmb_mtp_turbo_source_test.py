import importlib.util
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("native_turbo",R/"tools/chimera/verify_native_mmb_mtp_turbo.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TurboSource(unittest.TestCase):
 def test_source_provenance(self):
  m,p=mod.load()
  self.assertEqual(m["base"]["commit"],"9ae73e68f5a78933c0d988bbd17bf4647ad6a0b2")
  self.assertGreater(p.stat().st_size,250000)
  self.assertEqual(len(m["donor_atomic_patches"]),8)
 def test_bridge_not_full_atomic2(self):
  m,p=mod.load()
  self.assertIn("not full Atomic2",m["scope"])
  self.assertFalse(any(m["qualification"].values()))
 def test_real_vulkan_shaders_and_graph(self):
  m,p=mod.load()
  s=p.read_text()
  for term in ("flash_attn_dequant.glsl","llama_turbo_wht","GGML_TYPE_TURBO3_0"):
   self.assertIn(term,s)
if __name__=="__main__":unittest.main()
