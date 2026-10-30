import json
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from cube_sweep import OUT, ROOT, load
from cube_variants import KEY, QUESTION, views

PARSED = ROOT / "experiments/2026-10-29_ed-analysis/parsed"
DIFFS = ["short", "medium", "long", "very_long", "very_very_long"]
ROWS = ["full", "no_answer", "core", "ops", "ops_no_answer", "ops_core", "ed_floor", "residual", "en_len", "hi_len"]
BOOT = 2000
RNG = np.random.default_rng(9)


def cluster_ci(values, clusters, stat=np.mean):
    ids, inverse = np.unique(clusters, return_inverse=True)
    totals = np.bincount(inverse, weights=values)
    counts = np.bincount(inverse)
    draws = RNG.integers(0, len(ids), (BOOT, len(ids)))
    boots = totals[draws].sum(1) / counts[draws].sum(1)
    return values.mean(), *np.percentile(boots, [2.5, 97.5])


def stratified(part, column, group, base="both correct"):
    d = part[part.outcome.isin([group, base])].dropna(subset=[column])
    strata = d.groupby(["difficulty", "task"], observed=True)
    usable = [(k, g) for k, g in strata if g.outcome.eq(group).any() and g.outcome.eq(base).any()]

    def estimate(items):
        num = den = 0.0
        for g in items:
            a, b = g[g.outcome.eq(group)][column], g[g.outcome.eq(base)][column]
            if len(a) and len(b):
                num += len(a) * (a.mean() - b.mean())
                den += len(a)
        return num / den

    point = estimate([g for _, g in usable])
    boots = []
    prepared = [(g, g.groupby("question_id").indices, list(g.groupby("question_id").indices)) for _, g in usable]
    for _ in range(300):
        items = []
        for g, indices, ids in prepared:
            chosen = RNG.choice(len(ids), len(ids))
            items.append(g.iloc[np.concatenate([indices[ids[i]] for i in chosen])])
        boots.append(estimate(items))
    return point, *np.percentile(boots, [2.5, 97.5]), int(d.outcome.eq(group).sum()), len(usable)


def auc(pos, neg):
    all_values = np.concatenate([pos, neg])
    ranks = pd.Series(all_values).rank().to_numpy()
    return (ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def stratified_auc(part, column, group, base="both correct"):
    num = den = 0.0
    for _, g in part.groupby(["difficulty", "task"], observed=True):
        a, b = g[g.outcome.eq(group)][column].dropna().to_numpy(), g[g.outcome.eq(base)][column].dropna().to_numpy()
        if len(a) >= 5 and len(b) >= 5:
            num += len(a) * auc(a, b)
            den += len(a)
    return num / den


def fmt(triple):
    return f"{triple[0]:+.3f} [{triple[1]:+.3f}, {triple[2]:+.3f}]"


def outcome_section(std):
    print("\n=== A. outcome vs both correct, within task x difficulty, question-cluster CI (standard/content)")
    rows = []
    for column in ROWS:
        for group in ["en only", "hi only", "both wrong"]:
            p, lo, hi, n, cells = stratified(std, column, group)
            rows.append({"view": column, "group": group, "diff": p, "lo": lo, "hi": hi, "n": n, "cells": cells})
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "outcome_stratified.csv", index=False)
    print(table.pivot(index="view", columns="group", values="diff").reindex(ROWS).round(3).to_string())
    print(table[table.group.eq("en only")].round(3).to_string(index=False))

    print("\n=== B. same question, different insertion: hi flips while en stays right")
    answered = std[std.outcome.isin(["both correct", "en only"])]
    rows = []
    for column in ROWS:
        wide = answered.pivot_table(index=QUESTION, columns="outcome", values=column, aggfunc="mean", observed=True).dropna()
        diff = (wide["en only"] - wide["both correct"]).to_numpy()
        rows.append({"view": column, "questions": len(diff), "mean": diff.mean(), "se": diff.std(ddof=1) / np.sqrt(len(diff))})
    fe = pd.DataFrame(rows).assign(lo=lambda d: d["mean"] - 1.96 * d.se, hi=lambda d: d["mean"] + 1.96 * d.se)
    fe.to_csv(OUT / "outcome_same_question.csv", index=False)
    print(fe.round(3).to_string(index=False))

    print("\n=== C. AUC within task x difficulty: en only vs both correct / hi only vs both correct / both wrong vs both correct")
    rows = []
    for column in ROWS:
        rows.append({"view": column, **{g: stratified_auc(std, column, g) for g in ["en only", "hi only", "both wrong"]}})
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    pd.DataFrame(rows).to_csv(OUT / "outcome_auc.csv", index=False)

    print("\n=== C2. by task: en only minus both correct, full and ops_no_answer (cells with both outcomes)")
    rows = []
    for task, g in std.groupby("task"):
        rows.append({"task": task, "full": stratified(g, "full", "en only")[0], "residual": stratified(g, "residual", "en only")[0],
                     "ops_no_answer": stratified(g, "ops_no_answer", "en only")[0], "en_only_n": int(g.outcome.eq("en only").sum())})
    print(pd.DataFrame(rows).round(3).to_string(index=False))


