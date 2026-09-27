"""Duration generators (date and time)."""

import random
from datetime import datetime, timedelta
from typing import Dict

from trd.generators.base import BaseGenerator


class DateDurationGenerator(BaseGenerator):
    """Generator for date duration tasks.
    
    Example: "How many day(s) have passed between 2025-03-20 and 2025-03-29?"
    """
    
    @property
    def template_key(self) -> str:
        return "duration_date"
    
    @property
    def task_name(self) -> str:
        return "date_duration"
    
    def generate_data(self) -> Dict[str, str]:
        """Generate data for a date duration problem.
        
        Returns:
            Dictionary with start_date, end_date, and answer (number of days)
        """
        start_date = datetime(*self.config.start_date)
        end_date = datetime(*self.config.end_date)
        
        # Generate random end date within range
        days_range = (end_date - start_date).days
        random_end_date = start_date + timedelta(days=random.randint(0, days_range))
        
        # Generate duration within configured range
        duration = random.randint(self.config.duration_date_min, self.config.duration_date_max)
        
        # Calculate start date by going back from end date
        random_start_date = random_end_date - timedelta(days=duration)
        
        return {
            "start_date": random_start_date.strftime("%Y-%m-%d"),
            "end_date": random_end_date.strftime("%Y-%m-%d"),
            "answer": str(duration),
        }


class TimeDurationGenerator(BaseGenerator):
    """Generator for time duration tasks.
    
    Example: "If I looked at the clock at 13:32 and now it is 14:21, how many minutes have gone by?"
    """
    
    @property
    def template_key(self) -> str:
        return "duration_time"
    
    @property
    def task_name(self) -> str:
        return "time_duration"
    
    def generate_data(self) -> Dict[str, str]:
        """Generate data for a time duration problem.
        
        Returns:
            Dictionary with start_time, end_time, and answer (number of minutes)
        """
        # Generate random start time
        start_time = datetime.strptime(
            f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}", "%H:%M"
        )
        
        # Generate duration within configured range
        duration_minutes = random.randint(
            self.config.duration_time_min, self.config.duration_time_max
        )
        
        # Calculate end time
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        return {
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M"),
            "answer": str(duration_minutes),
        }
