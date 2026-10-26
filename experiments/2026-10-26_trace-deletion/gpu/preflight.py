import ast
import glob
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
REPO = "sarvamai/sarvam-105b-fp8"
HOTPATCH = "https://huggingface.co/sarvamai/sarvam-105b/resolve/main/hotpatch_vllm.py"
EXECUTOR = "https://huggingface.co/sarvamai/sarvam-105b/raw/main/sarvam.py"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""), flush=True)
    return ok


def get(url, limit=None):
    req = urllib.request.Request(url, headers={"User-Agent": "netherite-preflight"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(limit) if limit else r.read()


def safe(name, fn):
    try:
        fn()
    except Exception as e:
        check(name, False, f"{type(e).__name__}: {e}")


check("Python 3.8+ on this Mac", sys.version_info >= (3, 8), sys.version.split()[0])

for f in ["setup.sh", "serve.sh", "deadline.sh"]:
    p = HERE / f
    check(f"gpu/{f} exists and has valid bash syntax", p.exists() and subprocess.run(["bash", "-n", str(p)]).returncode == 0)
for f in ["continue.py", "status.py", "monitor.py"]:
    p = HERE / f
    ok = p.exists()
    if ok:
        try:
            ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            ok = False
    check(f"gpu/{f} exists and parses", ok)


def requests():
    reqs = json.load(open(EXP / "outputs" / "requests_cap1000.json", encoding="utf-8"))
    ids = [r["id"] for r in reqs]
    versions = Counter(r["meta"]["version"] for r in reqs)
    shape = all([m["role"] for m in r["messages"]] == ["user", "assistant"] and r["messages"][1]["content"].strip() for r in reqs)
    check("requests_cap1000.json: 702 unique requests, 234 each of A/B/C, every one ends with a non-empty assistant prefix",
          len(reqs) == 702 and len(set(ids)) == 702 and versions == Counter({"A": 234, "B": 234, "C": 234}) and shape, f"{len(reqs)} requests {dict(versions)}")


safe("requests file", requests)

keys = glob.glob(os.path.expanduser("~/.ssh/*.pub"))
check("an SSH public key exists on this Mac (it must also be added in Jarvislabs Settings -> SSH keys)", bool(keys), ", ".join(keys))


def jl_checks():
    check("jl CLI installed", shutil.which("jl") is not None, shutil.which("jl") or "run: pip install jarvislabs")
    r = subprocess.run(["jl", "list", "--json"], capture_output=True, text=True, timeout=120)
    check("jl is logged in (jl list works)", r.returncode == 0, (r.stderr or "").strip()[-200:])
    running = r.stdout.lower().count("running")
    check("no Jarvislabs instance is already running (avoids paying twice)", running == 0, f"{running} running" if running else "")
    h = subprocess.run(["jl", "create", "--help"], capture_output=True, text=True, timeout=60).stdout
    check("jl create supports --gpu, --num-gpus, --storage", all(f in h for f in ("--gpu", "--num-gpus", "--storage")))


safe("jl CLI", jl_checks)


def hf_checks():
    info = json.loads(get(f"https://huggingface.co/api/models/{REPO}?blobs=true"))
    check("model repo is public and not gated", not info.get("gated") and not info.get("private") and not info.get("disabled"))
    shards = [s for s in info["siblings"] if s["rfilename"].endswith(".safetensors")]
    total = sum(s.get("size", 0) for s in info["siblings"]) / 1e9
    check("23 weight shards, about 112.6 GB in total (fits in 250 GB of storage)", len(shards) == 23 and 100 < total < 150, f"{len(shards)} shards, {total:.1f} GB")
    config = json.loads(get(f"https://huggingface.co/{REPO}/resolve/main/config.json"))
    check("weights are SarvamMLAForCausalLM with modelopt FP8", config.get("architectures") == ["SarvamMLAForCausalLM"] and config.get("quantization_config", {}).get("quant_method") == "modelopt")
    template = get(f"https://huggingface.co/{REPO}/resolve/main/chat_template.jinja").decode()
    check("chat template turns thinking off with enable_thinking -> <|nothink|>", "enable_thinking" in template and "<|nothink|>" in template)
    hot = get(HOTPATCH).decode()
    (HERE / "hotpatch_vllm.py").write_text(hot, encoding="utf-8")
    check("hotpatch_vllm.py downloads and pins vllm 0.15.0 and registers SarvamMLAForCausalLM", "vllm==0.15.0" in hot and "SarvamMLAForCausalLM" in hot, "saved a copy to gpu/hotpatch_vllm.py")
    check("the vLLM model file the hotpatch downloads is reachable", len(get(EXECUTOR, 2000)) > 500)


safe("Hugging Face", hf_checks)


def template_render():
    try:
        import jinja2
    except ImportError:
        print("[SKIP] chat template render test: run `python3 -m pip install --user jinja2` and re-run to enable it")
        return
    template = get(f"https://huggingface.co/{REPO}/resolve/main/chat_template.jinja").decode()
    env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
    env.globals["raise_exception"] = lambda m: (_ for _ in ()).throw(RuntimeError(m))
    env.filters["tojson"] = lambda x, **k: json.dumps(x, ensure_ascii=False)
    req = next(r for r in json.load(open(EXP / "outputs" / "requests_cap1000.json", encoding="utf-8")) if r["meta"]["language"] == "hi_IN")
    rendered = env.from_string(template).render(messages=req["messages"], add_generation_prompt=False, enable_thinking=False)
    final = req["messages"][-1]["content"].strip()
    ok = "<|nothink|>" in rendered and final in rendered
    check("rendered prompt contains <|nothink|> and the exact assistant prefix (needed for continue_final_message)", ok)
    if ok:
        cut = rendered[: rendered.rindex(final) + len(final)]
        print("    prompt tail the model will continue from:\n    " + repr(cut[-300:]))


safe("chat template render", template_render)

print("\nPREFLIGHT:", "PASS" if all(results) else "FAIL")
sys.exit(0 if all(results) else 1)