def cell_section(std):
    print("\n=== D. task x difficulty cells: mean RDS vs en-hi accuracy gap")
    cells = std.groupby(["task", "difficulty"], observed=True).agg(
        full=("full", "mean"), floor=("ed_floor", "mean"), ops=("ops_no_answer", "mean"), core=("core", "mean"),
        residual=("residual", "mean"), en=("en_correct", "mean"), hi=("hi_correct", "mean")).reset_index()
    cells["gap"] = cells.en - cells.hi
    cells.to_csv(OUT / "cells.csv", index=False)
    print(cells.pivot(index="task", columns="difficulty", values="gap").reindex(columns=DIFFS).round(3).to_string())
    for name in ["full", "floor", "residual", "ops", "core", "hi"]:
        print(name, "spearman with gap", round(cells[name].rank().corr(cells.gap.rank()), 3))
    within = cells.assign(**{c: cells[c] - cells.groupby("task")[c].transform("mean") for c in ["full", "floor", "residual", "ops", "gap", "hi"]})
    print("within-task pearson:", {c: round(within[c].corr(within.gap), 3) for c in ["full", "floor", "residual", "ops", "hi"]})
    print("short->very_very_long per task")
    t = cells[cells.difficulty.isin(["short", "very_very_long"])].pivot(index="task", columns="difficulty", values=["full", "floor", "ops", "en", "hi", "gap"])
    print(t.round(3).to_string())
    corr = [(task, round(g.full.corr(g.gap), 3), round(g.floor.corr(g.gap), 3)) for task, g in cells.groupby("task")]
    print("per-task corr(full,gap),(floor,gap) over 5 levels:", corr)


