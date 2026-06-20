#!/usr/bin/env bash
# Run CLIPer inference for a single config.
# Usage:
#   bash scripts/run_inference.sh configs/voc21_vitb16.yaml [--save-vis]

set -euo pipefail

CONFIG=${1:-"configs/voc21_vitb16.yaml"}
EXTRA_ARGS="${@:2}"

echo "=== CLIPer Inference ==="
echo "Config : $CONFIG"
echo "CUDA   : $(python -c 'import torch; print(torch.cuda.get_device_name(0))')"

python infer.py --config "$CONFIG" $EXTRA_ARGS
