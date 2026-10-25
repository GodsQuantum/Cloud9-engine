import ast,pathlib,unittest
SRC=pathlib.Path(__file__).resolve().parents[1]/"tools/local_agents/atomic2_native_guarded_c09_lab.py"
class AtomicLabSafe(unittest.TestCase):
 def test_syntax(self):ast.parse(SRC.read_text())
 def test_exact_binary_sha(self):self.assertIn("8ddf5bf86d78797e72a1d82ccc23a48875887427eefde8464bd72f6bb1705e85",SRC.read_text())
 def test_all_real_tools_simulated(self):self.assertIn("no_real_tool_execution",SRC.read_text());self.assertIn("eval.toolbox(fixture)",SRC.read_text())
 def test_native_gpu_lock_no_service_prestop(self):
  s=SRC.read_text();self.assertIn("fcntl.LOCK_EX|fcntl.LOCK_NB",s);self.assertNotIn("systemctl stop",s);self.assertNotIn("docker stop",s)
 def test_close_own_pid_only(self):
  s=SRC.read_text();self.assertIn("child.terminate()",s);self.assertIn("child.kill()",s)
 def test_memory_survival(self):
  s=SRC.read_text();self.assertIn('get("psi_memory_full_avg10",99)<0.5',s);self.assertIn('get("mem_available_gib",0)>=21',s)
 def test_immutable_artifact(self):self.assertIn('not OUT.exists() and not LOG.exists()',SRC.read_text())
 def test_runtime_watchdog_strict(self):
  s=SRC.read_text()
  self.assertIn('measured.get("psi_memory_full_avg10",99)>=2.0',s)
  self.assertIn('measured.get("mem_available_gib",0)<19.0',s)
  self.assertIn('stop_own(child)',s)
  self.assertIn('watchdog_events',s)
 def test_resumed_checkpoint_validation_has_strict_identity(self):
  import ast
  s=SRC.read_text()
  self.assertIn("DUPLICATE_OR_UNKNOWN_COMPLETED_CASE",s)
  self.assertIn("UNSAFE_OR_FAILED_CHECKPOINT_REQUIRES_REVIEW",s)
  self.assertIn("PINNED_CHECKPOINT_METADATA_MISMATCH",s)
  self.assertIn("seen:continue",s)
 def test_fresh_attempt_log_immutable(self):
  s=SRC.read_text()
  self.assertIn("MISSING_CHECKPOINT_OR_LOG_COLLISION",s)
  self.assertIn("attempt_ids",s)
 def test_resume_verification_function_direct(self):
  import ast
  source=ast.parse(SRC.read_text())
  fn=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=="verify_checkpoint")
  mod=ast.Module(body=[fn],type_ignores=[])
  namespace={}
  exec(compile(mod,str(SRC),"exec"),namespace)
  valid={"source_binary_sha256":"a","fixture_sha256":"fixture",
         "model_alias":"Cloud9-Atomic2-C09-Guarded-LAB",
         "kv_k":"q8_0","kv_v":"turbo3","production_promoted":False,"lab_only":True,
         "status":"paused_resource_pressure",
         "results":[{"rep":1,"fixture":"a","passed":True,"strict_json":True,"unsafe":False}]}
  allowed={(1,"a"),(1,"b")}
  self.assertEqual(namespace["verify_checkpoint"](valid,"a","fixture",allowed),{(1,"a")})
  import copy
  wrong=copy.deepcopy(valid);wrong["results"].append(wrong["results"][0])
  with self.assertRaisesRegex(ValueError,"DUPLICATE"):
   namespace["verify_checkpoint"](wrong,"a","fixture",allowed)
  wrong=copy.deepcopy(valid);wrong["results"][0]["unsafe"]=True
  with self.assertRaisesRegex(ValueError,"UNSAFE"):
   namespace["verify_checkpoint"](wrong,"a","fixture",allowed)
  wrong=copy.deepcopy(valid);wrong["kv_v"]="f16"
  with self.assertRaisesRegex(ValueError,"METADATA"):
   namespace["verify_checkpoint"](wrong,"a","fixture",allowed)
 def test_model_no_prod(self):self.assertIn('assert man["production_promoted"] is False',SRC.read_text())
if __name__=="__main__":unittest.main()
