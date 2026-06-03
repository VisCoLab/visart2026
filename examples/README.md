# Example renders

25 sample images produced by the pipeline as a smoke test on the PCSS (Eagle) cluster.

- **Config**: 5 datapoints × 5 cameras, RGB, 512×512, Cycles on GPU (CUDA), Blender 5.1.2.
- **Source images**: 5 distinct paintings from the MET dataset (one object per datapoint); each datapoint's exact source path is recorded in its `metadata.json`.

Each `<datapoint>/` folder contains:
- `source.jpg` — the original painting fed onto the canvas (copied from the MET dataset),
- `<frame>_<mode>_<camera>.png` — the 5 camera renders,
- `metadata.json` — scene metadata for that datapoint.
