#!/usr/bin/env python3
"""CPU-only eligibility tests: no credentials, models, GPU or network."""
import importlib.util
from pathlib import Path
import unittest
P=Path(__file__).resolve().parents[1]/"scripts/turboquant_kv_gate.py"
spec=importlib.util.spec_from_file_location("gate",P)
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)

def record(case,sec,prompt=12000,valid=True):
    return {"case":case,"correct":valid,"wall_s":sec,"prompt_tokens":prompt}

def make():
    def suite(t_long,t_tool,kv,k,v):
        return {"K":k,"V":v,"status":"passed","isolated_kv_allocation_mib":kv,
                "rows":[record("retrieval",t_long) for _ in range(3)]+[record("calendar",t_tool,prompt=250) for _ in range(3)]}
    return {"context":32768,"comparisons":{
       "f16":suite(40,2,1800,"f16","f16"),
       "q8k-turbo4v":suite(40.5,2.1,950,"q8_0","turbo4"),
       "q8k-turbo3v":suite(40.5,2.1,820,"q8_0","turbo3")}}

class GateTests(unittest.TestCase):
 def test_quality_memory_latency_good(self):
    self.assertTrue(gate.judge(make(),"q8k-turbo4v")["eligible"])
 def test_late_candidate(self):
    p=make()
    for r in p["comparisons"]["q8k-turbo4v"]["rows"][:3]:r["wall_s"]=70
    self.assertIn("long_prompt_latency_regressed",gate.judge(p,"q8k-turbo4v")["reasons"])
 def test_one_incorrect_output_rejected(self):
    p=make();p["comparisons"]["q8k-turbo3v"]["rows"][1]["correct"]=False
    self.assertFalse(gate.judge(p,"q8k-turbo3v")["eligible"])
 def test_original_f16_incorrect_rejected(self):
    p=make();p["comparisons"]["f16"]["rows"][0]["correct"]=False
    self.assertIn("f16_retrieval_quality_regression",gate.judge(p,"q8k-turbo4v")["reasons"])
 def test_no_memory_proof_rejected(self):
    p=make();p["comparisons"]["q8k-turbo3v"].pop("isolated_kv_allocation_mib")
    self.assertIn("isolated_kv_memory_evidence_missing",gate.judge(p,"q8k-turbo3v")["reasons"])
 def test_rss_only_not_accepted(self):
    p=make();p["comparisons"]["q8k-turbo4v"].pop("isolated_kv_allocation_mib")
    p["comparisons"]["q8k-turbo4v"]["startup_rss_mib"]=400
    self.assertFalse(gate.judge(p,"q8k-turbo4v")["eligible"])
 def test_less_than_three_repeats_rejected(self):
    p=make();p["comparisons"]["q8k-turbo4v"]["rows"].pop()
    self.assertIn("q8k-turbo4v_calendar_insufficient_repeats",gate.judge(p,"q8k-turbo4v")["reasons"])
 def test_under_32k_rejected(self):
    p=make();p["context"]=8192
    self.assertIn("context_mismatch",gate.judge(p,"q8k-turbo4v")["reasons"])
 def test_short_prompt_rejected(self):
    p=make();p["comparisons"]["q8k-turbo4v"]["rows"][0]["prompt_tokens"]=2500
    self.assertIn("q8k-turbo4v_long_context_not_measured",gate.judge(p,"q8k-turbo4v")["reasons"])
 def test_no_unsafe_kv(self):
    p=make();p["comparisons"]["q8k-turbo4v"]["K"]="turbo3"
    self.assertIn("unsupported_kv_combination",gate.judge(p,"q8k-turbo4v")["reasons"])
 def test_memory_saving_floor(self):
    p=make();p["comparisons"]["q8k-turbo4v"]["isolated_kv_allocation_mib"]=1500
    self.assertIn("measured_kv_saving_below_20_percent",gate.judge(p,"q8k-turbo4v")["reasons"])

if __name__=="__main__":unittest.main(verbosity=2)
