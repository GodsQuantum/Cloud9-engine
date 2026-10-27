import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
QUAL=ROOT/'tools/qualification'
sys.path.insert(0,str(QUAL))
spec=importlib.util.spec_from_file_location('flashnext_ad427_native_smoke',QUAL/'flashnext_ad427_native_smoke.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class NativeFlashSmokeTest(unittest.TestCase):
    def test_exact_model_and_draft_and_gpu_offload(self):
        a=module.COMMAND
        self.assertIn('--n-cpu-moe',a)
        self.assertEqual(a[a.index('--n-cpu-moe')+1],'48')
        self.assertIn('-ngl',a)
        self.assertEqual(a[a.index('-ngl')+1],'99')
        self.assertEqual(a[a.index('--spec-draft-n-max')+1],'3')
        self.assertEqual(a[a.index('--spec-type')+1],'draft-mtp')
        self.assertEqual(a[a.index('-md')+1],str(module.DRAFT))
        self.assertIn('per_layer_token_embd\\.weight=CPU',a)
        self.assertEqual(a[a.index('--moe-cache')+1],'off')
        self.assertEqual(a[a.index('--tensor-read-lazy')+1],'on')
        self.assertEqual(a[a.index('--load-mode')+1],'mmap')
        self.assertNotIn('--mlock',a)
        self.assertNotIn('--no-mmap',a)
        self.assertNotIn('--no-host',a)
        self.assertTrue(str(module.TARGET).endswith('-00001-of-00033.gguf'))

    def test_preflight_refuses_busy_guard_without_any_gpu_use(self):
        g={'allow':False,'mem_available_gib':35,'psi_memory_full_avg10':0,'swap_used_percent':40}
        with patch.object(module.gate,'guardian',return_value=g),patch.object(module.gate,'psi_io_full',return_value=0),patch.object(module.gate,'host_temp',return_value=62),patch.object(module.gate,'embeddings_busy',return_value=False),patch.object(module.gate,'fetch',side_effect=[{'worker_model':None},{'status':'ok','loaded_models':[]}]):
            x=module.readonly_preflight()
        self.assertFalse(x['allow']);self.assertIn('OFFICIAL_GPU_GUARD_DENIED',x['reasons'])

    def test_io_and_memory_psi_fail_closed(self):
        g={'allow':True,'mem_available_gib':36,'psi_memory_full_avg10':2,'swap_used_percent':40}
        with patch.object(module.gate,'guardian',return_value=g),patch.object(module.gate,'psi_io_full',return_value=12),patch.object(module.gate,'host_temp',return_value=62),patch.object(module.gate,'embeddings_busy',return_value=False),patch.object(module.gate,'fetch',side_effect=[{'worker_model':None},{'status':'ok','loaded_models':[]}]):
            x=module.readonly_preflight()
        self.assertFalse(x['allow'])
        self.assertIn('HOST_MEMORY_PSI',x['reasons'])
        self.assertIn('HOST_IO_PSI',x['reasons'])

    def test_embedded_service_busy_still_blocks_by_default(self):
        health={'allow':True,'mem_available_gib':36,'psi_memory_full_avg10':0,'swap_used_percent':40}
        with patch.object(module.gate,'guardian',return_value=health),patch.object(module.gate,'psi_io_full',return_value=0),patch.object(module.gate,'host_temp',return_value=62),patch.object(module.gate,'embeddings_busy',return_value=True),patch.object(module.gate,'fetch',side_effect=[{'worker_model':None},{'status':'ok','loaded_models':[]}]):
            x=module.readonly_preflight()
        self.assertFalse(x['allow'])
        self.assertIn('EMBEDDINGS_ACTIVE_OR_UNKNOWN',x['reasons'])

    def test_owner_coexist_only_when_physical_gpu_is_measured_idle(self):
        health={'allow':True,'mem_available_gib':36,'psi_memory_full_avg10':0,'swap_used_percent':40}
        for physically_idle in (False,True):
            with patch.object(module.gate,'guardian',return_value=health),patch.object(module.gate,'psi_io_full',return_value=0),patch.object(module.gate,'host_temp',return_value=62),patch.object(module.gate,'embeddings_busy',return_value=True),patch.object(module,'measured_gpu_physically_idle',return_value=physically_idle),patch.object(module.gate,'fetch',side_effect=[{'worker_model':None},{'status':'ok','loaded_models':[]}]):
                x=module.readonly_preflight(owner_idle_coexist=True)
            self.assertEqual(x['allow'],physically_idle)
            self.assertEqual(x['owner_measured_gpu_idle_coexist'],physically_idle)

    def test_calibrated_gtt_request_keeps_native_guard_authoritative(self):
        health={'allow':False,'mem_available_gib':29,'psi_memory_full_avg10':0,'swap_used_percent':42}
        with patch.object(module.gate,'guardian',return_value=health) as g,patch.object(module.gate,'psi_io_full',return_value=0),patch.object(module.gate,'host_temp',return_value=62),patch.object(module.gate,'embeddings_busy',return_value=False),patch.object(module.gate,'fetch',side_effect=[{'worker_model':None},{'status':'ok','loaded_models':[]}]):
            info=module.readonly_preflight(owner_compact_start=True,required_gtt_gib=10.0)
        g.assert_called_once_with(10.0)
        self.assertFalse(info['allow'])
        self.assertEqual(info['required_gtt_gib'],10.0)
        self.assertEqual(info['start_ram_floor_gib'],26)
        self.assertIn('OFFICIAL_GPU_GUARD_DENIED',info['reasons'])

    def test_owner_compact_start_requires_26_gib_no_unconditional_override(self):
        h={'allow':True,'mem_available_gib':25,'psi_memory_full_avg10':0,'swap_used_percent':42}
        with patch.object(module.gate,'guardian',return_value=h),patch.object(module.gate,'psi_io_full',return_value=0),patch.object(module.gate,'host_temp',return_value=62),patch.object(module.gate,'embeddings_busy',return_value=False),patch.object(module.gate,'fetch',side_effect=[{'worker_model':None},{'status':'ok','loaded_models':[]}]):
            info=module.readonly_preflight(owner_compact_start=True,required_gtt_gib=10.0)
        self.assertFalse(info['allow'])
        self.assertIn('HOST_AVAILABLE_RAM_BELOW_26GIB',info['reasons'])

    def test_trusted_graph_shape_and_source_unchanged(self):
        a=json.loads((ROOT/'certification/flashnext_frspec_native_qualification_20261026.json').read_text())
        x=a['actual_target_vs_draft_metadata_comparison']
        self.assertEqual(x['both_gguf_arch'],'qwen4exp')
        self.assertEqual(x['target_block_count'],48)
        self.assertEqual(x['draft_block_count_including_MTP'],49)
        self.assertEqual(x['both_expert_count'],512)
        self.assertFalse(a['production_mutated'])

if __name__=='__main__':unittest.main()
