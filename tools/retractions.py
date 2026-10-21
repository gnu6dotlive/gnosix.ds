#!/usr/bin/env python3
"""Read the register of what has been disqualified.

A retraction is not a deletion. The contract keeps every element it has ever
published, so a correction can be read afterwards: what the element was,
which version carried it, when it was retracted, and why.

This module is where that register is read. Everything else in the system —
the role projection, the gate that checks the register, the consumer gate
that tells a consumer it is standing on something withdrawn — reads it
through here, so there is one place that says what a retraction is.

    python3 tools/retractions.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "core" / "RETRACTIONS.json"

# The kinds of thing the contract can withdraw. An element is a thing the
# contract publishes with a name; a behaviour is a thing the contract does.
ELEMENT_KINDS = ("role", "token", "rule", "component", "scheme", "state")
KINDS = ("element", "behaviour")


def load() -> dict:
    """The register, as it is on disk."""
    return json.loads(REGISTER.read_text(encoding="utf-8"))


def entries(register: dict | None = None) -> list[dict]:
    """Every retraction, in the order the register holds them."""
    register = register if register is not None else load()
    return list(register.get("retractions", []))


def marked(register: dict | None = None) -> dict[str, dict]:
    """The elements that carry a mark, by the name they are marked under.

    The key is the kind and the name, joined: `role:accent`. A behaviour has
    no place in the contract to be marked, so it is not here — it lives in
    the register alone.
    """
    register = register if register is not None else load()
    found: dict[str, dict] = {}
    for entry in entries(register):
        if entry.get("kind") != "element":
            continue
        found[f"{entry.get('element_kind')}:{entry.get('element')}"] = entry
    return found


def mark_of(contract_element: dict, register: dict | None = None) -> str | None:
    """The retraction a contract element carries, if it carries one."""
    value = contract_element.get("retracted")
    if not value:
        return None
    register = register if register is not None else load()
    for entry in entries(register):
        if entry.get("id") == value:
            return value
    return value


def note(entry: dict) -> str:
    """The one line a projection carries for a retracted element."""
    return (f"RETRACTED by {entry.get('id', 'an unknown retraction')}: "
            f"{entry.get('what', 'no reason recorded')}")


def main() -> int:
    register = load()
    rows = entries(register)
    if not rows:
        print("PASS: nothing is retracted")
        return 0
    for entry in rows:
        print(f"{entry.get('id', '?')}: {entry.get('what', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
