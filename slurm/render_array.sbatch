#!/bin/bash
#SBATCH --job-name=visart-arr
#SBATCH --account=pl0896-03
#SBATCH --partition=tesla
#SBATCH --gpus-per-node=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=20:00:00
#SBATCH --array=0-4
#SBATCH --output=slurm-%A_%a.out
#
# Generate the synthetic dataset as a 5-task SLURM array over the one-per-object
# manifest. Each task renders a 1000-image slice (the last is clamped), so the
# tasks tile the manifest with no gaps/overlap:
#   task k -> --data-index k*1000, --render-frames 1 <slice>
# With 4898 sources x 5 cameras that is 24,490 RGB images.
#
#   sbatch slurm/render_array.sbatch
#   squeue -u $USER ; tail -f slurm-<arrayjobid>_<task>.out
#
# Each task writes to its own shard dir so per-task datapoint folders don't collide:
#   $SAVE_BASE/<task_id>/<datapoint>/<frame>_<mode>_<camera>.png
set -euo pipefail

REPO="${VISART_REPO:-/mnt/storage_6/project_data/pl0896-03/visart2026}"
BLENDER="$(ls -d "$REPO"/vendor/blender-*-linux-x64/blender 2>/dev/null | head -1)"
SCENE="$REPO/blender/basic.blend"
ENABLE_GPU="$REPO/blender/src/enable_gpu.py"
MAIN="$REPO/blender/src/main.py"
DATA_PATH="$REPO/data/paintings_train_images_unique.json"
SAVE_BASE="${VISART_SAVE_BASE:-/mnt/storage_5/scratch/pl0896-03/visart-dataset}"

PER_SHARD=1000
TOTAL=$(grep -c '^"' "$DATA_PATH")               # number of paths in the manifest
DATA_INDEX=$(( SLURM_ARRAY_TASK_ID * PER_SHARD ))
N=$PER_SHARD
if (( DATA_INDEX + N > TOTAL )); then            # clamp the final shard
    N=$(( TOTAL - DATA_INDEX ))
fi

SAVE_PATH="$SAVE_BASE/$SLURM_ARRAY_TASK_ID"
mkdir -p "$SAVE_PATH"

echo "shard $SLURM_ARRAY_TASK_ID: data-index=$DATA_INDEX frames=1..$N (manifest total=$TOTAL) -> $SAVE_PATH"
nvidia-smi --query-gpu=name --format=csv,noheader || true

"$BLENDER" -b "$SCENE" \
    --python "$ENABLE_GPU" \
    --python "$MAIN" -- \
    --render-frames 1 "$N" \
    --render-mode rgb \
    --data-path "$DATA_PATH" \
    --data-index "$DATA_INDEX" \
    --save-path "$SAVE_PATH" \
    --render-resolution 512 512

echo "shard $SLURM_ARRAY_TASK_ID DONE: $(find "$SAVE_PATH" -name '*.png' | wc -l) PNGs"
