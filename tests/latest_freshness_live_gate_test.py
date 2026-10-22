#!/usr/bin/env python3
"""Mocked regression gates: no network, host calls, model loading or GPU."""
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

P = Path(__file__).resolve().parents[1] / 'tools/benchmarks'
spec = importlib.util.spec_from_file_location('verify_latest_sources', P/'verify_latest_sources.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
manifest = json.loads((P/'latest_engine_sources_20261023.json').read_text())


def snapshot(path):
    if 'stew675' in path: k='rdna'
    elif 'AtomicBot-ai' in path: k='atomic'
    elif 'Niko1221' in path: k='strata'
    elif 'ggml-org' in path: k='upstream'
    elif 'PrismML-Eng' in path: k='prism'
    else: raise AssertionError('Unexpected API endpoint: '+path)
    entry = manifest['github_repositories'][k]
    if path.endswith('/releases/latest'):
        return {'tag_name':entry['release_tag']}
    if '/git/tags/' in path:
        return {'object':{'type':'commit','sha':entry.get('release_commit','011c9e600a93bbc9fd451c563501b5831c32bbca')}}
    return {'object':{'type':'commit','sha':entry.get('release_commit',entry.get('commit','011c9e600a93bbc9fd451c563501b5831c32bbca'))}}


class LiveFreshnessGate(unittest.TestCase):
    def test_all_five_sources_current(self):
        results=mod.verify_all(manifest,snapshot)
        self.assertEqual(len(results),5)
        self.assertEqual({x['source'] for x in results},{'rdna','upstream','prism','atomic','strata'})

    def test_current_candidate_verified_live(self):
        entry=mod.verify_candidate('rdna-r113-hip-4b',manifest,snapshot)
        self.assertEqual(entry['track'],'release:v14-097cf33d9-r113')
        self.assertTrue(entry['checked_at_utc'])

    def test_latest_release_replaces_pin(self):
        def newer(path):
            if 'stew675' in path and path.endswith('/releases/latest'):
                return {'tag_name':'v14-097cf33d9-r114'}
            return snapshot(path)
        with self.assertRaisesRegex(mod.StaleSource, 'r114'):
            mod.verify_candidate('rdna-r113-hip-4b',manifest,newer)

    def test_latest_head_change_replaces_pin(self):
        def newer(path):
            if 'ggml-org' in path and '/git/ref/heads/' in path:
                return {'object':{'type':'commit','sha':'a'*40}}
            return snapshot(path)
        with self.assertRaisesRegex(mod.StaleSource,'HEAD'):
            mod.verify_candidate('upstream-master-4b',manifest,newer)

    def test_moved_release_tag_refused(self):
        def moved(path):
            if 'AtomicBot-ai' in path and '/git/ref/tags/' in path:
                return {'object':{'type':'commit','sha':'b'*40}}
            return snapshot(path)
        with self.assertRaisesRegex(mod.StaleSource,'tag resolved'):
            mod.verify_candidate('atomic4b',manifest,moved)

    def test_annotated_tag_resolves_to_commit(self):
        def tagged(path):
            if 'stew675' in path and '/git/ref/tags/' in path:
                return {'object':{'type':'tag','sha':'c'*40}}
            if 'stew675' in path and '/git/tags/' in path:
                return {'object':{'type':'commit','sha':manifest['github_repositories']['rdna']['release_commit']}}
            return snapshot(path)
        self.assertEqual(mod.verify_candidate('rdna-r113-hip-4b',manifest,tagged)['source'],'rdna')

    def test_offline_is_unverified_not_approved(self):
        def no_network(path):
            raise mod.UnverifiedSource('GITHUB_UNREACHABLE')
        with self.assertRaises(mod.UnverifiedSource):
            mod.verify_candidate('prism-head-4b',manifest,no_network)

    def test_stale_historical_engine_never_admitted(self):
        for legacy in ('b11798-4b','rdna-r111-hip-4b','rdna-r112-hip-4b','b11798-hermes9b'):
            with self.subTest(legacy=legacy):
                with self.assertRaisesRegex(mod.StaleSource,'RETIRED'):
                    mod.verify_candidate(legacy,manifest,snapshot)

    def test_source_url_outside_official_github_denied(self):
        bad={**manifest['github_repositories']['rdna'],'repository':'https://example.com/stew675/repo'}
        with self.assertRaises(mod.UnverifiedSource):
            mod.verify_one('rdna',bad,snapshot)

    def test_replay_legacy_source_hash_never_approved(self):
        pinned=dict(manifest['github_repositories']['upstream'])
        pinned['commit']='9febe63d5a379f8568bae7116a5b2ba844a4a4a6'
        with self.assertRaises(mod.StaleSource):
            mod.verify_one('upstream',pinned,snapshot)

    def test_missing_gh_cli_fails_closed(self):
        with patch.object(mod.subprocess,'run',side_effect=FileNotFoundError('gh')):
            with self.assertRaises(mod.UnverifiedSource):
                mod.github_api('repos/ggml-org/llama.cpp/git/ref/heads/master')


if __name__=='__main__':
    unittest.main(verbosity=2)
