#!/usr/bin/env python3
"""Check that the register of upstream is honest.

The contract is the semantic authority. Wayland, GPUI/Zed and Hyprland are
projection targets and sources of evidence, and they are watched, not
obeyed: when one of them changes, the change is measured against what the
contract already says.

The exit condition for an upstream change is four things — the exact
revision, the contract element it bears on, whether a projection changes,
and either a reproducible gate or an explicit conclusion that there is no
effect. So the register is held to exactly that:

  every rail says what it watches and what would make a change material;
  every pin is an exact revision, never a moving reference, and says where
  it was measured;
  every observation names a rail, an exact revision, the contract elements
  it bears on, whether a projection changes, and either a gate that exists
  or the reason there is no effect;
  and the elements an observation names are elements the contract has.

    python3 tools/check_upstream.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

REGISTER = ROOT / "core" / "UPSTREAM.json"
RULES = ROOT / "core" / "rules.json"
COMPONENTS = ROOT / "core" / "COMPONENTS.json"
ROLES = ROOT / "core" / "ROLES.json"
STATES = ROOT / "profiles" / "native" / "states.json"
DEVIATIONS = ROOT / "core" / "DEVIATIONS.json"
DERIVATIONS = ROOT / "core" / "DERIVATIONS.json"

# A pin that names a moving reference is not a pin: the next change could
# not be a difference against it.
MOVING = ("latest", "main", "master", "head", "current", "tip", "nightly")
EVIDENCE = ("source", "runtime", "both")
IDENTIFIER = re.compile(r"^UP-\d{3}$")


def contract_elements() -> set[str]:
    """Everything the contract publishes that an observation may bear on."""
    found: set[str] = set()
    found |= {rule["id"] for rule in json.loads(RULES.read_text(encoding="utf-8"))["rules"]}
    found |= set(json.loads(COMPONENTS.read_text(encoding="utf-8"))["components"])
    found |= set(json.loads(ROLES.read_text(encoding="utf-8"))["roles"])
    found |= {state["id"] for state in json.loads(STATES.read_text(encoding="utf-8"))["states"]}
    found |= {entry["id"] for entry in json.loads(DEVIATIONS.read_text(encoding="utf-8"))["deviations"]}
    found |= set(json.loads(DERIVATIONS.read_text(encoding="utf-8")).get("derivations", {}))
    return found


def problems(register: dict, root: Path = ROOT) -> list[str]:
    """What is wrong with the register, and with what it says of upstream."""
    found: list[str] = []
    elements = contract_elements()

    rails = {}
    for rail in register.get("rails", []):
        identifier = rail.get("id", "")
        if not identifier:
            found.append("a rail has no identifier")
            continue
        if identifier in rails:
            found.append(f"the rail {identifier} is declared twice")
        rails[identifier] = rail
        if not rail.get("subject"):
            found.append(f"the rail {identifier} does not say what it watches")
        if not rail.get("materiality"):
            found.append(f"the rail {identifier} does not say what would make a change material")

    pins = {}
    for pin in register.get("pins", []):
        rail = pin.get("rail")
        if rail not in rails:
            found.append(f"a pin names the rail {rail!r}, which is not a rail of the register")
        if not pin.get("revision"):
            found.append(f"a pin on the rail {rail} does not say the revision")
        if not pin.get("where"):
            found.append(f"a pin on the rail {rail} does not say where it was measured")
        revision = (pin.get("exact") or pin.get("revision") or "").lower()
        for moving in MOVING:
            if re.search(rf"\b{moving}\b", revision):
                found.append(f"the pin on the rail {rail} names a moving reference ({moving}), "
                             f"which is not a revision")
        # A pin the repository holds must still be the pin: a file that
        # names a revision is a file that can be checked against it.
        where = pin.get("where", "")
        if (root / where).is_file():
            text = (root / where).read_text(encoding="utf-8")
            exact = pin.get("exact") or ""
            # The file names the version and the digest separately, so the
            # parts are checked, not the sentence.
            tokens = re.findall(r"\b[0-9a-f]{32,}\b", exact)
            tokens += [part for part in re.split(r"[,;]", exact)
                       if re.fullmatch(r"[0-9][0-9A-Za-z.\-]*", part.strip())]
            for token in tokens:
                if token and token not in text:
                    found.append(f"the pin on the rail {rail} says {token!r}, which {where} does not "
                                 f"hold: the pin has rotted")
        pins.setdefault(rail, []).append(pin)

    for rail in rails:
        if rail not in pins:
            found.append(f"the rail {rail} has no pin: a change could not be measured against "
                         f"anything")

    seen: set[str] = set()
    for observation in register.get("observations", []):
        identifier = observation.get("id", "")
        if not IDENTIFIER.match(identifier):
            found.append(f"{identifier or 'an observation'} has no identifier of the shape UP-NNN")
            continue
        if identifier in seen:
            found.append(f"{identifier} is in the register twice")
        seen.add(identifier)

        rail = observation.get("rail")
        if rail not in rails:
            found.append(f"{identifier} names the rail {rail!r}, which is not a rail of the register")

        upstream = observation.get("upstream") or {}
        if not upstream.get("what"):
            found.append(f"{identifier} does not say what upstream it observed")
        revision = upstream.get("revision") or ""
        if not revision:
            found.append(f"{identifier} does not pin the revision it observed")
        for moving in MOVING:
            if re.search(rf"\b{moving}\b", revision.lower()):
                found.append(f"{identifier} pins a moving reference ({moving}), which is not a revision")
        if not upstream.get("change"):
            found.append(f"{identifier} does not say what changed")

        bears_on = observation.get("bears_on") or []
        if not bears_on:
            found.append(f"{identifier} does not say what contract element it bears on")
        for element in bears_on:
            if element not in elements:
                found.append(f"{identifier} bears on {element}, which the contract does not publish")

        projection = observation.get("projection")
        if not projection:
            found.append(f"{identifier} does not say whether a projection changes")
        elif projection != "none" and not (root / projection).exists():
            found.append(f"{identifier} says the projection {projection} changes, which is not in "
                         f"the repository")

        if observation.get("evidence") not in EVIDENCE:
            found.append(f"{identifier} does not say whether the support is source or runtime "
                         f"evidence")

        gate = observation.get("gate")
        conclusion = observation.get("conclusion")
        if not gate and not conclusion:
            found.append(f"{identifier} has neither a gate nor a conclusion: the exit condition "
                         f"asks for one or the other")
        if gate and not (root / gate).exists():
            found.append(f"{identifier} names the gate {gate}, which is not in the repository")
        if conclusion and not conclusion.strip():
            found.append(f"{identifier} has an empty conclusion")

    return found


def main() -> int:
    if not REGISTER.is_file():
        print("FAIL: core/UPSTREAM.json does not exist")
        return 1
    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    found = problems(register)
    if found:
        print(f"FAIL: {len(found)} problem(s) with the register of upstream")
        for problem in found:
            print(f"  - {problem}")
        return 1
    rails = len(register.get("rails", []))
    pins = len(register.get("pins", []))
    observations = len(register.get("observations", []))
    print(f"PASS: the register of upstream holds ({rails} rails, {pins} pins, "
          f"{observations} observations)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
