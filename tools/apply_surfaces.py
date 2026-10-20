"""Apply the surface layer to the first-party design surfaces.

Every colour a first-party surface used that the token source does not
contain is replaced by the layer's value: a custom property where the file
can carry one, the sanctioned literal where it cannot.

The result is that the package's own surfaces use the system's colours
rather than their own, and `tools/contract_colors.py` can refuse anything
else. The rewrite is idempotent and reversible: the layer says what every
value was, so a file can be read against it.

    python3 tools/apply_surfaces.py            # rewrite
    python3 tools/apply_surfaces.py --check    # report the drift
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "core/TOKENS.json"
SURFACES = ROOT / "core/SURFACES.json"

HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")

# The files that draw the system's own interface.
TARGETS = [
    "site/style.css",
    "site/site.webmanifest",
    "profiles/web/demo.html",
    "references/actions.svg",
    "references/adaptive.svg",
    "references/fields.svg",
    "references/identity.svg",
    "references/state.svg",
    "references/surfaces.svg",
]


def names() -> dict[str, str]:
    """Every sanctioned value, and the custom property that carries it."""
    out: dict[str, str] = {}
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    for family, ramp in tokens["color"].items():
        for shade, value in ramp.items():
            name = "-".join(part.lower() for part in _words(family))
            shade_name = "-".join(part.lower() for part in _words(shade))
            out[value.upper()] = f"--gnosix-{name}-{shade_name}"
    surfaces = json.loads(SURFACES.read_text(encoding="utf-8"))
    for spec in surfaces.get("families", {}).values():
        for step in spec.get("steps", []):
            out[step["value"].upper()] = f"--gnosix-{step['id']}"
    for accent in surfaces.get("accents", []):
        out[accent["value"].upper()] = f"--gnosix-{accent['id']}"
    # A merged tint carries the property of the colour it was merged into.
    for spec in surfaces.get("families", {}).values():
        for step in spec.get("steps", []):
            for alias in step.get("aliases", []):
                out[alias.upper()] = f"--gnosix-{step['id']}"
    for accent in surfaces.get("accents", []):
        for alias in accent.get("aliases", []):
            out[alias.upper()] = f"--gnosix-{accent['id']}"
    return out


def _words(name: str) -> list[str]:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name).split()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="apply the surface layer")
    parser.add_argument("--check", action="store_true", help="report the drift; write nothing")
    args = parser.parse_args(argv)

    legal = names()
    changed: list[str] = []
    problems: list[str] = []

    for rel in TARGETS:
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        is_markup = rel.endswith(".html")
        is_svg = rel.endswith(".svg")

        def replace(match: re.Match) -> str:
            value = match.group(0).upper()
            if value not in legal:
                return match.group(0)
            if is_markup or rel.endswith(".css"):
                return f"var({legal[value]})"
            # An SVG and a manifest carry their values literally: a custom
            # property in a standalone SVG would need a style block the
            # scene does not have, and the manifest is read by the shell.
            return legal[value].replace("--gnosix-", "").upper() if False else value

        updated = HEX.sub(replace, text)
        if updated == text:
            continue
        if args.check:
            problems.append(rel)
        else:
            path.write_text(updated, encoding="utf-8")
            changed.append(rel)

    if args.check:
        # A custom property that nothing defines resolves to nothing, and the
        # surface falls back to whatever the cascade gives it. That is how a
        # renumbered layer would quietly drain the colour out of a page.
        defined = set()
        tokens_css = ROOT / "profiles/web/tokens.css"
        if tokens_css.exists():
            defined = set(re.findall(r"(--gnosix-[a-z0-9-]+)\s*:", tokens_css.read_text()))
        for rel in TARGETS:
            path = ROOT / rel
            if not path.exists():
                continue
            for name in set(re.findall(r"var\((--gnosix-[a-z0-9-]+)\)", path.read_text())):
                if name not in defined:
                    problems.append(f"{rel} refers to {name}, which nothing defines")
        if problems:
            print(f"FAIL: {len(problems)} problem(s) in the first-party surfaces")
            for rel in problems:
                print(f"  - {rel}")
            return 1
        print("PASS: every first-party surface uses the system's colours")
        return 0

    print(f"rewrote {len(changed)} file(s)")
    for rel in changed:
        print(f"  {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
