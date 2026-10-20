import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.project_tokens import check_projection, render_css, render_kotlin


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
        self.assertEqual(kotlin.count(" = Color("), sum(len(ramp) for ramp in tokens["color"].values()))

    def test_changed_web_projection_is_rejected(self):
        tokens = json.loads((ROOT / "core/TOKENS.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "core").mkdir()
            (root / "profiles/web").mkdir(parents=True)
            native = root / "profiles/android/sample/app/src/main/java/labs/gnuin/gnosixds"
            native.mkdir(parents=True)
            (root / "core/TOKENS.json").write_text(json.dumps(tokens))
            (root / "profiles/web/tokens.css").write_text(render_css(tokens).replace("#4169E1", "#4169E2"))
            (native / "GnosixColors.kt").write_text(render_kotlin(tokens))
            self.assertTrue(any("tokens.css differs" in e for e in check_projection(root)))


if __name__ == "__main__":
    unittest.main()
