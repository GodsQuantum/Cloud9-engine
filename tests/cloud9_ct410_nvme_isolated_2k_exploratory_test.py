#!/usr/bin/env python3
"""Unit-only guardrails for isolated 2K CT410 exploratory smoke A/B."""
import importlib.util
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO
import json,sys,unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('cloud9_gpu_smoke',ROOT/'tools/benchmarks/cloud9_ct410_nvme_isolated_2k_exploratory.py')
M=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

class CT410IsolatedSmoketest(unittest.TestCase):
    def hw(self,**updates):
        value={'available_gib':25,'swap_percent':65,
               'memory_psi_full_avg10':0.02,'io_psi_full_avg10':89,
               'gtt_gib':0.20,'tctl_c':64}
        value.update(updates)
        return value
    def gate(self,host=None,official=None,clients=None,backup=False):
        with patch.object(M,'host_state',return_value=host or self.hw()):
            with patch.object(M,'official_gpu_check_4g',return_value=official or {'allow':True}):
                with patch.object(M,'production_clients',return_value=clients or []):
                    with patch.object(M,'backup_running',return_value=backup):
                        return M.check()
    def test_host_io_exception_only_for_exploratory_smoke(self):
        g=self.gate()
        self.assertTrue(g['allow'])
        self.assertEqual(g['host']['io_psi_full_avg10'],89)
        self.assertEqual(M.PROD.parent.name,'production-copy-upstream-2bb-20261023')
        self.assertEqual(M.VULKAN.parent.name,'upstream-master9ff-vulkan-gfx1103-20261023')
    def test_reject_if_official_arbiter_declines(self):
        self.assertIn('OFFICIAL_GPU_REJECT',self.gate(official={'allow':False})['reasons'])
    def test_reject_memory_psi_and_min_memory(self):
        self.assertIn('MEMORY_PSI',self.gate(host=self.hw(memory_psi_full_avg10=.35))['reasons'])
        self.assertIn('RAM_BELOW_24',self.gate(host=self.hw(available_gib=23.9))['reasons'])
    def test_reject_clients_backup_thermal(self):
        self.assertIn('PROD_CLIENT',self.gate(clients=['connection'])['reasons'])
        self.assertIn('BACKUP_STARTED',self.gate(backup=True)['reasons'])
        self.assertIn('TEMP',self.gate(host=self.hw(tctl_c=73))['reasons'])
    def test_official_4g_lease_is_explicit_and_not_a_bypass(self):
        source=(ROOT/'tools/benchmarks/cloud9_ct410_nvme_isolated_2k_exploratory.py').read_text()
        self.assertIn('CHECK coexist-light 4.0',source)
        self.assertIn("if not gpu.get('allow'):failures.append('OFFICIAL_GPU_REJECT')",source)
        self.assertIn("if h['gtt_gib']>4:return 'GTT_LIMIT'",source)

    def test_watchdog_preserves_host_ram(self):
        self.assertEqual(M.monitor_bad(self.hw(available_gib=17)),'MEMORY_RESERVE')
        self.assertEqual(M.monitor_bad(self.hw(gtt_gib=4.1)),'GTT_LIMIT')
        self.assertEqual(M.monitor_bad(self.hw(tctl_c=78)),'THERMAL')
        self.assertIsNone(M.monitor_bad(self.hw()))
    def test_same_flags_and_no_force_16k_claim(self):
        self.assertEqual(M.FLAGS2[:6],('-c','2048','-b','512','-ub','512'))
        self.assertIn('--spec-type',M.FLAGS2)
        self.assertIn('draft-mtp',M.FLAGS2)
        source=(ROOT/'tools/benchmarks/cloud9_ct410_nvme_isolated_2k_exploratory.py').read_text()
        self.assertIn('EXPLORATORY_ONLY_NOT_PRODUCTION_ELIGIBLE',source)
        self.assertIn('never',M.__doc__.lower() if M.__doc__ else 'never')
    def test_single_candidate_mode_cannot_repeat_prod_baseline(self):
        source=(ROOT/'tools/benchmarks/cloud9_ct410_nvme_isolated_2k_exploratory.py').read_text()
        self.assertIn("parser.add_argument('--candidate-only'",source)
        self.assertIn("selected=(('vulkan9ff',VULKAN),) if args.candidate_only",source)
        self.assertIn('for name,binary in selected:',source)

    def test_without_execute_does_not_launch_model(self):
        with patch.object(M,'check',return_value={'allow':False,'reasons':['MEMORY_PSI']}):
            with patch.object(M,'trial',side_effect=AssertionError('model must not be loaded')):
                with patch.object(sys,'argv',['smoketest']),redirect_stdout(StringIO()) as out:
                    M.main()
        self.assertIn('ADMISSION',out.getvalue())

if __name__=='__main__':unittest.main(verbosity=2)
