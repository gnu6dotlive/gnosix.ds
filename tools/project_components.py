#!/usr/bin/env python3
"""Project the component specification into the web profile.

`profiles/web/components.css` used to be written by hand, which meant the
styles a consumer shipped and the contract behind them were two things
that could disagree. It is now rendered from `core/COMPONENTS.json`.

The renderer is generic. It used to carry one hand-written block of CSS
per component, which meant that every component added to the contract
needed a new special case here, and a design system whose projection
grows a special case per component is a design system whose projection
cannot be trusted. A component now states what it is made of, and this
walks the statements.

A component states:

  tokens       the roles it wears: background, text, border, and
               optionally mark for the pip that carries a state
  geometry     its radius, its minimum height, its padding, its gap
  typography   its weight, its size, its line height
  variants     the roles it plays, and the tokens it wears in each
  states       what happens to it, and the pseudo-class that says so
  parts        the elements it is made of, when it is more than one
  a11y         the focus ring it owes, and the target it must reach

    python3 tools/project_components.py --write
    python3 tools/project_components.py --check
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from oklch import contrast_ratio, hex_to_rgb  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# Running this file as a script puts tools/ on sys.path, not the package
# root, so `from tools.project_roles import ...` fails with a
# ModuleNotFoundError. Putting the package root on the path first makes
# both forms work, the same way tools/rebuild_manifest.py does it.
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

SPEC = ROOT / "core/COMPONENTS.json"
ROLES = ROOT / "core/ROLES.json"
OUT = ROOT / "profiles/web/components.css"

# The target's base. Not part of the contract: it is what a web profile
# does about fonts, resets and motion preferences.
BASE = '''@import url("./tokens.css");
@import url("./roles.css");
@import url("./icons.css");

@font-face {
  font-family: "Space Grotesk";
  src: url("../../assets/fonts/SpaceGrotesk-wght.woff2") format("woff2");
  font-style: normal;
  font-weight: 300 700;
  font-display: swap;
}

:root {
  font-family: var(--gnosix-font-primary);
  color: var(--gnosix-ink);
  background: var(--gnosix-surface);
  font-synthesis: none;
}

body,
button,
input,
textarea,
select,
code,
kbd,
samp,
pre {
  font-family: var(--gnosix-font-primary);
}

code,
kbd,
samp,
pre,
.gnosix-system {
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum" 1;
  letter-spacing: .02em;
}

button,
input,
textarea,
select {
  font: inherit;
}
'''


def words(name: str) -> list[str]:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name).split()


def kebab(name: str) -> str:
    return "-".join(part.lower() for part in words(name))


def role_var(name: str | None) -> str | None:
    """A role, as the custom property that carries it."""
    if not name or name in ("inherit", "transparent", "none"):
        return name
    return f"var(--gnosix-{kebab(name)})"


def length(value) -> str | None:
    """A length, as the specification states it."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if "step" in value:
        return f"var(--gnosix-radius-{value['step']})"
    if "px" in value:
        return f"{value['px']}px"
    if "em" in value:
        return f"{value['em']}em"
    if "number" in value:
        return str(value["number"])
    raise ValueError(f"a length with no unit: {value}")


def token_properties(tokens: dict) -> list[tuple[str, str]]:
    """The declarations a set of tokens states."""
    out = []
    background = tokens.get("background")
    if background:
        out.append(("background", role_var(background)))
    text = tokens.get("text")
    if text:
        out.append(("color", role_var(text)))
    border = tokens.get("border")
    if border:
        out.append(("border-color", role_var(border)))
    return out


def geometry_properties(geometry: dict) -> list[tuple[str, str]]:
    """The declarations a set of geometry states."""
    out = []
    radius = length(geometry.get("radius"))
    if radius:
        out.append(("border-radius", radius))
    minimum = length(geometry.get("min-height"))
    if minimum:
        out.append(("min-height", minimum))
    padding = geometry.get("padding")
    if padding:
        if "all" in padding:
            out.append(("padding", length(padding["all"])))
        else:
            out.append(("padding",
                        f"{length(padding.get('block'))} {length(padding.get('inline'))}"))
    gap = length(geometry.get("gap"))
    if gap:
        out.append(("gap", gap))
    size = length(geometry.get("size"))
    if size:
        out.append(("width", size))
        out.append(("height", size))
    width = length(geometry.get("width"))
    if width:
        out.append(("width", width))
    height = length(geometry.get("height"))
    if height:
        out.append(("height", height))
    return out


