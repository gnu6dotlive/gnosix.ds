#!/usr/bin/env python3
"""Rebuild the site favicon as a transparent, correctly sized icon set.

The V3.4.0 `site/favicon.png` was 128x128, fully opaque, and carried the ratified
mark's dark field baked into every corner. On a light browser tab or a light title bar
it rendered as a dark square, which is the most visible possible failure for the one
asset a visitor cannot opt out of seeing.

It was also a single undersized file. 128px is not a size any browser requests for a
tab; browsers ask for 32, 16, 180 (touch) and 192 (PWA). Shipping one size means the
browser always has to downscale, and downscale a 128 with no alpha does it badly.

This tool regenerates the icon from the ratified mark master rather than editing the
existing bitmap. The existing file is exactly a LANCZOS downscale of the `viewBox`
crop declared in `gnosix-ds-mark.svg`, so re-deriving from that crop reproduces the
ratified appearance and changes only the container: the dark field becomes alpha, and
the artwork itself is untouched. That is a container repair under ID-003.

The field is keyed with a flood fill from the image border rather than a global
threshold. The mark's dark plate outlines sit close to the field colour, so a threshold
would either eat the outlines or leave a halo; a border-connected fill cannot reach them
because they are enclosed by the plates.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MARK = ROOT / "assets" / "identity" / "gnosix-ds-mark.png"
SITE = ROOT / "site"

# Must match the viewBox declared for gnosix-ds-mark.svg in tools/rebuild_svg_wrappers.py.
CROP = (250, 205, 1000, 955)

SIZES = (16, 32, 48, 180, 192, 512)

# A pixel counts as field while it is within this distance of the seed field colour.
FIELD_TOLERANCE = 10.0


def extract_rgba() -> Image.Image:
    """Return the mark crop with its authored field carried as alpha."""
    with Image.open(MARK) as handle:
        mark = np.array(handle.convert("RGB")).astype(np.float64)
    x0, y0, x1, y1 = CROP
    crop = mark[y0:y1, x0:x1]

    field = np.array([12.0, 13.0, 18.0])
    seed = crop[0, 0]
    if np.abs(seed - field).max() > FIELD_TOLERANCE:
        raise ValueError(f"expected a dark field at the crop origin, found {seed}")

    # Border-connected flood fill: the field is what the corners can reach without
    # crossing artwork. Iterating a binary dilation to a fixed point is simple and, at
    # this image size, fast enough to run inside a test.
    close = np.abs(crop - seed).max(axis=2) <= FIELD_TOLERANCE
    reachable = np.zeros(close.shape, dtype=bool)
    reachable[0, :] = close[0, :]
    reachable[-1, :] = close[-1, :]
    reachable[:, 0] = close[:, 0]
    reachable[:, -1] = close[:, -1]

    while True:
        grown = reachable.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                grown |= np.roll(reachable, (dy, dx), axis=(0, 1))
        grown &= close
        if np.array_equal(grown, reachable):
            break
        reachable = grown

    alpha = np.where(reachable, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([crop.astype(np.uint8), alpha]), mode="RGBA")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="report what would change without writing")
    args = parser.parse_args()

    source = extract_rgba()
    width, height = source.size

    # Interior pixels must be untouched artwork; only the field may become transparent.
    array = np.array(source)
    opaque = array[:, :, 3] == 255
    if not opaque.any():
        print("FAIL: flood fill removed the whole mark", file=sys.stderr)
        return 1
    if opaque.mean() > 0.97:
        print("FAIL: field was not removed", file=sys.stderr)
        return 1

    written = []
    for size in SIZES:
        resized = source.resize((size, size), Image.LANCZOS)
        path = SITE / f"favicon-{size}.png"
        if not args.check:
            resized.save(path, optimize=True)
        written.append((path, resized))

    # Keep favicon.png as the 32px icon so existing references still resolve.
    legacy = dict(written)[SITE / "favicon-32.png"]
    if not args.check:
        legacy.save(SITE / "favicon.png", optimize=True)

    total = sum(p.stat().st_size for p, _ in written if p.exists()) if not args.check else 0
    verb = "would write" if args.check else "wrote"
    print(
        f"{verb} {len(written)} icon sizes from the {width}x{height} mark crop; "
        f"opaque coverage {opaque.mean() * 100:.1f}%; total {total / 1024:.0f} KB"
    )
    if args.check:
        print("--check: nothing written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
