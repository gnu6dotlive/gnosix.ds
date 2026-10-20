# Changelog

All notable changes to gnosix_DS are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [semantic versioning](https://semver.org/spec/v2.0.0.html).

The canonical version lives in [`VERSION`](VERSION). Every other place the
package states a version is a slot that `tools/version.py` keeps in step, and
`python -m tools.version --check` fails the build if any of them drifts.

## [3.5.0] — 2026-10-20

The contract gains a **surface layer**, and COL-001 becomes executable.

**The package was breaking its own rule.** COL-001 says to read exact
approved colours from core/TOKENS.json. The package's own public reference
broke it in ninety-four places, with fifty-nine colours the contract never
stated: a cool neutral ramp, from the dark substrate's elevation to the
lightest hairline, with a couple of deliberate tints beside it. The web
profile's demo had a second palette of its own. Nothing noticed, because
nothing looked.

`core/SURFACES.json` now states that layer: sixty-six steps and three
accents, each with its lightness, its chroma and its role. The hue comes from
the family's base token, so a step cannot drift out of the palette's family
without the check noticing. The site's colours, the demo's colours and the
reference scenes' colours are all now the system's own, and
`tools/contract_colors.py` refuses any colour that is not a token, a step or
a declared accent.

The result is the same page, rendered from the system's own colours: the
public reference and the version before it differ by **zero pixels** over
twelve million, measured in a browser rather than argued.

**The neutral ramp was already there.** The greys the site used are all at
the hue of anthracite, with a chroma that rises as they get lighter — a
perceptual ramp, arrived at by hand and never written down. The layer writes
it down, and derives the values from what it states.

**A step is named by its lightness, not by its position.** That is a
correction of a mistake made in this release: the first version numbered the
steps, and adding one renumbered the rest, and every file that referred to
the old names quietly lost its colour — a custom property that resolves to
nothing falls back to whatever the cascade gives it, so the page drained its
own colour without a word. The names are now stable under insertion, and
`tools/apply_surfaces.py --check` refuses a surface that refers to a
property nothing defines.

Also: the web projection and the FigCraft projection now carry the surface
layer whole, and `figcraft/check_tokens.py` checks the two against each
other on values with the names normalised, because they name the same token
differently and a diff of the text would fail on two systems that agree.

## [Unreleased]

Nothing yet. The next release is cut with
`python -m tools.release bump --patch|minor|major`, which moves `VERSION`,
syncs every slot and rebuilds the manifest in one step.

## [3.4.2] — 2026-10-20

Ratifies the icon pack and carries the V3.4.1 asset repairs. The ratified
opaque masters are unchanged — byte-identical to V3.3.1 — and nothing in this
release redraws artwork. What changed is the containers the artwork travels
in, the icon set the interface draws from, and the validation that should
have caught all of it.

**The icon pack is ratified.** The interface icons are Tabler Icons 3.49.0
and the flags are Tabler Flags 0.1.1, both MIT licensed. A curated subset —
41 icons and 8 flags — is vendored at a pinned upstream tag rather than
referenced from a CDN, each recorded in `assets/icons/icon-manifest.json` with
its upstream URL, its role and its SHA-256. The subset is deliberately
smaller than the upstream catalogue, which is documented in the manifest.

**`ICON-001` governs the use of glyphs.** Interface icons come from the
ratified subset, and a text character may not stand in for one. The V3.4.1
site broke that rule in three places — an arrow-down-right, an arrow-up-right
and a multiplication sign used as a close control — because a character that
renders as an icon is still an icon, with none of the guarantees: it inherits
the font's metrics, it cannot be recoloured independently, and it is a
different shape on every platform. Those are now ratified glyphs, and the
reference scenes' character-drawn state pip is a vector mark.

**The alpha masters are no longer premultiplied in place.** Their edge pixels
stored a blend of the subject with the removed dark field instead of the
subject at partial coverage, and the coverage ramp was quantised to two
values. The result was invisible in review — compositing the field colour
back over the asset reproduces the master perfectly — and wrong everywhere
the asset is meant to be used: a dark grey fringe traced the silhouette of
every cube on any neutral substrate. `tools/rekey_alpha.py` re-derives a
straight alpha channel for the edge band only, and the asset suite now
asserts the property directly: no edge pixel may get darker when the
substrate is changed from the field to white.

**The validation now covers what it missed.** V3.4.0's alpha gate looped over
every pixel and skipped every pixel where `alpha != 255`, which is exactly
the population the defect lived in. The mascots were veiled across their
whole body rather than antialiased at the edge. All eight SVG wrappers
embedded their payload twice, in `href` and the deprecated `xlink:href`, for a
2× size cost on multi-megabyte files. `gnosix-ds-mark.svg` declared no
intrinsic size. The favicon was a 128px fully opaque dark square.
`__pycache__` and `.pytest_cache` shipped inside the tarball.

Full detail, including two test bugs found while writing the new gates, is
in [`qa/QA.md`](qa/QA.md).

## [3.4.1] — 2026-10

Repaired the asset containers and the validation that missed them. The
ratified opaque masters are unchanged. The alpha masters, the mascots, the
SVG wrappers, the mark's intrinsic size, the favicon and the packaging
artefacts are all as described under 3.4.2 above, which carried these repairs
forward. The motion contract and the alpha compositing variants were
introduced in 3.4.0 and are unchanged by both.

## [3.4.0] — 2026-10

Introduced the motion contract and the alpha compositing variants. The motion
profile supplies the motion *meaning* — six laws, four prohibitions, seven
motion roles each with a declared reduced-motion projection, and seven seams
— and deliberately does not ratify a global duration ladder
(`MOT-BAN-TOKEN-LADDER` prohibits promoting target-local frame counts into
`TOKENS.json`). One alpha compositing variant per identity shipped as
`*-cube-alpha.png` plus an exact-fidelity SVG wrapper.

## Older releases

Releases before 3.4.0 were distributed as tarballs and are not reconstructed
here. The packaged history begins at 3.4.0.
