#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
python3 - "$ROOT/bin/cloud9-model-router.py" <<'PY'
import ast,sys
src=open(sys.argv[1]).read()
tree=ast.parse(src)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="model_oversize_decision")
ns={}
exec(compile(ast.Module(body=[fn],type_ignores=[]),sys.argv[1],"exec"),ns)
f=ns["model_oversize_decision"]
MiB=1024*1024
max_file=40*1024**3
special=30*1024**3

assert f({"id":"small"},2*MiB,max_file,special)==(True,"within-generic-limit")
assert f({"id":"lab"},50*1024**3,max_file,special,env_allow=True)==(True,"explicit-lab-override")
assert f({"id":"plain"},50*1024**3,max_file,special)==(False,"generic-oversize-refusal")

good={"id":"gyro","oversize_policy":"ngram-on-disk","extra_args":["--ngram-on-disk"],
      "estimated_resident_bytes":29*1024**3}
assert f(good,58*1024**3,max_file,special)==(True,"typed-ngram-on-disk")

bad_cases=[
 {"id":"missing-flag","oversize_policy":"ngram-on-disk","extra_args":[],"estimated_resident_bytes":29*1024**3},
 {"id":"too-large","oversize_policy":"ngram-on-disk","extra_args":["--ngram-on-disk"],"estimated_resident_bytes":31*1024**3},
 {"id":"unknown","oversize_policy":"magic","extra_args":[],"estimated_resident_bytes":1},
]
for case in bad_cases:
    try:
        f(case,58*1024**3,max_file,special)
    except RuntimeError:
        pass
    else:
        raise AssertionError(f"case should fail: {case}")
print("typed oversize policy test: PASS")
PY
