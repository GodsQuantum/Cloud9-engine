import ast
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tools/local_agents/cloud9-model-router-idle-coexist-20261024.py"
TEXT=SOURCE.read_text()
TREE=ast.parse(TEXT)
FUNCTIONS={n.name:n for n in TREE.body if isinstance(n,ast.FunctionDef)}
ROUTER=next(n for n in TREE.body if isinstance(n,ast.ClassDef) and n.name=="RouterState")
METHODS={n.name:n for n in ROUTER.body if isinstance(n,ast.FunctionDef)}
STUB=ast.Module(body=[FUNCTIONS["autosubs_gpu_idle"],FUNCTIONS["light_gpu_user"]],type_ignores=[])

class Reply:
 def __init__(self,data):self.data=data
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self):return json.dumps(self.data).encode()
class IdleCoexistTest(unittest.TestCase):
 def setUp(self):
  self.scope={"urllib":urllib,"json":json,"tcp_port_busy":lambda port:False}
  exec(compile(STUB,str(SOURCE),"exec"),self.scope)
 def test_known_idle_container_identifiers_only(self):
  f=self.scope["light_gpu_user"]
  sid="speaches-abcdef";vid="voice-abcdef";aid="aligner-abcdef"
  self.assertTrue(f((1,"llama-server","0::/cloud9-embedding.service"),sid,vid,aid))
  self.assertTrue(f((2,"speaches","0::/docker-"+sid+".scope"),sid,vid,aid))
  self.assertTrue(f((3,"voicestudio","0::/docker-"+vid+".scope"),sid,vid,aid))
  self.assertTrue(f((4,"aligner","0::/docker-"+aid+".scope"),sid,vid,aid))
  self.assertFalse(f((5,"unknown","0::/docker-malicious-abcdef.scope"),sid,vid,aid))
 def test_voice_or_aligner_not_whitelisted_without_identity(self):
  f=self.scope["light_gpu_user"]
  self.assertFalse(f((1,"voicestudio","docker-voice-abcdef"),"speaches","", "aligner"))
  self.assertFalse(f((1,"aligner","docker-aligner-abcdef"),"speaches","voice",""))
 def test_autosubs_idle_requires_empty_model_list(self):
  with patch.object(urllib.request,"urlopen",return_value=Reply({"status":"ok","loaded_models":[]})):
   self.assertTrue(self.scope["autosubs_gpu_idle"]())
  with patch.object(urllib.request,"urlopen",return_value=Reply({"status":"ok","loaded_models":["ASR"]})):
   self.assertFalse(self.scope["autosubs_gpu_idle"]())
 def test_autosubs_busy_connection_and_health_failure_block(self):
  self.scope["tcp_port_busy"]=lambda p:p==8007
  with patch.object(urllib.request,"urlopen") as request:
   self.assertFalse(self.scope["autosubs_gpu_idle"]())
   request.assert_not_called()
  self.scope["tcp_port_busy"]=lambda _:False
  with patch.object(urllib.request,"urlopen",side_effect=OSError("service down")):
   self.assertFalse(self.scope["autosubs_gpu_idle"]())
 def test_coexist_branch_does_not_stop_voice(self):
  code=ast.get_source_segment(TEXT,METHODS["acquire_gpu"])
  self.assertIn('if voice_was and mode == "coexist-light":',code)
  self.assertIn('if voice_was and mode == "exclusive":',code)
  self.assertIn('if not autosubs_gpu_idle()',code)
  self.assertIn('light_gpu_user(u,sid,vid,aid)',code)
  self.assertNotIn('falling back to exclusive',code)
if __name__=="__main__":unittest.main()
