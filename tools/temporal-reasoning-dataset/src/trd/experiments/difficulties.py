"""Difficulties experiment: All 5 difficulty levels across tasks and languages.

Default formula: tasks × samples_per_task × languages × difficulties
With defaults: 9 × 100 × 10 × 5 = 45,000 samples

Experiments can be configured with custom samples_per_task, languages, and tasks.
"""

from trd.config.timeframes import DIFFICULTY_LEVELS, TimeframeConfig
from trd.experiments.base import BaseExperiment


class DifficultiesExperiment(BaseExperiment):
    """Difficulties experiment across all 5 difficulty levels.
    
    This experiment generates samples for all tasks across all languages
    for each difficulty level: short, medium, long, very_long, very_very_long.
    
    Sample count formula: tasks × samples_per_task × languages × difficulties
    Default total: 9 × 100 × 10 × 5 = 45,000 samples
    """
    
    @property
    def experiment_name(self) -> str:
        return "difficulties"
    
    def generate(self) -> int:
        """Generate the difficulties dataset.
        
        Returns:
            Total number of samples generated
        """
        self._reset_seed()
        total_samples = 0
        
        for difficulty in DIFFICULTY_LEVELS:
            config = TimeframeConfig.from_name(difficulty)
            output_path = self._get_output_path(subdir=difficulty)
            
            for language in self.languages:
                # Reset seed for each language to ensure reproducibility
                self._reset_seed()
                
                for task_name in self.tasks:
                    samples = self._generate_task_dataset(
                        task_name=task_name,
                        config=config,
                        language=language,
                        output_path=output_path,
                    )
                    total_samples += samples
        
        return total_samples
    
    def get_total_expected_samples(self) -> int:
        """Calculate expected samples: tasks × samples × languages × difficulties."""
        num_difficulties = len(DIFFICULTY_LEVELS)
        return len(self.tasks) * self.samples_per_task * len(self.languages) * num_difficulties
