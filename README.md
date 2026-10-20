# gnosix_DS V3.4.2

Portable interface design: rules, tokens, inspectable reference scenes and
explicit platform mappings that carry gnosix from the browser to Compose to
GPUI without turning any toolkit into the design system.

The ratified identity masters are unchanged — byte-identical to V3.3.1 — and
this release redraws no artwork. What it changes is the containers the
artwork travels in, the icon set the interface draws from, and the validation
that should have caught all of it. The release history is in
[`CHANGELOG.md`](CHANGELOG.md); the version that this checkout states lives in
[`VERSION`](VERSION) and nowhere else.

## Current authority

- `core/TOKENS.json` — portable color and typography tokens.
- `core/rules.json` — stable visual/semantic rule IDs.
- `core/IDENTITY.md` — ratified identity masters and canonical public naming.
- `core/MAPPING.md` — portable role → target projection → evidence boundary.
- `profiles/` — Web, Android/Compose, gnos.ux/GPUI and Motion mappings.
- `references/` — six inspectable annotated scenes; fixture-local dimensions are not global tokens.
- `site/` — public visual reference with dedicated component-layout and alpha-compositing sections.

## Working on this repository

The package is qualified by one command, and it is the same command locally
and in CI:

```sh
python3 -m tools.ci
```

It runs every gate in the list and prints one verdict. The list lives in
`tools/ci.py`, in the repository, so a developer and an agent run exactly the
same thing; `.github/workflows/ci.yml` provisions an environment and then gets
out of the way. A check list reproduced in YAML is a second implementation of
the contract, and the second one is the one nobody runs locally.

The suite needs three packages, declared in `requirements.txt`:

```sh
python3 -m pip install -r requirements.txt
```

The gates under `tools/` need none of them. They are standard-library only,
deliberately: a gate that cannot run without a wheel is a gate that does not
always run.

### The version authority

The package states its version in more than one place, and until this release
each of those places was written by hand. That is how V3.4.2 shipped with a
manifest still announcing V3.4.0 and a web manifest still announcing V3.4.1:
the two files that were supposed to describe the release were themselves
drifting independently of it, and nothing in the gate chain noticed.

There is now one value with one owner:

```sh
python3 -m tools.version --show     # the version and every slot that states it
python3 -m tools.version --check     # the gate: does every slot agree?
python3 -m tools.version --sync      # write VERSION into every slot
python3 -m tools.version --set 3.5.0 # move VERSION and sync it
```

`VERSION` is the source. `core/rules.json` (which the test suite already
treated as authoritative), the motion profile, the six reference scenes and
their six sheets, the site's six display slots, the web manifest and the
package manifest are the slots. `--check` verifies the property rather than a
diff, and reports the slot that disagrees rather than a patch.

Only mechanical slots are rewritten. Prose that names a past release — "V3.4.2
ratifies the icon pack" — is history, not a slot, and a bump leaves it alone:
the patterns are anchored on their surrounding markup, so a bare version
number in a sentence is never a candidate. `tests/test_version.py` asserts
this, and also asserts that the rewrite touches nothing but the version.

### Releasing

```sh
python3 -m tools.release status              # where the repository stands
python3 -m tools.release bump --patch        # move VERSION, sync, rebuild the manifest
git commit -am "release: 3.4.3"
python3 -m tools.release build               # dist/Gnosix-DS-V3.4.3.tar.gz
python3 -m tools.release tag                 # annotated v3.4.3
git push && git push --tags
python3 -m tools.release publish             # GitHub release with the archive
```

The order is enforced, not conventional. `bump` moves the version and
rebuilds the manifest, because the manifest hashes the version file. `tag`
refuses a dirty tree, because a tag names a state and a dirty tree is not
one. `publish` refuses unless the tree is clean, the tag exists, the tag
agrees with the version, and the archive has already been built.

Pushing the tag also triggers `.github/workflows/release.yml`, which
qualifies the tagged commit, builds the archive from it and attaches it to
the release. The archive is byte-reproducible — sorted entries, fixed
timestamps, a gzip header carrying neither a name nor a time — so the
SHA-256 printed in the log is a statement about the source rather than about
the runner that packed it.

## Validation

Run all of the following from the package root before redistribution, or run
`python3 -m tools.ci`, which runs them in this order and reports one verdict:

```sh
python3 tools/project_tokens.py --check
python3 -m tools.version --check
python3 tools/contract.py --validate .
python3 tools/rebuild_manifest.py --check
python3 tools/rekey_alpha.py --check
python3 tools/repair_mascot_alpha.py --check
python3 tools/rebuild_svg_wrappers.py --check
python3 tools/build_favicons.py --check
python3 tools/vendor_icons.py --check
python3 tools/apply_icons.py --check
python3 -m unittest discover -s tests -v
```

