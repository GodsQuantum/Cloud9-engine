#!/usr/bin/env python3
"""CI-only source and backend parity gate for native MMB ablation."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class HIPBaselineParity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.a=(ROOT/'.github/workflows/lab-upstream-master-hip-gfx1103-latest.yml').read_text()
  cls.b=(ROOT/'.github/workflows/lab-native-chimera-mmb-r114-on-latest.yml').read_text()
  cls.m=json.loads((ROOT/'tools/chimera/native-mmb-r114-on-latest184f.json').read_text())
  cls.p=json.loads((ROOT/'tools/benchmarks/latest_engine_sources_20261023.json').read_text())
 def test_identical_native_hip_toolchain(self):
  for s in (self.a,self.b):
   for flag in ('rocm[libraries,devel,device-gfx1103]==10.1.0','-DGGML_HIP=ON','-DGPU_TARGETS=gfx1103','-DCMAKE_BUILD_TYPE=Release','--parallel 2'):
    self.assertIn(flag,s)
 def test_same_actual_latest_source(self):
  self.assertEqual(self.m['base']['commit'],self.p['github_repositories']['upstream']['commit'])
  self.assertIn('verify_latest_sources.py --candidate upstream-master-4b',self.a)
  self.assertIn('verify_latest_sources.py --all',self.b)
 def test_not_promoted(self):
  self.assertIn('NO_GPU_CERTIFICATION.txt',self.a)
  self.assertIn('NOT-QUALIFIED.txt',self.b)
  self.assertFalse(self.m['qualification']['benchmark'])
if __name__=='__main__':unittest.main(verbosity=2)
