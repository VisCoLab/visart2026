#!/usr/bin/env python3
"""Build SynGallery sample figures for the paper's supplementary material:
5-column grids of curated renders, 8/7/6 rows (40/35/30 cells).

There are multiple curated index SETS (--set); each is 40 chosen paintings.
The chosen paintings fill the grid in row-major order (left-to-right,
top-to-bottom); fewer rows = a prefix of the same list, so the smaller grids
are the top rows of the 8-row one. How each cell's camera angle is chosen
depends on --mode:

  columns  one angle per column, from --degrees (default 150 120 90 60 30)
  single   the same angle (--degree) in every cell
  random   a random angle per cell (seeded by --seed; row-major draw order, so
           a 6-row grid's angles are the top 30 cells of the 8-row grid)

Images are the SynGallery-1024 renders, read from the on-disk source dataset
(byte-identical to patryk-bartkowiak/SynGallery-1024).

Reproduce every committed figure (sample_grid_set<S>_<mode>_5x<rows>.png):
  for s in 1 2; do for rows in 8 7 6; do
    python figures/make_grid.py --set $s --mode single  --degree 60 --rows $rows \
        --out figures/sample_grid_set${s}_all60_5x$rows.png
    python figures/make_grid.py --set $s --mode random  --seed 0 --rows $rows \
        --out figures/sample_grid_set${s}_random_5x$rows.png
    python figures/make_grid.py --set $s --mode columns --degrees 150 120 90 60 30 --rows $rows \
        --out figures/sample_grid_set${s}_150-120-90-60-30_5x$rows.png
  done; done
"""

import argparse
import random
from pathlib import Path

from PIL import Image

DATASET = Path("/mnt/storage_6/project_data/pl0896-03/visart-dataset-v2-1024")
ANGLES = [30, 60, 90, 120, 150]
COLS = 5
SETS = {
    1: [
        2, 4, 49, 74, 147, 151, 161, 176, 545, 852, 856, 859, 860, 861, 875,
        882, 886, 892, 897, 925, 930, 982, 1287, 1293, 1321, 1326, 1327, 1365,
        1376, 1448, 1474, 1594, 1667, 1811, 1840, 1841, 1949, 1961, 1964, 1989,
    ],
    2: [
        2030, 2038, 2063, 2065, 2180, 2186, 2252, 2263, 2306, 2389, 2396, 2400,
        2421, 2451, 2520, 2540, 3014, 3030, 3047, 3092, 3160, 3408, 3583, 3594,
        3611, 3627, 3632, 3737, 3746, 3785, 3800, 4534, 3932, 3994, 3998, 3999,
        4072, 4133, 4268, 4272,
    ],
}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--set", type=int, choices=sorted(SETS), default=1,
                   dest="set_id", help="which curated index set")
    p.add_argument("--mode", choices=("columns", "single", "random"), required=True)
    p.add_argument("--rows", type=int, default=8, help="grid rows (8, 7 or 6)")
    p.add_argument("--degrees", type=int, nargs=COLS, default=[150, 120, 90, 60, 30],
                   help="per-column angles for --mode columns")
    p.add_argument("--degree", type=int, default=60, help="angle for --mode single")
    p.add_argument("--seed", type=int, default=0, help="RNG seed for --mode random")
    p.add_argument("--cell", type=int, default=512)
    p.add_argument("--gutter", type=int, default=8)
    p.add_argument("--out", type=Path, required=True)
    return p.parse_args()


def angle_grid(a):
    """Return a rows x COLS matrix of camera angles per cell."""
    if a.mode == "single":
        return [[a.degree] * COLS for _ in range(a.rows)]
    if a.mode == "columns":
        return [[a.degrees[c] for c in range(COLS)] for _ in range(a.rows)]
    rng = random.Random(a.seed)
    return [[rng.choice(ANGLES) for _ in range(COLS)] for _ in range(a.rows)]


def main():
    a = parse_args()
    indices = SETS[a.set_id]
    need = a.rows * COLS
    if need > len(indices):
        raise SystemExit(f"{a.rows} rows needs {need} indices, set {a.set_id} has {len(indices)}")
    angles = angle_grid(a)
    W = COLS * a.cell + (COLS + 1) * a.gutter
    H = a.rows * a.cell + (a.rows + 1) * a.gutter
    canvas = Image.new("RGB", (W, H), "white")

    for r in range(a.rows):
        for c in range(COLS):
            idx, deg = indices[r * COLS + c], angles[r][c]
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
    print(f"wrote {a.out.name}  ({W}x{H}, {a.out.stat().st_size/2**20:.1f} MiB) "
          f"— set {a.set_id}, 5x{a.rows}, {label}")


if __name__ == "__main__":
    main()
