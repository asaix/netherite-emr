"""Insertions experiment: Contextual noise with similar/dissimilar distractors.

Default formula: tasks × samples_per_task × languages × variations (similar/dissimilar)
With defaults: 9 × 100 × 10 × 2 = 18,000 samples

Experiments can be configured with custom samples_per_task, languages, and tasks.
"""

import random
from pathlib import Path
from typing import List, Tuple

from trd.config.timeframes import MEDIUM_TIMEFRAME
from trd.experiments.base import BaseExperiment
from trd.generators import GENERATOR_MAP
from trd.templates.insertions import get_random_insertion, prepend_insertion
from trd.utils.io import save_to_csv


class InsertionsExperiment(BaseExperiment):
    """Insertions experiment with similar and dissimilar contextual distractors.
    
    This experiment generates samples with contextual insertions prepended to questions:
    - Similar: Time-related distractors (e.g., "I always forget how many days are in each month.")
    - Dissimilar: Unrelated distractors (e.g., "My brother just bought a blue motorcycle.")
    
    Sample count formula: tasks × samples_per_task × languages × 2 (variations)
    Default total: 9 × 100 × 10 × 2 = 18,000 samples
    """
    
    @property
    def experiment_name(self) -> str:
        return "insertions"
    
    def generate(self) -> int:
        """Generate the insertions dataset.
        
        Returns:
            Total number of samples generated
        """
        self._reset_seed()
        total_samples = 0
        config = MEDIUM_TIMEFRAME
        
        # Generate for both insertion types
        for insertion_type in ["similar", "dissimilar"]:
            output_path = self._get_output_path(subdir=insertion_type)
            
            for language in self.languages:
                # Reset seed for each language to ensure reproducibility
                self._reset_seed()
                
                for task_name in self.tasks:
                    samples = self._generate_task_with_insertions(
                        task_name=task_name,
                        config=config,
                        language=language,
                        output_path=output_path,
                        insertion_type=insertion_type,
                    )
                    total_samples += samples
        
        return total_samples
    
    def _generate_task_with_insertions(
        self,
        task_name: str,
        config,
        language: str,
        output_path: Path,
        insertion_type: str,
    ) -> int:
        """Generate dataset for a single task with insertions.
        
        Args:
            task_name: Name of the task
            config: Timeframe configuration
            language: Language code
            output_path: Output directory
            insertion_type: Either "similar" or "dissimilar"
            
        Returns:
            Number of samples generated
        """
        generator_class = GENERATOR_MAP[task_name]
        generator = generator_class(config, language)
        
        # Get the template key for insertions lookup
        template_key = generator.template_key
        
        # Generate samples with insertions
        data: List[Tuple[str, str]] = [("question", "answer")]  # Header
        
        for _ in range(self.samples_per_task):
            sample = generator.generate_sample()
            
            # Get a random insertion for this task in the correct language
            similar = (insertion_type == "similar")
            insertion = get_random_insertion(language, template_key, similar)
            
            # Prepend insertion to question
            question_with_insertion = prepend_insertion(sample.question, insertion)
            
            data.append((question_with_insertion, sample.answer))
        
        # Save with standardized naming
        filename = f"{task_name}_{config.name}_{language}.csv"
        filepath = output_path / filename
        save_to_csv(data, filepath)
        
        return self.samples_per_task
    
    def get_total_expected_samples(self) -> int:
        """Calculate expected samples: tasks × samples × languages × 2 variations."""
        num_variations = 2  # similar and dissimilar
        return len(self.tasks) * self.samples_per_task * len(self.languages) * num_variations
