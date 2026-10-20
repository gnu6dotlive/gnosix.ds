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

# The document's name, which is what a published library is called.
DOCUMENT_NAME = "gnosix.ds"
LIBRARY_DESCRIPTION = "The gnosix design system: approved colours, spacing, type and the rules that govern them."

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
        # How many pages have been created, so the library can be moved to
        # the last position without a magic number.
        self.pages = 0


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
          fill: str | None = None, radius: int = 0, parent=INHERIT,
          props: dict | None = None) -> int:
    merged = dict(props or {})
    if fill:
        merged["fills"] = [{"type": "solid", "color": fill}]
    if radius:
        merged["cornerRadius"] = radius
    params = {"type": "frame", "name": name, "x": x, "y": y, "width": w, "height": h}
    if merged:
        params["props"] = merged
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


def open_board(ctx: Ctx, script: Script, page: str, name: str, height: int, colour: dict,
               width: int = PAGE_W) -> dict:
    """Start a page and put one board frame on it."""
    # Every board gets its own page. The document's default page is left
    # empty and deleted at the end, because renaming the current page is
    # how a board ends up on the wrong page: page.rename without an id
    # renames whichever page is current, and the current page is the one
    # the last board was built on.
    added = script.add("page.add", name=page)
    script.add("page.select", id=script.ref(added))
    ctx.pages += 1
    # The board sits on the page, not inside the previous page's board.
    board = frame(ctx, name, 0, 0, width, height, fill=colour["shellWhite"], parent=None)
    ctx.parent = script.ref(board)
    return script.ref(board)



# ------------------------------------------------------- the library

class Mains:
    """The component mains, created once on the Library page.

    The boards place instances of these. A main is what the library
    publishes: `library.publish` offers components, component sets, styles
    and variable collections, so anything that is not a component cannot
    travel to another file.
    """

    def __init__(self):
        self.library_page: int | None = None
        self.rule_card: int | None = None
        self.state_pip: int | None = None
        self.specimen: int | None = None
        self.icon_cell: int | None = None
        self.glyphs: dict[str, int] = {}


def build_rule_card_main(ctx: Ctx, script: Script, colour: dict, x: int = 0, y: int = 0) -> int:
    """The rule card: a badge, the statement, the scene it governs.

    Three text properties, so a consumer places the card and writes the
    rule into it without knowing how the card is laid out.
    """
    card = frame(ctx, "Rule Card", x, y, 520, 152, fill=colour["pureWhite"], radius=12)
    script.add("node.set", ids=[script.ref(card)], props={"strokes": [
        {"type": "solid", "color": colour["hairline"], "strokeWeight": 1}]})
    badge = frame(ctx, "ID", 20, 20, 92, 24, fill=colour["royalBlue"], radius=12,
                  parent=script.ref(card))
    badge_text = text(ctx, "ID-000", 12, 5, 12, colour["pureWhite"], "Bold",
                       parent=script.ref(badge))
    statement = text(ctx, "The statement of the rule.", 20, 56, 14, colour["anthracite"],
                     width=480, parent=script.ref(card))
    scene = text(ctx, "scene: reference", 20, 124, 11, colour["muted"],
                 parent=script.ref(card))

    script.add("component.create", ids=[script.ref(card)])
    for name, layer, default in (("id", badge_text, "ID-000"),
                                  ("rule", statement, "The statement of the rule."),
                                  ("scene", scene, "scene: reference")):
        script.add("component.addProperty", id=script.ref(card), name=name, type="text",
                   layer=script.ref(layer), default=default)
    return card


