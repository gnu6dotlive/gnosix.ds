#!/usr/bin/env python3
"""Publish the gnu6-design package, and re-cut it from the contract.

The `gnu6-design` package is what three repositories vendor. Its sheet
carried the design system's namespace in the layer ids' pre-kebab
spelling, and only a quarter of the published names, because it was cut
from Gnosix-DS-V3.4.1 and then frozen: the generator that produced it is
gone, and the only surviving forms of it are three byte-identical
vendored copies.

So the package is re-cut here, from the contract, by a generator that
exists and is gated:

  the vocabulary   the sheet's components are the field's, and they stay.
                   They are what every consumer already uses, and the
                   system's own components are the set they map onto.
  the namespace   every --gnosix-* name the sheet declares is rebound to
                   the name the system publishes, by NAM-001. The values
                   were always right; only the spelling had drifted.
  the vocabulary  the system's own names are added: the colours the
  of the system  sheet omits, the surfaces, the roles, the spacing.

    python3 tools/package_gnu6_design.py --write
    python3 tools/package_gnu6_design.py --check
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from oklch import hex_to_rgb, rgb_to_oklch  # noqa: E402

PACKAGE = ROOT / "packaging/gnu6-design"
LEGACY = PACKAGE / "legacy/gnu6-1.1.1.css"
ROLES = PACKAGE / "legacy/roles.json"
SHEET = PACKAGE / "gnu6.css"
LOCK = PACKAGE / "gnu6-design.lock.json"

GNOSIX_VAR = re.compile(r"--gnosix-[A-Za-z0-9-]+")


def words(name: str) -> list[str]:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name).split()


def kebab(name: str) -> str:
    return "-".join(part.lower() for part in words(name))


def published_name(*parts: str) -> str:
    out = []
    for part in parts:
        out.extend(words(part))
    return "--gnosix-" + "-".join(word.lower() for word in out)


def layer_ids() -> dict[str, str]:
    """Every layer the contract has, and the name it publishes.

    The key is the id in any spelling: the sheet declares
    `--gnosix-signalOrange-base` and the contract publishes
    `--gnosix-signal-orange-base`, and they are the same layer.
    """
    tokens = json.loads((ROOT / "core/TOKENS.json").read_text(encoding="utf-8"))
    surfaces = json.loads((ROOT / "core/SURFACES.json").read_text(encoding="utf-8"))
    out = {}
    for family, ramp in tokens["color"].items():
        for shade in ramp:
            name = published_name(family, shade)
            out[name.replace("--gnosix-", "").replace("-", "").lower()] = name
            out[f"{family}/{shade}".replace("-", "").replace("/", "").lower()] = name
    for spec in surfaces["families"].values():
        for step in spec["steps"]:
            name = published_name(step["id"])
            out[name.replace("--gnosix-", "").replace("-", "").lower()] = name
    for accent in surfaces["accents"]:
        name = published_name(accent["id"])
        out[name.replace("--gnosix-", "").replace("-", "").lower()] = name
    return out


def rebind(text: str) -> tuple[str, list[str]]:
    """The sheet, with every name the system publishes under its own name."""
    ids = layer_ids()
    changed = []

    def substitute(match: re.Match) -> str:
        name = match.group(0)
        key = name.replace("--gnosix-", "").replace("-", "").lower()
        if key in ids and ids[key] != name:
            changed.append(f"{name} -> {ids[key]}")
            return ids[key]
        return name

    return GNOSIX_VAR.sub(substitute, text), changed


def bind_roles(text: str) -> str:
    """The sheet's own role layer, bound to the system.

    The sheet declared thirty-four roles for the dark substrate and
    thirty-four for the light one, by hand. Each colour it declared is
    bound here to the step of the system that carries it, so the sheet
    names the system instead of carrying a colour of its own.
    """
    binding = json.loads(ROLES.read_text(encoding="utf-8"))["colours"]

    def substitute(match: re.Match) -> str:
        value = match.group(0).upper()
        name = binding.get(value)
        if not name:
            return match.group(0)
        return f"var({name})"

    return re.sub(r"#[0-9A-Fa-f]{6}\b", substitute, text)


def system_block() -> str:
    """The names the sheet omits, written the way the system writes them."""
    tokens = json.loads((ROOT / "core/TOKENS.json").read_text(encoding="utf-8"))
    surfaces = json.loads((ROOT / "core/SURFACES.json").read_text(encoding="utf-8"))
    rows = ["", "/* The system's own vocabulary, added by the re-cut. The sheet",
            "   above declares the field's names; these are the system's, and a",
            "   consumer that has adopted the package has both. */", ":root {"]
    for family, ramp in tokens["color"].items():
        for shade, value in ramp.items():
            rows.append(f"  {published_name(family, shade)}: {value.upper()};")
    for spec in surfaces["families"].values():
        for step in spec["steps"]:
            rows.append(f"  {published_name(step['id'])}: {step['value'].upper()};")
    for accent in surfaces["accents"]:
        rows.append(f"  {published_name(accent['id'])}: {accent['value'].upper()};")
    for role, weight in tokens["typography"]["weights"].items():
        rows.append(f"  --gnosix-weight-{role}: {int(weight)};")
    for step, value in (tokens.get("spacing") or {}).items():
        rows.append(f"  --gnosix-space-{step}: {value}px;")
    rows.append("}")
    return "\n".join(rows) + "\n"


def system_colours() -> set[str]:
    """Every colour the contract has."""
    tokens = json.loads((ROOT / "core/TOKENS.json").read_text(encoding="utf-8"))
    surfaces = json.loads((ROOT / "core/SURFACES.json").read_text(encoding="utf-8"))
    out = set()
    for ramp in tokens["color"].values():
        for value in ramp.values():
            out.add(value.upper())
    for spec in surfaces["families"].values():
        for step in spec["steps"]:
            out.add(step["value"].upper())
    for accent in surfaces["accents"]:
        out.add(accent["value"].upper())
    return out


def foreign(sheet: str) -> list[str]:
    """The colours the sheet carries that the system does not have."""
    sanctioned = system_colours()
    return sorted({value.upper() for value in re.findall(r"#[0-9A-Fa-f]{6}", sheet)
                   if value.upper() not in sanctioned})


def build() -> tuple[str, list[str], str]:
    legacy = LEGACY.read_text(encoding="utf-8")
    # The hand-made role layer goes first: it is the sheet's own colours
    # that the system does not have.
    legacy = bind_roles(legacy)
    rebound, changed = rebind(legacy)
    # The header states the version it was cut from, and the re-cut states
    # the version it is cut from now.
    header = re.sub(r"^/\* gnu6-design [^*]*\*/",
                    f"/* gnu6-design — re-cut by tools/package_gnu6_design.py from\n"
                    f"   gnosix.ds {(ROOT / 'VERSION').read_text(encoding='utf-8').strip()}. "
                    "Do not edit. */",
                    rebound, count=1)
    sheet = header.rstrip("\n") + "\n" + system_block()
    return sheet, changed, legacy


def lock_for(sheet: str) -> str:
    document = {
        "package": "gnu6-design",
        "version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "source": "gnosix.ds — packaging/gnu6-design, re-cut from the contract",
        "files": {"gnu6.css": hashlib.sha256(sheet.encode("utf-8")).hexdigest()},
        "note": "The package a consumer vendors. The sheet is the field's component "
                "vocabulary with the system's own namespace; the names are the ones "
                "the system publishes, and the values are the contract's.",
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="publish the gnu6-design package")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    sheet, changed, _ = build()
    lock = lock_for(sheet)

    if args.write:
        PACKAGE.mkdir(parents=True, exist_ok=True)
        SHEET.write_text(sheet, encoding="utf-8")
        LOCK.write_text(lock, encoding="utf-8")
        print(f"wrote {SHEET.relative_to(ROOT)}")
        print(f"wrote {LOCK.relative_to(ROOT)}")
        print(f"{len(changed)} name(s) rebound to the spelling the system publishes")
        return 0

    problems = []
    # The ratchet: the legacy vocabulary's own colours may shrink, never
    # grow. The count is recorded when the vocabulary is adopted.
    adoption = PACKAGE / "legacy/adoption.json"
    if adoption.is_file():
        recorded = json.loads(adoption.read_text(encoding="utf-8"))
        found = foreign(sheet)
        if len(found) > recorded["foreign_colours"]:
            problems.append(f"the sheet carries {len(found)} colours the system does "
                            f"not have, and the adopted vocabulary recorded "
                            f"{recorded['foreign_colours']}: the ratchet does not grow")
    if not SHEET.is_file():
        problems.append(f"{SHEET.relative_to(ROOT)} does not exist")
    elif SHEET.read_text(encoding="utf-8") != sheet:
        problems.append(f"{SHEET.relative_to(ROOT)} is not what the contract cuts")
    if not LOCK.is_file():
        problems.append(f"{LOCK.relative_to(ROOT)} does not exist")
    elif LOCK.read_text(encoding="utf-8") != lock:
        problems.append(f"{LOCK.relative_to(ROOT)} is not what the sheet hashes to")
    if problems:
        print(f"FAIL: {len(problems)} problem(s) with the package")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"PASS: the package is what the contract cuts "
          f"({len(changed)} name(s) rebound)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
