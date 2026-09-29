# Allows us to have a full grid of difficulties and insertion levels

import configparser
import random
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
from trd.utils.io import save_to_json

config = configparser.ConfigParser()
config.read(Path(__file__).resolve().parent / "config" / "generator.cfg")
LANGUAGES = [lang.strip() for lang in config["generator"]["languages"].split(",")]
SEED = config["generator"].getint("seed")
SAMPLES_PER_TASK = config["generator"].getint("SAMPLES_PER_TASK")
DRAWS_MULTIPLIER = config["generator"].getint("DRAWS_MULTIPLIER")


class DifficultyInsertionsExperiment(BaseExperiment):
    experiment_name = "difficulty_insertions"

    def generate(self):
        for difficulty in DIFFICULTY_LEVELS:
            config = TimeframeConfig.from_name(difficulty)
            self._reset_seed()
            for task in self.tasks:
                generators = {
                    language: GENERATOR_MAP[task](config, language)
                    for language in self.languages
                }
                questions = {language: {} for language in self.languages}
                for _ in range(DRAWS_MULTIPLIER * self.samples_per_task):
                    state = random.getstate()
                    draw = {}
                    for language, generator in generators.items():
                        random.setstate(state)
                        draw[language] = self._sample(generator, language)
                    if all(
                        d["no_insertion"] not in questions[language]
                        for language, d in draw.items()
                    ):
                        for language, d in draw.items():
                            questions[language][d["no_insertion"]] = d
                    if len(questions[self.languages[0]]) == self.samples_per_task:
                        break
                for language, q in questions.items():
                    path = self.output_dir / difficulty / f"{task}_{language}.json"
                    save_to_json(dict(enumerate(q.values())), path)
                    print(f"{path}: {len(q)}")

    def _sample(self, generator, language):
        sample = generator.generate_sample()
        return {
            "no_insertion": sample.question,
            "similar_insertion": prepend_insertion(
                sample.question,
                get_random_insertion(language, generator.template_key, True),
            ),
            "dissimilar_insertion": prepend_insertion(
                sample.question,
                get_random_insertion(language, generator.template_key, False),
            ),
            "answer": sample.answer,
        }


if __name__ == "__main__":
    DifficultyInsertionsExperiment(
        output_dir=sys.argv[1],
        languages=LANGUAGES,
        seed=SEED,
        samples_per_task=SAMPLES_PER_TASK,
    ).generate()
