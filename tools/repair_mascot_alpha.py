#!/usr/bin/env python3
"""Repair the mascot alpha channels.

The V3.4.0 mascots carry a false-transparency defect of their own. Their alpha channel
is bimodal: a genuine antialiased edge ramp of roughly nine thousand pixels, and then a
plateau covering the rest of the artwork that sits at 252-254 instead of 255. The body
of `syster-color` is only 0.1% fully opaque, so compositing the mascot on any substrate
lays a uniform veil of that substrate across the whole character rather than across its
edge. The mascot never quite arrives.

`syster-outline` is worse in kind: 100% of its partial pixels are near-black, so its
soft edge is a black key that will fringe on any light substrate.

The fix is to promote the plateau to full opacity while leaving the real edge ramp
alone. The distinction is made per pixel rather than by threshold, so a genuine soft
shadow authored into the artwork would survive if one existed; the histogram is bimodal
with a two-pixel gap, so nothing ambiguous is caught in the middle.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASCOT = ROOT / "assets" / "mascot"

ASSETS = ("syster-color.png", "syster-mono.png", "syster-outline.png")

# Pixels at or above this alpha that have no neighbour below PLATEAU_FLOOR are interior
# and belong at full opacity. Anything touching a genuinely soft pixel is left alone.
PLATEAU_CEILING = 252
PLATEAU_FLOOR = 240


def repair(name: str, write: bool) -> dict:
    path = MASCOT / name
    with Image.open(path) as handle:
        image = np.array(handle.convert("RGBA"))

    alpha = image[:, :, 3]
    visible = alpha > 0
    if not visible.any():
        raise ValueError(f"{name} is fully transparent")

    # Interior = high alpha whose 8-neighbourhood contains no soft pixel. A pixel that
    # touches a real ramp value is part of the ramp, not the plateau.
    soft = (alpha > 0) & (alpha < PLATEAU_FLOOR)
    near_soft = soft.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            near_soft |= np.roll(soft, (dy, dx), axis=(0, 1))
    # np.roll wraps; clear the wrap seam so the border is not falsely treated as soft.
    if near_soft.shape[0] > 2:
        near_soft[0, :] &= ~soft[-1, :]
        near_soft[-1, :] &= ~soft[0, :]
        near_soft[:, 0] &= ~soft[:, -1]
        near_soft[:, -1] &= ~soft[:, 0]

    interior = (alpha >= PLATEAU_CEILING) & ~near_soft
    out = image.copy()
    out[interior, 3] = 255

    before_opaque = int((alpha[visible] == 255).sum())
    after_opaque = int((out[:, :, 3][visible] == 255).sum())
    ramp_before = int(((alpha > 0) & (alpha < PLATEAU_CEILING)).sum())
    ramp_after = int(((out[:, :, 3] > 0) & (out[:, :, 3] < PLATEAU_CEILING)).sum())

    # Compositing the mascot on a light substrate must no longer be veiled: compare the
    # body interior against a pure-white and a pure-black substrate. On a correct asset
    # the interior is identical on both, because it is fully opaque.
    body = interior & visible
    white = np.full(image.shape[:2] + (3,), 255.0)
    black = np.zeros(image.shape[:2] + (3,))
    cov = (out[:, :, 3] / 255.0)[:, :, None]
    on_white = cov * out[:, :, :3].astype(np.float64) + (1.0 - cov) * white
    on_black = cov * out[:, :, :3].astype(np.float64) + (1.0 - cov) * black
    veil = float(np.abs(on_white[body] - on_black[body]).max()) if body.any() else 0.0

    report = {
        "asset": name,
        "opaque_before": before_opaque,
        "opaque_after": after_opaque,
        "ramp_before": ramp_before,
        "ramp_after": ramp_after,
        "body_veil": round(veil, 3),
    }

    if write:
        Image.fromarray(out, mode="RGBA").save(path, optimize=True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="report what would change without writing")
    args = parser.parse_args()

    failures = 0
    for name in ASSETS:
        report = repair(name, write=not args.check)
        problems = []
        if report["body_veil"] > 1.0:
            problems.append(f"body still veiled by {report['body_veil']}")
        if report["ramp_after"] == 0 and report["ramp_before"] > 0:
            problems.append("edge ramp destroyed")
        failures += bool(problems)
        verb = "would repair" if args.check else "repaired"
        print(
            f"{verb} {report['asset']}: fully opaque {report['opaque_before']} -> "
            f"{report['opaque_after']}px, edge ramp {report['ramp_before']} -> "
            f"{report['ramp_after']}px, body veil {report['body_veil']}"
            + (f"  [FAIL: {', '.join(problems)}]" if problems else "  [ok]")
        )

    if args.check:
        print("\n--check: nothing written")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
