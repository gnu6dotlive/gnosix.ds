"""Generate target color declarations from the one approved token source."""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = "profiles/web/tokens.css"
ANDROID = "profiles/android/sample/app/src/main/java/labs/gnuin/gnosixds/GnosixColors.kt"


def words(name: str) -> list[str]:
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", name).split()


def colors(tokens: dict):
    for family, ramp in tokens["color"].items():
        for shade, value in ramp.items():
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
                raise ValueError(f"Invalid color value: {family}.{shade}")
            yield family, shade, value.upper()


def css_font_stack(values: list[str]) -> str:
    parts = []
    for value in values:
        if " " in value and not value.startswith(("ui-", "system-")):
            parts.append(f'"{value}"')
        else:
            parts.append(value)
    return ", ".join(parts)


def render_css(tokens: dict) -> str:
    rows = [":root {\n"]
    for family, shade, value in colors(tokens):
        name = "-".join(part.lower() for part in words(family))
        shade_name = "-".join(part.lower() for part in words(shade))
        rows.append(f"  --gnosix-{name}-{shade_name}: {value};\n")
    typography = tokens.get("typography", {})
    for role in ("primary", "display", "body", "navigation", "controls", "technical"):
        stack = typography.get(role)
        if isinstance(stack, list) and stack:
            rows.append(f"  --gnosix-font-{role}: {css_font_stack(stack)};\n")
    for role, weight in typography.get("weights", {}).items():
        rows.append(f"  --gnosix-weight-{role}: {int(weight)};\n")
    rows.append(surface_properties())
    return "".join(rows) + "}\n"


def surface_properties() -> str:
    """The surface layer, as custom properties.

    The layer is stated in core/SURFACES.json, and the web projection
    carries it, so the site and the profile use the same values rather than
    each keeping its own.
    """
    path = ROOT / "core/SURFACES.json"
    if not path.is_file():
        return ""
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for family, spec in document.get("families", {}).items():
        for step in spec.get("steps", []):
            rows.append(f"  --gnosix-{step['id']}: {step['value'].upper()};\n")
    for accent in document.get("accents", []):
        rows.append(f"  --gnosix-{accent['id']}: {accent['value'].upper()};\n")
    return "".join(rows)


def render_kotlin(tokens: dict) -> str:
    rows = ["package labs.gnuin.gnosixds\n\n", "import androidx.compose.ui.graphics.Color\n\n",
            "object GnosixColors {\n"]
    for family, shade, value in colors(tokens):
        name = "".join(part[:1].upper() + part[1:] for part in words(family)) + shade[:1].upper() + shade[1:]
        rows.append(f"    val {name} = Color(0xFF{value[1:]})\n")
    return "".join(rows) + "}\n"


def outputs(root: Path) -> dict[str, str]:
    tokens = json.loads((root / "core/TOKENS.json").read_text(encoding="utf-8"))
    return {WEB: render_css(tokens), ANDROID: render_kotlin(tokens)}


def check_projection(root: Path) -> list[str]:
    errors = []
    for rel, expected in outputs(root).items():
        path = root / rel
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            errors.append(f"{path.name} differs from TOKENS.json")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write:
        for rel, content in outputs(ROOT).items():
            path = ROOT / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return 0
    errors = check_projection(ROOT)
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
