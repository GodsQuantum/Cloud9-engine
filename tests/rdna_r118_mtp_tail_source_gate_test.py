#!/usr/bin/env python3
"""Guard full RDNA r118 PR206 MTP tail optimization against silent loss.

Does not claim an on-GPU speedup. The native MMB-only chimera is distinct.
"""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class LatestRDNAMTPTailContract(unittest.TestCase):
    def test_current_donor_pinned_and_optimizations_checked(self):
        data=json.loads((ROOT/'tools/benchmarks/latest_engine_sources_20261023.json').read_text())
        rdna=data['github_repositories']['rdna']
        self.assertEqual(rdna['release_tag'],'v14-097cf33d9-r118')
        self.assertEqual(rdna['release_commit'],'989e7bc67135773f30568a996fcaf8861b7c3f08')
        self.assertEqual(len(rdna['patch_sha256']),14)
        workflow=(ROOT/'.github/workflows/hip-r118-gfx1103-latest-lab.yml').read_text()
        for required in ('R118_PATCH_TREE_PASS','LLAMA_MTP_TAIL_READBACK',
                         'prompt_batch_unneeded','llama_set_embeddings_nextn_from',
                         'R118_MTP_TAIL_READBACK_SOURCE_CONTRACT_PASS',
                         'RDNA_NEWER_RELEASE_EXISTS_REPIN_REQUIRED'):
            self.assertIn(required,workflow)
        self.assertNotIn('rdna-r117-patches',workflow)

    def test_native_mmb_is_not_misrepresented_as_full_mtp_hybrid(self):
        m=json.loads((ROOT/'tools/chimera/native-mmb-r118-on-latest4231.json').read_text())
        self.assertEqual(m['donor']['release_tag'],'v14-097cf33d9-r118')
        self.assertEqual(m['port']['resulting_tree'],'2e7bdc4c447c48759e8ba0a5eae8c82d81a27e40')
        self.assertIn('MTP block02 changed',m['port']['latest_r118_byte_identity'])
        self.assertFalse(m['qualification']['production'])
        self.assertFalse(m['qualification']['FlashNext_gt20_certified'])
        self.assertIsNone(json.loads((ROOT/'tools/benchmarks/latest_engine_sources_20261023.json').read_text())['lab_candidate_binary_sha256']['rdna-r118-hip-4b'])

if __name__=='__main__':
    unittest.main(verbosity=2)
