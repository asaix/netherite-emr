from common import *

F = frame()
rng = np.random.default_rng(60)
tm = lambda s: int(s[:2]) * 60 + int(s[3:5])
T = F[F.task.isin(["time_addition", "time_subtraction"]) & F.p_ans.fillna("").str.fullmatch(r"\d{2}:\d{2}")]
twelve = T[((T.p_ans.map(tm) - T.gold.map(tm)) % 1440 == 720)]
canon = {"date_addition": r"\d{4}-\d{2}-\d{2}", "date_subtraction": r"\d{4}-\d{2}-\d{2}", "date_recurrence": r"\d{4}-\d{2}-\d{2}", "time_addition": r"\d{2}:\d{2}", "time_subtraction": r"\d{2}:\d{2}", "date_duration": r"-?\d+", "time_duration": r"-?\d+", "interval_date": r"\d{4}-\d{2}-\d{2} to \d{4}-\d{2}-\d{2}", "day_of_week": r"\S+"}
F["canon"] = [bool(re.fullmatch(canon[t], a)) if isinstance(a, str) else None for t, a in zip(F.task, F.p_ans)]
CASES = {
    "answer_not_on_last_line": F[F.answered & ~F.on_last],
    "my_label_only": F[F.my_raw.notna() & ~F.answered],
    "answered_but_length": F[F.answered & (F.finish == "length")],
    "stop_unanswered": F[~F.answered & (F.finish == "stop")],
    "noncanonical_format": F[F.canon == False],
    "twelve_hour_off": twelve,
    "parser_bug": F[F.p_ans != F.r_ans].dropna(subset=["p_ans"]),
    "dow_wrong": F[(F.task == "day_of_week") & (F.acc == 0)],
    "dow_right": F[(F.task == "day_of_week") & (F.acc == 1)],
    "time_right": F[F.task.isin(["time_addition", "time_subtraction"]) & (F.acc == 1)],
    "wrong_other": F[(F.acc == 0) & ~F.task.isin(["day_of_week"])],
}
print({k: (len(v), v.groupby("lang").size().to_dict()) for k, v in CASES.items()})
QUOTA = {"answer_not_on_last_line": 6, "my_label_only": 3, "answered_but_length": 5, "stop_unanswered": 1, "noncanonical_format": 8, "twelve_hour_off": 8, "parser_bug": 5, "dow_wrong": 8, "dow_right": 4, "time_right": 4, "wrong_other": 60}
for lang in LANGS:
    ids = []
    for k, v in CASES.items():
        s = v[v.lang == lang]
        n = min(QUOTA[k], len(s))
        if n:
            ids += [(k, i) for i in rng.choice(s.id.to_numpy(), n, replace=False)]
    have = {i for _, i in ids}
    ids = ids[:]
    want = {i: k for k, i in ids if k != "wrong_other"}
    for k, i in ids:
        if k == "wrong_other" and len(want) < 60 and i not in want:
            want[i] = k
    rows = []
    for lvl in LEVELS:
        for r in json.load(open(ROOT / "responses/standard" / f"{lvl}.json", encoding="utf-8")):
            if r["id"] in want:
                f = F[F.id == r["id"]].iloc[0]
                rows.append({"case": want[r["id"]], "id": r["id"], "gold": r["meta"]["answer"], "finish": r["finish_reason"], "project_answer": f.p_ans, "project_correct": f.p_ok, "my_extract": f.my_raw, "my_correct": f.my_ok, "tail": (r["content"] or "")[-260:]})
    d = pd.DataFrame(rows).sort_values(["case", "id"])
    d.to_csv(HAND / f"sample_{lang}.csv", index=False)
    print(lang, len(d))
