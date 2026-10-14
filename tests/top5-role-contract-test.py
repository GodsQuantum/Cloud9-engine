#!/usr/bin/env python3
"""Pure CPU tests for Cloud9 stable top-five role aliases."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parent
ROLES=ROOT/"config/top5-hof-20261014.json"
CATALOG=ROOT/"config/model-catalog.json"
HALL=PROJECT/"HALL_OF_FAME.json"

class RoleContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roles=json.loads(ROLES.read_text())
        cls.cat=json.loads(CATALOG.read_text())
        cls.hall=json.loads(HALL.read_text()) if HALL.exists() else None
        cls.lookup={m["id"]:m for m in cls.cat["models"]}
    def test_exactly_five_roles(self):
        self.assertEqual(len(self.roles["selection"]),5)
        self.assertEqual(len({x["role_alias"] for x in self.roles["selection"]}),5)
    def test_original_eight_preserved(self):
        self.assertEqual(len(self.lookup),8)
        self.assertEqual(len(self.cat["models"]),8)
    def test_evidence_from_unique_hall_and_no_fabricated_records(self):
        if self.hall is None:
            self.skipTest("Canonical Hall lives in parent project, not standalone engine CI checkout")
        evidence={r["id"]:r for r in self.hall["records"]}
        for row in self.roles["selection"]:
            with self.subTest(role=row["role_alias"]):
                self.assertIn(row["hall_evidence_id"],evidence)
                self.assertEqual(evidence[row["hall_evidence_id"]]["engine_identity"]["family"],"llama.cpp")
                self.assertEqual(row["performance_claim"],"historical only; benchmark protocols differ")
    def test_all_aliases_resolve_to_unique_configured_runtime(self):
        seen={}
        for m in self.cat["models"]:
            for a in [m["id"],*m.get("aliases",[])]:
                self.assertNotIn(a.lower(),seen)
                seen[a.lower()]=m
        for row in self.roles["selection"]:
            with self.subTest(role=row["role_alias"]):
                m=seen[row["role_alias"].lower()]
                self.assertEqual(m["id"],row["model_id"])
                self.assertEqual(m["backend"],row["engine_runtime"])
                self.assertEqual(m["context"],row["context"])
                self.assertEqual(m["gpu_mode"],row["gpu_mode"])
                self.assertTrue(m["model"].startswith("/srv/lxc/ia-compute/data/models/"))
    def test_all_exclusive_large_remain_exclusive(self):
        for row in self.roles["selection"]:
            m=self.lookup[row["model_id"]]
            if m["group"]=="large":self.assertEqual(m["gpu_mode"],"exclusive")
    def test_no_dangerous_default_flags(self):
        self.assertNotIn("RADV_PERFTEST",str(self.cat))
        self.assertEqual(self.cat["defaults"]["max_model_bytes"],42949672960)
        self.assertTrue(self.roles["constraints"]["no_auto_driver_or_mount_changes"])
        self.assertTrue(self.roles["constraints"]["no_auto_model_deletions"])
    def test_prism_and_strata_specialized_not_assumed_equivalent(self):
        others=self.roles["specialized_backends"]
        self.assertIn("prism",others);self.assertIn("strata",others)
        self.assertEqual(others["strata"]["state"].startswith("candidate"),True)
        self.assertNotIn(others["prism"]["model_id"],[x["model_id"] for x in self.roles["selection"]])
    def test_small_bench_requires_future_hardware_validation(self):
        self.assertEqual(self.roles["state"],"validated_for_catalog_routing_not_new_gpu_benchmark")
        for row in self.roles["selection"]:
            self.assertGreater(float(row["historical_decode_tps"]),0)
    def test_named_roles_are_explicit_not_silent_fallbacks(self):
        self.assertEqual(
            {x["role_alias"] for x in self.roles["selection"]},
            {"Cloud9-Fast","Cloud9-Quick","Cloud9-Structured","Cloud9-Deep","Cloud9-Creative"})
if __name__=="__main__":
    unittest.main(verbosity=2)