def build_state_pip_main(ctx: Ctx, script: Script, colour: dict, x: int = 0, y: int = 0) -> int:
    """The state pip: a mark whose shape carries the state.

    The reference scene forbids the rounded status capsule and prescribes
    "text + pip instead", so the pip is a mark and not a badge, and its
    shape differs between the two states. The shape is the non-colour cue
    A11Y-001 asks for; the words beside it carry the meaning.

    Two variants under one variant property. The engine creates the
    property and its values itself when components are combined, and
    names them "Property 1", "Default" and "Variant2"; they are renamed
    afterwards, because a published library that offers a variant called
    "Variant2" is not a library anybody can use.
    """
    # A component is a frame or a group, so the mark is a shape inside a
    # transparent frame rather than the shape itself. The frame carries no
    # fill, so nothing is drawn but the mark.
    #
    # Three states, not two: a pairing that meets the body threshold and one
    # that meets only the large threshold are not the same state, and a pip
    # that said "fail" on a passing pairing would be lying. The shapes are
    # the grammar - a filled disc, a ring, a triangle - and the words
    # beside them say which threshold was met.
    body = frame(ctx, "State Pip / body", x, y, 16, 16, fill=None)
    script.add("node.create", type="ellipse", name="mark", x=2, y=2, width=12, height=12,
               parent=script.ref(body),
               props={"fills": [{"type": "solid", "color": colour["beretGreen"]}]})
    large = frame(ctx, "State Pip / large", x + 40, y, 16, 16, fill=None)
    ring = script.add("node.create", type="ellipse", name="mark", x=2, y=2, width=12, height=12,
                      parent=script.ref(large),
                      props={"strokes": [{"type": "solid", "color": colour["royalBlue"],
                                          "strokeWeight": 2}]})
    script.add("object.removeFill", ids=[script.ref(ring)])
    failing = frame(ctx, "State Pip / fail", x + 80, y, 16, 16, fill=None)
    script.add("node.create", type="polygon", name="mark", x=2, y=2, width=12, height=12,
               parent=script.ref(failing),
               props={"fills": [{"type": "solid", "color": colour["alert"]}],
                      "pointCount": 3})
    script.add("component.create", ids=[script.ref(body)])
    script.add("component.create", ids=[script.ref(large)])
    script.add("component.create", ids=[script.ref(failing)])
    script.add("component.combineVariants",
               ids=[script.ref(body), script.ref(large), script.ref(failing)])
    set_id = script.ref(body)

    script.add("component.editProperty", id=set_id, name="Property 1", newName="state",
               value="Default", newValue="body")
    script.add("component.editProperty", id=set_id, name="state",
               value="Variant2", newValue="large")
    script.add("component.editProperty", id=set_id, name="state",
               value="Variant3", newValue="fail")
    return body


def build_specimen_main(ctx: Ctx, script: Script, colour: dict, weights: dict, x: int = 0, y: int = 0) -> int:
    """The type specimen, one variant per ratified weight.

    The weight is a variant rather than a text property, because a text
    property carries a string and not a typographic weight: the specimen's
    own weight is the thing being demonstrated.
    """
    styles = {"regular": "Regular", "medium": "Medium",
              "semibold": "SemiBold", "bold": "Bold"}
    parts = []
    for index, (weight_name, weight) in enumerate(weights.items()):
        # A frame and not a bare text layer: a component is a frame or a
        # group, and the frame also gives the specimen a box to sit in.
        line = frame(ctx, f"Specimen / {weight_name}", x, y + index * 80, 1072, 60, fill=None)
        text(ctx, "Ship interfaces, not mockups", 0, 0, 40, colour["anthracite"],
             styles.get(weight_name, "Regular"), parent=script.ref(line))
        script.add("component.create", ids=[script.ref(line)])
        parts.append(line)
    # All of them at once. Combining a set with another component replaces
    # the set rather than adding to it, so a set built two at a time keeps
    # only the last pair.
    first = parts[0]
    script.add("component.combineVariants", ids=[script.ref(part) for part in parts])
    # The engine names the property and its values itself; a published
    # library that offers a variant called "Variant2" is not usable.
    script.add("component.editProperty", id=script.ref(first), name="Property 1",
               newName="weight", value="Default", newValue="regular")
    for index, weight_name in enumerate(list(weights)[1:], start=2):
        script.add("component.editProperty", id=script.ref(first), name="weight",
                   value=f"Variant{index}", newValue=weight_name)
    return first


