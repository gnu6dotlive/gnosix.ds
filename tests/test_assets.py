import hashlib
import json
import re
import unittest
from pathlib import Path
from PIL import Image
from tools.check_fonts import font_has_glyphs

ROOT = Path(__file__).resolve().parents[1]

RATIFIED = {
    "gnosix-cube.png": "c5b5d61ac2bb71211bd1caf18fb5b0a1dca2e18c5e96cf4ea74d27561ed42958",
    "gnu6-live-cube.png": "20f6a4970d4375851738b9a0ef6ec0ddce36803f0fb001657bd0337b3d87b858",
    "gnuinlabs-cube.png": "45e6c00f4a845c2291fd95c8b1e75ebb0d24dfee2b7a44294cd14e96301e8896",
    "gnosix-ds-mark.png": "72d6c8264deff81f3b7f535d063086204cc03921eee3fee804c5f3f7e1b4aaa9",
}

# V3.4.1 compositing variants. Ratified in their own right: packaged and hashed, so ID-003's
# "packaged masters or exact-fidelity containers" clause is satisfied rather than weakened.
ALPHA = {
    "gnosix-cube-alpha.png": "af177020fb05dd726638de592c1241105ea7e4c3a0eb3532f4c646bda4b0cff4",
    "gnu6-live-cube-alpha.png": "ff1e1467ba5e1d5a3891c90bc210272de55b60e5109ec474c764a692c2f2f910",
    "gnuinlabs-cube-alpha.png": "097438a515864050e095ff57b6fbc85a938f3dd0c5aa482940e810e64b6018ed",
}

MASCOTS = {
    "syster-color.png": "a11aac810afced96c250cc153fa3ab9e7ecf101ab8ab82cc69b2a9cc3859da7e",
    "syster-mono.png": "4858290930162a4e8a7e7a451538a9c5ac8a9312faa3f552f7c27eca8f29214e",
    "syster-outline.png": "60b61bbf3b37aad86aa53b54339bbfcbe22620ff0ae1941d4221e2d5502bf84b",
}

ALPHA_PAIRS = {
    "gnosix-cube-alpha.png": "gnosix-cube.png",
    "gnu6-live-cube-alpha.png": "gnu6-live-cube.png",
    "gnuinlabs-cube-alpha.png": "gnuinlabs-cube.png",
}

IDENTITY_SVGS = (
    "gnosix-cube", "gnu6-live-cube", "gnuinlabs-cube", "gnosix-ds-mark-master",
    "gnosix-ds-mark", "gnosix-cube-alpha", "gnu6-live-cube-alpha", "gnuinlabs-cube-alpha",
)


def _load_rgba(path: Path):
    with Image.open(path) as handle:
        return handle.convert("RGBA")


def _load_rgb(path: Path):
    with Image.open(path) as handle:
        return handle.convert("RGB")


def _composite_over(rgba, background):
    """Composite an RGBA image over a flat background, as a renderer would."""
    canvas = Image.new("RGBA", rgba.size, tuple(background) + (255,))
    canvas.alpha_composite(rgba)
    return canvas.convert("RGB")


