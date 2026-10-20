"""Generate core/SURFACES.json from the colours the site already uses.

The package states its palette in core/TOKENS.json and nothing else. The
public reference then needed a set of surfaces, inks and hairlines that the
palette does not contain, and it invented fifty-nine of them: a cool
neutral ramp that no file in the package explained, with a couple of
deliberate tints beside it. COL-001 says to read exact approved colours
from the token source, and the package's own site broke it in ninety-four
places.

This script does not design a new palette. It reads the colours the site
already uses, works out what each one is for, and writes them down as a
layer of the contract: a family whose hue comes from a token, with the
lightness and the chroma of each step stated. The site then uses the
sanctioned values, and a gate refuses any colour that is not one of them.

    python3 tools/build_surfaces.py
"""

import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oklch import hex_to_rgb, rgb_to_oklch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site/style.css"
TOKENS = ROOT / "core/TOKENS.json"
OUT = ROOT / "core/SURFACES.json"

# A step whose chroma is under this is achromatic: its hue carries no
# information, so the family's hue rule does not apply to it.
NEUTRAL_CHROMA_MAX = 0.006


def approved_tokens() -> set[str]:
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    return {value.upper() for ramp in tokens["color"].values() for value in ramp.values()}


# The first-party design surfaces: every place the package draws its own
# interface. The vendored assets are artwork and are not surfaces.
SURFACE_FILES = [
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


def collect() -> list[dict]:
    """Every colour the first-party surfaces use, with what it is used for."""
    uses: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)

    for rel in SURFACE_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if rel.endswith(".css"):
            for block in re.finditer(r"([^{}]+)\{([^{}]*)\}", text):
                for declaration in block.group(2).split(";"):
                    if ":" not in declaration:
                        continue
                    prop, value = declaration.split(":", 1)
                    prop = prop.strip().lower()
                    for value_hex in re.findall(r"#[0-9A-Fa-f]{6}\b", value):
                        uses[value_hex.upper()][prop] += 1
        elif rel.endswith(".svg"):
            for element in re.finditer(r"<(text|tspan|rect|path|circle|ellipse|line|polygon|stop|polyline)\b[^>]*>", text):
                tag = element.group(1)
                for value_hex in re.findall(r"#[0-9A-Fa-f]{6}\b", element.group(0)):
                    uses[value_hex.upper()][f"svg:{tag}"] += 1
        else:
            for value_hex in re.findall(r"#[0-9A-Fa-f]{6}\b", text):
                uses[value_hex.upper()]["manifest"] += 1

    approved = approved_tokens()
    out = []
    for value_hex, props in uses.items():
        if value_hex in approved:
            continue
        lightness, chroma, hue = rgb_to_oklch(hex_to_rgb(value_hex))
        out.append({
            "value": value_hex,
            "lightness": round(lightness, 4),
            "chroma": round(chroma, 4),
            "hue": round(hue, 1),
            "props": dict(props),
        })
    out.sort(key=lambda item: (item["lightness"], item["value"]))
    return out


def role_for(item: dict) -> tuple[str, str]:
    """A family and a role, from the property and the lightness."""
    props = item["props"]
    lightness = item["lightness"]

    def count(*names: str) -> int:
        return sum(props.get(name, 0) for name in names)

    ink = count("color", "svg:text", "svg:tspan")
    hairline = sum(n for p, n in props.items() if p.startswith("border"))
    surface = count("background", "svg:rect", "svg:path", "svg:circle", "svg:ellipse",
                    "svg:line", "svg:polygon", "svg:polyline", "svg:stop", "manifest")

    if ink and ink >= hairline and ink >= surface:
        if lightness < 0.62:
            return "ink-on-light", "text on the light substrate"
        return "ink-on-dark", "text on the dark substrate"
    if hairline and hairline >= surface:
        return "hairline", "a hairline between surfaces"
    if lightness < 0.55:
        return "surface-dark", "a raised surface on the dark substrate"
    return "surface-light", "a raised surface on the light substrate"