def build_library_page(ctx: Ctx, script: Script, tokens: dict, colour: dict, manifest: dict, source: Path, mains: Mains) -> None:
    """The component mains.

    The library's published assets live here, and the boards place instances
    of them. The page is built first because the boards need the mains, and
    moved to the end afterwards: a reader opening the project wants the
    boards, not the machinery.
    """
    library_page = script.add("page.add", name="Library")
    mains.library_page = library_page
    ctx.pages += 1
    board = frame(ctx, "Library / board", 0, 0, PAGE_W, 900, fill=colour["shellWhite"],
                  parent=None)
    ctx.parent = script.ref(board)

    mains.rule_card = build_rule_card_main(ctx, script, colour, x=0, y=0)
    mains.state_pip = build_state_pip_main(ctx, script, colour, x=0, y=200)
    weights = tokens.get("typography", {}).get("weights", {})
    mains.specimen = build_specimen_main(ctx, script, colour, weights, x=0, y=260)
    # The glyphs, and the cell they are shown in.
    mains.glyphs = build_icon_mains(ctx, script, source, manifest, colour, x=0, y=420)
    mains.icon_cell = build_icon_cell_main(ctx, script, colour, mains.glyphs, x=0, y=700)



def build_icon_mains(ctx: Ctx, script: Script, source: Path, manifest: dict, colour: dict,
                     x: int = 0, y: int = 0) -> dict[str, int]:
    """The vendored glyphs, as components.

    A glyph is a component so that it can be swapped: the cell's icon slot
    holds an instance of one, and a consumer replaces it with another. The
    glyphs are the ratified subset from the manifest, so the library offers
    exactly what the package ships and no more.

    The names come from the manifest rather than from the file names, so the
    layer tree reads as the design system and not as a file listing.
    """
    entries = manifest.get("entries", [])
    mains: dict[str, int] = {}
    per_row = 16
    for index, entry in enumerate(entries):
        column = index % per_row
        row = index // per_row
        cell_x = x + column * 40
        cell_y = y + row * 40
        glyph = script.add("file.import", path=entry["path"])
        script.add("object.rename", ids=[script.ref(glyph)], name=entry["name"])
        script.add("node.reparent", ids=[script.ref(glyph)], parent=ctx.parent)
        script.add("node.set", ids=[script.ref(glyph)],
                   props={"x": cell_x, "y": cell_y, "width": 24, "height": 24})
        script.add("component.create", ids=[script.ref(glyph)])
        mains[entry["name"]] = glyph
    return mains


def build_icon_cell_main(ctx: Ctx, script: Script, colour: dict, glyphs: dict[str, int],
                         x: int = 0, y: int = 0) -> int:
    """The cell a glyph is shown in, with the glyph swappable.

    The cell carries an instance of one of the glyphs and an instance-swap
    property, so a consumer places the cell and says which glyph it holds.
    The label is a text property for the same reason.
    """
    cell = frame(ctx, "Icon Cell", x, y, 88, 120, fill=colour["pureWhite"], radius=8)
    script.add("node.set", ids=[script.ref(cell)], props={"strokes": [
        {"type": "solid", "color": colour["hairline"], "strokeWeight": 1}]})

    # The first glyph in the manifest is the default the swap property
    # offers; the others are the preferred values.
    names = list(glyphs)
    default = names[0] if names else None
    # Both the glyph and the label are inside the cell: a property binds to
    # a layer of the component, so a label beside the cell would not be
    # carried by it.
    slot = script.add("instance.create", component=script.ref(glyphs[default]),
                      x=32, y=20, parent=script.ref(cell))
    label = text(ctx, default, 0, 84, 11, colour["slate"], width=88, align="center",
                 parent=script.ref(cell))

    script.add("component.create", ids=[script.ref(cell)])
    script.add("component.addProperty", id=script.ref(cell), name="icon", type="instanceSwap",
               layer=script.ref(slot), default=default,
               preferred=[script.ref(glyphs[name]) for name in names])
    script.add("component.addProperty", id=script.ref(cell), name="name", type="text",
               layer=script.ref(label), default=default)
    return cell


