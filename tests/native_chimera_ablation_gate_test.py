#!/usr/bin/env python3
"""Offline fail-closed tests for isolated current-source MMB+MMF32 experiments."""
import importlib.util,json,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('latest_bench',R/'tools/benchmarks/live_quality12_mtp_20261022.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
m=json.loads((R/'tools/benchmarks/latest_engine_sources_20261023.json').read_text())

def mock(path):
 if 'ggml-org' in path:key='upstream'
 elif 'stew675' in path:key='rdna'
 elif 'PrismML' in path:key='prism'
 else:raise AssertionError(path)
 v=m['github_repositories'][key]
 if path.endswith('/releases/latest'):return {'tag_name':v['release_tag']}
 return {'object':{'type':'commit','sha':v.get('release_commit',v.get('commit'))}}

class NativeChimeraAB(unittest.TestCase):
 def test_three_modes_same_binary_and_model(self):
  modes=('chimera-f502-mmb-off','chimera-f502-mmb-on','chimera-f502-mmb-mmf32')
  specs=[b.CANDIDATES[x] for x in modes]
  self.assertEqual(len({str(x['bin']) for x in specs}),1)
  self.assertIn("latest-chimera-mmb-r117-on-masterf502-hip-20261023",str(specs[0]["bin"]))
  self.assertEqual(len({str(x['model']) for x in specs}),1)
  self.assertEqual({x['backend'] for x in specs},{'HIP'})
  self.assertEqual([x['env']['GGML_CUDA_MMB'] for x in specs],['0','1','1'])
  self.assertEqual([x['env']['GGML_CUDA_MMF32'] for x in specs],['0','0','1'])
  self.assertEqual({x['env']['GGML_CUDA_MMB_RDNA3'] for x in specs},{'1'})
 def test_two_independent_current_attestations(self):
  for name in ('chimera-f502-mmb-off','chimera-f502-mmb-on','chimera-f502-mmb-mmf32'):
   with self.subTest(name=name):
    d=b.validate_latest_only(name,live_api=mock,_test_skip_binary_sha=True)
    a=d['_freshness_attestation']
    self.assertEqual(a['commit'],m['github_repositories']['upstream']['commit'])
    self.assertEqual(a['rdna_donor']['commit'],m['github_repositories']['rdna']['release_commit'])
 def test_donor_release_changed_denied(self):
  def newer(path):
   if 'stew675' in path and path.endswith('/releases/latest'):return {'tag_name':'v14-097cf33d9-r118'}
   return mock(path)
  with self.assertRaisesRegex(Exception,'STALE rdna'):
   b.validate_latest_only('chimera-f502-mmb-on',live_api=newer,_test_skip_binary_sha=True)
 def test_trunk_head_changed_denied(self):
  def newer(path):
   if 'ggml-org' in path:return {'object':{'type':'commit','sha':'a'*40}}
   return mock(path)
  with self.assertRaisesRegex(Exception,'STALE upstream'):
   b.validate_latest_only('chimera-f502-mmb-on',live_api=newer,_test_skip_binary_sha=True)
 def test_same_compiled_binary_identity_and_hip_baseline_not_ready(self):
  modes=('chimera-f502-mmb-off','chimera-f502-mmb-on','chimera-f502-mmb-mmf32')
  self.assertEqual({m['lab_candidate_binary_sha256'][name] for name in modes},{'e987022084a2e03f07c33c606f034a6cb55b3db873fce5a8f025ec8f3f08e810'})
  # The baseline ABI is SHA-verified, but it is NOT GPU-qualified yet.
  self.assertEqual(m['lab_candidate_binary_sha256']['upstream-f502-hip-4b'], 'c271dc4d8d5e74891018191ec0b8439c1df124bccc69064159b7a24ea279cece')
  self.assertFalse(m.get('production_eligible',False))
 def test_historical_engine_is_not_allowed(self):
  self.assertNotIn('rdna-r114-hip-4b',b.LATEST_ONLY_CANDIDATES)
  self.assertNotIn('b11798-4b',b.LATEST_ONLY_CANDIDATES)
if __name__=='__main__':unittest.main(verbosity=2)
