import importlib.util,unittest,pathlib
P=pathlib.Path(__file__).resolve().parents[1]/"tools/qualification/rank_cloud9_hardware_engines.py"
s=importlib.util.spec_from_file_location("rank_cloud9_hardware_engines",P)
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class RankEvidence(unittest.TestCase):
 def test_source_json_all(self):
  out=r.decision()
  self.assertFalse(out["all_purpose_production_certified"])
  self.assertFalse(out["production_modified"])
 def test_atomic_16k_verified_exact(self):
  out=r.decision();self.assertEqual(out["atomic2"]["historical_16K_exact_retrieval"],"3/3 five markers, 16330 actual input tokens")
  self.assertGreater(out["atomic2"]["historical_16K_median_decode_tps"],30)
 def test_real_agent_code_quality_blocks(self):
  self.assertEqual(r.decision()["atomic2"]["historical_quality_36_categories"]["code"],"0/9")
 def test_chimera_c09_and_16k_separate(self):
  out=r.decision()
  self.assertIn("36/36",out["chimera"]["simulated_diagnostic_tools"])
  self.assertIn("failed",out["chimera"]["current_16K"])
 def test_unmatched_protocols_not_ranked_pareto(self):
  self.assertIn("NOT directly comparable",r.decision()["source_lineage"])
 def test_runtime_does_not_mutate_service(self):
  text=P.read_text()
  self.assertNotIn("systemctl restart",text)
  self.assertNotIn("pct stop",text)
  self.assertNotIn("subprocess.run",text)
 def test_live_candidate_optional(self):
  data=r.decision()["atomic2"]["new_live_C09"]
  self.assertTrue(data is None or "scored_cases" in data)
if __name__=="__main__":unittest.main()
