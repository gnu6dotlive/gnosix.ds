# gnosix.DS — upstream presentation intake

**2026-10-21 · research note**

`gnosix.DS` remains the portable semantic contract. Wayland, GPUI/Zed and Hyprland are projection targets or evidence sources, never authorities over the design system.

## Watch

### Workspace and surface identity

Track `ext-workspace-v1`, activation/presentation protocols and compositor-specific workspace/toplevel extensions. The useful unit is an exact semantic identity that can be mapped onto a target surface.

### GPUI / Zed

Watch display identity, window↔display association, visibility/suspension, IME and non-primary-output positioning. A change matters only when it changes an observable contract obligation or projection gate.

### Hyprland

Watch workspace sharing, toplevel mapping, focus grabs, input capture, pointer constraints and popup behavior. Hyprland-specific behavior must remain an enrichment rather than a hidden portability requirement.

## Evaluation rule

For each material upstream change:

1. pin the exact upstream revision;
2. identify the affected semantic rule/component;
3. distinguish source support from runtime evidence;
4. update a projection only when a gate or contract obligation changes;
5. record negative/non-impact results as deliberately as positive results.

## Non-goals

No toolkit is promoted to design-system authority. No compositor-specific API is silently made portable. No visual reference is treated as semantic evidence without a measurable contract or gate.
