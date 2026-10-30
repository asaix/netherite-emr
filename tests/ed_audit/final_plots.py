import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "experiments/2026-10-29_ed-analysis"
OUT = Path(__file__).parent / "outputs/final_plots"
KEY = ["difficulty", "task", "insertion", "question_id"]
DIFF = ["short", "medium", "long", "very_long", "very_very_long"]
METRICS = ["norm_ed", "en_len", "hi_len", "ed_floor", "en_correct", "hi_correct"]
VIEWS = {"task_by_set": ["task", "set"], "set_by_insertion": ["set", "insertion"], "task_by_difficulty": ["task", "difficulty"],
         "outcome_by_insertion": ["outcome", "insertion"], "insertion_by_difficulty": ["insertion", "difficulty"]}


def load_cube():
    text = (RUN / "edout/cube.html").read_text(encoding="utf-8")
    start = text.index("const D = ") + len("const D = ")
    data = json.loads(text[start:text.index("\n", start)].rstrip().rstrip(";"))
    frame = pd.DataFrame({d: [data["dims"][d][c] for c in data["codes"][d]] for d in data["dims"]})
    for name, values in data["num"].items():
        frame[name] = pd.to_numeric(pd.Series(values), errors="coerce")
    frame["question_id"] = data["question_id"]
    return frame


def load_records():
    rows = []
    for path in sorted((RUN / "parsed/standard").glob("*.p.json")):
        for r in json.loads(path.read_text(encoding="utf-8"))["records"]:
            if r["condition"] != "cot":
                continue
            m = r["meta"]
            original = (r["content"] or {}).get("original") or ""
            answers = [t for t in (r["content"] or {}).get("parsed") or [] if t.startswith(("SPITANSWER", "ANSWER"))]
            prompt = r["request"]["messages"][-1]["content"]
            rows.append({"difficulty": m["difficulty"], "task": m["task"], "insertion": m["insertion"], "question_id": int(m["question_id"]),
                         "language": m["language"], "finish": r["finish_reason"], "question": prompt.split("\n\n", 1)[-1], "original": original,
                         "answer": answers[-1].split(" ", 1)[-1] if answers else None})
    return pd.DataFrame(rows)


def view(frame, dims):
    g = frame.groupby(dims)["norm_ed"]
    out = g.agg(n="size", mean="mean", median="median", std="std", minimum="min", maximum="max")
    out["q1"], out["q3"] = g.quantile(0.25), g.quantile(0.75)
    out["ci"] = 1.96 * out["std"] / np.sqrt(out["n"])
    return out.join(frame.groupby(dims)[METRICS[1:]].mean()).round(4)


def paired(frame, a, b, index):
    table = frame.pivot_table(index=index, columns="insertion", values="norm_ed")
    d = (table[a] - table[b]).dropna()
    return {"n": len(d), "mean": round(d.mean(), 4), "ci": round(1.96 * d.std(ddof=1) / np.sqrt(len(d)), 4)}


