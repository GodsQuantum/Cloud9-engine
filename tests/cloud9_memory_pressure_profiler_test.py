#!/usr/bin/env python3
"""Offline, deterministic safety contracts for Cloud9 host memory profiler."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'cloud9_memory_pressure_profiler', ROOT / 'tools/benchmarks/cloud9_memory_pressure_profiler.py'
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def snapshot(mem=40, swap=10, psi=.01, ct_swap=40, oom=55, gtt=1):
    return {
        'monotonic': 10.0,
        'mem': {'mem_total_gib': 92.0, 'mem_available_gib': mem, 'swap_percent': swap},
        'psi': {'full_avg10': psi},
        'gpu_gtt_used_gib': gtt,
        'swap_pages': {'pswpin': 100, 'pswpout': 200},
        'cgroups': {
            '400': {'present': True, 'swap_percent_of_cgroup_limit': ct_swap,
                    'oom_kills_cumulative': oom},
            '410': {'present': True, 'swap_percent_of_cgroup_limit': ct_swap,
                    'oom_kills_cumulative': 0},
            '700': {'present': True, 'swap_percent_of_cgroup_limit': None,
                    'oom_kills_cumulative': 0},
        },
    }


class HostMemoryPressureProfiler(unittest.TestCase):
    def test_parse_linux_proc_data(self):
        m = mod.parse_meminfo('MemTotal: 96468992 kB\nMemAvailable: 33554432 kB\n'
                              'SwapTotal: 20447232 kB\nSwapFree: 10223616 kB\n')
        self.assertEqual(m['mem_available_gib'], 32.0)
        self.assertEqual(m['swap_percent'], 50.0)
        self.assertEqual(mod.parse_pressure('some avg10=1.00 avg60=0.50 avg300=0.10 total=20\n'
                                            'full avg10=3.29 avg60=0.80 avg300=0.20 total=12\n')['full_avg10'], 3.29)
        self.assertEqual(mod.parse_vmstat('pswpin 123\npswpout 456\n'),
                         {'pswpin': 123, 'pswpout': 456})
        with self.assertRaises(ValueError):
            mod.parse_meminfo('MemAvailable: 6 kB')
        with self.assertRaises(ValueError):
            mod.parse_pressure('some avg10=1.2 avg60=1 avg300=1 total=0')
        with self.assertRaises(ValueError):
            mod.parse_vmstat('pswpin 42\n')

    def test_critical_swap_or_memory_pressure_refuses_even_when_gpu_arbiter_might_allow(self):
        diag = mod.diagnose(snapshot(mem=26.675, swap=84.95, psi=3.09, ct_swap=99.5))
        self.assertEqual(diag['lab_precheck_advisory_only'], 'POSTPONE_GPU_LOADER')
        for expected in ('HOST_AVAILABLE_LT_32_GIB_FOR_4B_UMA_LOAD',
                         'HOST_SWAP_OCCUPANCY_GTE_80_PCT', 'HOST_PSI_FULL_AVG10_GTE_0_35',
                         'CRITICAL_CGROUP_400_SWAP_GTE_95_PCT',
                         'CRITICAL_CGROUP_410_SWAP_GTE_95_PCT'):
            self.assertIn(expected, diag['reasons'])
        self.assertFalse(diag['official_gpu_arbiter_checked'])
        self.assertTrue(diag['official_gpu_arbiter_required_before_any_real_gpu_run'])

    def test_historical_cumulative_oom_not_incident(self):
        a = snapshot(oom=55)
        b = snapshot(oom=55)
        b['monotonic'] = 14.0
        trend = mod.change_between(a, b)
        self.assertEqual(trend['new_cgroup_oom_kills']['400'], 0)
        self.assertEqual(mod.diagnose(b, trend)['lab_precheck_advisory_only'], 'QUIET_HOST')

    def test_real_oom_delta_and_swap_io_rate_are_concerning(self):
        a = snapshot(oom=55)
        b = snapshot(oom=56)
        b['monotonic'] = 14.0
        b['swap_pages'] = {'pswpin': 20000, 'pswpout': 1000}
        trend = mod.change_between(a, b)
        self.assertGreater(trend['swap_io']['pswpin_mib_per_sec'], 8)
        self.assertEqual(trend['new_cgroup_oom_kills']['400'], 1)
        reason = mod.diagnose(b, trend)['reasons']
        self.assertIn('SWAP_IO_RATE_GT_8_MIB_PER_SEC', reason)
        self.assertIn('NEW_CRITICAL_OR_DEV_CGROUP_OOM_KILL', reason)
        with self.assertRaises(ValueError):
            mod.change_between(b, a)

    def test_cgroup_limits_and_missing_telemetry_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p/'memory.current').write_text('2147483648\n')
            (p/'memory.max').write_text('max\n')
            (p/'memory.swap.current').write_text('4294967296\n')
            (p/'memory.swap.max').write_text('4294967296\n')
            (p/'memory.events').write_text('oom 55\noom_kill 8\n')
            result = mod.cgroup_snapshot(p)
            self.assertEqual(result['swap_percent_of_cgroup_limit'], 100)
            self.assertEqual(result['oom_kills_cumulative'], 8)
            self.assertIsNone(result['memory_limit_gib'])
        snap = snapshot()
        snap['cgroups']['410'] = {'present': False}
        snap['gpu_gtt_used_gib'] = None
        reasons = mod.diagnose(snap)['reasons']
        self.assertIn('CRITICAL_CGROUP_410_UNAVAILABLE', reasons)
        self.assertIn('GPU_GTT_TELEMETRY_UNAVAILABLE', reasons)

    def test_fixture_host_snapshot_is_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            def create(path, content):
                f = p/path
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(content)
            create('proc/meminfo','MemTotal: 96468992 kB\nMemAvailable: 41943040 kB\n'
                   'SwapTotal: 20447232 kB\nSwapFree: 18350080 kB\n')
            create('proc/pressure/memory',
                   'some avg10=0.01 avg60=0.02 avg300=0.03 total=2\n'
                   'full avg10=0.00 avg60=0.01 avg300=0.02 total=1\n')
            create('proc/vmstat','pswpin 42\npswpout 52\n')
            create('sys/class/drm/card0/device/mem_info_gtt_used','536870912\n')
            for c in ('400','410','700'):
                create(f'sys/fs/cgroup/lxc/{c}/memory.current','1073741824\n')
                create(f'sys/fs/cgroup/lxc/{c}/memory.max','68719476736\n')
                create(f'sys/fs/cgroup/lxc/{c}/memory.swap.current','1073741824\n')
                create(f'sys/fs/cgroup/lxc/{c}/memory.swap.max','4294967296\n')
                create(f'sys/fs/cgroup/lxc/{c}/memory.events','oom 0\noom_kill 0\n')
            before = {str(x.relative_to(p)):x.read_bytes() for x in p.rglob('*') if x.is_file()}
            snap = mod.sample_host(p)
            self.assertEqual(snap['gpu_gtt_used_gib'], 0.5)
            self.assertEqual(mod.diagnose(snap)['lab_precheck_advisory_only'], 'QUIET_HOST')
            after = {str(x.relative_to(p)):x.read_bytes() for x in p.rglob('*') if x.is_file()}
            self.assertEqual(before, after, 'Profiler must not change any observed file')


if __name__ == '__main__':
    unittest.main(verbosity=2)
