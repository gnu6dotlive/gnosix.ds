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
from oklch import (contrast_ratio, hex_to_rgb, rgb_to_oklch, oklch_to_rgb,  # noqa: E402
                    rgb_to_hex)

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


# A surface takes the ink of the substrate it belongs to, and a substrate is
# a question of lightness: a step darker than the middle belongs to the dark
# substrate, a step lighter than it belongs to the light one. The substrate
# therefore follows the value, the way the hue follows the family.
MIDDLE = 0.3

# A hairline is a graphic, not text: 3:1 against the substrate it sits on.
HAIRLINE_MINIMUM = 3.0
# Body text: 4.5:1.
INK_MINIMUM = 4.5


# A surface takes the ink of the substrate it belongs to, and the substrate
# comes from the family: the dark family sits on the dark substrate and
# takes the light ink, and the light family takes the dark ink. The ink is
# lighter or darker than the surface it is named for - that is what makes
# it an ink.
#
# A hairline is the one case where the substrate follows the value: a line
# is on the substrate it contrasts with, so a light line is on the dark
# substrate and a dark one is on the light.
MIDDLE = 0.3

# A hairline is a graphic, not text: 3:1 against the substrate it sits on.
HAIRLINE_MINIMUM = 3.0
# Body text: 4.5:1.
INK_MINIMUM = 4.5


def is_dark(value: str) -> bool:
    from oklch import rgb_to_oklch
    lightness, _, _ = rgb_to_oklch(hex_to_rgb(value))
    return lightness < MIDDLE


def _base_of(families: dict, family: str, darkest: bool):
    """The base of a substrate: the darkest dark surface, the lightest light one."""
    steps = families.get(family, {}).get("steps", [])
    if not steps:
        return None
    return (min if darkest else max)(
        steps, key=lambda s: rgb_to_oklch(hex_to_rgb(s["value"]))[0])


def legibility(document: dict) -> list[str]:
    """Every surface takes a legible ink, and every hairline its own substrate.

    A surface without a legible ink is a hole in the system: the designer has
    nothing to put on it that passes. A hairline that does not reach 3:1
    against the substrate it is for is a line nobody can see.
    """
    problems: list[str] = []
    families = document.get("families", {})

    # The palette is part of the system, so its colours are candidate inks
    # as well as the layer's own steps. The strongest ink on a substrate is
    # often the palette's, and a check that only looked at the layer would
    # call a legible surface illegible.
    tokens = json.loads((ROOT / "core/TOKENS.json").read_text(encoding="utf-8"))
    palette = []
    for ramp in tokens["color"].values():
        for value in ramp.values():
            palette.append({"id": "token", "value": value.upper()})

    for surface_family, ink_family in (("surface-dark", "ink-on-dark"),
                                       ("surface-light", "ink-on-light")):
        inks = list(families.get(ink_family, {}).get("steps", []))
        # The palette's own strong inks belong to the substrate they read on.
        strong = [c for c in palette
                  if (c["value"] == tokens["color"]["neutral"]["shellWhite"].upper()
                      and ink_family == "ink-on-dark")
                  or (c["value"] == tokens["color"]["neutral"]["anthracite"].upper()
                      and ink_family == "ink-on-light")]
        inks += strong
        for step in families.get(surface_family, {}).get("steps", []):
            if not inks:
                problems.append(f"{step['id']}: the {ink_family} family is empty")
                continue
            best = max(inks, key=lambda i: contrast_ratio(
                hex_to_rgb(i["value"]), hex_to_rgb(step["value"])))
            got = contrast_ratio(hex_to_rgb(best["value"]), hex_to_rgb(step["value"]))
            if got < INK_MINIMUM:
                problems.append(
                    f"{step['id']}: the best ink is {best['id']} at {round(got, 2)}, "
                    f"under {INK_MINIMUM}")

    # A hairline is a graphic, and it is seen against one substrate or the
    # other: a light line on the dark substrate, a dark line on the light
    # one. Which is which is a fact about where it is used, not something
    # its own lightness settles - a hairline at the middle of the ramp is
    # neither. So the check is the one that holds either way: a hairline
    # must reach 3:1 against the base of at least one of the two
    # substrates, or it is a line nobody can see.
    dark_base = _base_of(families, "surface-dark", darkest=True)
    light_base = _base_of(families, "surface-light", darkest=False)
    for step in families.get("hairline", {}).get("steps", []):
        if dark_base is None or light_base is None:
            continue
        on_dark = contrast_ratio(hex_to_rgb(step["value"]), hex_to_rgb(dark_base["value"]))
        on_light = contrast_ratio(hex_to_rgb(step["value"]), hex_to_rgb(light_base["value"]))
        if max(on_dark, on_light) < HAIRLINE_MINIMUM:
            problems.append(
                f"{step['id']}: {round(max(on_dark, on_light), 2)} against the nearest "
                f"substrate, under {HAIRLINE_MINIMUM}")

    return problems


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

    problems.extend(legibility(document))
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
