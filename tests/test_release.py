"""Tests for the release lifecycle.

The package and the manifest describe the same set of files, and it is
possible for them to stop agreeing: a file is added to the repository and
hashed into the manifest but left out of the archive, or the other way
round. Nothing in the design system's own gates would notice, because the
gates read the repository and the archive is built from it afterwards.

These tests close that gap. They are the reason a distributable archive
that does not validate on its own is a failing test rather than a surprise
found by a consumer.
"""

import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from tools import release as release_tool

ROOT = Path(__file__).resolve().parents[1]


class ReleaseLifecycleTests(unittest.TestCase):
    def test_manifest_and_package_contain_the_same_files(self):
        """Every file the manifest hashes is a file the archive carries.

        The manifest is the authority on what the package contains, and the
        archive is the package. If the two disagree, a consumer that unpacks
        the archive and runs the gates gets a "missing file" error for
        something the manifest promised, or the manifest describes files
        that are not there to be checked.
        """
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        described = {item["path"] for item in manifest["files"]}
        packaged = {str(path.relative_to(ROOT)) for path in release_tool.packaged_files()}

        # The manifest does not hash itself: it is the index of the package,
        # and an index that contains its own digest cannot be regenerated
        # without changing the digest it is meant to record.
        described.add("manifest.json")

        self.assertEqual(
            described - packaged, set(),
            "the manifest describes files the archive does not carry")
        self.assertEqual(
            packaged - described, set(),
            "the archive carries files the manifest does not describe")

    def test_the_archive_contains_the_tools_and_the_tests(self):
        """The gates travel with the package.

        The README tells a consumer to run the validation from the package
        root before redistributing. That is only possible if the tools and
        the tests are in it.
        """
        packaged = {str(path.relative_to(ROOT)) for path in release_tool.packaged_files()}
        self.assertIn("tools/contract.py", packaged)
        self.assertIn("tools/ci.py", packaged)
        self.assertIn("tools/version.py", packaged)
        self.assertIn("tests/test_contract.py", packaged)

    def test_the_archive_carries_no_build_artifacts(self):
        packaged = {str(path.relative_to(ROOT)) for path in release_tool.packaged_files()}
        for path in packaged:
            with self.subTest(path=path):
                self.assertNotIn("__pycache__", path)
                self.assertNotIn(".pytest_cache", path)
                self.assertFalse(path.endswith(".pyc"))

    def test_the_archive_is_byte_reproducible(self):
        """The same commit produces the same archive.

        The published SHA-256 is a statement about the source, not about the
        machine that packed it. Sorted entries, fixed timestamps and a gzip
        header carrying neither a name nor a time are what make that true.
        """
        with tempfile.TemporaryDirectory() as tmp:
            first = release_tool.build_archive(release_tool.version())[0].read_bytes()
            second = release_tool.build_archive(release_tool.version())[0].read_bytes()
            self.assertEqual(hashlib.sha256(first).hexdigest(), hashlib.sha256(second).hexdigest())

    def test_the_archive_passes_its_own_gates(self):
        """A distributable archive that does not validate is not distributable.

        The gates are run, not the whole qualification: the test suite
        contains this test, and qualifying the extracted archive with the
        suite would qualify it with this test, which qualifies the archive
        again. The gates are the part of the contract that can be checked in
        a package without recursing.
        """
        with tempfile.TemporaryDirectory() as tmp:
            archive = release_tool.build_archive(release_tool.version())[0]
            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(tmp, filter="data")
            extracted = Path(tmp) / release_tool.archive_root(release_tool.version())
            result = subprocess.run(
                [sys.executable, "-m", "tools.ci", "--gates-only"],
                cwd=extracted, capture_output=True, text=True, check=False)
            self.assertEqual(
                result.returncode, 0,
                (result.stdout + result.stderr)[-4000:])

    def test_bump_computes_the_next_version(self):
        self.assertEqual(release_tool.bump("3.4.2", "patch"), "3.4.3")
        self.assertEqual(release_tool.bump("3.4.2", "minor"), "3.5.0")
        self.assertEqual(release_tool.bump("3.4.2", "major"), "4.0.0")
        self.assertEqual(release_tool.bump("3.9.9", "minor"), "3.10.0")

    def test_the_archive_is_named_for_its_version(self):
        version = release_tool.version()
        self.assertEqual(release_tool.archive_name(version), f"Gnosix-DS-V{version}.tar.gz")
        self.assertEqual(release_tool.archive_root(version), f"Gnosix-DS-V{version}")
        self.assertEqual(release_tool.tag_name(version), f"v{version}")

    def test_the_changelog_has_a_section_for_the_current_version(self):
        version = release_tool.version()
        notes = release_tool.changelog_section(version)
        self.assertIsNotNone(notes, f"CHANGELOG.md has no section for {version}")
        self.assertIn(version, notes)


if __name__ == "__main__":
    unittest.main()
