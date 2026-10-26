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
 def test_partial_policy_uses_official_minimum_and_gpu_floor(self):
  g={"allow":True,"mem_available_gib":26,"psi_memory_full_avg10":0,"safe_total_gtt_gib":6,"swap_used_percent":71}
  with mock.patch.object(b,"guardian",return_value=g) as gg, mock.patch.object(b,"psi_io_full",return_value=1),mock.patch.object(b,"host_temp",return_value=63),mock.patch.object(b,"fetch",side_effect=[{"worker_model":None},{"status":"ok","loaded_models":[]}]):
   x=b.preflight("pym","upstream_b11844","base","partial")
  self.assertTrue(x["admitted"]);gg.assert_called_once_with(6.0)
  self.assertEqual(x["min_available_gib"],24.4)
 def test_minimal_gpu_pym_profile(self):
  g={"allow":True,"mem_available_gib":26,"psi_memory_full_avg10":0,"safe_total_gtt_gib":6,"swap_used_percent":71}
  with mock.patch.object(b,"guardian",return_value=g) as gg, mock.patch.object(b,"psi_io_full",return_value=1),mock.patch.object(b,"host_temp",return_value=63),mock.patch.object(b,"fetch",side_effect=[{"worker_model":None},{"status":"ok","loaded_models":[]}]):
   result=b.preflight("pym","upstream_b11844","base","partial_min")
  self.assertTrue(result["admitted"]);gg.assert_called_once_with(2.75)
 def test_partial_also_never_bypasses_official_guard(self):
  g={"allow":False,"mem_available_gib":26,"psi_memory_full_avg10":0,"safe_total_gtt_gib":6,"swap_used_percent":71}
  with mock.patch.object(b,"guardian",return_value=g),mock.patch.object(b,"psi_io_full",return_value=1),mock.patch.object(b,"host_temp",return_value=63),mock.patch.object(b,"fetch",side_effect=[{"worker_model":None},{"status":"ok","loaded_models":[]}]):
   x=b.preflight("pym","upstream_b11844","base","partial")
  self.assertFalse(x["admitted"])
 def test_lfm_official_guard_preflight_after_download(self):
  from pathlib import Path
  import tempfile
  with tempfile.TemporaryDirectory() as dr:
   p=Path(dr)/"LFM.gguf"
   p.write_bytes(b"dummy")
   with mock.patch.dict(b.MODELS,{"lfm_official_q4":p}),mock.patch.object(b,"guardian") as guard:
    x=b.preflight("lfm_official_q4","upstream_b11844","base")
  self.assertFalse(x["admitted"]);guard.assert_not_called()
 def test_atomic2_stage_available_and_no_mtp_lfm(self):
  self.assertTrue(b.BINARIES["atomic2"].exists())
  from pathlib import Path
  import tempfile
  with tempfile.TemporaryDirectory() as dr:
   tmp=Path(dr)/"lfm.gguf";tmp.write_bytes(b"test")
   with mock.patch.dict(b.MODELS,{"lfm_official_q4":tmp}),mock.patch.object(b,"guardian") as guard:
    self.assertIn("NON_PYM_INLINE_MTP_UNVERIFIED",b.preflight("lfm_official_q4","atomic2","mtp2")["reasons"])
   guard.assert_not_called()
 def test_post_load_runtime_never_understeps_emergency_floor(self):
  source=P.read_text()
  self.assertIn('g.get("mem_available_gib",0)<20.5',source)
  self.assertIn('g.get("psi_memory_full_avg10",99)>=.5',source)
  self.assertIn('result["latest_runtime_guard"]',source)
  self.assertIn('g.get("mem_available_gib",0)<20.5 or',source)
 def test_three_distinct_quality_tasks(self):self.assertEqual([x[0] for x in b.PROMPTS],["math","code","fr"])
if __name__=="__main__":unittest.main()
