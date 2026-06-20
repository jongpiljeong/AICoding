#!/usr/bin/env bash
# Run evaluation across all three benchmark datasets.
# Adjust CONFIG paths as needed.

set -euo pipefail

CONFIGS=(
    "configs/voc21_vitb16.yaml"
    "configs/coco_stuff164k_vitl14.yaml"
    "configs/ade20k_vitl14.yaml"
)

for cfg in "${CONFIGS[@]}"; do
    echo ""
    echo "==========================================="
    echo " Evaluating: $cfg"
    echo "==========================================="
    python infer.py --config "$cfg"
done
