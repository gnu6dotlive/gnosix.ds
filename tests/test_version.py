"""Tests for the version authority.

The version drifted three ways in V3.4.2: the manifest announced V3.4.0, the
web manifest announced V3.4.1, and nothing in the gate chain noticed. These
tests are the gate that would have noticed, and they are written so that the
next drift cannot be introduced quietly:

    - a slot that disagrees with VERSION fails the gate;
    - a slot that has disappeared fails the gate, rather than being skipped;
    - a slot added to a file that no pattern anchors is not silently adopted;
    - prose that names a past release is not a slot, and survives a bump;
    - the rewrite touches nothing but the version itself.
"""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools import version as version_tool

ROOT = Path(__file__).resolve().parents[1]


class VersionAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.version = version_tool.read_version()

    def test_version_file_is_a_semantic_version(self):
        self.assertRegex(self.version, r"^\d+\.\d+\.\d+$")

    def test_every_slot_agrees_with_the_version_file(self):
        problems = version_tool.check(self.version)
        self.assertEqual(problems, [], "\n".join(problems))

    def test_every_slot_is_found(self):
        """A slot that no longer matches its pattern is a failure, not a skip.

        The slot list is the authority on where the version appears. If a
        pattern stops matching because the markup moved, the version is now
        stated in a place the gate cannot see, and the gate must say so
        rather than report a clean run over the slots it still recognises.
        """
        for rel, pattern, description in version_tool.all_text_slots():
            with self.subTest(slot=f"{rel}: {description}"):
                self.assertIsNotNone(
                    version_tool.read_slot(rel, pattern),
                    f"the slot {description} in {rel} no longer matches its pattern")

    def test_json_slots_exist_and_are_top_level(self):
        for rel, key in version_tool.json_slots():
            with self.subTest(slot=f"{rel}:{key}"):
                data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
                self.assertIn(key, data, f"{rel} has no top-level {key}")
                self.assertEqual(data[key], self.version)

    def test_a_disagreeing_slot_fails_the_gate(self):
        """The gate must be able to fail, and fail for the right reason."""
        with tempfile.TemporaryDirectory() as tmp:
            original = version_tool.ROOT
            try:
                version_tool.ROOT = Path(tmp)
                (Path(tmp) / "core").mkdir()
                rulefile = Path(tmp) / "core/rules.json"
                rulefile.write_text(json.dumps({"version": "9.9.9", "rules": []}), encoding="utf-8")
                problems = version_tool.check(self.version)
                self.assertTrue(
                    any("core/rules.json" in problem and "9.9.9" in problem for problem in problems),
                    problems)
            finally:
                version_tool.ROOT = original

    def test_a_missing_slot_fails_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = version_tool.ROOT
            try:
                version_tool.ROOT = Path(tmp)
                (Path(tmp) / "core").mkdir()
                rulefile = Path(tmp) / "core/rules.json"
                rulefile.write_text(json.dumps({"rules": []}), encoding="utf-8")
                problems = version_tool.check(self.version)
                self.assertTrue(
                    any("no version key" in problem for problem in problems),
                    problems)
            finally:
                version_tool.ROOT = original

    def test_prose_naming_a_past_release_is_not_a_slot(self):
        """A version in running prose must survive a bump untouched.

        The site says things like "V3.4.2 ratifies the icon pack". That is a
        statement about a past release, not a slot, and rewriting it on every
        bump would falsify the history.
        """
        site = (ROOT / "site/index.html").read_text(encoding="utf-8")
        self.assertIn("V3.4.2 ratifies the icon pack", site)
        for pattern in (r'V3\.4\.2 ', r'>V3\.4\.2<'):
            for match in re.finditer(pattern, site):
                start = max(0, match.start() - 120)
                window = site[start:match.end() + 40]
                self.assertNotIn(
                    "gnosix-contract-version", window,
                    "a prose occurrence was matched by a slot pattern")

    def test_sync_changes_nothing_but_the_version(self):
        """The rewrite is surgical: no re-encoding, no incidental edits."""
        with tempfile.TemporaryDirectory() as tmp:
            original = version_tool.ROOT
            try:
                version_tool.ROOT = Path(tmp)
                for rel, _ in version_tool.json_slots():
                    target = Path(tmp) / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(
                        (ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")
                for rel, _, _ in version_tool.all_text_slots():
                    target = Path(tmp) / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(
                        (ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")

                changed = version_tool.sync("9.9.9")
                self.assertTrue(changed, "the sync changed nothing")

                # Normalising every version token away must make each file
                # identical to its original. Anything else is an edit the
                # rewrite made that has nothing to do with the version.
                for rel, _ in version_tool.json_slots():
                    with self.subTest(slot=rel):
                        before = (ROOT / rel).read_text(encoding="utf-8")
                        after = (Path(tmp) / rel).read_text(encoding="utf-8")
                        strip = lambda s: re.sub(r"\d+\.\d+\.\d+", "X", s)
                        self.assertEqual(strip(before), strip(after))
                for rel, _, _ in version_tool.all_text_slots():
                    with self.subTest(slot=rel):
                        before = (ROOT / rel).read_text(encoding="utf-8")
                        after = (Path(tmp) / rel).read_text(encoding="utf-8")
                        strip = lambda s: re.sub(r"\d+\.\d+\.\d+", "X", s)
                        self.assertEqual(strip(before), strip(after))
            finally:
                version_tool.ROOT = original

    def test_sync_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = version_tool.ROOT
            try:
                version_tool.ROOT = Path(tmp)
                for rel, _ in version_tool.json_slots():
                    target = Path(tmp) / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(
                        (ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")
                for rel, _, _ in version_tool.all_text_slots():
                    target = Path(tmp) / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(
                        (ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")

                version_tool.sync("9.9.9")
                first = {rel: (Path(tmp) / rel).read_text(encoding="utf-8")
                         for rel, _ in version_tool.json_slots()}
                for rel, _, _ in version_tool.all_text_slots():
                    first[rel] = (Path(tmp) / rel).read_text(encoding="utf-8")

                self.assertEqual(version_tool.sync("9.9.9"), [])
                for rel, text in first.items():
                    with self.subTest(slot=rel):
                        self.assertEqual((Path(tmp) / rel).read_text(encoding="utf-8"), text)
            finally:
                version_tool.ROOT = original

    def test_non_ascii_is_not_re_escaped(self):
        """Re-serialising a JSON file would un-escape its non-ASCII text.

        The reference scenes carry characters that were escaped when they
        were written. A rewrite that round-trips them through json.dumps
        changes bytes that have nothing to do with the version, in files that
        are hashed into the manifest.
        """
        actions = (ROOT / "references/actions.json").read_text(encoding="utf-8")
        if "\\u" not in actions:
            self.skipTest("this file carries no escaped non-ASCII text")
        with tempfile.TemporaryDirectory() as tmp:
            original = version_tool.ROOT
            try:
                version_tool.ROOT = Path(tmp)
                target = Path(tmp) / "references/actions.json"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(actions, encoding="utf-8")
                version_tool.write_json_slot("references/actions.json", "version", "9.9.9")
                rewritten = target.read_text(encoding="utf-8")
                self.assertIn("\\u", rewritten)
                self.assertIn('"version": "9.9.9"', rewritten)
            finally:
                version_tool.ROOT = original

    def test_cli_check_passes_on_the_repository(self):
        result = subprocess.run(
            [sys.executable, "-m", "tools.version", "--check"],
            cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_public_form_carries_the_leading_zero(self):
        self.assertEqual(version_tool.public_form("3.4.2"), "03.4.2")
        for rel, pattern, _ in version_tool.all_text_slots():
            with self.subTest(slot=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                if "gnosix_DS 0" in text and "gnosix_DS V" not in text:
                    self.assertIn(version_tool.public_form(self.version), text)


if __name__ == "__main__":
    unittest.main()
