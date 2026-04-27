import math
import statistics
from typing import List, Dict, Any
from engine.models import MatrixEntry, ChartData
from engine.interpreter import AstrologicalInterpreter

class MatrixAnalyzer:
    def __init__(self):
        self.interpreter = AstrologicalInterpreter()

    def calculate_ascendant_scenarios(self, matrix: list) -> List[Dict[str, Any]]:
        """
        Calculates the best time window and max score for EVERY Ascendant (1-12).
        Uses Reference Location (Index 0) for Time Label to keep it simple.
        """
        scenarios = {} # RashiID -> {score, time, asc}
        
        # Filter for Reference Location (Index 0) to get specific timings
        ref_entries = [e for e in matrix if e.location_index == 0]
        
        # Initialize with None
        for i in range(1, 13):
            scenarios[i] = {"score": -1, "time": "N/A", "ascendant": i}
            
        for entry in ref_entries:
            # Calculate Functional Strength: Sum of Kendras (1,4,7,10) & Trikonas (5,9)
            # This shows how strong the pillars of life are for this Ascendant.
            # Houses are 1-indexed in our model keys.
            power_houses = [1, 4, 5, 7, 9, 10]
            power_score = sum(entry.chart.houses[h_idx].sav_score for h_idx in power_houses)
            
            ascendant = entry.chart.houses[1].rashi_id
            
            # Derive Time
            total_minutes = entry.time_slice_index * 15
            hours = total_minutes // 60
            minutes = total_minutes % 60
            time_label = f"{hours:02d}:{minutes:02d}"
            
            # Record if better than existing for this Ascendant
            # Or just first occurance? Usually scores don't change much effectively for SAME ascendant same day.
            # But let's take MAX score.
            if power_score > scenarios[ascendant]['score']:
                scenarios[ascendant] = {
                    "score": power_score,
                    "time": time_label,
                    "ascendant": ascendant
                }
                
        # Convert to list
        result = list(scenarios.values())
        # Filter out any that didn't appear (unlikely in 24h but possible at poles)
        result = [x for x in result if x['score'] != -1]
        
        # Sort by Score Descending
        return sorted(result, key=lambda x: x['score'], reverse=True)

    def calculate_elemental_balance(self, matrix: list) -> Dict[str, float]:
        """
        Calculates the count of planets in Fire, Earth, Air, Water signs.
        Uses the first chart as reference (since heavy planets don't change signs in 24h usually).
        """
        element_counts = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
        ELEMENTS = {
            1: "Fire", 5: "Fire", 9: "Fire",
            2: "Earth", 6: "Earth", 10: "Earth",
            3: "Air", 7: "Air", 11: "Air",
            4: "Water", 8: "Water", 12: "Water"
        }
        
        ref = matrix[0].chart.planets
        for p_name, p_data in ref.items():
            # Check planets (ignore nodes if desired, but typically included)
            # models.py says PlanetPosition has rashi (int)
            elem = ELEMENTS.get(p_data.rashi, "Unknown")
            if elem in element_counts:
                element_counts[elem] += 1
                
        return element_counts

    def calculate_directional_strength(self, matrix: list) -> Dict[str, Any]:
        """
        Calculates average SAV score for East (Fire), South (Earth), West (Air), North (Water).
        """
        directions = {
            "East (Fire)": [1, 5, 9],
            "South (Earth)": [2, 6, 10],
            "West (Air)": [3, 7, 11],
            "North (Water)": [4, 8, 12]
        }
        
        scores = {k: [] for k in directions}
        
        for entry in matrix:
            for h in entry.chart.houses.values():
                for d, rashis in directions.items():
                    if h.rashi_id in rashis:
                        scores[d].append(h.sav_score)
                        
        results = {}
        for d, vals in scores.items():
            results[d] = round(statistics.mean(vals), 1)
            
        # Find dominant
        sorted_dirs = sorted(results.items(), key=lambda x: x[1], reverse=True)
        winner = sorted_dirs[0]
        
        return {
            "scores": results,
            "winner": winner[0],
            "winner_score": winner[1]
        }

    def analyze_yogas(self, matrix: list) -> List[Dict[str, str]]:
        """
        Checks for Universal Yogas present in ALL charts.
        """
        ref = matrix[0]
        planets = ref.chart.planets
        yogas = []
        
        def get_r(p_name): return planets[p_name].rashi
        
        # 1. Budhaditya (Sun + Mercury)
        if get_r("Sun") == get_r("Mercury"):
            yogas.append({
                "name": "Budhaditya Yoga",
                "desc": "Sun and Mercury in the same sign. Enhances intellect and communication."
            })
            
        # 2. Chandra-Mangala (Moon + Mars)
        m_r = get_r("Moon")
        ma_r = get_r("Mars")
        if m_r == ma_r:
             yogas.append({
                "name": "Chandra-Mangala Yoga",
                "desc": "Moon and Mars conjoined. Earnings through enterprise."
            })
        elif abs(m_r - ma_r) == 6:
             yogas.append({
                "name": "Chandra-Mangala Yoga (Opposition)",
                "desc": "Moon and Mars in mutual aspect. High energy for financial gain."
            })
            
        # 3. Gajakesari (Moon + Jupiter) - Check Universality
        j_r = get_r("Jupiter")
        is_gaja_universal = True
        for entry in matrix:
            curr_moon_r = entry.chart.planets["Moon"].rashi
            # Distance 1, 4, 7, 10
            dist = (curr_moon_r - j_r + 12) % 12 + 1
            if dist not in [1, 4, 7, 10]:
                is_gaja_universal = False
                break
        
        if is_gaja_universal:
             yogas.append({
                "name": "Gajakesari Yoga",
                "desc": "Moon in angular relationship to Jupiter. Reputation and wisdom."
            })
            
        # 4. Saturn-Mars Link
        s_r = get_r("Saturn")
        s_aspects = [(s_r + 2) % 12 + 1, (s_r + 6) % 12 + 1, (s_r + 9) % 12 + 1] # 3, 7, 10
        m_aspects = [(ma_r + 3) % 12 + 1, (ma_r + 6) % 12 + 1, (ma_r + 7) % 12 + 1] # 4, 7, 8
        
        if ma_r in s_aspects or s_r in m_aspects:
             yogas.append({
                "name": "Saturn-Mars Mutual Influence",
                "desc": "High-intensity technical energy. Discipline meets Action."
            })
            
        return yogas

    def calculate_life_activation_windows(self, matrix: list, rashi_stats: dict, dob) -> List[Dict[str, Any]]:
        """
        Calculates when Jupiter/Saturn/Rahu transit through the 3 strongest Rashis.
        This shows "Peak Life Periods" independent of birth time.
        """
        from datetime import date, timedelta
        
        # 1. Identify Top 3 Power Zones
        sorted_rashis = sorted(rashi_stats.items(), key=lambda x: x[1]['mean_score'], reverse=True)
        power_zones = [int(r_id) for r_id, _ in sorted_rashis[:3]]
        
        # 2. Get current planetary positions from reference chart (from DOB)
        ref = matrix[0]
        current_positions = {
            "Jupiter": ref.chart.planets["Jupiter"].rashi,
            "Saturn": ref.chart.planets["Saturn"].rashi,
            "Rahu": 12  # Placeholder, will need actual Rahu position
        }
        
        # 3. Use TODAY as reference for future predictions
        today = date.today()
        
        # Calculate how many years ahead we should project from 1989 to today
        # Then project future transits from today
        years_since_dob = today.year - dob.year
        
        # Helper: Calculate when a planet enters a target Rashi from TODAY
        def calculate_entry_date(current_rashi_at_dob, target_rashi, speed_months_per_sign, start_date_dob, years_elapsed, is_retrograde=False):
            """Returns approximate future entry date from TODAY."""
            # First project where planet is TODAY
            # Full cycles from 1989 to today
            if is_retrograde:
                total_signs = (years_elapsed * 12) / speed_months_per_sign  # How many signs backward
                current_rashi_today = (current_rashi_at_dob - int(total_signs)) % 12
                if current_rashi_today == 0: current_rashi_today = 12
                distance = (current_rashi_today - target_rashi) % 12
            else:
                total_signs = (years_elapsed * 12) / speed_months_per_sign  # How many signs forward
                current_rashi_today = ((current_rashi_at_dob - 1 + int(total_signs)) % 12) + 1
                distance = (target_rashi - current_rashi_today) % 12
                
            months_away = distance * speed_months_per_sign
            entry_date_from_today = today + timedelta(days=int(months_away * 30.44))
            return entry_date_from_today
        
        transit_windows = []
        
        # Calculate for each planet and power zone
        planets_config = [
            ("Jupiter", 12, False),
            ("Saturn", 30, False),
            ("Rahu", 18, True)
        ]
        
        for planet, speed, retrograde in planets_config:
            curr_rashi = current_positions.get(planet, 1)
            
            for power_rashi in power_zones:
                entry = calculate_entry_date(curr_rashi, power_rashi, speed, dob, years_since_dob, retrograde)
                
                # Only include future dates within reasonable range (next 15 years)
                if entry.year >= today.year and entry.year <= 2040:
                    # Calculate age at entry
                    age_at_entry = entry.year - dob.year
                    
                    transit_windows.append({
                        "planet": planet,
                        "target_rashi": power_rashi,
                        "entry_date": entry.strftime("%Y-%m"),
                        "age": age_at_entry,
                        "duration_months": speed,
                        "significance": "High" if power_rashi == power_zones[0] else "Medium"
                    })
        
        # Sort by date
        transit_windows.sort(key=lambda x: x['entry_date'])
        
        # Take top 8 most significant
        return transit_windows[:8]

    def calculate_moon_phase(self, matrix: list) -> Dict[str, Any]:
        """
        Calculates Tithi and Phase.
        """
        ref = matrix[0]
        sun_long = ref.chart.planets["Sun"].longitude
        moon_long = ref.chart.planets["Moon"].longitude
        
        if moon_long < sun_long:
            moon_long += 360
            
        diff = moon_long - sun_long
        tithi_num = int(diff / 12) + 1
        
        phases = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", 
                  "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", 
                  "Trayodashi", "Chaturdashi", "Purnima/Amavasya"]
        
        paksha = "Shukla (Waxing)" if tithi_num <= 15 else "Krishna (Waning)"
        idx = (tithi_num - 1) % 15
        name = phases[idx]
        if tithi_num == 30: name = "Amavasya"
        if tithi_num == 15: name = "Purnima"
        
        return {
            "tithi": f"{name} {paksha}",
            "degrees_separation": round(diff, 1)
        }

    def analyze(self, matrix: List[MatrixEntry], dob=None) -> Dict[str, Any]:
        """
        Main analysis pipeline.
        """
        sample_count = len(matrix)
        
        # 1. House Analysis (SAV & Shodhita)
        house_stats = {}
        for h_idx in range(1, 13):
            sav_scores = [entry.chart.houses[h_idx].sav_score for entry in matrix] 
            sho_scores = [entry.chart.houses[h_idx].shodhita_score for entry in matrix]
            
            # Stability: % of charts that have the most common score
            def calc_stability(scores):
                if not scores: return 0.0
                most_common_count = scores.count(statistics.mode(scores))
                return (most_common_count / len(scores)) * 100
                
            house_stats[h_idx] = {
                "sav_mean": statistics.mean(sav_scores),
                "sav_stdev": statistics.stdev(sav_scores) if len(sav_scores) > 1 else 0,
                "sav_stability": calc_stability(sav_scores),
                "sho_mean": statistics.mean(sho_scores),
                "sho_stability": calc_stability(sho_scores)
            }

        # 2. Rashi & Planetary Power Analysis
        rashi_map = {i: [] for i in range(1, 13)}
        planet_power = {}
        
        # Calculate Planet Power from first chart (BAV contribution is constant per day usually)
        ref_chart = matrix[0].chart
        rashi_bav_breakdown = {} # rashi_id -> {p_name: score}

        for h in ref_chart.houses.values():
            rashi_bav_breakdown[h.rashi_id] = h.bav_scores
            for p_name, score in h.bav_scores.items():
                if score > 0:
                    planet_power[p_name] = planet_power.get(p_name, 0) + 1
                    
        for entry in matrix:
            for h_data in entry.chart.houses.values():
                r_id = h_data.rashi_id
                rashi_map[r_id].append(h_data.sav_score)
                
        rashi_stats = {}
        lords = {
            1: "Mars", 8: "Mars", 2: "Venus", 7: "Venus",
            3: "Mercury", 6: "Mercury", 4: "Moon", 5: "Sun",
            9: "Jupiter", 12: "Jupiter", 10: "Saturn", 11: "Saturn"
        }
        for r_id in range(1, 13):
            # FIXED scores (Universal DNA)
            fixed_sav_scores = []
            fixed_sho_scores = []
            # TOTAL scores (Daily Variance)
            total_sav_scores = []
            
            for entry in matrix:
                for h in entry.chart.houses.values():
                    if h.rashi_id == r_id:
                        fixed_sav_scores.append(h.fixed_sav)
                        fixed_sho_scores.append(h.fixed_shodhita)
                        total_sav_scores.append(h.sav_score)
            
            if fixed_sav_scores:
                mean_fixed = sum(fixed_sav_scores) / len(fixed_sav_scores)
                mean_sho = sum(fixed_sho_scores) / len(fixed_sho_scores)
                
                # Stability of FIXED scores (should be high)
                def calc_stability(scores):
                    if not scores: return 0.0
                    mode_val = statistics.mode(scores)
                    return (scores.count(mode_val) / len(scores)) * 100
                    
                stability_pct = calc_stability(fixed_sav_scores)
                
                rashi_stats[r_id] = {
                    "mean_score": mean_fixed, # Using fixed as the base "Identity"
                    "mean_shodhita": mean_sho,
                    "total_sav_mean": sum(total_sav_scores) / len(total_sav_scores),
                    "stability_pct": stability_pct,
                    "key_insights": {
                        "strength_tier": "High" if mean_fixed > 30 else "Avg" if mean_fixed > 25 else "Low",
                        "primary_driver": lords.get(r_id, "Unknown"),
                        "fixed_status": "FIXED" if stability_pct >= 70 else "VARIABLE"
                    }
                }
            
        # 3. Universal Nakshatras
        reference_entry = matrix[0]
        reference_planets = list(reference_entry.chart.planets.values()) 
        universal_nakshatras = []
        for p_idx, p_data in enumerate(reference_planets): # Note: This assumes dict order is stable or list conversion is consistent
            # Better to iterate by name
            p_name = p_data.name
            target_nak = p_data.nakshatra
            is_universal = True
            for entry in matrix:
                if entry.chart.planets[p_name].nakshatra != target_nak:
                    is_universal = False
                    break
            if is_universal:
                universal_nakshatras.append({
                    "planet": p_name,
                    "nakshatra_id": target_nak
                })
        
        
        # 4. Advanced Metrics
        ascendant_scenarios = self.calculate_ascendant_scenarios(matrix)
        element_counts = self.calculate_elemental_balance(matrix)
        directional_strength = self.calculate_directional_strength(matrix)
        yogas = self.analyze_yogas(matrix)
        tithi_info = self.calculate_moon_phase(matrix)
        
        # Life Activation Windows (requires DOB)
        life_windows = []
        if dob:
            life_windows = self.calculate_life_activation_windows(matrix, rashi_stats, dob)
        
        # Phase 2: Planetary Strength
        planetary_strength = self.calculate_planetary_strength(matrix)
        
        # Phase 3: Dasha Timeline  
        dasha_periods = []
        if dob:
            ref = matrix[0]
            moon_nak = ref.chart.planets["Moon"].nakshatra
            dasha_periods = self.calculate_vimshottari_dasha(dob, moon_nak)
                
        # 5. Narrative Generation
        narrative = self.interpreter.generate_narrative({
            "house_analysis": house_stats,
            "rashi_analysis": rashi_stats,
            "bav_breakdown": rashi_bav_breakdown,
            "planet_power": planet_power, 
            "common_links": {
                "nakshatra_positions": universal_nakshatras
            },
            "peak_times": ascendant_scenarios, # Renamed
            "elemental_balance": element_counts,
            "directional_strength": directional_strength,
            "yogas": yogas,
            "tithi_info": tithi_info,
            "life_activation_windows": life_windows,
            "planetary_strength": planetary_strength,
            "dasha_periods": dasha_periods
        })

        return {
            "sample_count": sample_count,
            "narrative": narrative,
            "yogas_debug": yogas
        }
    
    def calculate_planetary_strength(self, matrix: list) -> Dict[str, int]:
        """
        Simplified Shad Bala - calculates relative strength of each planet.
        Returns scores 0-100 for each planet.
        """
        ref = matrix[0].chart
        strengths = {}
        
        # Dignity scores based on rashi position
        dignity_map = {
            "Sun": {5: 20, 1: 15, 4: -10, 7: -10},  # Exalted in Leo, debilitated in Libra
            "Moon": {2: 20, 8: -10},  # Exalted in Taurus
            "Mars": {10: 20, 4: -10},  # Exalted in Capricorn
            "Mercury": {6: 20, 12: -10},  # Exalted in Virgo
            "Jupiter": {4: 20, 10: -10},  # Exalted in Cancer
            "Venus": {12: 20, 6: -10},  # Exalted in Pisces
            "Saturn": {7: 20, 1: -10}  # Exalted in Libra
        }
        
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            score = 50  # Base score
            p_data = ref.planets[planet]
            rashi = p_data.rashi
            
            # Add dignity
            if planet in dignity_map and rashi in dignity_map[planet]:
                score += dignity_map[planet][rashi]
            
            # Add house strength (based on BAV contribution across all houses)
            total_bav = sum([h.bav_scores.get(planet, 0) for h in ref.houses.values()])
            score += min(30, total_bav)  # Cap at 30
            
            # Normalize to 0-100
            strengths[planet] = max(0, min(100, score))
            
        return strengths
    
    def calculate_vimshottari_dasha(self, dob, moon_nakshatra: int) -> List[Dict[str, Any]]:
        """
        Calculates Vimshottari Dasha periods.
        Returns list of {planet, start_age, end_age, duration_years}
        """
        from datetime import date
        
        # Dasha sequence and durations (in years)
        dasha_sequence = [
            ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10),
            ("Mars", 7), ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)
        ]
        
        # Nakshatra to starting Dasha lord
        nak_to_lord = {
            1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8,  # Ashwini to Ashlesha
            10: 0, 11: 1, 12: 2, 13: 3, 14: 4, 15: 5, 16: 6, 17: 7, 18: 8,  # Magha to Jyeshtha
            19: 0, 20: 1, 21: 2, 22: 3, 23: 4, 24: 5, 25: 6, 26: 7, 27: 8   # Mula to Revati
        }
        
        start_index = nak_to_lord.get(moon_nakshatra, 0)
        
        periods = []
        current_age = 0
        
        # Generate periods for 120 years (full cycle)
        for i in range(9):
            idx = (start_index + i) % 9
            planet, duration = dasha_sequence[idx]
            
            periods.append({
                "planet": planet,
                "start_age": current_age,
                "end_age": current_age + duration,
                "duration_years": duration
            })
            
            current_age += duration
            
        # Return only periods up to age 90 or next 60 years
        today = date.today()
        current_user_age = today.year - dob.year
        relevant_periods = [p for p in periods if p['end_age'] >= current_user_age and p['start_age'] <= current_user_age + 60]
        
        return relevant_periods[:8]  # Limit to next 8 periods

