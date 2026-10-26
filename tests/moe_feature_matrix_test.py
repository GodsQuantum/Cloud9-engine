import pathlib,json,unittest
P=pathlib.Path(__file__).resolve().parents[1]
class Validate(unittest.TestCase):
 def setUp(self):self.d=json.loads((P/"certification/moe_tournament_20261026.json").read_text())
 def test_pym_primary_not_small_moe(self):
  self.assertEqual(self.d["targets"][0]["id"],"pym-q2")
  self.assertEqual(self.d["targets"][1]["id"],"pym-heretic")
 def test_flash_original_absent_not_falsely_substituted(self):
  self.assertFalse(self.d["targets"][2]["engine_compare"])
  self.assertIsNone(self.d["targets"][2]["path"])
 def test_true_128k(self):
  self.assertEqual(self.d["protocol"]["contexts"][-1],131072)
  self.assertTrue(self.d["protocol"]["final_answer_required"])
 def test_cross_feature_parity(self):
  f={x["id"]:x for x in self.d["features"]}
  self.assertEqual(f["mtp2"]["upstream"],"native")
  self.assertEqual(f["mtp2"]["atomic2"],"native")
  self.assertIn("port",f["mtp_adaptive"]["upstream"])
  self.assertIn("port",f["kv_turbo3"]["upstream"])
  self.assertIn("port",f["expert_cache"]["atomic2"])
 def test_safety(self):
  self.assertTrue(self.d["safety"]["official_guard"])
  self.assertTrue(self.d["safety"]["no_stop_pbs_haos_embeddings"])
  self.assertTrue(self.d["safety"]["no_default_prod_change"])
 def test_names_unique(self):
  for key in ("features","targets","engines"):
   x=[i["id"] for i in self.d[key]]
   self.assertEqual(len(x),len(set(x)))
 def test_plan_exists(self):
  self.assertGreater((P/"certification/MOE_ENGINE_TOURNAMENT_20261026.md").stat().st_size,3000)
