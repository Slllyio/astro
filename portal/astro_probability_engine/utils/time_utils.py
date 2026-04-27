
import datetime
from typing import List
from config import TIME_SLICES, TIME_INTERVAL_MINUTES

def generate_time_slices(dob_date: datetime.date) -> List[datetime.datetime]:
    """Generates 96 time slices for the given date starting at 00:00."""
    start_dt = datetime.datetime.combine(dob_date, datetime.time.min)
    slices = []
    for i in range(TIME_SLICES):
        delta = datetime.timedelta(minutes=i * TIME_INTERVAL_MINUTES)
        slices.append(start_dt + delta)
    return slices
