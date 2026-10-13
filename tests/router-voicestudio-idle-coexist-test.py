#!/usr/bin/env python3
"""Offline tests for conservative VoiceStudio/Cloud9 GPU coexistence admission."""
import ast
from pathlib import Path
import subprocess
import types
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
ROUTER=ROOT/"bin/cloud9-model-router.py"


def helpers():
    tree=ast.parse(ROUTER.read_text(encoding="utf-8"))
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef)
              and n.name in ("idle_voicestudio_gpu_id","light_gpu_user")]
    assert len(selected)==2
    ns={"subprocess":subprocess,"gtt_used_mib":lambda:200,
        "run_docker":lambda *a,**k:types.SimpleNamespace(returncode=0,stdout="healthy\n"),
        "container_id":lambda c:"f"*64}
    exec(compile(ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[])),
                 str(ROUTER),"exec"),ns)
    return ns


class VoiceAdmission(unittest.TestCase):
    def setUp(self):
        self.ns=helpers()
        self.original_run=subprocess.run
        self.ns["subprocess"]=types.SimpleNamespace(
            PIPE=-1,DEVNULL=-3,
            run=lambda *a,**k:types.SimpleNamespace(returncode=0,stdout=""))

    def test_known_idle_healthy_container_admitted(self):
        self.assertEqual(self.ns["idle_voicestudio_gpu_id"](),"f"*64)
        self.assertTrue(self.ns["light_gpu_user"]((17,"python3","0::/docker-"+"f"*64),
                                                  "", "f"*64))

    def test_model_active_gtt_over_512_refused(self):
        self.ns["gtt_used_mib"]=lambda:512
        self.assertEqual(self.ns["idle_voicestudio_gpu_id"](),"")

    def test_health_must_be_healthy(self):
        self.ns["run_docker"]=lambda *a,**k:types.SimpleNamespace(
            returncode=0,stdout="starting\n")
        self.assertEqual(self.ns["idle_voicestudio_gpu_id"](),"")

    def test_health_inspect_errors_fail_closed(self):
        self.ns["run_docker"]=lambda *a,**k:types.SimpleNamespace(
            returncode=1,stdout="")
        self.assertEqual(self.ns["idle_voicestudio_gpu_id"](),"")

    def test_busy_http_connection_blocks_admission(self):
        self.ns["subprocess"].run=lambda *a,**k:types.SimpleNamespace(
            returncode=0,stdout="ESTAB 127.0.0.1:3900")
        self.assertEqual(self.ns["idle_voicestudio_gpu_id"](),"")

    def test_port_inspection_failure_blocks(self):
        self.ns["subprocess"].run=lambda *a,**k:types.SimpleNamespace(
            returncode=1,stdout="")
        self.assertEqual(self.ns["idle_voicestudio_gpu_id"](),"")

    def test_ss_exception_blocks(self):
        self.ns["subprocess"].run=Mock(side_effect=OSError("no ss"))
        self.assertEqual(self.ns["idle_voicestudio_gpu_id"](),"")

    def test_unknown_gpu_user_still_blocked(self):
        self.assertFalse(self.ns["light_gpu_user"]((7,"unknown","0::/docker-unknown"),
                                                   "", "f"*64))
        self.assertFalse(self.ns["light_gpu_user"]((7,"python","0::/docker-"+"f"*64),"",""))

    def test_existing_embed_speaches_preserved(self):
        fn=self.ns["light_gpu_user"]
        self.assertTrue(fn((1,"llama","0::/cloud9-embedding.service"),"",""))
        self.assertTrue(fn((2,"python","0::/docker-"+"a"*64),"a"*64,""))

    def test_only_explicit_voice_container_id(self):
        fn=self.ns["light_gpu_user"]
        self.assertFalse(fn((2,"python","0::/docker-"+"b"*64),"","f"*64))

    def test_coexist_only_not_exclusive(self):
        tree=ast.parse(ROUTER.read_text(encoding="utf-8"))
        f=[node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef)
           and node.name=="acquire_gpu"]
        self.assertEqual(len(f),1)
        snippet=ast.get_source_segment(ROUTER.read_text(),f[0])
        self.assertIn('if mode=="coexist-light" else ""',snippet)
        self.assertIn('blocked=users if mode=="exclusive"',snippet)
        self.assertIn('idle_voicestudio_gpu_id()',snippet)
        self.assertIn("light_gpu_user(u,sid,vid)",snippet)


if __name__=="__main__":
    unittest.main(verbosity=2)