The six asset tools are read-only under `--check` and idempotent: each reports
the property it verifies rather than a file diff, so running it twice gives
the same answer as running it once. That is what makes them usable as gates
rather than one-time scripts.

## Icon pack

The ratified icon pack is **[Tabler Icons](https://github.com/tabler/tabler-icons) 3.49.0** and the ratified flag pack is **[Tabler Flags](https://github.com/tabler/tabler-flags) 0.1.1**. Both are MIT licensed, Copyright (c) 2018-2026 Paweł Kuna, and the verbatim license text ships in `assets/icons/licenses/`.

Rule `ICON-001` governs the use of glyphs: interface icons come from the
ratified subset, and a text character may not stand in for one. The site
broke that rule in three places — an arrow-down-right, an arrow-up-right and
a multiplication sign used as a close control — because a character that
renders as an icon is still an icon, with none of the guarantees: it inherits
the font's metrics, it cannot be recoloured independently, and it is a
different shape on every platform. Those are now ratified glyphs, and the
reference scenes' character-drawn state pip is a vector mark.

The package **vendors** a curated subset at a pinned upstream tag rather than
referencing a CDN, exactly as it vendors Space Grotesk. A design contract
whose appearance changes when a third party publishes is not a contract. The
subset is 41 icons and 8 flags, each recorded in
`assets/icons/icon-manifest.json` with its upstream URL, its role and its
SHA-256. `tools/vendor_icons.py --fetch` regenerates it and `--check`
verifies it without touching the network.

Icons are stroked SVG on a 24×24 grid painting in `currentColor`, so a glyph
inherits the colour and size of the text it sits beside. Flags are artwork on
a 30×24 canvas with their own fill, and are not squeezed into the icon grid.
`profiles/web/icons.css` gives consumers `.gnosix-icon` and `.gnosix-flag`.

The upstream set is much larger — 6238 icons and 304 flags. This package
ships only what it references, because a few dozen megabytes of catalogue
would imply an authority over the whole set that no consumer here has asked
for. The upstream set stays documented in the manifest, so a consumer needing
a glyph this package does not vendor can fetch it from the same pinned tag.

## Identity assets

The ratified `gnosix`, `gnu6.live` and `gnu.in.labs` cube images remain the
visual masters, and remain byte-identical to V3.3.1. The ratified overlapping
orange / Royal Blue / green plate mark is unchanged. Exact-fidelity SVG
wrappers are provided for consumers that require SVG; they are not
vector-native reconstructions, and each embeds its payload once rather than
twice.

One **alpha compositing variant** per identity ships as `*-cube-alpha.png`
plus an exact-fidelity SVG wrapper. These are the same artwork with the
authored dark field carried as alpha: the RGB of every fully opaque pixel is
byte-identical to the corresponding opaque master, and the asset suite
verifies that rather than asserting it. The edge pixels are straight alpha —
the subject colour at true coverage, not a premultiplied blend — so the
masters composite cleanly on any neutral substrate. Per `ID-004` they are
sanctioned on neutral substrates only — Anthracite, Shell White and neutral
greys. Over Signal Orange, Royal Blue or Beret Green the opaque master is
used, because a chromatic substrate would collapse the cube's dark faces into
the brand hue.

Interface/reference typography remains Space Grotesk. The terminal symbols
baked into the accepted cube artwork are image content, not live UI
typography.

## Motion contract

`profiles/motion/` supplies the motion **meaning**: six laws (causality,
performance, continuity, interruptibility, reduced-motion equivalence,
stillness-before-climax), four prohibitions, seven motion roles each with a
declared reduced-motion projection, and seven seams. It deliberately does
**not** ratify a global duration ladder. The Remotion block declares frame
counts at 60fps and marks them target-local, and `MOT-BAN-TOKEN-LADDER`
prohibits promoting them into `TOKENS.json`.

Two entries are worth reading before building anything animated:

- `MOT-BAN-IDENTITY-MOTION` forbids applying motion to a ratified master.
  Perspective, re-lighting and geometric normalisation stay prohibited under
  `ID-003`; the profile grants no exception. A mark is a still thing and the
  frame moves around it.
- `targets.remotion.reduced_motion.detection` requires reduced motion to be
  an **explicit input**, because a headless renderer reports the render
  machine's motion preference rather than the viewer's, so a media-query-only
  implementation produces no evidence.

## Evidence and status

Web, Android and gnos.ux/GPUI remain `mapped`. Motion is also `mapped`,
implemented by the Remotion target. None is promoted to `rendered` or
`verified` until target-scoped evidence is recorded in this package: renders
produced by a consumer live in that consumer's repository, and the evidence
ladder is explicit that a capture has to be recorded against the claim it
supports. The package does not promote a profile merely because another
profile renders correctly.

## Licence

MIT — see [`LICENSE`](LICENSE). The redistributed third-party assets and
their licences are listed in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
and per file in [`assets/LICENSES.md`](assets/LICENSES.md).
