# Allows us to have a full grid of difficulties and insertion levels

import configparser
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent / "tools" / "temporal-reasoning-dataset" / "src"
    ),
)

from trd.config.timeframes import DIFFICULTY_LEVELS, TimeframeConfig
from trd.experiments.base import BaseExperiment
from trd.generators import GENERATOR_MAP
from trd.templates.insertions import get_random_insertion, prepend_insertion
from trd.utils.io import load_from_csv, save_dataset, save_to_csv

config = configparser.ConfigParser()
config.read(Path(__file__).resolve().parent / "config" / "generator.cfg")
LANGUAGES = [lang.strip() for lang in config["generator"]["languages"].split(",")]
SEED = config["generator"].getint("seed")
SAMPLES_PER_TASK = config["generator"].getint("SAMPLES_PER_TASK")
VARIANTS = {
    "insertions-similar": True,
    "insertions-dissimilar": False,
    "no-insertions": None,
}


class DifficultyInsertionsExperiment(BaseExperiment):
    experiment_name = "difficulty_insertions"

    def generate(self):
        for difficulty in DIFFICULTY_LEVELS:
            config = TimeframeConfig.from_name(difficulty)
            for variant, similar in VARIANTS.items():
                path = self.output_dir / difficulty / variant
                for language in self.languages:
                    self._reset_seed()
                    for task in self.tasks:
                        if similar is None:
                            self._generate_task_dataset(task, config, language, path)
                        else:
                            self._generate_with_insertions(
                                task, config, language, path, similar
                            )

    def _generate_with_insertions(self, task, config, language, path, similar):
        generator = GENERATOR_MAP[task](config, language)
        data = [("question", "answer")]
        for _ in range(self.samples_per_task):
            sample = generator.generate_sample()
            insertion = get_random_insertion(language, generator.template_key, similar)
            data.append((prepend_insertion(sample.question, insertion), sample.answer))
        save_dataset(data, path, task, config.name, language)


def unique_rows(data):
    first = {}
    for i, (question, _) in enumerate(data):
        first.setdefault(question, i)
    return set(first.values())


def prune(output_dir):
    for ref in sorted(Path(output_dir).rglob(f"*_{LANGUAGES[0]}.csv")):
        stem = ref.name.removesuffix(f"{LANGUAGES[0]}.csv")
        files = [ref.with_name(f"{stem}{language}.csv") for language in LANGUAGES]
        datasets = [load_from_csv(f) for f in files]
        keep = set.intersection(*map(unique_rows, datasets))
        for f, data in zip(files, datasets):
            save_to_csv([row for i, row in enumerate(data) if i in keep], f)
            print(f"{f}: {len(keep) - 1}")


if __name__ == "__main__":
    DifficultyInsertionsExperiment(
        output_dir=sys.argv[1],
        languages=LANGUAGES,
        seed=SEED,
        samples_per_task=SAMPLES_PER_TASK,
    ).generate()
    # removes duplicates while guaranteeing that each specific csv at /some/path/something_english.csv has the exact same questions and number of questions as /some/path/something_hindi.csv
    prune(sys.argv[1])