def build_web_page(ctx: Ctx, script: Script, source: Path, colour: dict, mains: Mains) -> None:
    """A web surface, drawn in the system.

    This is the system's own vocabulary applied to a page: the substrates are
    the two the contract names, the type is the ratified family, the accents
    are the approved colours, and the icons come from the ratified subset
    through the library's own cell.

    The dark band is not a theme. gnosix is a substrate system: a page is
    light or it is the other substrate, and the meaning is in the pairing
    rather than in a mode.
    """
    width, margin = 1440, 96
    content = width - 2 * margin

    height = 72 + 560 + 420 + 300 + 140
    open_board(ctx, script, "Web", "Web / Landing", height, colour, width=width)
    board = ctx.parent

    def band(y: int, h: int, fill: str) -> dict:
        """A full-bleed band across the page."""
        return script.ref(rect(ctx, f"Band {y}", 0, y, width, h, fill))

    def action(label: str, x: int, y: int, primary: bool) -> dict:
        """A button. Not a capsule: CMP-001 forbids the rounded status
        capsule, and the reference scene's buttons have a modest radius."""
        fill = colour["signalOrange"] if primary else colour["pureWhite"]
        ink = colour["pureWhite"] if primary else colour["anthracite"]
        button = frame(ctx, f"Action / {label}", x, y, 0, 48, fill=fill, radius=10,
                       props={"layout": "horizontal", "padding": [0, 24, 0, 24]})
        script.add("node.set", ids=[script.ref(button)], props={"sizingH": "hug"})
        if not primary:
            script.add("node.set", ids=[script.ref(button)], props={"strokes": [
                {"type": "solid", "color": colour["hairline"], "strokeWeight": 1}]})
        text(ctx, label, 24, 15, 16, ink, "Bold", parent=script.ref(button))
        return script.ref(button)

    # ---- nav ----------------------------------------------------------
    text(ctx, "gnosix", margin, 26, 24, colour["anthracite"], "Bold")
    links = ("Contract", "Targets", "Rules", "Library")
    for index, label in enumerate(links):
        text(ctx, label, width - margin - 190 - 24 - len(links) * 110 + index * 110,
             32, 16, colour["slate"])
    action("Read the contract", width - margin - 190, 18, True)

    # ---- hero ---------------------------------------------------------
    text(ctx, "PORTABLE DESIGN CONTRACT", margin, 150, 12, colour["signalOrange"],
         "Bold", tracking="14%")
    text(ctx, "A design system that travels,", margin, 186, 56, colour["anthracite"], "Bold")
    text(ctx, "and that your agents can drive.", margin, 250, 56, colour["anthracite"], "Bold")
    text(ctx, "Rules, tokens, reference scenes and explicit target mappings, in one "
              "package and in one file. Nothing here is a picture of a thing.",
         margin, 340, 20, colour["slate"], width=520)
    action("Get started", margin, 440, True)
    action("See the library", margin + 190, 440, False)

    # The identity master, the alpha variant, on the other substrate. This
    # is ID-004 in practice: the alpha master is sanctioned on a neutral
    # substrate, and pure white is one.
    image = script.add("file.import", path="assets/identity/gnosix-cube-alpha.png")
    script.add("object.rename", ids=[script.ref(image)], name="Identity / gnosix")
    script.add("node.reparent", ids=[script.ref(image)], parent=board)
    script.add("node.set", ids=[script.ref(image)],
               props={"x": width - margin - 320, "y": 150, "width": 320, "height": 320})

    # ---- features, on the other substrate ------------------------------
    band(632, 420, colour["shellWhite"])
    features = [
        ("layers-subtract", "One vocabulary",
         "Portable roles, stable rule ids and one approved token source."),
        ("palette", "Approved colours",
         "Twenty-one colours and four weights, each with its approved pairing."),
        ("code", "Real handoff",
         "CSS, HTML and React generated from the design that shipped."),
    ]
    card_w = (content - 2 * 32) // 3
    for index, (glyph, title, body) in enumerate(features):
        x = margin + index * (card_w + 32)
        card = frame(ctx, f"Feature / {title}", x, 704, card_w, 276,
                     fill=colour["pureWhite"], radius=16)
        script.add("node.set", ids=[script.ref(card)], props={"strokes": [
            {"type": "solid", "color": colour["hairline"], "strokeWeight": 1}]})
        # The glyph itself, not the cell: the cell carries the glyph's
        # name, which a feature card has no use for.
        mark = script.add("instance.create", component=script.ref(mains.glyphs[glyph]),
                          x=28, y=28, parent=script.ref(card))
        text(ctx, title, 28, 176, 22, colour["anthracite"], "Bold", parent=script.ref(card))
        text(ctx, body, 28, 212, 16, colour["slate"], width=card_w - 56,
             parent=script.ref(card))

    # ---- the other substrate -------------------------------------------
    band(1052, 300, colour["anthracite"])
    text(ctx, "Ship the contract, not a copy of it.", margin, 1108, 40,
         colour["pureWhite"], "Bold")
    text(ctx, "The package is the source. The projections follow it, and the "
              "gates say when they have not.",
         margin, 1164, 18, colour["hairline"], width=560)
    button = frame(ctx, "Action / Get started", width - margin - 180, 1150, 0, 48,
                   fill=colour["pureWhite"], radius=10,
                   props={"layout": "horizontal", "padding": [0, 24, 0, 24]})
    script.add("node.set", ids=[script.ref(button)], props={"sizingH": "hug"})
    text(ctx, "Get started", 24, 15, 16, colour["anthracite"], "Bold",
         parent=script.ref(button))

    # ---- footer --------------------------------------------------------
    text(ctx, "gnosix", margin, 1372, 20, colour["anthracite"], "Bold")
    text(ctx, "Portable design contract · Apache-2.0 sources, MIT assets",
         margin + 90, 1376, 14, colour["muted"])



