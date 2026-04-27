
from typing import Dict, List

class BAVCalculator:
    """
    Implements standard Paraśara Ashtakavarga Rules.
    (Rekhas/Bindus contributed by planets in houses from themselves and others).
    """

    # BINDU TABLES (Benefic Places)
    # 1-indexed houses from the reference planet
    RULES = {
        "Sun": {
            "Sun": [1, 2, 4, 7, 8, 9, 10, 11],
            "Moon": [3, 6, 10, 11],
            "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
            "Mercury": [3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [5, 6, 9, 11],
            "Venus": [6, 7, 12],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
            "Lagna": [3, 4, 6, 10, 11, 12]
        },
        "Moon": {
            "Sun": [3, 6, 7, 8, 10, 11],
            "Moon": [1, 3, 6, 7, 10, 11],
            "Mars": [2, 3, 5, 6, 9, 10, 11],
            "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
            "Jupiter": [1, 4, 7, 8, 10, 11, 12],
            "Venus": [3, 4, 5, 7, 9, 10, 11],
            "Saturn": [3, 5, 6, 11],
            "Lagna": [3, 6, 10, 11]
        },
        "Mars": {
            "Sun": [3, 5, 6, 10, 11],
            "Moon": [3, 6, 11],
            "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
            "Mercury": [3, 5, 6, 11],
            "Jupiter": [6, 10, 11, 12],
            "Venus": [6, 8, 11, 12],
            "Saturn": [1, 4, 7, 8, 9, 10, 11],
            "Lagna": [1, 3, 6, 10, 11]
        },
        "Mercury": {
            "Sun": [5, 6, 9, 11, 12],
            "Moon": [2, 4, 6, 8, 10, 11],
            "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
            "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [6, 8, 11, 12],
            "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
            "Lagna": [1, 2, 4, 6, 8, 10, 11]
        },
        "Jupiter": {
            "Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11],
            "Moon": [2, 5, 7, 9, 11],
            "Mars": [1, 2, 4, 7, 8, 10, 11],
            "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
            "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
            "Venus": [2, 5, 6, 9, 10, 11],
            "Saturn": [3, 5, 6, 12],
            "Lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11]
        },
        "Venus": {
            "Sun": [8, 11, 12],
            "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12],
            "Mars": [3, 4, 6, 9, 11, 12],
            "Mercury": [3, 5, 6, 9, 11],
            "Jupiter": [5, 8, 9, 10, 11],
            "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
            "Saturn": [3, 4, 5, 8, 9, 10, 11],
            "Lagna": [1, 2, 3, 4, 5, 8, 9, 11]
        },
        "Saturn": {
            "Sun": [1, 2, 4, 7, 8, 10, 11],
            "Moon": [3, 6, 11],
            "Mars": [3, 5, 6, 10, 11, 12],
            "Mercury": [6, 8, 9, 10, 11, 12],
            "Jupiter": [5, 6, 11, 12],
            "Venus": [6, 11, 12],
            "Saturn": [3, 5, 6, 11],
            "Lagna": [1, 3, 4, 6, 10, 11]
        }
    }
    
    # Mapping planet names to index if needed, but we used names in main mock.
    
    @staticmethod
    def calculate_bav(candidate_planet: str, all_positions: Dict[str, int], exclude_list: List[str] = None) -> Dict[int, int]:
        """
        Calculates the BAV distribution (12 signs) for a given candidate planet.
        """
        if exclude_list is None: exclude_list = []
        if candidate_planet in BAVCalculator.RULES:
            rules = BAVCalculator.RULES[candidate_planet]
        else:
            return {}

        bav_counts = {r: 0 for r in range(1, 13)}
        
        for donor, benefics in rules.items():
            if donor in exclude_list or donor not in all_positions:
                continue
                
            donor_rashi = all_positions[donor]
            for house_offset in benefics:
                target_rashi = (donor_rashi + house_offset - 1) % 12
                if target_rashi == 0: target_rashi = 12
                bav_counts[target_rashi] += 1
                
        return bav_counts

    @staticmethod
    def trikona_shodhana(bav: Dict[int, int]) -> Dict[int, int]:
        """
        Phase 3: Trikona Shodhana (Reduction by Trines).
        Subtract the minimum score in each trine group from all signs in that group.
        Groups: (1,5,9), (2,6,10), (3,7,11), (4,8,12)
        """
        reduced = bav.copy()
        trines = [
            [1, 5, 9],
            [2, 6, 10],
            [3, 7, 11],
            [4, 8, 12]
        ]
        
        for group in trines:
            scores = [bav[r] for r in group]
            min_score = min(scores)
            for r in group:
                reduced[r] -= min_score
                
        return reduced

    @staticmethod
    def ekadhipatya_shodhana(bav: Dict[int, int], all_positions: Dict[str, int]) -> Dict[int, int]:
        """
        Phase 3: Ekadhipatya Shodhana (Reduction by Ownership).
        Pairs: Mars(1,8), Venus(2,7), Mercury(3,6), Jupiter(9,12), Saturn(10,11).
        Excludes Sun(5) and Moon(4).
        """
        reduced = bav.copy()
        
        # Mapping Rashi -> occupying planets (excluding nodes/Lagna for occupancy usually? 
        # Standard rules: Sun-Saturn. Some include nodes, but typically 7 planets.)
        occupancy = {r: [] for r in range(1, 13)}
        planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        for p in planets:
            if p in all_positions:
                occupancy[all_positions[p]].append(p)

        pairs = [
            (1, 8),  # Mars
            (2, 7),  # Venus
            (3, 6),  # Mercury
            (9, 12), # Jupiter
            (10, 11) # Saturn
        ]

        for r1, r2 in pairs:
            b1, b2 = reduced[r1], reduced[r2]
            p1, p2 = occupancy[r1], occupancy[r2]
            
            # If both have 0 or both have planets: No reduction
            if (b1 == 0 and b2 == 0) or (p1 and p2):
                continue
            
            # Case: Both unoccupied
            if not p1 and not p2:
                if b1 == b2:
                    reduced[r1] = reduced[r2] = 0
                else:
                    m = min(b1, b2)
                    reduced[r1] -= m
                    reduced[r2] -= m
            
            # Case: One occupied, one not
            else:
                occ_r, unocc_r = (r1, r2) if p1 else (r2, r1)
                occ_b, unocc_b = reduced[occ_r], reduced[unocc_r]
                
                if unocc_b == 0:
                    continue
                
                if unocc_b > occ_b:
                    reduced[unocc_r] = occ_b
                elif unocc_b <= occ_b:
                    reduced[unocc_r] = 0
                    
        return reduced

    @staticmethod
    def calculate_sarvashtakavarga(all_positions_rashi: Dict[str, int], exclude_list: List[str] = None) -> Dict[int, Dict[str, int]]:
        """
        Calculates SAV for all 12 Rashis.
        Returns: { Rashi_ID: { "total": int, "breakdown": {Planet: score} } }
        """
        if exclude_list is None: exclude_list = []
        rashi_totals = {r: {"total": 0, "breakdown": {}} for r in range(1, 13)}
        planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        
        for p in planets:
            p_bav = BAVCalculator.calculate_bav(p, all_positions_rashi, exclude_list)
            for r in range(1, 13):
                score = p_bav[r]
                rashi_totals[r]["total"] += score
                rashi_totals[r]["breakdown"][p] = score
                
        return rashi_totals

    @staticmethod
    def calculate_shodhita_sav(all_positions_rashi: Dict[str, int], exclude_list: List[str] = None) -> Dict[int, int]:
        """
        Phase 3: Shodhita SAV (Reduced SAV).
        """
        if exclude_list is None: exclude_list = []
        shodhita_sav = {r: 0 for r in range(1, 13)}
        planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        
        for p in planets:
            # 1. Raw BAV
            p_bav = BAVCalculator.calculate_bav(p, all_positions_rashi, exclude_list)
            # 2. Trikona Shodhana
            p_tri = BAVCalculator.trikona_shodhana(p_bav)
            # 3. Ekadhipatya Shodhana
            p_eka = BAVCalculator.ekadhipatya_shodhana(p_tri, all_positions_rashi)
            
            # Sum reduced points
            for r in range(1, 13):
                shodhita_sav[r] += p_eka[r]
                
        return shodhita_sav
