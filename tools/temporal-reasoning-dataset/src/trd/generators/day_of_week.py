"""Day of week generator for weekday identification tasks."""

import random
from datetime import datetime, timedelta
from typing import Dict

from trd.generators.base import BaseGenerator
from trd.utils.locale import get_day_name


class DayOfWeekGenerator(BaseGenerator):
    """Generator for day of week tasks.
    
    Example: "What day of the week (e.g., Monday, Tuesday, ...) is 2025-09-22?"
    
    This is a memorization task that depends on calendar knowledge.
    """
    
    @property
    def template_key(self) -> str:
        return "day_of_week"
    
    @property
    def task_name(self) -> str:
        return "day_of_week"
    
    def generate_data(self) -> Dict[str, str]:
        """Generate data for a day of week problem.
        
        Returns:
            Dictionary with date and answer (day name in the target language)
        """
        start_date = datetime(*self.config.start_date)
        end_date = datetime(*self.config.end_date)
        
        # Generate random date within range
        days_range = (end_date - start_date).days
        random_date = start_date + timedelta(days=random.randint(0, days_range))
        
        # Get the day name in the target language
        day_name = get_day_name(random_date, self.language)
        
        return {
            "date": random_date.strftime("%Y-%m-%d"),
            "answer": day_name,
        }