def insertion_section(std, variants):
    print("\n=== E. distractor: paired difference to no_insertion, per question (standard/content)")
    rows = []
    for column in ["full", "ed_floor", "residual", "ops_no_answer", "core", "en_len", "hi_len", "en_correct", "hi_correct"]:
        wide = std.pivot_table(index=QUESTION, columns="insertion", values=column, observed=True)
        for ins in ["similar_insertion", "dissimilar_insertion"]:
            d = (wide[ins] - wide["no_insertion"]).dropna().to_numpy()
            se = d.std(ddof=1) / np.sqrt(len(d))
            rows.append({"metric": column, "insertion": ins, "diff": d.mean(), "lo": d.mean() - 1.96 * se, "hi": d.mean() + 1.96 * se, "n": len(d)})
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "insertion_paired.csv", index=False)
    print(table.round(3).to_string(index=False))

    print("\n-- by task: similar minus none (full, hi_correct, en_correct)")
    rows = []
    for task, g in std.groupby("task"):
        row = {"task": task}
        for column in ["full", "hi_correct", "en_correct"]:
            wide = g.pivot_table(index=QUESTION, columns="insertion", values=column, observed=True)
            d = (wide["similar_insertion"] - wide["no_insertion"]).dropna()
            row[column] = d.mean()
            row[f"{column}_se"] = d.std(ddof=1) / np.sqrt(len(d))
        rows.append(row)
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "insertion_by_task.csv", index=False)
    print(table.round(3).to_string(index=False))
    print("cross-task spearman: RDS change vs hi accuracy change", round(table.full.rank().corr(table.hi_correct.rank()), 3))

    print("\n-- how far a distractor moves each language from its own no-distractor trace")
    s = variants[variants.set.eq("standard") & variants.kind.isin(["en_self", "hi_self"])]
    print(s.groupby(["kind", "insertion"])[["full", "no_answer", "core", "ops", "ops_no_answer"]].mean().round(3).to_string())
    print(s.groupby(["task", "kind"]).full.mean().unstack().round(3).to_string())
    print(s.groupby(["difficulty", "kind"], observed=True).full.mean().unstack().reindex(DIFFS).round(3).to_string())

    print("\n-- flip test: distractor moves hi from right to wrong, en right throughout")
    wide = std.pivot_table(index=QUESTION, columns="insertion", values=["hi_correct", "en_correct", "full"], observed=True).dropna()
    selfs = s[s.kind.eq("hi_self")].set_index(QUESTION + ["insertion"]).full
    enselfs = s[s.kind.eq("en_self")].set_index(QUESTION + ["insertion"]).full
    rows = []
    for ins in ["similar_insertion", "dissimilar_insertion"]:
        base = wide[(wide["hi_correct"]["no_insertion"].eq(1)) & (wide["en_correct"]["no_insertion"].eq(1)) & (wide["en_correct"][ins].eq(1))]
        for label, mask in {"hi flips wrong": base["hi_correct"][ins].eq(0), "hi stays right": base["hi_correct"][ins].eq(1)}.items():
            sub = base[mask]
            delta = sub["full"][ins] - sub["full"]["no_insertion"]
            idx = pd.MultiIndex.from_frame(sub.index.to_frame(index=False).assign(insertion=ins))
            hs, es = selfs.reindex(idx).to_numpy(), enselfs.reindex(idx).to_numpy()
            rows.append({"insertion": ins, "group": label, "n": len(sub), "rds_change": delta.mean(), "rds_change_se": delta.std() / np.sqrt(len(sub)),
                         "hi_self": np.nanmean(hs), "hi_self_se": np.nanstd(hs) / np.sqrt(len(sub)), "en_self": np.nanmean(es)})
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "distractor_flip.csv", index=False)
    print(table.round(3).to_string(index=False))


def ops_section(std):
    print("\n=== F. what the length gap is made of (mean tokens per trace, standard/content)")
    for name, part in {"all answered": std[std.outcome.ne("unanswered")], "both correct": std[std.outcome.eq("both correct")]}.items():
        en, hi = Counter(), Counter()
        for seq in part.en:
            en.update(t.split(" ")[0] for t in seq)
        for seq in part.hi:
            hi.update(t.split(" ")[0] for t in seq)
        table = pd.DataFrame({"en": pd.Series(en) / len(part), "hi": pd.Series(hi) / len(part)}).fillna(0)
        table["gap"] = table.en - table.hi
        table["share_of_gap"] = table.gap / table.gap.sum()
        table = table.sort_values("gap", ascending=False)
        table.to_csv(OUT / f"op_gap_{name.replace(' ', '_')}.csv")
        print(f"\n-- {name}: n={len(part)}, en {table.en.sum():.1f} hi {table.hi.sum():.1f}\n{table.round(3).to_string()}")
    has = lambda seq, ops: any(t.split(" ")[0] in ops for t in seq)
    verify = {"CHECK", "REVISE"}
    print("\ntraces with CHECK/REVISE: en", round(std.en.map(lambda s: has(s, verify)).mean(), 3), "hi", round(std.hi.map(lambda s: has(s, verify)).mean(), 3))
    print("median lengths en/hi", std.en_len.median(), std.hi_len.median(), "both correct", std[std.outcome.eq("both correct")][["en_len", "hi_len"]].median().to_dict())
    print("hi shorter share", round((std.hi_len < std.en_len).mean(), 3), "floor mean", round(std.ed_floor.mean(), 3), "floor share of RDS", round(std.ed_floor.mean() / std.full.mean(), 3))
    print("unanswered pairs", int(std.outcome.eq("unanswered").sum()), "en_correct na", int(std.en_correct.isna().sum()), "hi_correct na", int(std.hi_correct.isna().sum()),
          "means without unanswered en_len/hi_len", std[std.outcome.ne("unanswered")][["en_len", "hi_len"]].mean().round(2).to_dict())