def build_prototype_page(ctx: Ctx, script: Script, colour: dict, mains: Mains) -> None:
    """The three-state machine, wired as a prototype.

    The contract's own state scene is a three-step machine - intent,
    pending, observed - and STA-001 says the projection must not claim
    success before the observation. So the states are written in words, as
    the contract's own scene does, and the glyph beside them comes from the
    ratified subset: clock for intent, loader for pending, check for
    observed. Nothing here is a hand-authored mark, which is what ICON-001
    asks for, and no state is a capsule, which is what CMP-001 forbids.

    The screens are connected with a click that navigates, and the flow
    starts at the first one.
    """
    width, height = 1000, 620
    states = [
        ("01 / INTENT", "Request pending",
         "Requested on intent. Not an observed result.",
         "clock", colour["slate"], "Requesting", "Now"),
        ("02 / PENDING", "Waiting for observation",
         "The request was made. The result has not been observed yet.",
         "loader-2", colour["royalBlue"], "Observed", "Now"),
        ("03 / OBSERVED", "Observed and reconciled",
         "The observation arrived and was reconciled with what was intended.",
         "check", colour["beretGreen"], "Start again", "Now"),
    ]

    # The screens sit at the top level of the page, not inside a board: a
    # flow starts at a top-level frame, and a prototype's screens are
    # top-level frames in any case.
    added = script.add("page.add", name="Prototype")
    script.add("page.select", id=script.ref(added))
    ctx.pages += 1
    ctx.parent = None

    frames = []
    for index, (label, title, body, glyph, accent, action, target) in enumerate(states):
        x = 64 + index * (width + 64)
        screen = frame(ctx, f"Screen / {label}", x, 200, width, height,
                       fill=colour["pureWhite"], radius=16, parent=None)
        script.add("node.set", ids=[script.ref(screen)], props={"strokes": [
            {"type": "solid", "color": colour["hairline"], "strokeWeight": 1}]})

        text(ctx, label, 48, 48, 12, accent, "Bold", tracking="14%",
             parent=script.ref(screen))
        text(ctx, title, 48, 88, 40, colour["anthracite"], "Bold",
             parent=script.ref(screen))
        text(ctx, body, 48, 148, 18, colour["slate"], width=520,
             parent=script.ref(screen))

        # The state mark: a glyph from the ratified subset, in the state
        # colour. It is a mark beside the words, not a capsule.
        mark = script.add("instance.create", component=script.ref(mains.glyphs[glyph]),
                          x=48, y=228, parent=script.ref(screen))
        script.add("node.set", ids=[script.ref(mark)], props={"width": 32, "height": 32})
        text(ctx, label.split("/")[-1].strip(), 96, 236, 14, accent, "Bold",
             parent=script.ref(screen))

        button = frame(ctx, f"Action / {action}", 48, height - 108, 0, 48,
                       fill=colour["signalOrange"], radius=10,
                       props={"layout": "horizontal", "padding": [0, 24, 0, 24],
                              "sizingH": "hug", "sizingV": "hug"},
                       parent=script.ref(screen))
        text(ctx, action, 24, 15, 16, colour["pureWhite"], "Bold",
             parent=script.ref(button))
        frames.append((script.ref(screen), script.ref(button), action, target))

    # The connections. A click on a button navigates to the next screen, and
    # the transition is a dissolve, so the change of state is legible.
    for index in range(len(frames) - 1):
        source, button, action, _ = frames[index]
        target = frames[index + 1][0]
        script.add("proto.interaction.add",
                   id=button,
                   trigger={"type": "onClick"},
                   action={"type": "navigate", "dest": target},
                   transition={"type": "dissolve"}, durationMs=200)

    # The last screen starts again at the first.
    last = frames[-1]
    script.add("proto.interaction.add",
               id=last[1],
               trigger={"type": "onClick"},
               action={"type": "navigate", "dest": frames[0][0]},
               transition={"type": "dissolve"}, durationMs=200)

    # The flow, starting at the first screen.
    script.add("proto.flow.add", start=frames[0][0], name="Request lifecycle")
    script.add("proto.settings", device="Desktop", background=colour["shellWhite"])


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


