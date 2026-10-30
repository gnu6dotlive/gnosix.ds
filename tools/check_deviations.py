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


def probe_the_spacing_scale_has_ten_steps() -> list[str]:
    """The ten steps stand, and the three that are not in them are not."""
    tokens = json.loads((ROOT / "core" / "TOKENS.json").read_text(encoding="utf-8"))
    spacing = tokens.get("spacing") or {}
    problems = []
    if len(spacing) != 10:
        problems.append(f"the spacing scale has {len(spacing)} steps, and the "
                        f"decision was that ten stand")
    for value in (20, 40, 80):
        if value in spacing.values():
            problems.append(f"the spacing scale carries {value}, which is "
                            f"mapped rather than inserted")
    return problems


def probe_the_native_profile_carries_the_states() -> list[str]:
    """The native profile names every state the contract declares."""
    contract = json.loads((ROOT / "core" / "COMPONENTS.json").read_text(encoding="utf-8"))
    declared = set()
    for component in contract["components"].values():
        for state in component.get("states") or []:
            declared.add(state["name"])
    states = json.loads((ROOT / "profiles" / "native" / "states.json").read_text(encoding="utf-8"))
    named = {state["id"] for state in states["states"]}
    problems = []
    for state in sorted(declared - named):
        problems.append(f"{state}: the contract declares it and the native "
                        f"profile does not name it")
    for state in sorted(named - declared):
        problems.append(f"{state}: the native profile names it and the "
                        f"contract does not declare it")
    return problems


def probe_the_rule_count_is_stated() -> list[str]:
    """The README counts the obligations the contract holds, and counts them right.

    The number is prose, and prose drifts: the README said sixteen while
    the contract carried twenty-three. The count is read from the
    contract and compared with what the README says.
    """
    rules = json.loads((ROOT / "core" / "rules.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    wanted = len(rules["rules"])
    spoken = re.search(r"(\d+)\s+numbered obligations", readme)
    if not spoken:
        return ["the README does not say how many obligations the contract holds"]
    if int(spoken.group(1)) != wanted:
        return [f"the README says {spoken.group(1)} obligations and the contract "
                f"holds {wanted}"]
    return []


def probe_the_readme_counts_are_stated() -> list[str]:
    """The README counts the gates and the roles, and names every gate.

    The README announced twenty-two gates and fourteen roles while the
    qualification ran thirty-six and the contract bound sixteen, and its
    list of gates had lost seven of them. Both counts are read from where
    they live — the qualification's own list and the role register — and
    every gate the qualification runs has to be named in the README.
    """
    sys.path.insert(0, str(ROOT))
    from tools.ci import GATES

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roles = json.loads((ROOT / "core" / "ROLES.json").read_text(encoding="utf-8"))["roles"]
    gates = [label for label, _ in GATES] + ["test suite"]
    problems = []
    spoken = re.search(r"(\d+) gates, one command", readme)
    if not spoken:
        problems.append("the README does not say how many gates qualify the package")
    elif int(spoken.group(1)) != len(gates):
        problems.append(f"the README says {spoken.group(1)} gates and the "
                        f"qualification runs {len(gates)}")
    spoken = re.search(r"(\d+) roles —", readme)
    if not spoken:
        problems.append("the README does not say how many roles the contract binds")
    elif int(spoken.group(1)) != len(roles):
        problems.append(f"the README says {spoken.group(1)} roles and the "
                        f"contract binds {len(roles)}")
    for label in gates:
        if label not in readme:
            problems.append(f"the README does not name the gate {label!r}")
    return problems


def probe_the_text_roles_declare_their_pairing() -> list[str]:
    """Every role that carries text is measured against the ground it sits on.

    The table holds the pairings where text is written on a ground, and
    each of them measures at least 4.5:1. A role that carries text wears a
    colour, and that colour has to be in the table: the defect this probe
    keeps closed was a state colour that was never measured against the
    light substrate at all.
    """
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "tools"))
    from contrast import resolve
    from oklch import contrast_ratio, hex_to_rgb

    tokens = json.loads((ROOT / "core/TOKENS.json").read_text(encoding="utf-8"))
    roles = json.loads((ROOT / "core/ROLES.json").read_text(encoding="utf-8"))
    problems = []
    for pairing, declared in (tokens.get("contrast") or {}).items():
        ink, substrate = pairing.split("_on_")
        got = contrast_ratio(hex_to_rgb(resolve(tokens, ink)), hex_to_rgb(resolve(tokens, substrate)))
        if got < 4.5:
            problems.append(f"{pairing}: text is written on that ground at "
                            f"{round(got, 2)}:1, and 4.5:1 is the floor")
    inks = {resolve(tokens, pairing.split("_on_")[0]) for pairing in tokens.get("contrast", {})}
    for name, role in (roles.get("roles") or {}).items():
        if role.get("carries") != "text":
            continue
        for substrate in ("light", "dark"):
            binding = role.get(substrate)
            if not binding:
                continue
            value = resolve(tokens, binding)
            if value is None:
                problems.append(f"{name}: its {substrate} binding {binding} names no colour")
                continue
            if value.upper() not in {i.upper() for i in inks if i}:
                problems.append(f"{name}: the {substrate} colour {binding} is not measured "
                                f"against any ground in the contrast table")
    return problems


