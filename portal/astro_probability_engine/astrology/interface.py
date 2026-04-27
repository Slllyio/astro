
from abc import ABC, abstractmethod
from typing import Dict, Any
from engine.models import ChartData
import datetime

class AstrologyService(ABC):
    
    @abstractmethod
    def calculate_chart(self, dt: datetime.datetime, location: Dict[str, Any]) -> ChartData:
        pass