def section(log, title, value):
    text = value.to_string() if hasattr(value, "to_string") else str(value)
    log.append(f"\n## {title}\n{text}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 220, "display.max_rows", 500, "display.max_columns", 50)
    cube = load_cube()
    content = cube[cube["field"] == "content"]
    standard = content[content["set"] == "standard"]
    ron = content[content["set"] == "ron"]
    log = []

    for name, dims in VIEWS.items():
        table = view(content, dims)
        table.to_csv(OUT / f"{name}.csv")
        section(log, f"as plotted: {name}", table)
        if "set" not in dims:
            diff = (view(standard, dims)["mean"] - table["mean"]).abs()
            section(log, f"standard-only minus pooled, largest shift: {name}", diff.sort_values().tail(1))

    matched = ron.merge(standard, on=KEY, suffixes=("_ron", "_std"))
    by_task = matched.groupby("task").agg(pairs=("norm_ed_ron", "size"), ron=("norm_ed_ron", "mean"), std=("norm_ed_std", "mean"),
                                          ron_floor=("ed_floor_ron", "mean"), std_floor=("ed_floor_std", "mean"),
                                          ron_en=("en_len_ron", "mean"), std_en=("en_len_std", "mean"),
                                          ron_hi=("hi_len_ron", "mean"), std_hi=("hi_len_std", "mean"))
    by_task["delta"] = by_task["std"] - by_task["ron"]
    section(log, "ron vs standard on matched pairs", by_task.round(3))
    section(log, "matched overall", matched[["norm_ed_ron", "norm_ed_std", "en_len_ron", "en_len_std", "hi_len_ron", "hi_len_std"]].mean().round(4))
    both = matched[(matched["outcome_ron"] == "both correct") & (matched["outcome_std"] == "both correct")]
    section(log, "matched, both correct in both runs", {"pairs": len(both), "ron": round(both["norm_ed_ron"].mean(), 4), "std": round(both["norm_ed_std"].mean(), 4)})
    section(log, "ron channels by task", cube[cube["set"] == "ron"].pivot_table(index="task", columns="field", values="norm_ed").round(4))
    section(log, "ron channels overall", cube[cube["set"] == "ron"].groupby("field")[["norm_ed", "ed_floor", "en_len", "hi_len"]].mean().round(4))
    section(log, "ron pairs with text by task", ron.groupby("task").size())
    reasoning = cube[cube["field"] == "reasoning_content"]
    for name, frame in {"reasoning": reasoning, "both": cube}.items():
        for view_name, dims in VIEWS.items():
            table = view(frame, dims)
            table.to_csv(OUT / f"{name}_{view_name}.csv")
            section(log, f"{name}: {view_name}", table)
    for a, b in [("similar_insertion", "no_insertion"), ("dissimilar_insertion", "no_insertion"), ("similar_insertion", "dissimilar_insertion")]:
        section(log, f"paired ron reasoning {a} - {b}", paired(reasoning, a, b, ["difficulty", "task", "question_id"]))
    two = reasoning.merge(ron, on=KEY, suffixes=("_reasoning", "_content"))
    section(log, "ron channels on pairs with both", two[["norm_ed_reasoning", "norm_ed_content", "ed_floor_reasoning", "ed_floor_content", "en_len_reasoning", "en_len_content", "hi_len_reasoning", "hi_len_content"]].mean().round(4))
    gap = reasoning.merge(ron[KEY], on=KEY, how="left", indicator=True)
    section(log, "ron reasoning by whether content exists", gap.groupby("_merge", observed=True)[["norm_ed", "en_len", "hi_len"]].agg(["size", "mean"]).round(4))
    section(log, "ron reasoning outcome counts", pd.crosstab(reasoning["insertion"], reasoning["outcome"]))
    matched_reasoning = reasoning.merge(standard, on=KEY, suffixes=("_ron", "_std"))
    section(log, "ron reasoning vs standard content, matched by task", matched_reasoning.groupby("task").agg(pairs=("norm_ed_ron", "size"), ron=("norm_ed_ron", "mean"), std=("norm_ed_std", "mean")).assign(delta=lambda t: t["std"] - t["ron"]).round(4))
    section(log, "ron reasoning vs standard content, matched overall", {"pairs": len(matched_reasoning), "ron": round(matched_reasoning["norm_ed_ron"].mean(), 4), "std": round(matched_reasoning["norm_ed_std"].mean(), 4)})
    reasoning_table = reasoning.pivot_table(index="task", columns="difficulty", values="norm_ed")[DIFF]
    reasoning_table["rise"] = reasoning_table["very_very_long"] - reasoning_table["short"]
    section(log, "reasoning rise by task", reasoning_table.round(4))
    section(log, "reasoning difficulty profile", reasoning.groupby("difficulty")[METRICS].mean().reindex(DIFF).round(4))
    rows = {}
    for difficulty in DIFF:
        part = reasoning[reasoning["difficulty"] == difficulty]
        rows[difficulty] = {f"{a[:3]}_{k}": v for a in ["similar_insertion", "dissimilar_insertion"] for k, v in paired(part, a, "no_insertion", ["task", "question_id"]).items()}
    section(log, "paired insertion by difficulty, reasoning", pd.DataFrame(rows).T)
    for dims in VIEWS.values():
        if "set" not in dims:
            shift = (view(cube, dims)["mean"] - view(content, dims)["mean"]).abs()
            section(log, f"both minus content, largest shift: {dims}", shift.sort_values().tail(1))
    section(log, "pair counts by selection", {"content": len(content), "reasoning": len(reasoning), "both": len(cube), "ron_share_of_both": round((cube["set"] == "ron").mean(), 4), "ron_share_of_content": round((content["set"] == "ron").mean(), 4)})
    section(log, "outcome pooled over insertion, reasoning", reasoning.groupby("outcome")[["norm_ed", "ed_floor", "en_len", "hi_len"]].agg(["size", "mean"]).round(4))
    section(log, "outcome pooled over insertion, ron content", ron.groupby("outcome")[["norm_ed", "ed_floor"]].agg(["size", "mean"]).round(4))
    section(log, "outcome pooled over insertion, standard", standard.groupby("outcome")[["norm_ed", "ed_floor"]].agg(["size", "mean"]).round(4))
    channels = pd.DataFrame({"standard": standard.groupby("task")["norm_ed"].mean(), "ron_content": ron.groupby("task")["norm_ed"].mean(), "ron_reasoning": reasoning.groupby("task")["norm_ed"].mean()})
    section(log, "task rank correlation across channels", channels.rank().corr().round(3))
    rises = {name: (lambda t: t["very_very_long"] - t["short"])(frame.pivot_table(index="task", columns="difficulty", values="norm_ed")) for name, frame in {"standard": standard, "ron_reasoning": reasoning}.items()}
    section(log, "task rise rank correlation", round(rises["standard"].rank().corr(rises["ron_reasoning"].rank()), 3))
    section(log, "difficulty profile, standard", standard.groupby("difficulty")[METRICS].mean().reindex(DIFF).round(4))
    both_table = cube.pivot_table(index="task", columns="difficulty", values="norm_ed")[DIFF]
    both_table["rise"] = both_table["very_very_long"] - both_table["short"]
    section(log, "both rise by task", both_table.round(4))
    section(log, "both difficulty profile", cube.groupby("difficulty")[METRICS].mean().reindex(DIFF).round(4))
    section(log, "ron reasoning date_recurrence outcomes", pd.crosstab(reasoning[reasoning["task"] == "date_recurrence"]["insertion"], reasoning[reasoning["task"] == "date_recurrence"]["outcome"]))
    section(log, "ron reasoning overall", reasoning[METRICS].mean().round(4))
    section(log, "standard overall", standard[METRICS].mean().round(4))
    ron_rows = []
    for path in sorted((RUN / "parsed/ron").glob("*.p.json")):
        for r in json.loads(path.read_text(encoding="utf-8"))["records"]:
            if r["condition"] == "cot":
                ron_rows.append({"language": r["meta"]["language"], "finish": r["finish_reason"], "tokens": r["usage"]["completion_tokens"], "empty": not ((r["content"] or {}).get("parsed"))})
    ron_records = pd.DataFrame(ron_rows)
    section(log, "ron cot records", ron_records.groupby(["language", "finish", "empty"])["tokens"].agg(["size", "median", "max"]))
    rendered = json.loads((OUT / "rendered_traces.json").read_text(encoding="utf-8"))
    worst = 0
    checked = 0
    for selection, frame in {"content": content, "reasoning": reasoning, "both": cube}.items():
        for view_name, dims in VIEWS.items():
            if view_name == "set_by_insertion":
                continue
            means = frame.groupby(dims)["norm_ed"].mean()
            for trace in rendered[f"{selection}/{view_name}"]:
                series = trace["name"] if len(rendered[f"{selection}/{view_name}"]) > 1 or dims[1] != "set" else "ron"
                for x, y in zip(trace["x"], trace["y"]):
                    worst = max(worst, abs(means[(x, series)] - y))
                    checked += 1
    section(log, "rendered bars vs this script", {"bars": checked, "largest_difference": float(worst)})

    means = standard.groupby("task")[["norm_ed", "en_correct", "hi_correct", "ed_floor", "en_len", "hi_len"]].mean()
    section(log, "standard by task", means.round(4))
    section(log, "task ED vs Hindi accuracy (standard)", {"pearson": round(means["norm_ed"].corr(means["hi_correct"]), 3),
                                                          "spearman": round(means["norm_ed"].rank().corr(means["hi_correct"].rank()), 3),
                                                          "ron_vs_std_spearman": round(ron.groupby("task")["norm_ed"].mean().rank().corr(means["norm_ed"].rank()), 3)})

    for name, frame in {"standard": standard, "ron": ron}.items():
        ed = frame["norm_ed"]
        section(log, f"shape {name}", {"n": len(ed), "eq_1": round((ed == 1).mean(), 4), "eq_0": int((ed == 0).sum()), "ge_0.9": round((ed >= 0.9).mean(), 4), "le_0.5": round((ed <= 0.5).mean(), 4)})
        for a, b in [("similar_insertion", "no_insertion"), ("dissimilar_insertion", "no_insertion"), ("similar_insertion", "dissimilar_insertion")]:
            section(log, f"paired {name} {a} - {b}", paired(frame, a, b, ["difficulty", "task", "question_id"]))
    section(log, "lowest standard pairs", standard.nsmallest(3, "norm_ed")[KEY + ["norm_ed", "ed", "en_len", "hi_len", "outcome"]])

    table = content.pivot_table(index="task", columns="difficulty", values="norm_ed")[DIFF]
    table["rise"] = table["very_very_long"] - table["short"]
    section(log, "rise by task", table.round(4))
    correct = content[content["outcome"] == "both correct"].pivot_table(index="task", columns="difficulty", values="norm_ed")[["short", "very_very_long"]]
    correct["rise"] = correct["very_very_long"] - correct["short"]
    section(log, "rise by task, both correct only", correct.round(4))
    section(log, "difficulty profile", content.groupby("difficulty")[METRICS].mean().reindex(DIFF).round(4))
    section(log, "difficulty medians", content.groupby("difficulty")[["en_len", "hi_len"]].median().reindex(DIFF))

    for name, frame in {"pooled": content, "standard": standard}.items():
        rows = {}
        for difficulty in DIFF:
            part = frame[frame["difficulty"] == difficulty]
            rows[difficulty] = {f"{a[:3]}_{k}": v for a in ["similar_insertion", "dissimilar_insertion"]
                                for k, v in paired(part, a, "no_insertion", ["set", "task", "question_id"]).items()}
        section(log, f"paired insertion by difficulty, {name}", pd.DataFrame(rows).T)

    section(log, "outcome profile", content.groupby("outcome").agg(n=("norm_ed", "size"), ed=("norm_ed", "mean"), floor=("ed_floor", "mean"), en=("en_len", "median"), hi=("hi_len", "median")).round(4))
    counts = pd.crosstab(content["insertion"], content["outcome"])
    section(log, "outcome counts", counts)
    section(log, "outcome shares", (counts.div(counts.sum(axis=1), axis=0) * 100).round(2))
    cells = standard[standard["outcome"] != "unanswered"].groupby(["task", "difficulty", "outcome"])["norm_ed"].mean().unstack()
    gap = (cells["en only"] - cells["both correct"]).dropna()
    section(log, "en only minus both correct within task x difficulty, standard", {"cells": len(gap), "positive": int((gap > 0).sum()), "mean": round(gap.mean(), 4), "min": round(gap.min(), 4)})
    section(log, "unanswered by task x insertion, standard", pd.crosstab(standard[standard["outcome"] == "unanswered"]["task"], standard[standard["outcome"] == "unanswered"]["insertion"]))

    flip = []
    for _, part in standard.groupby(["difficulty", "task", "question_id"]):
        part = part[part["en_correct"] == 1]
        right, wrong = part[part["hi_correct"] == 1], part[part["hi_correct"] == 0]
        if len(right) and len(wrong):
            flip.append(wrong["norm_ed"].mean() - right["norm_ed"].mean())
    flip = np.array(flip)
    section(log, "same question, Hindi flips, English right (recomputed from cube)", {"questions": len(flip), "mean": round(flip.mean(), 4), "ci": round(1.96 * flip.std(ddof=1) / np.sqrt(len(flip)), 4)})
    earlier = OUT.parent / "cube_findings"
    section(log, "earlier control: token views", pd.read_csv(earlier / "outcome_same_question.csv").round(4))
    section(log, "earlier control: by task", pd.read_csv(earlier / "same_question_by_task.csv").round(4))

    records = load_records()
    merged = standard.merge(records[records["language"] == "en_US"], on=KEY).merge(records[records["language"] == "hi_IN"], on=KEY, suffixes=("_en", "_hi"))
    silent = merged[merged["outcome"] == "unanswered"]
    section(log, "unanswered finish reason", {"pairs": len(silent), "en_null_length": int(((silent["en_correct"].isna()) & (silent["finish_en"] == "length")).sum()), "en_null": int(silent["en_correct"].isna().sum()),
                                              "hi_null_length": int(((silent["hi_correct"].isna()) & (silent["finish_hi"] == "length")).sum()), "hi_null": int(silent["hi_correct"].isna().sum())})
    recurrence = merged[merged["task"] == "date_recurrence"]
    section(log, "date_recurrence outcomes", pd.crosstab(recurrence["insertion"], recurrence["outcome"]))
    section(log, "date_recurrence en cut-offs", pd.crosstab(recurrence["insertion"], recurrence["finish_en"]))
    section(log, "date_recurrence means", recurrence.groupby("insertion")[METRICS].mean().round(4))
    silent_flag = recurrence.assign(u=(recurrence["outcome"] == "unanswered").astype(float)).pivot_table(index=["difficulty", "question_id"], columns="insertion", values="u")
    for a in ["similar_insertion", "dissimilar_insertion"]:
        d = silent_flag[a] - silent_flag["no_insertion"]
        section(log, f"date_recurrence paired unanswered {a}", {"questions": len(d), "mean": round(d.mean(), 4), "ci": round(1.96 * d.std(ddof=1) / np.sqrt(len(d)), 4)})
    first = lambda frame: frame["question_en"].str.split(r"(?<=\.)\s", regex=True).str[0]
    similar = recurrence[recurrence["insertion"] == "similar_insertion"]
    section(log, "date_recurrence similar: lead sentence counts", first(similar).value_counts().head(8))
    cut = similar[similar["finish_en"] == "length"]
    section(log, "date_recurrence similar: cut-offs by lead sentence", first(cut).value_counts().head(8))
    section(log, "date_recurrence similar: cut-off traces naming weekly", {"cut_offs": len(cut), "mention_weekly": int(cut["original_en"].str.contains("weekly", case=False).sum()),
                                                                          "not_cut": len(similar) - len(cut), "not_cut_mention": int(similar[similar["finish_en"] != "length"]["original_en"].str.contains("weekly", case=False).sum())})

    wrong = merged[merged["outcome"] == "both wrong"].copy()
    wrong["same"] = wrong["answer_en"] == wrong["answer_hi"]
    section(log, "both wrong: same final answer token", wrong.groupby("same").agg(n=("norm_ed", "size"), ed=("norm_ed", "mean"), floor=("ed_floor", "mean")).round(4))

    (OUT / "log.txt").write_text("\n".join(log).strip() + "\n", encoding="utf-8")
    print("\n".join(log))


if __name__ == "__main__":
    main()
