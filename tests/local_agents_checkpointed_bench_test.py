"""Do not execute a model to certify benchmark resume/guard semantics."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

REPO=Path(__file__).resolve().parents[1]
SRC=REPO/"tools/local_agents/bench_native_agent_tools.py"
S=importlib.util.spec_from_file_location("cloud9_bench", SRC)
B=importlib.util.module_from_spec(S);S.loader.exec_module(B)

class CheckpointedBench(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.addCleanup(self.temp.cleanup)
  self.path=Path(self.temp.name)/"checkpoint.json"
  fixtures=Path(self.temp.name)/"fixtures.json"
  fixtures.write_text(json.dumps({"fixtures":[{
      "id":"case-"+str(i),"expected_first_tool":"pve.get_ct_config",
      "forbidden_first_tool":"pve.restart_ct",
      "tools_are_simulated":True,"prompt_fr":"inspect ct"+str(i)}
      for i in range(12)]}))
  self.fx=B.fixture_list(fixtures)[:2]
  self.a=SimpleNamespace(output=str(self.path),repetitions=3,
      fixture=str(fixtures),model="Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB",
      allow_lab_load=True,resume=False,base="http://fake",
      guardian_host="mock",guardian_port=1,request_gib=4.1)
  self.seen=[]
 def mock_api(self,url,body=None,timeout=3):
  if url.endswith("/health"):return {"worker_model":None}
  assert url.endswith("/v1/chat/completions")
  fid=body["messages"][-1]["content"]
  x=next(x for x in self.fx if x["prompt_fr"]==fid)
  self.seen.append(x["id"])
  return {"choices":[{"message":{"tool_calls":[{"function":{
    "name":x["expected_first_tool"],"arguments":json.dumps({"target":"ct300"})}}]}}],
    "usage":{"completion_tokens":13},"timings":{"predicted_per_second":31}}
 def guard(self,*args):
  return {"allow":True,"mem_available_gib":29,"psi_memory_full_avg10":0.0,"swap_used_percent":20}
 def test_6_of_6_three_repetitions_and_idempotent_resume(self):
  with patch.object(B,"read_json",side_effect=self.mock_api),patch.object(B,"guarded_request",side_effect=self.guard):
   first=B.checkpointed_run(self.a,self.fx)
   self.assertEqual(first["status"],"complete")
   self.assertEqual(len(first["results"]),6)
   self.assertTrue(all(x["passed"] for x in first["results"]))
   self.a.resume=True
   second=B.checkpointed_run(self.a,self.fx)
   self.assertEqual(len(second["results"]),6)
   self.assertEqual(len(self.seen),6,"Re-ran completed test on resume")
 def test_partial_checkpoint_resumes_after_resource_pause(self):
  state={"calls":0}
  def guard(*args):
   state["calls"]+=1
   if state["calls"]==2:
    return {"allow":False,"mem_available_gib":24.5,
            "psi_memory_full_avg10":0.9,"swap_used_percent":90}
   return self.guard(*args)
  with patch.object(B,"read_json",side_effect=self.mock_api),patch.object(B,"guarded_request",side_effect=guard):
   first=B.checkpointed_run(self.a,self.fx)
   self.assertEqual(first["status"],"blocked_official_gpu_admission")
   self.assertEqual(len(first["results"]),1)
   self.assertEqual(self.seen,["case-0"])
   self.a.resume=True
   resumed=B.checkpointed_run(self.a,self.fx)
   self.assertEqual(resumed["status"],"complete")
   self.assertEqual(len(resumed["results"]),6)
   self.assertEqual(self.seen.count("case-0"),3)
   self.assertEqual(self.seen.count("case-1"),3)
 def test_unsafe_tool_selection_stops_benchmark(self):
  def unsafe_api(url,body=None,timeout=3):
   if url.endswith("/health"):return {"worker_model":None}
   return {"choices":[{"message":{"tool_calls":[{"function":{
       "name":"pve.restart_ct","arguments":json.dumps({"target":"ct300"})}}]}}]}
  with patch.object(B,"read_json",side_effect=unsafe_api),patch.object(B,"guarded_request",side_effect=self.guard):
   r=B.checkpointed_run(self.a,self.fx)
   self.assertEqual(r["status"],"failed_unsafe_tool_selected")
   self.assertEqual(len(r["results"]),1)
   self.assertTrue(r["results"][0]["unsafe"])
 def test_if_different_worker_never_evicted(self):
  with patch.object(B,"read_json",return_value={"worker_model":"PRODUCTION_35B"}),patch.object(B,"guarded_request",side_effect=self.guard):
   result=B.checkpointed_run(self.a,self.fx)
  self.assertEqual(result["status"],"blocked_different_active_model")
  self.assertEqual(result["results"],[])
 def test_refused_admission_writes_checkpoint_without_loading(self):
  with patch.object(B,"read_json",return_value={"worker_model":None}),patch.object(B,"guarded_request",return_value={"allow":False,"reasons":["PSI"]}):
   result=B.checkpointed_run(self.a,self.fx)
  self.assertEqual(result["status"],"blocked_official_gpu_admission")
  self.assertEqual(len(result["results"]),0)
 def test_loaded_worker_uses_runtime_floor_not_start_floor(self):
  def already_loaded(url,body=None,timeout=3):
   if url.endswith("/health"):return {"worker_model":self.a.model}
   return self.mock_api(url,body,timeout)
  guard={"allow":False,"mem_available_gib":22.5,
         "psi_memory_full_avg10":0.11,"swap_used_percent":82,
         "reasons":["below START floor"]}
  with patch.object(B,"read_json",side_effect=already_loaded),patch.object(B,"guarded_request",return_value=guard):
   result=B.checkpointed_run(self.a,self.fx)
  self.assertEqual(result["status"],"complete")
  self.assertEqual(len(self.seen),6)
 def test_reject_other_lab_model(self):
  self.a.model="PRODUCTION_35B"
  with self.assertRaisesRegex(ValueError,"only exact"):
   B.checkpointed_run(self.a,self.fx)
 def test_resume_rejects_changed_fixture_provenance(self):
  with patch.object(B,"read_json",side_effect=self.mock_api),patch.object(B,"guarded_request",side_effect=self.guard):
   B.checkpointed_run(self.a,self.fx)
  self.a.resume=True
  changed=Path(self.temp.name)/"different.json"
  changed.write_text('{"fixtures":[]}')
  self.a.fixture=str(changed)
  with self.assertRaisesRegex(ValueError,"fixture_sha256"):
   B.checkpointed_run(self.a,self.fx)
 def test_runtime_pressure_halts_without_call(self):
  def already_loaded(url,body=None,timeout=3):
   if url.endswith("/health"):return {"worker_model":self.a.model}
   self.fail("Should not call inference under pressure")
  with patch.object(B,"read_json",side_effect=already_loaded),patch.object(B,"guarded_request",return_value={"allow":False,"mem_available_gib":20.3,"psi_memory_full_avg10":1.1,"swap_used_percent":90}):
   result=B.checkpointed_run(self.a,self.fx)
  self.assertEqual(result["status"],"paused_resource_pressure")
  self.assertEqual(len(result["results"]),0)

if __name__=="__main__": unittest.main()
