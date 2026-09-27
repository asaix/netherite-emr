"""Variations experiment: Medium difficulty across all tasks and languages.

Default formula: tasks × samples_per_task × languages
With defaults: 9 × 100 × 10 = 9,000 samples

Experiments can be configured with custom samples_per_task, languages, and tasks.
"""

from trd.config.timeframes import MEDIUM_TIMEFRAME
from trd.experiments.base import BaseExperiment


class VariationsExperiment(BaseExperiment):
    """Variations experiment using medium difficulty configuration.
    
    This is the baseline experiment that generates samples for all tasks
    across all languages using the medium difficulty level.
    
    Sample count formula: tasks × samples_per_task × languages
    Default total: 9 × 100 × 10 = 9,000 samples
    """
    
    @property
    def experiment_name(self) -> str:
        return "variations"
    
    def generate(self) -> int:
        """Generate the variations dataset.
        
        Returns:
            Total number of samples generated
        """
        self._reset_seed()
        total_samples = 0
        config = MEDIUM_TIMEFRAME
        output_path = self._get_output_path()
        
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
        """Calculate expected samples: tasks × samples × languages × 1."""
        return len(self.tasks) * self.samples_per_task * len(self.languages)
