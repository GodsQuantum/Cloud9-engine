import hashlib
import json
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]

class FRSPECNativePatchProofTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((R / "certification/flashnext_frspec_native_qualification_20261026.json").read_text())
        cls.patch = R / cls.evidence["patch"]

    def test_source_patch_integrity(self):
        self.assertEqual(hashlib.sha256(self.patch.read_bytes()).hexdigest(), self.evidence["patch_sha256"])
        s = self.patch.read_text()
        for component in ("LLM_TENSOR_NEXTN_FC_EMBD", "LLM_TENSOR_NEXTN_FC_HIDDEN", "GGML_TYPE_I64", "ggml_set_rows", "GGML_TYPE_F32", "MTP-only sidecar"):
            self.assertIn(component, s)

    def test_real_gguf_proof_and_no_false_benchmark(self):
        e = self.evidence
        self.assertEqual(e["sidecar_tensor_count"], 36)
        self.assertEqual(e["target_vocabulary_size"], 248320)
        self.assertEqual(e["draft_output_vocabulary_size"], 65536)
        self.assertEqual(e["d2t_unique_entries"], e["d2t_entries"])
        self.assertTrue(e["d2t_within_target_vocab"])
        self.assertLess(e["d2t_max"], e["target_vocabulary_size"])
        self.assertEqual(e["actual_matched_target_plus_frspec_inference"], "NOT_EXECUTED")
        self.assertIsNone(e["actual_flashnext_tps"])
        self.assertFalse(e["production_mutated"])

    def test_qa_evidence_files_exist(self):
        for rel in self.evidence["test_logs"]:
            self.assertTrue((R / rel).is_file(), rel)
        log = (R / self.evidence["test_logs"][1]).read_text()
        self.assertIn("QWEN4EXP MTP-only sidecar cannot run as target model", log)

if __name__ == "__main__":
    unittest.main()
