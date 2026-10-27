import ast
import io
import json
import pathlib
import unittest
import urllib.request
from unittest import mock

SOURCE=pathlib.Path(__file__).resolve().parents[1]/"bin/cloud9-model-router.py"

def subject():
    tree=ast.parse(SOURCE.read_text())
    fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="embedding_busy")
    ns={"urllib":urllib,"json":json,"EMBED_ENDPOINT":"http://192.168.1.219:8091"}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(SOURCE),"exec"),ns)
    return ns["embedding_busy"]

class EmbeddingBusySafety(unittest.TestCase):
    def test_actual_bind_address(self):
        t=SOURCE.read_text()
        self.assertIn('"http://192.168.1.219:8091"',t)
        self.assertNotIn('urlopen("http://127.0.0.1:8091/slots"',t)
    def test_processing_is_busy(self):
        with mock.patch("urllib.request.urlopen",return_value=io.BytesIO(json.dumps([{"is_processing":True},{"is_processing":False}]).encode())) as f:
            self.assertTrue(subject()())
            self.assertEqual(f.call_args.args[0],"http://192.168.1.219:8091/slots")
    def test_idle_means_safe(self):
        with mock.patch("urllib.request.urlopen",return_value=io.BytesIO(json.dumps([{"is_processing":False,"state":"idle"},{"is_processing":False,"state":"idle"}]).encode())):
            self.assertFalse(subject()())
    def test_fail_closed_unreachable(self):
        with mock.patch("urllib.request.urlopen",side_effect=OSError("offline")):
            self.assertTrue(subject()())
    def test_fail_closed_unknown_state(self):
        for sample in ({},[],[None],{"is_processing":False}):
            with self.subTest(sample=sample),mock.patch("urllib.request.urlopen",return_value=io.BytesIO(json.dumps(sample).encode())):
                self.assertTrue(subject()())
    def test_fail_closed_malformed_json(self):
        with mock.patch("urllib.request.urlopen",return_value=io.BytesIO(b"not-json")):
            self.assertTrue(subject()())
