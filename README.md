<div align="center">

# gnosix.DS

**A portable interface contract.** Rules, tokens, semantic roles, components and
inspectable reference scenes that carry one design system from the browser to
Compose to GPUI — without turning any toolkit into the design system.

`v4.0.0` · MIT · 21 gates, one command

</div>

---

## What this is

A design system is a set of decisions that other people make every day. This
package holds those decisions in a form a machine can check, and projects them
onto the targets that have to honour them.

The distinguishing idea is that **portable meaning is authoritative**. The
contract says what a surface is *for*; each target says what that is worth in
its own idiom. Nothing here is a picture of a thing, and nothing here is
somebody else's component library with the serial numbers filed off.

The system is in four tiers, and each one is a file you can read:

| Tier | File | What it holds |
|---|---|---|
| Rules | `core/rules.json` | 16 numbered obligations — `COL-001`, `A11Y-001`, `SUR-001` — each with an observable and a test |
| Palette & surfaces | `core/TOKENS.json`, `core/SURFACES.json` | the approved colours, the elevation ramps, the spacing steps, the family and the weights |
| Semantic roles | `core/ROLES.json` | 14 roles — `surface`, `ink`, `accent`, `focus`, `positive` — bound to a token on each substrate |
| Components | `core/COMPONENTS.json` | 14 elements: their roles, states, variants, geometry, typography and the accessibility they owe |

Everything below the tiers is a **projection**: generated from the contract,
checked in, and refused if it drifts.

---

## The system at a glance

### The palette

Five approved colours. The system spends Signal Orange on the principal
operation of a context and on nothing else; the rest carry structure.

| | | |
|---|---|---|
| **Anthracite** `#111418` | the dark substrate, and the ink on it | `neutral/anthracite` |
| **Shell White** `#F7F3ED` | the light substrate | `neutral/shellWhite` |
| **Signal Orange** `#FF6A00` | the one accent | `signalOrange/base` |
| **Beret Green** `#5F7F52` | a condition that is well | `beretGreen/base` |
| **Royal Blue** `#4169E1` | focus, and selection | `royalBlue/base` |

Each family carries a ramp of steps. The surface layer adds 66 elevation steps
across two substrates, every one of them identified by its own lightness and
chroma, so a surface cannot drift out of its family without the check
noticing.

### The roles

The tier that was missing until this release, and the reason one frontend in
the field carried two hundred and fifty hardcoded hex values in one
stylesheet. A role says what a thing is **for**; the contract says what that
is worth on each substrate.

| Role | Light | Dark | |
|---|---|---|---|
| `surface` | Shell White | Anthracite | the page behind everything |
| `surface-raised` | `#F7F8F8` | `#1D2228` | a card, a panel, a tile |
| `surface-overlay` | `#FBFBFB` | `#242A31` | a dialog, a menu, a popover |
| `surface-sunken` | `#E1E5E8` | `#14181C` | a well: a code block, a track |
| `ink` | Anthracite | Shell White | the text that is read first |
| `ink-muted` | `#4B5560` | `#8D99A6` | a caption, a secondary label |
| `hairline` | `#E3E5E8` | `#2B3138` | the line between two surfaces |
| `accent` | Signal Orange | Signal Orange | the principal operation, and only that |
| `accent-ink` | Anthracite | Anthracite | the text that sits on the accent |
| `focus` | Royal Blue | Royal Blue | where the keyboard is |
| `positive` | Beret Green | `#8DA982` | a condition that is well, as a mark |
| `positive-surface` | `#E8EFE5` | `#455F3D` | the tinted surface behind the word |
| `caution` | `#F5A524` | `#F5A524` | a condition that asks for inspection |
| `critical` | `#E5484D` | `#E5484D` | a condition that is a failure |

The split between `positive` and `positive-surface` is measured, not tasteful:
the approved green measures **4.09** against the light substrate and cannot
carry body text, so it is the mark — the pip beside the word — and the tinted
surface behind the word is a separate role. Every pairing that carries text
is checked at 4.5 on both substrates.

### The components

The names come from a measurement of the field, not from a preference. The
private frontends that use this system were walked, their component names
counted, and the count taken over *lineages* rather than repositories: two of
those repositories are one lineage, and the design sheet they share is one
artefact written once, so counting them twice would have made one opinion
look like an agreement.

Twenty-six names appear in two or more independent lineages. The parts of a
dialog are parts of a dialog, and the domain-shaped ones are patterns rather
than components. What remains is what a web surface, a native surface and a
portal already agree on.

