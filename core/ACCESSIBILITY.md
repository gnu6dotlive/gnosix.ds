# Accessibility and conformance

WCAG 2.2 AA is the Web baseline where applicable. Native profiles must translate its relevant outcomes into their own accessibility APIs and tests. This file sets outcomes; each profile names its implementation and evidence.

1. Identify an interactive control by role, name, current state and focus without relying on hue alone.
2. Preserve readable text at 200% Web zoom and at platform enlarged-text settings without hiding actions or reversing reading order.
3. Verify actual text/substrate contrast. The existing pairing rule forbids white normal essential text on Signal Orange; validation of other pairings depends on their actual size and use.
4. Distinguish pending, success, rejection and unknown in text and accessible state. Success cannot be inferred from a request.
5. Honor reduced motion while retaining state meaning. Inspect target-size rules in each platform's own logical units; CSS px and Android dp are not interchangeable.
6. Record exceptions per fixture with the target, measured behavior and reason. A screenshot alone does not prove keyboard, touch or screen-reader behavior.
7. An icon that carries meaning needs an accessible name; an icon that repeats adjacent text is decorative and must be hidden from assistive technology. The ratified glyphs paint in `currentColor` and scale with their type, so they do not change a control's hit target, but they also do not carry a name on their own. A control whose only label is an icon needs `aria-label` or a visually hidden text equivalent.

Conformance for a profile requires exact approved tokens/assets, semantic and state parity, applicable accessible behavior, and evidence for all six fixture families. Statuses are `specified`, `mapped`, `rendered`, and `verified`. `mapped` describes documentation/code mapping; `rendered` requires a real target capture; `verified` additionally requires recorded functional/accessibility checks. These claims are target- and version-scoped.
