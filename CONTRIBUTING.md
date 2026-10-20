# Contributing

gnosix_DS is a portable design contract: rules, tokens, reference scenes and
explicit platform mappings. Contributions should preserve the project's
authority and evidence boundaries rather than treating it as a conventional
theme or a set of mockups.

## Before changing anything

Read [`README.md`](README.md) for what the package is and what it claims, and
[`core/IDENTITY.md`](core/IDENTITY.md) and [`core/MAPPING.md`](core/MAPPING.md)
for the boundaries that cannot move. The fifteen rules in `core/rules.json`
are the contract; a change that breaks one is a change to the contract, and
that is a deliberate act, not a side effect.

## Local checks

```sh
python3 -m pip install -r requirements.txt
python3 -m tools.ci
```

`python3 -m tools.ci` is the repository-owned qualification contract invoked
by GitHub CI. Run it locally before opening a change that should be
publication-ready. The list of gates lives in `tools/ci.py`, in the
repository: the same command a developer and an agent run, so local truth and
CI truth cannot drift apart.

Individual gates can be run on their own, and every one of them is
read-only under `--check`:

```sh
python3 -m tools.ci --only version
python3 -m tools.version --check
```

## The version

Do not hand-edit a version string. `VERSION` is the source and every other
place the version appears is a slot that `tools/version.py` keeps in step.
If you change the version, change it here:

```sh
python3 -m tools.version --set 3.4.3
```

and then rebuild the manifest, because the manifest hashes the version file:

```sh
python3 -m tools.rebuild_manifest
```

`python3 -m tools.version --check` fails the build if any slot disagrees, if
a slot has disappeared, or if the tagged commit and the version file tell
different stories. Prose that names a past release is history, not a slot:
a bump leaves it alone, and the test suite asserts that it does.

## Evidence

Tests and receipts should state exactly what they prove and what they do not
prove. Prefer deterministic source tests for invariants, runtime evidence for
runtime behavior, and explicit operator review for human/perceptual gates.
The `qa/QA.md` file is the record of what a release actually fixed; a change
that repairs a defect belongs there.

Raw logs are not a substitute for a bounded claim. Link the smallest evidence
set that supports the claim.

## Assets

Third-party material is vendored at a pinned upstream tag, never fetched from
a CDN, and every vendored file's SHA-256 is recorded and asserted. When you
add or update a vendored asset, update `assets/icons/icon-manifest.json` and
`assets/LICENSES.md` in the same commit, and update
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) when importing new
third-party material.

Project artwork — the identity masters, the mascot references, the reference
sheets, the site — is not to be replaced with a regenerated approximation.
`ID-003` prohibits redrawing a ratified master.

## Changes and commits

Keep commits coherent and reviewable. Preserve unrelated work and byte-exact
provenance. Do not rewrite upstream/vendor patches or historical evidence to
satisfy cosmetic formatting rules.

AI-assisted changes are acceptable when their source, review boundary, tests
and evidence remain inspectable. Generated text or code does not receive
special authority merely because a model produced it.

## Licensing

First-party contributions are submitted for inclusion under the **MIT
License** (see [LICENSE](LICENSE)). Contributors must have the necessary
rights to license their work under MIT; do not copy GPL-only third-party code
into MIT-designated first-party files. Retain third-party notices and update
`THIRD_PARTY_NOTICES.md` when importing third-party material.
