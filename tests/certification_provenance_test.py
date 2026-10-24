import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

R=Path(__file__).resolve().parents[1]
S=importlib.util.spec_from_file_location("regcheck",R/"tools/qualification/check_proof_registry.py")
M=importlib.util.module_from_spec(S)
S.loader.exec_module(M)
class ProofRegistryTest(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((R/"certification/certification_registry.json").read_text())
 def test_schema_and_historical_proofs(self):
  M.validate(self.d)
  self.assertEqual(self.d["hall_record_count_at_audit"],192)
  self.assertEqual([g["id"] for g in self.d["gates"] if g["status"]=="HISTORICAL_VALID"],["C01","C02","C03"])
  self.assertNotIn("C03",self.d["minimum_production_path"])
 def test_all_evidence_has_sha(self):
  for g in self.d["gates"]:
   for e in g["evidence"]:
    self.assertEqual(len(e["sha256"]),64)
 def test_deterministic_handoff_and_matrix(self):
  self.assertEqual((R/"certification/CURRENT_STATUS.md").read_text(),M.render_status(self.d))
  self.assertEqual((R/"certification/NEXT_HANDOFF.md").read_text(),M.render_handoff(self.d))
 def test_repo_raw_benchmarks_shas_pinned_even_without_cloud9_host(self):
  self.assertEqual(self.d["hall_record_count_at_audit"],192)
  self.assertEqual(len(self.d["repo_proof_snapshots"]),7)
  M.validate(self.d)
  altered=json.loads(json.dumps(self.d))
  altered["repo_proof_snapshots"][0]["sha256"]="0"*64
  with self.assertRaisesRegex(AssertionError,"digest mismatch"):
   M.validate(altered)
 def test_sha_detects_mutated_historical_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   proof=root/"oldproof.json"
   proof.write_bytes(b"correct historical file")
   sample={"id":"C01","title":"a","scope":"b","remaining":"c","acceptance":"d",
        "status":"HISTORICAL_VALID",
        "evidence":[{"project_path":"oldproof.json","sha256":M.sha(proof),"note":"old source"}]}
   other={"schema_version":1,"gates":[sample],
       "minimum_production_path":[],"full_product_path":[],
       "historic_proofs_not_current_build_certification":["C01"]}
   M.validate(other,root)
   proof.write_bytes(b"modified")
   with self.assertRaisesRegex(AssertionError,"changed"):
    M.validate(other,root)
if __name__=="__main__":unittest.main()