def within_language_other_q(frame):
    print("\n=== G. templatedness: same-language, different question (same task x difficulty x insertion)")
    rows = []
    with Pool(16) as pool:
        for (s, field), part in frame.groupby(["set", "field"]):
            part = part.sort_values(["task", "difficulty", "insertion", "question_id"], key=lambda c: c.astype(int) if c.name == "question_id" else c)
            for lang in ["en", "hi"]:
                other = part.groupby(["task", "difficulty", "insertion"], observed=True)[lang].transform(lambda c: list(np.roll(c.to_numpy(dtype=object), 1)))
                d = pd.DataFrame(pool.map(views, list(zip(part[lang], other)), chunksize=32))
                rows.append({"set": s, "field": field, "kind": f"{lang}_other_q", **d.mean().to_dict()})
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "within_language_other_q.csv", index=False)
    print(table.round(3).to_string(index=False))


def records(name):
    out = []
    for d in DIFFS:
        for r in json.load(open(PARSED / name / f"{d}.p.json", encoding="utf-8"))["records"]:
            if r["condition"] != "cot":
                continue
            m = r["meta"]
            out.append({**{k: m[k] for k in ["difficulty", "task", "question_id", "insertion", "language", "answer"]},
                        "question": r["request"]["messages"][-1]["content"], "finish": r["finish_reason"],
                        "content": r["content"]["original"], "reasoning": r["reasoning_content"]["original"],
                        "completion": (r.get("usage") or {}).get("completion_tokens")})
    return pd.DataFrame(out)


def script_share(text):
    if not text:
        return np.nan
    hi = sum("ऀ" <= c <= "ॿ" for c in text)
    en = sum(c.isascii() and c.isalpha() for c in text)
    return hi / (hi + en) if hi + en else np.nan


