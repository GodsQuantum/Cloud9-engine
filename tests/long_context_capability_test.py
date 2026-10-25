import importlib.util
import pathlib
import struct
import tempfile
import unittest

FILE=pathlib.Path(__file__).resolve().parents[1]/"tools/qualification/long_context_capability.py"
spec=importlib.util.spec_from_file_location("long_context_capability",FILE)
c=importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

def stub_gguf(path,arch="qwen35",context=262144):
    parts=[]
    def item(key,val,kind):
        key=key.encode();out=struct.pack("<Q",len(key))+key+struct.pack("<I",kind)
        if kind==8:
            val=val.encode();return out+struct.pack("<Q",len(val))+val
        return out+struct.pack("<"+{4:"I",10:"Q"}[kind],val)
    parts=[
      item("general.architecture",arch,8),item("general.name","fixture",8),
      item("qwen35.context_length",context,10),item("qwen35.block_count",33,4),
      item("qwen35.full_attention_interval",4,4),
      item("qwen35.attention.head_count_kv",4,4),
      item("qwen35.attention.key_length",256,4),
      item("qwen35.attention.value_length",256,4)]
    path.write_bytes(b"GGUF"+struct.pack("<IQQ",3,0,len(parts))+b"".join(parts))

class LongContextCapability(unittest.TestCase):
    def test_read_realistic_gguf_header_without_weights(self):
        with tempfile.TemporaryDirectory() as temp:
            path=pathlib.Path(temp)/"fixture.gguf";stub_gguf(path)
            data=c.metadata(path)
            self.assertEqual(data["qwen35.context_length"],262144)
            self.assertEqual(data["general.architecture"],"qwen35")
    def test_context_window_estimates_not_a_certification(self):
        with tempfile.TemporaryDirectory() as temp:
            path=pathlib.Path(temp)/"fixture.gguf";stub_gguf(path)
            r=c.report(path)
            self.assertEqual(len(r["context_envelope"]),6)
            self.assertEqual(r["policy"]["agentic_target"].split()[0],"128K")
            self.assertFalse(r["policy"]["production_promoted"])
            self.assertFalse(r["policy"]["full_inference_above_8k_certified"])
            for x in r["context_envelope"]:
                self.assertLess(x["estimated_KV_q8_0_GiB"],x["estimated_KV_f16_GiB"])
                self.assertEqual(x["evidence_class"],"THEORETICAL_APPROXIMATION_NOT_GPU_CERTIFICATION")
    def test_reject_short_native_context(self):
        with tempfile.TemporaryDirectory() as temp:
            path=pathlib.Path(temp)/"fixture.gguf";stub_gguf(path,context=16384)
            with self.assertRaises(AssertionError):c.report(path)
    def test_reject_mismatched_architecture(self):
        with tempfile.TemporaryDirectory() as temp:
            path=pathlib.Path(temp)/"fixture.gguf";stub_gguf(path,arch="llama")
            with self.assertRaisesRegex(ValueError,"ONLY_QWEN35"):c.report(path)
    def test_reject_bad_magic(self):
        with tempfile.TemporaryDirectory() as temp:
            path=pathlib.Path(temp)/"fixture.gguf";path.write_bytes(b"nope")
            with self.assertRaisesRegex(ValueError,"INVALID_GGUF"):c.metadata(path)
    def test_estimates_are_monotonic(self):
        with tempfile.TemporaryDirectory() as temp:
            path=pathlib.Path(temp)/"fixture.gguf";stub_gguf(path)
            out=c.report(path)["context_envelope"]
            self.assertEqual([x["tokens"] for x in out],[8192,16384,32768,65536,131072,262144])
            self.assertEqual([x["estimated_KV_f16_GiB"] for x in out],sorted(x["estimated_KV_f16_GiB"] for x in out))

if __name__=="__main__":
    unittest.main()
