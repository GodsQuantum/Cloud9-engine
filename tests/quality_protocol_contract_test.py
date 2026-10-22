#!/usr/bin/env python3
import importlib.util
import pathlib
import unittest

p=pathlib.Path(__file__).resolve().parents[1]/"tools/benchmarks/one_engine_quality_protocol_20261022.py"
s=importlib.util.spec_from_file_location("protocol",p)
q=importlib.util.module_from_spec(s);s.loader.exec_module(q)

class QualityContract(unittest.TestCase):
 def test_3x4_cases(self):
  self.assertEqual(len(q.CASES),12)
  self.assertEqual({k:sum(c["kind"]==k for c in q.CASES) for k in ("json","tools","code","fr")},{"json":3,"tools":3,"code":3,"fr":3})
 def test_exact_json_only(self):
  self.assertTrue(q.grade("j_sum",{"content":'{"total":31,"ville":"Toulouse","date":"2026-10-19"}'})["correct"])
  self.assertFalse(q.grade("j_sum",{"content":"Here: "+'{"total":31,"ville":"Toulouse","date":"2026-10-19"}'})["correct"])
 def test_tool_must_be_real_call_not_prose(self):
  ok={"content":"","tool_calls":[{"function":{"name":"calendar_lookup","arguments":'{"date":"2026-10-19"}'}}]}
  self.assertTrue(q.grade("t_calendar",ok)["correct"])
  self.assertFalse(q.grade("t_calendar",{"content":"I looked up the calendar"})["correct"])
 def test_code_semantics_not_enough_to_pass_format(self):
  self.assertTrue(q.grade("c_add",{"content":'{"corrected_line":"    return a + b"}'})["correct"])
  self.assertFalse(q.grade("c_add",{"content":'{"corrected_line":"    def add(a,b): return a+b"}'})["correct"])
 def test_french_style_is_not_autocertified(self):
  x=q.grade("f_comedy",{"content":"bonjour"})
  self.assertFalse(x["correct"]);self.assertTrue(x["editorial_pending"])
 def test_aggregate_refuses_missing(self):
  with self.assertRaises(ValueError):q.aggregate([])
 def test_aggregate_36_synthetic_records_not_certified(self):
  rows=[]
  for c in q.CASES:
   for rep in (1,2,3):
    if c["kind"] in ("json","code"):
     import json
     msg={"content":json.dumps(c["expected"],ensure_ascii=False)}
    elif c["kind"]=="tools":
     import json
     msg={"content":"","tool_calls":[{"function":{"name":c["fn"],"arguments":json.dumps(c["args"])}}]}
    else:
     msg={"content":("Je raconte des dinosaures, ma batterie et mon dentiste, "
        "j'explique ce mardi une facture et un rendez-vous; ma mémoire du contexte "
        "d'inférence reste claire dans ces expériences fictives. "
        "Je décris un scénario technique et comique inventé, sans données réelles "
        "ni informations personnelles, et je garde le français simple et correct.")}
    rows.append({"id":c["id"],"rep":rep,"message":msg})
  result=q.aggregate(rows)
  self.assertEqual(sum(v["n"] for v in result["quality"].values()),36)
  self.assertFalse(result["certified"])
if __name__=="__main__":unittest.main(verbosity=2)
