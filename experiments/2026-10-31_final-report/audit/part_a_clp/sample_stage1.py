import pickle
import random
import sys
import pandas as pd

sys.dont_write_bytecode = True
df = pd.DataFrame(pickle.load(open("cache/rows.pkl", "rb")))
texts = pickle.load(open("cache/texts.pkl", "rb"))
feats = pd.DataFrame(pickle.load(open("cache/feats.pkl", "rb"))).set_index(["level", "task", "q"])
c = df[(df.cond == "clp") & (df.q < 50) & df.task.isin(["date_addition", "date_subtraction", "date_recurrence"]) & df.scored]
rows = c.sample(40, random_state=20261031)
print("SEED 20261031 N 40")
for i, r in enumerate(rows.itertuples()):
    t = texts["s1", r.level, r.task, r.q, r.ins]
    en = feats.loc[(r.level, r.task, r.q), "en"]
    gold = feats.loc[(r.level, r.task, r.q), "answer_en"]
    print(f"\n#### {i} {r.level}/{r.task}/{r.q}/{r.ins} gold={gold} s1_last={r.s1_last} s1_gold={r.s1_gold} s2_ans={r.answer} EN_Q: {en}")
    print(t if len(t) < 1500 else t[:500] + "\n[...]\n" + t[-900:])

other = c[(c.s1_gold == False)]
rec = other[(other.correct == True) & (other.s1_has_date == True)].sample(20, random_state=11)
print("\n\n=========== OTHER BIN, STAGE 2 CORRECT, N 20 (seed 11)")
for i, r in enumerate(rec.itertuples()):
    t = texts["s1", r.level, r.task, r.q, r.ins]
    gold = feats.loc[(r.level, r.task, r.q), "answer_en"]
    print(f"\n#### R{i} {r.level}/{r.task}/{r.q}/{r.ins} gold={gold} s1_last={r.s1_last} any_gold={r.s1_any_gold} s2_ans={r.answer}")
    print(t[-420:])
print("\n\n=========== NO DATE IN STAGE 1 (all)")
none = c[c.s1_has_date == False]
print(len(none), none.correct.astype(float).mean())
for i, r in enumerate(none.sample(12, random_state=12).itertuples()):
    t = texts["s1", r.level, r.task, r.q, r.ins]
    gold = feats.loc[(r.level, r.task, r.q), "answer_en"]
    print(f"\n#### N{i} {r.level}/{r.task}/{r.q}/{r.ins} gold={gold} correct={r.correct} s2_ans={r.answer} s1_cut={r.s1_cutoff}")
    print(t[:350] + (" [...] " + t[-250:] if len(t) > 600 else t[350:]))
