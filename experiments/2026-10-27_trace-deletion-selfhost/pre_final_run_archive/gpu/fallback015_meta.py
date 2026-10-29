import json
import shutil
import sys
from pathlib import Path

MODEL = Path(sys.argv[2] if len(sys.argv) > 2 else "/home/models/sarvam-105b-fp8")
FILES = ["config.json", "hf_quant_config.json"]
KEYS = ("kv_cache_scheme", "kv_cache_quant_algo")


def kv_keys(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in KEYS and v is not None:
                found.append(f"{path}{k}={v!r}")
            found += kv_keys(v, f"{path}{k}.")
    return found


def strip(obj):
    if isinstance(obj, dict):
        for k in KEYS:
            if k in obj:
                obj[k] = None if k == "kv_cache_quant_algo" else obj.pop(k)
                if k == "kv_cache_scheme":
                    obj.pop(k, None)
        for v in obj.values():
            strip(v)


mode = sys.argv[1]
for name in FILES:
    path, backup = MODEL / name, MODEL / (name + ".orig_session4")
    if not path.exists():
        continue
    if mode == "apply":
        if not backup.exists():
            shutil.copy2(path, backup)
        data = json.load(open(path))
        before = kv_keys(data)
        strip(data)
        json.dump(data, open(path, "w"), indent=2)
        after = kv_keys(json.load(open(path)))
        print(f"{name}: removed {before} -> remaining {after}")
        if after:
            sys.exit(f"{name} still has KV-cache settings")
    elif mode == "restore" and backup.exists():
        shutil.copy2(backup, path)
        print(f"{name}: restored")
print("FALLBACK_META_OK")
