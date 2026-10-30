import argparse
import json
from io import StringIO
from itertools import combinations
from pathlib import Path

import pandas as pd

from metrics import DIFFICULTY_ORDER

FIELDS = ["content", "reasoning_content"]
DIMS = ["set", "field", "difficulty", "task", "insertion", "outcome"]
CUBE = ["difficulty", "task", "insertion", "outcome"]
OUTCOMES = ["both correct", "en only", "hi only", "both wrong", "unanswered"]
ORDER = {"difficulty": DIFFICULTY_ORDER, "outcome": {o: i for i, o in enumerate(OUTCOMES)}}
METRICS = {
    "norm_ed": "normalized ED",
    "ed": "edit distance",
    "len_gap": "length gap (hi − en)",
    "ed_floor": "length floor |hi − en| / max",
    "en_len": "en length",
    "hi_len": "hi length",
    "en_correct": "en accuracy",
    "hi_correct": "hi accuracy",
}
STATS = ["count", "mean", "median", "std"]

TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><title>ED cube</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
body{font-family:system-ui,sans-serif;margin:0;display:flex;background:#fff;color:#222}
#side{width:250px;flex:none;padding:12px;border-right:1px solid #ddd;height:100vh;overflow:auto;box-sizing:border-box;position:sticky;top:0;font-size:13px}
#main{flex:1;min-width:0;padding:12px;display:grid;grid-template-columns:repeat(auto-fit,minmax(560px,1fr));gap:12px}
#main>div{border:1px solid #eee;min-height:440px}
#count{font-weight:bold;margin-bottom:8px}
select{width:100%;margin:2px 0 8px}
fieldset{border:1px solid #ddd;margin:0 0 8px;padding:4px 8px}
fieldset label{display:block}
#tablewrap{grid-column:1/-1;min-height:0!important;max-height:420px;overflow:auto}
table{border-collapse:collapse;font-size:12px;width:100%}
td,th{padding:3px 8px;border-bottom:1px solid #eee;text-align:right;position:relative}
th{position:sticky;top:0;background:#f6f6f6}
td:nth-child(-n+2),th:nth-child(-n+2){text-align:left}
</style></head><body>
<div id="side"></div>
<div id="main">
<div id="mean"></div><div id="dist"></div><div id="heat"></div><div id="correct"></div><div id="gap"></div>
<div id="tablewrap"><table id="table"></table></div>
</div>
<script>
const D = __DATA__;
const DIMS = Object.keys(D.dims), N = D.question_id.length, side = document.getElementById("side");
const val = id => document.getElementById(id).value;
const lab = (d, i) => D.dims[d][D.codes[d][i]];
const dimOpts = DIMS.map(d => [d, d]);
const COLOURS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"];

function select(id, title, options, value) {
  side.insertAdjacentHTML("beforeend", `<b>${title}</b><select id="${id}">${options.map(([v, t]) => `<option value="${v}"${v === value ? " selected" : ""}>${t}</option>`).join("")}</select>`);
}
side.insertAdjacentHTML("beforeend", `<div id="count"></div>`);
select("metric", "Metric", Object.entries(D.metrics), "norm_ed");
select("x", "Group by", dimOpts, "difficulty");
select("color", "Color by", [["", "none"], ...dimOpts], "set");
select("rows", "Heatmap rows", dimOpts, "task");
select("cols", "Heatmap columns", dimOpts, "difficulty");
select("gapx", "Scatter x", [["ed_floor", D.metrics.ed_floor], ["len_gap", D.metrics.len_gap]], "ed_floor");
for (const d of DIMS) {
  side.insertAdjacentHTML("beforeend", `<fieldset><legend>${d} <a href="#" data-d="${d}">toggle</a></legend>${D.dims[d].map((v, i) =>
    `<label><input type="checkbox" data-d="${d}" value="${i}"${d === "field" && v !== "content" && D.dims.field.includes("content") ? "" : " checked"}> ${v}</label>`).join("")}</fieldset>`);
}
side.addEventListener("change", draw);
side.addEventListener("click", e => {
  if (e.target.tagName !== "A") return;
  e.preventDefault();
  const boxes = [...side.querySelectorAll(`input[data-d="${e.target.dataset.d}"]`)], on = !boxes.every(b => b.checked);
  boxes.forEach(b => b.checked = on);
  draw();
});

function filtered(metric) {
  const allowed = DIMS.map(d => new Set([...side.querySelectorAll(`input[data-d="${d}"]:checked`)].map(b => +b.value)));
  const out = [];
  for (let i = 0; i < N; i++) if (D.num[metric][i] !== null && DIMS.every((d, k) => allowed[k].has(D.codes[d][i]))) out.push(i);
  return out;
}

function group(idx, dims) {
  if (!dims.length) return [[[], idx]];
  const m = new Map();
  for (const i of idx) {
    const key = dims.map(d => D.codes[d][i]).join(",");
    if (!m.has(key)) m.set(key, []);
    m.get(key).push(i);
  }
  const cmp = (a, b) => { for (let k = 0; k < a.length; k++) if (a[k] !== b[k]) return a[k] - b[k]; return 0; };
  return [...m].map(([k, v]) => [k.split(",").map(Number), v]).sort((a, b) => cmp(a[0], b[0]));
}

function stats(vals) {
  vals = vals.filter(v => v !== null);
  const n = vals.length, s = vals.sort((a, b) => a - b);
  if (!n) return {n, mean: null, median: null, std: null, ci: null};
  const mean = s.reduce((a, b) => a + b, 0) / n;
  const median = n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2;
  const std = n > 1 ? Math.sqrt(s.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1)) : 0;
  return {n, mean, median, std, ci: 1.96 * std / Math.sqrt(n)};
}

function draw() {
  const metric = val("metric"), x = val("x"), color = val("color"), y = D.num[metric], name = D.metrics[metric];
  const idx = filtered(metric);
  document.getElementById("count").textContent = `${idx.length} pairs selected`;
  const series = color ? group(idx, [color]).map(([[c], v]) => [D.dims[color][c], v]) : [["all", idx]];
  const cfg = {responsive: true, displaylogo: false};
  const layout = (title, extra) => ({title: {text: title, font: {size: 14}, x: 0.01, xanchor: "left"}, margin: {t: 40, l: 60, r: 10, b: 110}, legend: {orientation: "h", y: -0.22, yanchor: "top"}, ...extra});
  const cat = d => ({type: "category", categoryorder: "array", categoryarray: D.dims[d], title: d});
  const who = s => color ? `${color}: ${s}<br>` : "";

  Plotly.react("mean", series.map(([s, v]) => {
    const g = group(v, [x]).map(([[c], w]) => [D.dims[x][c], stats(w.map(i => y[i]))]);
    return {type: "bar", name: s, x: g.map(r => r[0]), y: g.map(r => r[1].mean), error_y: {type: "data", array: g.map(r => r[1].ci)},
      customdata: g.map(r => [r[1].n, r[1].ci]), hovertemplate: `${x}: %{x}<br>${who(s)}mean ${name}: %{y:.4f} ± %{customdata[1]:.4f} (95% CI)<br>pairs: %{customdata[0]}<extra></extra>`};
  }), layout(`Mean ${name} by ${x} (95% CI)`, {barmode: "group", xaxis: cat(x), yaxis: {title: name}}), cfg);

  const box = (div, d, title) => Plotly.react(div, series.flatMap(([s, v], k) => {
    const style = {type: "box", legendgroup: s, offsetgroup: s, boxpoints: false, boxmean: true, marker: {color: COLOURS[k % COLOURS.length]}, hoverlabel: {namelength: -1}};
    return [{...style, name: s, x: [D.dims[d][0]], y: [null]}, ...group(v, [d]).map(([[c], w]) =>
      ({...style, name: `${d}: ${D.dims[d][c]}<br>${who(s)}pairs: ${w.length}`, showlegend: false, x: w.map(() => D.dims[d][c]), y: w.map(i => y[i])}))];
  }), layout(title, {boxmode: "group", xaxis: cat(d), yaxis: {title: name}}), cfg);
  box("dist", x, `${name} distribution by ${x}`);
  box("correct", "outcome", `${name} by correctness outcome (en / hi)`);

  const r = val("rows"), c = val("cols");
  const z = D.dims[r].map(() => D.dims[c].map(() => null)), n = D.dims[r].map(() => D.dims[c].map(() => 0));
  for (const [[a, b], v] of group(idx, [r, c])) { const st = stats(v.map(i => y[i])); z[a][b] = st.mean; n[a][b] = st.n; }
  Plotly.react("heat", [{type: "heatmap", x: D.dims[c], y: D.dims[r], z, customdata: n, colorscale: "Viridis", texttemplate: "%{z:.2f}",
    hovertemplate: `${r}: %{y}<br>${c}: %{x}<br>mean ${name}: %{z:.4f}<br>pairs: %{customdata}<extra></extra>`}],
    layout(`Mean ${name}: ${r} × ${c}`, {xaxis: {type: "category", title: c}, yaxis: {type: "category", automargin: true}}), cfg);

  const gx = val("gapx"), xs = D.num[gx], bin = v => gx === "ed_floor" ? Math.round(v * 20) / 20 : v;
  const traces = series.flatMap(([s, v], k) => {
    const colour = COLOURS[k % COLOURS.length], bins = new Map();
    for (const i of v) { const b = bin(xs[i]); if (!bins.has(b)) bins.set(b, []); bins.get(b).push(y[i]); }
    const trend = [...bins].sort((a, b) => a[0] - b[0]).map(([b, ys]) => [b, stats(ys).mean]);
    return [
      {type: "scattergl", mode: "markers", name: s, legendgroup: s, x: v.map(i => xs[i]), y: v.map(i => y[i]), marker: {size: 4, opacity: 0.3, color: colour},
        text: v.map(i => [...DIMS.map(d => `${d}: ${lab(d, i)}`), `question_id: ${D.question_id[i]}`].join("<br>")),
        hovertemplate: `%{text}<br>${D.metrics[gx]}: %{x:.3f}<br>${name}: %{y:.3f}<extra></extra>`},
      {type: "scatter", mode: "lines", name: `${s} binned mean`, legendgroup: s, x: trend.map(t => t[0]), y: trend.map(t => t[1]), line: {width: 2, color: colour},
        hovertemplate: `${who(s)}binned mean<br>${D.metrics[gx]}: %{x:.3f}<br>mean ${name}: %{y:.4f}<extra></extra>`},
    ];
  });
  if (gx === "ed_floor" && metric === "norm_ed") traces.push({type: "scatter", mode: "lines", name: "y = x", x: [0, 1], y: [0, 1], line: {dash: "dot", color: "#888"}});
  Plotly.react("gap", traces, layout(`${name} vs ${D.metrics[gx]}`, {xaxis: {title: D.metrics[gx]}, yaxis: {title: name}}), cfg);

  const dims = color && color !== x ? [x, color] : [x];
  const fmt = v => v === null ? "" : Number.isInteger(v) ? v : v.toFixed(4);
  const head = [...dims, "n", "mean", "median", "std", "95% CI", "en acc", "hi acc"];
  const body = group(idx, dims).map(([k, v]) => {
    const st = stats(v.map(i => y[i]));
    return [...k.map((code, j) => D.dims[dims[j]][code]), st.n, st.mean, st.median, st.std, st.ci,
      stats(v.map(i => D.num.en_correct[i])).mean, stats(v.map(i => D.num.hi_correct[i])).mean];
  });
  document.getElementById("table").innerHTML = `<tr>${head.map(h => `<th>${h}</th>`).join("")}</tr>` +
    body.map(row => `<tr>${row.map(v => `<td>${typeof v === "string" ? v : fmt(v)}</td>`).join("")}</tr>`).join("");
}
draw();
</script></body></html>
"""


def values(frame, dim):
    return sorted(frame[dim].unique(), key=lambda v: ORDER.get(dim, {}).get(v, v))


def outcome(en, hi):
    return "unanswered" if pd.isna(en) or pd.isna(hi) else OUTCOMES[2 * (1 - int(en)) + (1 - int(hi))]


def load(path):
    path = Path(path)
    frames = []
    for file in sorted(path.rglob("*.csv")) if path.is_dir() else [path]:
        text = file.read_text(encoding="utf-8")
        if "\n\n" not in text:
            continue
        pairs = pd.read_csv(StringIO(text.split("\n\n", 1)[1]))
        for field in FIELDS:
            if f"{field}_norm_edit_distance" not in pairs:
                continue
            en, hi = pairs[f"{field}_en_len"], pairs[f"{field}_hi_len"]
            frames.append(pd.DataFrame({
                "set": file.parent.name,
                "field": field,
                **{k: pairs[k] for k in ["question_id", "difficulty", "task", "insertion", "en_correct", "hi_correct"]},
                "outcome": [outcome(e, h) for e, h in zip(pairs["en_correct"], pairs["hi_correct"])],
                "norm_ed": pairs[f"{field}_norm_edit_distance"],
                "ed": pairs[f"{field}_edit_distance"],
                "en_len": en,
                "hi_len": hi,
                "len_gap": hi - en,
                "ed_floor": ((hi - en).abs() / pd.concat([en, hi], axis=1).max(axis=1)).fillna(0),
            }).dropna(subset=["norm_ed"]))
    return pd.concat(frames, ignore_index=True)


def html(frame, path):
    dims = {d: values(frame, d) for d in DIMS}
    data = {
        "dims": dims,
        "codes": {d: frame[d].map({v: i for i, v in enumerate(dims[d])}).tolist() for d in DIMS},
        "num": {m: [None if pd.isna(v) else round(float(v), 4) for v in frame[m]] for m in METRICS},
        "metrics": METRICS,
        "question_id": frame["question_id"].tolist(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")


def cube(frame, out):
    frame = frame.assign(**{d: pd.Categorical(frame[d], categories=values(frame, d), ordered=True) for d in ORDER})
    out.mkdir(parents=True, exist_ok=True)
    for metric in METRICS:
        rows = []
        for n in range(len(CUBE) + 1):
            for keys in combinations(CUBE, n):
                stats = frame.groupby(["set", "field", *keys], observed=True)[metric].agg(STATS).reset_index()
                rows.append(stats.assign(**{k: "ALL" for k in CUBE if k not in keys}))
        pd.concat(rows)[["set", "field", *CUBE, *STATS]].to_csv(out / f"{metric}.csv", index=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="+")
    ap.add_argument("--html")
    ap.add_argument("--out")
    args = ap.parse_args()

    frame = pd.concat([load(p) for p in args.input], ignore_index=True)
    first = Path(args.input[0])
    path = Path(args.html) if args.html else first / "cube.html" if first.is_dir() else first.with_suffix(".html")
    html(frame, path)
    print(f"{len(frame)} rows -> {path}")
    if args.out:
        cube(frame, Path(args.out))
        print(f"stats -> {args.out}")
