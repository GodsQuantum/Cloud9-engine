#!/usr/bin/env python3
"""Source watch must suggest updates after CI, never auto-promote to main.

Run with Python stdlib only. No network, GPU, build, or production actions.
"""
from pathlib import Path
import re
import subprocess
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / ".github/workflows/source-watch.yml"


def run_blocks(source):
    lines = source.splitlines()
    blocks = []
    for i, line in enumerate(lines):
        if re.fullmatch(r"\s*run:\s*\|\s*", line):
            indent = len(line) - len(line.lstrip())
            collected = []
            for next_line in lines[i + 1:]:
                if next_line.strip():
                    level = len(next_line) - len(next_line.lstrip())
                    if level <= indent:
                        break
                collected.append(next_line)
            blocks.append(textwrap.dedent("\n".join(collected)))
    return blocks


class SourceWatchSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = FILE.read_text(encoding="utf-8")
        cls.blocks = run_blocks(cls.source)

    def test_has_schedule_but_not_main_push(self):
        self.assertIn("schedule:", self.source)
        self.assertIn("workflow_dispatch:", self.source)
        self.assertNotIn('git push origin "$candidate_sha:refs/heads/main"', self.source)
        self.assertNotRegex(self.source, r"git\s+push[^\n]*refs/heads/main")
        self.assertNotIn("gh issue close", self.source)

    def test_sources_are_compatible_before_proposal(self):
        self.assertIn('gh workflow run ci.yml --ref "$branch"', self.source)
        self.assertIn('gh run watch "$run_id" --exit-status', self.source)
        self.assertIn('gh pr create --base main --head "$branch" --draft', self.source)
        self.assertIn('gh pr edit "$existing"', self.source)
        self.assertIn("pull-requests: write", self.source)
        self.assertIn("main is unchanged", self.source)

    def test_candidate_branch_per_sha_never_forced(self):
        self.assertIn('branch="bot/source-sync-u', self.source)
        self.assertIn('git ls-remote --exit-code --heads origin "$branch"', self.source)
        self.assertNotIn("git push --force", self.source)
        self.assertIn('git push origin "$branch"', self.source)
        self.assertIn("preserving original CI and PR", self.source)

    def test_cannot_claim_hardware_certified_after_build(self):
        self.assertIn("NOT a hardware certification", self.source)
        self.assertIn("Cloud9 Radeon 780M correctness/stability", self.source)
        self.assertIn("Hall of Fame", self.source)
        self.assertIn("production promotion remains separate", self.source)

    def test_embedded_bash_syntax(self):
        self.assertGreaterEqual(len(self.blocks), 1)
        for index, body in enumerate(self.blocks):
            with self.subTest(block=index):
                proc = subprocess.run(["bash", "-n"], input=body, text=True, capture_output=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
