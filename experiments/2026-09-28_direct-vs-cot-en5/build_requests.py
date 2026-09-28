"""Turn a config + the TRD-generated CSV dataset into a requests.jsonl for
run_batch.py.

  python build_requests.py --config configs/exp1_direct_vs_cot.yaml \
      --dataset-dir Dataset --output requests/exp1.jsonl

The problem bank is whatever custom-generator.py already wrote under
Dataset/<difficulty>/<variant>/<task>_<difficulty>_<language>.csv - there is
no separate problems.jsonl conversion step.

A "problem" here is a row index shared by every requested
(question_lang, distractor_type) file within one (task, difficulty) cell.
custom-generator.py snapshots/restores the global `random` state around its
insertion draw, so picking a distractor no longer perturbs the sequence
generate_sample() sees - all distractor variants (and all languages) stay
row-aligned by construction. Each file is still pruned of duplicate questions
independently, so a stray collision can still knock one file out of sync for
a given index. Before treating an index as one problem, this script checks
that every requested distractor_type agrees on the answer there (checked
separately per language, since the answer text itself can be localized);
indices that disagree are dropped rather than silently paired as if they
were the same problem - see build_problem_pool().
"""
import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

import yaml

TEMPLATE_VERSION = "v1"

# Must match trd.config.timeframes.DIFFICULTY_LEVELS
DIFFICULTY_LEVELS = ["short", "medium", "long", "very_long", "very_very_long"]

# Must match trd.config.defaults.ALL_TASKS
ALL_TASKS = [
    "date_addition", "date_subtraction", "time_addition", "time_subtraction",
    "date_duration", "time_duration", "date_recurrence", "interval_date",
    "day_of_week",
]

# question_lang (as used in configs/prompts.yaml) -> locale suffix on disk
LANG_TO_LOCALE = {"en": "en_US", "hi": "hi_IN"}

# distractor_type (as used in configs/prompts.yaml) -> variant directory name
DISTRACTOR_TO_VARIANT = {
    "none": "no-insertions",
    "related": "insertions-similar",
    "unrelated": "insertions-dissimilar",
}


def csv_path(dataset_dir, task, difficulty, question_lang, distractor_type):
    variant = DISTRACTOR_TO_VARIANT[distractor_type]
    locale = LANG_TO_LOCALE[question_lang]
    return dataset_dir / difficulty / variant / f"{task}_{difficulty}_{locale}.csv"


def load_rows(path):
    """Return a CSV's (question, answer) rows, header dropped."""
    if not path.exists():
        raise SystemExit(f"missing dataset file: {path}")
    with open(path, encoding="utf-8") as f:
        return list(csv.reader(f))[1:]


def template_id(condition, question_lang, reasoning_lang):
    return f"{condition}_{question_lang}_{reasoning_lang}_{TEMPLATE_VERSION}"


def resolve_reasoning_lang(arm_value, question_lang):
    """'match' means reason in whatever language the question is in."""
    return question_lang if arm_value == "match" else arm_value


def build_problem_pool(cfg, dataset_dir):
    """Load every requested CSV and find the row indices safe to pair.

    Returns one (task, difficulty, aligned_indices, rows_by_combo) entry per
    cell, where aligned_indices are the row positions at which every
    requested distractor_type agrees on the answer, checked separately per
    question_lang. Answers are only compared within one language: languages
    are already guaranteed to be paired by construction (each language
    restarts generation from the same seed and prune() keeps them in sync),
    but the answer text itself can be localized (e.g. "Thursday" vs
    "गुरुवार" for day_of_week), so it must never be compared across
    languages.
    """
    wanted_tasks = ALL_TASKS if cfg["tasks"] == "all" else cfg["tasks"]
    combos = [(qlang, dtype) for qlang in cfg["question_langs"]
              for dtype in cfg["distractor_types"]]

    pool = []
    for task in wanted_tasks:
        for difficulty in cfg["difficulties"]:
            rows_by_combo = {
                (qlang, dtype): load_rows(csv_path(dataset_dir, task, difficulty, qlang, dtype))
                for qlang, dtype in combos
            }
            n_rows = min(len(rows) for rows in rows_by_combo.values())

            aligned = [
                i for i in range(n_rows)
                if all(
                    len({rows_by_combo[(qlang, dtype)][i][1]
                         for dtype in cfg["distractor_types"]}) == 1
                    for qlang in cfg["question_langs"]
                )
            ]
            dropped = n_rows - len(aligned)
            if dropped:
                print(f"  {task}/{difficulty}: dropped {dropped}/{n_rows} rows "
                      f"where distractor_types disagreed on the answer within "
                      f"a language (not the same underlying problem)")

            pool.append((task, difficulty, aligned, rows_by_combo))
    return pool


