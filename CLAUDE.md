# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A **headless Blender synthetic-data pipeline** (`visart2026`). It renders a 3D art-gallery scene of a framed picture and produces paired **RGB / mask / depth** images plus per-datapoint metadata — i.e. a training-data generator for computer vision. Each rendered "datapoint" loads a different source image onto the canvas and randomizes lighting, floor material, and camera pose.

Everything under `blender/src/` runs **inside Blender's bundled Python** (`import bpy`). These are not standalone scripts — they cannot run under a system `python3`. They import only `bpy` + the Python stdlib.

## Running the pipeline

The pipeline runs through a portable Blender install (see the cluster section). From the repo root:

```bash
vendor/blender-*/blender -b blender/basic.blend \
    --python blender/src/enable_gpu.py \
    --python blender/src/main.py -- \
    --render-frames 1 100 --render-mode rgb mask depth \
    --data-path /path/to/source/images --save-path /path/to/out
```

- `-b` = headless. Everything after `--` is passed to `main.py`'s argparse (Blender swallows args before `--`).
- `enable_gpu.py` switches Cycles to GPU; omit it for CPU rendering. It must precede `main.py` so both run in the same Blender session.
- See all flags: `… --python blender/src/main.py -- --help`. Full reference: [blender/README.md](blender/README.md). Key ones: `--fpd` (frames per datapoint), `--data-index` (0-based start offset into the sorted file list), `--margin`, `--light-shape {square,disk,random}`, `--light-spread MIN MAX`, `--render-resolution W H`.
- **On the cluster, submit via SLURM** — do not render on the login node: `sbatch slurm/render.sbatch` (see below).

There is **no build, lint, or test setup** — do not invent one. The only dependency beyond Blender is optional **PyYAML** (metadata falls back to JSON if absent).

## Module imports

`main.py` and `frame_loader.py` add their own directory to `sys.path` dynamically:

```python
sys.path.append(str(Path(__file__).resolve().parent))
```

so the sibling modules (`camera_settings`, `frame_loader`, `floor_setter`, `mod_lights`, `metadata_handler`, `placard_resetter`, …) import correctly wherever the repo lives. There are **no hardcoded machine paths**. (Earlier revisions hardcoded a developer's `/home/neerka/...` path; if you ever see that, it's stale.)

## The `.blend` ↔ code contract

`basic.blend` must contain specific named datablocks; the code looks them up by string and will `KeyError` otherwise:

- **Objects**: `canvas` (the picture plane), `frame`, `glass`, `plakietka` (the wall placard), `light` (an area light), `Ground` (the floor).
- **Collection**: `Cameras` — every camera in it renders each datapoint. The scene ships **5** (`front`, `right upper`, `left upper`, `right bottom`, `left bottom`), so N frames produce **N×5** images per mode.
- **Scene**: named `Scene`.
- **Compositing node groups**: one per render mode, named exactly `rgb`, `mask`, `depth`. `main.py` switches output via `scene.compositing_node_group = bpy.data.node_groups[<mode>]` — a **Blender 5.0+** property that replaced `scene.node_tree`, so the visual pass logic lives in the `.blend`'s compositor, not in Python.
- **Floor materials**: any material whose name starts with `floor_` is a candidate; `floor_setter.py` picks one at random per frame.
- **Blender version**: the scene was authored in **Blender 5.1** (`bpy.data.version == (5, 1, 29)`) and needs **5.0+** for `compositing_node_group`. Engine is **Cycles**. The pinned build is **5.1.2** (cluster section).

## Render loop (`main.py`)

For each frame in `[START, END]`: randomize light shape+spread (`mod_lights`), pick a random `floor_` material (`reset_floor`), jitter all cameras (`move_cameras`); every `FPD` frames advance to the next source image (`load_picture`); then for each render mode × each camera, render a PNG; dump `metadata.json`; restore camera poses (`reset_cameras`). Cameras are jittered from a snapshot taken once before the loop and reset after each datapoint.

**Output layout**: `save_path/<datapoint>/<frame>_<mode>_<camera>.png`, plus one `metadata.json` per datapoint folder. Source images come from a directory (sorted by name) **or** a `.json` manifest of paths (kept in order), and are consumed sequentially starting at `--data-index`; running past the end raises `IndexError` (no wraparound).

