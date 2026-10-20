# V03.4.2 quality ledger

## Scope

V3.4.2 ratifies the icon pack and carries the V3.4.1 asset repairs forward. It is a **discipline pass** on the asset layer, not a feature release in the product sense. It exists because V3.4.0 ratified assets that were not fit to ship, and because V3.4.1 fixed those assets without ever ratifying the glyph set the interface drew from. The ratified opaque masters — the three cubes and the `gnosix_DS` mark — are **byte-identical to V3.3.1 and to V3.4.0**; their SHA-256 values are unchanged and still asserted by `tests/test_assets.py`. Nothing in this release redraws artwork.

What changed is the *containers* the artwork travels in: alpha channels, SVG wrappers, the mascot PNGs, the site icon set, and the validation that was supposed to catch all of it.

## The icon pack

The decision is ratified: **Tabler Icons 3.49.0** for interface glyphs and **Tabler Flags 0.1.1** for country and organisation flags. Both MIT, Copyright (c) 2018-2026 Pawel Kuna, verbatim license text in `assets/icons/licenses/`.

Three things had to be true before the decision was actionable, and none of them were true when the pack was chosen.

**The package had no icon system at all.** There was no rule, no asset layer, and no set. The site's interface drew on three characters typed into the markup — an arrow-down-right, an arrow-up-right and a multiplication sign used as a close control — and nothing anywhere said that was wrong. A character that renders as an icon is still an icon, with none of the guarantees: it inherits the font's metrics, it cannot be recoloured independently of the label, and it is a different shape on every platform. `ICON-001` now says glyphs come from the ratified set, and `tools/apply_icons.py` rewrote all thirteen occurrences.

**The pack is vendored, not linked.** The package references no CDN anywhere, and treats Space Grotesk the same way: vendored at a pinned tag, digest-recorded, license shipped. A design contract whose appearance changes when a third party publishes is not a contract. `tools/vendor_icons.py --fetch` regenerates the subset from upstream; `--check` verifies what is vendored without touching the network.

**The subset is small on purpose.** Upstream ships 6238 icons and 304 flags. This package vendors 41 icons and 8 flags, each with a recorded role in `assets/icons/icon-manifest.json`. A few megabytes of unused catalogue would imply an authority over the whole set that no consumer here has asked for. The upstream set stays documented in the manifest, so a consumer needing a glyph this package does not vendor can fetch it from the same pinned tag.

### Two decisions worth recording

**Icons are inlined into the surface, not referenced across files.** A cross-file `<use href="sprite.svg#name">` is blocked by the browser when a page is opened from disk over `file://`, and these are static files people open directly. The reference scenes already inline their font for exactly this reason, so the icons follow the same precedent: the sprite is inlined as a hidden `<svg>` in the document, and each surface carries only the symbols it actually draws. The vendored `assets/icons/sprite.svg` remains the full set for consumers that reference it as a file.

**Flags are not icons.** Tabler flags are artwork on a 30x24 canvas with plain filled paths; Tabler icons are a 24x24 stroked grid painting in `currentColor`. The two are not interchangeable, so the flag subset is kept in its own directory, keeps its own aspect, and gets its own class. The test asserts the 30x24 viewBox rather than trusting the layout to be right.

### What was left alone

The reference scenes also contain a bullet separating footer metadata, an arrow inside a sentence describing reading order, a not-equal sign contrasting two concepts, and a minus sign inside a number. Those are prose typography, not interface glyphs, and `ICON-001` does not govern them. The one character that *was* standing in for a UI marker — the state pip in `actions.svg` — is now a vector disc. The site pips were already CSS shapes rather than characters, so they were left alone.

## The headline defect: false transparency

V3.4.0's alpha masters were premultiplied in place. The edge pixels stored a blend of the subject with the dark field rather than the subject at partial coverage, and the coverage ramp was quantised to exactly two values, 170 and 240.

This is the worst class of asset bug because it is invisible in review. Compositing the field colour back over the asset reproduces the ratified master perfectly, so the asset looks correct in isolation, on the surface it was cut from, in every screenshot taken against that background. It only fails on the substrates the asset exists to serve: a dark grey fringe traced the silhouette of every cube on Shell White, Anthracite or any neutral grey.

| asset | coverage levels before | after | band distance from field before | after |
|---|---|---|---|---|
| `gnosix-cube-alpha.png` | 2 | 235 | 39.3 | 127.4 |
| `gnu6-live-cube-alpha.png` | 2 | 237 | 43.3 | 118.4 |
| `gnuinlabs-cube-alpha.png` | 2 | 237 | 23.1 | 56.4 |

`tools/rekey_alpha.py` re-derives a straight alpha channel for the edge band only. Compositing the result back over the authored field reconstructs the ratified master **exactly** (residual 0.0) wherever the solved subject is representable, which is the algebraic guarantee that the artwork was not altered. A small tail of near-transparent pixels clamps, because there the subject colour is an extrapolation beyond 0-255; those pixels are below coverage 0.1 and are reported by the tool rather than hidden.

