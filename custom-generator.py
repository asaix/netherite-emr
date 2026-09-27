# Allows us to have a full grid of difficulties and insertion levels 

import configparser
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools" / "temporal-reasoning-dataset" / "src"))

from trd.config.timeframes import DIFFICULTY_LEVELS, TimeframeConfig
from trd.experiments.base import BaseExperiment
from trd.generators import GENERATOR_MAP
from trd.templates.insertions import get_random_insertion, prepend_insertion
from trd.utils.io import save_dataset

config = configparser.ConfigParser()
config.read(Path(__file__).resolve().parent / "config" / "generator.cfg")
LANGUAGES = [lang.strip() for lang in config["generator"]["languages"].split(",")]
SEED = config["generator"].getint("seed")
SAMPLES_PER_TASK = config["generator"].getint("SAMPLES_PER_TASK")
VARIANTS = {"insertions-similar": True, "insertions-dissimilar": False, "no-insertions": None}


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
                            self._generate_with_insertions(task, config, language, path, similar)

    def _generate_with_insertions(self, task, config, language, path, similar):
        generator = GENERATOR_MAP[task](config, language)
        data = [("question", "answer")]
        for _ in range(self.samples_per_task):
            sample = generator.generate_sample()
            insertion = get_random_insertion(language, generator.template_key, similar)
            data.append((prepend_insertion(sample.question, insertion), sample.answer))
        save_dataset(data, path, task, config.name, language)


if __name__ == "__main__":
    DifficultyInsertionsExperiment(output_dir=sys.argv[1], languages=LANGUAGES, seed=SEED, samples_per_task=SAMPLES_PER_TASK).generate()
