"""Time arithmetic generators (addition and subtraction)."""

import random
from datetime import datetime, timedelta
from typing import Dict

from trd.generators.base import BaseGenerator
from trd.templates.plurals import get_hour_form, get_minute_form


class TimeAdditionGenerator(BaseGenerator):
    """Generator for time addition tasks.
    
    Example: "It is now 19:29, what will the time be in 1 hour and 26 minutes?"
    """
    
    @property
    def template_key(self) -> str:
        return "addition_time"
    
    @property
    def task_name(self) -> str:
        return "time_addition"
    
    def generate_data(self) -> Dict[str, str]:
        """Generate data for a time addition problem.
        
        Returns:
            Dictionary with current_time, hours_to_add, minutes_to_add, 
            hour_or_hours, minute_or_minutes, and answer
        """
        # Generate random current time
        current_time = datetime.strptime(
            f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}", "%H:%M"
        )
        
        # Generate random hours and minutes to add within configured range
        hours_to_add = random.randint(0, self.config.hours_max)
        minutes_to_add = random.randint(0, 59)
        
        # Calculate future time
        future_time = current_time + timedelta(hours=hours_to_add, minutes=minutes_to_add)
        
        return {
            "current_time": current_time.strftime("%H:%M"),
            "hours_to_add": hours_to_add,
            "minutes_to_add": minutes_to_add,
            "hour_or_hours": get_hour_form(hours_to_add, self.language),
            "minute_or_minutes": get_minute_form(minutes_to_add, self.language),
            "answer": future_time.strftime("%H:%M"),
        }


class TimeSubtractionGenerator(BaseGenerator):
    """Generator for time subtraction tasks.
    
    Example: "It is now 19:29, what was the time 3 hours and 15 minutes ago?"
    """
    
    @property
    def template_key(self) -> str:
        return "subtraction_time"
    
    @property
    def task_name(self) -> str:
        return "time_subtraction"
    
    def generate_data(self) -> Dict[str, str]:
        """Generate data for a time subtraction problem.
        
        Returns:
            Dictionary with current_time, hours_to_subtract, minutes_to_subtract,
            hour_or_hours, minute_or_minutes, and answer
        """
        # Generate random current time
        current_time = datetime.strptime(
            f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}", "%H:%M"
        )
        
        # Generate random hours and minutes to subtract within configured range
        hours_to_subtract = random.randint(0, self.config.hours_max)
        minutes_to_subtract = random.randint(0, 59)
        
        # Calculate past time
        past_time = current_time - timedelta(hours=hours_to_subtract, minutes=minutes_to_subtract)
        
        return {
            "current_time": current_time.strftime("%H:%M"),
            "hours_to_subtract": hours_to_subtract,
            "minutes_to_subtract": minutes_to_subtract,
            "hour_or_hours": get_hour_form(hours_to_subtract, self.language),
            "minute_or_minutes": get_minute_form(minutes_to_subtract, self.language),
            "answer": past_time.strftime("%H:%M"),
        }
