#!/usr/bin/env bash
set -euo pipefail
WORK=${WORK:-/home/trace-deletion}
VENV=${VENV:-/home/venv031}
cd "$WORK"
export PYTHONUNBUFFERED=1
step() { echo "[$(date -u +%H:%M:%S)] $*"; }
step "creating virtual environment $VENV"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV" || { sudo apt-get install -y python3.10-venv && python3 -m venv "$VENV"; }
fi
step "upgrading pip"
"$VENV/bin/python" -m pip install -U pip
step "installing vllm 0.31.0 and 201 pinned packages (about 4 GB)"
"$VENV/bin/python" -m pip install --progress-bar off -r "$WORK/vllm031-py310-lock.txt"
step "applying the Sarvam loader patch"
SARVAM="$("$VENV/bin/python" -c 'import os, vllm; print(os.path.join(os.path.dirname(vllm.__file__), "model_executor", "models", "sarvam.py"))')"
"$VENV/bin/python" "$WORK/patch_sarvam_loader.py" "$SARVAM" && echo PATCH_LOADER_OK
step "checking vllm, torch and both GPUs"
"$VENV/bin/python" -c "
import torch, vllm
print('vllm', vllm.__version__, '| torch', torch.__version__, '| cuda', torch.version.cuda, '| available', torch.cuda.is_available(), '| gpus', torch.cuda.device_count())
assert vllm.__version__.startswith('0.31.0'), 'wrong vllm version'
assert torch.cuda.is_available() and torch.cuda.device_count() == 2, 'torch cannot see both GPUs'
"
test -x "$VENV/bin/vllm"
echo SETUP031_DONE
