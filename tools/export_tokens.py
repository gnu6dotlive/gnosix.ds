#!/usr/bin/env python3
"""Export the token source in the formats other tools speak.

The package states its tokens in a JSON of its own, and the web, the Android
and the native profiles project it from there. That makes the system
portable between the tools that read *those* profiles, and not between the
tools that read tokens: a Tailwind config, a Style Dictionary build or a
design-token pipeline cannot read core/TOKENS.json without being told how.

Two exports close that, and both are generated from the one source:

  gnosix.tokens.json             the W3C Design Tokens Community Group format
  gnosix.style-dictionary.json   the Style Dictionary source format

Neither is a second palette. They are the same values, reshaped for a
consumer that already knows how to read them.

    python3 tools/export_tokens.py --write
    python3 tools/export_tokens.py --check
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "core/TOKENS.json"
SURFACES = ROOT / "core/SURFACES.json"
OUT = ROOT / "profiles/interchange"

DTCG = OUT / "gnosix.tokens.json"
STYLE_DICTIONARY = OUT / "gnosix.style-dictionary.json"

DTCG_SCHEMA = "https://design-tokens.github.io/community-group/format/"


def words(name: str) -> list[str]:
    import re
    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name).split()


def kebab(name: str) -> str:
    return "-".join(part.lower() for part in words(name))


def dtcg(tokens: dict, surfaces: dict) -> dict:
    """The token source in the Design Tokens Community Group format."""
    colour = {}
    for family, ramp in tokens["color"].items():
        colour[kebab(family)] = {
            kebab(shade): {"$type": "color", "$value": value.upper()}
            for shade, value in ramp.items()
        }
    surface = {}
    for spec in surfaces.get("families", {}).values():
        for step in spec["steps"]:
            surface[step["id"]] = {"$type": "color", "$value": step["value"].upper()}
    for accent in surfaces.get("accents", []):
        surface[accent["id"]] = {"$type": "color", "$value": accent["value"].upper()}

    typography = tokens.get("typography", {})
    font_family = {
        role: {"$type": "fontFamily", "$value": stack}
        for role, stack in typography.items()
        if isinstance(stack, list)
    }
    font_weight = {
        role: {"$type": "fontWeight", "$value": int(value)}
        for role, value in typography.get("weights", {}).items()
    }
    space = {
        step: {"$type": "dimension", "$value": f"{value}px"}
        for step, value in tokens.get("spacing", {}).items()
    }
    return {
        "$schema": DTCG_SCHEMA,
        "gnosix": {
            "color": colour,
            "surface": surface,
            "fontFamily": font_family,
            "fontWeight": font_weight,
            "space": space,
        },
    }


def style_dictionary(tokens: dict, surfaces: dict) -> dict:
    """The token source in the Style Dictionary source format."""
    colour = {}
    for family, ramp in tokens["color"].items():
        colour[kebab(family)] = {
            kebab(shade): {"value": value.upper(), "type": "color"}
            for shade, value in ramp.items()
        }
    surface = {}
    for spec in surfaces.get("families", {}).values():
        for step in spec["steps"]:
            surface[step["id"]] = {"value": step["value"].upper(), "type": "color"}
    for accent in surfaces.get("accents", []):
        surface[accent["id"]] = {"value": accent["value"].upper(), "type": "color"}

    typography = tokens.get("typography", {})
    font_family = {
        role: {"value": stack, "type": "fontFamily"}
        for role, stack in typography.items()
        if isinstance(stack, list)
    }
    font_weight = {
        role: {"value": int(value), "type": "fontWeight"}
        for role, value in typography.get("weights", {}).items()
    }
    space = {
        step: {"value": f"{value}px", "type": "dimension"}
        for step, value in tokens.get("spacing", {}).items()
    }
    return {
        "color": colour,
        "surface": surface,
        "fontFamily": font_family,
        "fontWeight": font_weight,
        "space": space,
    }


def render(document: dict) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="export the tokens in the standard formats")
    parser.add_argument("--write", action="store_true", help="write the exports")
    parser.add_argument("--check", action="store_true", help="verify the exports are current")
    args = parser.parse_args(argv)

    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    surfaces = json.loads(SURFACES.read_text(encoding="utf-8")) if SURFACES.is_file() else {}
    exports = {
        DTCG: render(dtcg(tokens, surfaces)),
        STYLE_DICTIONARY: render(style_dictionary(tokens, surfaces)),
    }

    if args.write:
        OUT.mkdir(parents=True, exist_ok=True)
        for path, text in exports.items():
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
        return 0

    problems = []
    for path, text in exports.items():
        if not path.is_file():
            problems.append(f"{path.relative_to(ROOT)} does not exist")
        elif path.read_text(encoding="utf-8") != text:
            problems.append(f"{path.relative_to(ROOT)} is not what the token source gives")
    if problems:
        print(f"FAIL: {len(problems)} export(s) out of date")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"PASS: the exports match the token source ({len(exports)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
