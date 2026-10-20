import json
import re
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

from tools.project_tokens import check_projection


ROOT = Path(__file__).resolve().parents[1]
IDS = {"identity", "actions", "state", "surfaces", "fields", "adaptive"}


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.images = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.tags.append((tag, attrs))
        if tag == "img":
            self.images.append(attrs)


class WebTests(unittest.TestCase):
    def test_color_projections_are_current(self):
        self.assertEqual(check_projection(ROOT), [])

    def test_component_styles_reference_defined_tokens(self):
        """Every custom property a component uses is one the profile defines.

        The profile has two tiers now: the tokens, which carry the palette
        and the surfaces, and the roles, which bind a role to a token on
        each substrate. A component names a role, so both tiers have to be
        read for this to mean anything.
        """
        defined = set(re.findall(r"(--gnosix-[a-z0-9-]+):", (ROOT / "profiles/web/tokens.css").read_text()))
        defined |= set(re.findall(r"(--gnosix-[a-z0-9-]+):", (ROOT / "profiles/web/roles.css").read_text()))
        used = set(re.findall(r"var\((--gnosix-[A-Za-z0-9-]+)\)", (ROOT / "profiles/web/components.css").read_text()))
        self.assertEqual(used - defined, set())

    def test_the_role_layer_is_bound_to_the_contract(self):
        """Every role binds to a token the contract has, on both substrates.

        A role that binds to a token the contract does not have would
        project a custom property that resolves to nothing, and the
        surface would fall back to whatever the cascade gives it.
        """
        roles = json.loads((ROOT / "core/ROLES.json").read_text())
        tokens = json.loads((ROOT / "core/TOKENS.json").read_text())
        surfaces = json.loads((ROOT / "core/SURFACES.json").read_text())

        known = set()
        for family, ramp in tokens["color"].items():
            known |= {f"{family}/{shade}" for shade in ramp}
        for spec in surfaces["families"].values():
            known |= {step["id"] for step in spec["steps"]}
        known |= {accent["id"] for accent in surfaces["accents"]}

        for name, spec in roles["roles"].items():
            for substrate in ("light", "dark"):
                self.assertIn(spec[substrate], known, f"{name}.{substrate}")

    def test_static_site_exposes_six_accessible_visual_fixtures(self):
        html = (ROOT / "site/index.html").read_text()
        page = Elements()
        page.feed(html)
        for fixture in IDS:
            self.assertTrue(any(img.get("src") == f"../references/{fixture}.svg" and img.get("alt")
                                for img in page.images), fixture)
        self.assertTrue(all((ROOT / "site" / img["src"]).resolve().is_file() for img in page.images if img.get("src")))
        self.assertTrue(any(tag == "button" for tag, _ in page.tags))
        self.assertTrue(any(tag == "label" for tag, _ in page.tags))
        self.assertTrue(any(attrs.get("aria-live") == "polite" for _, attrs in page.tags))
        self.assertIn('id="components"', html)
        self.assertIn('href="#components"', html)
        self.assertIn('role="img"', html)
        self.assertIn("prefers-reduced-motion", (ROOT / "site/style.css").read_text())
        self.assertNotIn('class="chip', html)

    def test_space_grotesk_is_the_only_visual_family(self):
        site = (ROOT / "site/style.css").read_text()
        components = (ROOT / "profiles/web/components.css").read_text()
        tokens = (ROOT / "profiles/web/tokens.css").read_text()
        self.assertIn('font-family: "Space Grotesk"', site)
        self.assertIn('--gnosix-font-primary: "Space Grotesk"', tokens)
        self.assertNotIn('ui-monospace', site)
        self.assertNotIn('IBM Plex Mono', site + components)

    def test_ratified_identity_assets_are_used_by_site(self):
        html = (ROOT / "site/index.html").read_text()
        self.assertIn('../assets/identity/gnosix-ds-mark.svg', html)
        self.assertIn('../assets/identity/gnosix-cube.png', html)
        self.assertIn('../assets/identity/gnu6-live-cube.png', html)
        self.assertIn('../assets/identity/gnuinlabs-cube.png', html)

    def test_native_profile_and_projection_matrix_are_linked(self):
        html = (ROOT / "site/index.html").read_text()
        self.assertTrue((ROOT / "profiles/native/README.md").is_file())
        self.assertTrue((ROOT / "profiles/projection-map.json").is_file())
        self.assertIn('../profiles/native/README.md', html)
        self.assertIn('../profiles/projection-map.json', html)

    def test_request_does_not_announce_success(self):
        code = "const {projectState}=require('./profiles/web/state.js');console.log(JSON.stringify([projectState('on','off'),projectState('on','on')]))"
        result = subprocess.run(["node", "-e", code], cwd=ROOT, capture_output=True, text=True, check=True)
        pending, observed = json.loads(result.stdout)
        self.assertEqual(pending, {"text": "Request pending", "status": "pending"})
        self.assertEqual(observed, {"text": "Observed: on", "status": "observed"})


    def test_web_demo_lays_out_components_and_identity_assets(self):
        html = (ROOT / "profiles/web/demo.html").read_text()
        self.assertIn('../../assets/identity/gnosix-ds-mark.svg', html)
        self.assertIn('../../assets/identity/gnosix-cube.png', html)
        self.assertIn('../../assets/identity/gnu6-live-cube.png', html)
        self.assertIn('../../assets/identity/gnuinlabs-cube.png', html)
        self.assertIn('component layout', html.lower())

    def test_canonical_public_nomenclature(self):
        authored = "\n".join([
            (ROOT / "site/index.html").read_text(),
            (ROOT / "profiles/native/README.md").read_text(),
            (ROOT / "profiles/native/status.json").read_text(),
            (ROOT / "profiles/android/sample/app/src/main/java/labs/gnuin/gnosixds/ReferenceScreen.kt").read_text(),
            (ROOT / "core/IDENTITY.md").read_text(),
        ])
        self.assertNotIn("GNOS.UX", authored)
        self.assertIn("gnos.ux", authored)
        self.assertIn("gnosix", authored)


if __name__ == "__main__":
    unittest.main()
