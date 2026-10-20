#!/usr/bin/env python3
"""Rebuild the exact-fidelity SVG wrappers as production containers.

Each wrapper is a 4-line `<svg>` around a base64 PNG. Two defects made them unsuitable
to ship:

1. The payload was written twice, once in `href` and once in the deprecated
   `xlink:href`, byte for byte. That doubled a 2.4-3.0 MB file for no rendering benefit:
   every current renderer reads `href` and ignores `xlink:href`. Across the eight
   wrappers this was roughly 21 MB of the 30 MB asset payload.
2. `gnosix-ds-mark.svg` carried only a `viewBox` and no `width`/`height`, so it had no
   intrinsic size. Renderers disagree on the fallback for that, and consumers that
   measure an SVG before layout get a different answer depending on the engine.

`xlink:href` is retained only where the wrapper genuinely targets a renderer old enough
to need it, which after inspection is none of them, so it is dropped from all eight.
The `xmlns:xlink` declaration goes with it. This is a container change: the embedded
raster is untouched, which is what ID-003 requires.
"""

from __future__ import annotations

import argparse
import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ROOT / "assets" / "identity"

# stem -> (png it wraps, intrinsic width, intrinsic height, viewBox)
WRAPPERS = {
    "gnosix-cube": ("gnosix-cube.png", 1254, 1254, "0 0 1254 1254"),
    "gnu6-live-cube": ("gnu6-live-cube.png", 1254, 1254, "0 0 1254 1254"),
    "gnuinlabs-cube": ("gnuinlabs-cube.png", 1254, 1254, "0 0 1254 1254"),
    "gnosix-ds-mark-master": ("gnosix-ds-mark.png", 1254, 1254, "0 0 1254 1254"),
    "gnosix-ds-mark": ("gnosix-ds-mark.png", 750, 750, "250 205 750 750"),
    "gnosix-cube-alpha": ("gnosix-cube-alpha.png", 1254, 1254, "0 0 1254 1254"),
    "gnu6-live-cube-alpha": ("gnu6-live-cube-alpha.png", 1254, 1254, "0 0 1254 1254"),
    "gnuinlabs-cube-alpha": ("gnuinlabs-cube-alpha.png", 1254, 1254, "0 0 1254 1254"),
}

SUBSTRATE_NOTE = (
    " Sanctioned for compositing on neutral substrates only per ID-004; over Signal "
    "Orange, Royal Blue or Beret Green use the opaque master."
)

TITLES = {
    "gnosix-cube": "gnosix-cube — ratified visual master",
    "gnu6-live-cube": "gnu6.live-cube — ratified visual master",
    "gnuinlabs-cube": "gnu.in.labs-cube — ratified visual master",
    "gnosix-ds-mark-master": "Ratified gnosix_DS mark — exact visual master",
    "gnosix-ds-mark": "gnosix_DS ratified mark",
    "gnosix-cube-alpha": "gnosix cube alpha master — ratified compositing variant",
    "gnu6-live-cube-alpha": "gnu6.live cube alpha master — ratified compositing variant",
    "gnuinlabs-cube-alpha": "gnu.in.labs cube alpha master — ratified compositing variant",
}

DESCRIPTIONS = {
    "gnosix-cube": "Exact-fidelity SVG wrapper embedding the ratified PNG. Not a vector-native reconstruction.",
    "gnu6-live-cube": "Exact-fidelity SVG wrapper embedding the ratified PNG. Not a vector-native reconstruction.",
    "gnuinlabs-cube": "Exact-fidelity SVG wrapper embedding the ratified PNG. Not a vector-native reconstruction.",
    "gnosix-ds-mark-master": "Exact-fidelity SVG wrapper embedding the ratified PNG pixel-for-pixel. This is not vector-native reconstruction.",
    "gnosix-ds-mark": "Display crop of the exact ratified master. No artwork pixels are redrawn.",
    "gnosix-cube-alpha": "Exact-fidelity SVG wrapper embedding the ratified alpha-channel PNG. The artwork is byte-identical to the opaque ratified master wherever alpha is 255. Not a vector-native reconstruction." + SUBSTRATE_NOTE,
    "gnu6-live-cube-alpha": "Exact-fidelity SVG wrapper embedding the ratified alpha-channel PNG. The artwork is byte-identical to the opaque ratified master wherever alpha is 255. Not a vector-native reconstruction." + SUBSTRATE_NOTE,
    "gnuinlabs-cube-alpha": "Exact-fidelity SVG wrapper embedding the ratified alpha-channel PNG. The artwork is byte-identical to the opaque ratified master wherever alpha is 255. Not a vector-native reconstruction." + SUBSTRATE_NOTE,
}

DATA_URI = re.compile(r"data:image/png;base64,([A-Za-z0-9+/=]+)")


def build(stem: str) -> tuple[str, dict]:
    png_name, width, height, view_box = WRAPPERS[stem]
    payload = base64.b64encode((IDENTITY / png_name).read_bytes()).decode("ascii")
    source_width = 1254

    preserve = ' preserveAspectRatio="xMidYMid meet"' if stem == "gnosix-ds-mark-master" else ""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="{view_box}">\n'
        f"<title>{TITLES[stem]}</title>\n"
        f"<desc>{DESCRIPTIONS[stem]}</desc>\n"
        f'<image x="0" y="0" width="{source_width}" height="{source_width}"{preserve} '
        f'href="data:image/png;base64,{payload}"/>\n'
        f"</svg>\n"
    )
    path = IDENTITY / f"{stem}.svg"
    stats = {
        "asset": f"{stem}.svg",
        "bytes_before": path.stat().st_size if path.exists() else 0,
        "bytes_after": len(svg.encode("utf-8")),
        "payloads": len(DATA_URI.findall(svg)),
    }
    return svg, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="report what would change without writing")
    args = parser.parse_args()

    failures = 0
    saved_before = saved_after = 0
    for stem in WRAPPERS:
        svg, stats = build(stem)
        problems = []
        if stats["payloads"] != 1:
            problems.append(f"{stats['payloads']} embedded payloads")
        if "xlink:href" in svg:
            problems.append("xlink:href still present")
        if "<text" in svg:
            problems.append("wrapper contains live text")
        if 'width="0"' in svg or 'height="0"' in svg:
            problems.append("zero intrinsic size")
        failures += bool(problems)
        saved_before += stats["bytes_before"]
        saved_after += stats["bytes_after"]
        if not args.check:
            (IDENTITY / f"{stem}.svg").write_text(svg, encoding="utf-8")

    print(
        f"{len(WRAPPERS)} wrappers: {saved_before / 1048576:.1f} MB -> "
        f"{saved_after / 1048576:.1f} MB "
        f"(-{(saved_before - saved_after) / 1048576:.1f} MB)"
    )
    if args.check:
        print("--check: nothing written")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