def build_contrast_page(ctx: Ctx, script: Script, tokens: dict, colour: dict, mains: Mains) -> None:
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

        # The verdict is written in words, and marked with a pip whose shape
        # differs. A rounded status capsule is the forbidden form: the
        # reference scene shows one struck through, with "text + pip
        # instead", and CMP-001 is the rule that forbids it. The words are
        # also the non-colour state cue A11Y-001 asks for.
        #
        # The ink is the neutral one, because the palette has no colour that
        # reads as a failure and still passes AA on white: Signal Orange is
        # 2.87 against white, and the approved pairings do not include a
        # failing ink. The pip carries the tone; the words carry the
        # meaning.
        if ratio >= 4.5:
            verdict, state = "AA body", "body"
        elif ratio >= 3.0:
            verdict, state = "AA large", "large"
        else:
            verdict, state = "fails AA", "fail"
        pip = script.add("instance.create", component=script.ref(mains.state_pip),
                         x=900, y=42, parent=script.ref(row))
        script.add("instance.setProperties", ids=[script.ref(pip)],
                   properties={"state": state})
        text(ctx, verdict, 924, 44, 12, colour["anthracite"], "Medium",
             parent=script.ref(row))
        y += 112


def build_type_page(ctx: Ctx, script: Script, tokens: dict, colour: dict, mains: Mains) -> None:
    """The ratified weights, as specimens and as text styles."""
    typography = tokens.get("typography", {})
    weights = typography.get("weights", {})
    primary = (typography.get("primary") or ["Space Grotesk"])[0]
    styles = {"regular": "Regular", "medium": "Medium",
              "semibold": "SemiBold", "bold": "Bold"}

    open_board(ctx, script, "Type", "Type / board", 210 + len(weights) * 130 + 180, colour)
    title_block(ctx, "Type",
                "Space Grotesk, the only visual family. Weights are the ratified "
                "four; the technical style adds tabular figures.", colour)

    y = 210
    for weight_name, weight in weights.items():
        section_label(ctx, f"{weight_name} / {weight}", MARGIN, y, colour)
        y += 28
        # An instance of the specimen set, with the weight as a variant.
        specimen = script.add("instance.create", component=script.ref(mains.specimen),
                              x=MARGIN, y=y, parent=ctx.parent)
        script.add("instance.setProperties", ids=[script.ref(specimen)],
                   properties={"weight": weight_name})
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
        # The style is named by its number, not by its name, so the two
        # projections can be compared: the package states the weights as
        # numbers in its custom properties, and a name would not match.
        script.add("style.create", type="text", name=f"Type / {weight}",
                   value={"fontSize": 16, "fontFamily": primary,
                          "fontStyle": styles.get(weight_name, "Regular")})


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


