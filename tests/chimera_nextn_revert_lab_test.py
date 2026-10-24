import hashlib
import json
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/"tools/chimera/patches/20261025-master9ae-nextn-rereserve-revert-LAB.patch"
W=R/".github/workflows/lab-chimera-nextn-vulkan-ab.yml"
class NextNSourceProof(unittest.TestCase):
 def test_exact_single_file_delta(self):
  text=P.read_text()
  self.assertEqual(hashlib.sha256(P.read_bytes()).hexdigest(),"84120fcb675e0b274147b16a5296ab5b266b76e29ae246cea21e54729337e5ee")
  self.assertEqual(text.count("diff --git"),1)
  self.assertIn("-        sched_need_reserve = true;",text)
 def test_experimental_ci_pinned(self):
  text=W.read_text()
  self.assertIn("workflow_dispatch",text)
  self.assertIn("d122b09e38c4e5397601c1ade0c3c6cc3aea39cc",text)
  self.assertIn("NOT-PRODUCTION.txt",text)
  self.assertNotIn("pct exec",text)
if __name__=="__main__":unittest.main()
