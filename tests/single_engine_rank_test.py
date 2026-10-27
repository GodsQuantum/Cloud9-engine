#!/usr/bin/env python3
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from single_engine_rank import evaluate,rank
def example(name="ok"):
    return {"identity":{"id":name,"engine":"test","model":"synthetic",
            "quant":"Q4","model_sha256":"a"*64,"engine_sha256":"b"*64},
        "hardware":"Cloud9 Radeon 780M gfx1103","repetitions":3,
        "speculation":{"native_supported":True,"enabled":True,
                       "draft_proposed":100,"draft_accepted":45},
        "quality":{k:{"n":10,"correct":10} for k in ("json","tools","code","fr")},
        "context":[{"observed_prompt_tokens":32768,"retrieval_trials":10,
                    "retrieval_correct":10,"positions":5,"no_truncation_proven":True}],
        "performance":{"decode_tps":30,"prefill_tps":350,"time_to_correct_tool_s":4},
        "safety":{"device_lost":False,"oom":False,"service_regression":False,
                  "peak_tctl_c":70,"peak_host_ram_gib":20},
        "openai_native_tools_ok":True}
class TestGate(unittest.TestCase):
    def test_qualifies(self):self.assertTrue(evaluate(example())["eligible"])
    def test_mtp_must_be_effective(self):
        a=example();a["speculation"]["draft_accepted"]=0
        self.assertFalse(evaluate(a)["eligible"])
    def test_bad_tools_beats_no_score(self):
        a=example();a["quality"]["tools"]["correct"]=9;a["performance"]["decode_tps"]=500
        self.assertFalse(evaluate(a)["eligible"])
    def test_allocate_does_not_prove_context(self):
        a=example();a["context"][0]["no_truncation_proven"]=False
        self.assertEqual(evaluate(a)["context"],0)
    def test_thermal_guard(self):
        a=example();a["safety"]["peak_tctl_c"]=80
        self.assertFalse(evaluate(a)["eligible"])
    def test_one_no_champion(self):
        self.assertEqual(rank({"schema_version":1,"candidates":[example()]})["status"],"UNPROVEN")
    def test_pareto_tradeoff(self):
        a=example("fast");b=example("long")
        b["context"][0]["observed_prompt_tokens"]=65536
        b["performance"]["decode_tps"]=22
        self.assertEqual(set(rank({"schema_version":1,"candidates":[a,b]})["pareto"]),{"fast","long"})
    def test_dominated_excluded(self):
        a=example("fast");b=example("slow")
        b["performance"]["decode_tps"]=20
        self.assertEqual(rank({"schema_version":1,"candidates":[a,b]})["pareto"],["fast"])
if __name__=="__main__":unittest.main(verbosity=2)
