#!/usr/bin/env python3
"""Release lock tests. No GPU, downloads, credentials or production writes."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "sources.lock").read_text())
DOC = (ROOT / "docs/backend-qualification-20261016.md").read_text()

class BackendReleaseGate(unittest.TestCase):
    def test_atomic_source_pinned_not_transplanted(self):
        atomic = LOCK["atomic"]
        self.assertEqual(atomic["repository"], "https://github.com/AtomicBot-ai/atomic-llama-cpp-turboquant.git")
        self.assertEqual(atomic["branch"], "master")
        # Releases advance; never hard-code a past release or commit here.
        self.assertRegex(atomic["release"], r"\Ab[0-9]+-[0-9]+\.[0-9]+\.[0-9]+\Z")
        self.assertRegex(atomic["commit"], r"\A[0-9a-f]{40}\Z")
        self.assertIn("candidate_only", atomic["qualification"])
        self.assertNotEqual(atomic["commit"], LOCK["upstream"]["commit"])

    def test_rejected_v070_separate_from_production(self):
        candidate = LOCK["upstream_candidate"]
        self.assertEqual(candidate["tag"], "v0.7.0")
        self.assertEqual(candidate["commit"], "620d2225cc436ab0b001e3200e590e3b286ef9ab")
        self.assertEqual(candidate["status"], "long_context_regression_not_promoted")
        self.assertNotEqual(LOCK["upstream"]["commit"], candidate["commit"])
        self.assertEqual(LOCK["patchset"], "patches/upstream-latest")

    def test_no_claims_of_strata_or_atomic_production(self):
        self.assertIn("no final generated token", DOC)
        self.assertIn("Not promoted", DOC)
        self.assertIn("16K/32K", DOC)
        self.assertIn("GPU memory guard", DOC)
        self.assertIn("single", DOC)
        self.assertIn("1024-dimensional", DOC)

    def test_no_private_paths_in_doc(self):
        for fragment in ("/home/", "/srv/", "192.168.", "password=", "api_key=", "@gmail."):
            self.assertNotIn(fragment, DOC)

if __name__ == "__main__":
    unittest.main(verbosity=2)
