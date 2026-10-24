import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("guard",ROOT/"tools/chimera/verify_native_turbo_backend_guard.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
class SourcePolicyTest(unittest.TestCase):
    def test_verified_provenance(self):
        m,p=module.verify()
        self.assertEqual(m["base"]["commit"],"9ae73e68f5a78933c0d988bbd17bf4647ad6a0b2")
        self.assertGreater(m["port"]["changed_files"],55)
        self.assertGreater(p.stat().st_size,300000)
    def test_no_unapproved_hip_turbo_backend(self):
        m,p=module.verify()
        self.assertFalse(m["qualification"]["production"])
        self.assertFalse(m["qualification"]["gpu_model_quality"])
        self.assertIn("HIP/ROCm",p.read_text())
    def test_gpu_guard_matched_to_real_cache_constructor(self):
        m,p=module.verify()
        s=p.read_text()
        self.assertIn('if (!llama_cloud9_turbo_backend_allowed',s)
        self.assertIn('ggml_backend_dev_type(dev)',s)
        self.assertIn('ggml_backend_reg_name(reg)',s)
if __name__=="__main__": unittest.main()
