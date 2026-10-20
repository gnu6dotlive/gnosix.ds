"""The surface layer: derive it, check it, and publish it as CSS.

core/SURFACES.json states the surfaces, the inks and the hairlines that the
palette in core/TOKENS.json does not contain. Each step gives its lightness
and its chroma; the hue comes from the family's base token, so a step cannot
drift out of the palette's family without the check noticing.

    python3 tools/surfaces.py --check     # the gate
    python3 tools/surfaces.py --css       # the custom properties
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oklch import hex_to_rgb, rgb_to_oklch, oklch_to_rgb, rgb_to_hex  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SURFACES = ROOT / "core/SURFACES.json"
TOKENS = ROOT / "core/TOKENS.json"

# How far a step's hue may sit from its family's base before it has left the
# family. Wide enough for the rounding of a hand-chosen chroma, tight enough
# to catch a colour that was borrowed from somewhere else.
HUE_TOLERANCE = 30.0


def load() -> dict:
    return json.loads(SURFACES.read_text(encoding="utf-8"))


def token_values() -> dict[str, str]:
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    out = {}
    for family, ramp in tokens["color"].items():
        for shade, value in ramp.items():
            out[f"{family}/{shade}"] = value.upper()
    return out


def every_step(document: dict):
    for family, spec in document.get("families", {}).items():
        for step in spec.get("steps", []):
            yield family, spec, step
    for accent in document.get("accents", []):
        yield "accents", {"base": None}, accent


def check(document: dict) -> list[str]:
    problems: list[str] = []
    tokens = token_values()
    base_hue = {name: rgb_to_oklch(hex_to_rgb(value))[2]
                for name, value in tokens.items()}

    for family, spec, step in every_step(document):
        name = step.get("id", "?")
        declared = step.get("value", "").upper()
        lightness = step.get("lightness")
        chroma = step.get("chroma")
        hue = step.get("hue")
        if None in (lightness, chroma, hue):
            problems.append(f"{name}: the step does not state its lightness, chroma and hue")
            continue

        computed = rgb_to_hex(oklch_to_rgb(lightness, chroma, hue)).upper()
        if computed != declared:
            problems.append(f"{name}: declares {declared}, its lightness and chroma give {computed}")

        neutral_max = document.get("derivation", {}).get("neutral_chroma_max", 0.008)
        if chroma < neutral_max:
            continue
        if family == "accents":
            # A deliberate tint: it is declared, named and given a role, and
            # it is not pretending to be a neutral.
            continue
        base = spec.get("base")
        if base not in base_hue:
            problems.append(f"{name}: its family names no base token ({base})")
            continue
        distance = abs((hue - base_hue[base] + 180) % 360 - 180)
        if distance > HUE_TOLERANCE:
            problems.append(
                f"{name}: its hue {hue:.1f} is {distance:.1f} degrees from {base}'s "
                f"{base_hue[base]:.1f}, so it has left the family")

    return problems


def css(document: dict) -> str:
    """The custom properties the web projection and the site both use."""
    rows = []
    for family, spec in document.get("families", {}).items():
        for step in spec.get("steps", []):
            rows.append(f"  --gnosix-{step['id']}: {step['value'].upper()};")
    for accent in document.get("accents", []):
        rows.append(f"  --gnosix-{accent['id']}: {accent['value'].upper()};")
    return "\n".join(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="the surface layer")
    parser.add_argument("--check", action="store_true", help="verify the layer against its own derivation")
    parser.add_argument("--css", action="store_true", help="print the custom properties")
    args = parser.parse_args(argv)

    document = load()
    if args.css:
        print(css(document))
        return 0

    problems = check(document)
    if problems:
        print(f"FAIL: {len(problems)} problem(s) in the surface layer")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    total = sum(1 for _ in every_step(document))
    print(f"PASS: the surface layer holds ({total} surfaces)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
