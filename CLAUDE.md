# CLAUDE.md

Evaluating multilingual temporal reasoning in LLMs through a chain-of-thought lens.

## Git

- `main` is the main branch. Never commit directly to `main`; work on a `feat/<feature-name>` branch.
- Merge into `main` with squash merges unless the individual commits must be preserved.
- Only commit or push when asked.

## Organization

- Keep files and directories organized, with clear names. Don't fill normal codebase directories with instruction files, scratch files or results.
- Each experiment run lives in `experiments/<YYYY-MM-DD>_<experiment-name>/` and contains:
  - copies of the files as they were run,
  - all outputs the program generates (nothing written outside that folder),
  - its hyperparameters, in a `.cfg`/`.yaml` file or in the Python file,
  - its input data if that data can change (unchanging data doesn't need to be copied).
- Changes made while experimenting stay inside that experiment's folder.
- Hyperparameters and settings go in config files (`config/`) or the Python file, never in environment variables.

## Code style

- Minimal code. No comments unless asked for.
- JSON output is pretty-printed (`indent=2`, `ensure_ascii=False`), not dumped on one line.

## Layout

- `tools/temporal-reasoning-dataset/`: the original TRD code from the paper. Do not modify it; import its classes and extend them elsewhere.
- `custom-generator.py`: builds the dataset as `<output>/<difficulty>/<task>_<lang>.json`. Each question ID maps to `no_insertion`, `similar_insertion`, `dissimilar_insertion` and `answer`. Question IDs match across languages.
- `config/generator.cfg`: languages, seed, `SAMPLES_PER_TASK`, `DRAWS_MULTIPLIER`.
- `sarvam.py`: runs a dataset through the Sarvam API; settings in `config/sarvam.yaml`, prompts in `config/prompt.yaml`, `problems_per_task`, `languages` and `conditions` (`direct`, `cot`, `en-cot`) in `config/general.yaml`. `en-cot` gives the question in its own language and asks for reasoning in `en_cot_language` (`config/prompt.yaml`).
- `parser.py`: turns CoT text into op tokens (e.g. `SUB 2025-05-26 4`). `python parser.py --input results.json --output parsed.json` writes `{stats, records}` (GIVEN is checked against each record's question), with `content` and `reasoning_content` nested as `{original, parsed}` (`parsed` is null when the text is null or empty), and prints the stats. Ops, argument labels, trigger phrases and other settings are in `config/parser.yaml`; flow diagram in `docs/parser.svg`.
- `tests/test_parser.py`: hand-checked parser cases; run `python tests/test_parser.py` after editing `config/parser.yaml`.
- `tests/parser_regression/`: full-dataset checks for parser changes. `regress.py <baseline dir> <name>` compares a saved parser (`baseline/`) with the current one sentence by sentence; `scan.py <name>` lists the most frequent uncovered sentence shapes, the shapes behind each op and consistency flags. Results and findings in `outputs/SUMMARY.md`.
- `ed.py`: pairs English/Hindi CoT records from a parsed.json and computes Levenshtein edit distance over their op tokens (skipping pairs where either side is empty or null), normalized by the longer length, where a substitution between tokens that differ only by a missing year/month (`06-05`, `5` or `06` vs `2025-06-05`/`2025-06`) costs `partial_date_cost` from `config/ed.yaml`, for `content` and `reasoning_content`. Prints aggregates over every combination of difficulty, task and insertion; `--output` saves a CSV with the aggregates on top, a blank line, then one row per pair, dropping columns that are entirely empty unless `--nodrop` is given. Needs pandas (in `.venv`). Tested by `tests/test_ed.py`; diagram in `docs/ed.svg`.

## other

- don't warn the user about sarvam api keys being part of the git history
