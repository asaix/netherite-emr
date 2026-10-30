import json
import random
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from cube_sweep import OUT, ROOT, load
from cube_variants import ANSWERS, KEY, QUESTION, distance

EXP = ROOT / "experiments/2026-10-29_ed-analysis"
DIFFS = ["short", "medium", "long", "very_long", "very_very_long"]
VERIFY = {"CHECK", "REVISE"}
RNG = np.random.default_rng(9)


def ci(values, clusters):
    frame = pd.DataFrame({"v": values, "c": clusters}).dropna()
    grouped = frame.groupby("c").v.agg(["sum", "count"]).to_numpy()
    draws = RNG.integers(0, len(grouped), (2000, len(grouped)))
    boots = grouped[draws, 0].sum(1) / grouped[draws, 1].sum(1)
    return f"{frame.v.mean():+.3f} [{np.percentile(boots, 2.5):+.3f}, {np.percentile(boots, 97.5):+.3f}] n={len(frame)}"


def cut_index(seq):
    for i, t in enumerate(seq):
        if t.split(" ")[0] in VERIFY:
            return i
    return len(seq)


def answer_value(seq):
    values = [t.split(" ", 1)[1] for t in seq if t.startswith("SPITANSWER ")]
    return values[-1] if values else None


def reached_before_verify(seq):
    value = answer_value(seq)
    if value is None:
        return np.nan
    tail = value[5:] if len(value) == 10 and value[4] == "-" else value
    return any(value in t or tail in t.split(" ")[1:] for t in seq[:cut_index(seq)])


def truncated_row(pair):
    en, hi = pair
    cut = en[:cut_index(en)]
    final = [t for t in en if t.split(" ")[0] in ANSWERS][-1:]
    kept = cut if cut[-1:] == final else cut + final
    drop = lambda seq: [t for t in seq if t.split(" ")[0] not in VERIFY]
    return {"cut_len": len(cut), "cut_rds": distance(kept, hi), "drop_verify_rds": distance(drop(en), drop(hi))}


def opseq(seq):
    return [t.split(" ")[0] for t in seq if t.split(" ")[0] not in ANSWERS]


def op_pair(pair):
    return distance(opseq(pair[0]), opseq(pair[1]))