def build_components_page(ctx: Ctx, script: Script, manifest: dict, colour: dict, mains: Mains) -> None:
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
    y = 210
    for kind, label, cell, per_row in (("icon", "Icons", 88, 10), ("flag", "Flags", 88, 10)):
        entries = entries_by_kind.get(kind, [])
        section_label(ctx, f"{label} / {len(entries)}", MARGIN, y, colour)
        y += 30
        for index, entry in enumerate(entries):
            column = index % per_row
            row = index // per_row
            x = MARGIN + column * (cell + 16)
            cy = y + row * 128
            # An instance of the cell, with the glyph swapped in. The glyph
            # is a component, so the swap is what a consumer does too.
            cell_frame = script.add("instance.create", component=script.ref(mains.icon_cell),
                                    x=x, y=cy, parent=ctx.parent)
            script.add("instance.setProperties", ids=[script.ref(cell_frame)], properties={
                "icon": script.ref(mains.glyphs[entry["name"]]),
                "name": entry["name"],
            })
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
        image = script.add("file.import", path=f"assets/identity/{filename}")
        script.add("object.rename", ids=[script.ref(image)], name=label)
        script.add("node.reparent", ids=[script.ref(image)], parent=script.ref(cell))
        script.add("node.set", ids=[script.ref(image)], props={"x": 8, "y": 8,
                                                               "width": 152, "height": 152})
        text(ctx, label, x, y + 176, 12, colour["slate"], width=168)


def build_scenes_page(ctx: Ctx, script: Script, references: list[dict], colour: dict) -> None:
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
        scene = script.add("file.import", path=reference["artwork"])
        script.add("object.rename", ids=[script.ref(scene)], name=reference.get("id", "scene"))
        script.add("node.reparent", ids=[script.ref(scene)], parent=ctx.parent)
        # The scenes are 1200 wide, the width of the board, so they sit
        # full-bleed. Insetting them by the margin would push their right
        # edge past the board and clip it.
        script.add("node.set", ids=[script.ref(scene)], props={"x": 0, "y": y})
        y += 720 + 56


