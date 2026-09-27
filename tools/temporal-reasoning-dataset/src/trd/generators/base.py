"""Base generator class for temporal reasoning tasks."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

from trd.config.timeframes import TimeframeConfig
from trd.templates.questions import get_question_template


@dataclass
class Sample:
    """A single sample from the dataset.
    
    Attributes:
        question: The question text
        answer: The answer text
        task: Task name (e.g., "date_addition")
        language: Language code (e.g., "en_US")
        difficulty: Difficulty level (e.g., "medium")
        metadata: Optional additional metadata
    """
    question: str
    answer: str
    task: str = ""
    language: str = ""
    difficulty: str = ""
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert sample to dictionary."""
        return {
            "question": self.question,
            "answer": self.answer,
        }
    
    def to_row(self) -> tuple:
        """Convert sample to CSV row tuple."""
        return (self.question, self.answer)


class BaseGenerator(ABC):
    """Abstract base class for temporal reasoning sample generators.
    
    Subclasses must implement:
    - generate_data(): Generate the raw data for a single sample
    - template_key: Property that returns the template key for this task
    - task_name: Property that returns the task name
    """
    
    def __init__(
        self,
        config: TimeframeConfig,
        language: str = "en_US",
    ):
        """Initialize the generator.
        
        Args:
            config: Timeframe configuration with difficulty parameters
            language: Language code for question templates
        """
        self.config = config
        self.language = language
        self._template = get_question_template(language, self.template_key)
    
    @property
    @abstractmethod
    def template_key(self) -> str:
        """Return the template key for this task (e.g., 'addition_date')."""
        pass
    
    @property
    @abstractmethod
    def task_name(self) -> str:
        """Return the task name (e.g., 'date_addition')."""
        pass
    
    @abstractmethod
    def generate_data(self) -> Dict[str, str]:
        """Generate the raw data for a single sample.
        
        Returns:
            Dictionary with template parameters and 'answer' key
        """
        pass
    
    def generate_sample(self) -> Sample:
        """Generate a single sample.
        
        Returns:
            Sample with question and answer
        """
        data = self.generate_data()
        question = self._template.format(**data)
        answer = data["answer"]
        
        return Sample(
            question=question,
            answer=answer,
            task=self.task_name,
            language=self.language,
            difficulty=self.config.name,
        )
    
    def generate_samples(self, num_samples: int) -> List[Sample]:
        """Generate multiple samples.
        
        Args:
            num_samples: Number of samples to generate
            
        Returns:
            List of Sample objects
        """
        return [self.generate_sample() for _ in range(num_samples)]
    
    def generate_dataset(self, num_samples: int) -> List[tuple]:
        """Generate a dataset as list of (question, answer) tuples.
        
        This format is suitable for CSV export with a header row.
        
        Args:
            num_samples: Number of samples to generate
            
        Returns:
            List with header tuple followed by sample tuples
        """
        samples = self.generate_samples(num_samples)
        rows = [("question", "answer")]  # Header
        rows.extend([sample.to_row() for sample in samples])
        return rows
