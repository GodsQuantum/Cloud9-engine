import importlib.util,json,sqlite3,tempfile,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("integration",R/"tools/local_agents/audit_omniroute_local_integration.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class TestNativeIntegration(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  p=Path(self.tmp.name)
  self.db=p/"test.sqlite"
  self.cat=p/"catalog.json"
  self.cat.write_text(json.dumps({"models":[{"id":"Cloud9-Qwen3.8-4B-Heretic","group":"small","uncensored":True},
                                          {"id":"Cloud9-MiniCPM5-2B-DSpark","group":"small","uncensored":True},
                                          {"id":"Cloud9-Pym-35B-A3B-MTP","group":"large","uncensored":False}]}))
  db=sqlite3.connect(self.db)
  db.execute("create table provider_connections(provider text,name text,is_active integer,test_status text,provider_specific_data text)")
  db.execute("create table combos(name text,data text)")
  db.execute("insert into provider_connections values (?,?,?,?,?)",
             ("llama-cpp","Cloud9 native",1,"active",'{"url":"http://192.168.1.219:8090","apiKey":"UNTRUSTED_SECRET"}'))
  db.execute("insert into combos values (?,?)",("Cloud9-Engine",
      json.dumps({"strategy":"priority","models":[{"model":"llama-cpp/Cloud9-Qwen3.8-4B-Heretic"}]})))
  db.commit()
  db.close()
 def test_pure_and_no_secrets(self):
  value=mod.assess(self.db,self.cat)
  self.assertTrue(value["static_native_connection_valid"])
  self.assertEqual(value["combo"]["model_count"],1)
  self.assertFalse(value["selected_roles"]["Cloud9-Pym-35B-A3B-MTP"]["in_native_cloud9_combo"])
  self.assertNotIn("UNTRUSTED_SECRET",json.dumps(value))
  self.assertFalse(value["model_inference_certified"])
 def test_wrong_backend_ref_fails(self):
  conn=sqlite3.connect(self.db)
  conn.execute("update combos set data=?",('{"models":[{"model":"llama-cpp/Cloud9-MISSING"}]}',))
  conn.commit()
  conn.close()
  data=mod.assess(self.db,self.cat)
  self.assertFalse(data["static_native_connection_valid"])
if __name__=="__main__":unittest.main()
