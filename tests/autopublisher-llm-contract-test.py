#!/usr/bin/env python3
"""Offline AutoPublisher export contract tests: no secrets, GPU, n8n or HTTP."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "autopublisher-llm-contract.py"
spec = importlib.util.spec_from_file_location("autopublisher_contract", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def make_node(name, content, *, model="Flash", url="http://127.0.0.1:20128/v1/chat/completions"):
    json_text = json.dumps(content, ensure_ascii=False)
    expression = (
        "={{ JSON.stringify({model:'" + model + "',temperature:0.15,"
        "max_tokens:4200,response_format:{type:'json_object'},"
        "messages:[{role:'system',content:" + json_text +
        "},{role:'user',content:JSON.stringify({transcript_pack:$json.transcript_pack})}]}) }}"
    )
    return {
        "name": name, "type": "n8n-nodes-base.httpRequest",
        "parameters": {"jsonBody": expression, "method": "POST",
                       "specifyBody": "json", "sendBody": True, "url": url,
                       "options": {"timeout": 120000}},
    }


class ContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        (self.folder / "editorial_extractor_prompt.md").write_text("EDITORIAL",encoding="utf-8")
        (self.folder / "voice_copy_pack_prompt.md").write_text("COPY",encoding="utf-8")
        self.workflow = {"name": "offline fixture", "active": False,
                         "nodes": [
                             make_node("Editorial Extractor", "EDITORIAL"),
                             make_node("Voice Copy Pack", "COPY"),
                             make_node("Repair Copy", "COPY"),
                         ]}

    def test_exact_prompts_and_transport(self):
        report = module.inspect(self.workflow, self.folder)
        self.assertTrue(report["prompt_matches"])
        self.assertTrue(report["schema_transport_valid"])
        self.assertEqual([v["model_alias"] for v in report["llm_nodes"]],["Flash"]*3)
        self.assertTrue(report["source_is_file_snapshot_not_live_n8n_status"])
        self.assertFalse(report["workflow_is_marked_active_in_export"])

    def test_prompt_drift_detected_even_when_rest_are_identical(self):
        self.workflow["nodes"][0] = make_node("Editorial Extractor", "OLD")
        report = module.inspect(self.workflow, self.folder)
        self.assertFalse(report["prompt_matches"])
        self.assertFalse(report["llm_nodes"][0]["prompt_matches_canonical"])
        self.assertTrue(all(v["prompt_matches_canonical"] for v in report["llm_nodes"][1:]))

    def test_never_put_raw_prompt_or_token_in_summary(self):
        secret_marker = "SENSITIVE_FIXTURE_DO_NOT_EMIT"
        (self.folder / "editorial_extractor_prompt.md").write_text(secret_marker)
        self.workflow["nodes"][0] = make_node("Editorial Extractor", secret_marker)
        report = module.inspect(self.workflow, self.folder)
        data = json.dumps(report)
        self.assertNotIn(secret_marker,data)
        self.assertNotIn("transcript_pack:$json.transcript_pack",data)

    def test_missing_or_duplicate_llm_node_rejected(self):
        with self.assertRaisesRegex(ValueError,"Missing required nodes"):
            module.inspect({"nodes":self.workflow["nodes"][:2]},self.folder)
        with self.assertRaisesRegex(ValueError,"Duplicate LLM node"):
            module.inspect({"nodes":self.workflow["nodes"]*2},self.folder)

    def test_invalid_transport_flagged_without_network_access(self):
        self.workflow["nodes"][0] = make_node("Editorial Extractor","EDITORIAL",url="file:///tmp/not-a-server")
        report = module.inspect(self.workflow,self.folder)
        self.assertFalse(report["schema_transport_valid"])
        self.assertFalse(report["llm_nodes"][0]["valid_http_only"])

    def test_no_hidden_model_alias_switch(self):
        self.workflow["nodes"][0]["parameters"]["jsonBody"] = (
            self.workflow["nodes"][0]["parameters"]["jsonBody"]
            .replace("model:'Flash'","model:$json.provider_secret"))
        with self.assertRaisesRegex(ValueError,"expected exactly one"):
            module.inspect(self.workflow,self.folder)


if __name__=="__main__":
    unittest.main(verbosity=2)
