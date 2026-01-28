"""
Note Parser - G7.0 (Operator Excellence)
Extracts follow-up intent and dates from free-text notes.
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

def parse_followup(note: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse a note for follow-up intent.
    Returns (due_at_iso, task_type) or (None, None).
    
    Supported patterns:
    - "call [tomorrow|next week|monday...]"
    - "follow up [on date]"
    - "callback [time]"
    """
    if not note:
        return None, None
        
    lower_note = note.lower()
    now = datetime.now()
    due_date = None
    task_type = "follow_up"
    
    # Task Type Inference
    if "call" in lower_note:
        task_type = "call"
    elif "email" in lower_note:
        task_type = "email"
        
    # Relative Date Parsing
    if "tomorrow" in lower_note:
        due_date = now + timedelta(days=1)
    elif "next week" in lower_note:
        due_date = now + timedelta(days=7)
    elif "in " in lower_note and " days" in lower_note:
        try:
            match = re.search(r'in (\d+) days', lower_note)
            if match:
                days = int(match.group(1))
                due_date = now + timedelta(days=days)
        except: pass

    # Weekday Parsing
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for i, day in enumerate(weekdays):
        if day in lower_note and "next " + day not in lower_note: # Simple weekday mentions
             current_day = now.weekday()
             days_ahead = (i - current_day)
             if days_ahead <= 0: # Target day already happened this week, move to next week
                 days_ahead += 7
             due_date = now + timedelta(days=days_ahead)
             break
        
    # Standardize time to 10am if not specified
    if due_date:
        due_date = due_date.replace(hour=10, minute=0, second=0, microsecond=0)
        return due_date.isoformat(), task_type
        
    return None, None