### Why the old test suite passed

This is the part worth reading. V3.4.0 shipped a test named `test_alpha_master_is_the_same_artwork_not_a_new_one`, and QA.md described it as turning "a one-time manual inspection into a permanent regression gate."

It could not have caught this. The test looped over every pixel and asserted the RGB matched the opaque master — but only after `if a != 255: continue`. It skipped precisely the population the defect lived in. The interior was gated; the edge, the only part that was wrong, was invisible to it.

The new test states the property instead of the proxy: composite the asset over the field and over white, and require that no edge pixel gets *darker* when the substrate gets lighter. That fails for a premultiplied edge and passes for a straight one, whatever else changes.

## Also closed

- **Mascot alpha.** `syster-color.png` was 0.1% fully opaque: its entire body sat at 252-254, so compositing it laid a uniform film of the substrate over the whole character. `tools/repair_mascot_alpha.py` promotes the plateau to full opacity and leaves the genuine antialiased outline alone. `syster-color` is now 96.7% fully opaque with a 3.3% edge band, and `syster-mono` 91.0%.
- **SVG wrappers.** All eight embedded their payload twice, once in `href` and once in the deprecated `xlink:href`, byte for byte. That is a straight 2x on files of 2.4-3.0 MB for no rendering benefit, since every current renderer reads `href` and ignores the second copy. The wrappers now total 10.3 MB instead of 21.2 MB. The suite asserts one payload, and that it decodes to the current PNG, which also catches a wrapper embedding a stale raster.
- **`gnosix-ds-mark.svg` had no intrinsic size.** It carried a `viewBox` and no `width`/`height`, and renderers disagree about the fallback. All eight wrappers now declare both.
- **The favicon was unusable.** 128x128, fully opaque, with the mark's dark field baked into every corner: a dark square on any light tab bar, at a size no browser requests. `tools/build_favicons.py` regenerates it from the ratified mark crop at 16/32/48/180/192/512, keyed with a border-connected flood fill so the mark's dark plate outlines survive. The site now ships an icon set, an `apple-touch-icon` and a web manifest.
- **Build artifacts shipped in the tarball.** `tools/__pycache__/*.cpython-314.pyc` and `.pytest_cache/` were present despite a `.gitignore` existing, because the archive was built from a working tree. A test now fails the package if they reappear.
- **The alpha masters were never demonstrated.** The package shipped three compositing variants and the public reference showed only the opaque masters, so `ID-004`'s substrate restriction was documented but never exercised anywhere a consumer would look. A regression that broke the alpha assets would still have left a site that looked correct. The site now carries a dedicated alpha-compositing section that places all three masters on named token substrates, and two tests pin it: one asserts every alpha master is placed somewhere on the page, the other asserts every substrate used is drawn from the neutral ramp declared in `references/identity.json` rather than a list restated in the test.
- **The site contract digest was manual.** `site/index.html` hardcodes `gnosix-contract-digest` and nothing validated it against `manifest.json`. This was logged as a residual risk in V3.4.0 and left alone to keep that change reviewable. It is closed here: the digest is regenerated as part of the release, and the value in the page matches `manifest.json`.

## Verification added

1. `test_alpha_masters_are_unmatted_so_no_dark_fringe_on_light_substrates` — the fringe test described above.
2. `test_alpha_masters_have_a_continuous_coverage_ramp` — rejects a quantised edge.
3. `test_svg_containers_embed_their_payload_exactly_once` — payload count and byte-exact decode.
4. `test_svg_containers_declare_an_intrinsic_size` — every wrapper declares width and height.
5. `test_mascots_are_byte_exact`, `test_mascot_bodies_are_fully_opaque`, `test_mascot_bodies_do_not_shift_with_the_substrate` — the mascots are pinned and the veil cannot return. The substrate test is the strongest of the three: it samples the body and requires it to composite identically on black and on white, which is a direct statement of the property the veil broke.
6. `test_mascot_edge_band_is_a_thin_antialiased_outline` — distinguishes an edge from a soft mask.
7. `test_favicons_are_transparent_and_correctly_sized`, `test_favicon_artwork_is_the_ratified_mark`, `test_site_references_the_icon_set` — the icon set is pinned to the ratified mark, so regenerating it stays a container repair.
8. `test_package_ships_no_build_artifacts` — packaging hygiene as a gate.
9. `test_icon_pack_is_vendored_pinned_and_licensed` — the pack is present, digest-pinned and MIT licensed, with the license text shipped as that license requires.
10. `test_sprite_contains_every_ratified_icon` — the shipped sprite is complete.
11. `test_flags_are_vendored_at_their_own_proportions` — flags keep their 30x24 canvas rather than being squeezed into the icon grid.
12. `test_no_ad_hoc_glyphs_stand_in_for_icons` — no character stands in for an icon on the site, and the reference scene's state pip is a vector mark.
13. `test_site_icons_resolve_within_the_document` — every icon the site draws resolves to a symbol the document defines, and no symbol is inlined that the page never draws.
14. `test_icon_rule_is_ratified` — the pack decision is a rule, not a habit.
15. `test_web_profile_exposes_the_icon_layer` — a consumer gets `icons.css`, not just the icon files.

