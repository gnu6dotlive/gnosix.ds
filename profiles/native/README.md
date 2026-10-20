# Native / GPUI mapping

This profile maps the gnosix portable contract to gnos.ux surfaces implemented with GPUI. It is intentionally **not** a Web-to-Rust component port: roles and state cross the boundary; HTML/CSS component structure does not.

## Typography

Use the packaged `assets/fonts/SpaceGrotesk-native.ttf` as the application font asset and select **Space Grotesk** for visible UI, reference labels, metadata and technical strings. Current upstream GPUI supports application-supplied raw TTF/OTF fonts through its text system / font-loading path; V3.4.1 therefore maps the shipped TTF directly instead of relying on a host-installed family. Keep the exact API behind a small gnos.ux font adapter because GPUI remains pre-1.0 and changes frequently.

Typography gate: load the TTF before the first reference surface, verify `éàçîœ>_$#`, verify weights 300–700, and capture the computed/selected family in runtime evidence. No second interface family is part of the V3.4.1 visual contract; baked identity artwork is not interface typography.

## Semantic projection

| Portable role | GPUI projection boundary | Runtime evidence needed |
|---|---|---|
| `primary-action` | focusable action element; Signal Orange paint; Anthracite text; keyboard activation | focus-visible capture + keyboard activation test |
| `secondary-action` | lower visual priority with the same discoverability and accessible name | focus order + contrast evidence |
| `status-*` | text first; optional small painted pip; never a rounded status capsule | color-disabled/readability check |
| `evidence` | Space Grotesk technical treatment with tabular numerals for short IDs/measurements | font selection + copy/readability capture |
| `focus` | explicit visible focus treatment independent of hover | keyboard traversal evidence |
| `selection` | structural surface/edge/outline treatment plus accessible selected state | selected-state semantics evidence |
| `scalar-field` | shader/custom paint is presentation only; quantity/range/legend/missing state stay inspectable outside the shader | legend + missing-state + semantic description evidence |

## Surface projection

Keep the portable surface layers separate in the gnos.ux implementation:

- **geometry / visible hull** → layout bounds, clipping and custom path geometry;
- **material** → fill, gradient, texture or custom paint response;
- **chrome** → border, separator, focus and selection treatment;
- **depth** → contact/lift/recess/rim/bevel paint without redefining hit testing;
- **content** → text/icons/visual data with semantic role;
- **interaction / hit region** → focus, pointer and keyboard target;
- **allocation** → layout reservation independent from paint overflow.

A shader may implement material or a scalar field; it does not own semantic state. The data model supplies the state and the renderer projects it.

## Current upstream note

The mapping was checked against the current Zed/GPUI repository on 2026-09-24. Upstream documents `gpui_platform::application()` for standalone apps, Linux Wayland/X11 backends, and raw TTF/OTF font addition. GPUI is still pre-1.0, so this profile treats those API details as version-scoped implementation guidance rather than portable authority.

Upstream references:
- `https://github.com/zed-industries/zed/blob/main/crates/gpui/README.md`
- `https://github.com/zed-industries/zed/blob/main/crates/gpui/examples/README.md`

## The projection

`src/` is a crate that carries the contract as Rust constants: the palette,
the surface layer, the measured contrast ratios, the spacing steps and the
weights. It is generated from `core/TOKENS.json` and `core/SURFACES.json` by
`tools/project_tokens.py`, so the native projection is the same values under
the same names as the web and the Android ones. There is no second palette
to keep in step.

```sh
cargo test --manifest-path profiles/native/Cargo.toml
```

The crate has no dependencies, on purpose. The GPUI adapter is version-scoped
and belongs to the implementation that uses it; what is ratified here is the
projection, and that needs nothing but the standard library.

## Status

This profile is `mapped`. The projection is generated and checked in every
qualification, but no compiled gnos.ux fixture or target capture is included
in this package, so it must not be called rendered or verified.
