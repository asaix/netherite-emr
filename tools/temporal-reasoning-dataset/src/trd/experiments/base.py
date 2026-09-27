"""Base experiment class for dataset generation."""

import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

from trd.config.defaults import (
    ALL_TASKS,
    NUMBER_OF_SAMPLES_DEFAULT,
    RANDOM_SEED,
)
from trd.config.languages import LANGUAGE_CODES
from trd.config.timeframes import MEDIUM_TIMEFRAME, TimeframeConfig
from trd.generators import GENERATOR_MAP
from trd.utils.io import save_dataset


class BaseExperiment(ABC):
    """Abstract base class for experiments.
    
    Subclasses must implement:
    - generate(): Generate the complete dataset for this experiment
    - experiment_name: Property that returns the experiment name
    """
    
    def __init__(
        self,
        samples_per_task: int = NUMBER_OF_SAMPLES_DEFAULT,
        languages: Optional[List[str]] = None,
        tasks: Optional[List[str]] = None,
        output_dir: Union[str, Path] = "./output",
        seed: int = RANDOM_SEED,
        format: str = "csv",
    ):
        """Initialize the experiment.
        
        Args:
            samples_per_task: Number of samples per task per language
            languages: List of language codes (default: all supported)
            tasks: List of task names (default: all tasks)
            output_dir: Output directory for generated files
            seed: Random seed for reproducibility
            format: Output format ("csv" or "json")
        """
        self.samples_per_task = samples_per_task
        self.languages = languages or LANGUAGE_CODES
        self.tasks = tasks or ALL_TASKS
        self.output_dir = Path(output_dir)
        self.seed = seed
        self.format = format
    
    @property
    @abstractmethod
    def experiment_name(self) -> str:
        """Return the experiment name (e.g., 'variations')."""
        pass
    
    @abstractmethod
    def generate(self) -> int:
        """Generate the complete dataset for this experiment.
        
        Returns:
            Total number of samples generated
        """
        pass
    
    def _get_output_path(self, subdir: str = "") -> Path:
        """Get the output path for this experiment.
        
        Args:
            subdir: Optional subdirectory
            
        Returns:
            Path to output directory
        """
        path = self.output_dir / self.experiment_name
        if subdir:
            path = path / subdir
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def _generate_task_dataset(
        self,
        task_name: str,
        config: TimeframeConfig,
        language: str,
        output_path: Path,
        prefix: str = "",
    ) -> int:
        """Generate dataset for a single task.
        
        Args:
            task_name: Name of the task
            config: Timeframe configuration
            language: Language code
            output_path: Output directory
            prefix: Optional filename prefix
            
        Returns:
            Number of samples generated
        """
        generator_class = GENERATOR_MAP[task_name]
        generator = generator_class(config, language)
        data = generator.generate_dataset(self.samples_per_task)
        
        save_dataset(
            data=data,
            output_dir=output_path,
            task_name=task_name,
            difficulty=config.name,
            language=language,
            prefix=prefix,
            format=self.format,
        )
        
        return self.samples_per_task
    
    def _reset_seed(self) -> None:
        """Reset random seed for reproducibility."""
        random.seed(self.seed)
    
    def get_total_expected_samples(self) -> int:
        """Calculate the total expected number of samples.
        
        This method should be overridden by subclasses if the calculation
        differs from the default.
        
        Returns:
            Expected total number of samples
        """
        return len(self.tasks) * len(self.languages) * self.samples_per_task
