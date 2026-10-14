#!/usr/bin/env python3
"""Smoke actual model-router /v1/models without GPU or model loading."""
import json
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "bin/cloud9-model-router.py"
CATALOG = ROOT / "config/model-catalog.json"


def endpoint(url):
    with urllib.request.urlopen(url, timeout=2) as resp:
        return json.load(resp)


class SpecialtyContract(unittest.TestCase):
    def test_real_http_catalog_and_legacy_compat(self):
        expected = json.loads(CATALOG.read_text())["models"]
        self.assertEqual(len(expected), 8)
        self.assertEqual(len({m["id"].casefold() for m in expected}), 8)
        # Separate ephemeral local listener; no CT410 listener, GPU or model involved.
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        with tempfile.TemporaryDirectory(prefix="cloud9-model-catalog-test-") as home:
            cmd = [sys.executable, "-B", str(ROUTER), "--host", "127.0.0.1",
                   "--port", str(port), "--engine-home", home, "--catalog", str(CATALOG)]
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            try:
                root = f"http://127.0.0.1:{port}"
                for _ in range(40):
                    if proc.poll() is not None:
                        raise AssertionError("router exited before readiness")
                    try:
                        result = endpoint(root + "/v1/models")
                        break
                    except (OSError, urllib.error.URLError):
                        time.sleep(0.05)
                else:
                    self.fail("model router did not listen on ephemeral port")
                rows = result["data"]
                self.assertEqual(len(rows), 8)
                self.assertEqual([x["id"] for x in rows], [x["id"] for x in expected])
                for item, original in zip(rows, expected, strict=True):
                    with self.subTest(model=item["id"]):
                        self.assertEqual(item["name"], original["display_name"])
                        self.assertEqual(item["cloud9"]["specialty"], original["specialty"])
                        self.assertEqual(item["cloud9"]["aliases"], original["aliases"])
                        # The legacy ID and human-friendly specialty ID must resolve identically.
                        for alias in (original["id"], original["aliases"][-1]):
                            resolved = endpoint(root + "/v1/models/" + alias)
                            self.assertEqual(resolved["id"], original["id"])
                            self.assertEqual(resolved["name"], original["display_name"])
            finally:
                proc.terminate()
                try:
                    proc.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
