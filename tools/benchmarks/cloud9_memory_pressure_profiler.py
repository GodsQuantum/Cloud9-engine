#!/usr/bin/env python3
"""Read-only Cloud9 host UMA/swap/PSI diagnostic for LLM GPU prequalification.

This is an *advisory* separate from the authoritative CT410 GPU arbiter.
It cannot authorize a benchmark and it makes zero host/service changes.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import time
from datetime import datetime, timezone

GIB = 1024 ** 3
CGROUPS = ('400', '410', '700')
ROOT = Path('/sys/fs/cgroup')


def parse_meminfo(content: str) -> dict[str, float]:
    values = {name: int(value) for name, value in re.findall(r'^(\w+):\s+(\d+) kB$', content, flags=re.M)}
    required = ('MemTotal', 'MemAvailable', 'SwapTotal', 'SwapFree')
    if any(name not in values for name in required):
        raise ValueError('Incomplete Linux /proc/meminfo')
    swap_total = values['SwapTotal']
    swap_free = values['SwapFree']
    if swap_total < 0 or not 0 <= swap_free <= swap_total:
        raise ValueError('Inconsistent swap totals')
    return {
        'mem_total_gib': round(values['MemTotal'] / 1048576, 3),
        'mem_available_gib': round(values['MemAvailable'] / 1048576, 3),
        'swap_used_gib': round((swap_total - swap_free) / 1048576, 3),
        'swap_percent': round(100 * (1 - swap_free / swap_total), 3) if swap_total else 0.0,
    }


def parse_pressure(content: str) -> dict[str, float]:
    result = {}
    for category, avg10, avg60, avg300 in re.findall(
        r'^(some|full) avg10=([\d.]+) avg60=([\d.]+) avg300=([\d.]+)', content, re.M
    ):
        result[f'{category}_avg10'] = float(avg10)
        result[f'{category}_avg60'] = float(avg60)
        result[f'{category}_avg300'] = float(avg300)
    if 'full_avg10' not in result or 'some_avg10' not in result:
        raise ValueError('Incomplete Linux /proc/pressure/memory')
    return result


def parse_vmstat(content: str) -> dict[str, int]:
    result = dict((k, int(v)) for k, v in re.findall(r'^(pswpin|pswpout)\s+(\d+)$', content, re.M))
    if set(result) != {'pswpin', 'pswpout'}:
        raise ValueError('Missing Linux swap-page counters')
    return result


def parse_counter(content: str) -> int | None:
    value = content.strip()
    if value == 'max':
        return None
    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError('Invalid cgroup memory counter') from exc
    if number < 0:
        raise ValueError('Negative cgroup memory counter')
    return number


def cgroup_snapshot(folder: Path) -> dict:
    if not folder.is_dir():
        return {'present': False}
    fields = ('memory.current', 'memory.max', 'memory.swap.current', 'memory.swap.max')
    raw = {}
    for field in fields:
        f = folder / field
        if not f.is_file():
            return {'present': False, 'missing': field}
        raw[field] = parse_counter(f.read_text())
    swap_max = raw['memory.swap.max']
    swap_curr = raw['memory.swap.current']
    events = {}
    events_file = folder / 'memory.events'
    if events_file.is_file():
        events = {k: int(v) for k, v in re.findall(r'^(\w+)\s+(\d+)$', events_file.read_text(), re.M)}
    return {
        'present': True,
        'memory_gib': round((raw['memory.current'] or 0) / GIB, 3),
        'memory_limit_gib': round(raw['memory.max'] / GIB, 3) if raw['memory.max'] is not None else None,
        'swap_gib': round((swap_curr or 0) / GIB, 3),
        'swap_limit_gib': round(swap_max / GIB, 3) if swap_max is not None else None,
        'swap_percent_of_cgroup_limit': round(100 * swap_curr / swap_max, 3)
            if swap_max and swap_curr is not None else None,
        # Historical cumulative values, never infer a current OOM incident from this alone.
        'oom_kills_cumulative': events.get('oom_kill'),
        'oom_attempts_cumulative': events.get('oom'),
    }


def sample_host(root: Path = Path('/')) -> dict:
    def read(path: str) -> str:
        return (root / path.lstrip('/')).read_text()
    mem = parse_meminfo(read('proc/meminfo'))
    psi = parse_pressure(read('proc/pressure/memory'))
    vmstat = parse_vmstat(read('proc/vmstat'))
    cgroups = {ct: cgroup_snapshot(root / f'sys/fs/cgroup/lxc/{ct}') for ct in CGROUPS}
    gpu_path = root / 'sys/class/drm/card0/device/mem_info_gtt_used'
    gpu_gib = None
    if gpu_path.is_file():
        gpu_gib = round(int(gpu_path.read_text().strip()) / GIB, 3)
    return {
        'utc': datetime.now(timezone.utc).isoformat(),
        'monotonic': time.monotonic(),
        'mem': mem,
        'psi': psi,
        'swap_pages': vmstat,
        'gpu_gtt_used_gib': gpu_gib,
        'cgroups': cgroups,
    }


def change_between(before: dict, after: dict, page_bytes: int = 4096) -> dict:
    seconds = after['monotonic'] - before['monotonic']
    if seconds <= 0:
        raise ValueError('Non-positive sampling interval')
    rates = {}
    for key in ('pswpin', 'pswpout'):
        delta = after['swap_pages'][key] - before['swap_pages'][key]
        if delta < 0:
            raise ValueError('Swap counter moved backwards')
        rates[key + '_mib_per_sec'] = round(delta * page_bytes / 1048576 / seconds, 3)
    oom_deltas = {}
    for cid in CGROUPS:
        former = before['cgroups'][cid].get('oom_kills_cumulative')
        latter = after['cgroups'][cid].get('oom_kills_cumulative')
        if former is not None and latter is not None:
            if latter < former:
                raise ValueError(f'Cgroup {cid} OOM counter reset')
            oom_deltas[cid] = latter - former
    return {'interval_sec': round(seconds, 3), 'swap_io': rates,
            'new_cgroup_oom_kills': oom_deltas}


def diagnose(snap: dict, trend: dict | None = None) -> dict:
    """Conservative advisory only. Official CT410 admission remains compulsory."""
    reasons = []
    mem, psi = snap['mem'], snap['psi']
    if mem['mem_available_gib'] < 32:
        reasons.append('HOST_AVAILABLE_LT_32_GIB_FOR_4B_UMA_LOAD')
    if mem['swap_percent'] >= 80:
        reasons.append('HOST_SWAP_OCCUPANCY_GTE_80_PCT')
    if psi['full_avg10'] >= 0.35:
        reasons.append('HOST_PSI_FULL_AVG10_GTE_0_35')
    if snap.get('gpu_gtt_used_gib') is None:
        reasons.append('GPU_GTT_TELEMETRY_UNAVAILABLE')
    for cid in ('400', '410'):
        cgroup = snap['cgroups'].get(cid, {})
        if not cgroup.get('present'):
            reasons.append(f'CRITICAL_CGROUP_{cid}_UNAVAILABLE')
        elif (percent := cgroup.get('swap_percent_of_cgroup_limit')) is not None and percent >= 95:
            reasons.append(f'CRITICAL_CGROUP_{cid}_SWAP_GTE_95_PCT')
    if trend is not None:
        if any(x > 8 for x in trend['swap_io'].values()):
            reasons.append('SWAP_IO_RATE_GT_8_MIB_PER_SEC')
        if any(x for x in trend['new_cgroup_oom_kills'].values()):
            reasons.append('NEW_CRITICAL_OR_DEV_CGROUP_OOM_KILL')
    return {'lab_precheck_advisory_only': 'QUIET_HOST' if not reasons else 'POSTPONE_GPU_LOADER',
            'reasons': reasons, 'official_gpu_arbiter_checked': False,
            'official_gpu_arbiter_required_before_any_real_gpu_run': True}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--samples', type=int, default=4)
    p.add_argument('--interval', type=float, default=1.0)
    args = p.parse_args()
    if not 2 <= args.samples <= 16 or not 0.5 <= args.interval <= 5:
        p.error('Allowed range samples 2..16 and interval 0.5..5 seconds')
    timeline = []
    for index in range(args.samples):
        timeline.append(sample_host())
        if index + 1 < args.samples:
            time.sleep(args.interval)
    diff = change_between(timeline[0], timeline[-1], os.sysconf('SC_PAGE_SIZE'))
    verdict = diagnose(timeline[-1], diff)
    print(json.dumps({
        'source': 'Cloud9 local read-only /proc + /sys cgroup / DRM telemetry',
        'samples': args.samples, 'first': timeline[0], 'last': timeline[-1],
        'trend': diff, 'diagnostic': verdict,
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
