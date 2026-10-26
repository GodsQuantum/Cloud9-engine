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

    def test_real_target_and_fr_draft_are_same_architecture(self):
        topo = self.evidence["actual_target_vs_draft_metadata_comparison"]
        self.assertEqual(topo["both_gguf_arch"], "qwen4exp")
        self.assertEqual(topo["target_block_count"] + topo["draft_nextn_predict_layers"], topo["draft_block_count_including_MTP"])
        self.assertEqual(topo["draft_last_MTP_block_index"], topo["target_block_count"])
        self.assertEqual(topo["both_tokenizer_vocab"], self.evidence["target_vocabulary_size"])
        self.assertTrue(topo["structural_relation_correct"])
        self.assertEqual(topo["real_execution_qualification"], "NOT_RUN")

    def test_historical_flashnext_numbers_are_not_new_gpu_measurements(self):
        h = self.evidence["legacy_safe_engine_recovery_audit"]
        self.assertEqual(h["historical_safe_decode_tps"], 17.878)
        self.assertEqual(h["historical_safe_MTP_depth"], 3)
        self.assertFalse(h["historical_GDN_fusion_enabled"])
        self.assertFalse(h["source_commit_resolved"])
        self.assertFalse(h["historical_commit_embedded_found"])
        self.assertIsNone(self.evidence["actual_flashnext_tps"])

    def test_qa_evidence_files_exist(self):
        for rel in self.evidence["test_logs"]:
            self.assertTrue((R / rel).is_file(), rel)
        log = (R / self.evidence["test_logs"][1]).read_text()
        self.assertIn("QWEN4EXP MTP-only sidecar cannot run as target model", log)

if __name__ == "__main__":
    unittest.main()
