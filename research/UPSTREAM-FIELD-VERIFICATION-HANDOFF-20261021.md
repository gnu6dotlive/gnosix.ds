# The field-side verification gate — a handoff, not a record

**2026-10-21 · handoff · gnosix.ds**

This document states work to be done in another repository, under another
authorisation. It states **no pin, no observation and no upstream state**:
those live in `core/UPSTREAM.json`, which is the single source of truth for
what the system's projections and the field's evidence are qualified
against. This document says what a gate must do so that the pins this
repository can only *reference* become pins the field can *verify*.

Nothing here changes the design-system contract, and nothing here adopts an
upstream.

---

## 1. Why the gap exists

The contract's register of upstream holds pins for the field's compositor,
the field's Wayland protocols and the field's vendored toolkit. Three of
the four are recorded as **referenced**: the contract names the exact
identity, and the field's own repository records it, but *this* repository
cannot check that the field is using the revision it names. A green gate
here proves the record is well formed; it proves nothing about the field's
machine.

The gap is deliberate and it is not closable from here: the contract
repository cannot guarantee that a different repository is using the
revision it writes down. Closing it means a gate in the field.

## 2. Scope of the future work

**Repository:** `tension-atoi/gnosix` (the field).
**Authorisation required:** a separate operator decision for that
repository. This handoff is a specification, not an authorisation.
**Out of scope:** the design-system contract, its tokens, its rules, its
projections, and any upstream adoption.

## 3. What the gate must do

The gate lives in the field, compares the identities the field *declares*
against the identities the field *has*, and reports.

### 3.1 Required inputs

| input | where it comes from | what is compared |
|---|---|---|
| the declared compositor identity | the field's own record of the compositor it qualifies against | the identity `hyprctl version` reports on the host: the version, the tag and the build commit |
| the declared toolkit identity | the field's vendored `gpui-pre-linux` manifest and the workspace patch note | the `gpui_linux` upstream revision the vendored snapshot names, and the crate version |
| the declared protocol identity | the field's host package record | the `wayland-protocols` and `libwayland` versions the host carries |
| the contract's expectation | `core/UPSTREAM.json` in `tension-atoi/gnosix.ds`, read-only, at the revision the field declares | the exact identity the contract records for each rail |

The contract's register is an *input*, never a source to write to. The
field reports; the contract records.

### 3.2 The comparison

For each rail the field declares:

1. the declared identity and the observed identity are compared as
   **immutable identifiers** — a version, a commit, a digest — and never as
   a moving reference;
2. a match is reported as `verified`, with the identifiers that were
   compared and the digests of the evidence they were read from;
3. a difference is reported as `drift`, with both identities side by side;
4. a difference that is **not explained** is a failure, and the gate
   **fails closed**;
5. a difference that the field's own record explains (a vendored snapshot
   the field carries on purpose, with its reason) is reported as a known
   divergence, and it is still a drift: it is reported, not accepted.

### 3.3 What the gate must not claim

- It must not claim **runtime compatibility** from a source identity. A
  matching version says the source is the one that was declared; it says
  nothing about what the compositor did with it.
- It must not claim **product-level qualification**. The levels stay
  apart: semantic, declared, source, observed, installed. A source
  comparison is a *source* result.
- It must not **adopt** an upstream, and it must not update the contract's
  register.

### 3.4 The result it emits

A provenance-bearing result: for every rail, the declared identity, the
observed identity, the verdict (`verified`, `known divergence`, `drift`),
the evidence that was read (paths and digests), the date, and the commit
of the field the result was produced from. The result is evidence, in the
field's own evidence discipline, and it is what a later contract-side
observation can cite — at the level it actually reaches.

## 4. Exit conditions

The field-side gate is done when:

- every rail the field declares is compared against an immutable identity;
- an unexplained difference fails the gate rather than passing it;
- the result names the evidence it read, with digests;
- the result states its level and claims nothing above it;
- the field's own qualification runs the gate, and the result is kept as
  evidence;
- the contract's register can then move a pin from `referenced` to
  `verified` **by a separate, recorded decision** that cites the field's
  result — never by the field's gate editing the contract.

## 5. What remains undecided

- Which claims of the field depend on the layer-shell axis (the scope
  question raised by `UP-001`) is a field-side question: the field's
  evidence ledger does not say which of its claims depend on the resize
  path. Until it does, `UP-001`'s scope is stated as the contract can
  state it, and no more.
- The behavioural evaluation of the two layer-shell implementations — the
  smallest falsifiable experiment in `UP-001` — is authorised nowhere yet.
  The contract does not need it to remain the contract; the field's
  qualifications may.
