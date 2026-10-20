#!/usr/bin/env python3
"""Project the semantic role layer, and check that it is legible.

The contract has a palette, a surface layer and a set of roles stated in
prose. What it did not have was the binding between them, so a consumer
had to choose a colour for every role for itself - which is why one
frontend in the field carries about two hundred and fifty hardcoded hex
values in a single stylesheet, and why a change of substrate had to be
redone by hand.

This projects that binding. The role layer is stated in core/ROLES.json:
each role names the token it is bound to on the light substrate and on the
dark one. The projections carry the binding to the targets - CSS custom
properties, Rust constants, Kotlin colours - and the check refuses a
binding whose ink does not read on its own surface.

    python3 tools/project_roles.py --write
    python3 tools/project_roles.py --check
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from oklch import contrast_ratio, hex_to_rgb  # noqa: E402

ROLES = ROOT / "core/ROLES.json"
TOKENS = ROOT / "core/TOKENS.json"
SURFACES = ROOT / "core/SURFACES.json"

WEB = ROOT / "profiles/web/roles.css"
NATIVE = ROOT / "profiles/native/src/roles.rs"
ANDROID = ROOT / ("profiles/android/sample/app/src/main/java/labs/gnuin/"
                  "gnosixds/GnosixRoles.kt")

# The pairings that must read. A role layer that is not legible is not a
# role layer; it is a second palette.
READS = [
    ("ink", "surface", 4.5),
    ("ink-muted", "surface", 4.5),
    ("ink", "surface-raised", 4.5),
    ("ink", "surface-overlay", 4.5),
    ("ink-muted", "surface-raised", 4.5),
    ("accent-ink", "accent", 4.5),
    ("ink", "surface-sunken", 4.5),
    ("ink", "positive-surface", 4.5),
]


def words(name: str) -> list[str]:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name).split()


def kebab(name: str) -> str:
    return "-".join(part.lower() for part in words(name))


def published_name(*parts: str) -> str:
    out = []
    for part in parts:
        out.extend(words(part))
    return "--gnosix-" + "-".join(word.lower() for word in out)


def load() -> tuple[dict, dict, dict]:
    return (json.loads(ROLES.read_text(encoding="utf-8")),
            json.loads(TOKENS.read_text(encoding="utf-8")),
            json.loads(SURFACES.read_text(encoding="utf-8")))


def resolve(reference: str, tokens: dict, surfaces: dict) -> str | None:
    """The value of a token reference: a shade, a family base, or a surface step."""
    if "/" in reference:
        family, _, shade = reference.partition("/")
        ramp = tokens["color"].get(family)
        if isinstance(ramp, dict):
            return ramp.get(shade) or ramp.get("base")
        return None
    for spec in surfaces.get("families", {}).values():
        for step in spec.get("steps", []):
            if step["id"] == reference:
                return step["value"]
    for accent in surfaces.get("accents", []):
        if accent["id"] == reference:
            return accent["value"]
    return None


def snake(reference: str) -> str:
    """A reference, as the Rust profile names its constants."""
    if "/" in reference:
        family, _, shade = reference.partition("/")
        parts = words(family) + words(shade)
    else:
        parts = []
        for chunk in reference.split("-"):
            parts.extend(words(chunk))
    return "_".join(part.upper() for part in parts)


def reference_name(reference: str) -> str:
    """The published custom property a reference is bound to."""
    if "/" in reference:
        family, _, shade = reference.partition("/")
        return published_name(family, shade)
    return published_name(reference)


def problems(roles: dict, tokens: dict, surfaces: dict) -> list[str]:
    out = []
    for name, spec in roles["roles"].items():
        for substrate in ("light", "dark"):
            reference = spec.get(substrate)
            if not reference:
                out.append(f"{name}: no {substrate} binding")
                continue
            if resolve(reference, tokens, surfaces) is None:
                out.append(f"{name}.{substrate}: {reference} is not a token of the contract")
    return out


def readings(roles: dict, tokens: dict, surfaces: dict) -> list[str]:
    """The pairings that must read, and whether they do."""
    out = []
    for substrate in ("light", "dark"):
        for ink_role, surface_role, minimum in READS:
            ink = roles["roles"].get(ink_role, {}).get(substrate)
            surface = roles["roles"].get(surface_role, {}).get(substrate)
            if not ink or not surface:
                continue
            ink_value = resolve(ink, tokens, surfaces)
            surface_value = resolve(surface, tokens, surfaces)
            if not ink_value or not surface_value:
                continue
            ratio = contrast_ratio(hex_to_rgb(ink_value), hex_to_rgb(surface_value))
            if ratio + 1e-9 < minimum:
                out.append(f"{substrate}: {ink_role} on {surface_role} measures "
                           f"{ratio:.2f}, below {minimum}")
    return out


def render_web(roles: dict) -> str:
    lines = [
        "/* Generated from core/ROLES.json. Do not edit.",
        " *",
        " * The semantic role layer: what a thing is for, bound to a token on each",
        " * substrate. The components name the role and are written once.",
        " */",
        "",
        '@import url("./tokens.css");',
        "",
    ]
    for substrate in ("light", "dark"):
        selector = ':root,\n[data-gnosix-substrate="light"]' if substrate == "light" \
            else '[data-gnosix-substrate="dark"]'
        lines.append(f"{selector} {{")
        for name, spec in roles["roles"].items():
            reference = spec[substrate]
            lines.append(f"  --gnosix-{name}: var({reference_name(reference)});")
        lines.append("}")
        lines.append("")
    return "\n".join(lines)


def render_rust(roles: dict) -> str:
    lines = [
        "//! Generated from core/ROLES.json. Do not edit.",
        "//!",
        "//! The semantic role layer as Rust constants: a role bound to a token on",
        "//! the light substrate and on the dark one. A native target chooses a",
        "//! substrate and reads the roles from it.",
        "",
        "#![allow(dead_code)]",
        "",
        "/// One substrate: every role, bound to a colour.",
        "#[derive(Clone, Copy, Debug, PartialEq, Eq)]",
        "pub struct Substrate {",
    ]
    for name in roles["roles"]:
        lines.append(f"    pub {kebab(name).replace('-', '_')}: &'static str,")
    lines.append("}")
    lines.append("")
    for substrate in ("light", "dark"):
        lines.append(f"/// The {substrate} substrate.")
        lines.append(f"pub const {substrate.upper()}: Substrate = Substrate {{")
        for name, spec in roles["roles"].items():
            reference = spec[substrate]
            # The palette lives in one module and the surface layer in
            # another; a reference says which by its own shape.
            module = "colour" if "/" in reference else "surface"
            lines.append(f"    {kebab(name).replace('-', '_')}: "
                         f"crate::theme::{module}::{snake(reference)},")
        lines.append("};")
        lines.append("")
    return "\n".join(lines)


def render_kotlin(roles: dict, tokens: dict, surfaces: dict) -> str:
    lines = [
        "// Generated from core/ROLES.json. Do not edit.",
        "//",
        "// The semantic role layer as Compose colours: a role bound to a token on",
        "// the light substrate and on the dark one.",
        "",
        "package labs.gnuin.gnosixds",
        "",
        "import androidx.compose.ui.graphics.Color",
        "",
        "object GnosixRoles {",
    ]
    for substrate in ("light", "dark"):
        lines.append(f"    /** The {substrate} substrate. */")
        lines.append(f"    val {substrate.capitalize()}: Map<String, Color> = mapOf(")
        for name, spec in roles["roles"].items():
            value = resolve(spec[substrate], tokens, surfaces)
            lines.append(f'        "{name}" to Color(0xFF{value[1:]}),')
        lines.append("    )")
        lines.append("")
    lines.append("    /** The role, in the substrate the theme is in. */")
    lines.append("    fun of(substrate: String, role: String): Color =")
    lines.append('        (if (substrate == "dark") Dark else Light)[role]')
    lines.append("        ?: error(\"the contract has no role named $role\")")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def outputs(roles: dict, tokens: dict, surfaces: dict) -> dict:
    return {
        WEB: render_web(roles),
        NATIVE: render_rust(roles),
        ANDROID: render_kotlin(roles, tokens, surfaces),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="project the semantic role layer")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    roles, tokens, surfaces = load()
    failures = problems(roles, tokens, surfaces) + readings(roles, tokens, surfaces)
    if failures:
        print(f"FAIL: {len(failures)} problem(s) with the role layer")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    for path, text in outputs(roles, tokens, surfaces).items():
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
            continue
        if not path.is_file():
            print(f"FAIL: {path.relative_to(ROOT)} does not exist")
            return 1
        if path.read_text(encoding="utf-8") != text:
            print(f"FAIL: {path.relative_to(ROOT)} is not what the roles project")
            return 1

    if args.write:
        return 0
    print(f"PASS: the role layer projects cleanly ({len(roles['roles'])} roles, "
          f"{len(READS)} pairings legible on both substrates)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