def build_rules_page(ctx: Ctx, script: Script, rules: list[dict], references: list[dict], colour: dict, mains: Mains) -> None:
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
        scene = by_id.get(rule["id"])
        # An instance of the published Rule Card, not a copy of it: the
        # card's layout lives in the main, so a change to the main changes
        # every card on this page.
        card = script.add("instance.create", component=script.ref(mains.rule_card),
                          x=x, y=y, parent=ctx.parent)
        script.add("instance.setProperties", ids=[script.ref(card)], properties={
            "id": rule["id"],
            "rule": rule.get("statement", ""),
            "scene": f"scene: {scene}" if scene else "",
        })
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

    # The colours the boards are drawn with, named explicitly. Folding every
    # shade into one flat dict would leave "base" and "royalBlue" meaning
    # whichever family happened to be last, and the boards would be drawn in
    # a shade nobody ratified.
    colour = dict(FALLBACK)
    for name, value in tokens["color"]["neutral"].items():
        colour[name] = value
    colour["signalOrange"] = tokens["color"]["signalOrange"]["base"]
    colour["beretGreen"] = tokens["color"]["beretGreen"]["base"]
    colour["royalBlue"] = tokens["color"]["royalBlue"]["base"]
    colour["alert"] = tokens["color"]["semantic"]["alert"]

    script = Script()
    ctx = Ctx(script)
    mains = Mains()

    # The document's name is what a published library is called, and the
    # default is "Untitled".
    script.add("file.rename", name=DOCUMENT_NAME)

    token_variables(script, tokens)
    # The library first: the boards place instances of its mains.
    build_library_page(ctx, script, tokens, colour, manifest, source, mains)
    build_colour_page(ctx, script, tokens, colour)
    build_contrast_page(ctx, script, tokens, colour, mains)
    build_type_page(ctx, script, tokens, colour, mains)
    build_spacing_page(ctx, script, tokens, colour)
    build_components_page(ctx, script, manifest, colour, mains)
    build_scenes_page(ctx, script, references, colour)
    build_rules_page(ctx, script, rules_doc.get("rules", []), references, colour, mains)
    build_web_page(ctx, script, source, colour, mains)
    build_prototype_page(ctx, script, colour, mains)

    # The library is the last page: a reader opening the project wants the
    # boards, not the machinery. It was created first, because the boards
    # need its mains, so it is moved afterwards. The index counts from the
    # start, and the document's default page is still in front of it, so
    # the last position is the number of pages created.
    script.add("page.move", id=script.ref(mains.library_page), index=ctx.pages)

    # The document's default page, empty since every board got its own.
    script.add("page.delete", id=1)

    # Publishing makes the file a library other files can consume. It is
    # part of the build because the library is a published asset, not
    # something a consumer has to do by hand.
    script.add("library.publish", description=LIBRARY_DESCRIPTION)
    return script


def run_script(cli: str, script_path: Path, out: Path, cwd: Path) -> tuple[bool, str]:
    """Run the command script.

    The working directory is the repository root, because the script's file
    paths are relative to it. A relative path in a script is resolved
    against the working directory of the process that runs it, so running
    the script from anywhere else would import the wrong files, or none.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [cli, "run", str(script_path), "--out", str(out)],
        cwd=cwd, capture_output=True, text=True, check=False)
    return result.returncode == 0, result.stdout + result.stderr


# The receipt the engine writes when a library is published. Its id and its
# timestamp are minted at the moment of publication, so they differ on every
# build even when nothing about the design changed.
LIBRARY_RECEIPT = "library/manifest.json"


def digest(path: Path) -> str:
    """The digest of the design content, not of the container.

    The archive is a zip, and publishing a library writes a receipt into it
    with a fresh id and a fresh timestamp. The design itself - the document
    and the images - is byte for byte the same from one build to the next,
    and that is what the gate is about. So the receipt is compared with its
    two volatile fields removed, and everything else with its bytes.
    """
    import zipfile

    parts = []
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            data = archive.read(name)
            if name == LIBRARY_RECEIPT:
                receipt = json.loads(data)
                receipt.pop("id", None)
                receipt.pop("time", None)
                data = json.dumps(receipt, sort_keys=True).encode("utf-8")
            parts.append(f"{name}\0{hashlib.sha256(data).hexdigest()}\n")
    return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()


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
        ok, output = run_script(cli, rebuilt_script, rebuilt, source)
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

    ok, output = run_script(cli, script_path, out, source)
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