| | | |
|---|---|---|
| `button` | the control a person presses | 4 variants · 6 states |
| `text-input` | a field with a visible label | 5 states |
| `badge` | a short mark that says what a thing is | 4 variants |
| `card` | a raised surface holding one thing | |
| `dialog` | an interruption that takes the keyboard | 6 parts |
| `tooltip` | an explanation that goes away | 3 parts |
| `select` | a control that opens a list of choices | 3 parts |
| `tabs` | panels that share one subject | 3 parts |
| `toaster` | where a transient message arrives | 2 parts |
| `toggle` | something that is on or off | 3 parts |
| `command-palette` | a field that takes a command | 5 parts |
| `icon` | a glyph from the ratified subset | |
| `section-heading` | the heading of a section | 4 parts |
| `system` | the typographic and numeric base | |

Every component states its roles, its states, its variants, its geometry, its
typography and the accessibility it owes — and the stylesheet is rendered from
those statements by a renderer that is generic. Adding a component to the
contract means stating it, not adding a case to the renderer.

---

## Using it

The contract is portable; the rendering is not. Each target consumes the
projections and restates nothing.

### Web

```html
<link rel="stylesheet" href="profiles/web/tokens.css">
<link rel="stylesheet" href="profiles/web/roles.css">
<link rel="stylesheet" href="profiles/web/components.css">
```

```html
<button class="gnosix-button" data-variant="primary">Enable</button>
<input class="gnosix-text-input" id="target">
<p class="gnosix-badge" data-variant="attention">Request pending</p>
```

The substrate is chosen once, by the attribute:

```html
<body data-gnosix-substrate="dark">
```

Roles are bound per substrate, so a component is written once and reads on
both. `profiles/web/state.ts` projects a request into its observed state, and
never announces a success it has not observed.

### Native — Rust

```rust
use gnosix_ds::roles;

let theme = roles::DARK;          // or roles::LIGHT
let surface = theme.surface;      // the contract's own constant
```

The crate is dependency-free, and the values it carries are the contract's
constants rather than a second transcription of them.

### Android — Compose

```kotlin
val surface = GnosixRoles.of("dark", "surface")
```

### Interchange

`profiles/interchange/` carries the tokens in the two formats other tools
already read: **DTCG** (`gnosix.tokens.json`) and **Style Dictionary**
(`gnosix.style-dictionary.json`).

### FigCraft

`figcraft/` projects the system into a FigCraft project — ten boards, the
whole component vocabulary, and a published library another `.figcraft` can
consume. The projection is a generated artefact of this repository, byte-gated
against its source, not a place the contract is edited.

---

## What is in here

```
core/          the contract: rules, tokens, surfaces, roles, components, semantics
profiles/      the projections: web, native, android, interchange, motion
references/    six annotated scenes — actions, adaptive, fields, identity, state, surfaces
site/          the public visual reference
tools/         the gates, and the generators behind every projection
figcraft/      the FigCraft projection
assets/        the ratified fonts, icons and identity masters
```

### The frontend audit

`profiles/frontend-audit/` holds the audit of the ten private frontends that
consume this system: a **matrix** of what each one does against each
criterion, an **inventory** of every colour, family and length it uses that
the contract does not sanction, and an **absorption plan** that says what each
one must change and in what order.

The measurement is taken over lineages, and the reason is written down: a
repository is not an opinion, and a design sheet written once and vendored in
two places is one artefact, not two agreements.

---

## Working on it

The package is qualified by one command, and it is the same command locally
and in CI:

```sh
python3 -m tools.ci
```

It runs every gate in the list and prints one verdict. The list lives in
`tools/ci.py`, in the repository, so a developer and an agent run exactly the
same thing. A check list reproduced in YAML is a second implementation of the
contract, and the second one is the one nobody runs locally.

The gates under `tools/` need no packages at all. They are standard-library
only, deliberately: a gate that cannot run without a wheel is a gate that
does not always run.

### The gates

```
tokens project cleanly                        the role layer is bound to the contract
the surface layer is derived                  the component stylesheet is what the spec projects
the contrast table measures what it says      every colour is one of ours
the token exports are current                 the surfaces use the system's colours
version authority                             contract validates
manifest matches the tree                     alpha masters are straight
mascot alpha is repaired                      svg wrappers embed once
favicons are the right crop                   icon subset is vendored
no ad-hoc glyphs                              the FigCraft projection matches the source
the two token projections agree               the web code matches the design
test suite
```

### The version authority

The package states its version in more than one place, and until V3.4.2 each of
those places was written by hand — which is how a release shipped with a
manifest still announcing an older version and a web manifest announcing a
different one, with nothing in the gate chain noticing.

There is now one value with one owner:

```sh
python3 -m tools.version --show     # the version and every slot that states it
python3 -m tools.version --check     # the gate: does every slot agree?
python3 -m tools.version --sync      # write VERSION into every slot
```

`VERSION` is the source. The rules file, the motion profile, the projection
map, the six reference scenes and their sheets, the site's display slots, the
web manifest and the package manifest are the slots. `--check` verifies the
property rather than a diff, and reports the slot that disagrees rather than
a patch.

### Releasing

