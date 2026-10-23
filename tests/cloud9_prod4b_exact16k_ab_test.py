#!/usr/bin/env python3
"""Offline contracts for production-parameter Qwen4B benchmark guard."""
from contextlib import redirect_stdout
from io import StringIO
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SRC=Path(__file__).resolve().parents[1]/'tools/benchmarks/cloud9_prod4b_exact16k_ab.py'
spec=importlib.util.spec_from_file_location('cloud9_16k_ab',SRC)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ProductionVsLatest16K(unittest.TestCase):
    def data(self,swap_free=3_500_000,available=40_000_000,mem_psi=0.04,io_psi=0.02):
        mem=(
            f'MemAvailable: {available} kB\n'
            'SwapTotal: 20_000_000 kB\n'
        ).replace('20_000_000','20000000')+f'SwapFree: {swap_free} kB\n'
        p=lambda f: f'some avg10=0.10 avg60=0.11 avg300=0.13 total=1\nfull avg10={f} avg60=0.1 avg300=0.1 total=2\n'
        return m.parse_telemetry(mem,p(mem_psi),p(io_psi),500000000,60.0)

    def test_same_prod_flags_identically_applied(self):
        self.assertIn('16384',m.FLAGS)
        self.assertIn('f16',m.FLAGS)
        self.assertIn('--no-spec-draft-backend-sampling',m.FLAGS)
        self.assertIn('draft-mtp',m.FLAGS)
        self.assertNotEqual(m.PROD,m.LATEST)
        self.assertIn('da2',str(m.LATEST))
        self.assertIn('production-upstream-a868-reference',str(m.PROD))

    def test_mem_parser_and_pressure(self):
        data=self.data(swap_free=5000000)
        self.assertAlmostEqual(data['swap_percent'],75.0)
        self.assertAlmostEqual(data['memory_psi_full_avg10'],.04)
        self.assertAlmostEqual(data['io_psi_full_avg10'],.02)
        with self.assertRaises(ValueError):
            m.parse_telemetry('no memory data','full avg10=0.1','full avg10=0.1',0,60)

    def test_watchdog_does_not_ignore_io_stall(self):
        t=self.data(swap_free=6000000)
        self.assertFalse(m.watchdog_bad(t))
        for override in ({'memory_psi_full_avg10':1.5},{'io_psi_full_avg10':12},
                         {'swap_percent':90},{'available_gib':20},{'tctl_c':78},
                         {'gtt_gib':8}):
            self.assertTrue(m.watchdog_bad(dict(t,**override)))

    def test_preflight_without_execute_cannot_allocate_gpu(self):
        failed={'allow':False,'reasons':['OFFICIAL_GPU_REJECTION']}
        with patch.object(m,'admission',return_value=failed),patch.object(m,'run_trial',side_effect=AssertionError('NO_GPU_ALLOWED')):
            with patch.object(sys,'argv',['bench']),redirect_stdout(StringIO()) as io:
                m.main()
            response=json.loads(io.getvalue())
        self.assertEqual(response['status'],'PREFLIGHT_ONLY')
        self.assertEqual(response['admission']['reasons'],['OFFICIAL_GPU_REJECTION'])

    def test_execute_refuses_safety_block(self):
        failed={'allow':False,'reasons':['MEMORY_PSI_GE_0.35']}
        with patch.object(m,'admission',return_value=failed),patch.object(m,'run_trial',side_effect=AssertionError('MUST_NOT_RUN')):
            with patch.object(sys,'argv',['bench','--execute']),redirect_stdout(StringIO()) as io:
                with self.assertRaises(SystemExit) as refused:
                    m.main()
        self.assertEqual(refused.exception.code,3)
        self.assertEqual(json.loads(io.getvalue())['status'],'GPU_BLOCKED')

if __name__=='__main__':
    unittest.main(verbosity=2)
