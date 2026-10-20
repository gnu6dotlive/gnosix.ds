# Identity contract

## Canonical public names

Use these spellings in user-facing copy and authored reference material: `gnosix`, `gnos.ux`, `gnu6.live`, `gnu.in.labs`, and `gnosix_DS`. Programming-language identifiers may use platform-appropriate casing such as `GnosixColors`; those identifiers are not display-name authority. The retired all-caps dotted spelling must not re-enter current surfaces.

`core/rules.json` provides stable rule IDs. Interface color tokens remain in `TOKENS.json`; the ratified identity masters below are authored material artwork and are not required to be pixel-flat token swatches.

| Identity | Semantic color family | Dark face | Symbol | Ratified master | Exact SVG container | Alpha master |
|---|---|---|---|---|---|---|
| gnosix | Signal Orange | right | `>_` | `assets/identity/gnosix-cube.png` | `assets/identity/gnosix-cube.svg` | `assets/identity/gnosix-cube-alpha.png` |
| gnu6.live | Royal Blue | left | `>$` | `assets/identity/gnu6-live-cube.png` | `assets/identity/gnu6-live-cube.svg` | `assets/identity/gnu6-live-cube-alpha.png` |
| gnu.in.labs | Beret Green | top | `>#` | `assets/identity/gnuinlabs-cube.png` | `assets/identity/gnuinlabs-cube.svg` | `assets/identity/gnuinlabs-cube-alpha.png` |

The three cube PNG files are the **ratified visual masters**. Preserve each image as authored: topology, dark-face assignment, glyph scale, material response, highlight, edge treatment and local color modulation belong to the artwork. Do not regenerate a cube from tokens, reconstruct its glyph with live text, perspective-transform the glyph, or normalize the three masters into a synthetic shared geometry. The semantic color-family names above connect the marks to the wider system; they do not imply that every painted pixel equals the flat base token.

The cube glyphs are artwork, not interface typography. Lato Black was the selected typographic direction during exploration, but the accepted raster masters are the final appearance authority until a separately proven vector trace is ratified. Interface and documentation typography remains Space Grotesk.

## Alpha compositing variants

V3.4.1 ratifies one alpha-channel master per identity, listed in the table above. These are **compositing variants, not new artwork**: the RGB of every fully opaque pixel is byte-identical to the corresponding opaque master, and the only change is that the flat dark field the artwork was authored on is carried as alpha rather than as color. `tools/` and the asset suite verify this identity rather than asserting it, so a future edit that repainted, eroded or re-graded the subject would fail validation.

The alpha masters are **straight (unmatted) alpha**. The edge pixels store the subject colour at partial coverage; they do not store a blend of the subject with the removed field. This matters because the two are indistinguishable when the asset is viewed on the field it was cut from, and visibly different everywhere else: a premultiplied edge composites as a dark fringe on any neutral substrate. `tests/test_assets.py` asserts this directly by requiring the edge to lighten, never darken, when the substrate is changed from the field to white.

The coverage ramp along the silhouette is continuous rather than quantised, so the outline stays smooth at presentation sizes well above 32px.

The alpha masters exist so a consumer can place a mark over a sanctioned neutral substrate without rebuilding the artwork. Because the dark faces of all three cubes sit close to Anthracite, the following substrates are sanctioned:

- the `neutral` ramp: `anthracite`, `shellWhite`, `pureWhite`, `hairline`, `quietDivider`, `muted`, `slate`.

The following are **not** sanctioned, and the opaque master is used instead:

- `signalOrange.*`, `royalBlue.*`, `beretGreen.*` — a chromatic substrate collapses the cube's dark faces into the brand hue and destroys the dark-face assignment that `ID-001` protects.

This is rule `ID-004`. It is a substrate restriction only. It does not permit perspective transforms, re-lighting, per-pixel recolouring, or any other manipulation of the master; `ID-003` continues to govern all of those unchanged.

## Mascot and icon assets

`assets/mascot/` holds the three Syster references. Their alpha channels are straight alpha with a genuinely opaque body and a thin antialiased outline. A body that sits just below full opacity is a defect, not a style: it lays a film of the substrate over the whole character. The suite asserts the body is opaque rather than asserting a particular edge hardness, so an authored soft shadow would still pass.

`site/favicon-*.png` is generated from the ratified `gnosix-ds-mark.png` crop by `tools/build_favicons.py`, at 16, 32, 48, 180, 192 and 512px. The icons carry the mark's field as alpha. The site also ships `site.webmanifest` and an `apple-touch-icon`. Regenerating them is a container change: the opaque artwork inside is the ratified mark, which the suite verifies against the same crop.

## gnosix_DS mark

`assets/identity/gnosix-ds-mark.png` is the ratified orange / royal-blue / green layered-plate mark used beside the `gnosix_DS` wordmark. `gnosix-ds-mark-master.svg` is an exact pixel-for-pixel SVG wrapper of that master. `gnosix-ds-mark.svg` changes only the SVG viewBox to remove presentation whitespace for UI placement; it does not redraw the artwork.

The mark and the three cubes are distinct identity objects. Do not fuse them into a rainbow cube or substitute Syster for either.

Syster remains a mascot reference under `assets/mascot/`. Artwork defines appearance only; it says nothing about runtime behavior or authority.

## Interface glyphs are not identity artwork

The ratified identity masters and the interface icon set are different things, and the boundary is `ICON-001`. The cube's terminal symbols are baked into the artwork and are not live glyphs. The interface icons under `assets/icons/` are Tabler, vendored and pinned, and they are never mixed into an identity master. A mark is not a component, and a component is not a mark.

`core/IDENTITY.md` governs the first; `ICON-001` governs the second. Neither permits a glyph to be substituted for the other.
