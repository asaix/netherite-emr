import base64
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUBE = ROOT / "experiments/2026-10-29_ed-analysis/edout/cube.html"
DOCS = ROOT / "docs/final"
OUT = Path(__file__).parent / "outputs/final_plots"
VIEWS = {
    "task_by_set": ("task", "set", "mean"),
    "set_by_insertion": ("set", "insertion", "dist"),
    "task_by_difficulty": ("task", "difficulty", "mean"),
    "outcome_by_insertion": ("outcome", "insertion", "mean"),
    "insertion_by_difficulty": ("insertion", "difficulty", "mean"),
}
FIELDS = {
    "content": (["content"], "content only", OUT / "content_rendered"),
    "reasoning": (["reasoning_content"], "reasoning_content only (ron)", DOCS / "reasoning"),
    "both": (["content", "reasoning_content"], "content + reasoning_content", DOCS / "both"),
}
DRIVER = """
<script>
(async () => {
  const views = %s, fields = %s, out = {};
  for (const [fieldName, [allowed, label]] of Object.entries(fields)) {
    document.querySelectorAll('input[data-d="field"]').forEach(b => b.checked = allowed.includes(D.dims.field[+b.value]));
    for (const [viewName, [x, color, div]] of Object.entries(views)) {
      document.getElementById("x").value = x;
      document.getElementById("color").value = color;
      draw();
      const el = document.getElementById(div), rotated = x === "task";
      const present = D.dims[x].filter((_, c) => el.data.some(t => (t.x || []).includes(D.dims[x][c]) && (t.y || []).some(v => v !== null)));
      await Plotly.relayout(el, {
        "title.text": `${el.layout.title.text} | ${label}`,
        "margin.r": rotated ? 90 : 40, "margin.b": rotated ? 170 : 120, "legend.y": rotated ? -0.42 : -0.2,
        "xaxis.categoryarray": present,
        "yaxis.range": div === "dist" ? [-0.03, 1.05] : [0, 1.05],
      });
      out[`${fieldName}/${viewName}`] = {
        png: await Plotly.toImage(el, {format: "png", width: 760, height: 520, scale: 2}),
        traces: el.data.map(t => ({name: t.name, type: t.type, x: t.x, y: div === "mean" ? t.y : null, n: div === "mean" ? (t.customdata || []).map(c => c[0]) : t.y.length})),
      };
    }
  }
  const pre = document.createElement("pre");
  pre.id = "result";
  pre.textContent = JSON.stringify(out);
  document.body.appendChild(pre);
})();
</script></body></html>
"""


def main():
    html = CUBE.read_text(encoding="utf-8")
    fields = {name: [allowed, label] for name, (allowed, label, _) in FIELDS.items()}
    html = html.replace("</body></html>", DRIVER % (json.dumps(VIEWS), json.dumps(fields)))
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "cube.html"
        page.write_text(html, encoding="utf-8")
        dom = subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--enable-unsafe-swiftshader", f"--user-data-dir={tmp}/profile",
                              "--virtual-time-budget=240000", "--dump-dom", page.as_uri()], capture_output=True, text=True, timeout=500).stdout
    match = re.search(r'<pre id="result">(.*?)</pre>', dom, re.S)
    data = json.loads(match.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))
    traces = {}
    for key, item in data.items():
        field, view = key.split("/")
        folder = FIELDS[field][2]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{view}.png").write_bytes(base64.b64decode(item["png"].split(",", 1)[1]))
        traces[key] = item["traces"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "rendered_traces.json").write_text(json.dumps(traces, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"rendered {len(data)} plots")


if __name__ == "__main__":
    main()
