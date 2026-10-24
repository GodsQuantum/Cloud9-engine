#!/usr/bin/env python3
"""Verify LAB scorecard is evidence-backed and never promotes short GPU samples."""
import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cloud9_2k_score',ROOT/'tools/benchmarks/cloud9_ct410_nvme_scorecard.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
class TestLabScoreboard(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.base=Path(self.temporary.name)
        self.run=self.base/'nvme-lite-20261023T000000Z'
        self.run.mkdir()
    def tearDown(self):
        self.temporary.cleanup()
    def row(self,name,pp=125.7,tg=24.8,passed=True,reason=None):
        logfile=self.run/(name+'.log')
        logfile.write_text('Prompt: '+str(pp)+' t/s | Generation: '+str(tg)+' t/s')
        return {'name':name,'pass':passed,'reason':reason,'return_code':0 if passed else -15,
                'speed_tps':{'pp':pp,'tg':tg},'log':str(logfile),
                'sha256_log':hashlib.sha256(logfile.read_bytes()).hexdigest()}
    def save(self,*rows):
        (self.run/'results.json').write_text(json.dumps({'status':'COMPLETE_EXPLORATORY','rows':rows}))
    def test_provenance_checked_and_no_auto_promotion(self):
        self.save(self.row('production'),self.row('vulkan9ff',pp=119.4,tg=22.5))
        d=M.build(self.base)
        self.assertEqual(d['valid_runs'],2)
        self.assertEqual(d['excluded_runs'],0)
        self.assertFalse(d['production_eligible'])
        self.assertFalse(d['certified'])
        self.assertFalse(d['full_16k_qualified'])
        self.assertTrue(d['hall_of_fame_unchanged'])
        self.assertEqual(d['paired'][0]['generation_delta_pct'],-9.27)
        self.assertEqual(d['paired'][0]['prefill_delta_pct'],-5.01)
    def test_tamper_log_sha_is_excluded(self):
        row=self.row('production')
        self.save(row)
        (self.run/'production.log').write_text('modified after original hash')
        d=M.build(self.base)
        self.assertEqual(d['valid_runs'],0)
        self.assertEqual(d['excluded_runs'],1)
    def test_aborted_even_with_speed_is_excluded(self):
        row=self.row('vulkan9ff',pp=60.8,tg=23.8,passed=False,reason='MEMORY_PRESSURE')
        self.save(row)
        d=M.build(self.base)
        self.assertEqual(d['valid_runs'],0)
        self.assertEqual(d['excluded_runs'],1)
        self.assertEqual(len(d['paired']),0)
    def test_no_fake_pair_from_independent_trials(self):
        self.save(self.row('production'))
        run2=self.base/'nvme-lite-20261023T000001Z';run2.mkdir()
        p=run2/'vulkan9ff.log';p.write_text('Prompt: 115.0 t/s | Generation: 23.7 t/s')
        (run2/'results.json').write_text(json.dumps({'rows':[{
            'name':'vulkan9ff','pass':True,'return_code':0,'reason':None,
            'speed_tps':{'pp':115,'tg':23.7},
            'log':str(p),'sha256_log':hashlib.sha256(p.read_bytes()).hexdigest()}]}))
        d=M.build(self.base)
        self.assertEqual(d['valid_runs'],2)
        self.assertEqual(len(d['paired']),0)
    def test_summary_markdown_warns_uncertified(self):
        self.save(self.row('production'))
        doc=M.build(self.base)
        rendered=M.markdown(doc)
        self.assertIn('NOT CERTIFIED',rendered)
        self.assertIn('production',rendered)
        self.assertIn('SHA256=',rendered)
if __name__=='__main__':unittest.main()
