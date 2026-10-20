# Changelog

All notable changes to gnosix_DS are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [semantic versioning](https://semver.org/spec/v2.0.0.html).

The canonical version lives in [`VERSION`](VERSION). Every other place the
package states a version is a slot that `tools/version.py` keeps in step, and
`python -m tools.version --check` fails the build if any of them drifts.

## [3.8.0] — 2026-10-20

The system is audited against the ten private frontends that use it, and
one rule that was living in the wrong place comes home.

**The namespace had drifted without anybody being able to check it.** The
rule that a published token name is the layer id, kebab-cased, under the
`--gnosix-` prefix, lived in `tools/project_tokens.py` — inside a
projection, not in the contract. Two repositories ship a vendored copy of
the namespace, and their copy is spelled differently: fifteen of its
twenty-one names disagree with the published spelling while **all
twenty-one values are identical**. Not one colour has drifted. Fifteen
spellings have. The copy also carries twenty-one of the ninety colours the
system publishes.

Nothing could have caught this. Each projection agreed with itself, and
the rule that decided the spelling was not written down anywhere a reader
could check it against. **NAM-001** now states it in `core/rules.json`,
its implementation is one function in `tools/project_tokens.py`, and a gate
asserts that the published name set equals the name set derived from the
contract. The gate was proved to bite: with the vendored spelling
substituted, it fails.

**The audit.** `tools/audit_frontends.py` walks the ten frontends and
produces a matrix and an inventory under `profiles/frontend-audit/`. The
matrix is the work list — colours, families and lengths each frontend uses
that the contract does not sanction — and the counts are the point, because
a yes/no would have hidden the size of the job. `ABSORPTION.md` reads the
numbers: what each frontend must change, in what order, and the four
decisions that are the owner's to make.

The palette is already shared. Eight of the ten frontends carry the
system's colours, to the byte, under their own names. The gap is spelling
and components, not taste. Two of the ten are not consumers at all, and
one of those claims in its source that it derives from a gnosix path that
does not exist.

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

## [3.6.0] — 2026-10-20

The contract stops being one shape and starts being portable.

**The contrast table is derived.** `core/TOKENS.json` stated seven approved
pairings and the ratio each one measures, and those numbers were written by
hand - so a colour could change and the ratio beside it would keep saying
what it said before. `tools/contrast.py` computes every declared ratio from
the palette it names and fails when the two disagree. A pairing name reads
`ink_on_substrate`, the way the contract reads it, where COL-002 puts white
essential text on Signal Orange; a name that is a family means that
family's base. Measured: changing Signal Orange by one unit moves the ratio
from 6.43 to 6.47, and the gate says so.

**The Android profile carries the surface layer.** `GnosixColors.kt` held
the palette; it now holds the surfaces too, in `GnosixSurfaces`, generated
from `core/SURFACES.json` like everything else. A Compose surface is the
system's own and not a second one written by hand.

**The native profile is not a stub.** `profiles/native/` was a status file
and a README. It now ships the projection as Rust constants - the palette,
the surfaces, the measured contrast ratios, the spacing and the weights -
in a crate with no dependencies, generated from the one token source, with
tests that say the palette is the approved one. It stays `mapped`: the
projection is ratified, the fixture is not, and no render is claimed.

**The tokens are exported in the formats other tools speak.** A design
system is portable when the tools that consume it can read it, and a
Tailwind config or a Style Dictionary build cannot read `core/TOKENS.json`
without being told how. `profiles/interchange/` carries the W3C Design
Tokens Community Group format and the Style Dictionary source format, both
generated from the token source and both checked in every qualification.
Neither is a second palette; they are the same values, reshaped for a
consumer that already knows how to read them.

The rules are not exported, on purpose. A format that carries values cannot
carry a constraint, and a rule that is not checked is documentation.

## [3.6.1] — 2026-10-20

The surface layer is checked for legibility, not only for derivation.

`tools/surfaces.py` verified that every step of the layer was the colour it
claimed to be. It now also verifies that the layer is *usable*: every
surface must take an ink that reaches AA against it, and every hairline
must reach 3:1 - the threshold for a graphic - against the substrate it is
seen on.

It found three surfaces that had no legible ink, and the reason was worth
having: the ink families of the layer are ramps, and the ramps stop short.
The strongest ink on a substrate is often the palette's own - anthracite on
the light substrate, shell white on the dark one - and the check was
looking only at the ramps, so it called legible surfaces illegible. The
palette is part of the system, and the check now counts it.

The hairline check is the one that holds either way: a line is on the
substrate it contrasts with, and which one that is, is a fact about where
it is used rather than something its own lightness settles. So a hairline
must reach 3:1 against the base of at least one of the two substrates, or
it is a line nobody can see.

## [3.7.0] — 2026-10-20

The contract gains a component layer.

`core/COMPONENTS.json` states the four components the contract defines -
the action, the input, the state and the system text - with the roles each
carries, the states it has, the tokens it uses and the accessibility it
owes. The tokens are named, never valued, so a component that names a
token the contract does not have is refused rather than projecting a custom
property that resolves to nothing.

`profiles/web/components.css` was written by hand, which meant the styles
a consumer shipped and the contract behind them were two things that could
disagree. It is now projected from the specification, and the projection is
checked in every qualification. The difference is small and one of the
differences is a repair: the hand-written stylesheet declared two of the
three states of the state component, and the projection declares all three.

The specification keeps the rules each component carries, so the rules are
attached to the thing they govern rather than to a paragraph somewhere.

What the specification does not do: it does not say that the public
reference uses these components. The site styles its own layouts with its
own class names and does not import the component stylesheet at all. That
is a real gap - the contract's components are used in one place out of two -
and it is the next thing to settle, not something to paper over here.

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
