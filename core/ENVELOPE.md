# Envelope contract

The envelope is the shell: the material a surface is made of, the way that
material is arranged around the content, and the rules by which it settles.
It is not a theme and it is not a palette. The palette says what colour a
thing may be; the envelope says how a shell is put together.

This document records the envelope's invariants, where each of them now
lives in the contract, and what the field's own prototype proves of them.

## The invariants

The envelope was worked out in the field, in a composition lab whose two
outputs are a wide screen and a portrait one, each with its own motion
state, its own policies and its own epoch. The lab's own summary is the
head of this list: **compose → canonical boundary → single paint · stable
rebuild parity · zero transition primitives · ordered axes · isolated
epochs**.

Stated in full, the envelope holds eighteen obligations:

**Composition and paint.** Semantic regions are composed into one canonical
material boundary before anything is filled or stroked; the surface is
painted by one path and one owner. No independently stroked shell region,
no duplicate shell stroke, no transition lobe and no connector survives a
settled surface. A topology has one output-local material owner, and a
notification's growth thickens that same material field rather than
opening a second one.

**Curvature.** The curvature is one authority for the whole composition. A
region carries no radius of its own, a window's rounding is the shell's
rounding, and the exposed lower turns consume the same radius.

**Settling.** A settled surface is a canonical state rebuilt from the
composition, not the residue of an animation. Transition geometry is
parametric only and has no independently renderable primitive. A closed
surface's axes read zero; an open one's read one; a settled axis carries
no residue into the next, and one axis settles before the next begins.

**Occupancy and policy.** A surface's occupancy is stated — normal,
maximised, true fullscreen, floating overlap — and never inferred from
its dimensions. The workarea policy, the fullscreen response and the
overlap response are stated beside the topology and are never inferred
from it: the topology of a surface is not its behaviour. Each output
resolves its own policies.

**Isolation.** A configuration epoch isolates what a profile may not bleed
into another: private motion state does not cross an epoch. The semantic
session is shared; the motion state is per-output.

**Geometry.** A surface's geometry is finite. No non-finite value reaches
a path, an axis or a wave.

**Suppression.** A surface that a policy suppresses paints nothing, and no
boundary of it remains in the surface.

## Where they live

| Rule | Obligation |
|---|---|
| `SUR-002` | compose first, paint once: one canonical boundary, one path, one owner |
| `SUR-003` | the curvature is one authority for the whole composition |
| `SUR-004` | a settled surface is rebuilt from the canonical state, not from an animation |
| `SUR-005` | occupancy is stated, never inferred; each output resolves its own policy |
| `SUR-006` | a configuration epoch isolates what a profile may not bleed into another |
| `SUR-007` | the axes are ordered; a settled axis carries no residue |
| `SUR-008` | the topology of a surface is not its behaviour |
| `SUR-009` | a suppressed surface paints nothing |
| `SUR-010` | a surface's geometry is finite |

## What the prototype proves

The field's prototype applies **fifteen** of the eighteen as failures —
the gate refuses to pass when the axes are not finite, when a closed
surface is not canonical, when a transition primitive is still resident,
when a stable pose does not rebuild identically, when the painted boundary
is not exactly one, when a fullscreen output yields locally, or when two
outputs share one physical state.

**Six of the eighteen have no failure behind them.** The curvature's
global authority is displayed as a metric and never fails. The trigger's
internality is never checked. The policies' independence per output is
not checked — the *state* is per-output, the *policy* is not compared.
The topology's neutrality is never checked. The epoch's isolation is
displayed and never checked. The workarea's explicitness is displayed and
never checked. A surface that broke those six would look right, and pass.

The badge in the prototype reads `R2.5 · 21 CONTRACTS PASS`. The number is
a claim, not a count: the gate raises fifteen distinct failures, and the
other six are the statements above that nothing fails on. The system's
contract now carries all eighteen as rules, which does not make them
enforced. `DEV-014` in the severity register names the gap and its owner.

## What is owed

The system holds no composition engine, so it cannot prove these rules
about itself. The engine is in the field — in the GPUI launcher, which is
where the envelope runs. The launcher's absorption is therefore not a
paperwork exercise: it is where six of these rules must acquire a failure
behind them, and where the envelope's canonical composition is checked
against the contract rather than described by it.

The direction of travel is the one the contract already takes elsewhere:
the system specifies, the field implements, and the field proves. What is
missing here is the third step, for six rules.
