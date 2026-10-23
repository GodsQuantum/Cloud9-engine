#!/usr/bin/env python3
"""No GPU: pin and source-integrity contract for master9ff RDNA r120 MMB candidate."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tools/chimera/native-mmb-r120-on-latest9ff.json'
CI = ROOT / '.github/workflows/lab-native-chimera-r120-master9ff-hip.yml'


class NativeChimeraMaster9ffContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = json.loads(SOURCE.read_text())
        cls.ci = CI.read_text()

    def test_provenance_and_trees(self):
        m = self.meta
        self.assertEqual(m['base']['commit'], '9ff0d7e90f0faaa7c16017e6dcf9cf91c50a100e')
        self.assertEqual(m['base']['tree'], '60bf42018da47404b7260ee2bebd108b6c1b511f')
        self.assertEqual(m['port']['resulting_tree'], '73feeff15bdf0194fa14eec88f70dfc5d1c0750f')
        self.assertEqual(m['donor']['commit'], 'ece2d7531b8630413770f61db46ff0700e6a8999')
        self.assertEqual(m['donor']['sha256'], '3d98feb0cd211ee5e8cb5919023c04f9a298e7f9f2be422541552fa93be039c2')

    def test_upstream_fix_not_overlaid(self):
        guard = self.meta['port']['upstream_native_cuda_graph_fix']
        self.assertEqual(guard['predicate'], 'n_captured += graph->instances.size();')
        self.assertFalse(guard['local_patch_required'])
        self.assertIn('UPSTREAM_GRAPH_FIX_NATIVE', self.ci)
        self.assertNotIn('git apply', self.ci.split('- name: Verify upstream CUDA graph fix already present')[1].split('- name: Install ROCm')[0])

    def test_locked_ci_no_false_gpu_certification(self):
        self.assertIn('UPSTREAM_MOVED_REPIN_REQUIRED', self.ci)
        self.assertIn('RDNA_DONOR_MOVED_REPIN_REQUIRED', self.ci)
        self.assertIn('-DGGML_HIP=ON', self.ci)
        self.assertIn('GPU_TARGETS=gfx1103', self.ci)
        self.assertIn('sha256sum', self.ci)
        self.assertFalse(self.meta['qualification']['compile'])
        self.assertFalse(self.meta['qualification']['on_device'])
        self.assertFalse(self.meta['qualification']['production'])
        self.assertFalse(self.meta['qualification']['FlashNext_gt20_certified'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
