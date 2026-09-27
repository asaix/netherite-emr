"""Memorization experiment: Temporal shifts across years (2025-2095).

Default formula: tasks × samples_per_task × languages × years
With defaults: 4 × 100 × 10 × 8 = 32,000 samples

Tests how models handle dates far from their training distribution.
Experiments can be configured with custom samples_per_task, languages, tasks, and years.
"""

from typing import List, Optional

from trd.config.defaults import MEMORIZATION_TASKS, MEMORIZATION_YEARS
from trd.config.timeframes import MEDIUM_TIMEFRAME
from trd.experiments.base import BaseExperiment


class MemorizationExperiment(BaseExperiment):
    """Memorization experiment testing temporal stability across years.
    
    This experiment tests how models handle dates spanning across multiple decades,
    extending beyond the likely boundaries of most pretraining corpora.
    
    Default tasks included:
    - day_of_week: Pure memorization task (which weekday is a date?)
    - interval_date: Memorization task (week boundaries)
    - date_addition: Reasoning task (to compare with memorization)
    - date_recurrence: Reasoning task (to compare with memorization)
    
    Default years: 2025, 2035, 2045, 2055, 2065, 2075, 2085, 2095 (8 years, step of 10)
    
    Sample count formula: tasks × samples_per_task × languages × years
    Default total: 4 × 100 × 10 × 8 = 32,000 samples
    """
    
    def __init__(
        self,
        samples_per_task: int = 100,
        languages: Optional[List[str]] = None,
        tasks: Optional[List[str]] = None,
        output_dir: str = "./output",
        seed: int = 9,
        format: str = "csv",
        years: Optional[List[int]] = None,
    ):
        """Initialize the memorization experiment.
        
        Args:
            samples_per_task: Number of samples per task per language per year
            languages: List of language codes (default: all supported)
            tasks: List of task names (default: memorization tasks)
            output_dir: Output directory for generated files
            seed: Random seed for reproducibility
            format: Output format ("csv" or "json")
            years: List of years to generate data for (default: 2025-2095 step 10)
        """
        # Use memorization-specific tasks by default
        tasks = tasks or MEMORIZATION_TASKS
        super().__init__(
            samples_per_task=samples_per_task,
            languages=languages,
            tasks=tasks,
            output_dir=output_dir,
            seed=seed,
            format=format,
        )
        self.years = years or MEMORIZATION_YEARS
    
    @property
    def experiment_name(self) -> str:
        return "memorization"
    
    def generate(self) -> int:
        """Generate the memorization dataset.
        
        Returns:
            Total number of samples generated
        """
        self._reset_seed()
        total_samples = 0
        output_path = self._get_output_path()
        
        for year in self.years:
            # Create config with shifted year range
            # Each year spans just that year (e.g., 2025-01-01 to 2025-12-31)
            config = MEDIUM_TIMEFRAME.with_year_range(year, year)
            
            for language in self.languages:
                # Reset seed for each language to ensure reproducibility
                self._reset_seed()
                
                for task_name in self.tasks:
                    samples = self._generate_task_dataset(
                        task_name=task_name,
                        config=config,
                        language=language,
                        output_path=output_path,
                        prefix=str(year),  # Prefix filename with year
                    )
                    total_samples += samples
        
        return total_samples
    
    def get_total_expected_samples(self) -> int:
        """Calculate expected samples: tasks × samples × languages × years."""
        return len(self.tasks) * self.samples_per_task * len(self.languages) * len(self.years)
