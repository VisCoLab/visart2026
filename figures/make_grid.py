#!/usr/bin/env python3
"""Build SynGallery sample figures for the paper's supplementary material:
a 5-column x 8-row grid of 40 curated renders.

The 40 chosen paintings fill the grid in row-major order (left-to-right,
top-to-bottom). How each cell's camera angle is chosen depends on --mode:

  columns  one angle per column, from --degrees (default 150 120 90 60 30)
  single   the same angle (--degree) in every cell
  random   a random angle per cell (seeded by --seed for reproducibility)

Images are the SynGallery-1024 renders, read from the on-disk source dataset
(byte-identical to patryk-bartkowiak/SynGallery-1024).

Reproduce all three committed figures:
  python figures/make_grid.py --mode single  --degree 60 --out figures/sample_grid_all60.png
  python figures/make_grid.py --mode random  --seed 0    --out figures/sample_grid_random.png
  python figures/make_grid.py --mode columns --degrees 150 120 90 60 30 \
      --out figures/sample_grid_150-120-90-60-30.png
"""

import argparse
import random
from pathlib import Path

from PIL import Image

DATASET = Path("/mnt/storage_6/project_data/pl0896-03/visart-dataset-v2-1024")
ANGLES = [30, 60, 90, 120, 150]
ROWS, COLS = 8, 5
INDICES = [
    2, 4, 49, 74, 147, 151, 161, 176, 545, 852, 856, 859, 860, 861, 875, 882,
    886, 892, 897, 925, 930, 982, 1287, 1293, 1321, 1326, 1327, 1365, 1376,
    1448, 1474, 1594, 1667, 1811, 1840, 1841, 1949, 1961, 1964, 1989,
]
assert len(INDICES) == ROWS * COLS, f"{len(INDICES)} indices != {ROWS*COLS}"

HERE = Path(__file__).resolve().parent


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mode", choices=("columns", "single", "random"), required=True)
    p.add_argument("--degrees", type=int, nargs=COLS, default=[150, 120, 90, 60, 30],
                   help="per-column angles for --mode columns")
    p.add_argument("--degree", type=int, default=60, help="angle for --mode single")
    p.add_argument("--seed", type=int, default=0, help="RNG seed for --mode random")
    p.add_argument("--cell", type=int, default=512)
    p.add_argument("--gutter", type=int, default=8)
    p.add_argument("--out", type=Path, required=True)
    return p.parse_args()


def angle_grid(a):
    """Return an 8x5 matrix of camera angles per cell."""
    if a.mode == "single":
        return [[a.degree] * COLS for _ in range(ROWS)]
    if a.mode == "columns":
        return [[a.degrees[c] for c in range(COLS)] for _ in range(ROWS)]
    rng = random.Random(a.seed)
    return [[rng.choice(ANGLES) for _ in range(COLS)] for _ in range(ROWS)]


def main():
    a = parse_args()
    angles = angle_grid(a)
    W = COLS * a.cell + (COLS + 1) * a.gutter
    H = ROWS * a.cell + (ROWS + 1) * a.gutter
    canvas = Image.new("RGB", (W, H), "white")

    for r in range(ROWS):
        for c in range(COLS):
            idx, deg = INDICES[r * COLS + c], angles[r][c]
            src = DATASET / str(idx) / f"0_rgb_{deg}.png"
            im = Image.open(src).convert("RGBA")
            bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
            im = Image.alpha_composite(bg, im).convert("RGB")
            if im.size != (a.cell, a.cell):
                im = im.resize((a.cell, a.cell), Image.LANCZOS)
            x = a.gutter + c * (a.cell + a.gutter)
            y = a.gutter + r * (a.cell + a.gutter)
            canvas.paste(im, (x, y))

    a.out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(a.out, optimize=True)
    label = {"single": f"all {a.degree}°", "columns": f"columns {a.degrees}",
             "random": f"random (seed {a.seed})"}[a.mode]
    print(f"wrote {a.out.name}  ({W}x{H}, {a.out.stat().st_size/2**20:.1f} MiB) — {label}")


if __name__ == "__main__":
    main()
