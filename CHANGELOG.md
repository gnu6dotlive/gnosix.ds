# Changelog

All notable changes to gnosix_DS are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [semantic versioning](https://semver.org/spec/v2.0.0.html).

The canonical version lives in [`VERSION`](VERSION). Every other place the
package states a version is a slot that `tools/version.py` keeps in step, and
`python -m tools.version --check` fails the build if any of them drifts.

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
