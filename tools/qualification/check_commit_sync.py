#!/usr/bin/env python3
"""Git native commit guard: affected engine/test changes must update registry and handoff."""
import subprocess
import sys
cmd=["git","diff","--name-only","HEAD^","HEAD"]
changed=set(subprocess.check_output(cmd,text=True).splitlines())
affects=lambda f: any(f.startswith(p) for p in (
 "tools/chimera/","tools/local_agents/","tools/benchmarks/",
 "src/","patches/","tests/local_agents","tests/chimera"))
core=sorted(x for x in changed if affects(x))
if core:
 required={"certification/certification_registry.json","certification/NEXT_HANDOFF.md",
 "certification/CURRENT_STATUS.md"}
 missing=required-changed
 if missing:
  print("CERTIFICATION_SYNC_REQUIRED_FOR",", ".join(core[:10]))
  print("MISSING_GENERATED_FILES",", ".join(sorted(missing)))
  sys.exit(2)
 print("CERTIFICATION_SYNC_COMPLETE",len(core),"affected files")
else:
 print("NO_ENGINE_PROOF_AFFECTING_COMMIT")
