#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1
VENV=${VENV:-/home/venv031}
NEW=${NEW:-/home/models/sarvam-105b-fp8-dynamic}
OLD=${OLD:-/home/models/sarvam-105b-fp8}
REPO=RedHatAI/sarvam-105b-FP8-dynamic
EXPECTED_BYTES=${EXPECTED_BYTES:-112662325736}
step() { echo "[$(date -u +%H:%M:%S)] $*"; }
HF="$VENV/bin/hf"
[ -x "$HF" ] || HF="$(command -v hf || true)"
[ -n "$HF" ] || { step "ERROR: no hf command found"; exit 1; }
step "disk before:"; df -h /home | tail -1
if [ -d "$OLD" ]; then
  step "deleting the old FP8 weights $OLD (frees about 105 GB)"
  rm -rf "$OLD"
  df -h /home | tail -1
fi
mkdir -p "$NEW"
step "downloading $REPO to $NEW (about 113 GB) with $HF"
( while sleep 30; do echo "[$(date -u +%H:%M:%S)] downloaded so far: $(du -sb "$NEW" | cut -f1 | awk '{printf "%.1f GB", $1/1e9}') of 112.7 GB"; done ) &
WATCH=$!
trap 'kill $WATCH 2>/dev/null || true' EXIT
"$HF" download "$REPO" --local-dir "$NEW"
kill $WATCH 2>/dev/null || true
step "verifying the download"
python3 - "$NEW" "$EXPECTED_BYTES" <<'PY'
import json, sys
from pathlib import Path
d, expected = Path(sys.argv[1]), int(sys.argv[2])
shards = sorted(d.glob("model-*-of-00023.safetensors"))
total = sum(p.stat().st_size for p in shards)
cfg = json.load(open(d / "config.json"))
q = cfg.get("quantization_config") or {}
print(f"shards {len(shards)} | bytes {total} (expected {expected}) | model_type {cfg.get('model_type')} | quant {q.get('quant_method')} | kv_cache_scheme {q.get('kv_cache_scheme')}")
ok = len(shards) == 23 and total == expected and cfg.get("model_type") == "sarvam_mla" and q.get("quant_method") == "compressed-tensors" and not q.get("kv_cache_scheme")
for f in ["tokenizer.json", "tokenizer_config.json", "chat_template.jinja", "configuration_sarvam_moe.py", "model.safetensors.index.json"]:
    if not (d / f).exists():
        print("missing", f); ok = False
sys.exit(0 if ok else 1)
PY
df -h /home | tail -1
step "DOWNLOAD_DONE"
