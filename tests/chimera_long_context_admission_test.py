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
    def test_native_turbo3_uses_existing_runner_and_unique_evidence(self):
        self.assertIn('parser.add_argument("--kv-k"',src)
        self.assertIn('parser.add_argument("--kv-v"',src)
        self.assertIn('parser.add_argument("--batch"',src)
        self.assertIn('"-ctk",args_parsed.kv_k,"-ctv",args_parsed.kv_v',src)
        self.assertIn('RUN_SUFFIX+=f"_k{args_parsed.kv_k}_v{args_parsed.kv_v}_b{args_parsed.batch}"',src)
        self.assertIn('blocked_experimental_kv_swap_safety',src)
        self.assertIn('choices=["f16","q8_0","turbo3"]',src)
        self.assertIn('blocked_known_bad_turbo3_quality',src)
        self.assertIn('PROVEN_BAD_VULKAN_TURBO3_8K_20261025',src)
        self.assertIn('RUN_SUFFIX+="_blocked_policy"',src)
        self.assertIn('REFUSE_TO_OVERWRITE_EVIDENCE',src)
        self.assertIn("LAB_START_MEM_GIB = 27.0 if TARGET==8192 else 30.0",src)
        self.assertIn("LAB_START_MAX_SWAP_PCT = 95.0",src)
        self.assertIn("blocked_lab_memory_headroom",src)
        self.assertIn("lab_start_preflight(state)",src)
        self.assertIn('if TARGET==16384:',src)
        self.assertIn('state.get("swap_total_gib",0)<23',src)
        self.assertIn('state.get("psi_memory_full_avg10",99)<0.10',src)
        self.assertIn('state.get("safe_total_gtt_gib",0)>=7.2',src)
        self.assertIn('state.get("safe_total_gtt_gib",0)>=7.8',src)
        self.assertIn('state.get("psi_memory_full_avg10",99)<0.05',src)
        self.assertIn('supply a unique --trial-id (no replay)',src)
        self.assertIn('parser.add_argument("--trial-id"',src)
        self.assertIn('re.fullmatch(r"[A-Za-z0-9_-]{1,48}"',src)
        self.assertIn('RUN_SUFFIX+=f"_trial_{args_parsed.trial_id}"',src)
        self.assertIn('state.get("swap_used_percent",100)>95',src)
        self.assertNotIn('systemctl restart',src)
    def test_build_ab_only_exact_verified_existing_lab_elfs(self):
        self.assertIn('parser.add_argument("--engine-build"',src)
        self.assertIn('"nextn-revert":"25e2d4560ecceeda57a9c6fa88bfd8b440c46f5bac5dfc71204002a1f798ed63"',src)
        self.assertIn('"baseline":"2e00292ca25dd5f7e7483f232d2b0c7fe30ba73deea503dcdb4792ac36e47cc3"',src)
        self.assertIn('actual_sha==EXPECTED_SERVER_SHA256[args_parsed.engine_build]',src)
        self.assertIn('chimera-master9ae-nextn-revert-vulkan-20261025/bin/llama-server',src)
        self.assertIn('RUN_SUFFIX+=f"_build_{args_parsed.engine_build.replace',src)
    def test_historical_fixtures_not_recreated(self):
        self.assertIn("atomic_turboquant_context_20261022.py",src)
        self.assertIn("fixture.build_target(TARGET)",src)
        self.assertIn("parsed==fixture.CODES",src)
        self.assertIn("range(args_parsed.rep_start,args_parsed.rep_end+1)",src)
    def test_report_has_evidence_of_full_context_ingestion(self):
        for required in ("measured_tokenizer_tokens","full_prompt_ingested","fixture_sha256","answer_sha256","prompt_tokens"):
            self.assertIn(required,src)

if __name__=="__main__":unittest.main()
