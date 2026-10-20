"""Generate target color declarations from the one approved token source."""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = "profiles/web/tokens.css"
ANDROID = "profiles/android/sample/app/src/main/java/labs/gnuin/gnosixds/GnosixColors.kt"
NATIVE = "profiles/native/src/theme.rs"


def words(name: str) -> list[str]:
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", name).split()


def published_name(*parts: str) -> str:
    """The published name of a layer.

    One rule, one place. The published name of a layer is its id,
    kebab-cased, under the --gnosix- prefix. The rule lives here, in the
    tool, rather than in a projection, so that a consumer, a projection
    and a gate can all ask for it and get the same answer. It used to
    live only in the web projection, which is how a vendored copy of the
    namespace was able to drift for so long without anybody being able to
    check it against anything.
    """
    out = []
    for part in parts:
        out.extend(words(part))
    return "--gnosix-" + "-".join(word.lower() for word in out)


def spacing_names(tokens: dict) -> set[str]:
    """The names the contract's spacing scale publishes."""
    return {published_name("space", step) for step in (tokens.get("spacing") or {})}


def radius_names(tokens: dict) -> set[str]:
    """The names the contract's radius scale publishes."""
    return {published_name("radius", step) for step in (tokens.get("radius") or {})}


def layer_names(tokens: dict) -> set[str]:
    """The names the contract's colour layers publish."""
    return {published_name(family, shade) for family, shade, _ in colors(tokens)}


def surface_names() -> set[str]:
    """The names the contract's surface layer publishes."""
    path = ROOT / "core/SURFACES.json"
    if not path.is_file():
        return set()
    document = json.loads(path.read_text(encoding="utf-8"))
    names = set()
    for spec in document.get("families", {}).values():
        for step in spec.get("steps", []):
            names.add(published_name(step["id"]))
    for accent in document.get("accents", []):
        names.add(published_name(accent["id"]))
    return names


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
        rows.append(f"  {published_name(family, shade)}: {value};\n")
    typography = tokens.get("typography", {})
    for role in ("primary", "display", "body", "navigation", "controls", "technical"):
        stack = typography.get(role)
        if isinstance(stack, list) and stack:
            rows.append(f"  --gnosix-font-{role}: {css_font_stack(stack)};\n")
    for role, weight in typography.get("weights", {}).items():
        rows.append(f"  --gnosix-weight-{role}: {int(weight)};\n")
    for step, value in (tokens.get("spacing") or {}).items():
        rows.append(f"  --gnosix-space-{step}: {value}px;\n")
    for step, value in (tokens.get("radius") or {}).items():
        rows.append(f"  --gnosix-radius-{step}: {value}px;\n")
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
            rows.append(f"  {published_name(step['id'])}: {step['value'].upper()};\n")
    for accent in document.get("accents", []):
        rows.append(f"  {published_name(accent['id'])}: {accent['value'].upper()};\n")
    return "".join(rows)


def render_kotlin(tokens: dict) -> str:
    rows = ["package labs.gnuin.gnosixds\n\n", "import androidx.compose.ui.graphics.Color\n\n",
            "object GnosixColors {\n"]
    for family, shade, value in colors(tokens):
        name = "".join(part[:1].upper() + part[1:] for part in words(family)) + shade[:1].upper() + shade[1:]
        rows.append(f"    val {name} = Color(0xFF{value[1:]})\n")
    rows.append("}\n")

    # The surface layer travels with the palette, so a Compose surface is
    # the system's own and not a second one written by hand.
    surfaces = load_surfaces()
    if surfaces:
        rows.append("\nobject GnosixSurfaces {\n")
        for spec in surfaces["families"].values():
            for step in spec["steps"]:
                rows.append(f"    val {kotlin_name(step['id'])} = Color(0xFF{step['value'].lstrip('#')})\n")
        for accent in surfaces["accents"]:
            rows.append(f"    val {kotlin_name(accent['id'])} = Color(0xFF{accent['value'].lstrip('#')})\n")
        rows.append("}\n")
    return "".join(rows)


