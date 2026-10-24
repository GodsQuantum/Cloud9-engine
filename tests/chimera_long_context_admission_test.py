"""Static policy gates for 8K/16K real-LAB test without touching GPU."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tools/chimera/lab_chimera_existing_five_needles.py"
src=SOURCE.read_text()
tree=ast.parse(src)
fns={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}

class LongContextSafety(unittest.TestCase):
    def test_8k_only_reserves_required_kv_plus_answer_room(self):
        self.assertIn("CONTEXT = TARGET + 512",src)
        self.assertIn("choices=[8192,16384]",src)
    def test_official_guardian_checked_before_any_gpu_lock_or_start(self):
        method=ast.get_source_segment(src,fns["run"])
        first=method.index("state=check(RESERVE)")
        lock=method.index("fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)")
        second=method.index("state=check(RESERVE)",first+1)
        launch=method.index("subprocess.Popen(args")
        self.assertLess(first,lock)
        self.assertLess(lock,second)
        self.assertLess(second,launch)
    def test_postload_survival_is_not_new_model_admission(self):
        self.assertIn("mem_available_gib",src)
        self.assertIn("postload_stability_verified",src)
        self.assertIn("stable>=2",src)
        self.assertIn("mem_available_gib\",0)<20.0",src)
        self.assertIn("psi_memory_full_avg10\",99)>=2.0",src)
    def test_faults_stop_only_lab_worker(self):
        self.assertIn("proc.terminate()",src)
        self.assertIn("WATCH_EVENTS",src)
        for forbidden in ("systemctl stop","docker stop","pct stop","qm stop","vzdump --stop","swapoff","drop_caches"):
            self.assertNotIn(forbidden,src)
    def test_historical_fixtures_not_recreated(self):
        self.assertIn("atomic_turboquant_context_20261022.py",src)
        self.assertIn("fixture.build_target(TARGET)",src)
        self.assertIn("parsed==fixture.CODES",src)
        self.assertIn("range(args_parsed.rep_start,args_parsed.rep_end+1)",src)
    def test_report_has_evidence_of_full_context_ingestion(self):
        for required in ("measured_tokenizer_tokens","full_prompt_ingested","fixture_sha256","answer_sha256","prompt_tokens"):
            self.assertIn(required,src)

if __name__=="__main__":unittest.main()
