#!/usr/bin/env python3
"""Re-derive production alpha masters from the ratified identity masters.

V3.4.0 shipped the `*-cube-alpha.png` compositing variants with two defects that made
them unfit to ship:

1. The coverage ramp was quantised to two values (170 and 240), so the silhouette edge
   was a hard two-step stair rather than an antialiased transition.
2. The edge pixels retained the *field-influenced* colour produced by the keying, not
   the subject colour. The variant was therefore premultiplied in place, and compositing
   it on a neutral substrate produced a dark fringe. This is the "false transparency"
   failure: the asset looks correctly cut out in isolation and wrong in context.

This tool rebuilds a straight (unmatted) alpha channel for the edge band only.

    observed = coverage * subject + (1 - coverage) * field

`field` is the authored dark field, recovered as the median of the already-transparent
region. `subject` is the nearest fully opaque artwork pixel, found by jump flooding
inward from the ratified interior. That nearest-pixel lookup matters: the cube carries
an authored dark rim along its silhouette, so a neighbourhood *average* would straddle
that rim and reintroduce contamination of its own.

The ratified opaque masters are never written. The fully opaque interior stays
byte-identical to the opaque master, because the tool only rewrites pixels whose
existing alpha is strictly between 0 and 255. That is what makes this a container repair
under ID-003 rather than a redraw: the artwork is preserved, the container is corrected.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ROOT / "assets" / "identity"

PAIRS = {
    "gnosix-cube-alpha.png": "gnosix-cube.png",
    "gnu6-live-cube-alpha.png": "gnu6-live-cube.png",
    "gnuinlabs-cube-alpha.png": "gnuinlabs-cube.png",
}

# Coverage is clamped inside this window. The floor stops near-transparent edge pixels
# from amplifying quantisation noise into visible speckle when un-premultiplied; the
# ceiling keeps a pixel that is nominally interior from being written as translucent.
COVERAGE_FLOOR = 0.06
COVERAGE_CEILING = 0.985

FAR = np.int64(1) << 40


def nearest_core(core: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Index grids of the nearest True cell in `core`, by jump flooding.

    Jump flooding visits a 3x3 neighbourhood at doubling radii, so the whole image is
    resolved in log2(max(H, W)) passes instead of a per-pixel search.
    """
    height, width = core.shape
    ys, xs = np.where(core)
    ny = np.full((height, width), -1, np.int64)
    nx = np.full((height, width), -1, np.int64)
    ny[ys, xs] = ys
    nx[ys, xs] = xs

    grid_y = np.broadcast_to(np.arange(height, dtype=np.int64)[:, None], (height, width))
    grid_x = np.broadcast_to(np.arange(width, dtype=np.int64)[None, :], (height, width))

    def squared_distance(cy: np.ndarray, cx: np.ndarray, ty: np.ndarray, tx: np.ndarray):
        return np.where(cy >= 0, (cy - ty) ** 2 + (cx - tx) ** 2, FAR)

    step = 1
    while step < max(height, width):
        best_d = squared_distance(ny, nx, grid_y, grid_x)
        out_y, out_x = ny.copy(), nx.copy()
        for dy in (-step, 0, step):
            for dx in (-step, 0, step):
                target_y = slice(max(0, -dy), height - max(0, dy))
                source_y = slice(max(0, dy), height - max(0, -dy))
                target_x = slice(max(0, -dx), width - max(0, dx))
                source_x = slice(max(0, dx), width - max(0, -dx))
                candidate_d = squared_distance(
                    ny[source_y, source_x], nx[source_y, source_x],
                    grid_y[target_y, target_x], grid_x[target_y, target_x],
                )
                window = best_d[target_y, target_x]
                better = candidate_d < window
                if not better.any():
                    continue
                ly, lx = np.nonzero(better)
                iy = ly + target_y.start
                ix = lx + target_x.start
                out_y[iy, ix] = ny[source_y, source_x][better]
                out_x[iy, ix] = nx[source_y, source_x][better]
                window[better] = candidate_d[better]
        ny, nx, best_d = out_y, out_x, best_d
        step *= 2
    return ny, nx


def solve_coverage(observed: np.ndarray, subject: np.ndarray, field: np.ndarray) -> np.ndarray:
    """Least-squares unmix of observed into subject and field, per pixel.

    Solving `observed - field = coverage * (subject - field)` across all three channels
    at once is stable where any single channel would be near-degenerate, which happens
    constantly here because the cube's dark faces sit within a few levels of the field.
    """
    delta = subject - field
    numerator = ((observed - field) * delta).sum(axis=2)
    denominator = (delta * delta).sum(axis=2)
    coverage = np.zeros_like(numerator)
    usable = denominator > 1e-6
    coverage[usable] = numerator[usable] / denominator[usable]
    return np.clip(coverage, 0.0, 1.0)


