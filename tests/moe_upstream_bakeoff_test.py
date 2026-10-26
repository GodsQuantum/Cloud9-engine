import ast,importlib.util,io,json,pathlib,tempfile,unittest
from unittest import mock
P=pathlib.Path(__file__).resolve().parents[1]/"tools/qualification/moe_upstream_bakeoff.py"
s=importlib.util.spec_from_file_location("moe_upstream_bakeoff",P)
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
class GuardTests(unittest.TestCase):
 def test_import_and_syntax(self):ast.parse(P.read_text())
 def test_models_are_exact_and_noninterchangeable(self):
  self.assertIn("Qwen3.6-35B-A3B-Pym-Q2-MTP.gguf",str(b.MODELS["pym"]))
  self.assertIn("GSQ-RCO-IQ1_M",str(b.MODELS["flash_alternate"]))
 def test_no_copying_historical_flash_speed(self):self.assertIn("NOT the historical AD-4.27",P.read_text())
 def test_authoritative_gtt_and_ram(self):
  s=P.read_text()
  self.assertIn("gguf_gib+23.0",s)
  self.assertIn("guardian(required_gtt)",s)
  self.assertIn('g.get("safe_total_gtt_gib",0)<required_gtt',s)
 def test_gpu_exclusive_and_owned_shutdown(self):
  source=P.read_text()
  self.assertIn("fcntl.LOCK_EX|fcntl.LOCK_NB",source)
  self.assertIn("stop_own(child)",source)
  self.assertNotIn("systemctl restart",source)
  self.assertNotIn("pct stop",source)
 def test_preflight_denies_without_waiting_for_model_load(self):
  g={"allow":False,"mem_available_gib":25,"psi_memory_full_avg10":0,"safe_total_gtt_gib":8,"swap_used_percent":72}
  with mock.patch.object(b,"guardian",return_value=g),mock.patch.object(b,"psi_io_full",return_value=0),mock.patch.object(b,"host_temp",return_value=60),mock.patch.object(b,"fetch",side_effect=[{"worker_model":None},{"status":"ok","loaded_models":[]}]):
   d=b.preflight("pym","upstream_b11844","mtp2")
  self.assertFalse(d["admitted"])
  self.assertIn("OFFICIAL_GPU_GUARD_DENIED",d["reasons"])
  self.assertIn("MODEL_SIZE_PLUS_PRODUCTION_RAM_RESERVE",d["reasons"])
  self.assertIn("INSUFFICIENT_GTT_FOR_MATCHED_FULL_OFFLOAD",d["reasons"])
 def test_flash_mtp_rejected_before_guard(self):
  with mock.patch.object(b,"guardian") as g:
   out=b.preflight("flash_alternate","upstream_b11844","mtp2")
  self.assertFalse(out["admitted"]);g.assert_not_called()
 def test_flash_alternate_never_labeled_as_historical(self):
  with mock.patch.object(b,"guardian") as guard:
   r=b.preflight("flash_alternate","upstream_b11844","base")
  self.assertFalse(r["admitted"])
  self.assertFalse(r["historical_17_878_tps_comparable"])
  self.assertGreater(r["actual_sharded_bytes"],55_000_000_000)
  guard.assert_not_called()
 def test_three_distinct_quality_tasks(self):self.assertEqual([x[0] for x in b.PROMPTS],["math","code","fr"])
if __name__=="__main__":unittest.main()
