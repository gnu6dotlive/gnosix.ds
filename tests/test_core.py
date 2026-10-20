import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

from tools.project_tokens import (check_projection, layer_names, render_css,
                                  render_kotlin, surface_names)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "0ce3dcfe595d402c94c1323b0ddc46350c6334404aff95c7646ade86c41b1e25"


class CoreTests(unittest.TestCase):
    def test_approved_tokens_are_preserved(self):
        source = ROOT / "core/TOKENS.json"
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), SOURCE_SHA)

    def test_brand_colors_project_to_both_platforms(self):
        tokens = json.loads((ROOT / "core/TOKENS.json").read_text())
        css = render_css(tokens)
        kotlin = render_kotlin(tokens)
        self.assertIn("--gnosix-royal-blue-base: #4169E1;", css)
        self.assertIn("--gnosix-neutral-shell-white: #F7F3ED;", css)
        self.assertIn("--gnosix-neutral-pure-white: #FFFFFF;", css)
        self.assertIn("--gnosix-signal-orange-base: #FF6A00;", css)
        self.assertIn("--gnosix-beret-green-base: #5F7F52;", css)
        self.assertIn('--gnosix-font-primary: "Space Grotesk"', css)
        self.assertIn("RoyalBlueBase = Color(0xFF4169E1)", kotlin)
        self.assertIn("SignalOrangeBase = Color(0xFFFF6A00)", kotlin)
        self.assertIn("BeretGreenBase = Color(0xFF5F7F52)", kotlin)
        # The palette and the surface layer are two blocks, and each carries
        # only its own values: a surface is not a palette colour, and the
        # projection does not blur the two.
        palette = kotlin.split("object GnosixColors {")[1].split("}")[0]
        surfaces = kotlin.split("object GnosixSurfaces {")[1].split("}")[0]
        self.assertEqual(palette.count(" = Color("), sum(len(ramp) for ramp in tokens["color"].values()))
        layer = json.loads((ROOT / "core/SURFACES.json").read_text())
        expected = sum(len(spec["steps"]) for spec in layer["families"].values()) + len(layer["accents"])
        self.assertEqual(surfaces.count(" = Color("), expected)

    def test_published_names_follow_the_naming_rule(self):
        """Every published name is a layer id, kebab-cased, under the prefix.

        The rule is NAM-001 in core/rules.json, and its implementation is
        published_name(). The gate asks the same function the projection
        asks, so it cannot pass by agreeing with a second copy of the
        rule. This is the gate that would have caught the vendored copy
        of the namespace, which drifted in fifteen spellings while every
        projection still agreed with itself.
        """
        tokens = json.loads((ROOT / "core/TOKENS.json").read_text())
        css = (ROOT / "profiles/web/tokens.css").read_text(encoding="utf-8")
        published = set(re.findall(r"(--gnosix-[A-Za-z0-9-]+)\s*:", css))
        roles = {name for name in published
                 if name.startswith(("--gnosix-font-", "--gnosix-weight-"))}
        self.assertEqual(published - roles, layer_names(tokens) | surface_names())

    def test_changed_web_projection_is_rejected(self):
        tokens = json.loads((ROOT / "core/TOKENS.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "core").mkdir()
            (root / "profiles/web").mkdir(parents=True)
            native = root / "profiles/android/sample/app/src/main/java/labs/gnuin/gnosixds"
            native.mkdir(parents=True)
            (root / "core/TOKENS.json").write_text(json.dumps(tokens))
            # The colour is tampered with to prove the projection gate notices. It is
# another approved token rather than an invented one, so the test file
# itself holds no colour the system does not have.
            (root / "profiles/web/tokens.css").write_text(render_css(tokens).replace("#4169E1", "#5F7F52"))
            (native / "GnosixColors.kt").write_text(render_kotlin(tokens))
            self.assertTrue(any("tokens.css differs" in e for e in check_projection(root)))


if __name__ == "__main__":
    unittest.main()
