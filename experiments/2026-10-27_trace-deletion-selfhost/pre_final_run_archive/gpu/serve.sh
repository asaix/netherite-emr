#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
MODEL_DIR=${MODEL_DIR:-/home/models/sarvam-105b-fp8}
KV_DTYPE=${KV_DTYPE:-bfloat16}
EXTRA_ARGS=${EXTRA_ARGS:-}
export VLLM_USE_FLASHINFER_MOE_FP8=0
exec vllm serve "$MODEL_DIR" \
  --served-model-name sarvam-105b-fp8 \
  --trust-remote-code \
  --tensor-parallel-size 2 \
  --quantization modelopt \
  --kv-cache-dtype "$KV_DTYPE" \
  --dtype bfloat16 \
  --no-enable-prefix-caching \
  --block-size 64 \
  --max-model-len 16384 \
  --seed 0 \
  --port 3002 \
  $EXTRA_ARGS
