
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class PlanetPosition:
    name: str
    longitude: float  # 0-360 degrees
    speed: float # Daily motion
    rashi: int # 1-12
    nakshatra: int # 1-27
    pada: int # 1-4
    kakshya: int # 1-8
    kakshya_ruler: str # Ruler of the 3.75 deg segment

@dataclass
class HouseData:
    house_num: int
    rashi_id: int # 1-12 (Aries=1)
    bav_scores: Dict[str, int] # Planet name -> bindu count
    sav_score: int
    shodhita_score: int = 0 # Phase 3: Reduced score
    fixed_sav: int = 0
    fixed_shodhita: int = 0
    shodhya_pinda: Optional[float] = 0.0 # Calculated later

@dataclass
class ChartData:
    timestamp: float # Unix timestamp
    location_name: str
    lat: float
    lon: float
    ascendant: float # Lagna longitude
    planets: Dict[str, PlanetPosition]
    houses:  Dict[int, HouseData] # 1-12 -> HouseData

@dataclass
class MatrixEntry:
    time_slice_index: int
    location_index: int
    chart: ChartData
