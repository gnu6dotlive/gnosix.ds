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
