#!/usr/bin/env python3
"""Synthetic pure-Python regression checks: Hall of Fame promotion is fail-closed."""
import importlib.util
from pathlib import Path
import tempfile
import unittest


SOURCE=Path(__file__).resolve().parents[1]/"scripts"/"hall-performance-gate.py"
spec=importlib.util.spec_from_file_location("hall_performance_gate",SOURCE)
assert spec and spec.loader
g=importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
SHA="f"*64
FIXTURE="e"*64


def make(name="baseline", engine="llama.cpp", *, decode=30.0,prefill=320.,wall=60.,
         quality=94.,gtt=8_000_000_000., modelsha=SHA,quant="Q4_K_M",
         dataset=FIXTURE, protocol="autopublisher-v223-extractor",
         status="validated_in_source"):
    return {
        "id":name, "engine":engine,"model":"Qwen3.8-4B-GGUF",
        "validation":status,
        "configuration":{"base_weights_fingerprint":modelsha,
                         "quantization_scheme":quant},
        "context":{"benchmark_protocol_id":protocol,"fixture_sha256":dataset,
                   "context_tokens":8192},
        "metrics":{"repeated_runs":[
            {"status":"ok","decode_tps":decode,"prefill_tps":prefill,
             "wall_s":wall,"quality_score":quality,"peak_gtt_bytes":gtt}
            for i in range(3)]},
        "sources":["Sources/Benchmarks/podcast-run.json"],
    }


class SafetyTests(unittest.TestCase):
    def test_exact_unchanged_model_passes_numeric_only(self):
        old=make()
        new=make(name="new",decode=31.,prefill=330.,wall=59.,quality=95.,gtt=7.9e9)
        exitcode,result=g.compare(new,[old])
        self.assertEqual(exitcode,0)
        self.assertTrue(all(v["gate_pass"] for v in result["differences"].values()))
        self.assertFalse(result["eligible_for_promotion"])

    def test_cross_engine_same_weights_and_quant_are_comparable(self):
        old=make()
        new=make(name="strata",engine="Strata",decode=35.,wall=57.)
        code,r=g.compare(new,[old])
        self.assertEqual(code,0)
        self.assertEqual(r["reference_id"],old["id"])
        self.assertEqual(r["candidate_engine"],"Strata")

    def test_a_regression_is_not_overlooked_by_good_decode(self):
        old=make()
        new=make(name="regressed",decode=100.,prefill=280.,quality=88.,gtt=9e9)
        code,r=g.compare(new,[old])
        self.assertEqual(code,2)
        self.assertFalse(r["differences"]["prefill_tps"]["gate_pass"])
        self.assertFalse(r["differences"]["quality_score"]["gate_pass"])
        self.assertFalse(r["differences"]["peak_gtt_bytes"]["gate_pass"])

    def test_missing_fingerprint_fails_closed(self):
        new=make(name="new",modelsha="")
        code,r=g.compare(new,[make()])
        self.assertEqual(code,3)
        self.assertIn("Missing fingerprint",r["issues"][0])

    def test_different_quant_fails_closed(self):
        code,r=g.compare(make(name="new",quant="Q5_K_M"),[make()])
        self.assertEqual(code,3)
        self.assertIsNone(r["reference_id"])

    def test_different_podcast_or_protocol_fails_closed(self):
        for opts in ({"dataset":"d"*64},{"protocol":"autoreels-v223"},{"modelsha":"a"*64}):
            with self.subTest(opts=opts):
                code,_=g.compare(make(name="new",**opts),[make()])
                self.assertEqual(code,3)

    def test_single_run_not_sufficient(self):
        new=make(name="new")
        new["metrics"]["repeated_runs"]=new["metrics"]["repeated_runs"][:1]
        code,r=g.compare(new,[make()])
        self.assertEqual(code,3)
        self.assertIn(">=3",r["issues"][0])

    def test_failing_or_missing_any_run_is_not_selectively_skipped(self):
        new=make(name="new")
        new["metrics"]["repeated_runs"][1]["status"]="failed"
        code,r=g.compare(new,[make()])
        self.assertEqual(code,3)
        self.assertIn("Run 2",r["issues"][0])

    def test_pick_fastest_verified_baseline_not_the_slowest(self):
        slow=make("old-slow",wall=80.)
        fast=make("old-fast",wall=60.)
        new=make("new",wall=70.)
        code,r=g.compare(new,[slow,fast])
        self.assertEqual(code,2)
        self.assertEqual(r["reference_id"],fast["id"])

    def test_bad_historical_score_cannot_certify_new_candidate(self):
        candidate=make(name="new")
        old=make("old",status="historical_unconfirmed")
        code,r=g.compare(candidate,[old])
        self.assertEqual(code,3)
        self.assertIsNone(r["reference_id"])

    def test_old_hall_lacks_repeated_runs_so_incomparable(self):
        old=make()
        old["metrics"]={"decode_tps":31}
        code,r=g.compare(make(name="new"),[old])
        self.assertEqual(code,3)
        self.assertFalse(r["eligible_for_promotion"])

    def test_median_not_cherry_pick_outlier(self):
        old=make()
        new=make(name="new",decode=40.)
        new["metrics"]["repeated_runs"][1]["decode_tps"]=5.
        new["metrics"]["repeated_runs"][2]["decode_tps"]=40.
        code,r=g.compare(new,[old])
        self.assertEqual(code,0)
        self.assertEqual(r["differences"]["decode_tps"]["candidate_median"],40.)

    def test_invalid_nan_stats_never_pass(self):
        new=make(name="new",decode=float("nan"))
        code,r=g.compare(new,[make()])
        self.assertEqual(code,3)
        self.assertIn("invalid",r["issues"][0])

    def test_not_certifying_strata_kernel_microseconds(self):
        old=make()
        old["metrics"]={"after_microseconds":11.6}
        code,r=g.compare(make(name="new",engine="Strata"),[old])
        self.assertEqual(code,3)


if __name__=="__main__":
    unittest.main(verbosity=2)