def kotlin_name(identifier: str) -> str:
    """A step's identifier as a Kotlin constant name."""
    parts = re.split(r"[^A-Za-z0-9]+", identifier)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def rust_name(identifier: str) -> str:
    """A step's identifier as a Rust constant name.

    The camelCase of the token source is split first, so the constant reads
    NEUTRAL_SHELL_WHITE and not NEUTRAL_SHELLWHITE.
    """
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", identifier)
    name = re.sub(r"[^A-Za-z0-9]+", "_", spaced).upper()
    # A Rust identifier cannot start with a digit, and the spacing steps do:
    # 2xs, 3xl, 4xl, 5xl. The prefix keeps them apart as well as legal.
    if name and name[0].isdigit():
        name = "S_" + name
    return name


def load_surfaces() -> dict:
    path = ROOT / "core/SURFACES.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def render_rust(tokens: dict) -> str:
    """The native projection: Rust constants, no handwritten second palette.

    The profile is a mapping, not a crate that depends on GPUI: the engine
    is pre-1.0 and its API is version-scoped. What can be ratified is the
    projection itself - the same values, under the same names, that the web
    and the Android profiles get - and that is what this file is.
    """
    surfaces = load_surfaces()
    rows = [
        "//! Generated from core/TOKENS.json and core/SURFACES.json. Do not edit.\n",
        "//!\n",
        "//! The gnosix portable contract as Rust constants: the palette, the\n",
        "//! surfaces, the measured contrast ratios, the spacing and the weights.\n",
        "//! A target implementation consumes these; it does not restate them.\n",
        "\n",
        "#![allow(dead_code)]\n",
        "\n",
        "/// The approved palette.\n",
        "pub mod colour {\n",
    ]
    for family, shade, value in colors(tokens):
        rows.append(f'    pub const {rust_name(family + "-" + shade)}: &str = "{value}";\n')
    rows.append("}\n\n")

    rows.append("/// The surface layer.\n")
    rows.append("pub mod surface {\n")
    for spec in surfaces.get("families", {}).values():
        for step in spec["steps"]:
            rows.append(f'    pub const {rust_name(step["id"])}: &str = "{step["value"]}";\n')
    for accent in surfaces.get("accents", []):
        rows.append(f'    pub const {rust_name(accent["id"])}: &str = "{accent["value"]}";\n')
    rows.append("}\n\n")

    rows.append("/// The measured contrast of each approved pairing.\n")
    rows.append("pub mod contrast {\n")
    for pairing, ratio in tokens.get("contrast", {}).items():
        rows.append(f"    pub const {rust_name(pairing)}: f64 = {ratio};\n")
    rows.append("}\n\n")

    rows.append("/// The ratified spacing steps.\n")
    rows.append("pub mod spacing {\n")
    for step, value in tokens.get("spacing", {}).items():
        rows.append(f"    pub const {rust_name(step)}: f64 = {value}.0;\n")
    rows.append("}\n\n")

    rows.append("/// The ratified radius steps.\n")
    rows.append("pub mod radius {\n")
    for step, value in tokens.get("radius", {}).items():
        rows.append(f"    pub const {rust_name(step)}: f64 = {value}.0;\n")
    rows.append("}\n\n")

    rows.append("/// The ratified weights.\n")
    rows.append("pub mod weight {\n")
    for role, value in tokens.get("typography", {}).get("weights", {}).items():
        rows.append(f"    pub const {rust_name(role)}: u16 = {int(value)};\n")
    rows.append("}\n")
    return "".join(rows)


def outputs(root: Path) -> dict[str, str]:
    tokens = json.loads((root / "core/TOKENS.json").read_text(encoding="utf-8"))
    return {WEB: render_css(tokens), ANDROID: render_kotlin(tokens), NATIVE: render_rust(tokens)}


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