class AssetTests(unittest.TestCase):
    def test_ratified_identity_masters_are_byte_exact(self):
        for name, expected in RATIFIED.items():
            with self.subTest(name=name):
                path = ROOT / "assets/identity" / name
                self.assertTrue(path.is_file())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)
                with Image.open(path) as im:
                    self.assertGreaterEqual(im.width, 1024)
                    self.assertEqual(im.width, im.height)

    def test_exact_svg_containers_embed_ratified_png(self):
        for stem in IDENTITY_SVGS:
            content = (ROOT / "assets/identity" / f"{stem}.svg").read_text()
            self.assertIn("data:image/png;base64,", content)
            self.assertNotIn("<text", content)

    def test_svg_containers_embed_their_payload_exactly_once(self):
        """V3.4.0 wrote every payload twice, in href and the deprecated xlink:href.

        That is a straight 2x on a multi-megabyte file and modern renderers ignore the
        second copy entirely, so it bought nothing. Asserting a single payload also
        catches the more general mistake: a wrapper that embeds a stale or wrong raster
        while still passing the substring check above.
        """
        import base64
        import re

        expected_png = {
            "gnosix-cube": "gnosix-cube.png",
            "gnu6-live-cube": "gnu6-live-cube.png",
            "gnuinlabs-cube": "gnuinlabs-cube.png",
            "gnosix-ds-mark-master": "gnosix-ds-mark.png",
            "gnosix-ds-mark": "gnosix-ds-mark.png",
            "gnosix-cube-alpha": "gnosix-cube-alpha.png",
            "gnu6-live-cube-alpha": "gnu6-live-cube-alpha.png",
            "gnuinlabs-cube-alpha": "gnuinlabs-cube-alpha.png",
        }
        pattern = re.compile(r"data:image/png;base64,([A-Za-z0-9+/=]+)")
        for stem, png_name in expected_png.items():
            with self.subTest(stem=stem):
                content = (ROOT / "assets/identity" / f"{stem}.svg").read_text()
                payloads = pattern.findall(content)
                self.assertEqual(
                    len(payloads), 1,
                    f"{stem}.svg embeds {len(payloads)} payloads; expected exactly 1",
                )
                self.assertNotIn("xlink:href", content, f"{stem}.svg keeps a duplicate href")
                self.assertEqual(
                    base64.b64decode(payloads[0]),
                    (ROOT / "assets/identity" / png_name).read_bytes(),
                    f"{stem}.svg does not embed the current {png_name}",
                )

    def test_svg_containers_declare_an_intrinsic_size(self):
        """An SVG with a viewBox and no width/height has no intrinsic size, and
        renderers disagree about the fallback. gnosix-ds-mark.svg was the one wrapper
        missing them."""
        import re

        for stem in IDENTITY_SVGS:
            with self.subTest(stem=stem):
                head = (ROOT / "assets/identity" / f"{stem}.svg").read_text()[:400]
                width = re.search(r'\bwidth="(\d+)"', head)
                height = re.search(r'\bheight="(\d+)"', head)
                self.assertIsNotNone(width, f"{stem}.svg declares no width")
                self.assertIsNotNone(height, f"{stem}.svg declares no height")
                self.assertGreater(int(width.group(1)), 0)
                self.assertGreater(int(height.group(1)), 0)
                self.assertIn("viewBox=", head)

    def test_alpha_masters_are_byte_exact(self):
        for name, expected in ALPHA.items():
            with self.subTest(name=name):
                path = ROOT / "assets/identity" / name
                self.assertTrue(path.is_file())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)
                with Image.open(path) as im:
                    self.assertEqual(im.width, im.height)
                    self.assertIn(im.mode, ("RGBA", "LA"), "alpha master must carry an alpha channel")

    def test_alpha_master_is_the_same_artwork_not_a_new_one(self):
        """The alpha variant must be the ratified master with the authored field keyed out.

        This is the property that makes promoting these assets safe rather than a new design
        decision. If a future edit repainted, eroded or re-graded the subject, the fully
        opaque pixels would stop matching and this fails.
        """
        for alpha_name, opaque_name in ALPHA_PAIRS.items():
            with self.subTest(pair=(alpha_name, opaque_name)):
                with Image.open(ROOT / "assets/identity" / alpha_name) as alpha_im:
                    with Image.open(ROOT / "assets/identity" / opaque_name) as opaque_im:
                        self.assertEqual(alpha_im.size, opaque_im.size)
                        alpha_px = alpha_im.convert("RGBA").load()
                        opaque_px = opaque_im.convert("RGB").load()
                        width, height = alpha_im.size
                        total = width * height
                        compared = 0
                        for y in range(height):
                            for x in range(width):
                                r, g, b, a = alpha_px[x, y]
                                if a != 255:
                                    continue
                                compared += 1
                                self.assertEqual(
                                    (r, g, b), opaque_px[x, y],
                                    f"{alpha_name} alters the artwork at ({x},{y})",
                                )
                        # Bound the opaque fraction from both sides. Below the floor the subject
                        # was eroded; at or above the ceiling nothing was keyed out and this is
                        # just the opaque master under a new name.
                        self.assertGreater(compared, total * 0.25,
                                           f"{alpha_name} has implausibly little opaque artwork")
                        self.assertLess(compared, total * 0.60,
                                        f"{alpha_name} carries no removed field; it is not a "
                                        f"compositing variant of the opaque master")

    def test_alpha_masters_are_unmatted_so_no_dark_fringe_on_light_substrates(self):
        """The edge pixels must store the artwork colour, not a field-contaminated blend.

        V3.4.0 shipped these variants premultiplied in place. Compositing the field colour
        back over them reproduced the master, so nothing looked wrong in isolation, but on
        a neutral substrate the edge showed a dark grey fringe around every cube. The
        signature of that bug is precise: moving the substrate from the dark field to a
        light one makes the edge *darker* rather than lighter, because the stored colour is
        the field itself. Under correct un-matting the edge is the subject at partial
        coverage, so a lighter substrate can only lighten it.

        This is the assertion the V3.4.0 suite was missing. Its only alpha test skipped
        every pixel where alpha != 255, which is exactly the population this defect lives
        in.
        """
        field = None
        for alpha_name, opaque_name in ALPHA_PAIRS.items():
            with self.subTest(pair=(alpha_name, opaque_name)):
                rgba = _load_rgba(ROOT / "assets/identity" / alpha_name)
                opaque = _load_rgb(ROOT / "assets/identity" / opaque_name)
                alpha = rgba.getchannel("A")
                band_mask = alpha.point(lambda value: 255 if 0 < value < 255 else 0)
                band_coords = [
                    (x, y)
                    for y in range(rgba.height)
                    for x in range(rgba.width)
                    if band_mask.getpixel((x, y)) == 255
                ]
                self.assertGreater(
                    len(band_coords), 500, f"{alpha_name} has no meaningful edge band"
                )

                field = opaque.getpixel((2, 2))
                on_field = _composite_over(rgba, field).load()
                on_white = _composite_over(rgba, (255, 255, 255)).load()

                darkened = 0
                worst = 0
                for x, y in band_coords:
                    delta = max(on_field[x, y]) - max(on_white[x, y])
                    if delta > 1:
                        darkened += 1
                        worst = max(worst, delta)
                self.assertEqual(
                    darkened, 0,
                    f"{alpha_name} shows a dark fringe on a light substrate: {darkened} band "
                    f"pixels get darker when the substrate lightens (worst {worst} levels). "
                    f"The edge is premultiplied with the removed field.",
                )

    def test_alpha_masters_have_a_continuous_coverage_ramp(self):
        """V3.4.0 quantised the edge to alpha 170 and 240, a two-step stair.

        A real antialiased silhouette has a continuous ramp. Two levels is not a soft
        edge, it is a jagged one, and it is visible as a stair-stepped outline at any size
        where the cube is more than a few dozen pixels across.
        """
        for alpha_name in ALPHA:
            with self.subTest(asset=alpha_name):
                alpha = _load_rgba(ROOT / "assets/identity" / alpha_name).getchannel("A")
                levels = {value for value in alpha.getdata() if 0 < value < 255}
                self.assertGreater(
                    len(levels), 32,
                    f"{alpha_name} quantises its edge to {len(levels)} levels; a real "
                    f"antialiased silhouette needs a continuous ramp",
                )


    def test_alpha_masters_are_not_sanctioned_on_chromatic_substrates(self):
        """ID-004: neutral substrates only. Assert the declared sets exactly partition the
        token families, so a future token addition cannot quietly widen the sanction."""
        tokens = json.loads((ROOT / "core/TOKENS.json").read_text())
        chromatic = {
            f"color.{family}.{step}"
            for family in ("signalOrange", "royalBlue", "beretGreen")
            for step in tokens["color"][family]
        }
        neutral = {f"color.neutral.{step}" for step in tokens["color"]["neutral"]}
        declared = json.loads((ROOT / "references/identity.json").read_text())["alpha_masters"]
        self.assertEqual(set(declared["refused_substrates"]), chromatic)
        self.assertEqual(set(declared["sanctioned_substrates"]), neutral)
        self.assertFalse(chromatic & neutral)
        self.assertIn("ID-004", json.loads((ROOT / "references/identity.json").read_text())["rules"])

    def test_mascots_are_byte_exact(self):
        for name, expected in MASCOTS.items():
            with self.subTest(name=name):
                path = ROOT / "assets/mascot" / name
                self.assertTrue(path.is_file())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)
                with Image.open(path) as im:
                    self.assertIn(im.mode, ("RGBA", "LA"))

    def test_mascot_bodies_are_fully_opaque(self):
        """The V3.4.0 mascots were veiled across their whole body, not just at the edge.

        Their alpha channel was bimodal: a real antialiased ramp of a few thousand pixels,
        and then a plateau at 252-254 covering everything else. `syster-color` was only
        0.1% fully opaque, so compositing it laid a uniform film of the substrate over the
        entire character. A mascot that never fully arrives is not a subtle defect; it is
        the asset failing to render.

        The threshold is scoped to the two filled mascots. `syster-outline` is line art of
        varying weight, so a large share of its pixels are legitimately part of an edge and
        a coverage ratio says nothing useful about it; it is judged by the substrate test
        below instead, which is a direct statement of the property that was broken.
        """
        for name in ("syster-color.png", "syster-mono.png"):
            with self.subTest(name=name):
                rgba = _load_rgba(ROOT / "assets/mascot" / name)
                alpha = rgba.getchannel("A")
                histogram = alpha.histogram()
                visible = sum(histogram[1:])
                self.assertGreater(visible, 1000, f"{name} has no visible artwork")
                veiled = sum(histogram[248:255])
                self.assertLess(
                    veiled / visible, 0.05,
                    f"{name} has {veiled / visible * 100:.1f}% of its artwork sitting just "
                    f"below full opacity; the body is veiled rather than the edge being soft",
                )
                self.assertGreater(
                    histogram[255] / visible, 0.75,
                    f"{name} is only {histogram[255] / visible * 100:.1f}% fully opaque",
                )

    def test_mascot_bodies_do_not_shift_with_the_substrate(self):
        """A fully opaque body composites identically on any substrate.

        This is the property the veil broke, stated so that it fails loudly if a future
        export reintroduces it: sample the body interior, composite on black and on white,
        and require the two to agree.
        """
        for name in MASCOTS:
            with self.subTest(name=name):
                rgba = _load_rgba(ROOT / "assets/mascot" / name)
                alpha = rgba.getchannel("A")
                body = alpha.point(lambda value: 255 if value == 255 else 0)
                if body.histogram()[255] < 500:
                    continue
                on_black = _composite_over(rgba, (0, 0, 0))
                on_white = _composite_over(rgba, (255, 255, 255))
                black_px = on_black.load()
                white_px = on_white.load()
                checked = 0
                for y in range(0, rgba.height, 7):
                    for x in range(0, rgba.width, 7):
                        if body.getpixel((x, y)) != 255:
                            continue
                        checked += 1
                        self.assertEqual(
                            black_px[x, y], white_px[x, y],
                            f"{name} body pixel ({x},{y}) shifts with the substrate; the "
                            f"mascot is not fully opaque there",
                        )
                self.assertGreater(checked, 100, f"{name} body sample was too small to judge")

    def test_mascot_edge_band_is_a_thin_antialiased_outline(self):
        """The mascot edge band must be a thin outline, not a body-wide soft mask.

        An earlier draft of this check asserted that partial pixels should not be
        near-black, on the theory that black meant a black key. That was wrong twice
        over: `syster-outline` is line art whose stroke colour genuinely is black, and
        `syster-color` has a black screen face, so near-black partial pixels are the
        artwork rather than a defect. A test built on that belief would have failed
        correct assets.

        The property that actually distinguishes a keyed matte from real antialiasing is
        geometric: a genuine edge is a thin band hugging the silhouette, while a matte
        error spreads partial coverage across the interior. So assert the band is thin
        relative to the artwork. This is scoped to the filled mascots, since
        `syster-outline` is line art and is mostly edge by design.
        """
        for name in ("syster-color.png", "syster-mono.png"):
            with self.subTest(name=name):
                rgba = _load_rgba(ROOT / "assets/mascot" / name)
                alpha = rgba.getchannel("A")
                histogram = alpha.histogram()
                visible = sum(histogram[1:])
                band = sum(histogram[1:255])
                self.assertGreater(band, 0, f"{name} has no antialiased edge at all")
                self.assertLess(
                    band / visible, 0.20,
                    f"{name} spreads partial coverage across {band / visible * 100:.0f}% of "
                    f"its artwork; that is a soft mask, not an antialiased outline",
                )

    def test_favicons_are_transparent_and_correctly_sized(self):
        """The V3.4.0 favicon was fully opaque with the mark's dark field baked in.

        On a light tab or title bar it rendered as a dark square, and 128px is not a size
        any browser requests. Require real alpha at every shipped size, and require the
        sizes a browser actually asks for.
        """
        site = ROOT / "site"
        for size in (16, 32, 48, 180, 192, 512):
            with self.subTest(size=size):
                path = site / f"favicon-{size}.png"
                self.assertTrue(path.is_file(), f"missing {path.name}")
                with Image.open(path) as im:
                    self.assertEqual(im.size, (size, size))
                    self.assertIn(im.mode, ("RGBA", "LA"))
                    alpha = im.convert("RGBA").getchannel("A")
                    histogram = alpha.histogram()
                    self.assertGreater(
                        histogram[0], 0,
                        f"{path.name} is fully opaque; the mark's field must be alpha",
                    )
                    self.assertGreater(
                        histogram[255], 0, f"{path.name} has no opaque artwork"
                    )

    def test_favicon_artwork_is_the_ratified_mark(self):
        """The icons must be derived from the ratified mark, not redrawn.

        The V3.4.0 favicon was exactly a LANCZOS downscale of the crop declared in
        gnosix-ds-mark.svg. Re-deriving from that same crop is what makes regenerating the
        icon a container repair under ID-003 rather than a new drawing.

        The comparison is made on fully opaque pixels and allows a small tolerance.
        Resizing an RGBA and an RGB image are not bit-identical under LANCZOS, because
        the filter sees a different number of channels and the transparent surround
        contributes no premultiplied colour; demanding exact equality would be asserting
        a property of the resampler rather than of the asset. What matters is that no
        opaque pixel has been repainted, which a redraw or a regrade would change by far
        more than this.
        """
        with Image.open(ROOT / "assets/identity/gnosix-ds-mark.png") as handle:
            mark = handle.convert("RGB")
        crop = mark.crop((250, 205, 1000, 955))
        with Image.open(ROOT / "site/favicon-32.png") as handle:
            icon = handle.convert("RGBA")
        self.assertEqual(icon.size, (32, 32))
        reference = crop.resize((32, 32), Image.LANCZOS).convert("RGBA")
        icon_px = icon.load()
        reference_px = reference.load()
        checked = 0
        for y in range(32):
            for x in range(32):
                if icon_px[x, y][3] != 255:
                    continue
                checked += 1
                for channel in range(3):
                    self.assertLessEqual(
                        abs(icon_px[x, y][channel] - reference_px[x, y][channel]), 4,
                        f"favicon-32 artwork differs from the ratified mark at ({x},{y})",
                    )
        self.assertGreater(checked, 100, "favicon-32 has too little opaque artwork to verify")

    def test_site_references_the_icon_set(self):
        html = (ROOT / "site/index.html").read_text()
        self.assertIn('rel="apple-touch-icon"', html)
        self.assertIn("site.webmanifest", html)
        for size in (16, 32):
            self.assertIn(f"favicon-{size}.png", html)
        self.assertTrue((ROOT / "site/site.webmanifest").is_file())

    def test_icon_pack_is_vendored_pinned_and_licensed(self):
        """The ratified icon pack must be present, digest-pinned and MIT licensed.

        A design contract that changes appearance when a third party releases is not a
        contract, so the package vendors the pack at a pinned upstream tag rather than
        referencing a CDN. The digests are recorded in the icon manifest, and the MIT
        text ships with the assets as that license requires.
        """
        manifest_path = ROOT / "assets/icons/icon-manifest.json"
        self.assertTrue(manifest_path.is_file(), "assets/icons/icon-manifest.json is missing")
        manifest = json.loads(manifest_path.read_text())

        self.assertEqual(manifest["icon_pack"], "Tabler Icons")
        self.assertEqual(manifest["icon_pack_license"], "MIT")
        self.assertEqual(manifest["flag_pack"], "Tabler Flags")
        self.assertEqual(manifest["flag_pack_license"], "MIT")
        self.assertIn("Pawel Kuna", manifest["attribution"])

        for license_name in ("Tabler-Icons-LICENSE.txt", "Tabler-Flags-LICENSE.txt"):
            path = ROOT / "assets/icons/licenses" / license_name
            with self.subTest(license=license_name):
                self.assertTrue(path.is_file(), f"{license_name} is missing")
                self.assertIn("MIT License", path.read_text())

        for entry in manifest["entries"]:
            with self.subTest(asset=entry["path"]):
                path = ROOT / entry["path"]
                self.assertTrue(path.is_file(), f"{entry['path']} is missing")
                data = path.read_bytes()
                self.assertEqual(
                    hashlib.sha256(data).hexdigest(), entry["sha256"],
                    f"{entry['path']} does not match its pinned digest",
                )
                self.assertIn(b"<svg", data)

        sprite_info = manifest["sprite"]
        sprite_path = ROOT / sprite_info["path"]
        self.assertTrue(sprite_path.is_file())
        self.assertEqual(
            hashlib.sha256(sprite_path.read_bytes()).hexdigest(), sprite_info["sha256"]
        )
        sprite_text = sprite_path.read_text()
        for entry in manifest["entries"]:
            if entry["kind"] == "icon":
                self.assertIn(f'id="{entry["name"]}"', sprite_text)

    def test_sprite_contains_every_ratified_icon(self):
        """The sprite is the shipped form of the set, so it must be complete."""
        manifest = json.loads((ROOT / "assets/icons/icon-manifest.json").read_text())
        sprite_text = (ROOT / "assets/icons/sprite.svg").read_text()
        for entry in manifest["entries"]:
            if entry["kind"] == "icon":
                with self.subTest(icon=entry["name"]):
                    self.assertIn(f'<symbol id="{entry["name"]}"', sprite_text)

    def test_flags_are_vendored_at_their_own_proportions(self):
        """A flag is artwork, not a stroked glyph, so it keeps its own aspect.

        Tabler flags are drawn on a 30x24 canvas. They must not be squeezed into the
        24x24 icon grid, and the flag set must be licensed separately from the icons.
        """
        manifest = json.loads((ROOT / "assets/icons/icon-manifest.json").read_text())
        flags = [e for e in manifest["entries"] if e["kind"] == "flag"]
        self.assertTrue(flags, "the ratified flag set is empty")
        for entry in flags:
            with self.subTest(flag=entry["name"]):
                text = (ROOT / entry["path"]).read_text()
                self.assertIn('viewBox="0 0 30 24"', text)

    def test_no_ad_hoc_glyphs_stand_in_for_icons(self):
        """ICON-001: an interface glyph comes from the ratified set.

        The V3.4.1 site carried three characters standing in for icons: an
        arrow-down-right, an arrow-up-right and a multiplication sign used as a close
        control. A character that renders as an icon is still an icon, with none of the
        guarantees: it inherits the font's metrics, it cannot be recoloured
        independently, and it is a different shape on every platform.

        Only interface glyphs are checked. The reference scenes also contain a bullet
        separating footer metadata, an arrow inside a sentence describing reading
        order, a not-equal sign contrasting two concepts and a minus sign inside a
        number. Those are prose typography, not icons, and ICON-001 does not govern
        them, so the check is limited to the glyphs that were actually standing in.
        """
        html = (ROOT / "site/index.html").read_text()
        for char in ("↘", "↗", "×"):
            with self.subTest(glyph=char):
                self.assertNotIn(
                    char, html,
                    f"{char!r} is standing in for an icon in the site; ICON-001 requires "
                    f"a ratified Tabler glyph",
                )

        actions = (ROOT / "references/actions.svg").read_text()
        self.assertNotIn("●", actions, "the state pip is still a text character")

    def test_site_icons_resolve_within_the_document(self):
        """Every icon the site draws must resolve to a symbol the document defines.

        A cross-file ``<use>`` reference is blocked by the browser when the page is
        opened from disk over ``file://``, and these are static files people open
        directly. The reference scenes already inline their font for the same reason,
        so the icons are inlined too.
        """
        html = (ROOT / "site/index.html").read_text()
        defined = set(re.findall(r'<symbol id="([A-Za-z0-9-]+)"', html))
        used = set(re.findall(r'<use href="#([A-Za-z0-9-]+)"', html))
        self.assertTrue(used, "the site draws no icons at all")
        self.assertEqual(
            used - defined, set(),
            "the site references icons it does not define; an unresolved <use> renders "
            "as nothing",
        )
        self.assertEqual(
            defined - used, set(),
            "the site inlines icons it never draws",
        )
        self.assertNotIn("sprite.svg#", html, "the site uses a cross-file icon reference")

    def test_icon_rule_is_ratified(self):
        """The icon pack decision has to be a rule, not a habit."""
        rules = json.loads((ROOT / "core/rules.json").read_text())["rules"]
        by_id = {rule["id"]: rule for rule in rules}
        self.assertIn("ICON-001", by_id)
        rule = by_id["ICON-001"]
        self.assertEqual(rule["level"], "MUST")
        self.assertEqual(rule["domain"], "icons")
        self.assertIn("Tabler", rule["statement"])

    def test_web_profile_exposes_the_icon_layer(self):
        """A consumer needs the icon layer, not just the icon files."""
        components = (ROOT / "profiles/web/components.css").read_text()
        self.assertIn('url("./icons.css")', components)
        icons_css = (ROOT / "profiles/web/icons.css").read_text()
        self.assertIn(".gnosix-icon", icons_css)
        self.assertIn(".gnosix-flag", icons_css)
        self.assertIn("currentColor", icons_css)
        readme = (ROOT / "profiles/web/README.md").read_text()
        self.assertIn("icons.css", readme)
        self.assertIn("ICON-001", readme)

    def test_site_demonstrates_the_alpha_masters_on_sanctioned_substrates(self):
        """The package ships three alpha masters; the public reference must show them.

        ID-004 restricts alpha masters to the neutral ramp, and that restriction is only
        meaningful if something in the package actually places one. Until this release the
        site showed only the opaque masters, so the substrate rule was documented but never
        demonstrated, and a regression that broke the alpha assets would still have left a
        site that looked fine.

        Each alpha master is placed on a substrate named in the markup, and the allowed set
        is the neutral ramp declared in references/identity.json rather than a list written
        out again here, so a future token addition cannot quietly widen what the site treats
        as sanctioned.
        """
        html = (ROOT / "site/index.html").read_text()
        css = (ROOT / "site/style.css").read_text()
        declared = json.loads((ROOT / "references/identity.json").read_text())["alpha_masters"]
        neutral_steps = set(json.loads((ROOT / "core/TOKENS.json").read_text())["color"]["neutral"])
        sanctioned = {
            entry.rsplit(".", 1)[-1] for entry in declared["sanctioned_substrates"]
        }
        self.assertTrue(sanctioned <= neutral_steps,
                        "declared sanctioned substrates must come from the neutral ramp")

        for name in ALPHA:
            with self.subTest(asset=name):
                self.assertIn(f"assets/identity/{name}", html,
                              f"the site never places {name}")

        self.assertIn('id="compositing"', html)
        self.assertIn("ID-004", html, "the substrate restriction is not stated on the page")

        import re
        substrates = set(re.findall(r'data-substrate="([A-Za-z]+)"', html))
        self.assertTrue(substrates, "alpha substrates are not named in the markup")
        self.assertTrue(
            substrates <= sanctioned,
            f"the site places alpha masters on {substrates - sanctioned}, which ID-004 "
            f"does not sanction",
        )
        for step in substrates:
            self.assertIn(f'data-substrate="{step}"', css,
                          f"substrate {step} is named in markup but has no declared background")

    def test_site_alpha_section_is_separate_from_the_opaque_hero(self):
        """The alpha section must not borrow the dark hero frame the opaque cubes sit in.

        Only the alpha masters are substrate bound, so this stays deliberately narrow. The
        point is structural: the compositing demonstration has to be its own section, so a
        future edit that merges it into the hero cannot quietly put a sanctioned-on-neutral
        asset on a surface nobody has checked.
        """
        html = (ROOT / "site/index.html").read_text()
        start = html.find('id="compositing"')
        self.assertGreater(start, 0, "no compositing section")
        end = html.find("</section>", start)
        section = html[start:end]
        self.assertIn("cube-alpha", section)
        self.assertNotIn("hero-cube", section)

    def test_package_ships_no_build_artifacts(self):
        """V3.4.0 shipped tools/__pycache__/*.cpython-314.pyc and .pytest_cache/.

        A .gitignore existed, so this was a packaging mistake rather than a policy
        decision: the tarball was built from a working tree. Stale bytecode in a
        redistributed contract is both noise and a way to ship code that does not match
        the source next to it.

        Running the suite creates fresh bytecode for the current interpreter, so only
        bytecode from *another* interpreter is treated as an offender. A single
        ``cpython-3XX.pyc`` matching the running version is this run's own artefact and is
        cleaned before packaging by tools/rebuild_manifest.py; anything else was shipped.
        """
        import sys

        # PEP 3147 names a cached module "<module>.cpython-3XX.pyc", so the version tag is
        # a suffix of the filename rather than the whole thing.
        tag = f".cpython-{sys.version_info.major}{sys.version_info.minor}.pyc"
        offenders = [
            str(path.relative_to(ROOT))
            for path in ROOT.rglob("*")
            if path.is_file()
            and (
                (path.suffix == ".pyc" and not path.name.endswith(tag))
                or (".pytest_cache" in path.parts)
            )
        ]
        self.assertEqual(offenders, [], f"build artifacts in package: {offenders}")

    def test_font_file_and_license_present(self):
        font = ROOT / "assets/fonts/SpaceGrotesk-wght.woff2"
        self.assertEqual(font.read_bytes()[:4], b"wOF2")
        self.assertIn("SIL OPEN FONT LICENSE", (ROOT / "assets/LICENSES.md").read_text().upper())

    def test_reference_svgs_embed_space_grotesk(self):
        for path in sorted((ROOT / "references").glob("*.svg")):
            content = path.read_text()
            self.assertIn('font-family:"Space Grotesk"', content, path.name)
            self.assertIn('data:font/woff2;base64,', content, path.name)

    def test_native_font_gate(self):
        native = ROOT / "assets/fonts/SpaceGrotesk-native.ttf"
        status = json.loads((ROOT / "profiles/android/status.json").read_text())
        if native.exists():
            self.assertTrue(font_has_glyphs(native, "éàçîœ>_$#"))
        else:
            self.assertEqual(status["status"], "mapped")
            self.assertIn("native font", " ".join(status["gaps"]).lower())

if __name__ == "__main__":
    unittest.main()
