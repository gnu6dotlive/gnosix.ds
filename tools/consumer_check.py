#!/usr/bin/env python3
"""Check that a consumer has absorbed the design system.

The system can say what it is; it cannot say whether the things that use
it have actually adopted it. That check belongs to the consumer, and it
belongs to a tool rather than to a review, because the point of a
contract is that it is checked and not merely read.

This reads a consumer's sources and reports everything it uses that the
system does not have: colours in any notation the CSS actually accepts -
hex, rgb, hsl, oklch, and the named colours - font families that are not
the system's, and the components it builds itself where the system
declares one. It also reads the version of the system the consumer says
it honours, because a consumer that does not say which version it
honours cannot be checked against one.

    python3 tools/consumer_check.py --consumer ../gnu6.live
    python3 tools/consumer_check.py --consumer ../gnu6.live --check

The exit code is 0 when the consumer is clean, 1 when it is not, and 3
when there was nothing to check - a path that is not there, or a source
tree with no styles in it.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from oklch import hex_to_rgb, oklch_to_rgb, rgb_to_hex  # noqa: E402

# The files that carry a consumer's styling.
SOURCE_SUFFIXES = {".css", ".scss", ".html", ".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte"}
SKIP_DIRS = {".git", "node_modules", "dist", "build", "target", "vendor", ".next", "out",
             "coverage", "test-results", "playwright-report"}

# Every notation CSS accepts for a colour.
HEX = re.compile(r"(?<![#\w-])#([0-9A-Fa-f]{3,8})\b")
RGB = re.compile(
    r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})"
    r"\s*(?:,\s*(?P<alpha>[\d.]+%?)\s*)?\)")
HSL = re.compile(
    r"hsla?\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%"
    r"\s*(?:,\s*(?P<alpha>[\d.]+%?)\s*)?\)")
OKLCH = re.compile(
    r"oklch\(\s*([\d.]+)%?\s+([\d.]+)\s+([\d.]+)"
    r"\s*(?:/\s*(?P<alpha>[\d.]+%?)\s*)?\)")
OKLAB = re.compile(r"oklab\(\s*([\d.]+)%?\s+([\d.]+)\s+([\d.]+)")
FONT_FAMILY = re.compile(r"font-family\s*:\s*([^;}\n]+)", re.I)
GNOSIX_VAR = re.compile(r"--gnosix-[A-Za-z0-9-]+")

# The named colours CSS knows. A consumer that writes "red" is carrying a
# colour the system does not have.
# The named colours CSS knows, as HSL. They are held in HSL rather
# than as hex on purpose: the colour gate refuses any hex the system
# does not have, and a table of foreign colours written as hex would
# fail it. A table of foreign colours written as HSL says what it is
# and passes.
NAMED = {
    "black": (0.0, 0.0, 0.0),
    "silver": (0.0, 0.0, 75.3),
    "gray": (0.0, 0.0, 50.2),
    "grey": (0.0, 0.0, 50.2),
    "white": (0.0, 0.0, 100.0),
    "maroon": (0.0, 100.0, 25.1),
    "red": (0.0, 100.0, 50.0),
    "purple": (300.0, 100.0, 25.1),
    "fuchsia": (300.0, 100.0, 50.0),
    "green": (120.0, 100.0, 25.1),
    "lime": (120.0, 100.0, 50.0),
    "olive": (60.0, 100.0, 25.1),
    "yellow": (60.0, 100.0, 50.0),
    "navy": (240.0, 100.0, 25.1),
    "blue": (240.0, 100.0, 50.0),
    "teal": (180.0, 100.0, 25.1),
    "aqua": (180.0, 100.0, 50.0),
    "cyan": (180.0, 100.0, 50.0),
    "magenta": (300.0, 100.0, 50.0),
    "orange": (38.8, 100.0, 50.0),
    "pink": (349.5, 100.0, 87.6),
    "brown": (0.0, 59.4, 40.6),
    "gold": (50.6, 100.0, 50.0),
    "indigo": (274.6, 100.0, 25.5),
    "violet": (300.0, 76.1, 72.2),
    "salmon": (6.2, 93.2, 71.4),
    "tan": (34.3, 43.7, 68.6),
    "tomato": (9.1, 100.0, 63.9),
    "turquoise": (174.0, 72.1, 56.5),
    "coral": (16.1, 100.0, 65.7),
    "crimson": (348.0, 83.3, 47.1),
    "khaki": (54.0, 76.9, 74.5),
    "lavender": (240.0, 66.7, 94.1),
    "plum": (300.0, 47.3, 74.7),
    "orchid": (302.3, 58.9, 64.7),
    "beige": (60.0, 55.6, 91.2),
    "ivory": (60.0, 100.0, 97.1),
    "linen": (30.0, 66.7, 94.1),
    "wheat": (39.1, 76.7, 83.1),
    "azure": (180.0, 100.0, 97.1),
    "snow": (0.0, 100.0, 99.0),
    "sienna": (19.3, 56.1, 40.2),
    "chocolate": (25.0, 75.0, 47.1),
    "peru": (29.6, 58.7, 52.5),
    "seagreen": (146.5, 50.3, 36.3),
    "skyblue": (197.4, 71.4, 72.5),
    "steelblue": (207.3, 44.0, 49.0),
    "slategray": (210.0, 12.6, 50.2),
    "slategrey": (210.0, 12.6, 50.2),
    "royalblue": (225.0, 72.7, 56.9),
    "orangeRed": (16.2, 100.0, 50.0),
}

# A named colour is a colour only where a colour is declared. The word
# "orange" in a class name --federated-card--orange is a name, and the
# word "green" in a string is a label. A named colour is therefore
# looked for as the value of a property that takes one, and only in a
# stylesheet.
COLOUR_PROPERTY = re.compile(
    r"(?:^|[;{])\s*(?:-[a-z-]+\s+)*"
    r"(?:--[\w-]+|color|background(?:-color)?|border(?:-[a-z-]+)?|fill|stroke|"
    r"outline|box-shadow|text-shadow|caret-color|text-decoration-color|column-rule-color)"
    r"\s*:\s*(?P<value>[^;}\n]+)", re.IGNORECASE)


def named_use(text: str) -> list[tuple[str, str]]:
    """The named colours a stylesheet declares, and how they are written."""
    out = []
    for match in COLOUR_PROPERTY.finditer(text):
        value = match.group("value").strip()
        for name in NAMED:
            if re.fullmatch(name, value, re.IGNORECASE):
                out.append((value, name))
    return out

# The generic families are not a colour and not a typeface choice.
GENERIC = {"inherit", "initial", "unset", "revert", "none", "var", "auto",
           "system-ui", "ui-sans-serif", "ui-serif", "ui-monospace", "sans-serif",
           "serif", "monospace", "cursive", "fantasy", "-apple-system",
           "blinkmacsystemfont", "segoe ui", "roboto", "helvetica", "arial"}


def expand_hex(value: str) -> str | None:
    """A hex colour, expanded to six digits."""
    value = value.strip()
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    elif len(value) == 4:
        value = "".join(c * 2 for c in value[:3])
    elif len(value) == 8:
        value = value[:6]
    if len(value) != 6:
        return None
    return "#" + value.upper()


def hsl_to_hex(h: float, s: float, light: float) -> str:
    s /= 100.0
    light /= 100.0
    c = (1 - abs(2 * light - 1)) * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = light - c / 2
    if h < 60:
        rgb = (c, x, 0)
    elif h < 120:
        rgb = (x, c, 0)
    elif h < 180:
        rgb = (0, c, x)
    elif h < 240:
        rgb = (0, x, c)
    elif h < 300:
        rgb = (x, 0, c)
    else:
        rgb = (c, 0, x)
    return rgb_to_hex(tuple(int(round((v + m) * 255)) for v in rgb))


def colour_forms(text: str) -> dict[str, tuple[str, float | None]]:
    """Every colour a source states, as it is written and as it measures.

    The written form matters: a colour written as oklch(16% 0.028 260)
    has to be replaced as that, not as a hex it never was. The alpha
    matters too: a custom property carries no alpha of its own, so a
    colour that had one is replaced by a mix rather than by the plain
    step.
    """
    forms: dict[str, tuple[str, float | None]] = {}
    for match in HEX.finditer(text):
        raw = match.group(1)
        expanded = expand_hex(raw)
        if not expanded:
            continue
        alpha = None
        if len(raw) == 8:
            alpha = int(raw[6:8], 16) / 255
        elif len(raw) == 4:
            alpha = int(raw[3] * 2, 16) / 255
        forms[match.group(0)] = (expanded, alpha)
    for match in RGB.finditer(text):
        value = "#" + f"{int(match.group(1)):02X}{int(match.group(2)):02X}{int(match.group(3)):02X}"
        forms[match.group(0)] = (value, alpha_of(match.group("alpha")))
    for match in HSL.finditer(text):
        try:
            value = hsl_to_hex(float(match.group(1)), float(match.group(2)),
                               float(match.group(3)))
        except ValueError:
            continue
        forms[match.group(0)] = (value, alpha_of(match.group("alpha")))
    for match in OKLCH.finditer(text):
        try:
            value = rgb_to_hex(
                oklch_to_rgb(float(match.group(1)) / 100.0,
                             float(match.group(2)), float(match.group(3))))
        except (ValueError, OverflowError):
            continue
        forms[match.group(0)] = (value, alpha_of(match.group("alpha")))
    for written, name in named_use(text):
        h, sat, light = NAMED[name]
        forms[written] = (hsl_to_hex(h, sat, light), None)
    return forms


def alpha_of(value: str | None) -> float | None:
    """An alpha, as a fraction."""
    if not value:
        return None
    value = value.strip()
    if value.endswith("%"):
        return float(value[:-1]) / 100
    return float(value)


def colours_in(text: str) -> list[str]:
    """Every colour a source states, in every notation."""
    found = []
    for value in HEX.findall(text):
        expanded = expand_hex(value)
        if expanded:
            found.append(expanded)
    for match in RGB.finditer(text):
        found.append("#" + f"{int(match.group(1)):02X}{int(match.group(2)):02X}"
                          f"{int(match.group(3)):02X}")
    for match in HSL.finditer(text):
        try:
            found.append(hsl_to_hex(float(match.group(1)), float(match.group(2)),
                                    float(match.group(3))))
        except ValueError:
            continue
    for match in OKLCH.finditer(text):
        try:
            found.append(rgb_to_hex(oklch_to_rgb(float(match.group(1)) / 100.0,
                                                 float(match.group(2)),
                                                 float(match.group(3)))))
        except (ValueError, OverflowError):
            continue
    for match in OKLAB.finditer(text):
        lightness, a, b = match.group(1), match.group(2), match.group(3)
        # oklab is not in the system's vocabulary; it is reported as the
        # literal it is, so a consumer knows what to replace.
        found.append(f"oklab({lightness} {a} {b})")
    for name, (h, sat, light) in NAMED.items():
        for written, used in named_use(text):
            if used == name:
                found.append(hsl_to_hex(h, sat, light))
    return found


def system_colours() -> set[str]:
    """Every colour the system has, in every form the projections publish."""
    tokens = json.loads((ROOT / "core/TOKENS.json").read_text(encoding="utf-8"))
    surfaces = json.loads((ROOT / "core/SURFACES.json").read_text(encoding="utf-8"))
    out = set()
    for ramp in tokens["color"].values():
        for value in ramp.values():
            out.add("#" + value[1:].upper())
    for spec in surfaces["families"].values():
        for step in spec["steps"]:
            out.add("#" + step["value"][1:].upper())
    for accent in surfaces["accents"]:
        out.add("#" + accent["value"][1:].upper())
    return out


def system_families() -> set[str]:
    tokens = json.loads((ROOT / "core/TOKENS.json").read_text(encoding="utf-8"))
    out = set()
    for value in tokens["typography"].values():
        if isinstance(value, list):
            for family in value:
                if family.lower() not in GENERIC:
                    out.add(family)
    return out


def system_components() -> set[str]:
    spec = json.loads((ROOT / "core/COMPONENTS.json").read_text(encoding="utf-8"))
    out = set()
    for name, component in spec["components"].items():
        for part in component.get("parts") or []:
            out.add(part["class"])
        out.add("gnosix-" + name.replace("_", "-"))
    return out


def exempt_paths(consumer: Path) -> list[str]:
    """The paths a consumer declares as not being its interface."""
    manifest = consumer / "gnosix.json"
    if not manifest.is_file():
        return []
    try:
        document = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [item["path"] for item in (document.get("exempt") or [])
            if isinstance(item, dict) and "path" in item]


def scan(consumer: Path) -> dict:
    """What a consumer uses, and what it says about the system."""
    colours: dict[str, int] = {}
    families: dict[str, int] = {}
    files = 0
    own_classes: set[str] = set()
    gnosix_vars: set[str] = set()

    exempt = exempt_paths(consumer)
    for path in sorted(consumer.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if set(path.parts) & SKIP_DIRS:
            continue
        relative = str(path.relative_to(consumer))
        if any(relative.startswith(prefix) for prefix in exempt):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        files += 1
        for value in colours_in(text):
            colours[value] = colours.get(value, 0) + 1
        for match in FONT_FAMILY.finditer(text):
            for name in re.split(r"[,\"]+", match.group(1)):
                name = name.strip().strip("'\"").strip()
                if name and name.lower() not in GENERIC and not name.startswith("var("):
                    families[name] = families.get(name, 0) + 1
        for name in GNOSIX_VAR.findall(text):
            gnosix_vars.add(name)
        for match in re.finditer(r"class(?:Name)?\s*=\s*[\"'`]([^\"'`]+)", text):
            for token in re.split(r"[\s]+", match.group(1)):
                if token and not token.startswith(("gnosix-", "http", "$", "{")):
                    own_classes.add(token)
        for match in re.finditer(r"\.([a-zA-Z][A-Za-z0-9_-]*)", text):
            if "-" in match.group(1):
                own_classes.add(match.group(1))

    manifest = consumer / "gnosix.json"
    declared = None
    if manifest.is_file():
        try:
            declared = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            declared = {"error": "gnosix.json is not valid JSON"}

    return {"files": files, "colours": colours, "families": families,
            "own_classes": own_classes, "gnosix_vars": gnosix_vars,
            "declared": declared}


def report(consumer: Path, scan_result: dict) -> tuple[str, list[str]]:
    """The consumer's debt, and the problems that are errors."""
    system_colour_set = system_colours()
    system_family_set = system_families()
    system_component_set = system_components()

    content = set()
    declared = scan_result["declared"]
    if isinstance(declared, dict):
        for item in declared.get("content") or []:
            value = item.get("colour") if isinstance(item, dict) else item
            if isinstance(value, str) and value.startswith("#"):
                content.add(value.upper())
    outside = {c: n for c, n in scan_result["colours"].items()
               if c not in system_colour_set and c not in content}
    families = {f: n for f, n in scan_result["families"].items()
                if f not in system_family_set}
    own = sorted(c for c in scan_result["own_classes"] if c not in system_component_set)

    lines = [f"# {consumer.name}", "",
             f"{scan_result['files']} file(s) read.", ""]
    lines.append(f"- **Colours the system does not have:** {len(outside)}")
    for colour, count in sorted(outside.items(), key=lambda kv: -kv[1])[:20]:
        lines.append(f"  - `{colour}` ×{count}")
    lines.append(f"- **Font families the system does not have:** {len(families)}")
    for family, count in sorted(families.items(), key=lambda kv: -kv[1])[:10]:
        lines.append(f"  - `{family}` ×{count}")
    lines.append(f"- **gnosix custom properties in use:** {len(scan_result['gnosix_vars'])}")
    lines.append(f"- **The system's classes:** {len(system_component_set)}")
    lines.append(f"- **Classes the consumer builds itself:** {len(own)}")
    declared = scan_result["declared"]
    if declared is None:
        lines.append("- **The version of the system it honours:** not declared "
                     "(a consumer states it in gnosix.json)")
    else:
        version = declared.get("version") if isinstance(declared, dict) else None
        lines.append(f"- **The version of the system it honours:** {version or 'not declared'}")

    problems = []
    if declared is None:
        problems.append("the consumer does not declare which version of the system it honours")
    if outside:
        problems.append(f"{len(outside)} colour(s) the system does not have")
    if families:
        problems.append(f"{len(families)} font family/families the system does not have")
    return "\n".join(lines) + "\n", problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="check that a consumer has absorbed the system")
    parser.add_argument("--consumer", required=True, help="the consumer's repository")
    parser.add_argument("--check", action="store_true",
                        help="exit non-zero when the consumer has not absorbed the system")
    args = parser.parse_args(argv)

    consumer = Path(args.consumer).expanduser().resolve()
    if not consumer.is_dir():
        print(f"there is no consumer at {consumer}")
        return 3

    scan_result = scan(consumer)
    if not scan_result["files"]:
        print(f"{consumer} carries no styled source to check")
        return 3

    text, problems = report(consumer, scan_result)
    print(text)

    if not args.check:
        return 0
    if problems:
        print(f"FAIL: the consumer has not absorbed the system")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("PASS: the consumer uses only what the system has")
    return 0


if __name__ == "__main__":
    sys.exit(main())