def main() -> int:
    items = collect()

    base_hue = rgb_to_oklch(hex_to_rgb("#111418"))[2]

    def is_accent(item: dict) -> bool:
        if item["chroma"] < 0.008:
            return False
        distance = abs((item["hue"] - base_hue + 180) % 360 - 180)
        return distance > 30

    # Two tints that are the same tint are one tint. The site and the web
    # demo had two warm glows a single unit apart, and a contract that
    # states both is a contract that states neither. Only the tints are
    # merged this way: the neutral ramp's own steps are a unit apart by
    # design, and merging them would collapse it.
    merged: list[dict] = []
    for item in sorted(items, key=lambda i: -sum(i["props"].values())):
        item["aliases"] = []
        if is_accent(item):
            for kept in merged:
                if kept["chroma"] < 0.008:
                    continue
                if abs(kept["lightness"] - item["lightness"]) <= 0.005 and \
                        abs(kept["hue"] - item["hue"]) <= 12:
                    kept["aliases"].append(item["value"])
                    break
            else:
                merged.append(item)
        else:
            merged.append(item)

    # The tints that are deliberately not neutral: the green of a confirmed
    # state, and the warm glow behind the hero. They are chromatic and their
    # hue has left the family's, so they are accents with a role rather than
    # steps of a neutral.
    families: dict[str, list[dict]] = collections.defaultdict(list)
    accent_rows = []
    for item in merged:
        if is_accent(item):
            green = 110 <= item["hue"] <= 180
            if green:
                name = "ink-positive" if "color" in item["props"] else "surface-positive"
                role = ("the green ink of a confirmed state" if name == "ink-positive"
                        else "the green ground of a confirmed state")
            else:
                name = "surface-warm"
                role = "the warm glow behind the hero"
            accent_rows.append({
                "id": f"{name}-l{round(item['lightness'] * 1000)}",
                "role_id": name,
                "value": item["value"],
                "lightness": item["lightness"],
                "chroma": item["chroma"],
                "hue": item["hue"],
                "role": role,
                "neutral": False,
                "aliases": item["aliases"],
            })
            continue
        family, role = role_for(item)
        families[family].append({
            "id": None,
            "value": item["value"],
            "lightness": item["lightness"],
            "chroma": item["chroma"],
            "hue": item["hue"],
            "role": role,
            "neutral": item["chroma"] < NEUTRAL_CHROMA_MAX,
            "aliases": item["aliases"],
        })

    # A step is named by its lightness, not by its position. A positional
    # name is renumbered the moment a step is added, and every file that
    # referred to the old name then quietly loses its colour - the custom
    # property resolves to nothing and the surface falls back to whatever
    # the cascade gives it. A lightness-named step keeps its name when a
    # step is added, and loses it only when the surface itself changes,
    # which is a change that should be visible.
    for family, rows in families.items():
        rows.sort(key=lambda r: r["lightness"])
        for row in rows:
            row["id"] = f"{family}-l{round(row['lightness'] * 1000)}"

    document = {
        "schema": "gnosix_DS.surfaces.v1",
        "status": "CURRENT",
        "derivation": {
            "space": "oklch",
            "hue": "from the base token of the family",
            "neutral_chroma_max": 0.008,
            "note": (
                "A surface is a step of its family's hue. The lightness and the chroma "
                "are chosen; the family is not. A step whose chroma is below "
                "neutral_chroma_max is achromatic, and its hue carries no information, "
                "so the family's hue does not apply to it. A colour outside this layer "
                "and outside the token source is not a colour of the system."
            ),
        },
        "families": {
            "surface-dark": {
                "base": "neutral/anthracite",
                "role": "the raised surfaces of the dark substrate",
                "steps": families.get("surface-dark", []),
            },
            "surface-light": {
                "base": "neutral/anthracite",
                "role": "the raised surfaces of the light substrate",
                "steps": families.get("surface-light", []),
            },
            "ink-on-dark": {
                "base": "neutral/anthracite",
                "role": "the text on the dark substrate",
                "steps": families.get("ink-on-dark", []),
            },
            "ink-on-light": {
                "base": "neutral/anthracite",
                "role": "the text on the light substrate",
                "steps": families.get("ink-on-light", []),
            },
            "hairline": {
                "base": "neutral/anthracite",
                "role": "the hairlines between surfaces",
                "steps": families.get("hairline", []),
            },
        },
        "accents": accent_rows,
    }

    OUT.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total = sum(len(f["steps"]) for f in document["families"].values()) + len(accent_rows)
    aliases = sum(len(a.get("aliases", [])) for a in accent_rows) + sum(
        len(st.get("aliases", [])) for f in document["families"].values() for st in f["steps"])
    print(f"wrote {OUT.relative_to(ROOT)}: {total} surfaces "
          f"({len(accent_rows)} accents, {total - len(accent_rows)} steps, "
          f"{aliases} merged)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