```sh
python3 -m tools.release status              # where the repository stands
python3 -m tools.release bump --patch        # move VERSION, sync, rebuild the manifest
git commit -am "release: 4.0.1"
python3 -m tools.release prove                # run the release job locally, record the proof
python3 -m tools.release build                # dist/Gnosix-DS-V4.0.1.tar.gz
python3 -m tools.release tag                  # annotated v4.0.1
git push && git push --tags
python3 -m tools.release publish              # GitHub release with the archive
```

The order is enforced, not conventional. `bump` moves the version and
rebuilds the manifest, because the manifest hashes the version file. `tag`
refuses a dirty tree, because a tag names a state and a dirty tree is not
one. `publish` refuses unless the tree is clean, the tag exists, the tag
agrees with the version, and the archive has already been built — and it is
idempotent, because a release that already exists with the same content
digest is already the one this tree would publish.

**Push the tag, and let the workflow publish it.** The release workflow
qualifies the tagged commit, builds the archive from it and attaches it. A
person publishing by hand as well is two correct things colliding.

The archive is built in two layers, and the two are reported separately
because only one of them is a statement about the source alone:

- The **tar stream** inside is byte-reproducible — entries are sorted,
  timestamps are fixed, ownership is cleared, and the gzip header carries
  neither a name nor a time. Its digest is the same on every machine that
  checks out the same commit, and it is the one published in the release
  notes.
- The **gzip wrapper** around it is not, because gzip's output depends on
  the zlib build that produced it.

So a consumer who rebuilds the archive gets a bit-identical tar and, on a
different zlib, a different `.tar.gz` around it. **Compare the content
digest.**

---

## The rest of the contract

### Icons

The ratified icon pack is **[Tabler Icons](https://github.com/tabler/tabler-icons) 3.49.0**
and the ratified flag pack is **[Tabler Flags](https://github.com/tabler/tabler-flags) 0.1.1**.
Both are MIT licensed, Copyright (c) 2018-2026 Paweł Kuna, and the verbatim
licence text ships in `assets/icons/licenses/`.

Rule `ICON-001` governs the use of glyphs: interface icons come from the
ratified subset, and a text character may not stand in for one. A character
that renders as an icon is still an icon, with none of the guarantees — it
inherits the font's metrics, it cannot be recoloured independently, and it is
a different shape on every platform.

The package **vendors** a curated subset at a pinned upstream tag rather than
referencing a CDN, exactly as it vendors Space Grotesk. A design contract
whose appearance changes when a third party publishes is not a contract. The
subset is 41 icons and 8 flags, each recorded in
`assets/icons/icon-manifest.json` with its upstream URL, its role and its
SHA-256.

### Identity

The ratified `gnosix`, `gnu6.live` and `gnu.in.labs` cube images are the
visual masters, and the ratified overlapping orange / Royal Blue / green
plate mark is unchanged.

One **alpha compositing variant** per identity ships as `*-cube-alpha.png`
plus an exact-fidelity SVG wrapper. These are the same artwork with the
authored dark field carried as alpha: the RGB of every fully opaque pixel is
byte-identical to the corresponding opaque master, and the asset suite
verifies that rather than asserting it. The edge pixels are straight alpha —
the subject colour at true coverage, not a premultiplied blend. Per `ID-004`
they are sanctioned on neutral substrates only. Over Signal Orange, Royal
Blue or Beret Green the opaque master is used, because a chromatic substrate
would collapse the cube's dark faces into the brand hue.

### Motion

`profiles/motion/` supplies the motion **meaning**: six laws (causality,
performance, continuity, interruptibility, reduced-motion equivalence,
stillness-before-climax), four prohibitions, seven motion roles each with a
declared reduced-motion projection, and seven seams. It deliberately does
**not** ratify a global duration ladder.

- `MOT-BAN-IDENTITY-MOTION` forbids applying motion to a ratified master. A
  mark is a still thing and the frame moves around it.
- `targets.remotion.reduced_motion.detection` requires reduced motion to be
  an **explicit input**, because a headless renderer reports the render
  machine's motion preference rather than the viewer's.

### Evidence and status

Web, Android and gnos.ux/GPUI are `mapped`. Motion is `mapped`, implemented
by the Remotion target. None is promoted to `rendered` or `verified` until
target-scoped evidence is recorded in this package: renders produced by a
consumer live in that consumer's repository, and the evidence ladder is
explicit that a capture has to be recorded against the claim it supports.
The package does not promote a profile merely because another profile renders
correctly.

---

## Licence

MIT — see [`LICENSE`](LICENSE). The redistributed third-party assets and their
licences are listed in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and
per file in [`assets/LICENSES.md`](assets/LICENSES.md).

The release history is in [`CHANGELOG.md`](CHANGELOG.md). The version this
checkout states lives in [`VERSION`](VERSION) and nowhere else.
