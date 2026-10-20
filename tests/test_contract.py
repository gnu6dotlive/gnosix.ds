import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.contract import contract_digest, validate_package


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def fixture(self, path="core/rules.json", *, profile_status="mapped", evidence=None, rules=None):
        (self.root / "core").mkdir(exist_ok=True)
        rulefile = self.root / "core/rules.json"
        rulefile.write_text(json.dumps({"rules": rules or [{"id": "COL-001"}]}))
        (self.root / "profiles/web").mkdir(parents=True, exist_ok=True)
        (self.root / "profiles/web/status.json").write_text(json.dumps({
            "profile": "web", "status": profile_status,
            "evidence": [] if evidence is None else evidence,
        }))
        self.manifest = {"version": "3.0.0", "contract_digest": "", "files": [{
            "path": path, "class": "core", "sha256": hashlib.sha256(rulefile.read_bytes()).hexdigest(),
        }]}
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))

    def test_rejects_escape_and_false_verification(self):
        self.fixture("../TOKENS.json", profile_status="verified", evidence=[])
        errors = validate_package(self.root)
        self.assertTrue(any("unsafe path" in error for error in errors), errors)
        self.assertTrue(any("verified requires evidence" in error for error in errors), errors)

    def test_duplicate_rule_ids(self):
        self.fixture(rules=[{"id": "COL-001"}, {"id": "COL-001"}])
        self.assertTrue(any("duplicate rule" in error for error in validate_package(self.root)))

    def test_rejects_wrong_hash(self):
        self.fixture()
        self.manifest["files"][0]["sha256"] = "0" * 64
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))
        self.assertTrue(any("hash mismatch" in error for error in validate_package(self.root)))

    def test_digest_uses_sorted_paths_and_file_hashes(self):
        (self.root / "b").write_text("second")
        (self.root / "a").write_text("first")
        a = hashlib.sha256(b"first").hexdigest()
        b = hashlib.sha256(b"second").hexdigest()
        expected = hashlib.sha256(f"a\0{a}\nb\0{b}\n".encode()).hexdigest()
        self.assertEqual(contract_digest(self.root, ["b", "a"]), expected)

    def test_valid_package_passes(self):
        self.fixture()
        self.assertEqual(validate_package(self.root), [])

    def test_cli_validate_command(self):
        result = subprocess.run([sys.executable, 'tools/contract.py', '--validate', '.'], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), 'PASS')


if __name__ == "__main__":
    unittest.main()
