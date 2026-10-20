# The FigCraft projection

`gnosix-ds.figcraft` is the gnosix design system as a FigCraft project: seven
pages built from the token source, the rules, the icon manifest and the
reference scenes.

It is a **build artefact**, not a copy. `generate.py` reads this repository
and writes the project, so a token change and a rebuild cannot disagree.

```sh
python3 figcraft/generate.py           # rebuild the project and the command script
python3 figcraft/generate.py --check   # the gate: rebuild and compare, write nothing
```

The gate is part of the qualification contract (`python3 -m tools.ci`), so a
projection that has drifted from the source fails the build.

## Why it is not in the package

The package ships the portable contract and the small projections of it —
the CSS custom properties, the Compose colours. The FigCraft projection is a
6 MB document for one editor among several, and it is only useful to a
consumer who already has the repository. So it lives in the repository and
not in the tarball, and `manifest.json` does not hash it.

## The mapping

| Source | Becomes |
|---|---|
| `core/TOKENS.json` `color` | a **variable collection** `Colour`, one variable per token, and a **paint style** per colour |
| `core/TOKENS.json` `spacing` | a **variable collection** `Space`, one number variable per step |
| `core/TOKENS.json` `typography.weights` | a **text style** per weight, and a specimen per weight |
| `core/TOKENS.json` `contrast` | the Contrast page: each pairing drawn as it is used, with its measured ratio and an AA verdict |
| `core/rules.json` | the Rules page: one card per rule, the rule carried as an **annotation** for Dev Mode |
| `assets/icons/icon-manifest.json` | the Components page: one cell per vendored glyph, imported from the SVG so the layers are editable |
| `references/*.svg` | the Scenes page: imported as editable frames, not pictures |

A swatch is **bound to its variable**, not filled with a literal. That is the
live edge of the system: `variable.set` on a token moves the swatch, and
`get_node` reports the binding as `boundVariables`.

## The two-level gate

The gate compares bytes, because the build is byte-deterministic and the
shape is not enough: the project has the same 777 nodes and the same seven
pages whether the token is `#FF6A00` or `#FF6B00`.

It has two levels, because a CI runner does not have a design editor:

1. **The command script** — `gnosix-ds.figcraft.jsonl` is what the generator
   says about the source. Comparing it needs only Python, and it catches the
   common drift: the source moved and nobody rebuilt.
2. **The project** — rebuilding the `.figcraft` needs the FigCraft CLI. It
   catches the other half: the script was regenerated but the project was
   hand-edited, or the engine changed underneath.

The second level is skipped, not failed, when no FigCraft CLI is present.

## The library

The projection is published as a **FigCraft library**, so another file can
consume the system rather than redraw it. `library.publish` runs as part of
the build, because the library is a published asset and not something a
consumer has to remember to do.

What it offers:

| | |
|---|---|
| `Rule Card` | a card carrying a rule: text properties `id`, `rule`, `scene` |
| `State Pip` | a state mark, three variants — `body`, `large`, `fail` — under one variant property `state` |
| `Specimen` | a type specimen, one variant per ratified weight, under `weight` |
| `Colour`, `Space` | the variable collections, with their variables |
| 25 paint styles | one per approved colour, named `family/shade` |

Consuming it, from any FigCraft file:

```sh
figcraft-cli run consume.jsonl
```

```json
{"command": "library.add", "params": {"path": "…/figcraft/gnosix-ds.figcraft"}}
{"command": "library.place", "params": {"library": "gnosix.ds", "component": "Rule Card", "x": 64, "y": 64}}
{"command": "instance.setProperties", "params": {"ids": [{"$step": 1}], "properties": {"id": "COL-001", "rule": "Read exact approved colors…", "scene": "scene: actions"}}}
{"command": "library.applyStyle", "params": {"library": "gnosix.ds", "style": "signalOrange/base", "ids": [12], "target": "fill"}}
```

`library.applyStyle` links the layer to the library's style rather than
copying the colour, so a change to the style reaches the consumer.

### The state pip, and why it is a mark

The reference scene forbids the rounded status capsule and prescribes
"text + pip instead"; CMP-001 is the rule that forbids it. The pip is
therefore a mark, not a badge, and its **shape** carries the state — a filled
disc, a ring, a triangle — with the words beside it saying which threshold
was met. Three states, not two: a pairing that meets the body threshold and
one that meets only the large threshold are not the same state.

The words are the neutral ink rather than a colour, because the palette has
no colour that reads as a failure and still passes AA on white: Signal
Orange is 2.87 against white, and the approved pairings do not include a
failing ink.

## Rebuilding elsewhere

The generator needs `figcraft-cli` on the path, or `FIGCRAFT_CLI` pointing at
it. The upstream repository is <https://github.com/storytold/figcraft>.

It also needs **Space Grotesk**, because the text layout is part of the file:
a machine without it lays the text out differently and the bytes differ
with the same script. The engine reads user fonts from `$XDG_DATA_HOME/fonts`
on Linux, so the font goes in there:

```sh
mkdir -p "$XDG_DATA_HOME/fonts"
cp assets/fonts/SpaceGrotesk-native.ttf "$XDG_DATA_HOME/fonts/"
```

The system's own fonts do not need to be pinned. The same bytes come out
with five fonts installed and with sixteen hundred, because every glyph in
the projection is in Space Grotesk and nothing falls back — but that stops
being true the moment a character missing from Space Grotesk enters the
design, and the gate is what would say so.

## What the gate compares

The command script, and the project. The script is the generator's account
of the source, and it is compared byte for byte, so it is a statement about
the source and not about the machine. The project is compared byte for byte
too, for the same reason: the shape of the project is identical whether the
token is `#FF6A00` or `#FF6B00`, so a shape comparison would pass a
one-hex change.

The comparison is over the **design content**, not over the container. The
archive is a zip, and publishing a library writes a receipt into it with a
fresh id and a fresh timestamp, so the container differs on every build even
when nothing about the design changed. The receipt is compared with those
two fields removed, and everything else with its bytes.
