"""Recurrence generator for recurring event tasks."""

import random
from datetime import datetime, timedelta
from typing import Dict

from trd.generators.base import BaseGenerator
from trd.templates.plurals import get_day_form


class RecurrenceGenerator(BaseGenerator):
    """Generator for recurrence date tasks.
    
    Example: "Today is 2025-02-23, and I have a recurrence every 7 days. 
              Without counting today, what is the date of the 2nd occurrence?"
    """
    
    @property
    def template_key(self) -> str:
        return "recurrence_date"
    
    @property
    def task_name(self) -> str:
        return "date_recurrence"
    
    def generate_data(self) -> Dict[str, str]:
        """Generate data for a recurrence date problem.
        
        Returns:
            Dictionary with current_date, recurrence_days, day_or_days, 
            occurrence, and answer
        """
        start_date = datetime(*self.config.start_date)
        end_date = datetime(*self.config.end_date)
        
        # Generate random current date within range
        days_range = (end_date - start_date).days
        current_date = start_date + timedelta(days=random.randint(0, days_range))
        
        # Generate random recurrence interval within configured range
        recurrence_days = random.randint(
            self.config.recurrence_every_min, self.config.recurrence_every_max
        )
        
        # Generate random occurrence number within configured range
        occurrence = random.randint(
            self.config.recurrence_question_min, self.config.recurrence_question_max
        )
        
        # Calculate the date of the nth occurrence
        # The nth occurrence is n * recurrence_days from the current date
        answer_date = current_date + timedelta(days=occurrence * recurrence_days)
        
        return {
            "current_date": current_date.strftime("%Y-%m-%d"),
            "recurrence_days": recurrence_days,
            "day_or_days": get_day_form(recurrence_days, self.language),
            "occurrence": occurrence,
            "answer": answer_date.strftime("%Y-%m-%d"),
        }
