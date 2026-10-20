# Web profile

This profile maps the portable gnosix contract to semantic HTML, generated CSS tokens and accessible interaction. It applies to vanilla Web, React, Vue or Svelte consumers; no framework owns the visual identity.

## Consume it

1. Import `components.css`; it imports generated `tokens.css` and the packaged Space Grotesk WOFF2. V3.4.1 uses Space Grotesk for body, navigation, controls, metadata, `code` and technical labels as well as display type.
2. Draw interface glyphs from the ratified Tabler subset. `icons.css` is imported by `components.css` and gives `.gnosix-icon`; reference the vendored sprite at `assets/icons/sprite.svg`. Do not hand-author an SVG glyph or substitute a text character for an icon — `ICON-001` governs this.
3. Use native `button`, `label`, `input` and status text. Add the `gnosix-*` classes to the corresponding roles. The pure `projectState` function does not turn a request into a successful observation.
4. Keep surface layers independent: layout/clip is geometry; background/gradient is material; border/focus is chrome; shadow/recess is depth; DOM content and hit regions retain their own semantics.
5. A scalar-field renderer may use CSS/SVG/canvas, but quantity, range, neutral point, missing state and legend remain inspectable content outside the paint operation.
6. `demo.html` is a local simulation. In an application, `observed` must come from the actual authoritative source. `ReactExample.tsx` is an integration example, not a separately verified React build.
7. Test keyboard focus, color contrast in context, 200% zoom, enlarged text, font load/fallback, screen-reader names, reduced motion and all six reference scenes. CSS px values in the sample are local control decisions, not global design-system tokens.

## Status

Read `status.json`, `profiles/projection-map.json` and `qa/QA.md` for current evidence. A reference HTML view, a browser capture and an application build are different claims. This profile does not assert that the gnosix shell runtime implements these visuals.
