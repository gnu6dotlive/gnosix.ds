# Asset licenses and provenance

| Asset | Provenance / purpose | License / note |
|---|---|---|
| `fonts/SpaceGrotesk-wght.woff2` | Space Grotesk variable Web source, weights 300–700 | SIL Open Font License 1.1; verbatim license in `fonts/SpaceGrotesk-OFL.txt` |
| `fonts/SpaceGrotesk-native.ttf` | Deterministic sfnt conversion of the packaged WOFF2 for native targets | Same SIL OFL 1.1 terms; SHA-256 `1da7b6f522eacee65e0ee4197aac77ecc21274875edb9b62771438934577218a` |
| `profiles/android/sample/app/src/main/res/font/space_grotesk.ttf` | Byte-identical Android resource copy of `SpaceGrotesk-native.ttf` | Same SIL OFL 1.1 terms |
| `fonts/IBMPlexMono-{400,500,600}.woff2` | IBM Plex Mono, the technical family; Latin subset, weights 400-600 | SIL Open Font License 1.1; verbatim license in `fonts/IBMPlexMono-OFL.txt`; SHA-256 `400` `08949f728dc52d528e69b1667d15c89a5686a4ee9a296ff90983985f99c380f7`, `500` `01d285447409c8a588692162439a038b8cbd7871309ee20267b0d2d91c6e8e22`, `600` `0d1f0b8d0722224e32e9f28261bdc86c79115be73444ae5eceb73976a1bcdf83` |
| `fonts/IBMPlexMono-native-{400,500,600}.ttf` | The same family, as sfnt for native targets | Same SIL OFL 1.1 terms; SHA-256 native `400` `5c6be3be05cc075aa0c353d818a8eb22a1f06b7f3d25a537b22c4c7751d7ae0e`, `500` `2c8c2e6c958ca6a3ad2c4f4eea1a9eafde9d6ef6bc6219103878a86fdbd45586`, `600` `aa6a6a54da1c0d5104b31b45550fd27eb493e4a0d44c85195555bae332eff2e0` |
| `profiles/android/sample/app/src/main/res/font/ibm_plex_mono.ttf` | Byte-identical Android resource copy of `IBMPlexMono-native-400.ttf` | Same SIL OFL 1.1 terms |
| `icons/outline/*.svg` | Tabler Icons 3.49.0, outline subset vendored for `ICON-001` | MIT, (c) 2018-2026 Paweł Kuna; verbatim license in `icons/licenses/Tabler-Icons-LICENSE.txt` |
| `icons/flags/*.svg` | Tabler Flags 0.1.1, ratified country and organisation flag subset | MIT, (c) 2018-2026 Paweł Kuna; verbatim license in `icons/licenses/Tabler-Flags-LICENSE.txt` |
| `icons/sprite.svg` | Symbol sheet built from the vendored icon subset by `tools/vendor_icons.py` | Same MIT terms as the icons it contains |
| `icons/icon-manifest.json` | Ratified icon set: upstream URLs, roles and SHA-256 digests | Package metadata; the digests are the authority |
| `identity/*.svg` | Gnosix / gnu6.live / gnu.in.labs identity artwork in this package | Project-owned design assets; SVGs embed the packaged Space Grotesk WOFF2 for deterministic authored typography |
| `mascot/*.png` | Syster visual references | Project-owned design assets |
| `references/visual-evidence/*.png` | Current visual evidence boards | Project-owned evidence assets; appearance evidence only |

The native TTF was produced locally with FontTools by loading the packaged variable WOFF2, clearing the WOFF2 flavor, and saving the equivalent sfnt/TTF. No outlines, naming tables, variable `wght` axis or glyph repertoire were intentionally changed. The conversion is covered by the original Space Grotesk OFL.

Release file hashes belong in `manifest.json`; the rows above document asset provenance and the stable native-font digest used by the V3.2 typography gate.

## Tabler icon and flag packs

The ratified icon pack is [Tabler Icons](https://github.com/tabler/tabler-icons) 3.49.0 and the ratified flag pack is [Tabler Flags](https://github.com/tabler/tabler-flags) 0.1.1. Both are MIT licensed, Copyright (c) 2018-2026 Paweł Kuna, and the verbatim license text ships in `icons/licenses/`.

The package **vendors** a curated subset at a pinned upstream tag rather than referencing a CDN. A design contract whose appearance changes when a third party publishes is not a contract, and the package's other third-party asset, Space Grotesk, is handled the same way. Every vendored file's SHA-256 is recorded in `icons/icon-manifest.json` and asserted by `tests/test_assets.py`; `tools/vendor_icons.py --fetch` regenerates the subset and `--check` verifies it without touching the network.

The subset is deliberately smaller than the upstream set. The upstream pack carries 6238 icons and the flag pack 304; this package ships 41 icons and 8 flags, each with a recorded role. Shipping the full catalogue would add megabytes to a contract that references a few dozen glyphs, and would imply an authority over the whole set that no consumer in this package has asked for. The upstream set remains documented in the manifest, so a consumer that needs a glyph this package does not vendor can fetch it from the same pinned tag.

Tabler icons are drawn on a 24×24 grid with a 2px stroke and paint in `currentColor`. Tabler flags are drawn on a 30×24 canvas with plain filled paths. The two are not interchangeable: a flag is artwork with its own proportions and is not squeezed into the icon grid.



## Ratified Gnosix identity artwork

The PNG identity masters and the exact-fidelity SVG containers in `assets/identity/` are project artwork ratified for gnu.in.labs / Gnosix use in this design-system package. They are not third-party font files and must not be substituted with regenerated approximations inside the package.
