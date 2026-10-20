# Visual contract

This document defines portable visual relationships. `TOKENS.json` alone defines exact approved colors and font names; fixture and sample dimensions are local examples.

## Color and type

Anthracite and Shell White carry most structure. Signal Orange communicates directional action and energy, Beret Green stable identity and calm confirmation, and Royal Blue identity plus a declared cool/signed endpoint where appropriate. Semantic alert/warn remain operational colors. A gradient is permitted for a declared quantity or material light response, never a generic brand wash. White normal essential text on Signal Orange fails the approved contrast pairing; use Anthracite on Signal Orange. Do not rely on color alone.

Space Grotesk is the single visual/interface family for display, paragraphs, navigation, controls, metadata, evidence labels and technical strings. Technical text is differentiated with weight, tracking and tabular numerals rather than a second interface typeface. **Ratified identity artwork is exempt from this typography rule:** the terminal symbols inside the three accepted cube masters are image content, not live UI text and must not be reconstructed from Space Grotesk. Keep French accents and symbol glyphs legible in actual interface text. A target may use a documented system fallback only when the packaged Space Grotesk asset cannot be loaded. No universal size, tracking or weight ladder is currently ratified; the shared weights in `TOKENS.json` define available emphasis, while fixture typography sizes remain local until explicitly promoted to tokens.

## Surfaces

The composition vocabulary is geometry/visible hull, material, chrome, depth/light response, content, interaction/focus and motion. An Envelope can connect compact and expanded shell-like surfaces but is not obligatory for every application page. `paint`, `input`, and `allocation` regions have distinct meanings even when they happen to overlap.

Material families: matte anthracite; Orange, Green or Blue painted metal; brushed or dark anodized aluminum; warm paper; smoked plastic. Material describes light/texture/opacity/substrate response, not component identity. Depth may express contact, lift, recess, inset, rim and shallow bevel. Keep light direction coherent; do not turn every section into a floating card. Chrome includes borders, separators, focus frames, state pips and selection outlines. A material change does not change a surface's semantic role.

## Responsive and motion

Preserve reading order, action priority, essential state labels and accessible names as space or text scale changes. A fixture viewport tests one condition, not a universal breakpoint. Motion reveals causality, remains interruptible when state changes, and preserves meaning with reduced motion. There is no approved global duration ladder or global theme pair.

V3.4.0 ratified the *meaning* of motion in `profiles/motion/` — causality, performance, continuity, interruptibility, reduced-motion equivalence, and stillness-before-climax — together with the seams and motion roles that follow from them. That release deliberately did **not** ratify a global duration ladder. Each target declares its own ladder in its own units, and `MOT-BAN-TOKEN-LADDER` prohibits promoting one into `TOKENS.json`. The Remotion target's frame counts are that target's business, exactly as a fixture's pixel dimensions are its own.
