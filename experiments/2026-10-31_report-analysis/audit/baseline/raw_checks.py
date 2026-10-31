from common import *

F = frame().set_index("id")
out = {"direct_first_vs_answer": {}, "examples": []}
rows = []
samples = []
for lvl in LEVELS:
    for r in json.load(open(ROOT / "responses/standard" / f"{lvl}.json", encoding="utf-8")):
        m = r["meta"]
        c = (r["content"] or "").translate(DIG)
        if r["condition"] == "direct":
            lines = [x.strip() for x in c.split("\n") if x.strip()]
            if len(lines) >= 2 and LABEL.search(lines[-1]):
                prev = re.sub(LABEL, "", lines[-2]).strip(" *`.।")
                ans = F.at[r["id"], "p_ans"]
                gv = gold_typed(m["task"], m["answer"])
                tp = typed(m["task"], prev)
                bare = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}(?: to \d{4}-\d{2}-\d{2})?|\d{1,2}:\d{2}|-?\d+|[^\s\d]+", prev)) and len(lines) == 2
                ta = typed(m["task"], ans) if isinstance(ans, str) else None
                if tp is not None and ta is not None:
                    rows.append({"id": r["id"], "lang": m["language"], "task": m["task"], "level": lvl, "insertion": m["insertion"], "prev_ok": tp == gv, "ans_ok": ta == gv, "same": tp == ta, "bare": bare})
        if m["task"] == "date_recurrence" and r["condition"] == "cot" and m["insertion"] == "similar_insertion" and F.at[r["id"], "sim_idx"] == 4 and lvl in ("short", "medium") and len(samples) < 8 and m["language"] == "en_US" and r["finish_reason"] == "length":
            samples.append({"id": r["id"], "head": r["content"][:700], "mid": r["content"][6000:6500], "tail": r["content"][-400:]})
    del r
P = pd.DataFrame(rows)
P = P[P.bare]
for (l), g in P.groupby("lang"):
    out["direct_first_vs_answer"][l] = {"n_with_two_values": len(g), "disagree": int((~g.same).sum()), "prev_right_answer_wrong": int((g.prev_ok & ~g.ans_ok).sum()), "prev_wrong_answer_right": int((~g.prev_ok & g.ans_ok).sum()), "acc_answer": round(100 * float(g.ans_ok.mean()), 2), "acc_prev": round(100 * float(g.prev_ok.mean()), 2)}
out["direct_first_vs_answer_task"] = {f"{l}/{t}": {"n": len(g), "disagree": int((~g.same).sum()), "prev_right_answer_wrong": int((g.prev_ok & ~g.ans_ok).sum()), "prev_wrong_answer_right": int((~g.prev_ok & g.ans_ok).sum())} for (l, t), g in P.groupby(["lang", "task"])}
out["jan_sentence_cutoff_samples"] = samples
dump(out, "results_raw.json")
print(json.dumps(out["direct_first_vs_answer"], indent=1))
print(json.dumps({k: v for k, v in out["direct_first_vs_answer_task"].items() if v["disagree"] > 20}, indent=0))
for s in samples[:3]:
    print(s["id"], "\nHEAD:", s["head"][:600], "\nMID:", s["mid"][:300], "\nTAIL:", s["tail"][-250:], "\n")
