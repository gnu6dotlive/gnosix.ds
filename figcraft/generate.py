#!/usr/bin/env python3
"""Build the gnosix.ds FigCraft project from the gnosix.ds repository.

The FigCraft project is a build artefact of the gnosix.ds repository, in the
same way the distributable tarball is: the repository is the source, the
project is what you get from it. Nothing here is hand-placed, so the two
cannot drift apart, and rebuilding after a token change is one command.

    python3 tools/gnosix_to_figcraft.py --source ~/Projects/gnosix.ds

What the project contains, and why each part is there:

  Colour      the approved palette as a variable collection, with every
              swatch bound to its variable rather than filled with a literal.
              Changing a token changes the swatch.
  Contrast    the seven approved pairings, each drawn as it is actually
              used, with its measured ratio. gnosix is a substrate system,
              not a theme system: the palette does not change between light
              and dark, the pairings do. So the pairings are what the
              project documents.
  Type        specimens for the ratified weights, and text styles that carry
              them.
  Spacing     the spacing scale as number variables, each shown as its own
              bar.
  Components  the vendored icon subset, the flag subset and the identity
              masters, imported as editable layers.
  Scenes      the six reference scenes, imported as editable frames rather
              than as pictures, so the layers inside them can be edited.
  Rules       the fifteen rules, each as a card, each carrying the rule as
              an annotation so Dev Mode shows it beside the thing it
              governs.

Every page holds exactly one board frame and everything lives inside it, so
a page exports as one image and a consumer can select a board rather than
hunting for loose layers.

The generator writes a command script and hands it to figcraft-cli, so the
build is the same machinery a developer would use by hand, and the script
is left behind for inspection.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# The repository this generator lives in. The projection is built from it and
# checked against it, so the paths default to it rather than to a location
# that only exists on one machine.
REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------- layout

PAGE_W = 1200
MARGIN = 64
CONTENT_W = PAGE_W - 2 * MARGIN

FALLBACK = {
    "anthracite": "#111418",
    "shellWhite": "#F7F3ED",
    "pureWhite": "#FFFFFF",
    "hairline": "#D7DADF",
    "muted": "#A1A6AD",
    "slate": "#667085",
    "signalOrange": "#FF6A00",
    "beretGreen": "#5F7F52",
    "royalBlue": "#4169E1",
}

FAMILY_LABEL = {
    "neutral": "Neutral",
    "signalOrange": "Signal Orange",
    "beretGreen": "Beret Green",
    "royalBlue": "Royal Blue",
    "semantic": "Semantic",
}


class Script:
    """An ordered list of FigCraft commands, with step references."""

    def __init__(self):
        self.steps: list[dict] = []

    def add(self, command: str, **params) -> int:
        self.steps.append({"command": command, "params": params})
        return len(self.steps) - 1

    def ref(self, step: int) -> dict:
        return {"$step": step}

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for step in self.steps:
                handle.write(json.dumps(step, ensure_ascii=False) + "\n")


class Ctx:
    """The board the current page is being drawn on.

    Helpers default to it, so a page builder states coordinates relative to
    its board and never repeats the parent.
    """

    def __init__(self, script: Script):
        self.script = script
        self.parent: dict | None = None


class _Inherit:
    """Marker: take the parent from the context.

    It exists because None is a meaningful value: a layer with no parent
    sits on the page, and a board frame has to say so explicitly or it
    would be built inside the previous board.
    """


INHERIT = _Inherit()


def _parent(ctx: Ctx, parent) -> dict | None:
    return ctx.parent if parent is INHERIT else parent


# ------------------------------------------------------------- primitives

def frame(ctx: Ctx, name: str, x: int, y: int, w: int, h: int,
          fill: str | None = None, radius: int = 0, parent=INHERIT) -> int:
    props = {}
    if fill:
        props["fills"] = [{"type": "solid", "color": fill}]
    if radius:
        props["cornerRadius"] = radius
    params = {"type": "frame", "name": name, "x": x, "y": y, "width": w, "height": h}
    if props:
        params["props"] = props
    params["parent"] = _parent(ctx, parent)
    return ctx.script.add("node.create", **params)


def rect(ctx: Ctx, name: str, x: int, y: int, w: int, h: int, fill: str,
         radius: int = 0, parent=INHERIT) -> int:
    props = {"fills": [{"type": "solid", "color": fill}]}
    if radius:
        props["cornerRadius"] = radius
    params = {"type": "rectangle", "name": name, "x": x, "y": y, "width": w, "height": h, "props": props}
    params["parent"] = _parent(ctx, parent)
    return ctx.script.add("node.create", **params)


def text(ctx: Ctx, body: str, x: int, y: int, size: int, fill: str,
         style: str | None = None, width: int | None = None, tracking: str | None = None,
         align: str | None = None, family: str = "Space Grotesk",
         parent=INHERIT) -> int:
    props = {"fontSize": size, "fontFamily": family, "fills": [{"type": "solid", "color": fill}]}
    if style:
        props["fontStyle"] = style
    if tracking:
        props["letterSpacing"] = tracking
    if align:
        props["textAlign"] = align
    params = {"type": "text", "text": body, "x": x, "y": y}
    if width:
        params["width"] = width
    params["props"] = props
    params["parent"] = _parent(ctx, parent)
    return ctx.script.add("node.create", **params)


def title_block(ctx: Ctx, title: str, subtitle: str, colour: dict) -> None:
    text(ctx, title, MARGIN, MARGIN, 48, colour["anthracite"], "Bold")
    text(ctx, subtitle, MARGIN, MARGIN + 62, 16, colour["slate"], width=CONTENT_W)


def section_label(ctx: Ctx, label: str, x: int, y: int, colour: dict) -> None:
    text(ctx, label.upper(), x, y, 12, colour["slate"], "Bold", tracking="12%")


def open_board(ctx: Ctx, script: Script, page: str, name: str, height: int, colour: dict) -> dict:
    """Start a page and put one board frame on it."""
    if page == "Colour":
        # The document's first page is reused rather than left empty beside
        # the real one.
        script.add("page.rename", name=page)
    else:
        # page.add does not switch the current page, so the board would be
        # built on whichever page was current before.
        added = script.add("page.add", name=page)
        script.add("page.select", id=script.ref(added))
    # The board sits on the page, not inside the previous page's board.
    board = frame(ctx, name, 0, 0, PAGE_W, height, fill=colour["shellWhite"], parent=None)
    ctx.parent = script.ref(board)
    return script.ref(board)


# --------------------------------------------------------------- the pages

def build_colour_page(ctx: Ctx, script: Script, tokens: dict, colour: dict) -> None:
    """The palette, every swatch bound to its variable."""
    y = 210
    cell_w, cell_h, gap, pitch = 160, 140, 16, 196
    per_row = (CONTENT_W + gap) // (cell_w + gap)

    # A family block is its label, its swatch rows and the gap under them.
    # The row count differs per family, so the height is summed rather than
    # multiplied: a board that is a page too short clips its last swatch,
    # and a board a page too long is mostly nothing.
    family_heights = []
    for family, ramp in tokens["color"].items():
        rows = (len(ramp) + per_row - 1) // per_row
        family_heights.append(30 + rows * pitch + 24)
    height = 210 + sum(family_heights) + 60

    open_board(ctx, script, "Colour", "Colour / board", height, colour)
    title_block(ctx, "Colour",
                "The approved palette. Every swatch is bound to its variable, so a "
                "token change moves the swatch.", colour)

    y = 210
    for family, ramp in tokens["color"].items():
        section_label(ctx, FAMILY_LABEL.get(family, family), MARGIN, y, colour)
        y += 30
        for index, (shade, value) in enumerate(ramp.items()):
            column = index % per_row
            row = index // per_row
            x = MARGIN + column * (cell_w + gap)
            cy = y + row * pitch
            token = f"{family}/{shade}"
            swatch = rect(ctx, f"Swatch / {token}", x, cy, cell_w, cell_h, value, radius=8)
            # The swatch is bound to the variable rather than filled with a
            # literal: the binding is the live edge of the system.
            script.add("variable.bind", ids=[script.ref(swatch)], field="fill", variable=token)
            # A hairline, because a light swatch on a light board is
            # otherwise not a swatch at all: shellWhite on shellWhite is a
            # hole in the page.
            script.add("node.set", ids=[script.ref(swatch)], props={"strokes": [
                {"type": "solid", "color": colour["hairline"], "strokeWeight": 1}]})
            text(ctx, shade, x, cy + cell_h + 10, 14, colour["anthracite"], "Medium")
            text(ctx, value, x, cy + cell_h + 30, 12, colour["slate"])
        rows = (len(ramp) + per_row - 1) // per_row
        y += rows * pitch + 24


def build_contrast_page(ctx: Ctx, script: Script, tokens: dict, colour: dict) -> None:
    """The approved pairings, drawn as they are used."""
    contrast = tokens.get("contrast", {})
    open_board(ctx, script, "Contrast", "Contrast / board", 210 + len(contrast) * 112 + 80, colour)
    title_block(ctx, "Contrast",
                "The approved pairings, drawn as they are used. gnosix is a "
                "substrate system: the palette is fixed, the pairing carries "
                "the meaning.", colour)

    y = 210
    for pairing, ratio in contrast.items():
        # "ink_on_substrate", read the way the rule reads it: COL-002 puts
        # white essential text on Signal Orange, so the first name is the
        # foreground and the second is what it sits on.
        ink, substrate = pairing.split("_on_")
        substrate_hex = tokens["color"].get(substrate, {}).get("base") \
            or tokens["color"].get("neutral", {}).get(substrate, colour["shellWhite"])
        ink_hex = tokens["color"].get("neutral", {}).get(ink) \
            or tokens["color"].get(ink, {}).get("base", colour["anthracite"])

        row = frame(ctx, f"Pairing / {pairing}", MARGIN, y, CONTENT_W, 96,
                    fill=colour["pureWhite"], radius=12)
        script.add("node.set", ids=[script.ref(row)], props={"strokes": [
            {"type": "solid", "color": colour["hairline"], "strokeWeight": 1}]})

        # Everything inside the row is positioned relative to the row, not to
        # the board. A child's x/y is relative to its parent frame, and a
        # page coordinate here would place the content far outside the row,
        # where the frame clips it.
        text(ctx, pairing, 24, 38, 14, colour["anthracite"], "Medium",
             parent=script.ref(row))
        # A frame, not a rectangle: the sample carries text on it, and a
        # rectangle cannot contain layers.
        sample = frame(ctx, f"Sample / {pairing}", 300, 20, 320, 56,
                       fill=substrate_hex, radius=8, parent=script.ref(row))
        text(ctx, "Aa 0O — sample", 20, 18, 18, ink_hex, "Medium", parent=script.ref(sample))

        text(ctx, f"{ratio}", 660, 34, 20, colour["anthracite"], "Bold",
             parent=script.ref(row))
        text(ctx, "contrast ratio", 660, 60, 12, colour["slate"],
             parent=script.ref(row))

        verdict = "AA body" if ratio >= 4.5 else ("AA large" if ratio >= 3.0 else "fails AA")
        badge = frame(ctx, f"Verdict / {pairing}", 900, 32, 140, 32,
                      fill=colour["beretGreen"] if ratio >= 4.5 else colour["signalOrange"],
                      radius=16, parent=script.ref(row))
        text(ctx, verdict, 16, 9, 12, colour["pureWhite"], "Bold", parent=script.ref(badge))
        y += 112


def build_type_page(ctx: Ctx, script: Script, tokens: dict, colour: dict) -> None:
    """The ratified weights, as specimens and as text styles."""
    typography = tokens.get("typography", {})
    weights = typography.get("weights", {})
    primary = (typography.get("primary") or ["Space Grotesk"])[0]

    open_board(ctx, script, "Type", "Type / board", 210 + len(weights) * 130 + 180, colour)
    title_block(ctx, "Type",
                "Space Grotesk, the only visual family. Weights are the ratified "
                "four; the technical style adds tabular figures.", colour)

    y = 210
    for weight_name, weight in weights.items():
        section_label(ctx, f"{weight_name} / {weight}", MARGIN, y, colour)
        y += 28
        text(ctx, "Ship interfaces, not mockups", MARGIN, y, 40,
             colour["anthracite"], "Bold" if weight >= 600 else "Regular")
        y += 62
        text(ctx, "A design source of truth your agents can edit, render and "
                 "hand off as code.", MARGIN, y, 16, colour["slate"], width=CONTENT_W)
        y += 44

    section_label(ctx, "technical", MARGIN, y, colour)
    y += 28
    text(ctx, "0123456789 · 42.5 °C · 03.4.2 · project://gnosix", MARGIN, y, 14,
         colour["slate"], tracking="4%")

    # Text styles carry the ratified weights, so a consumer applies the role
    # rather than re-deciding the size.
    for weight_name, weight in weights.items():
        script.add("style.create", type="text", name=f"Type / {weight_name}",
                   value={"fontSize": 16, "fontFamily": primary,
                          "fontStyle": "Bold" if weight >= 600 else "Regular"})


def build_spacing_page(ctx: Ctx, script: Script, tokens: dict, colour: dict) -> None:
    """The spacing scale, as number variables shown as their own bars."""
    spacing = tokens.get("spacing", {})
    open_board(ctx, script, "Spacing", "Spacing / board", 210 + len(spacing) * 56 + 80, colour)
    title_block(ctx, "Spacing",
                "The ratified spacing steps. Each bar is bound to its variable, "
                "so the scale is the same scale the code uses.", colour)

    y = 210
    for step, value in spacing.items():
        text(ctx, step, MARGIN, y + 8, 14, colour["anthracite"], "Medium")
        text(ctx, str(value), MARGIN + 120, y + 8, 14, colour["slate"])
        bar = rect(ctx, f"Space / {step}", MARGIN + 200, y, max(value, 2), 32,
                   colour["royalBlue"], radius=4)
        script.add("variable.bind", ids=[script.ref(bar)], field="width", variable=f"space/{step}")
        y += 56


def build_components_page(ctx: Ctx, script: Script, source: Path, manifest: dict, colour: dict) -> None:
    """The vendored icon subset, the flag subset and the identity masters."""
    entries_by_kind: dict[str, list] = {}
    for entry in manifest.get("entries", []):
        entries_by_kind.setdefault(entry.get("kind", "icon"), []).append(entry)

    icon_rows = (len(entries_by_kind.get("icon", [])) + 9) // 10
    flag_rows = (len(entries_by_kind.get("flag", [])) + 5) // 6
    height = 210 + 30 + icon_rows * 128 + 40 + 30 + flag_rows * 128 + 40 + 30 + 200

    open_board(ctx, script, "Components", "Components / board", height, colour)
    title_block(ctx, "Components",
                "The ratified glyphs and identity masters, imported as editable "
                "layers. Nothing here is a picture of a thing.", colour)

    y = 210
    for kind, label, cell, per_row in (("icon", "Icons", 88, 10), ("flag", "Flags", 120, 6)):
        entries = entries_by_kind.get(kind, [])
        section_label(ctx, f"{label} / {len(entries)}", MARGIN, y, colour)
        y += 30
        for index, entry in enumerate(entries):
            column = index % per_row
            row = index // per_row
            x = MARGIN + column * (cell + 16)
            cy = y + row * 128
            cell_frame = frame(ctx, f"{kind.title()} / {entry['name']}", x, cy, cell, 96,
                               fill=colour["pureWhite"], radius=8)
            script.add("node.set", ids=[script.ref(cell_frame)], props={"strokes": [
                {"type": "solid", "color": colour["hairline"], "strokeWeight": 1}]})
            icon = script.add("file.import", path=str(source / entry["path"]))
            # The import lands a frame named after the file; give it the
            # name the manifest uses so the layer tree reads as the design
            # system and not as a file listing.
            script.add("object.rename", ids=[script.ref(icon)], name=entry["name"])
            script.add("node.reparent", ids=[script.ref(icon)], parent=script.ref(cell_frame))
            script.add("node.set", ids=[script.ref(icon)], props={"x": 24, "y": 30})
            text(ctx, entry["name"], x, cy + 102, 11, colour["slate"], width=cell)
        rows = (len(entries) + per_row - 1) // per_row
        y += rows * 128 + 40

    section_label(ctx, "Identity masters", MARGIN, y, colour)
    y += 30
    identity = [
        ("gnosix-cube.png", "gnosix", None),
        ("gnu6-live-cube.png", "gnu6.live", None),
        ("gnuinlabs-cube.png", "gnu.in.labs", None),
        ("gnosix-cube-alpha.png", "gnosix / alpha", colour["pureWhite"]),
        ("gnu6-live-cube-alpha.png", "gnu6.live / alpha", colour["pureWhite"]),
        ("gnuinlabs-cube-alpha.png", "gnu.in.labs / alpha", colour["pureWhite"]),
    ]
    for index, (filename, label, substrate) in enumerate(identity):
        x = MARGIN + index * 184
        cell = frame(ctx, f"Identity / {label}", x, y, 168, 168,
                     fill=substrate or colour["pureWhite"], radius=12)
        script.add("node.set", ids=[script.ref(cell)], props={"strokes": [
            {"type": "solid", "color": colour["hairline"], "strokeWeight": 1}]})
        image = script.add("file.import", path=str(source / "assets/identity" / filename))
        script.add("object.rename", ids=[script.ref(image)], name=label)
        script.add("node.reparent", ids=[script.ref(image)], parent=script.ref(cell))
        script.add("node.set", ids=[script.ref(image)], props={"x": 8, "y": 8,
                                                               "width": 152, "height": 152})
        text(ctx, label, x, y + 176, 12, colour["slate"], width=168)


def build_scenes_page(ctx: Ctx, script: Script, source: Path, references: list[dict], colour: dict) -> None:
    """The six reference scenes, imported as editable frames."""
    height = 210 + len(references) * 802 + 80
    open_board(ctx, script, "Scenes", "Scenes / board", height, colour)
    title_block(ctx, "Scenes",
                "The six reference scenes, imported as editable frames. The layers "
                "inside them are vectors and text, not a picture.", colour)

    y = 210
    for reference in references:
        section_label(ctx, reference.get("id", ""), MARGIN, y, colour)
        y += 26
        scene = script.add("file.import", path=str(source / reference["artwork"]))
        script.add("object.rename", ids=[script.ref(scene)], name=reference.get("id", "scene"))
        script.add("node.reparent", ids=[script.ref(scene)], parent=ctx.parent)
        # The scenes are 1200 wide, the width of the board, so they sit
        # full-bleed. Insetting them by the margin would push their right
        # edge past the board and clip it.
        script.add("node.set", ids=[script.ref(scene)], props={"x": 0, "y": y})
        y += 720 + 56


def build_rules_page(ctx: Ctx, script: Script, rules: list[dict], references: list[dict], colour: dict) -> None:
    """The fifteen rules, each as a card carrying the rule as an annotation."""
    by_id = {}
    for reference in references:
        for rule_id in reference.get("rules", []):
            by_id[rule_id] = reference.get("id")

    card_w, card_h, gap = 520, 152, 32
    per_row = (CONTENT_W + gap) // (card_w + gap)
    rows = (len(rules) + per_row - 1) // per_row
    open_board(ctx, script, "Rules", "Rules / board", 210 + rows * (card_h + gap) + 80, colour)
    title_block(ctx, "Rules",
                "The ratified rules. Each card carries its rule as an annotation, "
                "so Dev Mode shows the rule beside the thing it governs.", colour)

    for index, rule in enumerate(rules):
        column = index % per_row
        row = index // per_row
        x = MARGIN + column * (card_w + gap)
        y = 210 + row * (card_h + gap)
        card = frame(ctx, f"Rule / {rule['id']}", x, y, card_w, card_h,
                     fill=colour["pureWhite"], radius=12)
        script.add("node.set", ids=[script.ref(card)], props={"strokes": [
            {"type": "solid", "color": colour["hairline"], "strokeWeight": 1}]})
        badge = frame(ctx, f"ID / {rule['id']}", 20, 20, 92, 24,
                      fill=colour["royalBlue"], radius=12, parent=script.ref(card))
        text(ctx, rule["id"], 12, 5, 12, colour["pureWhite"], "Bold", parent=script.ref(badge))
        text(ctx, rule.get("statement", ""), 20, 56, 14, colour["anthracite"],
             width=card_w - 40, parent=script.ref(card))
        scene = by_id.get(rule["id"])
        if scene:
            text(ctx, f"scene: {scene}", 20, card_h - 28, 11, colour["muted"],
                 parent=script.ref(card))
        # The rule travels with the card: Dev Mode shows it as a callout.
        script.add("annotation.add", id=script.ref(card), label=rule.get("statement", ""),
                   category="Development")


# ------------------------------------------------------------------- build

def token_variables(script: Script, tokens: dict) -> None:
    """The palette and the spacing scale, as variables."""
    for collection in ("Colour", "Space"):
        script.add("variable.createCollection", name=collection, modes=["Default"])
    for family, ramp in tokens["color"].items():
        for shade, value in ramp.items():
            script.add("variable.create", collection="Colour", name=f"{family}/{shade}",
                       type="color", value=value)
    for step, value in tokens.get("spacing", {}).items():
        script.add("variable.create", collection="Space", name=f"space/{step}",
                   type="number", value=value)
    # A paint style per approved colour, so a consumer can apply the role
    # rather than re-decide the hex.
    for family, ramp in tokens["color"].items():
        for shade, value in ramp.items():
            script.add("style.create", type="paint", name=f"{family} / {shade}",
                       value=[{"type": "solid", "color": value}])


def build_script(source: Path) -> Script:
    """The command script that produces the project from the token source."""
    tokens = json.loads((source / "core/TOKENS.json").read_text(encoding="utf-8"))
    rules_doc = json.loads((source / "core/rules.json").read_text(encoding="utf-8"))
    manifest = json.loads((source / "assets/icons/icon-manifest.json").read_text(encoding="utf-8"))
    references = [json.loads(path.read_text(encoding="utf-8"))
                  for path in sorted((source / "references").glob("*.json"))]

    colour = dict(FALLBACK)
    for family, ramp in tokens["color"].items():
        for shade, value in ramp.items():
            colour[shade] = value

    script = Script()
    ctx = Ctx(script)
    token_variables(script, tokens)
    build_colour_page(ctx, script, tokens, colour)
    build_contrast_page(ctx, script, tokens, colour)
    build_type_page(ctx, script, tokens, colour)
    build_spacing_page(ctx, script, tokens, colour)
    build_components_page(ctx, script, source, manifest, colour)
    build_scenes_page(ctx, script, source, references, colour)
    build_rules_page(ctx, script, rules_doc.get("rules", []), references, colour)
    return script


def run_script(cli: str, script_path: Path, out: Path) -> tuple[bool, str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [cli, "run", str(script_path), "--out", str(out)],
        capture_output=True, text=True, check=False)
    return result.returncode == 0, result.stdout + result.stderr


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def describe(cli: str, path: Path) -> str:
    """A one-line shape of a project, for the drift report."""
    result = subprocess.run([cli, "info", str(path)], capture_output=True, text=True, check=False)
    first = result.stdout.strip().splitlines()
    if not first:
        return "(unreadable)"
    head = first[0]
    pages = [line.strip() for line in first[1:] if line.strip().startswith("page ")]
    return f"{head} | " + "; ".join(pages)


def check(cli: str | None, source: Path, out: Path, script_path: Path) -> int:
    """The gate: rebuild the project and compare it with the committed one.

    The build is byte-deterministic, so the comparison is over bytes rather
    than over a shape. A shape comparison would let a change of one hex pass
    unnoticed, which is exactly the kind of change that matters here: the
    shape of the project is identical whether the token is #FF6A00 or
    #FF6B00.

    The command script is compared first and separately, because it needs no
    FigCraft at all. The script is what the generator says about the source,
    so comparing it catches the common drift - the source moved and nobody
    rebuilt - on a machine that has no design editor. The project comparison
    then catches the other half: the script was regenerated but the project
    was hand-edited, or the engine changed underneath.

    Exit codes: 0 pass, 1 fail, 3 skipped (nothing to compare against).
    """
    if not out.exists():
        if not script_path.exists():
            print("SKIP: no FigCraft projection is committed")
            return 3
        print(f"FAIL: {out} does not exist; run `python3 figcraft/generate.py`")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        rebuilt_script = Path(tmp) / script_path.name
        script = build_script(source)
        script.write(rebuilt_script)

        # Level one: the command script. No FigCraft needed.
        if script_path.exists():
            if script_path.read_text(encoding="utf-8") != rebuilt_script.read_text(encoding="utf-8"):
                print("FAIL: the FigCraft projection has drifted from the source")
                print("  the command script differs: the generator's output for the current")
                print("  source no longer matches the committed script")
                print(f"  run `python3 figcraft/generate.py` to bring it back")
                return 1
        else:
            print("FAIL: the command script is missing; run `python3 figcraft/generate.py`")
            return 1

        if cli is None:
            print("PASS: the command script matches the source "
                  "(the project itself was not compared: no FigCraft CLI here)")
            return 3

        # Level two: the project itself.
        rebuilt = Path(tmp) / out.name
        ok, output = run_script(cli, rebuilt_script, rebuilt)
        if not ok:
            print("FAIL: the rebuild itself failed")
            sys.stderr.write(output)
            return 1

        committed_digest = digest(out)
        rebuilt_digest = digest(rebuilt)

        if committed_digest == rebuilt_digest:
            print(f"PASS: the project matches the source ({committed_digest[:16]})")
            return 0

        print("FAIL: the project has drifted from the source")
        print(f"  committed {committed_digest}")
        print(f"  rebuilt   {rebuilt_digest}")
        print(f"  committed: {describe(cli, out)}")
        print(f"  rebuilt:   {describe(cli, rebuilt)}")
        print("  the command script matched, so the source did not move: the project was")
        print("  edited by hand, or the engine changed underneath it.")
        print("  a font difference also produces this: the text layout is part of the")
        print("  file, so a machine without the packaged Space Grotesk lays it out")
        print("  differently and the bytes differ with the same script.")
        print(f"  run `python3 figcraft/generate.py` to bring it back")
        return 1


def find_cli(explicit: str | None) -> str | None:
    """The figcraft CLI, or None when this machine has none.

    An explicit path is validated like any other: a CI job that sets
    FIGCRAFT_CLI to a path that is not there should degrade to the level-one
    check, not crash.
    """
    if explicit:
        candidate = Path(explicit)
        return str(candidate) if candidate.is_file() and os.access(candidate, os.X_OK) else None
    candidate = Path(os.path.expanduser("~/.local/bin/figcraft-cli"))
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return str(candidate)
    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="build the gnosix.ds FigCraft project")
    parser.add_argument("--source", default=str(REPO_ROOT),
                        help="the gnosix.ds repository")
    parser.add_argument("--out", default=str(REPO_ROOT / "figcraft" / "gnosix-ds.figcraft"),
                        help="the .figcraft to write")
    parser.add_argument("--script", default=str(REPO_ROOT / "figcraft" / "gnosix-ds.figcraft.jsonl"),
                        help="where to leave the command script")
    parser.add_argument("--cli", default=os.environ.get("FIGCRAFT_CLI"),
                        help="the figcraft CLI to run the project with")
    parser.add_argument("--check", action="store_true",
                        help="rebuild and compare with the committed project; do not write")
    args = parser.parse_args(argv)

    source = Path(args.source).resolve()
    if not (source / "core/TOKENS.json").is_file():
        raise SystemExit(f"not a gnosix.ds repository: {source}")

    out = Path(args.out)
    script_path = Path(args.script)
    cli = find_cli(args.cli)

    if args.check:
        return check(cli, source, out, script_path)

    if cli is None:
        raise SystemExit("no figcraft CLI found; set FIGCRAFT_CLI or pass --cli")

    script = build_script(source)
    script.write(script_path)
    print(f"wrote {script_path} ({len(script.steps)} commands)")

    ok, output = run_script(cli, script_path, out)
    if not ok:
        sys.stderr.write(output)
        return 1
    print(f"wrote {out}")
    print(f"  sha256 {digest(out)}")

    info = subprocess.run([cli, "info", str(out)], capture_output=True, text=True, check=False)
    print(info.stdout.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
