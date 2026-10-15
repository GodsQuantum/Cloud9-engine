#!/usr/bin/env python3
"""Unit-test GPU arbitration with mocks. No GPU, Docker or running services touched."""
import ast
import fcntl
from pathlib import Path
import tempfile
import threading
import time
import unittest

SOURCE=Path(__file__).resolve().parents[1]/"bin/cloud9-model-router.py"
TREE=ast.parse(SOURCE.read_text())
CLASS=next(x for x in TREE.body if isinstance(x,ast.ClassDef) and x.name=="RouterState")


class RouterVoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.containers={"speaches":False,"voicestudio":True}
        self.actions=[]
        self.clients=False
        env={
            "threading":threading,"time":time,"fcntl":fcntl,
            "GPU_LOCK":Path(self.temp.name)/"gpu.lock",
            "catalog":{"defaults":{"gpu_mode":"coexist-light","coexist_min_available_mib":12288,"coexist_max_gtt_mib":8192}},
            "EMBED_SERVICE":"cloud9-embedding.service",
            "SPEACHES_CONTAINER":"speaches",
            "VOICE_CONTAINER":"voicestudio",
            "mem_available_mib":lambda:49000,
            "gtt_used_mib":lambda:200,
            "service_active":lambda _:False,
            "container_running":lambda name:self.containers[name],
            "container_id":lambda name:"",
            "tcp_port_busy":lambda port:self.clients,
            "gpu_users":lambda:[],
            "run_systemctl":lambda *a,**kw:None,
        }
        def run_docker(*args,**_):
            self.actions.append(tuple(args))
            if args[0]=="stop":self.containers[args[-1]]=False
            if args[0]=="start":self.containers[args[-1]]=True
        env["run_docker"]=run_docker
        exec(compile(ast.fix_missing_locations(ast.Module(body=[CLASS],type_ignores=[])),str(SOURCE),"exec"),env)
        self.env=env
        self.router=env["RouterState"]()
        self.model={"id":"test-2b","gpu_mode":"coexist-light"}

    def test_idle_voice_yields_and_is_restored_at_unload(self):
        self.router.acquire_gpu(self.model)
        self.assertFalse(self.containers["voicestudio"])
        self.assertTrue(self.router.voice_was_running)
        self.assertEqual(len([a for a in self.actions if a[0]=="stop"]),1)
        self.router.release_gpu()
        self.assertTrue(self.containers["voicestudio"])
        self.assertFalse(self.router.voice_was_running)

    def test_active_voice_http_client_cannot_be_preempted(self):
        self.clients=True
        with self.assertRaisesRegex(RuntimeError,"active HTTP client"):
            self.router.acquire_gpu(self.model)
        self.assertTrue(self.containers["voicestudio"])
        self.assertFalse(self.actions)

    def test_gpu_admission_error_always_restores_voice(self):
        self.env["gpu_users"]=lambda: (_ for _ in ()).throw(RuntimeError("unclassified GPU user"))
        with self.assertRaisesRegex(RuntimeError,"unclassified GPU user"):
            self.router.acquire_gpu(self.model)
        self.assertTrue(self.containers["voicestudio"])
        self.assertEqual([a[0] for a in self.actions],["stop","start"])

    def test_no_voice_means_no_voice_lifecycle(self):
        self.containers["voicestudio"]=False
        self.router.acquire_gpu(self.model)
        self.router.release_gpu()
        self.assertEqual(self.actions,[])

if __name__=="__main__":
    unittest.main(verbosity=2)
