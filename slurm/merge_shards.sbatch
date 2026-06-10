#!/bin/bash
#SBATCH --job-name=visart-merge
#SBATCH --account=pl0896-03
#SBATCH --partition=standard
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=04:00:00
#SBATCH --output=slurm-%j.out
#
# Merge the per-task shard dirs written by render_array.sbatch into a flat
# dataset, renaming datapoint folders to their global index:
#   $SRC_BASE/<task>/<datapoint>/  ->  $DEST/<task*1000 + datapoint>/
# then verify the result (every folder: 5 PNGs + metadata.json).
#
# Run it after the render array succeeds, e.g. chained at submit time:
#   VISART_SRC_BASE=… VISART_DEST=… \
#       sbatch --dependency=afterok:<array_job_id> --kill-on-invalid-dep=yes \
#       slurm/merge_shards.sbatch
#
# Shards are copied, not moved — clean the scratch shard dirs manually after
# checking the verification output.
set -euo pipefail

SRC_BASE="${VISART_SRC_BASE:-/mnt/storage_5/scratch/pl0896-03/visart-dataset-v2}"
DEST="${VISART_DEST:-/mnt/storage_6/project_data/pl0896-03/visart-dataset-v2}"
PER_SHARD=1000

mkdir -p "$DEST"
total=0
for shard_dir in "$SRC_BASE"/[0-9]*; do
    shard=$(basename "$shard_dir")
    for dp_dir in "$shard_dir"/[0-9]*; do
        dp=$(basename "$dp_dir")
        global=$(( shard * PER_SHARD + dp ))
        if [[ -e "$DEST/$global" ]]; then
            echo "ERROR: $DEST/$global already exists — aborting" >&2
            exit 1
        fi
        cp -r "$dp_dir" "$DEST/$global"
        total=$(( total + 1 ))
    done
done
echo "merged $total datapoint folders into $DEST"

echo "folders : $(ls -d "$DEST"/[0-9]* | wc -l)"
echo "PNGs    : $(find "$DEST" -name '*.png' | wc -l)"
echo "metadata: $(find "$DEST" -name 'metadata.json' | wc -l)"

# dataset contract: one frame per datapoint, rgb only, 5 cameras
bad=0
for d in "$DEST"/[0-9]*; do
    n=$(find "$d" -maxdepth 1 -name '*.png' | wc -l)
    if [[ ! -f "$d/metadata.json" || "$n" -ne 5 ]]; then
        echo "INCOMPLETE: $d ($n PNGs, metadata $([[ -f $d/metadata.json ]] && echo ok || echo MISSING))"
        bad=1
    fi
done
if (( bad )); then
    echo "VERIFY FAILED" >&2
    exit 1
fi
echo "VERIFY OK"
