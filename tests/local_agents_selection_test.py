import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"tools/local_agents/model_routing_selection_20261024.json"
class SelectionTest(unittest.TestCase):
 def test_role_ids(self):
  m=json.loads(PATH.read_text())
  roles={x["role"]:x for x in m["roles"]}
  self.assertEqual(set(roles),{"fast_extract","structured_tools","complex_reasoning","uncensored_complex"})
  self.assertEqual(len({x["model_id"] for x in roles.values()}),4)
 def test_no_false_production(self):
  m=json.loads(PATH.read_text())
  self.assertEqual(m["status"],"LAB_SELECTION_NOT_PROMOTED")
  self.assertTrue(m["limits"]["no_production_router_change"])
  self.assertTrue(m["limits"]["gpu_guard_must_allow"])
  self.assertTrue(m["limits"]["one_gpu_worker_at_a_time"])
  self.assertFalse(next(x for x in m["roles"] if x["role"]=="complex_reasoning")["uncensored_required"])
  self.assertTrue(any("Flash-Next" in x["model_id"] for x in m["not_yet_admitted"]))
if __name__=="__main__":unittest.main()
