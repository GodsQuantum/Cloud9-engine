import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tools/local_agents/cloud9-model-router-per-model-performance-20261024.py"
tree=ast.parse(SOURCE.read_text())
klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="RouterState")
method=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=="worker_args")
module=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name="IsolatedRouter",bases=[],keywords=[],body=[method],decorator_list=[])],type_ignores=[]))
space={"a":SimpleNamespace(worker_host="127.0.0.1",worker_port=18091)}
exec(compile(module,str(SOURCE),"exec"),space)

class ModelPerformanceFlags(unittest.TestCase):
 def args_for(self,model):
  obj=space["IsolatedRouter"]()
  obj.runtime=lambda _: "/lab/chimera/bin/llama-server"
  return obj.worker_args(model)
 def flag(self,args,name):
  return args[args.index(name)+1]
 def model(self):
  return {"id":"Cloud9-test","model":"/lab/model.gguf","backend":"upstream-next"}
 def test_existing_model_flags_unchanged(self):
  args=self.args_for(self.model())
  self.assertEqual(self.flag(args,"-t"),"8")
  self.assertEqual(self.flag(args,"-tb"),"8")
  self.assertEqual(self.flag(args,"-b"),"1024")
  self.assertEqual(self.flag(args,"-ub"),"1024")
 def test_only_experimental_chimera_is_tuned(self):
  m=self.model()
  m.update({"id":"Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB","backend":"chimera-vulkan-guard-lab",
            "threads":6,"threads_batch":6,"batch":256,"ubatch":256})
  args=self.args_for(m)
  self.assertEqual(self.flag(args,"-t"),"6")
  self.assertEqual(self.flag(args,"-tb"),"6")
  self.assertEqual(self.flag(args,"-b"),"256")
  self.assertEqual(self.flag(args,"-ub"),"256")
  self.assertEqual(self.flag(args,"--fit"),"off")
if __name__=="__main__":unittest.main()
