#!/usr/bin/env python3
"""Check that the severity register is honest.

The register says what the system and the field do not agree about, what
each difference is worth, and who owns it. A register that nobody checks
is a list of intentions.

So the shape is checked — every deviation has an identifier, a severity
from the scale, a state, and an owner — and every *closed* deviation is
checked again: the probe named in the register is run, and a deviation
that has come back is a failure.

    python3 tools/check_deviations.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "core" / "DEVIATIONS.json"
SHEET = ROOT / "packaging" / "gnu6-design" / "gnu6.css"
SPEC = ROOT / "core" / "COMPONENTS.json"

SEVERITIES = {"critical", "major", "minor", "none"}
STATES = {"open", "closed"}
SELF_REFERENCE = re.compile(r"(--[\w-]+)\s*:\s*var\(\s*\1\s*\)")
SEMANTIC_LITERAL = re.compile(r"(--g6-[\w-]+)\s*:\s*#[0-9A-Fa-f]{6}")
CITED = ROOT / "profiles" / "frontend-audit" / "ABSORPTION.md"
ELEMENTS = ("button", "text-input", "badge", "card", "dialog", "tooltip",
            "select", "tabs", "toaster", "toggle", "command-palette", "icon",
            "section-heading", "system")


def probe_no_self_reference() -> list[str]:
    """The sheet must not name a custom property as a reference to itself."""
    if not SHEET.is_file():
        return []
    text = SHEET.read_text(encoding="utf-8")
    return [f"the sheet declares {name} as a reference to itself"
            for name in sorted(set(SELF_REFERENCE.findall(text)))]


def probe_no_foreign_literal() -> list[str]:
    """The sheet's own names must name the system, not carry a colour."""
    if not SHEET.is_file():
        return []
    text = SHEET.read_text(encoding="utf-8")
    return [f"the sheet's {name} still carries a colour of its own"
            for name in sorted(set(SEMANTIC_LITERAL.findall(text)))]


def probe_the_field_spellings_are_accounted() -> list[str]:
    """The field's three spellings must be accounted for, and differ."""
    document = json.loads(SPEC.read_text(encoding="utf-8"))
    vocabulary = document["vocabularies"]["gnu6-design"]["components"]
    problems = []
    for name in ("action", "state", "section"):
        entry = vocabulary.get(name, {})
        if not entry.get("account"):
            problems.append(f"{name}: the field's own spelling is not accounted for")
        if not entry.get("differs"):
            problems.append(f"{name}: the field's own spelling does not say "
                            f"where it differs from the system's")
    return problems


def probe_the_package_carries_the_elements() -> list[str]:
    """The package must publish the system's own elements."""
    if not SHEET.is_file():
        return []
    text = SHEET.read_text(encoding="utf-8")
    missing = [name for name in ELEMENTS if f".g6-{name}" not in text]
    return [f"the package does not publish the system's {name}" for name in missing]


def probe_the_cited_path_exists() -> list[str]:
    """The audit must not claim that a path does not exist.

    The audit said the path blob.in-showcase's source cites does not
    exist. It does. The claim was false, the audit was corrected, and the
    correction is what this probe holds: the false claim must not come
    back into the document.

    The probe reads the document, not the path. A gate that reads a path
    outside the repository is a gate the local qualification cannot
    reproduce — the runner does not have this machine's home — and the
    failure it produces is a failure of method, not of the code.
    """
    if not CITED.is_file():
        return [f"the audit is not there: {CITED}"]
    text = CITED.read_text(encoding="utf-8")
    problems = []
    for claim in ("claims to derive from a gnosix path that does not exist",
                  "That path does not exist"):
        if claim in text:
            problems.append(f"the audit still claims: {claim!r}")
    if "path exists" not in text.lower():
        problems.append("the audit does not say that the path exists")
    return problems


def probe_the_components_name_a_radius_step() -> list[str]:
    """A component's radius is a step of the scale, not a number."""
    document = json.loads(SPEC.read_text(encoding="utf-8"))
    tokens = json.loads((ROOT / "core" / "TOKENS.json").read_text(encoding="utf-8"))
    steps = set(tokens.get("radius") or {})
    problems = []
    for name, component in document["components"].items():
        for where, geometry in [(name, component.get("geometry") or {})] + [
                (f"{name}.parts.{part.get('name')}", part.get("geometry") or {})
                for part in component.get("parts") or []]:
            radius = (geometry or {}).get("radius")
            if not isinstance(radius, dict):
                continue
            if "step" in radius:
                if radius["step"] not in steps:
                    problems.append(f"{where}: the radius step "
                                   f"{radius['step']!r} is not one of the scale's")
            else:
                problems.append(f"{where}: the radius is a number, not a step")
    return problems


PROBES = {
    "no_self_reference": probe_no_self_reference,
    "no_foreign_literal": probe_no_foreign_literal,
    "the_field_spellings_are_accounted": probe_the_field_spellings_are_accounted,
    "the_package_carries_the_elements": probe_the_package_carries_the_elements,
    "the_cited_path_exists": probe_the_cited_path_exists,
    "the_components_name_a_radius_step": probe_the_components_name_a_radius_step,
}


def main() -> int:
    if not REGISTER.is_file():
        print(f"FAIL: {REGISTER.relative_to(ROOT)} does not exist")
        return 1
    document = json.loads(REGISTER.read_text(encoding="utf-8"))
    deviations = document.get("deviations", [])
    problems = []
    seen = set()

    for deviation in deviations:
        identifier = deviation.get("id", "")
        if not identifier:
            problems.append("a deviation has no identifier")
            continue
        if identifier in seen:
            problems.append(f"{identifier}: the identifier is used twice")
        seen.add(identifier)
        severity = deviation.get("severity")
        if severity not in SEVERITIES:
            problems.append(f"{identifier}: its severity is {severity!r}, which "
                            f"is not on the scale")
        state = deviation.get("state")
        if state not in STATES:
            problems.append(f"{identifier}: its state is {state!r}, which is "
                            f"neither open nor closed")
        if not deviation.get("what"):
            problems.append(f"{identifier}: it says nothing about what it is")
        if not deviation.get("owner"):
            problems.append(f"{identifier}: it names no owner")
        if state == "closed":
            probe = deviation.get("probe")
            if not probe:
                problems.append(f"{identifier}: it is closed and carries no "
                                f"probe to keep it closed")
                continue
            if probe not in PROBES:
                problems.append(f"{identifier}: its probe {probe!r} is not one "
                                f"the gate knows")
                continue
            for problem in PROBES[probe]():
                problems.append(f"{identifier}: {problem}")

    if problems:
        print(f"FAIL: {len(problems)} problem(s) with the severity register")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    closed = sum(1 for d in deviations if d.get("state") == "closed")
    open_ = len(deviations) - closed
    print(f"PASS: the severity register holds ({len(deviations)} deviations, "
          f"{closed} closed, {open_} open)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
