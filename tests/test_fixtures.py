import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.fixtures import validate_fixture


ROOT = Path(__file__).resolve().parents[1]
IDS = {"identity", "actions", "state", "surfaces", "fields", "adaptive"}


class FixtureTests(unittest.TestCase):
    def load(self, name):
        return json.loads((ROOT / "references" / f"{name}.json").read_text())

    def test_six_scenes_are_inspectable(self):
        self.assertEqual({p.stem for p in (ROOT / "references").glob("*.json")}, IDS)
        for name in IDS:
            with self.subTest(name=name):
                fixture = self.load(name)
                self.assertEqual(validate_fixture(ROOT, fixture), [])
                self.assertTrue(fixture["accessible_text"].strip())

    def test_pending_is_not_confirmed(self):
        fixture = self.load("state")
        fixture["states"]["pending"]["observed"] = "success"
        self.assertTrue(any("false success" in e for e in validate_fixture(ROOT, fixture)))

    def test_missing_accessibility_or_rule_fails(self):
        fixture = copy.deepcopy(self.load("actions"))
        fixture["accessible_text"] = ""
        fixture["rules"] = ["FAKE-999"]
        errors = validate_fixture(ROOT, fixture)
        self.assertTrue(any("accessible text" in e for e in errors))
        self.assertTrue(any("unknown rule" in e for e in errors))

    def test_missing_visual_source_fails(self):
        fixture = copy.deepcopy(self.load("surfaces"))
        fixture["source_hashes"]["references/visual-evidence/material-families.png"] = "0" * 64
        self.assertTrue(any("source hash" in e for e in validate_fixture(ROOT, fixture)))

    def test_reference_versions_are_current(self):
        rules_version = json.loads((ROOT / "core/rules.json").read_text())["version"]
        for name in IDS:
            with self.subTest(name=name):
                self.assertEqual(self.load(name)["version"], rules_version)
                svg = (ROOT / "references" / f"{name}.svg").read_text()
                self.assertIn(f"gnosix_DS 0{rules_version}", svg)

    @unittest.skipUnless(shutil.which("inkscape"), "Inkscape renderer unavailable")
    def test_surface_materials_render_as_visible_color(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "surfaces.png"
            result = subprocess.run(["inkscape", str(ROOT / "references/surfaces.svg"),
                                     "--export-type=png", f"--export-filename={output}",
                                     "--export-width=1200"], check=True, capture_output=True)
            self.assertNotIn(b"unknown type", result.stderr)
            image = Image.open(output).convert("RGB")
            self.assertNotEqual(image.getpixel((150, 350)), (255, 255, 255))
            self.assertNotEqual(image.getpixel((350, 350)), (255, 255, 255))


if __name__ == "__main__":
    unittest.main()
