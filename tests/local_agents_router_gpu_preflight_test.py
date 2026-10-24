import ast
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]/"tools/local_agents/cloud9-model-router-safe-lab-20261024.py"
TREE = ast.parse(SOURCE.read_text())
FUNCTIONS = {n.name:n for n in TREE.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
ROUTER = next(n for n in TREE.body if isinstance(n,ast.ClassDef) and n.name=="RouterState")
METHODS = {n.name:n for n in ROUTER.body if isinstance(n,ast.FunctionDef)}
STUB=ast.Module(body=[FUNCTIONS["conservative_request_gib"],FUNCTIONS["guardian_preflight"]],type_ignores=[])

class MockSocket:
 def __init__(self,response):
  self.response=response
  self.sent=b""
 def __enter__(self):return self
 def __exit__(self,*args):return False
 def settimeout(self,n):self.timeout=n
 def sendall(self,b):self.sent=b
 def recv(self,n):return json.dumps(self.response).encode()

class RouterSafeAdmission(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.model_path=Path(self.tmp.name)/"model.gguf"
  self.model_path.write_bytes(b"x"*1024)
  self.m={"id":"test-4B","model":str(self.model_path),"gpu_mode":"coexist-light"}
  self.namespace={"Path":Path,"socket":socket,"json":json,
      "catalog":{"defaults":{"gpu_mode":"exclusive"}},
      "ALLOW_SERVICE_PREEMPTION":False,
      "GPU_GUARDIAN_ADDRESS":("127.0.0.1",19755)}
  exec(compile(STUB,str(SOURCE),"exec"),self.namespace)
 def test_allow_reads_official_guardian(self):
  sock=MockSocket({"allow":True,"reasons":[]})
  with patch.object(socket,"create_connection",return_value=sock) as connect:
   self.assertEqual(self.namespace["guardian_preflight"](self.m),"coexist-light")
  self.assertIn(b"CHECK coexist-light",sock.sent)
  connect.assert_called_once()
 def test_denied_cannot_preempt(self):
  sock=MockSocket({"allow":False,"reasons":["host memory unavailable"]})
  with patch.object(socket,"create_connection",return_value=sock):
   with self.assertRaisesRegex(RuntimeError,"host memory unavailable"):
    self.namespace["guardian_preflight"](self.m)
 def test_guard_offline_fails_closed(self):
  with patch.object(socket,"create_connection",side_effect=OSError("unreachable")):
   with self.assertRaisesRegex(RuntimeError,"unavailable"):
    self.namespace["guardian_preflight"](self.m)
 def test_default_exclusive_declined_before_network(self):
  self.m["gpu_mode"]="exclusive"
  with patch.object(socket,"create_connection") as con:
   with self.assertRaisesRegex(RuntimeError,"maintenance opt-in"):
    self.namespace["guardian_preflight"](self.m)
   con.assert_not_called()
 def test_draft_size_included(self):
  draft=Path(self.tmp.name)/"draft.gguf"
  draft.write_bytes(b"y"*4096)
  self.m["extra_args"]=["--model-draft",str(draft)]
  size=self.namespace["conservative_request_gib"](self.m)
  self.assertGreater(size,1.5)
 def test_unknown_gpu_mode_fails(self):
  self.m["gpu_mode"]="mystery"
  with self.assertRaisesRegex(RuntimeError,"Invalid"):
   self.namespace["guardian_preflight"](self.m)
 def test_previous_worker_preflight_before_stop(self):
  fun=METHODS["ensure_worker_locked"]
  calls=[x for x in ast.walk(fun) if isinstance(x,ast.Call)]
  guard=[x.lineno for x in calls if isinstance(x.func,ast.Name) and x.func.id=="guardian_preflight"]
  stop=[x.lineno for x in calls if isinstance(x.func,ast.Attribute) and x.func.attr=="stop_worker_locked"]
  self.assertTrue(guard and stop)
  self.assertLess(min(guard),min(stop))
 def test_existing_worker_is_preserved_on_denial(self):
  # Execute the real method (extracted from the source), with a fake worker
  # that must survive a guardian denial during a model switch.
  import threading,time
  klass=ast.ClassDef(name="IsolatedRouter",bases=[],keywords=[],
      body=[METHODS["ensure_worker_locked"]],decorator_list=[])
  code=ast.fix_missing_locations(ast.Module(body=[klass],type_ignores=[]))
  def deny(_):
   raise RuntimeError("GUARD_DENIED")
  scope={"Path":Path,"os":os,"time":time,"catalog":{"defaults":{}},
         "model_oversize_decision":lambda *a,**k:(True,"within-generic-limit"),
         "guardian_preflight":deny}
  exec(compile(code,str(SOURCE),"exec"),scope)
  old=type("FakeWorker",(),{"poll":lambda self:None})()
  class State(scope["IsolatedRouter"]):
   worker=old
   worker_model="KNOWN_WORKER"
   active=0
   cv=threading.Condition()
   stopped=False
   def stop_worker_locked(self):self.stopped=True
  st=State()
  with self.assertRaisesRegex(RuntimeError,"GUARD_DENIED"):
   st.ensure_worker_locked(self.m)
  self.assertFalse(st.stopped)
  self.assertIs(st.worker,old)
  self.assertEqual(st.worker_model,"KNOWN_WORKER")
 def test_same_model_reused_without_rechecking_guard(self):
  import threading,time
  klass=ast.ClassDef(name="IsolatedRouter",bases=[],keywords=[],
      body=[METHODS["ensure_worker_locked"]],decorator_list=[])
  code=ast.fix_missing_locations(ast.Module(body=[klass],type_ignores=[]))
  scope={"Path":Path,"os":os,"time":time,"catalog":{"defaults":{}},
         "model_oversize_decision":lambda *a,**k:(True,"within-generic-limit"),
         "guardian_preflight":lambda _:(_ for _ in ()).throw(RuntimeError("unexpected guardian call"))}
  exec(compile(code,str(SOURCE),"exec"),scope)
  old=type("FakeWorker",(),{"poll":lambda self:None})()
  class State(scope["IsolatedRouter"]):
   worker=old
   worker_model="test-4B"
  st=State()
  st.ensure_worker_locked(self.m)
  self.assertIs(st.worker,old)
  self.assertEqual(st.worker_model,"test-4B")
 def test_no_automatic_exclusive_fallback(self):
  body=ast.get_source_segment(SOURCE.read_text(),METHODS["acquire_gpu"])
  self.assertNotIn("falling back to exclusive",body)
  self.assertIn("Never automatically preempt",body)
 def test_voice_never_stopped_by_default(self):
  body=ast.get_source_segment(SOURCE.read_text(),METHODS["acquire_gpu"])
  self.assertIn("if not ALLOW_SERVICE_PREEMPTION:",body)
  self.assertIn("VoiceStudio is running",body)
if __name__=="__main__": unittest.main()