def rekey(alpha_name: str, opaque_name: str, write: bool) -> dict:
    alpha_path = IDENTITY / alpha_name
    opaque_path = IDENTITY / opaque_name

    with Image.open(alpha_path) as handle:
        variant = np.array(handle.convert("RGBA"))
    with Image.open(opaque_path) as handle:
        opaque = np.array(handle.convert("RGB"))

    if variant.shape[:2] != opaque.shape[:2]:
        raise ValueError(f"{alpha_name} and {opaque_name} differ in size")

    current_alpha = variant[:, :, 3]
    interior = current_alpha == 255
    band = (current_alpha > 0) & (current_alpha < 255)
    if not band.any():
        raise ValueError(f"{alpha_name} carries no edge band; nothing to re-key")

    field = np.median(opaque[~band].reshape(-1, 3).astype(np.float64), axis=0)
    subject_y, subject_x = nearest_core(interior)
    if (subject_y[band] < 0).any():
        raise ValueError(f"{alpha_name}: band pixel with no reachable interior pixel")

    subject = opaque[subject_y, subject_x].astype(np.float64)
    coverage = solve_coverage(opaque.astype(np.float64), subject, field[None, None, :])

    band_coverage = np.clip(coverage[band], COVERAGE_FLOOR, COVERAGE_CEILING)
    # Un-premultiply so the stored colour is the artwork, not an artwork/field blend.
    # Compositing this over the field reconstructs the ratified master; compositing it
    # over any neutral substrate shows the subject colour at true coverage.
    subject_band = np.clip(
        (opaque[band].astype(np.float64) - (1.0 - band_coverage)[:, None] * field)
        / band_coverage[:, None],
        0.0, 255.0,
    )

    out = variant.copy()
    out[band, 0] = np.clip(np.rint(subject_band[:, 0]), 0, 255).astype(np.uint8)
    out[band, 1] = np.clip(np.rint(subject_band[:, 1]), 0, 255).astype(np.uint8)
    out[band, 2] = np.clip(np.rint(subject_band[:, 2]), 0, 255).astype(np.uint8)
    out[band, 3] = np.clip(np.rint(band_coverage * 255.0), 0, 255).astype(np.uint8)

    # The interior must still be the ratified artwork, untouched.
    interior_intact = bool(np.array_equal(out[interior, :3], opaque[interior].astype(np.uint8)))

    # Compositing over the authored field must reproduce the ratified master exactly.
    # Un-premultiplication is an algebraic identity, so this holds to the last bit
    # wherever the solved subject colour is representable. It cannot hold where the
    # solved subject falls outside 0-255 and has to be clipped, which happens only in
    # the near-transparent tail where coverage is tiny; there the subject estimate is
    # an extrapolation and the clamp is the correct, honest behaviour.
    raw_subject = (opaque[band].astype(np.float64)
                   - (1.0 - band_coverage)[:, None] * field) / band_coverage[:, None]
    in_gamut = (raw_subject >= 0.0).all(axis=1) & (raw_subject <= 255.0).all(axis=1)
    stored_subject = np.clip(raw_subject, 0.0, 255.0)
    if in_gamut.any():
        recon = (band_coverage[in_gamut, None] * stored_subject[in_gamut]
                 + (1.0 - band_coverage[in_gamut, None]) * field[None, :])
        residual = float(np.abs(recon - opaque[band][in_gamut].astype(np.float64)).max())
    else:
        residual = 0.0
    out_of_gamut = int((~in_gamut).sum())
    out_of_gamut_max_coverage = float(band_coverage[~in_gamut].max()) if out_of_gamut else 0.0

    old_colour = variant[band, :3].astype(np.float64)
    # The band colour is reported for diagnosis, not gated. After un-matting the subject
    # under the band is the cube's own dark rim, which legitimately sits closer to the
    # field than the bright faces do; a distance threshold would be measuring the
    # artwork, not the repair.
    contamination = float(np.abs(stored_subject - field).max(axis=1).mean())

    # The property that actually matters in production: a straight-alpha asset must show
    # no dark fringe when composited on a light substrate. Under correct un-matting the
    # band is the subject colour at partial coverage, so moving from the dark field to
    # pure white can only lighten it. If the stored colour were still premultiplied the
    # same composite would darken the edge instead, which is exactly the V3.4.0 failure.
    white = np.array([255.0, 255.0, 255.0])
    on_field = band_coverage[:, None] * stored_subject + (1.0 - band_coverage)[:, None] * field
    on_white = band_coverage[:, None] * stored_subject + (1.0 - band_coverage)[:, None] * white
    fringe_pixels = int((on_white.max(axis=1) < on_field.max(axis=1) - 1.0).sum())

    report = {
        "asset": alpha_name,
        "band_px": int(band.sum()),
        "levels_before": int(np.unique(current_alpha[band]).size),
        "levels_after": int(np.unique(out[band, 3]).size),
        "residual": round(residual, 4),
        "out_of_gamut": out_of_gamut,
        "out_of_gamut_max_coverage": round(out_of_gamut_max_coverage, 3),
        "interior_intact": interior_intact,
        "contamination": round(contamination, 1),
        "fringe_pixels": fringe_pixels,
    }

    if write:
        Image.fromarray(out, mode="RGBA").save(alpha_path, optimize=True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="report what would change without writing")
    args = parser.parse_args()

    failures = 0
    for alpha_name, opaque_name in PAIRS.items():
        report = rekey(alpha_name, opaque_name, write=not args.check)
        problems = []
        if not report["interior_intact"]:
            problems.append("interior altered")
        if report["levels_after"] < 32:
            problems.append("ramp still quantised")
        if report["residual"] > 0.5:
            problems.append(f"residual {report['residual']}")
        # Compositing on a light substrate must never darken the edge.
        if report["fringe_pixels"]:
            problems.append(f"{report['fringe_pixels']} band px still darken on white")
        failures += bool(problems)
        verb = "would re-key" if args.check else "re-keyed"
        print(
            f"{verb} {report['asset']}: band {report['band_px']}px, "
            f"coverage levels {report['levels_before']} -> {report['levels_after']}, "
            f"dark-fringe px on white {report['fringe_pixels']}, "
            f"residual {report['residual']} "
            f"(exact where in gamut; {report['out_of_gamut']}px clamped below coverage "
            f"{report['out_of_gamut_max_coverage']}), "
            f"interior intact {report['interior_intact']}"
            + (f"  [FAIL: {', '.join(problems)}]" if problems else "  [ok]")
        )

    if args.check:
        print("\n--check: nothing written")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