def probe_the_derivation_floor_is_computed() -> list[str]:
    """A derivation's floor is the number the system's own inks give.

    A derivation is admitted because of a number, and a number somebody
    typed is a wish. The floor of best-of-extremes is the geometric mean
    of the two extremes, because the worst ground is the one where the two
    inks read the same — and it is recomputed here from the roles, so that
    changing an ink changes the floor and the derivation is re-admitted on
    the new one or not at all.
    """
    import math
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "tools"))
    from contrast import resolve
    from oklch import hex_to_rgb

    tokens = json.loads((ROOT / "core/TOKENS.json").read_text(encoding="utf-8"))
    roles = json.loads((ROOT / "core/ROLES.json").read_text(encoding="utf-8"))["roles"]
    document = json.loads((ROOT / "core/DERIVATIONS.json").read_text(encoding="utf-8"))
    derivations = document.get("derivations") or {}

    def luminance(colour: str) -> float:
        def channel(value: int) -> float:
            c = value / 255
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        red, green, blue = (channel(v) for v in hex_to_rgb(colour))
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    problems = []
    for name, entry in derivations.items():
        if not entry.get("statement"):
            problems.append(f"{name}: states no computation")
        if not entry.get("floor_basis"):
            problems.append(f"{name}: states no basis for its floor")
        if entry.get("floor") is None and not entry.get("ground"):
            problems.append(f"{name}: has no floor and does not say it is a ground")

    light = resolve(tokens, roles["ink"]["dark"])
    dark = resolve(tokens, roles["ink"]["light"])
    if light and dark:
        high, low = sorted((luminance(light), luminance(dark)), reverse=True)
        computed = math.sqrt((high + 0.05) / (low + 0.05))
        stated = (derivations.get("best-of-extremes") or {}).get("floor")
        if not isinstance(stated, (int, float)):
            problems.append("best-of-extremes: states no floor to check")
        elif abs(computed - stated) > 0.01:
            problems.append(
                f"best-of-extremes: its floor is stated as {stated:.3f} and the "
                f"system's two inks give {computed:.3f}")
    return problems


PROBES = {
    "no_self_reference": probe_no_self_reference,
    "the_text_roles_declare_their_pairing": probe_the_text_roles_declare_their_pairing,
    "the_rule_count_is_stated": probe_the_rule_count_is_stated,
    "the_readme_counts_are_stated": probe_the_readme_counts_are_stated,
    "no_foreign_literal": probe_no_foreign_literal,
    "the_field_spellings_are_accounted": probe_the_field_spellings_are_accounted,
    "the_package_carries_the_elements": probe_the_package_carries_the_elements,
    "the_cited_path_exists": probe_the_cited_path_exists,
    "the_components_name_a_radius_step": probe_the_components_name_a_radius_step,
    "the_spacing_scale_has_ten_steps": probe_the_spacing_scale_has_ten_steps,
    "the_native_profile_carries_the_states": probe_the_native_profile_carries_the_states,
    "the_derivation_floor_is_computed": probe_the_derivation_floor_is_computed,
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
