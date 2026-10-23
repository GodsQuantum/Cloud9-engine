#!/usr/bin/env python3
"""Repo CI may audit historical pin drift, but never bypass live per-candidate gates."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
CI=(ROOT/'.github/workflows/ci.yml').read_text()
SOURCE=(ROOT/'tools/benchmarks/verify_latest_sources.py').read_text()
HIP=(ROOT/'.github/workflows/lab-native-chimera-r120-master9ff-hip.yml').read_text()
VULKAN=(ROOT/'.github/workflows/lab-latest-upstream-master9ff-vulkan.yml').read_text()
class HistoricalPinPolicy(unittest.TestCase):
    def test_ci_static_and_compile_not_blocked_by_historical_head_drift(self):
        self.assertIn('Audit live source freshness (advisory;', CI)
        self.assertIn('if python3 tools/benchmarks/verify_latest_sources.py --all',CI)
        self.assertIn('Live source audit exit $rc',CI)
        self.assertIn('Static checks',CI)
        self.assertIn('Apply Cloud9 patchset to locked upstream',CI)
    def test_actual_source_gate_still_fails_closed(self):
        self.assertIn('STALE_FAIL_CLOSED:',SOURCE)
        self.assertIn('UNVERIFIED_FAIL_CLOSED:',SOURCE)
        self.assertIn('UPSTREAM_MOVED_REPIN_REQUIRED',HIP)
        self.assertIn('UPSTREAM_MOVED_REPIN_REQUIRED',VULKAN)
        self.assertIn('RDNA_DONOR_MOVED_REPIN_REQUIRED',HIP)
        self.assertNotIn('continue-on-error: true',HIP)
        self.assertNotIn('continue-on-error: true',VULKAN)
if __name__=='__main__':
    unittest.main(verbosity=2)
