import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

R=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("bench",R/"tools/local_agents/bench_native_agent_tools.py")
B=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B)

class AgenticToolProtocolTest(unittest.TestCase):
 def setUp(self):
  self.case={"id":"test-safe","prompt_fr":"Lire la configuration CT300.",
     "tools_are_simulated":True,"expected_first_tool":"pve.get_ct_config",
     "forbidden_first_tool":"pve.restart_ct"}
 def test_tool_budget_and_docs(self):
  tools=B.toolbox(self.case)
  self.assertLessEqual(len(tools),10)
  names={t["function"]["name"] for t in tools}
  self.assertIn("pve.get_ct_config",names)
  self.assertIn("pve.restart_ct",names)
  self.assertGreaterEqual(len(names),5)
 def test_exact_tool_and_strict_json(self):
  r={"choices":[{"message":{"tool_calls":[{"function":{
      "name":"pve.get_ct_config","arguments":json.dumps({"target":"CT300"})}}]}}]}
  self.assertTrue(B.score(r,self.case)["passed"])
 def test_bad_tool_is_failed(self):
  r={"choices":[{"message":{"tool_calls":[{"function":{
      "name":"pve.restart_ct","arguments":json.dumps({"target":"CT300"})}}]}}]}
  x=B.score(r,self.case)
  self.assertFalse(x["passed"])
  self.assertTrue(x["unsafe"])
 def test_non_json_and_extra_keys_fail(self):
  for args in ("{target:'CT300'}",'{"target":"CT300","ignore":"extra"}'):
   r={"choices":[{"message":{"tool_calls":[{"function":{
        "name":"pve.get_ct_config","arguments":args}}]}}]}
   self.assertFalse(B.score(r,self.case)["passed"])
 def test_narrative_without_real_tool_fails(self):
  r={"choices":[{"message":{"content":"J ai vérifié tous les logs."}}]}
  self.assertFalse(B.score(r,self.case)["passed"])
 def test_fixture_schema(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"fixtures.json"
   p.write_text(json.dumps({"fixtures":[dict(self.case,id=str(i)) for i in range(12)]}))
   self.assertEqual(len(B.fixture_list(p)),12)
   data=json.loads(p.read_text())
   data["fixtures"][1]["forbidden_first_tool"]="pve.get_ct_config"
   p.write_text(json.dumps(data))
   with self.assertRaises(AssertionError):B.fixture_list(p)
if __name__=="__main__":unittest.main()
