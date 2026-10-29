import collections
import hashlib
import json
import re
import sys
import os
import urllib.request

HF = os.environ.get("HF_BASE", "https://huggingface.co")
RH = "RedHatAI/sarvam-105b-FP8-dynamic"
REF = "sarvamai/sarvam-105b-fp8"
EXPECTED_BYTES = 112_662_325_736
NON_FUNCTIONAL = {"pad_token", "transformers_version"}
SCALE = re.compile(r"(^|\.)(k|v|q|prob|kv)_scale$")
problems = []


def get(repo, name):
    req = urllib.request.Request(f"{HF}/{repo}/resolve/main/{name}", headers={"User-Agent": "netherite-check"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""), flush=True)
    if not ok:
        problems.append(name)


info = json.loads(urllib.request.urlopen(urllib.request.Request(f"{HF}/api/models/{RH}?blobs=true", headers={"User-Agent": "netherite-check"}), timeout=120).read())
shards = [s for s in info["siblings"] if s["rfilename"].endswith(".safetensors")]
total = sum(s.get("size", 0) for s in shards)
check("public, not gated", not info.get("gated") and not info.get("private"))
check("23 weight shards, about 113 GB", len(shards) == 23 and abs(total - EXPECTED_BYTES) < 1e9, f"{len(shards)} shards, {total / 1e9:.2f} GB")

for f in ["chat_template.jinja", "tokenizer.json", "configuration_sarvam_moe.py"]:
    try:
        a, b = sha(get(RH, f)), sha(get(REF, f))
        check(f"{f} identical to Sarvam's", a == b, f"red hat {a} sarvam {b}")
    except Exception as e:
        check(f"{f} identical to Sarvam's", False, repr(e))

for f in ["special_tokens_map.json", "generation_config.json"]:
    a, b = json.loads(get(RH, f)), json.loads(get(REF, f))
    d = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    print(f"{f} keys that differ: " + ", ".join(f"{k}: red hat={json.dumps(a.get(k), ensure_ascii=False)} sarvam={json.dumps(b.get(k), ensure_ascii=False)}" for k in d))
    check(f"{f} identical to Sarvam's except non-functional keys {sorted(NON_FUNCTIONAL)}", not [k for k in d if k not in NON_FUNCTIONAL], f"other differences: {[k for k in d if k not in NON_FUNCTIONAL]}")

rt, st = json.loads(get(RH, "tokenizer_config.json")), json.loads(get(REF, "tokenizer_config.json"))
diff = sorted(k for k in set(rt) | set(st) if rt.get(k) != st.get(k))
print("tokenizer_config.json keys that differ:", diff)
for k in diff:
    print(f"   {k}: red hat={json.dumps(rt.get(k), ensure_ascii=False)[:200]} | sarvam={json.dumps(st.get(k), ensure_ascii=False)[:200]}")
critical = [k for k in diff if k in ("added_tokens_decoder", "chat_template", "bos_token", "eos_token", "unk_token", "tokenizer_class", "add_bos_token", "add_eos_token")]
check("tokenizer_config.json differs only in non-functional keys", not critical, f"functional differences: {critical}" if critical else f"{len(diff)} cosmetic difference(s)")

cfg = json.loads(get(RH, "config.json"))
q = cfg.get("quantization_config") or {}
print("model_type:", cfg.get("model_type"), "| architectures:", cfg.get("architectures"), "| layers:", cfg.get("num_hidden_layers"))
print("quantization_config:", json.dumps({k: v for k, v in q.items() if k != "config_groups"}, ensure_ascii=False)[:600])
for name, group in (q.get("config_groups") or {}).items():
    print(f"  group {name}: targets={group.get('targets')} weights={json.dumps(group.get('weights'))[:200]} input_activations={json.dumps(group.get('input_activations'))[:200]}")
check("model type sarvam_mla / SarvamMLAForCausalLM", cfg.get("model_type") == "sarvam_mla" and cfg.get("architectures") == ["SarvamMLAForCausalLM"])
check("compressed-tensors format", q.get("quant_method") == "compressed-tensors", q.get("quant_method"))
check("KV cache not quantized (no kv_cache_scheme)", not q.get("kv_cache_scheme"), str(q.get("kv_cache_scheme")))
groups = list((q.get("config_groups") or {}).values())
dyn = all((g.get("input_activations") or {}).get("dynamic") is True and (g.get("input_activations") or {}).get("strategy") == "token" for g in groups) and groups
check("activations FP8 dynamic per token", bool(dyn))
ref_cfg = json.loads(get(REF, "config.json"))
ARCH_KEYS = ["hidden_size", "intermediate_size", "moe_intermediate_size", "num_hidden_layers", "num_attention_heads", "num_key_value_heads", "kv_lora_rank",
             "q_lora_rank", "qk_rope_head_dim", "qk_nope_head_dim", "v_head_dim", "num_experts", "num_experts_per_tok", "n_routed_experts", "n_shared_experts",
             "vocab_size", "rope_theta", "rope_scaling", "rope_parameters", "max_position_embeddings", "first_k_dense_replace", "rms_norm_eps", "router_dtype"]
all_diff = {k: (cfg.get(k), ref_cfg.get(k)) for k in sorted(set(cfg) | set(ref_cfg)) if k not in ("quantization_config",) and cfg.get(k) != ref_cfg.get(k)}
print("config.json keys that differ from Sarvam's FP8 config (all):", json.dumps(all_diff, ensure_ascii=False, default=str)[:1500])
arch_diff = [k for k in ARCH_KEYS if cfg.get(k) != ref_cfg.get(k)]
check("same architecture settings as Sarvam's config", not arch_diff, f"differ: {arch_diff}" if arch_diff else "")

weights = json.loads(get(RH, "model.safetensors.index.json"))["weight_map"]
patterns = collections.Counter(re.sub(r"\.\d+\.", ".N.", k) for k in weights)
print(f"\n{len(weights)} tensors, {len(patterns)} name patterns:")
for p, n in sorted(patterns.items()):
    print(f"  {n:5d}  {p}")
scales = sorted(k for k in weights if SCALE.search(k))
layers = sorted({int(m.group(1)) for k in weights if (m := re.match(r"model\.layers\.(\d+)\.", k))})
extra = [i for i in layers if i >= cfg.get("num_hidden_layers", 10 ** 9)]
input_scales = [k for k in weights if k.endswith("input_scale")]
print(f"KV/attention scale tensors: {len(scales)} | static input_scale tensors: {len(input_scales)} | layers {layers[0]}..{layers[-1]}, beyond num_hidden_layers: {extra}")
check("no static input scales (dynamic activations)", not input_scales)

print("\nCHECK REDHAT:", "PASS" if not problems else f"FAIL ({problems})")
sys.exit(0 if not problems else 1)
