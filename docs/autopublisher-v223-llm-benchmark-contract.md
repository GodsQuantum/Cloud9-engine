# AutoPublisher V22.3: LLM-only benchmark contract (Cloud9, 13 October 2026)

This document is about **actual AutoPublisher LLM node definitions** and **read-only verification**, not the old AutoPublisher V21 synthetic fixture, live n8n execution, any publication, or new GPU inference.

## Workflow and prompt authority

Canonical AutoPublisher project: `/srv/storage/cloud/arezki/Projets/Ssker Content Production/n8n Publishers/`.

The two system prompts are `04-workflow/editorial_extractor_prompt.md` and `04-workflow/voice_copy_pack_prompt.md`. They are large, separate stages; run one **editorial extraction** over the transcript, then **voice copy** over its structured editorial results. The repair stage consumes errors and copy, using the same voice system prompt. Do not collapse the stages into the much shorter V21 `quality_prompt()` used in older engine benchmarks.

The archive `04-workflow/AUTOPUBLISHER_V22_OMNIROUTE.json` is **marked active in its export**, but its actual **currently deployed n8n state has NOT been verified**. Its three relevant nodes are:

| Node | In-export model alias | Temperature | Output limit | HTTP timeout |
| --- | --- | --- | --- | --- |
| Editorial Extractor | `Flash` | 0.15 | 3000 tokens | 120 seconds |
| Voice Copy Pack | `Free` | 0.68 | 4200 tokens | 120 seconds |
| Repair Copy | `Flash` | 0.30 | 4200 tokens | 150 seconds |

Endpoint in this snapshot: `http://192.168.1.218:20128/v1/chat/completions`, OpenAI-style JSON requests. **The DNS/IP is not itself proof of backend inference engine or active deployment**.

Compared byte-for-byte after decoding the embedded JavaScript string literal, the exported **voice-copy and repair** system prompts match the current canonical voice prompt. The **editorial** prompt differs only in two respects identified by `difflib`: an old 2-item English props example versus the current 1–3 causally relevant prop instructions, and an extra trailing blank line in the file. Therefore **do not use the raw export as a perfect representation of the current prompt version without reconciling that drift**.

The archival `05-tests/AUTOPUBDRYRUN_DPAFM48_V223_LOCAL.json`, marked inactive, instead labels all three model calls `Cloud9-Engine`, uses 900-second timeouts and embeds older copies of both prompts. It is a **test export**, not a representation of the active OmniRoute route.

## Offline source-control audit

`scripts/autopublisher-llm-contract.py` validates an exported workflow without network, n8n calls, GPU, secrets or transcript printing. It checks exact system prompt SHA256, the three expected nodes, aliases, JSON-object schema, temperatures, max output and timeout, and HTTP-request transport.

Run on Cloud9 (read-only):

```bash
ROOT='/srv/storage/cloud/arezki/Projets/HomeLab/Moteurs IA'
AP='/srv/storage/cloud/arezki/Projets/Ssker Content Production/n8n Publishers'
python3 "$ROOT/Cloud9 Engine/scripts/autopublisher-llm-contract.py" \
  --workflow "$AP/04-workflow/AUTOPUBLISHER_V22_OMNIROUTE.json" \
  --prompts "$AP/04-workflow"
```

Add `--require-current-prompts` for a strict gate: exit code 5 when any system prompt differs. **The known V22 OmniRoute export currently exits 5 in strict mode**, specifically because its editorial props instruction is older. A read-only audit passing **does not** mean AutoPublisher or n8n was executed.

Six isolated Python tests in `tests/autopublisher-llm-contract-test.py` prove correct matching, change detection, secret/text non-disclosure, malformed/duplicate node rejection, unsafe transport rejection and model alias validation. Tests do not require model weights or a real n8n instance.

## Real performance/correctness campaign — UNEXECUTED pending GPU recovery

Before claiming `Cloud9-Engine` can replace OmniRoute `Flash`/`Free` for AutoPublisher, run the **same snapshot prompts, metadata, transcript compaction, show profile and editorial schema** with the true V22.3 workflow and at least 3 varied real podcast transcripts. Measure each *stage separately* and end-to-end, with normalized 0.15 and 0.68 temperatures where appropriate, grounded timecodes, JSON schema validity, anti-hallucination, author's actual voice, preview/repair rate, time to first token, prefill, decode tok/s, cold/warm load, peak RAM/GTT, CPU and GPU use, and p50/p95 with repeat runs.

Score not only speed: the rubric must favor the same topic throughout, accurate participant identities, genuinely funny and personal copy, no promotional filler, valid chapters, real evidence and useful visual prompts. Snapshot/scores should never log raw transcripts or personal contacts to the public GitHub repo/Hall of Fame. Store the **hash and protected local source path** in the single `HALL_OF_FAME.json`.

Then validate a genuine n8n LLM-only dry run without any publish/post/webhook side effects. For Archie, a read-only contacts/mail search is a separate agent integration test and must not trigger messages or editing. **No such real workflow test was run during this source audit** because the Cloud9 AMDGPU host preflight still fails with two kernel D-state tasks.

Do not change AutoPublisher's actual n8n workflow or its credential/provider aliases as a side effect of this engine source task. First obtain a current live export read-only and reconcile its prompt drift.