def ron_section(frame, variants):
    print("\n=== H. reasoning on vs standard, same questions")
    from metrics import extract_answer, is_correct
    ron, std = records("ron"), records("standard")
    keys = ["difficulty", "task", "question_id", "insertion", "language"]
    joined = ron.merge(std, on=keys, suffixes=("_ron", "_std"))
    print("ron records", len(ron), "matched", len(joined), "same prompt", round((joined.question_ron == joined.question_std).mean(), 4), "same gold", (joined.answer_ron == joined.answer_std).mean())
    for name, d in {"ron": ron, "std": std.merge(ron[keys], on=keys)}.items():
        d["answered"] = d.content.map(lambda t: bool(t) and extract_answer(t) is not None)
        d["correct"] = [int(is_correct({"meta": {"answer": a, "task": t}, "content": c})) if ok else np.nan for a, t, c, ok in zip(d.answer, d.task, d.content, d.answered)]
        d["wrong0"] = d.correct.fillna(0)
        d["qkey"] = d.difficulty + "|" + d.task + "|" + d.question_id.astype(str)
        d["hi_script"] = d.content.map(script_share)
        d["reasoning_script"] = d.reasoning.map(script_share)
        print(f"\n-- {name}")
        print(d.groupby("language").agg(n=("correct", "size"), answered=("answered", "mean"), acc_answered=("correct", "mean"), acc_all=("wrong0", "mean"),
                                        finish_length=("finish", lambda s: (s == "length").mean()), completion=("completion", "median"),
                                        content_hi_script=("hi_script", "mean"), reasoning_hi_script=("reasoning_script", "mean")).round(3).to_string())
        en, hi = d[d.language.eq("en_US")].set_index(keys[:-1]), d[d.language.eq("hi_IN")].set_index(keys[:-1])
        gap = (en.wrong0 - hi.wrong0).dropna()
        ci = cluster_ci(gap.to_numpy(float), en.loc[gap.index].qkey.to_numpy())
        print("gap en-hi counting unanswered as wrong:", fmt(ci))
        both = pd.concat([en.correct.rename("e"), hi.correct.rename("h"), en.qkey], axis=1).dropna()
        print("gap answered both:", fmt(cluster_ci((both.e - both.h).to_numpy(float), both.qkey.to_numpy())), "n", len(both))
        if name == "ron":
            print("reasoning script share, hi_IN deciles", d[d.language.eq("hi_IN")].reasoning_script.quantile([.1, .5, .9]).round(3).to_dict(),
                  "share of hi traces <10% Devanagari", round((d[d.language.eq("hi_IN")].reasoning_script < .1).mean(), 3))
            print("finish by language/difficulty", d.groupby(["language", "difficulty"]).finish.apply(lambda s: round((s == "length").mean(), 3)).unstack().to_string())

    pairs = frame.set_index(["set", "field", *KEY])
    r_c = pairs.xs(("ron", "content"), level=("set", "field"))
    r_r = pairs.xs(("ron", "reasoning_content"), level=("set", "field"))
    s_c = pairs.xs(("standard", "content"), level=("set", "field"))
    print("\n-- matched pair metrics (standard content vs ron content, ron reasoning)")
    for label, a, b in [("ron content", r_c, s_c), ("ron reasoning", r_r, s_c)]:
        idx = a.index.intersection(b.index)
        qkey = idx.droplevel("insertion").map(lambda t: "|".join(map(str, t))).to_numpy()
        for column in ["full", "ed_floor", "residual", "ops_no_answer", "core", "en_len", "hi_len"]:
            d = (a.loc[idx, column] - b.loc[idx, column]).to_numpy(float)
            print(f"{label:14s} {column:14s} n={len(idx)} ron={a.loc[idx, column].mean():.3f} std={b.loc[idx, column].mean():.3f} diff={fmt(cluster_ci(d, qkey))}")

    print("\n-- excess over same-language baseline on the ron question set")
    qs = r_r.index.droplevel("insertion").unique().to_frame(index=False)
    for (s, field), part in variants.groupby(["set", "field"]):
        p = part.merge(qs.assign(question_id=qs.question_id.astype(part.question_id.dtype)), on=QUESTION)
        row = p.groupby("kind")[["full", "ops", "ops_no_answer", "core"]].mean()
        base = (row.loc["en_self"] + row.loc["hi_self"]) / 2
        print(s, field, "n", p[p.kind.eq("en_hi_same_q")].shape[0])
        print(row.round(3).to_string())
        print("position (same_q - self)/(other_q - self):", ((row.loc["en_hi_same_q"] - base) / (row.loc["en_hi_other_q"] - base)).round(3).to_dict())

    both = r_c[r_c.outcome.eq("both correct")].groupby("task").full.mean().rename("ron_content")
    both_r = r_r[r_r.outcome.eq("both correct")].groupby("task").full.mean().rename("ron_reasoning")
    both_s = s_c[s_c.outcome.eq("both correct")].groupby("task").full.mean().rename("std_content")
    t = pd.concat([both_s, both, both_r], axis=1)
    print("\n-- both-correct RDS per task\n", t.round(3).to_string(), "\nspearman", t.corr(method="spearman").round(3).to_string())


if __name__ == "__main__":
    pd.set_option("display.width", 220, "display.max_columns", 40, "display.max_rows", 500)
    sys.path.insert(0, str(ROOT / "experiments/2026-10-29_ed-analysis"))
    variants = pd.read_pickle(OUT / "variants.pkl")
    variants["question_id"] = variants.question_id.astype(int)
    frame = load()
    frame["question_id"] = frame.question_id.astype(int)
    same = variants[variants.kind.eq("en_hi_same_q")].drop(columns=["kind", "en_correct", "hi_correct", "en", "hi"], errors="ignore")
    frame = frame.merge(same, on=["set", "field", *KEY])
    frame["residual"] = frame.full - frame.ed_floor
    frame["en"] = frame.en_seq.map(json.loads)
    frame["hi"] = frame.hi_seq.map(json.loads)
    std = frame[frame.set.eq("standard")].copy()
    section = sys.argv[1] if len(sys.argv) > 1 else "all"
    if section in ("all", "outcome"):
        outcome_section(std)
    if section in ("all", "cells"):
        cell_section(std)
    if section in ("all", "insertion"):
        insertion_section(std, variants)
    if section in ("all", "ops"):
        ops_section(std)
    if section in ("all", "other"):
        within_language_other_q(frame)
    if section in ("all", "ron"):
        ron_section(frame, variants)
