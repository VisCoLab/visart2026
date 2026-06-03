# Example renders

25 sample images produced by the pipeline as a smoke test on the PCSS (Eagle) cluster.

- **Config**: 5 datapoints × 5 cameras, RGB, 512×512, Cycles on GPU (CUDA).
- **Generated with**: `sbatch slurm/render.sbatch` — Blender 5.1.2, job `7313756` (~6 min on an H100).
- **Source images**: first 5 entries of [`../data/paintings_train_images.json`](../data/paintings_train_images.json) (MET dataset).

Each `<datapoint>/` folder contains:
- `source.jpg` — the original painting fed onto the canvas (copied from the MET dataset; full source path recorded in `metadata.json`),
- `<frame>_<mode>_<camera>.png` — the 5 camera renders,
- `metadata.json` — scene metadata for that datapoint.
