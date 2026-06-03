# Example renders

25 sample images produced by the pipeline as a smoke test on the PCSS (Eagle) cluster.

- **Config**: 5 datapoints × 5 cameras, RGB, 512×512, Cycles on GPU (CUDA).
- **Generated with**: `sbatch slurm/render.sbatch` — Blender 5.1.2, job `7313756` (~6 min on an H100).
- **Source images**: first 5 entries of [`../data/paintings_train_images.json`](../data/paintings_train_images.json) (MET dataset).

Layout mirrors the pipeline output: `<datapoint>/<frame>_<mode>_<camera>.png`, plus one `metadata.json` per datapoint.
