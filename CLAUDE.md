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
- `sarvam.py`: runs a dataset through the Sarvam API; settings in `config/sarvam.yaml`, prompts in `config/prompt.yaml`, `problems_per_task` in `config/general.yaml`.
