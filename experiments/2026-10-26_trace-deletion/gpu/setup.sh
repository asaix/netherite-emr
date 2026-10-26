#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
WORK=${WORK:-/home/trace-deletion}
MODEL_DIR=${MODEL_DIR:-/home/models/sarvam-105b-fp8}
cd "$WORK"
python3 -m pip install -U "huggingface_hub[hf_transfer]" > pip_hf.log 2>&1
export HF_HUB_ENABLE_HF_TRANSFER=1
mkdir -p "$MODEL_DIR"
if command -v hf > /dev/null; then
  nohup hf download sarvamai/sarvam-105b-fp8 --local-dir "$MODEL_DIR" > download.log 2>&1 &
else
  nohup huggingface-cli download sarvamai/sarvam-105b-fp8 --local-dir "$MODEL_DIR" > download.log 2>&1 &
fi
DOWNLOAD_PID=$!
wget -q -O hotpatch_vllm.py https://huggingface.co/sarvamai/sarvam-105b/resolve/main/hotpatch_vllm.py
python3 hotpatch_vllm.py > hotpatch.log 2>&1
wait $DOWNLOAD_PID
du -sh "$MODEL_DIR"
python3 -c "import vllm; print('vllm', vllm.__version__)"
grep -q SarvamMLAForCausalLM "$(python3 -c 'import vllm, os; print(os.path.dirname(vllm.__file__))')/model_executor/models/registry.py" && echo PATCH_OK
ls "$MODEL_DIR"/*.safetensors | wc -l
echo SETUP_DONE
