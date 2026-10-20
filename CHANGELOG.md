# Changelog

All notable changes to gnosix_DS are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [semantic versioning](https://semver.org/spec/v2.0.0.html).

The canonical version lives in [`VERSION`](VERSION). Every other place the
package states a version is a slot that `tools/version.py` keeps in step, and
`python -m tools.version --check` fails the build if any of them drifts.

## [4.3.1] — 2026-10-20

The eye, and the defect it found on the first look.

**The system now looks at itself.** The qualification says what the
contract holds; it never said what the contract *looks like*. So the eye
renders the system's own web surfaces, on both substrates, walks them
with axe, and compares the pictures with the ones the system carries. A
component that moves by a pixel is caught there, and the comparison is on
the bytes, so the picture the system ships is the picture that was
looked at.

The browser is pinned by the lockfile, and the font is the one this
repository packages, so the rendering is the same on every machine that
provisions the browser the way `ci/provision-browser.sh` says. The same
script runs in CI, in the release job and in the local simulation. Where
there is no browser — a copy of the package, which carries neither — the
gate says so and stops: that is the third answer, not a failure.

**And it found something on the first look.** The badge carries the
condition as a shape and a word, never as a colour alone — that is what
the contract says. The projection wrote the mark as the element's
*background*, which painted the whole badge the condition's colour, and
the text with it: the stable badge rendered green, and its text measured
4.08 against a ground it was never meant to sit on. The contract was
right and the projection was wrong, and nothing between them said so.

The mark is a pip now — the shape the contract describes, in the
condition's colour, beside the word — and the badge reads 17.36 against
its own ground. The eye's findings are at zero, and they are a ratchet:
a finding that is not in the list the system carries is a new one, and
the gate fails on it.

## [4.3.0] — 2026-10-20

What the field has worked on, and the system did not carry.

**The system had no radius scale.** Its own components carried six
different radii, written as numbers, and the field rounds every surface
on its own — two to fourteen pixels, and the pill. The scale is now
ratified: the two lineages' steps and the system's own, so that every
component names a step instead of a number, and the gate refuses a
number. Nothing moved on the screen: each component's radius is the
step that holds the value it already had.

**The system had no vocabulary of motion.** It had the laws, the roles,
the seams and one target, and the field had fifteen mechanisms it had
never heard of — a fade, a scale, a lift, a mask reveal, a blur, a
dither, a fold, a refraction, a burst, a pulse, a type-on, a snap, a
morph, a spring, a stagger. They are carried now, by name and by
meaning, and the system judges them: fourteen are lawful, and one is
refused. The field's pulse breathes on a cycle that is tied to nothing,
and the law says motion does not idle. The numbers — the milliseconds,
the curves, the delays — are the target's expression, and they stay
there.

**The native shell's thirty-one arrangements are carried as a
translation.** Windows, trays, widgets, nested panels, the arrangements
it offers to an agent — the field made them, the system did not declare
them, and now the contract says what they are and what shape each one
has. The shell has no licence, so nothing of its implementation travels:
what travels is the fact that the field made these arrangements and what
each one is for. The shell is not vendored here, so this is a record, and
the native profile still carries no vocabulary of its own — that is the
next unit.

**Two findings were left open and are now closed by decisions that were
already taken.** The In-Shell's scale of spacing has three steps the
system's does not, and the decision was already made: the ten steps
stand, and a frontend's own scale is mapped onto them. An ordered scale
that is published does not renumber itself in the middle, and the three
are mapped rather than inserted. And a duration named for idling is not
carried either: the law forbids motion that idles, and a vocabulary that
offers it invites it. The pulse stays — a pulse tied to a state change
is lawful; it is the untied one that is refused.

## [4.2.1] — 2026-10-20

A mask is not a surface. The consumer gate found a colour the system
does not have in two repositories that had already re-vendored the
package: the black inside a `mask-image`. It is an alpha channel, not a
surface — it says "opaque here" — and the system's own sheet draws its
fades that way. The gate now reads the system's rule rather than a
second one.

## [4.2.0] — 2026-10-20

The field's vocabulary is specified, and the sheet the field writes with
is clean for the first time.

**The contract held thirty-nine names and nothing else.** That is a
classification, and a classification says only that a name is of a kind:
it can never be wrong, and it says nothing about what the thing is. The
contract now holds what each of them is.

The thirty-six arrangements the field writes with — twenty-nine patterns
and seven primitives — are specified by measurement. Their parts, the
tokens they consume, the geometry they establish, the type they set and
the behaviour they carry are read off the sheet and written down, and a
gate checks both ways: a part the contract names that the sheet does not
have is a failure, and a declaration in the sheet that the contract does
not name is a failure. Nothing about the field's vocabulary is a matter
of opinion any more.

**The three names that overlap the system's elements are the field's own
implementations, and the contract says how far they differ.** The field's
`action`, `state` and `section` are its own spellings of the `button`,
the `badge` and the `section-heading`. The field's own code converges on
the system's names — `badge` in two lineages, `section-heading` in two —
so those stay canonical and the sheet's are the field's. What the sheet
does with them is now written down: the sheet's action carries a mark
and an arrow the system does not declare and a pressed state the system
does not declare, and its badge carries two conditions the system's does
not have. The system specifies; it does not copy, and now it says where
the field's own thing stops matching the system's.

**The published sheet carried thirteen invalid declarations.** Thirteen of
its custom properties were written as references to themselves — a name
that refers to itself is invalid at computed-value time, and it only
appeared to work because the system declared the same name again further
down the file. One of the sheet's roles also still carried a colour of
its own; the binding now covers it. The sheet names the system in every
place it used to carry a value.

**The package carries the system's own fourteen elements too.** Under the
field's prefix, with the system's roles bound to the sheet's substrate
and its own tokens underneath. A consumer that has adopted the package
has the whole contract in one stylesheet and writes one convention; the
field's three keep their names, because a name that meant two things
would be a name nobody could read.

**And a gate counts.** The component layer is measured, not chosen: the
number of components, the number of arrangements, the number of parts and
the number of rules are facts a gate can read.

**The consumer gate learned to judge the components.** It measured them
and said nothing: it reported how many classes a consumer builds itself
and never failed on them. It now measures the consumer's *components* —
by the system's own rule, the one the convergence used, so a name in a
global stylesheet stays a utility — and compares them with the contract's
vocabulary: the system's fourteen elements and the package's fifty-three
names. What is left is the consumer's own, and it says so in its
`gnosix.json`, with the reason. A component the contract does not have
and the consumer does not declare is a failure.

Measured today, the same rule over the same field: `gnu.in.work` declares
a thousand and five components of its own, `gnosis.OS` thirty-two,
`gnu6.live` forty-one, and the two repositories that had already
re-vendored the package declare none at all.

## [4.1.0] — 2026-10-20

The system publishes the package the field vendors, the field's
vocabulary is translated in the contract, and the spacing scale is
published at last.

**The package had no source.** The sheet the field vendors said of
itself: *generated by tools/build.py from gnosix_DS TOKENS.json*. That
generator was in a distribution of this system that no longer exists —
this repository's history begins at v3.4.2, and the v3.4.1 distribution
has no such tool. The package's only surviving forms were three
byte-identical vendored copies, each with its own lock, and its
namespace carried the layer ids in the spelling this system does not
publish. Every value in it was right; only the spelling had drifted,
which is the one kind of drift nobody can see by looking at a colour.

So the system publishes the package now, cut from the contract by
`tools/package_gnu6_design.py`: the field's component vocabulary stays,
every `--gnosix-*` name is rebound to the name the system publishes, and
the system's own vocabulary is added — the colours the sheet omitted, the
surfaces, the weights, the spacing scale. The three repositories that
vendor it re-vendored it, and their locks now say which state of the
system it was cut from.

**The sheet's own role layer went.** It bound thirty-four roles by hand
for each substrate, in two `:root` blocks, and that hand-made layer was
where the sheet's twenty-seven colours the system does not have came
from. The binding is now declared, reviewable, and every one of those
colours is a step of the system. The colour gate examines the package
like any other part of the tree; only the adopted legacy sheet is
exempt, because it is a record.

**Two holes in the system were closed rather than papered over in a
consumer.** The light substrate's ink ramp began at 0.445 while its
strong ink sat at 0.14, so there was a hole in the coverage and the
field's converged value fell into it: `ink-on-light-l342c06` is now a
step of the ramp. And the contract stated a *selection* among its
semantic roles without ever binding one: the role is bound now, and the
dark substrate's selection ground is an accent.

**The field's vocabulary is translated.** The package declares thirty-eight
`g6-*` components the field uses and the system did not declare. The
contract now says what each of them is — three of them are the system's
own elements under another name, twenty-nine are patterns, seven are
primitives the type, spacing, accessibility or motion tier governs. A
gate reads the relation both ways, so the two vocabularies cannot drift
apart.

**The spacing scale is published at last.** The system had ten steps and
did not expose them, so a consumer that declared eight of its own was
declaring what the system already had.

**And the push guard learned to qualify a branch.** A branch push
triggers the CI job, and the local simulation covers that job exactly;
the guard checked only tags, and two commits went out qualified against
the previous commit rather than against themselves. The guard now
refuses a dirty tree and qualifies the commit locally before it goes,
and the installed hook is a wrapper that runs the repository's own file
rather than a copy of it that can go stale.

## [4.0.0] — 2026-10-20

The system gains the tier it was missing, and the component layer is
rebuilt on what the field actually agrees on.

**The gap was not a palette. It was a tier.** The contract had a palette,
a surface layer and a set of roles stated in prose, and no binding
between them. Every consumer therefore chose a colour for every role for
itself — which is why one frontend in the field carries about two hundred
and fifty hardcoded hex values in a single stylesheet, and why changing
substrate there was a manual job. `core/ROLES.json` is that binding: a
role says what a thing is *for*, and is bound to a token on the light
substrate and on the dark one. A component now names the role and is
written once. The layer projects to CSS custom properties, to Rust
structs, one per substrate, and to Kotlin colour maps, and the gate
refuses a role that binds to a token the contract does not have, or a
role pairing whose text does not read.

**The component layer had four components, and the field used none of
them.** The names now come from a measurement. The ten frontends were
walked, their component names counted, and the count taken over *lineages*
rather than repositories — because two of those repositories are one
lineage, and the design sheet they share is one artefact written once, so
counting them twice would have made one opinion look like an agreement.
Twenty-six names appear in two or more independent lineages. The
sub-components of a dialog are parts of a dialog, not dialogs, and the
domain-shaped ones are patterns rather than components; what remains is
fourteen elements that a web surface, a native surface and a portal
already agree on.

So the layer is rebuilt around them: **button, text-input, badge, card,
dialog, tooltip, select, tabs, toaster, toggle, command-palette, icon,
section-heading**, and the system's own base. The published class names
change with it — `.gnosix-action` is `.gnosix-button`, `.gnosix-input` is
`.gnosix-text-input`, `.gnosix-state` is `.gnosix-badge` — which is why
this is a major version. Nothing in the field used the old names.

**The projection is now generic.** It used to carry one hand-written block
of CSS per component, which meant every component added to the contract
needed a new special case in the renderer, and a design system whose
projection grows a special case per component is one whose projection
cannot be trusted. A component is now added by stating it: its roles, its
states, its variants, its geometry, its typography, its parts and the
accessibility it owes. The renderer walks the statements.

**The palette is now stated as it measures.** The approved green measures
4.09 against the light substrate and cannot carry body text. It is a
mark — a pip, a dot, an edge — and the tinted surface behind the word is
a separate role, `positive-surface`. A badge that says a condition in
words and reinforces it with a shape is what the contract asked for, and
the gate now checks that every variant reads on its own background
instead of asserting that it does.

## [3.8.1] — 2026-10-20

Publishing a release becomes idempotent, and the release workflow learns
to read the tag it is given.

**A release and a workflow argued over the same release.** The 3.8.0 tag
was pushed and the release was published by hand; the workflow then
reached its publication step, found the release already there, and failed
on it. The failure was a collision between two correct things, and it
cost a runner run — which is the method failure this repository's own
policy is about.

`tools.release publish` now looks for the release before it creates one.
If the release exists and carries the same content digest — the sha256 of
the uncompressed tar, which is a statement about the source rather than
about the machine that compressed it — the publication is already done and
the command says so. If it exists with a *different* digest, the command
refuses and prints both, because a different archive under a tag that is
already published is a real problem and not a race.

The release workflow also had a latent fault: it declared a `tag` input
for a manual dispatch and then ignored it, so a manual dispatch checked
out the default branch and refused to publish because a branch is not
tagged. It now takes the tag it was asked for.

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
