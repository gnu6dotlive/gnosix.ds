#!/usr/bin/env python3
"""Check that the register of upstream is honest.

The contract is the semantic authority. Wayland, GPUI/Zed and Hyprland are
projection targets and sources of evidence, and they are watched, not
obeyed: when one of them changes, the change is measured against what the
contract already says.

So the register is held to the obligations, and not to its shape alone:

  a pin is not a name in a file. Every pin says the exact identity, the
  authority that owns and records it, whether this repository actually
  checks it, what behaviour was qualified against it, the divergence that
  is known, and what would justify refreshing it. A pin this repository
  cannot check is labelled as one — referenced, or declared — and a pin
  that claims to be verified while living in another repository is a
  failure, not a matter of taste.

  an observation says the exact identity and the source of what it
  observed, the rail and the contract elements it bears on, what was
  observed and what is inferred, the local evidence and the limits of it,
  the level the evidence is at, whether a projection changes, the gate that
  holds the answer or the reason none applies, the smallest falsifiable
  next experiment, the decision owner and the present disposition — and the
  scope: which claims depend on the affected behaviour, and which do not.

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

# The six things a pin must say, and the things an observation must say.
PIN_FIELDS = ("exact_identity", "authority", "verification", "qualification_scope",
              "known_divergence", "refresh_condition")
OBSERVATION_FIELDS = ("bears_on", "materiality", "observed_fact", "inference",
                      "local_evidence", "evidence_limits", "evidence_level",
                      "projection", "projection_reason", "next_experiment",
                      "decision_owner", "disposition", "scope_affected",
                      "scope_unaffected")

# The levels the authority boundary keeps apart: a record at one level is
# not a record at the next.
LEVELS = ("semantic", "declared", "source", "observed", "installed")
# The states of a pin's verification. A pin this repository cannot check
# is referenced or declared; only a pin the repository checks is verified.
VERIFICATIONS = ("verified", "referenced", "declared")


def is_repository(root: Path = ROOT) -> bool:
    """Whether this copy is the repository's own, and not a copy of the package.

    The local simulation of the runner is what makes a copy the
    repository: the package carries the expectations of the gates, not the
    machinery that runs them.
    """
    return (root / "ci" / "local-ci.sh").is_file()


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
    levels = tuple(register.get("levels", LEVELS))
    verifications = tuple(register.get("verifications", VERIFICATIONS))

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
        for field in PIN_FIELDS:
            if not pin.get(field):
                found.append(f"the pin on the rail {rail} does not say {field.replace('_', ' ')}")
        if not pin.get("where"):
            found.append(f"the pin on the rail {rail} does not say where it was measured")

        identity = pin.get("exact_identity", "")
        for moving in MOVING:
            if re.search(rf"\b{moving}\b", identity.lower()):
                found.append(f"the pin on the rail {rail} names a moving reference ({moving}), "
                             f"which is not an immutable identity")

        status = pin.get("verification")
        if status and status not in verifications:
            found.append(f"the pin on the rail {rail} says its verification is {status!r}, which is "
                         f"not one of {', '.join(verifications)}")
        elif status == "verified":
            # A pin is verified only when this repository checks it, and
            # this repository checks only what it holds.
            authority = pin.get("authority", "")
            if not authority.startswith("this repository"):
                found.append(f"the pin on the rail {rail} claims to be verified, but its authority "
                             f"is {authority!r}: a pin this repository cannot check is referenced "
                             f"or declared, never verified")
            elif not (root / pin.get("where", "")).is_file():
                # The file is not in this copy. The local simulation of the
                # runner is what tells a working copy of the repository from
                # a copy of the package: the package does not carry it. In
                # the repository, a verified pin that names a file the
                # repository does not hold is a failure. In a copy of the
                # package, the check cannot run — a skip, not a failure.
                if is_repository(root):
                    found.append(f"the pin on the rail {rail} claims to be verified, but "
                                 f"{pin.get('where')!r} is not a file this repository holds")


        # A pin the repository holds must still be the pin: a file that
        # names a revision is a file that can be checked against it.
        where = pin.get("where", "")
        if (root / where).is_file():
            text = (root / where).read_text(encoding="utf-8")
            # The file names the version and the digest separately, so the
            # parts are checked, not the sentence.
            tokens = re.findall(r"\b[0-9a-f]{32,}\b", identity)
            tokens += re.findall(r"\b\d+\.\d+(?:\.\d+)*\b", identity)
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
        for field in ("what", "exact_identity", "source", "published_behaviour", "field_behaviour"):
            if not upstream.get(field):
                found.append(f"{identifier} does not say the upstream {field.replace('_', ' ')}")

        revision = upstream.get("exact_identity", "")
        for moving in MOVING:
            if re.search(rf"\b{moving}\b", revision.lower()):
                found.append(f"{identifier} pins a moving reference ({moving}), which is not an identity")

        for field in OBSERVATION_FIELDS:
            if observation.get(field) in (None, "", []):
                found.append(f"{identifier} does not say {field.replace('_', ' ')}")

        bears_on = observation.get("bears_on") or []
        for element in bears_on:
            if element not in elements:
                found.append(f"{identifier} bears on {element}, which the contract does not publish")

        if observation.get("evidence_level") and observation["evidence_level"] not in levels:
            found.append(f"{identifier} says its evidence is at the level "
                         f"{observation['evidence_level']!r}, which is not one of {', '.join(levels)}")

        projection = observation.get("projection")
        if projection and projection != "none" and not (root / projection).exists():
            found.append(f"{identifier} says the projection {projection} changes, which is not in "
                         f"the repository")

        gate = observation.get("gate")
        if gate and not (root / gate).exists():
            found.append(f"{identifier} names the gate {gate}, which is not in the repository")
        if not gate and not observation.get("gate_reason"):
            found.append(f"{identifier} has neither a gate nor the reason none applies")

    for handoff in register.get("handoffs", []):
        where = handoff.get("where", "")
        if where and not (root / where).is_file():
            found.append(f"the handoff {handoff.get('id')} points at {where}, which is not in the "
                         f"repository")

    return found


def not_checkable_here(register: dict, root: Path = ROOT) -> list[str]:
    """The pins this copy cannot check, said out loud rather than passed over."""
    if is_repository(root):
        return []
    notes = []
    for pin in register.get("pins", []):
        if pin.get("verification") == "verified" and not (root / pin.get("where", "")).is_file():
            notes.append(f"the pin on the rail {pin.get('rail')} could not be checked in this copy: "
                         f"{pin.get('where')!r} is not in it")
    return notes


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
    handoffs = len(register.get("handoffs", []))
    for note in not_checkable_here(register):
        print(f"SKIP: {note}")
    print(f"PASS: the register of upstream holds ({rails} rails, {pins} pins, "
          f"{observations} observations, {handoffs} handoffs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
