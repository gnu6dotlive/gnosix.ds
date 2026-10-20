# Interchange / exports

The token source, exported in the formats other tools already speak.

A design system is portable when the tools that consume it can read it. The
package states its tokens in `core/TOKENS.json`, and the web, the Android
and the native profiles project it from there — so the system travels
between the tools that read *those* profiles, and not between the tools that
read tokens. A Tailwind config, a Style Dictionary build or a
design-token pipeline cannot read `core/TOKENS.json` without being told how.

This profile closes that. Two exports, both generated from the one source by
`tools/export_tokens.py`:

| File | Format | For |
|---|---|---|
| `gnosix.tokens.json` | the W3C Design Tokens Community Group format | a design-token pipeline, Figma Variables importers, anything that speaks DTCG |
| `gnosix.style-dictionary.json` | the Style Dictionary source format | a Style Dictionary build, and the config files derived from it |

Neither is a second palette. They are the same values, reshaped for a
consumer that already knows how to read them, and `tools/export_tokens.py
--check` fails the build if either drifts from the token source.

## What is not exported, and why

The **rules** are not exported. `core/rules.json` states constraints — a
contrast that must hold, a shape that is forbidden, a colour that must
appear on another — and a format that carries values cannot carry a
constraint. A rule that is not checked is documentation; the rules in this
package are checked, by `tools/contrast.py` for the measured pairings and by
`tools/contract_colors.py` for the palette itself.

The **contrast ratios** are exported as values, because they are values, but
they are derived: `tools/contrast.py` computes each one from the palette it
names and fails when the table and the palette disagree.

## Status

This profile is `mapped`. The exports are generated and checked in every
qualification, and a consumer of either format is a claim the package has
not made.