if __name__ == "__main__":
    pd.set_option("display.width", 220, "display.max_columns", 40, "display.max_rows", 500)
    frame = load()
    frame["question_id"] = frame.question_id.astype(int)
    frame["en"] = frame.en_seq.map(json.loads)
    frame["hi"] = frame.hi_seq.map(json.loads)
    frame["qkey"] = frame.difficulty.astype(str) + "|" + frame.task + "|" + frame.question_id.astype(str)
    std = frame[frame.set.eq("standard")].copy()
    ron_c = frame[frame.set.eq("ron") & frame.field.eq("content")].copy()
    ron_r = frame[frame.set.eq("ron") & frame.field.eq("reasoning_content")].copy()
    variants = pd.read_pickle(OUT / "variants.pkl")
    variants["question_id"] = variants.question_id.astype(int)

    print("=== a. english up to the first CHECK/REVISE, compared to full hindi (standard)")
    with Pool(16) as pool:
        cut = pd.DataFrame(pool.map(truncated_row, list(zip(std.en, std.hi)), chunksize=64), index=std.index)
    std = std.join(cut)
    for label, g in {"all": std, "answered": std[std.outcome.ne("unanswered")], "both correct": std[std.outcome.eq("both correct")]}.items():
        print(f"{label}: en_len {g.en_len.mean():.1f} (median {g.en_len.median():.0f}), en before first verify {g.cut_len.mean():.1f} (median {g.cut_len.median():.0f}), hi {g.hi_len.mean():.1f} (median {g.hi_len.median():.0f}), rds {g.norm_ed.mean():.3f}, rds truncated {g.cut_rds.mean():.3f}, drop verify ops {g.drop_verify_rds.mean():.3f}, verify share of en {1 - g.cut_len.sum() / g.en_len.sum():.3f}")

    print("\n=== b. difficulty rise in RDS: composition of outcomes vs within-outcome")
    labels = std.outcome.unique()
    short, vvl = std[std.difficulty.eq("short")], std[std.difficulty.eq("very_very_long")]
    share = lambda g: g.outcome.value_counts(normalize=True).reindex(labels).fillna(0)
    level = lambda g: g.groupby("outcome").norm_ed.mean().reindex(labels).fillna(0)
    print("short", round(short.norm_ed.mean(), 3), "very_very_long", round(vvl.norm_ed.mean(), 3))
    print(pd.DataFrame({"share_short": share(short), "share_vvl": share(vvl), "rds_short": level(short), "rds_vvl": level(vvl)}).round(3).to_string())
    mix = ((share(vvl) - share(short)) * (level(short) + level(vvl)) / 2).sum()
    within = (((share(short) + share(vvl)) / 2) * (level(vvl) - level(short))).sum()
    print("mix", round(mix, 3), "within", round(within, 3))

    print("\n=== c. step-type distance (no answers) on the 450 ron questions, with length-matched subset")
    questions = ron_r[QUESTION].drop_duplicates()
    rows = []
    with Pool(16) as pool:
        for name, part in {"standard": std.merge(questions, on=QUESTION), "ron content": ron_c, "ron reasoning": ron_r, "standard all": std}.items():
            part = part.sort_values(["task", "difficulty", "insertion", "question_id"], key=lambda c: c.astype(int) if c.name == "question_id" else c).reset_index(drop=True)
            cell = part.groupby(["task", "difficulty", "insertion"], observed=True)
            other_en = cell.en.transform(lambda c: list(np.roll(c.to_numpy(dtype=object), 1)))
            other_hi = cell.hi.transform(lambda c: list(np.roll(c.to_numpy(dtype=object), 1)))
            sets = {"en-hi same q": (part.en, part.hi), "en-hi other q": (part.en, other_hi), "en-en other q": (part.en, other_en), "hi-hi other q": (part.hi, other_hi)}
            results = {k: np.array(pool.map(op_pair, list(zip(*v)), chunksize=32), dtype=float) for k, v in sets.items()}
            for k, (a, b) in sets.items():
                la, lb = a.map(lambda s: len(opseq(s))).to_numpy(float), b.map(lambda s: len(opseq(s))).to_numpy(float)
                ratio = np.minimum(la, lb) / np.maximum(la, lb, where=np.maximum(la, lb) > 0, out=np.ones_like(la))
                rows.append({"set": name, "compare": k, "mean": np.nanmean(results[k]), "n": len(a), "matched": np.nanmean(results[k][ratio >= .8]), "matched_n": int((ratio >= .8).sum()), "len_a": la.mean(), "len_b": lb.mean()})
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "step_type_language_signature.csv", index=False)
    print(table.round(3).to_string(index=False))

    print("\n=== d. excess over same-language distance, per question")
    for (s, field), part in variants.groupby(["set", "field"]):
        same = part[part.kind.eq("en_hi_same_q")].groupby(QUESTION).full.mean()
        en_self = part[part.kind.eq("en_self")].groupby(QUESTION).full.mean()
        hi_self = part[part.kind.eq("hi_self")].groupby(QUESTION).full.mean()
        d = pd.concat([same.rename("same"), en_self.rename("e"), hi_self.rename("h")], axis=1).dropna()
        excess = d.same - (d.e + d.h) / 2
        print(s, field, ci(excess.to_numpy(), ["|".join(map(str, i)) for i in excess.index]), "same", round(d.same.mean(), 3), "self", round(((d.e + d.h) / 2).mean(), 3))
    on_ron = variants[variants.set.eq("standard")].merge(questions, on=QUESTION)
    same = on_ron[on_ron.kind.eq("en_hi_same_q")].groupby(QUESTION).full.mean()
    selfs = on_ron[on_ron.kind.isin(["en_self", "hi_self"])].groupby(QUESTION).full.mean()
    print("standard on ron questions", ci((same - selfs).dropna().to_numpy(), ["|".join(map(str, i)) for i in (same - selfs).dropna().index]))

    print("\n=== e. request parameters")
    for name in ["ron", "standard"]:
        data = json.load(open(EXP / "parsed" / name / "short.p.json", encoding="utf-8"))["records"]
        r = next(x for x in data if x["condition"] == "cot")
        print(name, {k: v for k, v in r["request"].items() if k != "messages"})
        print(name, "conditions", {c: sum(x["condition"] == c for x in data) for c in {x["condition"] for x in data}})

    print("\n=== f. stored tokens vs a fresh parse with the experiment's parser (sample)")
    sys.path.insert(0, str(EXP))
    import parser as exp_parser
    random.seed(9)
    for name in ["standard", "ron"]:
        for diff in ["short", "very_very_long"]:
            data = json.load(open(EXP / "parsed" / name / f"{diff}.p.json", encoding="utf-8"))["records"]
            same = total = 0
            for record in random.sample([r for r in data if r["condition"] == "cot"], 150):
                distractor = exp_parser.find_distractor({**record, "content": record["content"]["original"]})
                for field in ["content", "reasoning_content"]:
                    text, stored = record[field]["original"], record[field]["parsed"]
                    if text and text.strip():
                        same += stored == [t for s in exp_parser.parse_sentences(text, distractor, record["request"]["messages"][-1]["content"]) for t in s]
                        total += 1
            print(name, diff, f"{same}/{total} identical")

    print("\n=== f2. english: was the final answer already written before the first CHECK/REVISE?")
    std["pre"] = std.en.map(cut_index)
    std["reached"] = std.en.map(reached_before_verify)
    answered = std[std.en_correct.notna()]
    verified = answered[answered.pre < answered.en_len]
    print("has verify", round(len(verified) / len(answered), 3), "final value before first verify", round(verified.reached.mean(), 3), "position of first verify, median", round((verified.pre / verified.en_len).median(), 3))
    print(verified.groupby("task").reached.mean().round(3).to_dict())
    a = std[std.outcome.ne("unanswered")]
    print(a.groupby("difficulty", observed=True).agg(en=("en_len", "median"), en_pre=("pre", "median"), hi=("hi_len", "median"), en_mean=("en_len", "mean"), en_pre_mean=("pre", "mean"), hi_mean=("hi_len", "mean")).reindex(DIFFS).round(1).to_string())
    print(a.groupby("task").agg(en=("en_len", "median"), en_pre=("pre", "median"), hi=("hi_len", "median")).round(1).to_string())

    print("\n=== g. IGNORE tokens by task in english, similar distractor")
    s = std[std.insertion.eq("similar_insertion")]
    count = lambda seq: sum(t == "IGNORE" for t in seq)
    t = s.assign(en_i=s.en.map(count), hi_i=s.hi.map(count)).groupby("task")[["en_i", "hi_i"]].agg(["mean", lambda c: (c > 0).mean(), "max"])
    print(t.round(3).to_string())
    print("en median tokens among engaged", s[s.en.map(count) > 0].en.map(count).describe().round(1).to_dict())
    print("hi median tokens among engaged", s[s.hi.map(count) > 0].hi.map(count).describe().round(1).to_dict())

    print("\n=== h. outcome counts, standard")
    print(std.outcome.value_counts().to_string())
    answered = std[std.en_correct.notna() & std.hi_correct.notna()]
    print("accuracy on answered pairs: en", round(answered.en_correct.mean(), 3), "hi", round(answered.hi_correct.mean(), 3))
    print("share of pairs hi shorter", round((std.hi_len < std.en_len).mean(), 3))
