#!/bin/bash
#SBATCH --job-name=visart-render
#SBATCH --account=pl0896-03
#SBATCH --partition=tesla
#SBATCH --gpus-per-node=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=slurm-%j.out
#
# Render the visart2026 scene on a PCSS (Eagle) GPU node with Cycles.
#
#   1. Set DATA_PATH below to your source-image directory.
#   2. Submit:  sbatch slurm/render.sbatch
#   3. Watch:   squeue -u $USER   ;   tail -f slurm-<jobid>.out
#
# Output layout:  $SAVE_PATH/<datapoint>/<frame>_<mode>_<camera>.png  (+ metadata.json)
# The scene has 5 cameras, so each datapoint (frame) yields 5 PNGs per render mode.
# The default below renders 5 datapoints x 5 cameras = 25 RGB images.

set -euo pipefail

# ---- locations (override REPO via env if the repo moves) ----
REPO="${VISART_REPO:-/mnt/storage_6/project_data/pl0896-03/visart2026}"
BLENDER="$(ls -d "$REPO"/vendor/blender-*-linux-x64/blender 2>/dev/null | head -1)"
SCENE="$REPO/blender/basic.blend"
ENABLE_GPU="$REPO/blender/src/enable_gpu.py"
MAIN="$REPO/blender/src/main.py"

# ---- render parameters (EDIT) ----
DATA_PATH="$REPO/data/paintings_train_images.json"    # dir of images OR a .json manifest
SAVE_PATH="/mnt/storage_5/scratch/pl0896-03/visart-out/${SLURM_JOB_ID:-manual}"
RENDER_FRAMES="1 5"        # START END (inclusive); 5 datapoints -> 25 RGB images
RENDER_MODE="rgb"          # any of: rgb mask depth  (space separated)
RENDER_RES="512 512"       # WIDTH HEIGHT (small for a quick smoke test)

# ---- sanity checks ----
if [[ -z "$BLENDER" || ! -x "$BLENDER" ]]; then
    echo "ERROR: Blender not found under $REPO/vendor/ — run the install step first." >&2
    exit 1
fi
if [[ "$DATA_PATH" == *__SET_ME__* || ( ! -d "$DATA_PATH" && ! -f "$DATA_PATH" ) ]]; then
    echo "ERROR: set DATA_PATH to an existing image directory or .json manifest (got: $DATA_PATH)" >&2
    exit 1
fi

mkdir -p "$SAVE_PATH"
echo "Blender : $BLENDER"
echo "Scene   : $SCENE"
echo "Data    : $DATA_PATH"
echo "Output  : $SAVE_PATH"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || true

# ---- render: enable_gpu.py runs first, then the pipeline (same session) ----
"$BLENDER" -b "$SCENE" \
    --python "$ENABLE_GPU" \
    --python "$MAIN" -- \
    --render-frames $RENDER_FRAMES \
    --render-mode $RENDER_MODE \
    --data-path "$DATA_PATH" \
    --save-path "$SAVE_PATH" \
    --render-resolution $RENDER_RES

echo "DONE. PNGs written: $(find "$SAVE_PATH" -type f -name '*.png' | wc -l)"
echo "Output directory: $SAVE_PATH"