## Two test bugs found while writing these

Recorded because both would have shipped as false confidence.

The first draft of the mascot edge check asserted that partial pixels should not be near-black, reasoning that black meant a black key. That is wrong twice: `syster-outline` is line art whose stroke colour genuinely is black, and `syster-color` has a black screen face. The check would have failed correct assets. The replacement tests geometry instead — a real edge is a thin band, a matte error is body-wide.

The favicon comparison originally demanded exact equality with a LANCZOS downscale. Resizing RGBA and RGB are not bit-identical, because the filter sees a different channel count and the transparent surround contributes no premultiplied colour. The measured difference on fully opaque pixels is at most 2 levels, so the assertion now allows 4. What it is actually guarding is a repaint or a regrade, which would move pixels by far more.

## Evidence status

Web, Android, gnos.ux/GPUI and Motion all remain below `rendered`. No profile was promoted during this release. `profiles/motion/status.json` still declares its four gaps, including that no target has recorded a rendered motion sequence and that interruption mid-flight is unevidenced.

The icon pack is verified as an asset, not as a design decision. The digests prove the files are the upstream files at the pinned tag and that the licenses ship with them. Nothing yet proves the set looks right beside the ratified artwork, because nobody has placed a Tabler stroke next to a cube edge and looked at it.

The alpha masters are now verified by construction rather than by inspection: `tools/rekey_alpha.py` reports the reconstruction residual on every run, and the asset suite asserts the fringe property independently. That is a stronger claim than the V3.4.0 ledger could make, and it is a claim about the assets, not about a render — no consumer has yet placed a master on a sanctioned substrate in a real product and recorded the result.

## Residual risks

- **The icon subset is curated, so it can be incomplete.** A consumer needing a glyph outside the 41 will find it absent and will reach for another pack, which is exactly the drift `ICON-001` exists to prevent. The mitigation is the pinned upstream tag recorded in the manifest: a consumer can fetch the same upstream file the package would have vendored, and the digest scheme is already in place to verify it. The alternative, vendoring all 6238 icons, was rejected on weight and on the authority it would imply.
- **The icon set has not been reviewed against the brand.** Tabler is a coherent, well-made set, but the package has not yet checked how it sits beside the ratified artwork in a real surface. A Tabler stroke weight next to the cube's own edge treatment is a visual decision that nobody has made yet. This is the same gap the alpha masters had before V3.4.1: verified as assets, never placed.
- **Flag coverage is eight countries.** The flag set is present, licensed and correctly proportioned, but the package has no locale layer, so there is no ratified list of which flags a consumer would ever need. Eight is a starting subset, not a decision.
- **Upstream is vendored, so it does not track upstream.** The point of pinning is that the package does not change, but it also means a Tabler security or quality fix does not arrive automatically. Re-vendoring is a deliberate act with a new digest and a version bump.
- **The site digest is regenerated but still not validated at build time.** The value is now correct and the QA ledger records the procedure, but nothing in the test suite fails if a future edit changes the contract without updating the page. Closing that properly means making the site header a generated file; it was left as a documented manual step to keep this release reviewable.
- **Out-of-gamut clamp in the near-transparent tail.** Roughly 0.2-7% of edge pixels per asset have a solved subject outside 0-255 and are clamped, all of them below coverage 0.1. They are individually invisible, and the tool reports the count on every run so a regression in that number is visible.
- **The jump-flood nearest-neighbour solve is O(n) per doubling step over the full raster.** It takes about 30 seconds for all three masters, which is why the tools are not wired into the fast test path. A consumer re-keying their own assets should expect the same cost.
- **`syster-outline` is judged only by the substrate test.** Its coverage ratio is not a useful signal because it is line art. If a future export gives it a genuine soft drop shadow, the substrate test will not notice, because a shadow is legitimately not substrate-invariant.

## Validation gates

The package must pass token projection, contract validation, manifest drift, pytest and unittest. The asset gates additionally require:

```sh
python tools/rekey_alpha.py --check
python tools/repair_mascot_alpha.py --check
python tools/rebuild_svg_wrappers.py --check
python tools/build_favicons.py --check
python tools/vendor_icons.py --check
python tools/apply_icons.py --check
```

Each is read-only under `--check`, each reports the property it verifies rather than a file diff, and each is idempotent — running it twice reports the same result as running it once, which is what makes it safe to use as a gate rather than a one-time script.