def typography_properties(typography: dict) -> list[tuple[str, str]]:
    """The declarations a set of typography states."""
    out = []
    weight = typography.get("weight")
    if weight:
        out.append(("font-weight", f"var(--gnosix-weight-{weight})"))
    size = length(typography.get("size"))
    if size:
        out.append(("font-size", size))
    leading = length(typography.get("line-height"))
    if leading:
        out.append(("line-height", leading))
    return out


def declaration_block(pairs: list[tuple[str, str]]) -> str:
    body = "".join(f"  {name}: {value};\n" for name, value in pairs if value)
    return "{\n" + body + "}"


def render_component(name: str, component: dict) -> str:
    parts = component.get("parts") or [{"name": "root", "class": f"gnosix-{kebab(name)}"}]
    tokens = component.get("tokens") or {}
    geometry = component.get("geometry") or {}
    typography = component.get("typography") or {}
    ring = (component.get("a11y") or {}).get("focus-ring") or {}
    variants = component.get("variants") or []
    states = component.get("states") or []

    out = []
    for part in parts:
        cls = part["class"]
        part_tokens = part.get("tokens", tokens)
        part_geometry = part.get("geometry", geometry)
        part_typography = part.get("typography", typography)

        pairs = token_properties(part_tokens) + geometry_properties(part_geometry) \
            + typography_properties(part_typography)
        if part.get("border-width"):
            pairs.insert(0, ("border", f"{length(part['border-width'])} solid "
                                       f"{role_var(part_tokens.get('border') or 'hairline')}"))
        elif part_tokens.get("border"):
            pairs.append(("border", "1px solid " + role_var(part_tokens["border"])))
        else:
            pairs.append(("border", "1px solid transparent"))

        out.append(f"\n.{cls} {declaration_block(pairs)}")

        mark = part_tokens.get("mark")
        if mark:
            out.append(f"\n.{cls}::before {declaration_block([('background', role_var(mark))])}")

        if ring:
            out.append(
                f"\n.{cls}:focus-visible {declaration_block([('outline', f'{length(ring['width'])} solid {role_var(ring['role'])}'), ('outline-offset', length(ring['offset']))])}")

        for variant in variants:
            variant_tokens = variant.get("tokens") or {}
            properties = token_properties(variant_tokens)
            if variant_tokens.get("mark"):
                properties.append(("background", role_var(variant_tokens["mark"])))
            if variant.get("geometry"):
                properties += geometry_properties(variant["geometry"])
            if not properties:
                continue
            out.append(f'\n.{cls}[data-variant="{variant["name"]}"] '
                       f"{declaration_block(properties)}")

        for state in states:
            pseudo = state.get("pseudo")
            if not pseudo:
                continue
            overrides = state.get("overrides") or {}
            if not overrides:
                continue
            out.append(f"\n.{cls}{pseudo} {declaration_block(list(overrides.items()))}")

    return "".join(out)


def render(spec: dict) -> str:
    parts = [BASE]
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
    return "".join(parts)


def known_tokens() -> set[str]:
    """Every token the contract has, and every role it binds."""
    tokens = json.loads((ROOT / "core/TOKENS.json").read_text(encoding="utf-8"))
    out = set()
    for family, ramp in tokens["color"].items():
        for shade in ramp:
            out.add(f"{family}/{shade}")
    surfaces = json.loads((ROOT / "core/SURFACES.json").read_text(encoding="utf-8"))
    for spec in surfaces.get("families", {}).values():
        for step in spec["steps"]:
            out.add(step["id"])
    for accent in surfaces.get("accents", []):
        out.add(accent["id"])
    for step in tokens.get("spacing", {}):
        out.add(f"spacing/{step}")
    for role, weight in tokens.get("typography", {}).get("weights", {}).items():
        out.add(f"weight/{role}")
    roles = json.loads(ROLES.read_text(encoding="utf-8"))
    for role in roles["roles"]:
        out.add(role)
    return out


