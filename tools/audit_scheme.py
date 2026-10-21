#!/usr/bin/env python3
"""Audit a scheme against the system's guarantees.

The system's roles are static in their meaning and dynamic in their
value: the accent is a role, and what it carries is a scheme's decision.
A consumer that lets the wallpaper decide carries a scheme, and the
scheme has to keep the guarantees the system states.

That is the whole point of this tool. A scheme is accepted when the
system's own pairings still read: every text on the ground it is written
on, and every mark against the ground it is seen on. The pairing list
is the system's, read from the same place the projection reads it, so
there is one rule and not two.

    python3 tools/audit_scheme.py core/schemes.json
    python3 tools/audit_scheme.py --check
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLES = ROOT / "core" / "ROLES.json"
SCHEMES = ROOT / "core" / "schemes.json"

sys.path.insert(0, str(ROOT / "tools"))

from oklch import contrast_ratio, hex_to_rgb  # noqa: E402
from project_roles import GRAPHIC, READS, load, resolve  # noqa: E402


def scheme_values(scheme: dict, substrate: str, roles: dict, tokens: dict,
                  surfaces: dict) -> dict[str, str]:
    """The value of every role on a substrate: the scheme's, or the system's.

    A scheme says what it changes and leaves the rest alone. The system's
    own values are the default, so a consumer that carries a scheme for
    one role still has the system's other roles — and the guarantees are
    checked against the whole, not against the part.
    """
    values = {}
    override = (scheme.get("roles") or {}).get(substrate, {})
    for name, spec in roles.items():
        if name in override:
            values[name] = override[name]
            continue
        reference = resolve(spec[substrate], tokens, surfaces)
        if not reference:
            continue
        values[name] = reference
    return values


def audit(scheme: dict, roles: dict, tokens: dict, surfaces: dict) -> list[str]:
    """What a scheme breaks, if it breaks anything."""
    problems = []
    for substrate in ("light", "dark"):
        values = scheme_values(scheme, substrate, roles, tokens, surfaces)
        for ink_role, surface_role, minimum in READS + GRAPHIC:
            # A role may say where it does not go. The contract states it,
            # and the audit honours the statement rather than guessing.
            excluded = roles.get(ink_role, {}).get("excludes") or []
            if surface_role in excluded:
                continue
            foreground = values.get(ink_role)
            background = values.get(surface_role)
            if not foreground or not background:
                problems.append(f"{scheme.get('name', '?')}: the {substrate} "
                                f"scheme does not say what {ink_role} or "
                                f"{surface_role} is")
                continue
            ratio = contrast_ratio(hex_to_rgb(foreground),
                                    hex_to_rgb(background))
            if ratio < minimum:
                problems.append(
                    f"{scheme.get('name', '?')}: on the {substrate} substrate, "
                    f"{ink_role} on {surface_role} measures {ratio:.2f}, and "
                    f"the system requires {minimum:.1f}")
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="audit a scheme against the system's guarantees")
    parser.add_argument("scheme", nargs="?",
                        help="a scheme file; the contract's samples by default")
    parser.add_argument("--check", action="store_true",
                        help="check the contract's own schemes")
    parser.add_argument("--name", default="the declared scheme",
                        help="the name a scheme is reported under")
    args = parser.parse_args(argv)

    document, tokens, surfaces = load()
    roles = document["roles"]
    if args.scheme:
        document = json.loads(Path(args.scheme).read_text(encoding="utf-8"))
        # A consumer writes its scheme in its own declaration, and the
        # contract's samples write a family of them. One shape reaches the
        # audit either way: a scheme is a name and the roles it decides.
        if "schemes" in document:
            schemes = document["schemes"]
        elif "roles" in document:
            schemes = [{"name": document.get("name", "the declared scheme"),
                        "roles": document["roles"]}]
        else:
            schemes = [document]
        source = args.scheme
    else:
        if not SCHEMES.is_file():
            print(f"FAIL: {SCHEMES.relative_to(ROOT)} does not exist")
            return 1
        document = json.loads(SCHEMES.read_text(encoding="utf-8"))
        schemes = document.get("schemes", [])
        source = str(SCHEMES.relative_to(ROOT))

    if not schemes:
        print(f"FAIL: {source} carries no scheme")
        return 1

    problems = []
    for scheme in schemes:
        problems.extend(audit(scheme, roles, tokens, surfaces))

    if problems:
        print(f"FAIL: {len(problems)} problem(s) with the scheme")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"PASS: every scheme keeps the system's guarantees "
          f"({len(schemes)} schemes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
