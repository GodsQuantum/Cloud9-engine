#!/usr/bin/env python3
"""Only source provenance/port-gating QA; cannot substitute for GPU benchmark."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class NativeMMBCurrentSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads((ROOT/'tools/chimera/native-mmb-r120-on-latest062.json').read_text())
        cls.lock=json.loads((ROOT/'tools/benchmarks/latest_engine_sources_20261023.json').read_text())
        cls.ci=(ROOT/'.github/workflows/lab-native-chimera-mmb-r120-on-latest.yml').read_text()

    def test_port_is_from_actual_latest_donor_and_trunk(self):
        self.assertEqual(self.m['base']['commit'],self.lock['github_repositories']['upstream']['commit'])
        self.assertIn(self.m['base']['commit'],self.ci)
        self.assertNotIn('f50249819ccbf67a710f9a1927080e25775651ef',self.ci)
        self.assertEqual(self.m['donor']['commit'],self.lock['github_repositories']['rdna']['release_commit'])
        self.assertEqual(self.m['donor']['release_tag'],self.lock['github_repositories']['rdna']['release_tag'])
        self.assertEqual(self.m['donor']['release_tag'],'v14-097cf33d9-r120')

    def test_exact_manifest_hashes(self):
        self.assertRegex(self.m['donor']['sha256'],r'^[0-9a-f]{64}$')
        self.assertRegex(self.m['port']['resulting_tree'],r'^[0-9a-f]{40}$')
        self.assertEqual(self.m['port']['source_commit_local'],'ae6c3d07ee54723b719dd4a4e79a3af744c0f186')
        self.assertEqual(self.m['port']['files_ported'],6)

    def test_donor_is_compatible_and_gpu_tests_still_missing(self):
        self.assertIn('MIT',self.m['port']['libraries'])
        self.assertEqual(self.m['port']['backend'],'HIP gfx1103 (NOT GPU-verified)')
        self.assertFalse(self.m['qualification']['compile'])
        self.assertFalse(self.m['qualification']['rocm_lab_abi_pass'])
        self.assertFalse(self.m['qualification']['on_device'])
        self.assertFalse(self.m['qualification']['benchmark'])
        self.assertFalse(self.m['qualification']['production'])

    def test_ci_builds_on_runner_not_local_cloud9(self):
        self.assertIn('ubuntu-24.04',self.ci)
        self.assertNotIn("m['qualification']['compile'] is False",self.ci)
        self.assertIn('GPU_TARGETS=gfx1103',self.ci)
        self.assertIn('verify_latest_sources.py --all',self.ci)
        self.assertIn('MMB_KERNEL_NOT_COMPILED',self.ci)
        self.assertIn('MMF32_KERNEL_NOT_COMPILED',self.ci)
        self.assertIn('tree!=m[',self.ci)
        self.assertIn('NOT-QUALIFIED.txt',self.ci)
        self.assertIn('--exclude=tests/CMakeLists.txt',self.ci)

    def test_native_062_cuda_graph_chunking_fix(self):
        import hashlib
        repair=self.m['port']['post_port_fix']
        p=ROOT/repair['patch']
        self.assertTrue(p.is_file())
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),repair['sha256'])
        self.assertEqual(repair['resulting_tree'],'a6c565a3d4928482fed05fdd5fe23a239dab9116')
        self.assertIn('graph->instances.empty()',p.read_text())
        self.assertIn('Repair upstream CUDA graph chunk invalidation',self.ci)
        self.assertIn('DA2_CUDA_GRAPH_INSTANCES_FIX_SOURCE_TREE_PASS',self.ci)
        self.assertFalse(self.m['qualification']['production'])

    def test_cannot_be_a_production_candidate_just_by_compiling(self):
        self.assertNotIn('native-mmb',self.lock['lab_candidate_binary_sha256'])
        self.assertFalse(self.m['qualification']['production'])
        self.assertFalse(self.m['qualification']['benchmark'])

if __name__=='__main__':
    unittest.main(verbosity=2)
