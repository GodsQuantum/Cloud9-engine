#!/usr/bin/env python3
"""Mock GPU exclusive lock tests: VoiceStudio idle preemption and restoration."""
import ast
import fcntl
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import Mock

SOURCE=Path(__file__).resolve().parents[1]/"bin/cloud9-model-router.py"

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.track=[]
        self.voice=True
        self.busy=False
        self.foreign=[]
        t=ast.parse(SOURCE.read_text())
        block=[x for x in t.body if isinstance(x,ast.ClassDef) and x.name=="RouterState"]
        assert len(block)==1
        outer=self
        def docker(*args,**kwargs):
            outer.track.append(("docker",args[0],args[-1]))
            if args[0]=="stop" and args[-1]=="voicestudio":
                outer.voice=False
            if args[0]=="start" and args[-1]=="voicestudio":
                outer.voice=True
            return types.SimpleNamespace(returncode=0,stdout="")
        self.ns={
            "threading":threading,
            "fcntl":fcntl,
            "time":types.SimpleNamespace(monotonic=lambda:0,sleep=lambda _:None),
            "GPU_LOCK":str(Path(self.tmp.name)/"gpu.lock"),
            "SPEACHES_CONTAINER":"speaches",
            "VOICE_CONTAINER":"voicestudio",
            "EMBED_SERVICE":"cloud9-embedding.service",
            "catalog":{"defaults":{"gpu_mode":"exclusive"}},
            "service_active":lambda _:False,
            "container_running":lambda x:outer.voice if x=="voicestudio" else False,
            "idle_voicestudio_gpu_id":lambda:"voice-id" if not outer.busy else "",
            "embedding_busy":lambda:False,
            "tcp_port_busy":lambda _:False,
            "run_systemctl":Mock(),
            "run_docker":docker,
            "gpu_users":lambda:outer.foreign,
            "mem_available_mib":lambda:50000,
            "gtt_used_mib":lambda:200
        }
        exec(compile(ast.fix_missing_locations(ast.Module(body=block,type_ignores=[])),
                     str(SOURCE),"exec"),self.ns)
        self.router=self.ns["RouterState"]()

    def tearDown(self):
        if self.router.gpu_fd:
            self.router.release_gpu()
        self.tmp.cleanup()

    def test_idle_voice_preempted_and_restored_for_exclusive(self):
        self.router.acquire_gpu({"id":"Pym","gpu_mode":"exclusive"},timeout=1)
        self.assertFalse(self.voice)
        self.assertTrue(self.router.voice_was_running)
        self.router.release_gpu()
        self.assertTrue(self.voice)
        self.assertFalse(self.router.voice_was_running)
        self.assertEqual([x[1] for x in self.track if x[2]=="voicestudio"],["stop","start"])

    def test_busy_voice_refused_before_disrupting_any_services(self):
        self.busy=True
        with self.assertRaisesRegex(RuntimeError,"VoiceStudio is busy"):
            self.router.acquire_gpu({"id":"Pym","gpu_mode":"exclusive"},timeout=1)
        self.assertTrue(self.voice)
        self.assertEqual(self.track,[])
        self.assertIsNone(self.router.gpu_fd)

    def test_voice_not_running_is_not_started_unexpectedly(self):
        self.voice=False
        self.router.acquire_gpu({"id":"Pym","gpu_mode":"exclusive"},timeout=1)
        self.router.release_gpu()
        self.assertFalse(self.voice)
        self.assertEqual(self.track,[])

    def test_gpu_foreign_user_after_voice_stop_forces_restore(self):
        self.foreign=[(99,"foreign-user","foreign-cgroup")]
        with self.assertRaisesRegex(RuntimeError,"incompatible users"):
            self.router.acquire_gpu({"id":"Pym","gpu_mode":"exclusive"},timeout=1)
        self.assertTrue(self.voice)
        self.assertEqual([x[1] for x in self.track if x[2]=="voicestudio"],["stop","start"])
        self.assertIsNone(self.router.gpu_fd)

    def test_no_voice_stop_for_light_coexistence(self):
        self.ns["container_id"]=lambda x:"voice-id"
        self.ns["light_gpu_user"]=lambda *args:True
        self.router.acquire_gpu({"id":"MiniCPM","gpu_mode":"coexist-light"},timeout=1)
        self.assertTrue(self.voice)
        self.assertEqual(self.track,[])
        self.router.release_gpu()
        self.assertEqual(self.track,[])

if __name__=="__main__":
    unittest.main(verbosity=2)
