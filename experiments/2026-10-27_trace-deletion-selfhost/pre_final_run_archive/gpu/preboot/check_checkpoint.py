import collections
import hashlib
import json
import re
import sys
import urllib.request

FP8 = "sarvamai/sarvam-105b-fp8"
BF16 = "sarvamai/sarvam-105b"
SCALE = re.compile(r"(^|\.)(k|v|q|prob|kv)_scale$")


def get(repo, name):
    req = urllib.request.Request(f"https://huggingface.co/{repo}/resolve/main/{name}", headers={"User-Agent": "netherite-check"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


cfg = json.loads(get(FP8, "config.json"))
print("model_type:", cfg.get("model_type"))
print("architectures:", cfg.get("architectures"))
print("auto_map:", cfg.get("auto_map"))
print("num_hidden_layers:", cfg.get("num_hidden_layers"))
print("rope:", cfg.get("rope_parameters") or cfg.get("rope_scaling"))
print("quantization_config:", json.dumps(cfg.get("quantization_config"), indent=2))
try:
    print("hf_quant_config.json:", json.dumps(json.loads(get(FP8, "hf_quant_config.json")), indent=2))
except Exception as e:
    print("hf_quant_config.json: not found", e)

weights = json.loads(get(FP8, "model.safetensors.index.json"))["weight_map"]
patterns = collections.Counter(re.sub(r"\.\d+\.", ".N.", k) for k in weights)
print(f"\n{len(weights)} tensors, {len(patterns)} name patterns:")
for p, n in sorted(patterns.items()):
    print(f"  {n:5d}  {p}")

scales = sorted(k for k in weights if SCALE.search(k))
layers = sorted({int(m.group(1)) for k in weights if (m := re.match(r"model\.layers\.(\d+)\.", k))})
extra = [i for i in layers if i >= cfg.get("num_hidden_layers", 10**9)]
print(f"\nKV/attention scale tensors: {len(scales)}", scales[:6])
print(f"layer indices {layers[0]}..{layers[-1]}, beyond num_hidden_layers: {extra}")

files = sorted({v.split("--")[-1].split(".")[0] + ".py" for v in (cfg.get("auto_map") or {}).values()})
for f in files:
    try:
        a, b = (hashlib.sha256(get(r, f)).hexdigest()[:16] for r in (FP8, BF16))
        print(f"remote code {f}: fp8 {a} bf16 {b} {'SAME' if a == b else 'DIFFERENT'}")
    except Exception as e:
        print(f"remote code {f}: could not compare ({e})")

ok = cfg.get("model_type") == "sarvam_mla" and cfg.get("architectures") == ["SarvamMLAForCausalLM"]
print("\nVERDICT")
print(" model_type/arch as vLLM 0.31 expects:", "YES" if ok else "NO -> stop and report")
print(" loader patch needed for vLLM 0.31:", "YES" if scales or extra else "NO")
sys.exit(0 if ok else 1)
