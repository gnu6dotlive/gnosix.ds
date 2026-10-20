# Projection and mapping contract

V3.4.1 separates **portable meaning** from **target implementation**. A Web component, Compose control, GPUI element or video composition is never the source of truth for the design system. The source is the core role/rule/state vocabulary plus exact token and identity assets.

A mapping is complete enough to call `mapped` only when it answers four questions for every relevant role: **what semantic role is being projected, which core rules constrain it, how the target expresses it, and what evidence would promote the target from mapping to rendered/verified**. `profiles/projection-map.json` is the machine-readable matrix used by the public reference site.

## Mapping layers

| Portable layer | What must survive | Typical target responsibility |
|---|---|---|
| Identity | color family + anthracite face position + terminal glyph | load/paint the approved asset without merging identities |
| Typography | Space Grotesk across visible interface/reference text | load the packaged font; preserve weights/glyph coverage |
| Semantic role | action, prompt, evidence, focus, selection, status, field | choose an accessible native control/element and expose role/state |
| State model | intended ≠ observed ≠ projected | keep request intent separate from authoritative observation |
| Surface model | geometry, material, chrome, depth, content, hit region, allocation | keep render layers independently controllable |
| Adaptation | reading order, action priority, state labels, names | reflow without semantic reordering or hidden essential controls |
| Motion | causality, interruptibility, reduced-motion meaning | animate only after semantic state is defined |

## Evidence ladder

`specified` means the portable contract exists. `mapped` means a target translation exists in code/docs. `rendered` requires a real target render/capture. `verified` additionally requires target-scoped interaction/accessibility evidence. A profile never inherits maturity from another profile.

## Where a target's numbers live

A target expresses portable meaning in its own units, and those units are not portable. The web profile emits CSS custom properties; the Android sample emits Kotlin `Color` values; a motion target emits frame counts at its own frame rate. `MOT-BAN-TOKEN-LADDER` in `profiles/motion/motion.json` exists because a duration ladder is the easiest kind of target-local number to promote by accident — once six consumers agree on it, it starts behaving like a global token and the package can no longer say otherwise.

The discipline is the same one that keeps fixture dimensions out of `TOKENS.json`. Name the substrate, keep the numbers with the target, and let the portable layer carry only meaning.
