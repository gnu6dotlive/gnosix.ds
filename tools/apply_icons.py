#!/usr/bin/env python3
"""Replace ad-hoc text glyphs in a consumer surface with ratified Tabler icons.

The package now has a ratified icon set and rule `ICON-001`, which says interface
glyphs come from that set. Before this tool, the site carried three glyphs that were
typed characters standing in for icons: an arrow-down-right, an arrow-up-right and a
multiplication sign used as a close control. A character that renders as an icon is
still an icon, with none of the guarantees: it inherits the font's metrics, it cannot be
recoloured independently, and it is a different shape on every platform.

This tool rewrites those occurrences to inline SVG references to the vendored set.
Inline rather than ``<img>`` because the icons are ``currentColor`` and 24x24 with a
2px stroke: they need to inherit text colour and scale with type size, and an
``<img>`` cannot do either.

Usage:

    python tools/apply_icons.py --check   # report what would change, write nothing
    python tools/apply_icons.py --apply   # rewrite the surface

Inline rather than ``<img>`` because the icons are ``currentColor`` and 24x24 with a
2px stroke: they need to inherit text colour and scale with type size, and an
``<img>`` cannot do either.

A note on the sprite. ``<use href="sprite.svg#name">`` works in an HTML document, and
this is the right form there: one file, one request, recolourable through
``currentColor``. It does **not** work inside a standalone SVG document that a browser
loads through ``<img>``, because SVG in an image context is not allowed to pull in
external resources. The reference scenes under ``references/`` are consumed exactly
that way, so a glyph added to one of them has to be inlined into the document rather
than referenced. ``--inline`` does that, resolving each symbol against the sprite and
writing the geometry directly into the document.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site" / "index.html"
CSS = ROOT / "site" / "style.css"

# character -> ratified icon name
GLYPH_MAP = {
    "↘": "arrow-down-right",
    "↗": "arrow-up-right",
    "×": "x",
}

# Marks the inline SVG so the rewrite is idempotent and so the test can find every
# icon reference the page makes.
ICON_OPEN = '<svg class="gnosix-icon" aria-hidden="true" focusable="false"'


def icon_svg(name: str, size: int = 16) -> str:
    """An icon that references a symbol in the document's own inline sprite.

    The reference is a same-document fragment (``#name``), not a path to the sprite
    file. A cross-file ``<use>`` is blocked by the browser when the page is opened
    from disk over ``file://``, and this package's reference surfaces are static files
    people open directly. The reference scenes under ``references/`` already inline
    their font for the same reason.
    """
    return (
        f'{ICON_OPEN} width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'<use href="#{name}"></use>'
        f"</svg>"
    )


SPRITE = ROOT / "assets" / "icons" / "sprite.svg"

SPRITE_BLOCK_START = '<!-- ICON-001: ratified Tabler symbols, inlined so the surface renders from disk. -->'
SPRITE_BLOCK_END = "<!-- end ratified icon sprite -->"


def sprite_block(used: set[str]) -> str:
    """The inline sprite, containing only the symbols the surface actually uses.

    Inlining all 41 ratified symbols would ship 38 unused ones in every page that
    embeds the sprite. The vendored sprite file remains the full set for consumers
    that reference it as a file; this is just the subset a surface draws.
    """
    if not SPRITE.is_file():
        raise FileNotFoundError("assets/icons/sprite.svg is missing; run vendor_icons.py --fetch")
    text = SPRITE.read_text()
    symbols = re.findall(r'<symbol id="[A-Za-z0-9-]+"[^>]*>.*?</symbol>', text, re.DOTALL)
    if not symbols:
        raise ValueError("the sprite contains no symbols")
    selected = [s for s in symbols if re.search(r'<symbol id="([A-Za-z0-9-]+)"', s).group(1) in used]
    if not selected:
        raise ValueError("the surface uses no icons")
    body = "\n".join(selected)
    return (
        f'{SPRITE_BLOCK_START}\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true">\n'
        f"{body}\n"
        f"</svg>\n"
        f"{SPRITE_BLOCK_END}"
    )


def inject_sprite(text: str) -> str:
    """Place the inline sprite at the top of the body, replacing any previous one."""
    used = set(re.findall(r'<use href="#([A-Za-z0-9-]+)"', text))
    block = sprite_block(used)
    pattern = re.compile(
        re.escape(SPRITE_BLOCK_START) + r".*?" + re.escape(SPRITE_BLOCK_END) + r"\n?",
        re.DOTALL,
    )
    if pattern.search(text):
        return pattern.sub(block + "\n", text)
    marker = "<body>"
    index = text.find(marker)
    if index < 0:
        raise ValueError("the surface has no <body> to place the sprite in")
    index += len(marker)
    return text[:index] + "\n" + block + "\n" + text[index:]


def sprite_geometry(name: str) -> str:
    """Return the inner geometry of a symbol, for inlining into a standalone SVG."""
    if not SPRITE.is_file():
        raise FileNotFoundError("assets/icons/sprite.svg is missing; run vendor_icons.py --fetch")
    text = SPRITE.read_text()
    match = re.search(
        r'<symbol id="' + re.escape(name) + r'"[^>]*>(.*?)</symbol>', text, re.DOTALL
    )
    if not match:
        raise KeyError(f"the sprite has no symbol named {name}")
    return match.group(1).strip()


def inline_svg_icons(text: str) -> tuple[str, int]:
    """Replace external sprite references with inlined geometry.

    Needed for any standalone SVG consumed through an ``<img>`` element, where the
    browser will not resolve an external reference.
    """
    pattern = re.compile(
        r'<use href="[^"]*sprite\.svg#([A-Za-z0-9-]+)"\s*></use>'
    )

    def substitute(match: re.Match) -> str:
        return sprite_geometry(match.group(1))

    text, count = pattern.subn(substitute, text)
    return text, count


# The state pip in the actions reference scene is a filled disc standing in for a UI
# marker. It is drawn as a text character today, so it inherits the font's metrics and
# cannot be recoloured independently of the label. It becomes the ratified circle-dot.
#
# The other non-ASCII characters in the reference scenes are prose typography, not
# interface glyphs: the bullet separating footer metadata, the arrow in a sentence
# describing reading order, the not-equal sign in a sentence contrasting concepts, and
# the minus sign inside a number. ICON-001 governs interface glyphs, so those stay.
PIP_PATTERN = re.compile(
    r'<text x="102" y="560" font-size="16" fill="#111418" font-weight="600"\s*>'
    r"●\s+Request pending — awaiting observation</text>"
)
PIP_REPLACEMENT = (
    '<circle cx="106" cy="554" r="4" fill="#111418"/>'
    '<text x="118" y="560" font-size="16" fill="#111418" font-weight="600">'
    "Request pending — awaiting observation</text>"
)


def rewrite_html(text: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    # Normalise any previously written external sprite reference to a same-document one.
    text = re.sub(
        r'<use href="[^"]*sprite\.svg#([A-Za-z0-9-]+)"\s*></use>',
        r'<use href="#\1"></use>',
        text,
    )

    # 1. A glyph standing alone inside a decorative span.
    for char, name in GLYPH_MAP.items():
        pattern = re.compile(
            r'(<span aria-hidden="true">)' + re.escape(char) + r"(</span>)"
        )
        replacement = r"\g<1>" + icon_svg(name) + r"\g<2>"
        text, count = pattern.subn(replacement, text)
        if count:
            changes.append((f"{char!r} in a decorative span", str(count)))

    # 2. A glyph trailing the text of a link. The icon is decorative because the link
    #    already carries its own label, so it is hidden from assistive technology.
    for char, name in GLYPH_MAP.items():
        if char == "×":
            continue
        pattern = re.compile(re.escape(char) + r"(</a>)")
        replacement = icon_svg(name) + r"\g<1>"
        text, count = pattern.subn(replacement, text)
        if count:
            changes.append((f"{char!r} trailing a link", str(count)))

    # 3. The close control is a button with visible text, not a decorative span.
    close_pattern = re.compile(
        r'(<button class="dialog-close" type="button" aria-label="Close enlarged reference">)'
        r"Close " + re.escape("×") + r"(</button>)"
    )
    replacement = (
        r'\g<1>' + icon_svg("x", 18) + '<span class="dialog-close-label">Close</span>\g<2>'
    )
    text, count = close_pattern.subn(replacement, text)
    if count:
        changes.append(("'×' on the close control", str(count)))

    return text, changes


def rewrite_css(text: str) -> str:
    if ".ui-icon" in text:
        return text
    rule = """
/* ICON-001: interface glyphs are ratified Tabler icons. The shared icon layer lives in
   profiles/web/icons.css and is imported by the site, so the glyph rules are declared
   once for every consumer rather than per surface. Only the close control's own
   layout belongs here. */
.dialog-close {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
"""
    return text.rstrip() + "\n" + rule


def rewrite_reference_scenes(dry_run: bool = False) -> list[tuple[str, str]]:
    """Replace the character-drawn state pip in the reference scenes with a vector mark."""
    changes: list[tuple[str, str]] = []
    for path in sorted((ROOT / "references").glob("*.svg")):
        text = path.read_text()
        rewritten, count = PIP_PATTERN.subn(PIP_REPLACEMENT, text)
        if not count:
            continue
        if not dry_run:
            path.write_text(rewritten)
        changes.append((f"{path.name} state pip", str(count)))
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--inline", action="store_true",
                       help="inline sprite references into standalone SVG documents")
    args = parser.parse_args()

    if args.inline:
        total = 0
        for path in sorted((ROOT / "references").glob("*.svg")):
            text = path.read_text()
            rewritten, count = inline_svg_icons(text)
            if count:
                path.write_text(rewritten)
                print(f"inlined {count} sprite reference(s) in {path.name}")
                total += count
        print(f"inlined {total} sprite reference(s) in total")
        return 0

    html = SITE.read_text()
    rewritten, changes = rewrite_html(html)
    css = rewrite_css(CSS.read_text())

    # The reference scenes carry a character-drawn state pip, which is a separate
    # surface from the site and is rewritten independently of the site pass.
    scene_changes = rewrite_reference_scenes(dry_run=args.check)

    rewritten = inject_sprite(rewritten)

    if args.apply:
        SITE.write_text(rewritten)
        CSS.write_text(css)
    changes.extend(scene_changes)

    remaining = {char: rewritten.count(char) for char in GLYPH_MAP if char in rewritten}
    total = sum(int(n) for _, n in changes)

    if remaining:
        for char, count in remaining.items():
            print(f"FAIL: {count} ad-hoc glyph(s) {char!r} still present", file=sys.stderr)
        return 1

    verb = "would replace" if args.check else "replaced"
    for char, count in changes:
        print(f"{verb} {count} x {char!r}")
    print(f"{verb} {total} ad-hoc glyph(s) in total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
