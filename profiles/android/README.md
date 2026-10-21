# Android / Compose mapping

This profile maps the portable gnosix contract to Compose semantics. Colors come only from generated `GnosixColors.kt`. V3.4.1 packages `SpaceGrotesk-native.ttf` as `res/font/space_grotesk.ttf`; `GnosixType.primary` resolves to that family; `GnosixType.technical` resolves to **IBM Plex Mono**, packaged as `res/font/ibm_plex_mono.ttf`, because TYP-002 opens the technical text to the technical family.

The sample pins AGP 9.1.1, Compose compiler plugin 2.2.10 and BOM 2026.09.00. Compatibility and build output remain **unverified in this environment**: the presence of a native font asset closes the previous font-asset gap, but it does not prove Android rendering. Install a compatible Android SDK and Gradle, then run `gradle :app:assembleDebug :app:testDebugUnitTest` in `sample/` and capture a real render before promoting the profile to `rendered`.

## Role mapping

| Portable role/layer | Compose mapping | Evidence gate |
|---|---|---|
| primary typography | `FontFamily(Font(R.font.space_grotesk))` | rendered family + glyph coverage |
| primary action | `Button`, Signal Orange container, Anthracite label, 48 dp minimum target in this fixture | touch + focus/keyboard test on target device |
| status | `Text` plus `stateDescription`; optional adjacent pip rather than a status chip | TalkBack/state text check |
| request/observation | `StateProjection.kt` keeps requested separate from observed | pending-before-observed test |
| surface layers | layout/shape, paint/brush, border/focus, depth/draw layer and hit target stay separable | rendered surface comparison |
| scalar field | canvas/brush is presentation; legend/range/missing state remain semantic content | missing-state + TalkBack/legend inspection |
| adaptation | scrollable composition and `sp` text preserve reading order | font-scale and rotation checks |

The example uses textual identity descriptions rather than pretending SVG art is rendered natively. No animation is introduced. Verify focus, TalkBack, scaled text, and screenshot appearance on a device before changing status to `rendered` or `verified`. Requested connection remains pending until an external observation updates `observed`.

Reference IDs: `identity`, `actions`, `state`, `surfaces`, `fields`, `adaptive`. Fixture dimensions do not define global typography, spacing or shape values.
