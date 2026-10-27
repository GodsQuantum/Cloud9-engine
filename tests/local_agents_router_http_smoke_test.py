import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
ROUTER=ROOT/"tools/local_agents/cloud9-model-router-safe-lab-20261024.py"

class IsolatedHttp(unittest.TestCase):
 def test_preemptive_exclusive_denied_http_no_worker(self):
  # Server uses only temporary files, fake 16-byte weights, a nonexistent
  # backend, and loopback. Failure to gate would attempt backend-not-found,
  # which is separately asserted NOT to happen.
  with tempfile.TemporaryDirectory() as tmp:
   tmp=Path(tmp)
   model=tmp/"mock.gguf"
   model.write_bytes(b"GGUF"+bytes(12))
   catalog=tmp/"model-catalog.json"
   catalog.write_text(json.dumps({"models":[{
       "id":"Cloud9-Mock-Exclusive","model":str(model),
       "backend":"nonexistent","gpu_mode":"exclusive","extra_args":[]
       }],"defaults":{"gpu_mode":"exclusive","max_model_bytes":42949672960}}))
   # Choose a free loopback-only random port and release it immediately.
   import socket
   with socket.socket() as sock:
    sock.bind(("127.0.0.1",0))
    port=sock.getsockname()[1]
   cmd=[sys.executable,"-B",str(ROUTER),"--host","127.0.0.1","--port",str(port),
     "--catalog",str(catalog),"--engine-home",str(tmp),"--idle-seconds","3"]
   env=os.environ.copy()
   env.pop("CLOUD9_ENGINE_ALLOW_SERVICE_PREEMPTION",None)
   proc=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env)
   try:
    prefix="http://127.0.0.1:"+str(port)
    for _ in range(40):
     if proc.poll() is not None:
      self.fail("LAB router unexpectedly exited")
     try:
      with urllib.request.urlopen(prefix+"/health",timeout=.4) as h:
       status=json.load(h)
      break
     except (OSError,urllib.error.URLError):
      time.sleep(.08)
    else:self.fail("LAB router loopback health timeout")
    self.assertEqual(status["worker_model"],None)
    with urllib.request.urlopen(prefix+"/v1/models",timeout=2) as r:
     self.assertEqual(len(json.load(r)["data"]),1)
    request=urllib.request.Request(prefix+"/v1/chat/completions",
      data=json.dumps({"model":"Cloud9-Mock-Exclusive",
                       "messages":[{"role":"user","content":"hello"}]}).encode(),
      headers={"Content-Type":"application/json"},method="POST")
    with self.assertRaises(urllib.error.HTTPError) as ctx:
     urllib.request.urlopen(request,timeout=3)
    self.assertEqual(ctx.exception.code,503)
    with ctx.exception as denied:
     body=json.load(denied)
    self.assertIn("maintenance opt-in",body["error"]["message"])
    self.assertNotIn("nonexistent",body["error"]["message"])
    with urllib.request.urlopen(prefix+"/health",timeout=2) as r:
     self.assertIsNone(json.load(r)["worker_model"])
    self.assertFalse((tmp/"state/model-router-worker.log").exists())
   finally:
    proc.terminate()
    try:proc.communicate(timeout=4)
    except subprocess.TimeoutExpired:
     proc.kill()
     proc.communicate(timeout=4)
if __name__=="__main__":unittest.main()
