#!/usr/bin/env python3
"""Project the states of the contract into the native profile.

The native profile carries the roles and the states, and not the
HTML/CSS structure: roles and state cross the boundary. This projects
the states into Rust, and checks two things the contract cannot check
for itself:

  - every state the contract's elements declare is named in the native
    profile, and every state the native profile names is declared by the
    contract. A state the profile invents is a state no element has; a
    state the profile omits is a state a native surface cannot express.

  - the projection is what the profile says it is.

    python3 tools/project_native_states.py --write
    python3 tools/project_native_states.py --check
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATES = ROOT / "profiles" / "native" / "states.json"
CONTRACT = ROOT / "core" / "COMPONENTS.json"
RUST = ROOT / "profiles" / "native" / "src" / "states.rs"

RUST_NAME = re.compile(r"[A-Za-z0-9]+")


def snake(name: str) -> str:
    return "_".join(part.lower() for part in RUST_NAME.findall(name))


def contract_states() -> dict[str, set[str]]:
    """The states the contract's elements declare, and which declare them."""
    document = json.loads(CONTRACT.read_text(encoding="utf-8"))
    out: dict[str, set[str]] = {}
    for name, component in document["components"].items():
        for state in component.get("states") or []:
            out.setdefault(state["name"], set()).add(name)
    return out


def render(states: dict) -> str:
    lines = [
        "//! Generated from profiles/native/states.json. Do not edit.",
        "//!",
        "//! The states the system's elements declare, as a native target reads",
        "//! them: what a state means, the role it wears, and the treatment a",
        "//! surface gives it. The structure does not cross the boundary; the",
        "//! meaning and the state do.",
        "",
        "#![allow(dead_code)]",
        "",
        "/// One state: what it means, and the role it wears when it wears one.",
        "#[derive(Clone, Copy, Debug, PartialEq, Eq)]",
        "pub struct State {",
        "    pub id: &'static str,",
        "    pub role: Option<&'static str>,",
        "    pub treatment: &'static str,",
        "    pub evidence: &'static str,",
        "}",
        "",
    ]
    for state in states["states"]:
        role = state.get("role")
        lines.append(f"/// {state['meaning']}")
        lines.append(f"pub const {snake(state['id']).upper()}: State = State {{")
        lines.append(f"    id: {json.dumps(state['id'])},")
        role_literal = "None" if not role else f"Some({json.dumps(role)})"
        lines.append(f"    role: {role_literal},")
        lines.append(f"    treatment: {json.dumps(state['treatment'])},")
        lines.append(f"    evidence: {json.dumps(state['evidence'])},")
        lines.append("};")
        lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="project the states into the native profile")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if not STATES.is_file():
        print(f"FAIL: {STATES.relative_to(ROOT)} does not exist")
        return 1
    states = json.loads(STATES.read_text(encoding="utf-8"))
    declared = contract_states()
    named = {state["id"] for state in states["states"]}

    problems = []
    for state in sorted(declared):
        if state not in named:
            problems.append(f"{state}: the contract declares it and the native "
                            f"profile does not name it")
    for state in sorted(named):
        if state not in declared:
            problems.append(f"{state}: the native profile names it and the "
                            f"contract does not declare it")
    for state in states["states"]:
        for field in ("id", "meaning", "treatment", "evidence"):
            if not state.get(field):
                problems.append(f"{state.get('id')}: it says no {field}")

    if args.write:
        RUST.write_text(render(states), encoding="utf-8")
        if problems:
            print(f"WROTE: {len(states['states'])} states, but "
                  f"{len(problems)} problem(s) remain")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print(f"WROTE: {len(states['states'])} states projected into the "
              f"native profile")
        return 0

    if args.check:
        if not RUST.is_file():
            problems.append(f"{RUST.relative_to(ROOT)} does not exist")
        elif RUST.read_text(encoding="utf-8") != render(states):
            problems.append("the native profile's states are not what the "
                            "profile says they are")
        if problems:
            print(f"FAIL: {len(problems)} problem(s) with the native states")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print(f"PASS: the native profile carries the contract's states "
              f"({len(states['states'])} states, {len(declared)} declared)")
        return 0

    print(f"{len(states['states'])} states; the contract declares "
          f"{len(declared)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
