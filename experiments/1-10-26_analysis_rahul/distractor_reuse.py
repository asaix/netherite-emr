import pandas as pd

from temporal_answers import HERE, M, distractor_features, distractor_texts, judged, load_records, question_key, reuses_distractor

records = load_records()
(HERE / "outputs").mkdir(exist_ok=True)
distractors = distractor_texts(records)

rows = []
for r, kind, answer, gold in judged(records):
    if answer is None or M.is_correct(r):
        continue
    m = r["meta"]
    key = question_key(r)
    if m["insertion"] == "no_insertion":
        sources = [("no_insertion_placebo", d) for d in ("similar_insertion", "dissimilar_insertion")]
    else:
        sources = [("inserted", m["insertion"])]
    for source, insertion in sources:
        features = distractor_features(distractors[key, insertion])
        if any(features.values()):
            rows.append(
                {
                    "id": r["id"],
                    "task": m["task"],
                    "language": m["language"],
                    "condition": r["condition"],
                    "distractor_type": insertion,
                    "source": source,
                    "reuses_distractor": reuses_distractor(kind, answer, gold, features),
                }
            )

reuse = pd.DataFrame(rows)
reuse.to_csv(HERE / "outputs" / "distractor_reuse_per_response.csv", index=False)

keys = ["task", "language", "condition", "distractor_type"]
table = reuse.groupby(keys + ["source"])["reuses_distractor"].agg(wrong="count", reuse="sum", reuse_rate="mean").unstack("source")
table.columns = [f"{name}_{source}" for name, source in table.columns]
table = table.reset_index()
table["rate_inserted_minus_placebo"] = table["reuse_rate_inserted"] - table["reuse_rate_no_insertion_placebo"]
table.round(3).to_csv(HERE / "outputs" / "distractor_reuse.csv", index=False)

pooled = reuse.groupby(["language", "condition", "distractor_type", "source"])["reuses_distractor"].agg(wrong="count", reuse="sum", reuse_rate="mean")
print(pooled.round(3).to_string())
print(table.round(3).to_string(index=False))
