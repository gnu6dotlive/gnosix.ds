#!/usr/bin/env python3
"""Project the component specification into the web profile.

`profiles/web/components.css` used to be written by hand, which meant the
styles a consumer shipped and the contract behind them were two things
that could disagree. This renders the stylesheet from core/COMPONENTS.json
instead, so the styles are a projection of the contract rather than a copy
of it.

    python3 tools/project_components.py --write
    python3 tools/project_components.py --check

The base of the profile - the font, the resets, the reduced-motion
respect - is the target's own and stays in the profile. What is generated
is the part the contract states: the four components, their states, their
geometry and the accessibility they owe.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "core/COMPONENTS.json"
OUT = ROOT / "profiles/web/components.css"

# The target's base. Not part of the contract: it is what a web profile
# does about fonts, resets and motion preferences.
BASE = '''@import url("./tokens.css");
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
  color: var(--gnosix-neutral-anthracite);
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


def css_var(token: str | None) -> str | None:
    """A token's custom property, from the way the token is named."""
    if not token or token == "inherit":
        return None
    if token.startswith("weight/"):
        return f"var(--gnosix-weight-{token.split('/', 1)[1]})"
    family, _, shade = token.partition("/")
    return f"var(--gnosix-{kebab(family)}-{kebab(shade)})"


def length(value: dict) -> str:
    """A length, as the specification states it."""
    if "px" in value:
        return f"{value['px']}px"
    if "em" in value:
        return f"{value['em']}em"
    if "number" in value:
        return str(value["number"])
    raise ValueError(f"a length with no unit: {value}")


def render(spec: dict) -> str:
    parts = [BASE]
    components = spec["components"]

    # --- the action -----------------------------------------------------
    action = components["action"]
    tokens = action["tokens"]
    geometry = action["geometry"]
    ring = action["a11y"]["focus-ring"]
    parts.append(f"""
.gnosix-action {{
  min-height: {length(geometry['min-height'])};
  padding: {geometry['padding']['block']} {geometry['padding']['inline']};
  border: 1px solid {"transparent" if not tokens.get("border") else css_var(tokens["border"])};
  border-radius: {length(geometry['radius'])};
  background: {css_var(tokens["background"])};
  color: {css_var(tokens["text"])};
  cursor: pointer;
  font-weight: {css_var("weight/" + action["typography"]["weight"])};
}}

.gnosix-action:disabled {{
  cursor: not-allowed;
  opacity: .55;
}}

.gnosix-action:focus-visible,
.gnosix-input:focus-visible {{
  outline: {length(ring["width"])} solid {css_var(ring["token"])};
  outline-offset: {length(ring["offset"])};
}}
""")

    # --- the input ------------------------------------------------------
    field = components["input"]
    tokens = field["tokens"]
    geometry = field["geometry"]
    parts.append(f"""
.gnosix-input {{
  padding: {geometry['padding']['all']};
  border: {length(geometry['border-width'])} solid {css_var(tokens["border"])};
  border-radius: {length(geometry["radius"])};
  background: {css_var(tokens["background"])};
  color: inherit;
}}
""")

    # --- the state ------------------------------------------------------
    state = components["state"]
    mark = state["mark"]
    geometry = state["geometry"]
    parts.append(f"""
.gnosix-state {{
  display: flex;
  gap: {length(geometry["gap"])};
  align-items: baseline;
  line-height: {length(geometry["line-height"])};
}}

.gnosix-state::before {{
  width: {length(mark["diameter"])};
  height: {length(mark["diameter"])};
  border-radius: 50%;
  background: {css_var(mark["by-state"]["stable"])};
  content: "";
  flex: 0 0 auto;
}}

.gnosix-state[data-status="pending"]::before {{
  background: {css_var(mark["by-state"]["pending"])};
}}

.gnosix-state[data-status="attention"]::before {{
  background: {css_var(mark["by-state"]["attention"])};
}}
""")

    # --- motion ---------------------------------------------------------
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
    """Every token the contract has, named the way the specification names them."""
    tokens = json.loads((ROOT / "core/TOKENS.json").read_text(encoding="utf-8"))
    out = set()
    for family, ramp in tokens["color"].items():
        for shade in ramp:
            out.add(f"{family}/{shade}")
    for step in tokens.get("spacing", {}):
        out.add(f"spacing/{step}")
    for role, weight in tokens.get("typography", {}).get("weights", {}).items():
        out.add(f"weight/{role}")
    return out


def missing_tokens(spec: dict) -> list[str]:
    """The tokens a component names that the contract does not have.

    A component that names a token the contract does not have would project
    a custom property that resolves to nothing, and the surface would fall
    back to whatever the cascade gives it - the same quiet failure the
    surface layer had.
    """
    known = known_tokens()
    missing = []

    def check(where: str, value):
        if isinstance(value, str) and "/" in value and not value.startswith("http"):
            if value not in known and not value.startswith("weight/"):
                missing.append(f"{where}: {value}")

    for name, component in spec["components"].items():
        for role, token in (component.get("tokens") or {}).items():
            check(f"{name}.tokens.{role}", token)
        mark = component.get("mark") or {}
        for state, token in (mark.get("by-state") or {}).items():
            check(f"{name}.mark.{state}", token)
        ring = (component.get("a11y") or {}).get("focus-ring") or {}
        check(f"{name}.a11y.focus-ring", ring.get("token"))
    return missing


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

    problems = missing_tokens(spec)
    if problems:
        print(f"FAIL: {len(problems)} token(s) a component names that the contract does not have")
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
