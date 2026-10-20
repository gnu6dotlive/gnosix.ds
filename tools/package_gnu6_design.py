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
from project_tokens import css_font_stack  # noqa: E402

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


DECLARATION = re.compile(r"(--[\w-]+|[\w-]+)(\s*:\s*)(#[0-9A-Fa-f]{6}\b)")


def bind_roles(text: str) -> str:
    """The sheet's own role layer, bound to the system.

    The sheet declared thirty-four roles for the dark substrate and
    thirty-four for the light one, by hand. Each colour it declared is
    bound here to the step of the system that carries it, so the sheet
    names the system instead of carrying a colour of its own.

    A colour is never bound into the declaration of the name it binds.
    The sheet's palette block declares the system's own names, and a
    name written as a reference to itself is not a colour at all: it is
    invalid at computed-value time, and it only appears to work because
    the system declares the same name again further down.
    """
    binding = json.loads(ROLES.read_text(encoding="utf-8"))["colours"]

    def substitute(match: re.Match) -> str:
        prop, separator, value = match.group(1), match.group(2), match.group(3)
        name = binding.get(value.upper())
        if not name or name == prop:
            return match.group(0)
        return f"{prop}{separator}var({name})"

    return DECLARATION.sub(substitute, text)


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
    for role, stack in tokens["typography"].items():
        if role in ("weights", "technical_features") or not isinstance(stack, list):
            continue
        rows.append(f"  --gnosix-font-{role}: {css_font_stack(stack)};")
    for step, value in (tokens.get("spacing") or {}).items():
        rows.append(f"  --gnosix-space-{step}: {value}px;")
    rows.append("}")
    return "\n".join(rows) + "\n"


def role_block() -> str:
    """The system's roles, bound to the sheet's substrate.

    The sheet chooses its substrate with data-g6-mode; the system chooses
    its with data-gnosix-substrate. The package is one file, so the roles
    follow the sheet: the same three blocks, in the same order, with the
    system's role names bound to the system's own tokens. The elements
    below name the roles, and a role that resolves to nothing is a
    surface that falls back to whatever the cascade gives it.
    """
    from project_roles import reference_name

    roles = json.loads((ROOT / "core/ROLES.json").read_text(encoding="utf-8"))["roles"]

    def declarations(substrate: str, indent: str = "  ") -> str:
        rows = []
        for name, spec in roles.items():
            rows.append(f"{indent}--gnosix-{name}: "
                        f"var({reference_name(spec[substrate])});")
        return "\n".join(rows)

    lines = [
        "",
        "/* The system's roles, bound to the sheet's substrate. The roles say",
        "   what a thing is for; the sheet says which surface it sits on. */",
        ':root,',
        '[data-g6-mode="dark"] {',
        declarations("dark"),
        "}",
        "@media (prefers-color-scheme: light) {",
        '  :root:not([data-g6-mode="dark"]) {',
        declarations("light", "    "),
        "  }",
        "}",
        '[data-g6-mode="light"] {',
        declarations("light"),
        "}",
    ]
    return "\n".join(lines) + "\n"


def elements_block() -> str:
    """The system's own elements, in the field's spelling.

    The package is the contract's projection into the vocabulary the field
    writes in, so it carries the contract's elements too, under the g6-
    prefix. The field's own three — the action, the state and the section
    — keep their names: they are the field's own implementations, the
    contract says where they differ from the system's, and a name that
    meant two things would be a name nobody could read.
    """
    from project_components import render_component

    spec = json.loads((ROOT / "core/COMPONENTS.json").read_text(encoding="utf-8"))
    parts = [
        "",
        "/* The system's own elements, in the field's spelling. The field's",
        "   sheet keeps its own three — the action, the state and the section",
        "   — and the contract says where each differs from the system's. */",
    ]
    for name, component in spec["components"].items():
        parts.append(f"\n/* {name} — {component['description'].split('.')[0]}. */")
        parts.append(render_component(name, component))
    parts.append("""
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}
""")
    return "".join(parts).replace(".gnosix-", ".g6-")


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
    # The names come first, then the colours: a colour is bound to the
    # step of the system that carries it, and the step's name has to be
    # the one the system publishes before the two can be compared.
    rebound, changed = rebind(legacy)
    # The hand-made role layer goes second: it is the sheet's own colours
    # that the system does not have.
    rebound = bind_roles(rebound)
    # The header states the version it was cut from, and the re-cut states
    # the version it is cut from now.
    header = re.sub(r"^/\* gnu6-design [^*]*\*/",
                    f"/* gnu6-design — re-cut by tools/package_gnu6_design.py from\n"
                    f"   gnosix.ds {(ROOT / 'VERSION').read_text(encoding='utf-8').strip()}. "
                    "Do not edit. */",
                    rebound, count=1)
    sheet = (header.rstrip("\n") + "\n" + system_block() + role_block()
             + elements_block())
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
