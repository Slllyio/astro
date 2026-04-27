
import random
import datetime
import math
from typing import Dict, Any, List
from engine.models import ChartData, PlanetPosition, HouseData
from astrology.interface import AstrologyService
from astrology.bav_rules import BAVCalculator
from config import PLANETS, KAKSHYA_ZONES_PER_RASHI, KAKSHYA_DEGREES

class MockAstrologyService(AstrologyService):
    def __init__(self):
        # 12 Oct 1989 Approximate Positions (Sidereal/Lahiri)
        # Sourced from general ephemeris knowledge to match the user's chart.
        # These are used to seed the BAV Calculator.
        
        # Positions in degrees (0-360)
        # Aries=0-30, Taurus=30-60, ...
        # Sun in Virgo (~175)
        # Moon in Aquarius (to match typical charts? Or is it Pisces?) 
        # User image: Moon gives 4 pts to Aries.
        
        # Let's use the positions that are likely for Oct 12 1989.
        self.base_planet_positions = {
            "Sun": 175.0,     # Virgo (6)
            "Moon": 310.0,    # Aquarius (11)
            "Mars": 195.0,    # Libra (7)
            "Mercury": 170.0, # Virgo (6)
            "Jupiter": 75.0,  # Gemini (3)
            "Venus": 225.0,   # Scorpio (8)
            "Saturn": 255.0   # Sagittarius (9)
        }

    def calculate_chart(self, dt: datetime.datetime, location: Dict[str, Any]) -> ChartData:
        # 1. Calculate Lagna (Ascendant)
        utc_timestamp = dt.timestamp()
        hours_since_midnight_utc = (utc_timestamp % 86400) / 3600
        lon_offset = location['lon'] / 15.0
        
        # Rotational logic
        lagna_deg = ((hours_since_midnight_utc + lon_offset) * 15.0 + 180) % 360
        lagna_rashi_idx = int(lagna_deg / 30) + 1 # 1-12
        
        # 2. Update Moon Position (Transit)
        moon_movement = (hours_since_midnight_utc / 24.0) * 13.2
        current_moon_deg = (self.base_planet_positions["Moon"] + moon_movement) % 360
        moon_rashi = int(current_moon_deg / 30) + 1
        
        # 3. Prepare Positions for BAV Rules
        # We need specific positions for this chart (Rashi IDs)
        # Note: BAV Rules work on Rashi Index (1-12).
        current_positions = {}
        
        # Planets
        for p, deg in self.base_planet_positions.items():
            if p == "Moon":
                current_positions[p] = moon_rashi
            else:
                current_positions[p] = int(deg / 30) + 1
                
        # Lagna
        current_positions["Lagna"] = lagna_rashi_idx
        
        # 4. Generate BAV/SAV using REAL RULES ENGINE
        sav_data = BAVCalculator.calculate_sarvashtakavarga(current_positions)
        
        # 5. Build Planet Objects
        planets = {}
        for p_name, base_deg in self.base_planet_positions.items():
            deg = base_deg
            if p_name == "Moon":
                deg = current_moon_deg
            
            rashi = int(deg / 30) + 1
            rem_deg = deg % 30
            nakshatra = int(deg / 13.333333) + 1
            pada = int((deg % 13.333333) / 3.333333) + 1
            kakshya = int(rem_deg / KAKSHYA_DEGREES) + 1
            
            planets[p_name] = PlanetPosition(
                name=p_name,
                longitude=deg,
                speed=1.0 if p_name == "Moon" else 0.1,
                rashi=rashi,
                nakshatra=nakshatra,
                pada=pada,
                kakshya=kakshya
            )
            
        # 6. Map Houses
        houses = {}
        for h_num in range(1, 13):
            # House 1 = Lagna Rashi
            # If Lagna is 1 (Aries), House 1 is 1.
            target_rashi_id = (lagna_rashi_idx + (h_num - 1) - 1) % 12 + 1
            
            # Extract calculated data for this Rashi
            r_data = sav_data[target_rashi_id]
            
            houses[h_num] = HouseData(
                house_num=h_num,
                rashi_id=target_rashi_id,
                sav_score=r_data["total"],
                bav_scores=r_data["breakdown"]
            )
            
        return ChartData(
            timestamp=utc_timestamp,
            location_name=location['name'],
            lat=location['lat'],
            lon=location['lon'],
            ascendant=lagna_deg,
            planets=planets,
            houses=houses
        )
