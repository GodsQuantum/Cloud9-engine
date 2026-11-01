#!/usr/bin/env python3
"""Refresh stable engine source locks; fail closed on invalid release metadata."""
import json
import re
import subprocess
from pathlib import Path
from datetime import date

p = Path(__file__).resolve().parents[1] / "sources.lock"
j = json.loads(p.read_text())

def remote(repo, ref):
    lines = subprocess.check_output(
        ["git", "ls-remote", repo, ref], text=True, timeout=30
    ).splitlines()
    if not lines:
        raise SystemExit(f"Missing remote ref {ref}: {repo}")
    return lines

def head(entry):
    ref = "refs/heads/" + entry.get("branch", "master")
    return remote(entry["repository"], ref)[0].split()[0]

def atomic_stable(entry):
    # Include annotated tag dereferences; a tag-object SHA is not its commit.
    versions = {}
    for line in remote(entry["repository"], "refs/tags/b*-*"):
        sha, ref = line.split(None, 1)
        tag = ref.removeprefix("refs/tags/").removesuffix("^{}")
        if not re.fullmatch(r"b[0-9]+-[0-9]+\.[0-9]+\.[0-9]+", tag):
            continue
        if ref.endswith("^{}") or tag not in versions:
            versions[tag] = sha
    if not versions:
        raise SystemExit("No verifiable Atomic release tags")
    def version_key(tag):
        build, semver = tag[1:].split("-", 1)
        return (*map(int, semver.split(".")), int(build))
    tag = max(versions, key=version_key)
    return tag, versions[tag]

changed = []
for key in ("upstream", "atomic", "prism"):
    if key not in j:
        continue
    entry = j[key]
    branch_sha = head(entry)
    if key == "atomic":
        tag, release_sha = atomic_stable(entry)
        # Atomic is release-first. Do not silently attach a stale tag to HEAD.
        if release_sha != branch_sha:
            raise SystemExit(
                f"Atomic release {tag} at {release_sha} differs from master "
                f"{branch_sha}; review stable vs development explicitly"
            )
        updates = {"commit": release_sha, "release": tag, "release_commit": release_sha}
    else:
        updates = {"commit": branch_sha}
    for field, value in updates.items():
        if entry.get(field) != value:
            changed.append((key + "." + field, entry.get(field), value))
            entry[field] = value
if changed:
    j["observed_on"] = str(date.today())
    j.pop("tested_on", None)
    p.write_text(json.dumps(j, indent=2) + "\n")
    for key, previous, current in changed:
        print(f"{key}: {str(previous)[:16]} -> {str(current)[:16]}")
else:
    print("sources.lock already current")
