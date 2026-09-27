"""Date arithmetic generators (addition and subtraction)."""

import random
from datetime import datetime, timedelta
from typing import Dict

from trd.generators.base import BaseGenerator
from trd.templates.plurals import get_day_form


class DateAdditionGenerator(BaseGenerator):
    """Generator for date addition tasks.
    
    Example: "Today is 2025-08-26, what is the date going to be in 10 days?"
    """
    
    @property
    def template_key(self) -> str:
        return "addition_date"
    
    @property
    def task_name(self) -> str:
        return "date_addition"
    
    def generate_data(self) -> Dict[str, str]:
        """Generate data for a date addition problem.
        
        Returns:
            Dictionary with current_date, days_to_add, day_or_days, and answer
        """
        start_date = datetime(*self.config.start_date)
        end_date = datetime(*self.config.end_date)
        
        # Generate random current date within range
        days_range = (end_date - start_date).days
        current_date = start_date + timedelta(days=random.randint(0, days_range))
        
        # Generate random days to add within configured range
        days_to_add = random.randint(self.config.days_min, self.config.days_max)
        
        # Calculate future date
        future_date = current_date + timedelta(days=days_to_add)
        
        return {
            "current_date": current_date.strftime("%Y-%m-%d"),
            "days_to_add": days_to_add,
            "day_or_days": get_day_form(days_to_add, self.language),
            "answer": future_date.strftime("%Y-%m-%d"),
        }


class DateSubtractionGenerator(BaseGenerator):
    """Generator for date subtraction tasks.
    
    Example: "Today is 2025-08-26, what was the date 10 days ago?"
    """
    
    @property
    def template_key(self) -> str:
        return "subtraction_date"
    
    @property
    def task_name(self) -> str:
        return "date_subtraction"
    
    def generate_data(self) -> Dict[str, str]:
        """Generate data for a date subtraction problem.
        
        Returns:
            Dictionary with current_date, days_to_subtract, day_or_days, and answer
        """
        start_date = datetime(*self.config.start_date)
        end_date = datetime(*self.config.end_date)
        
        # Generate random current date within range
        days_range = (end_date - start_date).days
        current_date = start_date + timedelta(days=random.randint(0, days_range))
        
        # Generate random days to subtract within configured range
        days_to_subtract = random.randint(self.config.days_min, self.config.days_max)
        
        # Calculate past date
        past_date = current_date - timedelta(days=days_to_subtract)
        
        return {
            "current_date": current_date.strftime("%Y-%m-%d"),
            "days_to_subtract": days_to_subtract,
            "day_or_days": get_day_form(days_to_subtract, self.language),
            "answer": past_date.strftime("%Y-%m-%d"),
        }
