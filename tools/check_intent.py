#!/usr/bin/env python3
"""Check that the register of what the owner stated is honest.

A rule is the system's own statement. The register of intent is the owner's:
what he wants reached, what must never stop being true, what is true now,
and what exists. They are kept apart because they are not the same kind of
thing, and a register that mixes them cannot say what it knows.

So the shape is checked — every statement has an identifier, a kind, a
what, a provenance and a state — and then the substance is checked against
the contract:

  a goal says what reaching it looks like;
  an invariant says what holds it, and a gate that holds it is a gate that
  exists;
  a truth names the evidence, and the evidence is a file in this
  repository, so a truth that stops being true fails here;
  a capability says where, and where exists;
  a statement the owner has not yet carried into a release is recorded as
  stated, and says the day it was said.

    python3 tools/check_intent.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import ci  # noqa: E402

REGISTER = ROOT / "core" / "INTENT.json"
MANIFEST = ROOT / "manifest.json"

KINDS = {"goal", "invariant", "truth", "capability"}
PREFIX = {"goal": "GOAL", "invariant": "INV", "truth": "TRU", "capability": "CAP"}
STATES = {"stated", "ratified"}
IDENTIFIER = re.compile(r"^(GOAL|INV|TRU|CAP)-\d{3}$")


def published(root: Path = ROOT) -> set[str]:
    """The paths the published contract holds.

    The manifest is the authority for what the contract publishes, and a
    copy of the package is a copy of the manifest. A capability that lives
    outside the published contract cannot be consulted by anyone who holds
    the contract, so the register says where the thing is *in the
    contract*.
    """
    manifest = root / "manifest.json"
    if not manifest.is_file():
        return set()
    document = json.loads(manifest.read_text(encoding="utf-8"))
    files = document.get("files", document)
    if isinstance(files, dict):
        files = files.get("files", [])
    return {entry.get("path", "") for entry in files if isinstance(entry, dict)}


def problems(register: dict, root: Path = ROOT, gate_labels: set[str] | None = None) -> list[str]:
    """What is wrong with the register, and with what it says about the contract."""
    found: list[str] = []
    gate_labels = gate_labels if gate_labels is not None else {label for label, _ in ci.GATES}
    seen: set[str] = set()

    for statement in register.get("statements", []):
        identifier = statement.get("id", "")
        if not IDENTIFIER.match(identifier):
            found.append(f"{identifier or 'a statement'} has no identifier of the shape KIND-NNN")
            continue
        if identifier in seen:
            found.append(f"{identifier} is in the register twice")
        seen.add(identifier)

        kind = statement.get("kind")
        if kind not in KINDS:
            found.append(f"{identifier} is a {kind!r}, which is not a kind the register knows")
            continue
        if not identifier.startswith(PREFIX[kind] + "-"):
            found.append(f"{identifier} is a {kind} and does not carry that kind's prefix")

        if not statement.get("what"):
            found.append(f"{identifier} does not say what it is")
        if not statement.get("provenance"):
            found.append(f"{identifier} does not say where it came from")

        state = statement.get("state")
        if state not in STATES:
            found.append(f"{identifier} is {state!r}, which is not a state the register knows")
        elif state == "stated":
            if not statement.get("stated_on"):
                found.append(f"{identifier} is stated but does not say the day it was said")
        elif not statement.get("carried_in"):
            found.append(f"{identifier} is ratified but does not say the version that carries it")

        if kind == "goal" and not statement.get("done_when"):
            found.append(f"{identifier} is a goal and does not say what reaching it looks like")

        if kind == "invariant":
            held_by = statement.get("held_by")
            if not held_by:
                found.append(f"{identifier} is an invariant and does not say what holds it")
            else:
                # The holder may be a gate of this repository, or a practice
                # of the field that the contract can point at but not check.
                for label in gate_labels:
                    if label in held_by:
                        break
                else:
                    if not held_by.startswith("the field") and "tools/" not in held_by \
                            and "ci/" not in held_by:
                        found.append(f"{identifier} is held by {held_by!r}, which is neither a gate "
                                     f"of this repository nor a practice of the field")

        if kind == "truth":
            evidence = statement.get("evidence")
            if not evidence:
                found.append(f"{identifier} is a truth and does not name its evidence")
            else:
                # The evidence may name a place in a document: the file is
                # the first word, the rest is where in it.
                path = evidence.split()[0]
                if not (root / path).exists():
                    found.append(f"{identifier} names {evidence} as its evidence, which is not in "
                                 f"the repository")

        if kind == "capability":
            where = statement.get("where")
            if not where:
                found.append(f"{identifier} is a capability and does not say where it is")
            elif statement.get("published") is False:
                # It does not travel with the contract, so a copy of the
                # package may not hold it. What it must not do is claim to.
                if any(path.startswith(where.rstrip("/") + "/") or path == where
                       for path in published(root)):
                    found.append(f"{identifier} says it does not travel, and the published contract "
                                 f"holds it")
            elif not (root / where).exists():
                found.append(f"{identifier} says it is in {where}, which is not in the repository")
            elif statement.get("published") is not False:
                # A capability that travels is one anyone holding the
                # contract can consult. A capability that says it does not
                # travel is in the repository only, and says so.
                if not any(path.startswith(where.rstrip("/") + "/") or path == where
                           for path in published(root)):
                    found.append(f"{identifier} says it is in {where}, which the published contract "
                                 f"does not hold — say so, or point at what travels")

    return found


def main() -> int:
    if not REGISTER.is_file():
        print("FAIL: core/INTENT.json does not exist")
        return 1
    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    found = problems(register)
    if found:
        print(f"FAIL: {len(found)} problem(s) with the register of intent")
        for problem in found:
            print(f"  - {problem}")
        return 1
    statements = register.get("statements", [])
    tally: dict[str, int] = {}
    for statement in statements:
        tally[statement["kind"]] = tally.get(statement["kind"], 0) + 1
    stated = sum(1 for s in statements if s.get("state") == "stated")
    print(f"PASS: the register of intent holds ({len(statements)} statements: "
          + ", ".join(f"{count} {kind}" for kind, count in sorted(tally.items()))
          + f"; {stated} stated and not yet carried into a release)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
