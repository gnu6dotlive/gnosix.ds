# Third-party notices

This package redistributes third-party assets. Their licences are reproduced
verbatim in the package, and their provenance is recorded per file in
[`assets/LICENSES.md`](assets/LICENSES.md). The table here is a summary; the
files themselves are the authority.

| Asset | Version | Licence | Verbatim text |
|---|---|---|---|
| Space Grotesk (variable WOFF2, native TTF) | — | SIL Open Font License 1.1 | `assets/fonts/SpaceGrotesk-OFL.txt` |
| Tabler Icons (outline subset, 41 icons) | 3.49.0 | MIT, © 2018-2026 Paweł Kuna | `assets/icons/licenses/Tabler-Icons-LICENSE.txt` |
| Tabler Flags (subset, 8 flags) | 0.1.1 | MIT, © 2018-2026 Paweł Kuna | `assets/icons/licenses/Tabler-Flags-LICENSE.txt` |

## Referenced, not redistributed

The eye renders the system's own surfaces and looks at them. It needs a
browser and an accessibility engine, and neither is redistributed here:
they are installed from a lockfile that pins their versions, and they
run only where a browser is provisioned. The licences are the upstream
ones.

| Dependency | Version | Licence | Where |
|---|---|---|---|
| Playwright (browser automation) | 1.61.1 | Apache-2.0 | `qa/eye/package.json` |
| @axe-core/playwright (accessibility rules) | 4.12.1 | MPL-2.0 | `qa/eye/package.json` |
| axe-core (the rules themselves) | 4.12.1 | MPL-2.0 | a dependency of the above |

## What is not third-party

The identity masters in `assets/identity/`, the mascot references in
`assets/mascot/`, the reference sheets in `references/`, the visual evidence
boards in `references/visual-evidence/`, the site in `site/` and every line of
code and prose in this repository are project-owned work of the gnosix
project, distributed under the MIT licence in [`LICENSE`](LICENSE).

The SVG wrappers around the identity masters are exact-fidelity containers
that embed the PNG payload and the packaged Space Grotesk WOFF2. They are
containers, not vector-native reconstructions, and they carry the OFL terms
of the font they embed.

## Vendored, not referenced

The icon and flag subsets are vendored at a pinned upstream tag rather than
loaded from a CDN, and the font is vendored rather than fetched. A design
contract whose appearance changes when a third party publishes is not a
contract. Each vendored file's SHA-256 is recorded in
`assets/icons/icon-manifest.json` and asserted by the test suite;
`tools/vendor_icons.py --fetch` regenerates the subset and `--check` verifies
it without touching the network.

The upstream sets are much larger than this package ships: 6238 icons and 304
flags upstream, 41 and 8 here. A consumer needing a glyph this package does
not vendor can fetch it from the same pinned tag.
