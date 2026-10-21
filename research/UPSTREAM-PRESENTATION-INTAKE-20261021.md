# gnosix.DS — upstream presentation intake

**2026-10-21 · research note**

`gnosix.DS` remains the portable semantic contract. Wayland, GPUI/Zed and Hyprland are projection targets or evidence sources, never authorities over the design system.

This note says how an upstream change is evaluated. The evaluations
themselves are recorded in `core/UPSTREAM.json` — the registry — and the
checker `tools/check_upstream.py` holds the registry to what this note
says. The note states no pin and no observation of its own: there is one
source of truth for upstream state, and it is the registry.

## Watch

### Workspace and surface identity

Track `ext-workspace-v1`, activation/presentation protocols and compositor-specific workspace/toplevel extensions. The useful unit is an exact semantic identity that can be mapped onto a target surface.

### GPUI / Zed

Watch display identity, window↔display association, visibility/suspension, IME and non-primary-output positioning. A change matters only when it changes an observable contract obligation or projection gate.

### Hyprland

Watch workspace sharing, toplevel mapping, focus grabs, input capture, pointer constraints and popup behavior. Hyprland-specific behavior must remain an enrichment rather than a hidden portability requirement.

### The design engine

Watch the engine the board is projected through, and the fonts the projection is laid out with. A change in the projection of the tokens, of the board, or of the rendered bytes is material.

These four are the **rails** of the registry: what is watched, and what
would make a change material on each.

## The pin

A pin is not a name in a file. A pinned implementation is not qualified
because a version string appears somewhere; it is qualified against an
identity that cannot move, and the record says so.

Every pin in the registry distinguishes:

1. **Exact identity** — a version, a commit, a digest, or another immutable
   identifier. `main`, `latest` and `head` are not identities, and the
   checker rejects them.
2. **Pin authority** — the repository that owns and records the pin.
3. **Verification status** — `verified` when *this* repository checks the
   pin against the source or artefact it names; `referenced` or `declared`
   when it cannot. A pin that claims to be verified while living in another
   repository is a failure, and an exact reference that cannot be checked
   automatically is labelled as one. `referenced` is never silently
   promoted to `verified`.
4. **Qualification scope** — what behaviour was actually tested against that
   exact revision.
5. **Known divergence** — the relevant differences from upstream.
6. **Refresh condition** — the material change that would justify moving
   the pin.

A new upstream release does not automatically require adoption. A pin moves
only through a deliberate review that records the old and the new identity,
the material reason, the observations and contract elements affected, and
the qualification work the move requires.

## The observation

An observation is a change that was measured. It records:

- the exact upstream identity and the source it was read at;
- the affected rail and the contract elements it bears on;
- **the observed fact and the inference drawn from it, kept apart**;
- the local evidence and **the limits of that evidence**;
- the **level** the evidence reaches;
- whether a projection changes;
- the gate that holds the answer, or the reason no gate applies;
- the smallest falsifiable next experiment;
- the decision owner and the present disposition;
- **the scope**: which claims depend on the affected behaviour, and which
  remain unaffected.

## What is material

An upstream event is material when it:

1. changes or contradicts a contract guarantee;
2. invalidates evidence tied to a pinned implementation;
3. changes a primitive's observable behaviour relevant to geometry,
   identity, focus, surface lifetime, accessibility or presentation;
4. creates a reproducible regression or closes a known limitation;
5. unlocks a bounded experiment that could change an existing decision.

The watch is not a changelog. An event that touches no known invariant, pin,
qualification or research question opens no implementation task.

## The levels

A record at one level is not a record at the next, and a green gate at one
level says nothing at the next:

| level | what it is |
|---|---|
| semantic | what a role or a rule means |
| declared | what an implementation says it can do |
| source | a qualification of the source |
| observed | behaviour seen against an exact revision |
| installed | a product-level qualification on a real machine |

No upstream pin, source observation or green checker may be used to imply a
broader qualification than the evidence supports.

## The evaluation rule

For each material upstream change:

1. pin the exact upstream revision;
2. identify the affected semantic rule/component;
3. distinguish source support from runtime evidence;
4. update a projection only when a gate or contract obligation changes;
5. record negative/non-impact results as deliberately as positive results.

## What this does not do

This intake is an evidence and change-control mechanism. It does not ratify
upstream adoption, alter the design-system contract, or promote a product
capability. It does not change the field's behaviour, and it does not
change the contract to accommodate the field's implementation. A negative
result is recorded as carefully as a positive one, and neither is a verdict
on which implementation is right.

The gap this repository cannot close — the field verifying its own pins — is
specified in `research/UPSTREAM-FIELD-VERIFICATION-HANDOFF-20261021.md`,
which needs a separate authorisation for the field's repository.

## Non-goals

No toolkit is promoted to design-system authority. No compositor-specific API is silently made portable. No visual reference is treated as semantic evidence without a measurable contract or gate.
