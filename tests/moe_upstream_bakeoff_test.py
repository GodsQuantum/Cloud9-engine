import ast,importlib.util,io,json,pathlib,tempfile,unittest
from unittest import mock
P=pathlib.Path(__file__).resolve().parents[1]/"tools/qualification/moe_upstream_bakeoff.py"
s=importlib.util.spec_from_file_location("moe_upstream_bakeoff",P)
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
class GuardTests(unittest.TestCase):
 def test_import_and_syntax(self):ast.parse(P.read_text())
 def test_hof_atomic16_kv_rank_kept_on_atomic2_without_rewriting_results(self):
  self.assertEqual(b.HOF_PYM_KV_ORDER,("f16","turbo4","q8_0","turbo3"))
  self.assertEqual(b.HOF_PYM_TPS,{"f16":36.28,"turbo4":35.20,"q8_0":35.07,"turbo3":34.40})
  src=P.read_text()
  self.assertIn('"-ctk",(a.parity_kv if a.preset==PARITY_PRESET else "f16")',src)
  self.assertIn('"parity_kv":a.parity_kv',src)
  self.assertIn('PARITY_KV_UNSUPPORTED_BY_BINARY',src)
 def test_recent_real_pym_memory_psis_not_replayed(self):
  g={"allow":True,"mem_available_gib":33,"psi_memory_full_avg10":0,
     "safe_total_gtt_gib":14.5,"swap_used_percent":80}
  with mock.patch.object(b,"guardian",return_value=g),mock.patch.object(b,"psi_io_full",return_value=0),mock.patch.object(b,"host_temp",return_value=60):
   with mock.patch.object(b,"fetch",side_effect=[{"worker_model":None},[{"id":0,"is_processing":False}],{"status":"ok","loaded_models":[]}]):
    d=b.preflight("pym","atomic2","mtp2","full",b.PARITY_PRESET,"mmap")
  self.assertFalse(d["admitted"])
  self.assertIn("PYM_PRIOR_PSI_LOAD_HEADROOM",d["reasons"])
  self.assertGreater(d["min_available_gib"],37)
 def test_guard_source_address_restricted(self):
  with mock.patch.dict(b.os.environ,{"CLOUD9_GUARD_SOURCE_IP":"8.8.8.8"}):
   with self.assertRaisesRegex(ValueError,"UNAUTHORIZED_GUARD_SOURCE"):b.guardian(14)
 def test_resumable_task_subset_explicit(self):
  src=P.read_text()
  self.assertIn('selected_prompts=[x for x in PROMPTS if x[0] in a.tasks.split(",")]',src)
  self.assertIn('for name,prompt in selected_prompts:',src)
  self.assertIn('len(result["rows"])==len(selected_prompts)',src)
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
  with mock.patch.object(b,"guardian",return_value=g),mock.patch.object(b,"psi_io_full",return_value=0),mock.patch.object(b,"host_temp",return_value=60),mock.patch.object(b,"fetch",side_effect=[{"worker_model":None},[{"id":0,"is_processing":False}],{"status":"ok","loaded_models":[]}]):
   d=b.preflight("pym","upstream_b11844","mtp2")
  self.assertFalse(d["admitted"])
  self.assertIn("OFFICIAL_GPU_GUARD_DENIED",d["reasons"])
  self.assertIn("MODEL_SIZE_PLUS_PRODUCTION_RAM_RESERVE",d["reasons"])
  self.assertIn("INSUFFICIENT_GTT_FOR_MATCHED_FULL_OFFLOAD",d["reasons"])
 def test_flash_mtp_rejected_before_guard(self):
  with mock.patch.object(b,"guardian") as g:
   out=b.preflight("flash_alternate","upstream_b11844","mtp2")
  self.assertFalse(out["admitted"]);g.assert_not_called()
 def test_exact_flash_ad427_model_is_not_confused_with_missing_mtp_draft(self):
  self.assertIn("FlashNext-AD427",str(b.MODELS["flash_ad427"]))
  with mock.patch.object(b,"guardian") as guard:
   result=b.preflight("flash_ad427","atomic2","base")
  self.assertFalse(result["admitted"])
  self.assertTrue(result["historic_target_gguf_found"])
  self.assertTrue(result["fr_spec_sidecar_present"])
  self.assertTrue(result["fr_spec_sidecar_size_verified"])
  self.assertEqual(result["fr_spec_sidecar_expected_sha256"],"c9c505c1f68f008827a29733d5d2fe40a8170c324c676168831798b05217df4f")
  self.assertEqual(result["actual_sharded_bytes"],94525394976)
  self.assertIn("FLASH_AD427_DRAFT_FRSPEC_NOT_CONFIGURED",result["reasons"])
  self.assertFalse(result["historical_17_878_tps_comparable"])
  self.assertFalse(result["sha256_verified"])
  guard.assert_not_called()
 def test_flash_ad427_inline_mtp_not_falsely_supported(self):
  with mock.patch.object(b,"guardian") as guard:
   result=b.preflight("flash_ad427","atomic2","mtp3")
  self.assertFalse(result["admitted"])
  self.assertIn("NON_PYM_INLINE_MTP_UNVERIFIED",result["reasons"])
  guard.assert_not_called()
 def test_flash_ad427_missing_shards_fail_closed(self):
  with tempfile.TemporaryDirectory() as td:
   missing=pathlib.Path(td)/"Qwen3.8-Flash-Next-AD-4.27bpw-Q4_K_M-M64-00001-of-00033.gguf"
   missing.write_bytes(b"GGUF")
   with mock.patch.dict(b.MODELS,{"flash_ad427":missing}),mock.patch.object(b,"guardian") as guard:
    result=b.preflight("flash_ad427","atomic2","base")
  self.assertFalse(result["admitted"])
  self.assertFalse(result["historic_target_gguf_found"])
  self.assertIn("FLASH_AD427_SHARDS_INCOMPLETE",result["reasons"])
  guard.assert_not_called()
 def test_flash_alternate_never_labeled_as_historical(self):
  with mock.patch.object(b,"guardian") as guard:
   r=b.preflight("flash_alternate","upstream_b11844","base")
  self.assertFalse(r["admitted"])
  self.assertFalse(r["historical_17_878_tps_comparable"])
  self.assertGreater(r["actual_sharded_bytes"],55_000_000_000)
  guard.assert_not_called()
 def test_partial_policy_uses_official_minimum_and_gpu_floor(self):
  g={"allow":True,"mem_available_gib":26,"psi_memory_full_avg10":0,"safe_total_gtt_gib":6,"swap_used_percent":71}
  with mock.patch.object(b,"guardian",return_value=g) as gg, mock.patch.object(b,"psi_io_full",return_value=1),mock.patch.object(b,"host_temp",return_value=63),mock.patch.object(b,"fetch",side_effect=[{"worker_model":None},[{"id":0,"is_processing":False}],{"status":"ok","loaded_models":[]}]):
   x=b.preflight("pym","upstream_b11844","base","partial")
  self.assertTrue(x["admitted"]);gg.assert_called_once_with(6.0)
  self.assertEqual(x["min_available_gib"],24.4)
 def test_minimal_gpu_pym_profile(self):
  g={"allow":True,"mem_available_gib":26,"psi_memory_full_avg10":0,"safe_total_gtt_gib":6,"swap_used_percent":71}
  with mock.patch.object(b,"guardian",return_value=g) as gg, mock.patch.object(b,"psi_io_full",return_value=1),mock.patch.object(b,"host_temp",return_value=63),mock.patch.object(b,"fetch",side_effect=[{"worker_model":None},[{"id":0,"is_processing":False}],{"status":"ok","loaded_models":[]}]):
   result=b.preflight("pym","upstream_b11844","base","partial_min")
  self.assertTrue(result["admitted"]);gg.assert_called_once_with(2.75)
 def test_partial_also_never_bypasses_official_guard(self):
  g={"allow":False,"mem_available_gib":26,"psi_memory_full_avg10":0,"safe_total_gtt_gib":6,"swap_used_percent":71}
  with mock.patch.object(b,"guardian",return_value=g),mock.patch.object(b,"psi_io_full",return_value=1),mock.patch.object(b,"host_temp",return_value=63),mock.patch.object(b,"fetch",side_effect=[{"worker_model":None},[{"id":0,"is_processing":False}],{"status":"ok","loaded_models":[]}]):
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
 def test_lfm_compact_uses_native_guard(self):
  guard={"allow":True,"mem_available_gib":25.8,"psi_memory_full_avg10":0.02,"safe_total_gtt_gib":7.2,"swap_used_percent":74}
  with mock.patch.object(b,"guardian",return_value=guard) as gg, mock.patch.object(b,"psi_io_full",return_value=3),mock.patch.object(b,"host_temp",return_value=62),mock.patch.object(b,"fetch",side_effect=[{"worker_model":None},[{"id":0,"is_processing":False}],{"status":"ok","loaded_models":[]}]):
   model=b.MODELS["lfm_official_q4"]
   x=b.preflight("lfm_official_q4","upstream_b11844","base","compact")
  self.assertTrue(x["admitted"]);gg.assert_called_once_with(5.5);self.assertEqual(x["min_available_gib"],25)
 def test_compact_gated_to_lfm_only(self):
  text=P.read_text()
  self.assertIn('a.profile=="compact" and a.model!="lfm_official_q4"',text)
  self.assertIn('context="1536" if a.profile=="compact"',text)
  self.assertIn('"32" if a.profile=="compact"',text)
 def test_quality_requires_visible_final_and_correct_math(self):
  text=P.read_text()
  self.assertIn('"--reasoning-budget",str(a.thinking_budget)',text)
  self.assertIn('msg.get("reasoning_content")',text)
  self.assertIn('"math_answer_contains_925"',text)
  self.assertIn('all(x["math_answer_contains_925"] for x in math_rows)',text)
  self.assertIn('"max_tokens":a.max_output_tokens',text)
 def test_postload_cooldown_with_emergency_guard_intact(self):
  text=P.read_text()
  self.assertIn("for cooldown in range(8)",text)
  self.assertIn('g.get("mem_available_gib",0)<20.5',text)
  self.assertIn('g.get("psi_memory_full_avg10",99)>=1.8',text)
  self.assertIn("stop_own(child)",text)
 def test_native_zero_thinking_budget_toggle_for_agentic_latency(self):
  source=P.read_text()
  self.assertIn("choices=[0,128,256]",source)
  self.assertIn("str(a.thinking_budget)",source)
  self.assertIn('("on" if a.model=="lfm_official_q4" else "off")',source)
  self.assertNotIn('["--reasoning","on","--reasoning-budget"',source)
  self.assertIn('all(x["math_answer_contains_925"] for x in math_rows)',source)
 def test_busy_embeddings_no_gpu_admission_even_if_guard_accepts(self):
  g={"allow":True,"mem_available_gib":44,"psi_memory_full_avg10":0,"safe_total_gtt_gib":20,"swap_used_percent":35}
  with mock.patch.object(b,"guardian",return_value=g),mock.patch.object(b,"psi_io_full",return_value=1),mock.patch.object(b,"host_temp",return_value=63),mock.patch.object(b,"fetch",side_effect=[{"worker_model":None},[{"id":0,"is_processing":True}],{"status":"ok","loaded_models":[]}]):
   x=b.preflight("pym","upstream_b11844","mtp2")
  self.assertFalse(x["admitted"])
  self.assertIn("EMBEDDINGS_ACTIVE_OR_UNKNOWN",x["reasons"])
 def test_unreachable_embedding_slots_fail_closed(self):
  with mock.patch.object(b,"fetch",side_effect=OSError("embedding server down")):
   self.assertTrue(b.embeddings_busy())
 def test_pym_original_and_heretic_supported_on_three_engines(self):
  self.assertTrue(b.MODELS["pym_heretic"].exists())
  self.assertTrue(b.BINARIES["atomic2_zen4_lto"].exists())
  self.assertIn('choices=["base","mtp1","mtp2","mtp3","mtp_adaptive"]',P.read_text())
 def test_mtp_adaptive_upstream_denied_before_model_loading(self):
  with mock.patch.object(b,"guardian") as guard:
   o=b.preflight("pym","upstream_b11844","mtp_adaptive")
  self.assertFalse(o["admitted"])
  self.assertIn("ADAPTIVE_MTP_NOT_SUPPORTED_UPSTREAM",o["reasons"])
  guard.assert_not_called()
 def test_cross_engine_short_output_and_watchdog_embedding_guard(self):
  source=P.read_text()
  self.assertIn('choices=[128,192,256,384,768]',source)
  self.assertIn('"max_tokens":a.max_output_tokens',source)
  self.assertIn('"EMBEDDINGS_BECAME_BUSY_OR_UNKNOWN"',source)
  self.assertIn('guard_events.append({"reason":"EMBEDDINGS_BECAME_BUSY_OR_UNKNOWN"})',source)
 def test_guardian_is_authoritative_without_double_gtt_reservation(self):
  gguf=b.MODELS["pym"].stat().st_size/(1024**3)
  guard={"allow":True,"mem_available_gib":39.0,"psi_memory_full_avg10":0,
         "safe_total_gtt_gib":15.1,"swap_used_percent":70}
  with mock.patch.object(b,"guardian",return_value=guard) as g, mock.patch.object(b,"psi_io_full",return_value=1),mock.patch.object(b,"host_temp",return_value=58),mock.patch.object(b,"fetch",side_effect=[{"worker_model":None},[{"id":0,"is_processing":False}],{"status":"ok","loaded_models":[]}]):
   x=b.preflight("pym","atomic2","mtp2","full",b.PARITY_PRESET)
  self.assertTrue(x["admitted"])
  self.assertEqual(x["min_available_gib"],round(gguf+25,2))
  g.assert_called_once_with(14.0)
  with mock.patch.object(b,"guardian",return_value={**guard,"allow":False}),mock.patch.object(b,"psi_io_full",return_value=1),mock.patch.object(b,"host_temp",return_value=58),mock.patch.object(b,"fetch",side_effect=[{"worker_model":None},[{"id":0,"is_processing":False}],{"status":"ok","loaded_models":[]}]):
   self.assertFalse(b.preflight("pym","atomic2","mtp2","full",b.PARITY_PRESET)["admitted"])
 def test_8k_fallback_only_changes_context_not_mtp_kv_fullgpu(self):
  s=P.read_text()
  self.assertIn('choices=[8192,16384],default=16384',s)
  self.assertIn('context=str(a.parity_context) if a.preset==PARITY_PRESET',s)
  self.assertIn('PARITY_PRESET',s)
  self.assertIn('layers={"full":"99"',s)
  self.assertIn('experts={"full":"0"',s)
 def test_fullgpu_nonmmap_pym_device_lost_is_never_retried(self):
  with mock.patch.object(b,"guardian") as guardian:
   r=b.preflight("pym","atomic16","mtp2","full",b.PARITY_PRESET,"none")
  self.assertFalse(r["admitted"])
  self.assertIn("PYM_FULL_GPU_NOMMAP_RADV_DEVICE_LOST_20261026_DO_NOT_RETRY",r["reasons"])
  guardian.assert_not_called()
 def test_load_mode_single_parameter_ablation_keeps_other_flags_equal(self):
  for engine in ("atomic16","atomic2","upstream_b11844"):
   mmap=b.parity_extra_flags(engine,None,"mmap")
   nommap=b.parity_extra_flags(engine,None,"none")
   self.assertEqual(len(mmap),len(nommap))
   self.assertEqual(mmap[1],"mmap")
   self.assertEqual(nommap[1],"none")
   self.assertEqual(mmap[:1]+mmap[2:],nommap[:1]+nommap[2:])
 def test_atomic16_reference_executable_is_in_same_engine_matrix(self):
  self.assertIn("atomic16",b.BINARIES)
  self.assertIn("atomic17",b.BINARIES)
  self.assertTrue(b.BINARIES["atomic16"].exists())
  self.assertTrue(b.BINARIES["atomic17"].exists())
  self.assertIn("044dff242d78",str(b.BINARIES["atomic16"]))
 def test_atomic16_historical_parity_preset_explicit_and_full_gpu_only(self):
  source=P.read_text()
  self.assertEqual(b.PARITY_PRESET,"atomic16-mtp2-f16-fullgpu")
  self.assertIn('a.model=="pym" and a.mode=="mtp2" and a.profile=="full"',source)
  self.assertIn('context=str(a.parity_context) if a.preset==PARITY_PRESET',source)
  self.assertIn('bsize="1024" if a.preset==PARITY_PRESET',source)
  self.assertIn('ubsize="1024" if a.preset==PARITY_PRESET',source)
  self.assertIn('not_exact_atomic16_cli',source)
  self.assertIn('if a.preset==PARITY_PRESET:',source)
 def test_parity_is_native_and_identical_except_upstream_lazy_flag(self):
  for key in ("atomic2","atomic2_zen4_lto","upstream_b11844"):
   flags=b.parity_extra_flags(key," ".join(b.PARITY_REQUIRED_HELP)+" --lazy-mode")
   self.assertEqual(flags[:],b.parity_extra_flags(key))
   self.assertEqual(flags[:13],b.parity_extra_flags("atomic2")[:13])
   self.assertIn("--spec-draft-p-min",flags)
   self.assertIn("--no-spec-draft-backend-sampling",flags)
   self.assertIn("--no-cache-prompt",flags)
   self.assertEqual("--lazy-mode" in flags,key.startswith("upstream"))
 def test_parity_refuses_unsupported_flags_fail_closed(self):
  with self.assertRaisesRegex(ValueError,"PARITY_FEATURE_MISSING"):
   b.parity_extra_flags("atomic2","--poll --spec-type")
  with self.assertRaisesRegex(ValueError,"PARITY_UPSTREAM_LAZY_MODE_FLAG_MISSING"):
   b.parity_extra_flags("upstream_b11844"," ".join(b.PARITY_REQUIRED_HELP))
 def test_three_distinct_quality_tasks(self):self.assertEqual([x[0] for x in b.PROMPTS],["math","code","fr"])
if __name__=="__main__":unittest.main()
