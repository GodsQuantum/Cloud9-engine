import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class FlashNextAD427StorageBreakdownTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads((ROOT/'certification/flashnext_ad427_storage_breakdown_20261027.json').read_text())

    def test_exact_shards_and_arch_weights(self):
        d=self.d
        self.assertEqual(d['source_files'],33)
        self.assertEqual(d['source_bytes'],94525394976)
        self.assertEqual(d['total_tensors'],1224)
        self.assertEqual(d['n_gram_tensor']['name'],'per_layer_token_embd.weight')
        self.assertEqual(d['n_gram_tensor']['bytes'],38400184320)
        self.assertEqual(d['n_gram_tensor']['shape'],[160,320001536])

    def test_expected_residency_classes_are_distinct(self):
        c=self.d['classes']
        self.assertEqual(c['ngram_table']['tensors'],1)
        self.assertEqual(c['MoE_expert_weights']['tensors'],144)
        self.assertEqual(c['other_weights']['tensors'],1079)
        self.assertEqual(c['MoE_expert_weights']['bytes'],50646220800)
        self.assertEqual(c['other_weights']['bytes'],5467962880)
        self.assertLess(self.d['source_bytes']-sum(v['bytes'] for v in c.values()),16_000_000)
        self.assertFalse(self.d['GPU_execution_performed'])
        self.assertTrue(self.d['exact_quantization_preserved'])

if __name__=='__main__':unittest.main()
