# Example renders

25 sample images (5 distinct MET paintings × 5 cameras) — a quick look at the
pipeline output.

- **Config**: RGB, 512×512, Cycles on GPU (CUDA), Blender 5.1.2.
- **Scene**: the updated gallery from PR #1 `kuba/light-fix` — a more enclosed
  room (side walls) with all cameras unified to 32.44 mm — plus the
  camera-modifier jitter (`translation` + `rotation`, the defaults).
- **Source images**: 5 distinct MET objects (one painting each); the exact source
  path is recorded in each `metadata.json`.

Folders are **0-based** (`0`–`4`), matching the dataset convention. Each
`<datapoint>/` contains:
- `source.jpg` — the original painting fed onto the canvas,
- `<frame>_<mode>_<camera>.png` — the 5 camera renders,
- `metadata.json` — scene metadata for that datapoint.