### Module responsibilities (`blender/src/`)
- `main.py` — CLI parsing + the render loop (the file you `--python` for rendering).
- `enable_gpu.py` — enables Cycles GPU (OptiX → CUDA fallback) for headless renders; run via `--python` *before* `main.py`. No-op if no GPU is present.
- `frame_loader.py::load_picture` — loads the image, scales `canvas`/`frame`/`glass` to its aspect ratio, wires the image into the canvas material's Principled BSDF Base Color.
- `camera_settings.py` — snapshot / random-jitter / restore camera transforms.
- `floor_setter.py`, `mod_lights.py`, `placard_resetter.py`, `placard_loader.py` — per-element randomization/loading helpers (`placard_*` handle the wall placard, Polish *plakietka*).
- `metadata_handler.py::dump_scene_metadata` — robustly serializes visible objects + materials (resolving Principled inputs through node links and Geometry-Nodes attributes) to YAML, or JSON if PyYAML is missing. Note: output always uses a `metadata.json` filename even when the content is YAML.

### One-off asset generators (not part of rendering)
`frame_model_gen.py` and `frame_model_gen2.py` are run **interactively** (Blender Text Editor / Scripting workspace) to procedurally build frame-molding mesh variants from 2D profile curves into a collection. `frame_model_gen2.py` is the newer one (adds widths, materials, bevel/weighted-normal modifiers) and requires a material named `Frame` to already exist.

## Running on the PCSS (Eagle) cluster

This repo lives on the PSNC **Eagle** HPC cluster (grant/account `pl0896-03`). Jobs run under **SLURM**; rendering must go through the scheduler, **not** the login node.

- **Login**: `ssh <user>@eagle.man.poznan.pl` (configure SSH keys in the PCSS portal). Docs: [Getting Started](https://help.pcss.plcloud.pl/portal/hpc/2%20Getting%20Started/).
- **Modules**: `module avail`, `module load <name>`. Blender is **not** a module — this repo ships its own portable build. `python/3.13.0-gcc-14.2.0` and `cuda/*` modules exist if needed (Blender's Cycles does not need a CUDA module — it bundles its own kernels and uses the node's driver).
- **Partitions** (`sinfo`): `standard` (CPU, default), `fast` (CPU, ≤1 h), `tesla` / `proxima` (GPU). The render job targets **`tesla`** via `#SBATCH --partition=tesla` + `#SBATCH --gpus-per-node=1`. Docs: [Job Management](https://help.pcss.plcloud.pl/portal/hpc/4%20Job%20Management%20and%20Scheduling/), [Submitting](https://help.pcss.plcloud.pl/portal/hpc/submit/).
- **Storage** ([policy](https://help.pcss.plcloud.pl/portal/hpc/5%20Data%20Management%20and%20Transfer/#data-storage-policies)): home is **1 GB** (don't put data/tools there); `project_data` — this repo, `/mnt/storage_6/project_data/pl0896-03` — is shared + backed up; **scratch** (`/mnt/storage_5/scratch/pl0896-03`) is the workspace for inputs/outputs. Renders go to scratch, not the repo.

### Blender install
Blender is **not** committed. A portable build is extracted into `vendor/` (gitignored): `vendor/blender-5.1.2-linux-x64/blender`. To (re)install:
```bash
cd vendor
curl -fSLO https://download.blender.org/release/Blender5.1/blender-5.1.2-linux-x64.tar.xz
tar -xf blender-5.1.2-linux-x64.tar.xz && rm blender-5.1.2-linux-x64.tar.xz
```
The build must be **5.0+** (`compositing_node_group`); the scene was authored in 5.1.

### Submitting a render
Set `DATA_PATH` in [slurm/render.sbatch](slurm/render.sbatch), then:
```bash
sbatch slurm/render.sbatch          # submit
squeue -u $USER                     # watch the queue
tail -f slurm-<jobid>.out           # follow the log (written to repo root, gitignored)
seff <jobid>                        # resource usage after it finishes
```
The script enables the GPU (`enable_gpu.py`, which prefers **CUDA** — OptiX segfaults on the tesla nodes due to a driver/RT-core version skew), runs `main.py`, and writes to `/mnt/storage_5/scratch/pl0896-03/visart-out/<jobid>/`. Defaults render 5 datapoints × 5 cameras = 25 RGB images at 512² (≈6 min on an H100); edit `RENDER_FRAMES` / `RENDER_MODE` / `RENDER_RES` to scale up.

## Conventions

- Code, comments, and `blender/README.md` are in **English**. One Polish remnant is kept on purpose: the `.blend` object is named `plakietka` (placard), so the string literal `"plakietka"` stays in `main.py` / `frame_loader.py` / `placard_loader.py` to match the scene — renaming it there would break `bpy.data.objects[...]` lookups.
- `blender/assets/` holds the scene's resources: `hdrs/` (EXR environment lighting), `materials/` (per-material `.blend` libraries for floors/walls), `textures/` (`plk.png` is the placard texture). The `textures/.gitattributes` configures git-LFS for ML/binary formats.
