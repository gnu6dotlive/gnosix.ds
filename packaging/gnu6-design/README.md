# gnu6-design

The package a gnu6 surface vendors. One sheet, one vocabulary, and a
lock that says which state of the design system it was cut from.

## What it is

`gnu6.css` carries the **field's component vocabulary** — the `g6-*`
classes that every gnu6 surface already uses — bound to the **design
system's own names**. It is the same sheet that three repositories
vendored as `gnu6-design 1.1.1`, re-cut from the current contract.

## Why it is re-cut here

The 1.1.1 sheet was cut from `Gnosix-DS-V3.4.1` and then frozen. It
carried the layer ids in their pre-kebab spelling — `--gnosix-signalOrange-base`
where the system publishes `--gnosix-signal-orange-base` — and a quarter of
the published names. The generator that produced it is gone, and the only
surviving forms of it were three byte-identical vendored copies, each with
its own lock. Every value was right; only the spelling had drifted, which
is the one kind of drift nobody can see by looking at a colour.

So the package is cut here, by `tools/package_gnu6_design.py`, from
`core/`:

- the **vocabulary** of the field stays — the components every consumer
  already uses, and the set the system's own components map onto;
- every **`--gnosix-*` name** is rebound to the name the system publishes,
  by rule `NAM-001`;
- the system's **own vocabulary** is added: the colours the sheet omits,
  the surfaces, the weights, the spacing scale.

The sheet is the only file in the package. The fonts, the icons and the
identity masters are the consumer's own: the package is the shared
vocabulary, and a surface brings its own face.

## Using it

```html
<link rel="stylesheet" href="/gnu6/gnu6.css">
```

The lock says what it is:

```json
{ "package": "gnu6-design", "version": "4.0.0", "files": { "gnu6.css": "…" } }
```

A consumer vendors the sheet and keeps the lock beside it. When the
system moves, the package is re-cut here, the lock changes, and the
consumer re-vendors — one change, three consumers, instead of three
migrations.

## What is not in here

The system's own component stylesheet. It carries an icon import and a
font face that resolve inside the system and not inside a consumer, so a
consumer adopts it from the system's own web profile, pinned and locked,
rather than from this package.