def missing_tokens(spec: dict) -> list[str]:
    """The tokens and roles a component names that the contract does not have.

    A component that names a token the contract does not have would project
    a custom property that resolves to nothing, and the surface would fall
    back to whatever the cascade gives it - the same quiet failure the
    surface layer had.
    """
    known = known_tokens()
    tokens = json.loads((ROOT / "core/TOKENS.json").read_text(encoding="utf-8"))
    radius_steps = set(tokens.get("radius") or {})
    missing = []

    def check_tokens(where: str, tokens: dict):
        for role, token in (tokens or {}).items():
            # A null token means the thing has none of it, which is a
            # decision and not a gap.
            if token is None or token in ("inherit", "transparent", "none"):
                continue
            if token in known:
                continue
            missing.append(f"{where}.{role}: {token}")

    for name, component in spec["components"].items():
        check_tokens(f"{name}.tokens", component.get("tokens") or {})
        for variant in component.get("variants") or []:
            check_tokens(f"{name}.variants.{variant['name']}.tokens", variant.get("tokens") or {})
        for part in component.get("parts") or []:
            check_tokens(f"{name}.parts.{part.get('name')}.tokens", part.get("tokens") or {})
        ring = (component.get("a11y") or {}).get("focus-ring") or {}
        if ring.get("role") and ring["role"] not in known:
            missing.append(f"{name}.a11y.focus-ring: {ring['role']}")
        # A radius is a step of the scale, not a number written in the
        # component. A number there is a radius the system does not have,
        # and it is the same drift the field's radii show: every surface
        # rounding itself on its own.
        for where, geometry in [(name, component.get("geometry") or {})] + [
                (f"{name}.parts.{part.get('name')}", part.get("geometry") or {})
                for part in component.get("parts") or []]:
            radius = geometry.get("radius")
            if not isinstance(radius, dict):
                continue
            if "step" in radius:
                if radius["step"] not in radius_steps:
                    missing.append(f"{where}.radius: the step "
                                   f"{radius['step']!r} is not one of the "
                                   f"scale's")
            elif "px" in radius:
                missing.append(f"{where}.radius: {radius['px']}px is a "
                               f"number, not a step of the scale")
    return missing


def read_of(spec: dict) -> list[str]:
    """The variants whose text does not read on their own background.

    A variant is a promise that a thing will be legible in a certain
    state. The role layer says what a role is worth on each substrate;
    this says whether the two things the variant names can be read
    together. A transparent background is read against the substrate.
    """
    from tools.project_roles import load as load_roles
    from tools.project_roles import resolve

    roles, tokens, surfaces = load_roles()
    role_tokens = {name: spec.get("light") for name, spec in roles["roles"].items()}

    def value_of(reference: str) -> str | None:
        if reference in ("transparent", "none", "inherit"):
            return None
        if reference in role_tokens:
            reference = role_tokens[reference]
        return resolve(reference, tokens, surfaces)

    problems = []
    for name, component in spec["components"].items():
        for variant in component.get("variants") or []:
            tokens_of = variant.get("tokens") or {}
            background = value_of(tokens_of.get("background") or "")
            text = value_of(tokens_of.get("text") or "")
            if not text:
                continue
            if not background:
                # Transparent: the text sits on the surface of the page.
                background = value_of("surface")
            if not background:
                continue
            ratio = contrast_ratio(hex_to_rgb(text), hex_to_rgb(background))
            if ratio + 1e-9 < 4.5:
                problems.append(f"{name}.{variant['name']}: the text measures "
                                f"{ratio:.2f} on its own background, below 4.5")
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="project the component specification")
    parser.add_argument("--write", action="store_true", help="write the stylesheet")
    parser.add_argument("--check", action="store_true", help="verify the stylesheet is current")
    args = parser.parse_args(argv)

    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    stylesheet = render(spec)

    if args.write:
        OUT.write_text(stylesheet, encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}")
        return 0

    problems = missing_tokens(spec) + read_of(spec)
    if problems:
        print(f"FAIL: {len(problems)} problem(s) with the component specification")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    if not OUT.exists():
        print(f"FAIL: {OUT.relative_to(ROOT)} does not exist")
        return 1
    if OUT.read_text(encoding="utf-8") != stylesheet:
        print(f"FAIL: {OUT.relative_to(ROOT)} is not what the specification projects")
        return 1
    print(f"PASS: the stylesheet is what the specification projects "
          f"({len(spec['components'])} components)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