def sample_problems(pool, cfg, rng):
    """Pick n_per_cell paired problems per (task, difficulty) cell and
    assemble their renderings.
    """
    chosen = []
    for task, difficulty, aligned, rows_by_combo in pool:
        n = min(cfg["n_per_cell"], len(aligned))
        if n < cfg["n_per_cell"]:
            print(f"  warning: {(task, difficulty)} has only {len(aligned)} "
                  f"paired problems, wanted {cfg['n_per_cell']}")

        for i in rng.sample(sorted(aligned), n):
            renderings = defaultdict(dict)
            expected = None
            for (qlang, dtype), rows in rows_by_combo.items():
                question, answer = rows[i]
                renderings[qlang][dtype] = {"text": question}
                expected = answer

            chosen.append({
                "problem_id": f"{task}_{difficulty}_{i}",
                "task": task,
                "difficulty": difficulty,
                "expected": expected,
                "renderings": renderings,
            })
    return chosen


def build(cfg, pool, templates, rng):
    requests = []

    for p in sample_problems(pool, cfg, rng):
        for qlang in cfg["question_langs"]:
            for dtype in cfg["distractor_types"]:
                rendering = p["renderings"][qlang][dtype]

                for arm in cfg["arms"]:
                    condition = arm["condition"]
                    rlang = resolve_reasoning_lang(arm["reasoning_lang"], qlang)
                    tid = template_id(condition, qlang, rlang)
                    if tid not in templates:
                        raise SystemExit(f"missing template in prompts.yaml: {tid}")

                    prompt = templates[tid].format(question=rendering["text"])
                    req_id = (f"{cfg['experiment_tag']}_{p['problem_id']}"
                              f"_{qlang}_{rlang}_{condition}_{dtype}")

                    requests.append({
                        "id": req_id,
                        "condition": condition,
                        "messages": [{"role": "user", "content": prompt}],
                        "meta": {
                            "problem_id": p["problem_id"],
                            "task": p["task"],
                            "difficulty": p["difficulty"],
                            "question_lang": qlang,
                            "reasoning_lang": rlang,
                            "distractor_type": dtype,
                            "expected": p["expected"],
                            "prompt_template_id": tid,
                            "experiment_tag": cfg["experiment_tag"],
                        },
                    })

    return requests


def main(args):
    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    with open(args.prompts, encoding="utf-8") as f:
        templates = yaml.safe_load(f)

    dataset_dir = Path(args.dataset_dir)
    rng = random.Random(args.sample_seed)

    print(f"building {cfg['experiment_tag']} from {dataset_dir}")
    pool = build_problem_pool(cfg, dataset_dir)
    requests = build(cfg, pool, templates, rng)

    ids = [r["id"] for r in requests]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate request ids - check the config for a "
                         "repeated arm")

    with open(args.output, "w", encoding="utf-8") as f:
        for r in requests:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    n_cot = sum(1 for r in requests if r["condition"] == "cot")
    print(f"wrote {len(requests)} requests to {args.output} "
          f"({n_cot} cot, {len(requests) - n_cot} direct)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--dataset-dir", required=True,
                     help="root of the CSVs custom-generator.py wrote, e.g. Dataset/")
    ap.add_argument("--prompts", default="prompts.yaml")
    ap.add_argument("--output", required=True)
    ap.add_argument("--sample-seed", type=int, default=0,
                    help="fixes which problems are picked, so re-building a "
                         "config gives the same request set")
    main(ap.parse_args())
