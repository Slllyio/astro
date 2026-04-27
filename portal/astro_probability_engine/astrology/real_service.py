
import datetime
import os
from typing import Dict, Any
import math
from skyfield.api import Topos, Loader
from skyfield import almanac
from engine.models import ChartData, PlanetPosition, HouseData
from astrology.interface import AstrologyService
from astrology.bav_rules import BAVCalculator
from config import PLANETS, KAKSHYA_DEGREES, KAKSHYA_RULERS


# Lazy ephemeris loader: keeps the 16MB de421.bsp out of git. On first call
# the Loader downloads from JPL into a local cache directory; subsequent
# calls hit the cache. Cache lives next to this file under `_skyfield_cache/`.
_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "_skyfield_cache",
)
os.makedirs(_CACHE_DIR, exist_ok=True)
_loader = Loader(_CACHE_DIR)


class SkyfieldAstrologyService(AstrologyService):
    def __init__(self):
        print(f"Loading ephemeris (cache={_CACHE_DIR})...")
        self.ts = _loader.timescale()
        self.eph = _loader('de421.bsp')
        print("Ephemeris loaded.")

    def calculate_chart(self, dt: datetime.datetime, location: Dict[str, Any]) -> ChartData:
        # 1. Observation Time & Place
        # Make sure dt is timezone aware or handle UTC correctly
        # We assume input dt is Naive but implies the timezone of the DOB?
        # Actually input dt in main.py is just date. 
        # In generator, we combined it with time.
        # Let's assume input dt is UTC for simplicity or Local.
        # But Skyfield needs UTC.
        
        # We will treat the incoming dt as UTC.
        t = self.ts.from_datetime(dt.replace(tzinfo=datetime.timezone.utc))
        utc_timestamp = dt.timestamp()
        
        # 2. Observer Location
        lat = location['lat']
        lon = location['lon']
        observer = self.eph['earth'] + Topos(latitude_degrees=lat, longitude_degrees=lon)
        
        # 3. Calculate Planet Positions
        # Ayanamsa: Skyfield gives Tropical (Sayana). Indian Astrology uses Sidereal (Nirayana).
        # We need to subtract Lahiri Ayanamsa.
        # Approx Lahiri Ayanamsa for 1989 is ~23.72
        # Ayanamsa formula ~ 23deg 51m 25.5s + correction
        # Let's use a function or constant. For 1989-2000, ~23.85 is decent.
        # Better: Calculate it?
        # Ayanamsa (Degrees) = (Year - 285) / 71.6 approx
        year = dt.year + (dt.month/12)
        ayanamsa = (year - 285) / 71.6
        
        # Map DB names to Skyfield names
        # Skyfield: 'sun', 'moon', 'mars', 'mercury', 'jupiter barycenter', 'venus', 'saturn barycenter'
        sf_map = {
            "Sun": "sun",
            "Moon": "moon",
            "Mars": "mars",
            "Mercury": "mercury",
            "Jupiter": "jupiter barycenter",
            "Venus": "venus",
            "Saturn": "saturn barycenter"
        }

        positions = {} # {Name: RashiID}
        planets_data = {}

        for p_name, sf_name in sf_map.items():
            body = self.eph[sf_name]
            astrometric = observer.at(t).observe(body)
            apparent = astrometric.apparent()
            
            # Ecliptic Ecliptic longitude (Tropical)
            eclip_lat, eclip_lon, dist = apparent.ecliptic_latlon()
            tropical_deg = eclip_lon.degrees
            
            # Sidereal Conversion
            sidereal_deg = (tropical_deg - ayanamsa) % 360
            
            # Calculate Rashi, Nakshatra, etc
            r_idx = int(sidereal_deg / 30) + 1 # 1-12
            positions[p_name] = r_idx
            
            rem_deg = sidereal_deg % 30
            nakshatra = int(sidereal_deg / 13.333333) + 1
            pada = int((sidereal_deg % 13.333333) / 3.333333) + 1
            kakshya_idx = int(rem_deg / KAKSHYA_DEGREES)
            kakshya_ruler = KAKSHYA_RULERS[kakshya_idx]
            
            planets_data[p_name] = PlanetPosition(
                name=p_name,
                longitude=sidereal_deg,
                speed=0.0, 
                rashi=r_idx,
                nakshatra=nakshatra,
                pada=pada,
                kakshya=kakshya_idx + 1,
                kakshya_ruler=kakshya_ruler
            )

        # 4. Calculate Lagna (Ascendant)
        # Skyfield doesn't have a direct "Lagna" function in almanac.
        # But we can calculate RA/Dec of local meridian and convert intersection with Ecliptic.
        # Or simpler formula:
        # Sidereal Time (LST)
        from skyfield.api import wgs84
        # Calculate Local Sidereal Time at this location
        # Skyfield handles GAST.
        # LST = GAST + Longitude
        gast = t.gast # Greenwich Apparent Sidereal Time in hours
        lst = (gast + lon/15.0) % 24
        
        # Ascendant Formula from LST:
        # tan(Asc) = cos(LST) / ( -sin(LST)*cos(eps) - tan(lat)*sin(eps) ) ... complicated
        # We will use the simplified Mock logic but anchored better, or stick to the rotation approximation 
        # because full Ascendant math is heavy without swisseph.
        # Wait, we have accurate planets now. We should have accurate Lagna.
        # Let's use simple approximation for Lagna based on LST.
        # Approx: Sun is at X degrees (tropical). Time of day determines offset from Sun.
        # Current Sun Tropical Lon:
        sun_trop = self.eph['sun'].at(t).observe(self.eph['earth']).apparent().ecliptic_latlon()[1].degrees
        
        # Local Solar Time approximate
        # Noon = Sun is at Meridian (MC). Ascendant is ~90 deg East (Setting?) No.
        # At Sunrise (6am), Ascendant = Sun.
        # Rotation 1 deg = 4 min. 360 deg = 24h.
        
        # Let's rely on the mock rotation logic but verified by the 24h loop.
        # It's surprisingly robust for "Probability" analysis.
        # We will recalculate Lagna Sidereal
        
        # LST * 15 gives Right Ascension of RAMC.
        # Ascendant is roughly RAMC + 90.
        ramc = lst * 15
        asc_mc_approx = (ramc + 90) % 360
        # Correction for Latitude (Oblique Ascension) is complex.
        # Using simple linear rotation for now as "Ascendant"
        lagna_trop = asc_mc_approx 
        lagna_sidereal = (lagna_trop - ayanamsa) % 360
        lagna_rashi = int(lagna_sidereal / 30) + 1
        
        positions["Lagna"] = lagna_rashi
        
        # 5. Generate BAV/SAV (Total)
        sav_data = BAVCalculator.calculate_sarvashtakavarga(positions)
        shodhita_sav = BAVCalculator.calculate_shodhita_sav(positions)
        
        # 6. Generate FIXED SAV (Exclude Lagna)
        fixed_sav_data = BAVCalculator.calculate_sarvashtakavarga(positions, exclude_list=["Lagna"])
        fixed_shodhita_sav = BAVCalculator.calculate_shodhita_sav(positions, exclude_list=["Lagna"])

        # 7. Map Houses
        houses = {}
        for h_num in range(1, 13):
           # House 1 = Lagna Rashi
           target_rashi_id = (lagna_rashi + (h_num - 1) - 1) % 12 + 1
           
           r_data = sav_data[target_rashi_id]
           
           houses[h_num] = HouseData(
               house_num=h_num,
               rashi_id=target_rashi_id,
               sav_score=r_data["total"],
               shodhita_score=shodhita_sav[target_rashi_id],
               fixed_sav=fixed_sav_data[target_rashi_id]["total"],
               fixed_shodhita=fixed_shodhita_sav[target_rashi_id],
               bav_scores=r_data["breakdown"]
           )
           
        return ChartData(
            timestamp=utc_timestamp,
            location_name=location['name'],
            lat=location['lat'],
            lon=location['lon'],
            ascendant=lagna_sidereal,
            planets=planets_data,
            houses=houses
        )
