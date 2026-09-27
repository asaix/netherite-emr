"""Interval generator for week boundary tasks."""

import random
from datetime import datetime, timedelta
from typing import Dict

from trd.generators.base import BaseGenerator


class IntervalGenerator(BaseGenerator):
    """Generator for interval date tasks.
    
    Example: "If today is 2025-08-14, what are the dates for the start and 
              end of next week, assuming Monday is the first day of the week?"
    """
    
    @property
    def template_key(self) -> str:
        return "interval_date"
    
    @property
    def task_name(self) -> str:
        return "interval_date"
    
    def generate_data(self) -> Dict[str, str]:
        """Generate data for an interval date problem.
        
        Returns:
            Dictionary with current_date and answer (week start to end dates)
        """
        start_date = datetime(*self.config.start_date)
        end_date = datetime(*self.config.end_date)
        
        # Generate random current date within range
        days_range = (end_date - start_date).days
        current_date = start_date + timedelta(days=random.randint(0, days_range))
        
        # Calculate next week boundaries
        # Move to next week first (add 7 days)
        next_week_date = current_date + timedelta(days=7)
        
        # Get the boundaries of that week (Monday to Sunday)
        next_week_start, next_week_end = self._get_week_boundaries(next_week_date)
        
        return {
            "current_date": current_date.strftime("%Y-%m-%d"),
            "answer": f"{next_week_start.strftime('%Y-%m-%d')} to {next_week_end.strftime('%Y-%m-%d')}",
        }
    
    @staticmethod
    def _get_week_boundaries(reference_date: datetime) -> tuple:
        """Get the start and end dates of the week containing the reference date.
        
        Monday is considered the first day of the week (weekday() = 0).
        
        Args:
            reference_date: The reference date
            
        Returns:
            Tuple of (start_of_week, end_of_week) as datetime objects
        """
        # Get Monday of the week (weekday() returns 0 for Monday)
        start_of_week = reference_date - timedelta(days=reference_date.weekday())
        
        # Get Sunday (6 days after Monday)
        end_of_week = start_of_week + timedelta(days=6)
        
        return start_of_week, end_of_week
