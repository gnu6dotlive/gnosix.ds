#!/usr/bin/env python3
"""Check that the register of retractions is honest.

The owner reserves the right to withdraw an element or a behaviour after it
has been published. That right is only safe if the contract can be corrected
without erasing the correction's own history, so the register of
retractions has to be as real as the register of deviations:

  every retraction names a thing, a version that carried it, a day it was
  withdrawn, who withdrew it, and why;
  every retraction of an element names something the contract still
  publishes, and that element carries the mark;
  every element that carries a mark has an entry, and no other;
  the mark has travelled: the projections a consumer reads carry it, so a
  consumer cannot pick up a withdrawn element without being told;
  and nothing withdrawn is presented as live: the contract's own samples
  do not stand on a retracted role.

    python3 tools/check_retractions.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import retractions  # noqa: E402

REGISTER = ROOT / "core" / "RETRACTIONS.json"
ROLES = ROOT / "core" / "ROLES.json"
RULES = ROOT / "core" / "rules.json"
TOKENS = ROOT / "core" / "TOKENS.json"
COMPONENTS = ROOT / "core" / "COMPONENTS.json"
SCHEMES = ROOT / "core" / "schemes.json"
VERSION = ROOT / "VERSION"

# The projections a consumer reads, and the mark each must carry.
PROJECTIONS = (
    ROOT / "profiles" / "web" / "roles.css",
    ROOT / "profiles" / "native" / "src" / "roles.rs",
    ROOT / "profiles" / "android" / "sample" / "app" / "src" / "main" / "java" / "labs"
    / "gnuin" / "gnosixds" / "GnosixRoles.kt",
)

REQUIRED = ("id", "kind", "what", "carried_in", "retracted_on", "by", "why")


def contract_elements() -> dict[str, dict]:
    """Every element the contract publishes, by the name it is marked under."""
    found: dict[str, dict] = {}

    roles = json.loads(ROLES.read_text(encoding="utf-8"))["roles"]
    for name, spec in roles.items():
        found[f"role:{name}"] = spec

    rules = json.loads(RULES.read_text(encoding="utf-8"))["rules"]
    for rule in rules:
        found[f"rule:{rule['id']}"] = rule

    components = json.loads(COMPONENTS.read_text(encoding="utf-8"))["components"]
    for name, spec in components.items():
        found[f"component:{name}"] = spec

    schemes = json.loads(SCHEMES.read_text(encoding="utf-8"))["schemes"]
    for scheme in schemes:
        found[f"scheme:{scheme['name']}"] = scheme

    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))["color"]
    for family, ramp in tokens.items():
        if not isinstance(ramp, dict):
            continue
        for shade, value in ramp.items():
            found[f"token:{family}/{shade}"] = {"value": value}

    return found


def problems(register: dict, elements: dict[str, dict],
             projections: tuple[Path, ...] = PROJECTIONS,
             root: Path = ROOT,
             schemes: list | None = None,
             components: dict | None = None) -> list[str]:
    """What is wrong with the register, the marks, and the projections."""
    found: list[str] = []
    seen: set[str] = set()

    for entry in retractions.entries(register):
        identifier = entry.get("id", "")
        if not identifier:
            found.append("a retraction has no identifier")
            continue
        if identifier in seen:
            found.append(f"{identifier} is in the register twice")
        seen.add(identifier)

        for field in REQUIRED:
            if not entry.get(field):
                found.append(f"{identifier} does not say {field}")

        kind = entry.get("kind")
        if kind not in retractions.KINDS:
            found.append(f"{identifier} is a {kind!r}, which is not a kind the register knows")
            continue

        if kind == "element":
            element_kind = entry.get("element_kind")
            if element_kind not in retractions.ELEMENT_KINDS:
                found.append(f"{identifier} withdraws a {element_kind!r}, which is not a kind of element")
                continue
            name = entry.get("element")
            key = f"{element_kind}:{name}"
            if key not in elements:
                found.append(f"{identifier} withdraws {key}, which the contract does not publish")
                continue
            carried = elements[key].get("retracted")
            if carried != identifier:
                found.append(f"{key} does not carry the mark of {identifier}"
                             + (f"; it carries {carried}" if carried else "; it carries no mark"))
        else:
            lives_in = entry.get("lives_in")
            if not lives_in:
                found.append(f"{identifier} withdraws a behaviour and does not say where it lives")
            elif not (root / lives_in).exists():
                found.append(f"{identifier} withdraws a behaviour in {lives_in}, which is not in the repository")

    # Every mark has an entry, and no other.
    for key, element in elements.items():
        carried = element.get("retracted")
        if not carried:
            continue
        if carried not in seen:
            found.append(f"{key} carries the mark {carried}, which the register does not hold")

    # The mark has travelled: a consumer reading a projection must be told.
    marks = {entry["id"] for entry in retractions.entries(register) if entry.get("id")}
    if marks:
        for projection in projections:
            if not projection.is_file():
                found.append(f"{projection.name} does not exist")
                continue
            text = projection.read_text(encoding="utf-8")
            for mark in sorted(marks):
                if mark not in text:
                    found.append(f"{projection.name} does not carry the mark {mark}")

    # Nothing withdrawn is presented as live by the contract's own samples.
    retracted_roles = {
        entry.get("element") for entry in retractions.entries(register)
        if entry.get("kind") == "element" and entry.get("element_kind") == "role"
    }
    schemes = schemes if schemes is not None else []
    components = components if components is not None else {}
    if retracted_roles:
        for scheme in schemes:
            used = set(scheme.get("roles", {}).get("dark", {}))
            for role in sorted(used & retracted_roles):
                found.append(f"the scheme {scheme['name']} stands on the retracted role {role}")
        for name, spec in components.items():
            text = json.dumps(spec)
            for role in sorted(retracted_roles):
                if f'"{role}"' in text or f"'{role}'" in text:
                    found.append(f"the component {name} stands on the retracted role {role}")

    return found


def main() -> int:
    if not REGISTER.is_file():
        print("FAIL: core/RETRACTIONS.json does not exist")
        return 1
    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    schemes = json.loads(SCHEMES.read_text(encoding="utf-8"))["schemes"]
    components = json.loads(COMPONENTS.read_text(encoding="utf-8"))["components"]
    found = problems(register, contract_elements(), PROJECTIONS, ROOT, schemes, components)
    if found:
        print(f"FAIL: {len(found)} problem(s) with the register of retractions")
        for problem in found:
            print(f"  - {problem}")
        return 1
    count = len(retractions.entries(register))
    if not count:
        print("PASS: nothing is retracted")
        return 0
    print(f"PASS: the register of retractions holds ({count} retraction(s), every mark carried)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
