#!/usr/bin/env python3
"""Strict offline integrity rules for resuming interrupted GPU quality trials."""
import copy
import importlib.util
from pathlib import Path
import unittest

p=Path(__file__).resolve().parents[1]/"tools/benchmarks/live_quality12_mtp_20261022.py"
spec=importlib.util.spec_from_file_location("benchmark",p)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
CASES=[{"id":"j_sum"},{"id":"t_read"},{"id":"c_add"}]
EXPECTED={"candidate":"b11798-hermes9b","engine_sha256":"abc",
          "model":"qwen9b.gguf","model_bytes":123,"repetitions_requested":3,
          "protocol":{"version":1}}
def partial(rows=(),status="starting"):
    return {**EXPECTED,"status":status,"rows":list(rows),"error":"previous interrupted"}
def row(case="j_sum",rep=1,error=None):
    return {"id":case,"rep":rep,"correct":False,"error":error}

class ResumeEvidenceTest(unittest.TestCase):
    def resume(self,j):
        return mod.prepare_resume(copy.deepcopy(j),EXPECTED,CASES,3)
    def test_skips_existing_success(self):
        a,complete=self.resume(partial([row(),row("t_read")]))
        self.assertEqual(complete,{(1,"j_sum"),(1,"t_read")})
        self.assertEqual(a["status"],"resuming")
        self.assertEqual(len(a["rows"]),2)
        self.assertNotIn("error",a)
    def test_mismatched_model_refused(self):
        a=partial([row()])
        a["model"]="different.gguf"
        with self.assertRaises(AssertionError):self.resume(a)
    def test_mismatched_engine_hash_refused(self):
        a=partial([row()])
        a["engine_sha256"]="changed"
        with self.assertRaises(AssertionError):self.resume(a)
    def test_mismatched_protocol_refused(self):
        a=partial([row()])
        a["protocol"]={"version":2}
        with self.assertRaises(AssertionError):self.resume(a)
    def test_duplicate_id_refused(self):
        with self.assertRaises(AssertionError):self.resume(partial([row(),row()]))
    def test_invalid_case_id_refused(self):
        with self.assertRaises(AssertionError):self.resume(partial([row("outside")]))
    def test_invalid_repetition_refused(self):
        with self.assertRaises(AssertionError):self.resume(partial([row(rep=99)]))
    def test_error_row_is_queued_for_retrial(self):
        a,complete=self.resume(partial([row(),row("t_read",error="network")]))
        self.assertEqual(complete,{(1,"j_sum")})
        self.assertEqual(len(a["retry_history"]),1)
        self.assertEqual(len(a["rows"]),1)
    def test_reject_finished(self):
        with self.assertRaises(AssertionError):self.resume(partial([row()],"complete_editorial_review_pending"))
    def test_reject_all_completed_even_wrong_status(self):
        rows=[row(case,rep) for rep in range(1,4) for case in ("j_sum","t_read","c_add")]
        with self.assertRaises(AssertionError):self.resume(partial(rows))
    def test_resuming_state_allowed(self):
        a,b=self.resume(partial([row()],"resuming"))
        self.assertEqual(len(b),1)
    def test_does_not_modify_source_evidence(self):
        original=partial([row(),row("t_read",error="lost")])
        a,b=self.resume(original)
        self.assertEqual(len(original["rows"]),2)
        self.assertEqual(original["status"],"starting")

if __name__=="__main__":
    unittest.main(verbosity=2)
