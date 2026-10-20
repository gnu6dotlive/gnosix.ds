# Motion profile

V3.4.0 adds a motion profile. Before this release the package carried `MOT-001` as a
single accessibility rule and three sentences in `profiles/projection-map.json`, while
`core/VISUAL.md` explicitly declined to ratify a duration ladder. A consumer building
anything time-based therefore had no authority to build against.

This profile supplies that authority, and it splits it in two.

## What is portable

`motion.json` → `portable` is authoritative and travels to every target:

- **Six laws.** Causality, performance, continuity, interruptibility, reduced-motion
  equivalence, and stillness-before-climax. Each carries its own test.
- **Four prohibitions.** No idle wobble. No motion applied to a ratified identity master.
  No state meaning carried by animation alone. No promoting a target's duration ladder
  into `core/TOKENS.json`.
- **Seven motion roles.** Each names what it means, whether it may be interrupted, and
  what it becomes when motion is reduced. `state-pending` is explicitly *not* success.
- **Seven seams.** Five velocity-matched cuts plus `rack-focus`, and two in-scene
  patterns, `waterfall-entry` and `nudge-curve`.

## What is target-local

`motion.json` → `targets` is expression, not meaning. The Remotion block declares a
ladder in **frames at 60fps**, an easing vocabulary, a velocity-match travel fraction,
and a blur scale. These are the Remotion project's numbers.

They are not tokens. They are not a global duration ladder, and
`profiles/motion/motion.json` carries a prohibition (`MOT-BAN-TOKEN-LADDER`) aimed at
exactly the mistake of promoting them. This mirrors the existing position that fixture
viewports are not breakpoints and fixture dimensions are not global tokens: a target may
have its own numbers, and those numbers do not become the contract.

## Why identity motion is prohibited outright

`MOT-BAN-IDENTITY-MOTION` is the strictest entry here and it is deliberate. A ratified
cube is authored artwork with a specific dark-face assignment and material response.
Rotating it in 3D or re-lighting it changes the artwork, which `ID-003` already forbids.

The motion profile does not grant an exception. It states the consequence in motion
terms: **a mark is a still thing, and the frame moves around it.** Depth comes from
camera, staging, cast shadow on the substrate, and the chrome around the mark — never
from transforming the mark. Consumers that want a cube to feel dimensional must move the
camera, not the cube.

## Reduced motion is an input, not a media query

`MOT-001` requires honouring reduced motion. In a headless renderer the
`prefers-reduced-motion` media query reports the **render machine's** setting, not the
viewer's, so a CSS-only implementation silently does nothing in the one place evidence
would be produced. `targets.remotion.reduced_motion.detection` therefore requires reduced
motion to be exposed as an explicit input as well, and `reduced_motion_equivalent` is
declared per role so the reduced path is specified rather than improvised per component.

## Status

`mapped`. The portable contract exists, and one target — Remotion — now implements it.
`gnosix-remotion/src/motion/` binds the laws, prohibitions, roles and seams, and consumes the
target ladder from the generated projection rather than restating it. Both films render every
seam and every rule beat, and the QA reel is generated from the rule table, so a rule added to
`core/rules.json` produces a beat without anyone editing a composition.

It is not claimed as `rendered`. Rendered motion sequences exist in the target repository but
have not been ingested here as DS-scoped evidence, and the evidence ladder is explicit that
`rendered` means a real target capture recorded against *this* claim.
