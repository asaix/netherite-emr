#!/usr/bin/env bash
set -euo pipefail
VENV=${VENV:-/home/venv031}
export PATH="$VENV/bin:/usr/local/cuda/bin:$PATH"
export CUDA_HOME=/usr/local/cuda
MODEL_DIR=${MODEL_DIR:-/home/models/sarvam-105b-fp8-dynamic}
EXTRA_ARGS=${EXTRA_ARGS:-}
unset VLLM_USE_FLASHINFER_MOE_FP8
exec "$VENV/bin/vllm" serve "$MODEL_DIR" \
  --served-model-name sarvam-105b-fp8 \
  --trust-remote-code \
  --tensor-parallel-size 2 \
  --kv-cache-dtype bfloat16 \
  --moe-backend triton \
  --dtype bfloat16 \
  --no-enable-prefix-caching \
  --block-size 64 \
  --max-model-len 16384 \
  --seed 0 \
  --port 3002 \
  $EXTRA_ARGS
