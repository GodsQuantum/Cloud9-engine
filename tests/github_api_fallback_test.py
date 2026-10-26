"""Offline regression for current-source GitHub REST authentication fallback."""
import importlib.util
import io
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "tools/benchmarks/verify_latest_sources.py"
spec = importlib.util.spec_from_file_location("freshness_gate_under_test", SOURCE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class Response(io.BytesIO):
    status = 200
    def __enter__(self): return self
    def __exit__(self, *_): self.close()


class GithubRestFallbackTests(unittest.TestCase):
    def unauth(self):
        return subprocess.CompletedProcess(["gh", "api"], 4, "", "please run: gh auth login")

    def test_unauthenticated_reads_real_api_shape(self):
        with patch.object(gate.subprocess, "run", return_value=self.unauth()):
            with patch.object(gate, "urlopen", return_value=Response(b'{"object":{"sha":"a"}}')) as m:
                data = gate.github_api("repos/ggml-org/llama.cpp/git/ref/heads/master")
                self.assertEqual(data["object"]["sha"], "a")
                self.assertEqual(m.call_args[0][0].full_url, "https://api.github.com/repos/ggml-org/llama.cpp/git/ref/heads/master")

    def test_bad_json_fails_closed(self):
        with patch.object(gate.subprocess, "run", return_value=self.unauth()):
            with patch.object(gate, "urlopen", return_value=Response(b'not-json')):
                with self.assertRaises(gate.UnverifiedSource):
                    gate.github_api("repos/ggml-org/llama.cpp/releases/latest")

    def test_overlong_rest_response_fails_closed(self):
        with patch.object(gate.subprocess, "run", return_value=self.unauth()):
            with patch.object(gate, "urlopen", return_value=Response(b"x" * (1024 * 1024 + 1))):
                with self.assertRaisesRegex(gate.UnverifiedSource, "RESPONSE_TOO_LARGE"):
                    gate.github_api("repos/ggml-org/llama.cpp/releases/latest")

    def test_http_failure_fails_closed(self):
        from urllib.error import HTTPError
        with patch.object(gate.subprocess, "run", return_value=self.unauth()):
            with patch.object(gate, "urlopen", side_effect=HTTPError("https://api.github.com", 403, "rate limit", None, None)):
                with self.assertRaises(gate.UnverifiedSource):
                    gate.github_api("repos/ggml-org/llama.cpp/releases/latest")

    def test_authenticated_server_failure_no_anonymous_downgrade(self):
        failure = subprocess.CompletedProcess(["gh","api"], 1, "", "HTTP 500")
        with patch.object(gate.subprocess, "run", return_value=failure):
            with patch.object(gate, "urlopen") as m:
                with self.assertRaises(gate.UnverifiedSource):
                    gate.github_api("repos/ggml-org/llama.cpp/releases/latest")
                m.assert_not_called()

    def test_path_rejected_before_rest(self):
        with patch.object(gate.subprocess, "run", return_value=self.unauth()):
            with patch.object(gate, "urlopen") as m:
                with self.assertRaises(gate.UnverifiedSource):
                    gate.github_api("repos/example/x/../git/ref/heads/master")
                m.assert_not_called()


if __name__ == "__main__":
    unittest.main()
