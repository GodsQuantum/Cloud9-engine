#!/usr/bin/env python3
"""Fail-closed, live GitHub freshness gate for Cloud9's latest-only engine tournament.

No GPU usage, file mutations or daemon operations. Every live candidate is
checked against the provider's current refs/releases, not just its local pin.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

MANIFEST = Path(__file__).with_name("latest_engine_sources_20261023.json")


class StaleSource(RuntimeError):
    """The pinned source is no longer current. Re-pin and rebuild."""


class UnverifiedSource(RuntimeError):
    """GitHub is unreachable/ambiguous. Do not start a GPU benchmark."""


def _repo_path(url):
    u = urlparse(url)
    if u.scheme != "https" or u.hostname != "github.com":
        raise UnverifiedSource("UNTRUSTED_REPOSITORY_URL")
    parts = u.path.strip("/").removesuffix(".git").split("/")
    if len(parts) != 2 or not all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) for p in parts):
        raise UnverifiedSource("INVALID_GITHUB_REPOSITORY_PATH")
    return f"repos/{parts[0]}/{parts[1]}"


def github_api(path):
    """Use authenticated first-party gh CLI, with strict timeout; never guess on failure."""
    try:
        cp = subprocess.run(["gh", "api", path], capture_output=True,
                            text=True, check=False, timeout=18)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise UnverifiedSource("GITHUB_API_UNAVAILABLE") from exc
    if cp.returncode != 0:
        raise UnverifiedSource("GITHUB_API_FAILURE: " + cp.stderr.strip()[:180])
    try:
        data = json.loads(cp.stdout)
    except ValueError as exc:
        raise UnverifiedSource("GITHUB_API_BAD_JSON") from exc
    if not isinstance(data, dict):
        raise UnverifiedSource("GITHUB_API_BAD_RESPONSE")
    return data


def _sha(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise UnverifiedSource("GITHUB_API_MISSING_SHA")
    return value


def verify_one(name, meta, api=github_api):
    repo = _repo_path(meta["repository"])
    if name in ("upstream", "prism", "s1"):
        branch = meta["branch"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", branch):
            raise UnverifiedSource("INVALID_BRANCH")
        ref = api(f"{repo}/git/ref/heads/{branch}")
        current = _sha(ref.get("object", {}).get("sha"))
        pinned = _sha(meta["commit"])
        if current != pinned:
            raise StaleSource(f"STALE {name}: HEAD {current}, pinned {pinned}")
        return {"source": name, "track": f"HEAD:{branch}", "commit": current}

    if name not in ("rdna", "atomic", "strata"):
        raise UnverifiedSource(f"UNKNOWN_LATEST_TRACK {name}")
    latest = api(f"{repo}/releases/latest")
    tag = latest.get("tag_name")
    if not isinstance(tag, str) or not tag:
        raise UnverifiedSource(f"GITHUB_RELEASE_MISSING_TAG {name}")
    pinned_tag = meta["release_tag"]
    if tag != pinned_tag:
        raise StaleSource(f"STALE {name}: newest tag {tag}, pinned {pinned_tag}")
    ref = api(f"{repo}/git/ref/tags/{quote(tag, safe='-_.@')}")
    obj = ref.get("object")
    if not isinstance(obj, dict):
        raise UnverifiedSource("GITHUB_TAG_MISSING_OBJECT")
    for _ in range(4):
        sha = _sha(obj.get("sha"))
        if obj.get("type") == "commit":
            pinned = meta.get("release_commit")
            if pinned is not None and sha != _sha(pinned):
                raise StaleSource(f"STALE {name}: tag resolved to {sha}, pinned {pinned}")
            return {"source": name, "track": f"release:{tag}", "commit": sha}
        if obj.get("type") != "tag":
            raise UnverifiedSource(f"GITHUB_TAG_UNKNOWN_TYPE {name}")
        nested = api(f"{repo}/git/tags/{sha}")
        obj = nested.get("object")
        if not isinstance(obj, dict):
            raise UnverifiedSource("GITHUB_ANNOTATED_TAG_INVALID")
    raise UnverifiedSource("GITHUB_TAG_DEPTH_EXCEEDED")


CANDIDATE_TO_SOURCE = {
    "atomic4b": "atomic", "atomic4b-q8v": "atomic",
    "atomic4b-hip-turbo3": "atomic", "atomic4b-hip-q8v": "atomic",
    "rdna-r114-hip-4b": "rdna", "upstream-master-4b": "upstream",
    "prism-head-4b": "prism", "s1-head-4b": "s1",
}


def verify_candidate(candidate, manifest, api=github_api):
    if candidate not in CANDIDATE_TO_SOURCE:
        raise StaleSource(f"RETIRED_OR_UNKNOWN_CANDIDATE {candidate}")
    if manifest.get("production_approved"):
        raise UnverifiedSource("INVALID_LAB_MANIFEST")
    selected = CANDIDATE_TO_SOURCE[candidate]
    meta = manifest["github_repositories"].get(selected)
    if not isinstance(meta, dict):
        raise UnverifiedSource(f"PIN_MISSING {selected}")
    result = verify_one(selected, meta, api)
    result["candidate"] = candidate
    result["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
    return result


def verify_all(manifest, api=github_api):
    return [verify_one(k, v, api) for k, v in manifest["github_repositories"].items()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    exclusive = parser.add_mutually_exclusive_group(required=True)
    exclusive.add_argument("--candidate", choices=sorted(CANDIDATE_TO_SOURCE))
    exclusive.add_argument("--all", action="store_true")
    args = parser.parse_args()
    try:
        manifest = json.loads(MANIFEST.read_text())
        result = verify_all(manifest) if args.all else verify_candidate(args.candidate, manifest)
    except StaleSource as exc:
        print(f"STALE_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2
    except (UnverifiedSource, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"UNVERIFIED_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 3
    print(json.dumps({"status": "CURRENT", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
                      "result": result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
