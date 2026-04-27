
from typing import Dict, List, Any

class AstrologicalInterpreter:
    """
    Translates statistical data (scores, positions) into traditional
    astrological inferences and narratives.
    """

    # Knowledge Base (Simplified for the specific signatures we found, expandable)
    NAKSHATRA_NAMES = {
        1: "Ashwini", 2: "Bharani", 3: "Krittika", 4: "Rohini", 5: "Mrigashira",
        6: "Ardra", 7: "Punarvasu", 8: "Pushya", 9: "Ashlesha", 10: "Magha",
        11: "Purva Phalguni", 12: "Uttara Phalguni", 13: "Hasta", 14: "Chitra",
        15: "Swati", 16: "Vishakha", 17: "Anuradha", 18: "Jyeshtha", 19: "Mula",
        20: "Purva Ashadha", 21: "Uttara Ashadha", 22: "Shravana", 23: "Dhanishta",
        24: "Shatabhisha", 25: "Purva Bhadrapada", 26: "Uttara Bhadrapada", 27: "Revati"
    }
    
    NAKSHATRA_MEANINGS = {
        1: "Ashwini (The Star of Transport): Ruled by Ketu. Symbolized by a Horse's Head. **Shakti**: *Cid Vyapa Shakti* (Power to quickly reach things). \n**Vedic Insight**: Persons born with planets here have a pioneering spirit and healing energy (Ashwini Kumaras). It indicates a soul eager for new beginnings and swift action.",
        2: "Bharani (The Star of Restraint): Ruled by Venus. Symbolized by the Yoni. **Shakti**: *Apabharani Shakti* (Power to carry things away). \n**Vedic Insight**: Represents the struggle between opposites (Life/Death). It grants the power to endure extreme contradictions and birth new creations through labor.",
        3: "Krittika (The Star of Fire): Ruled by Sun. Symbolized by a Razor. **Shakti**: *Dahana Shakti* (Power to burn and purify). \n**Vedic Insight**: The 'Cutter'. It represents sharp intelligence and a critical nature. It burns away impurities to reveal the truth.",
        4: "Rohini (The Star of Ascent): Ruled by Moon. Symbolized by a Chariot. **Shakti**: *Rohana Shakti* (Power to make things grow). \n**Vedic Insight**: The favorite of the Moon. It represents fertility, agriculture, and the ability to manifest material desires.",
        5: "Mrigashira (The Searching Star): Ruled by Mars. Symbolized by a Deer's Head. **Shakti**: *Prinana Shakti* (Power to give fulfillment). \n**Vedic Insight**: Represents the spiritual warrior searching for soma (immortality). It grants a restless, inquisitive, and sensitive nature.",
        6: "Ardra (The Star of Sorrow): Ruled by Rahu. Symbolized by a Teardrop. **Shakti**: *Yatna Shakti* (Power to make effort). \n**Vedic Insight**: Represents the storm (Rudra) that clears the air. It indicates transformation through emotional turbulence and intellectual intensity.",
        7: "Punarvasu (The Star of Renewal): Ruled by Jupiter. Symbolized by a Quiver of Arrows. **Shakti**: *Vasutva Prapana Shakti* (Power to gain wealth/substance). \n**Vedic Insight**: 'Return of the Light'. It allows one to bounce back from failure. It is the star of safety, repetition, and restoration.",
        8: "Pushya (The Star of Nourishment): Ruled by Saturn. Symbolized by a Cow's Udder. **Shakti**: *Brahmavarchasa Shakti* (Power to create spiritual energy). \n**Vedic Insight**: Considered the most auspicious star. It grants the ability to nourish structures, societies, and families.",
        9: "Ashlesha (The Clinging Star): Ruled by Mercury. Symbolized by a Coiled Serpent. **Shakti**: *Vis Ashleshana Shakti* (Power to inflict poison). \n**Vedic Insight**: Represents Kundalini energy and primal instincts. It grants immense psychological insight but warns against deception.",
        10: "Magha (The Star of Power): Ruled by Ketu. Symbolized by a Throne. **Shakti**: *Tyage Kshepani Shakti* (Power to leave the body). \n**Vedic Insight**: Connected to the Pitris (Ancestors). It grants connection to lineage, authority, and the duty to uphold tradition.",
        11: "Purva Phalguni (The Fruit of the Tree): Ruled by Venus. Symbolized by a Hammock. **Shakti**: *Prajanana Shakti* (Power of procreation). \n**Vedic Insight**: Represents the joy of social connection and relaxation. It grants artistic talent and the ability to enjoy the fruits of past karma.",
        12: "Uttara Phalguni (The Star of Patronage): Ruled by Sun. Symbolized by a Bed legs. **Shakti**: *Chayani Shakti* (Power of accumulation). \n**Vedic Insight**: Ruled by Aryaman (God of Patronage). It represents kindness, social contracts, and wealth gained through noble relationships. A 'King-Maker' star.",
        13: "Hasta (The Golden Handed): Ruled by Moon. Symbolized by a Hand. **Shakti**: *Hasta Sthapaniya Agama Shakti* (Power to put one's object of desire in hand). \n**Vedic Insight**: Represents skilled craftsmanship and dexterity. It grants the ability to manifest what one seeks through hands-on effort and comedy.",
        14: "Chitra (The Star of Opportunity): Ruled by Mars. Symbolized by a Jewel. **Shakti**: *Punya Chayani Shakti* (Power to accumulate merit). \n**Vedic Insight**: The 'Celestial Architect' (Tvashtar). It represents design, illusion (Maya), and the ability to create dazzling structures or forms.",
        15: "Swati (The Self-Going Star): Ruled by Rahu. Symbolized by a Shoot of Plant. **Shakti**: *Pradhvamsa Shakti* (Power to scatter like the wind). \n**Vedic Insight**: Ruled by Vayu. It represents independence, diplomacy, and the ability to bend without breaking.",
        16: "Vishakha (The Star of Purpose): Ruled by Jupiter. Symbolized by a Triumphal Arch. **Shakti**: *Vyapana Shakti* (Power to achieve and manifest). \n**Vedic Insight**: Represents the split determination to achieve goals. It grants ambition, jealousy of rivals, and ultimate victory.",
        17: "Anuradha (The Star of Success): Ruled by Saturn. Symbolized by a Lotus. **Shakti**: *Radhana Shakti* (Power of worship). \n**Vedic Insight**: 'Following the Spark'. It represents friendship (Mitra) and devotion. It grants the ability to bloom even in difficult circumstances/mud.",
        18: "Jyeshtha (The Chief Star): Ruled by Mercury. Symbolized by an Earring/Talisman. **Shakti**: *Arohana Shakti* (Power to rise/conquer). \n**Vedic Insight**: The eldest sister (Alakshmi). It grants seniority, protection, and the burden of leadership. Represents psychological dominance.",
        19: "Mula (The Root Star): Ruled by Ketu. Symbolized by Tied Roots. **Shakti**: *Barhana Shakti* (Power to ruin and destroy). \n**Vedic Insight**: Ruled by Nirriti (Goddess of Calamity). It represents getting to the root of the matter, often through destruction of the old to build the new.",
        20: "Purva Ashadha (The Invincible Star): Ruled by Venus. Symbolized by a Fan. **Shakti**: *Varchograhana Shakti* (Power to invigorate water). \n**Vedic Insight**: Ruled by Apah (Water). It represents the declaration of war and the patience to wait for victory. Unbeatable resilience.",
        21: "Uttara Ashadha (The Universal Star): Ruled by Sun. Symbolized by an Elephant's Tusk. **Shakti**: *Apradhrisya Shakti* (Power to give permanent victory). \n**Vedic Insight**: Represents the 'Universal' (Vishvadevas). It grants alliances, integrity, and long-lasting achievements.",
        22: "Shravana (The Star of Learning): Ruled by Moon. Symbolized by an Ear. **Shakti**: *Samhanana Shakti* (Power to connect). \n**Vedic Insight**: Ruled by Vishnu. It represents listening/Sruti. It grants wide knowledge, oral tradition, and organizational skill.",
        23: "Dhanishta (The Star of Symphony): Ruled by Mars. Symbolized by a Drum. **Shakti**: *Khyapayitri Shakti* (Power to give fame and abundance). \n**Vedic Insight**: The 'Weathiest'. It represents rhythm, music, and emptiness (hollow drum). It grants wealth and the ability to time actions perfectly.",
        24: "Shatabhisha (The Veiling Star): Ruled by Rahu. Symbolized by an Empty Circle. **Shakti**: *Bheshaja Shakti* (Power to heal). \n**Vedic Insight**: '100 Physicians'. It represents boundaries, secrecy, and deep healing. It grants access to hidden knowledge and ocean mysteries.",
        25: "Purva Bhadrapada (The Scorching Pair): Ruled by Jupiter. Symbolized by a Sword/Two-faced man. **Shakti**: *Yajamana Udyamana Shakti* (Power to raise the evolutionary level). \n**Vedic Insight**: Fire Dragon (Aja Ekapada). It represents penance, intensity, and spiritual transformation through fire.",
        26: "Uttara Bhadrapada (The Warrior Star): Ruled by Saturn. Symbolized by Twins/Snake in water. **Shakti**: *Varshodyamana Shakti* (Power to bring rain). \n**Vedic Insight**: The Deep Sea Dragon (Ahir Budhnya). It represents control, kundalini capability, and the power to contain immense energy.",
        27: "Revati (The Keeper of Flocks): Ruled by Mercury. Symbolized by a Fish. **Shakti**: *Kshiradyapani Shakti* (Power of nourishment). \n**Vedic Insight**: The Final Path (Pushan). It represents safe travel, protection of animals, and transcendental wisdom."
    }

    RASHI_NATURE = {
        1: "Aries (Mesha): The Ram.",
        2: "Taurus (Vrishabha): The Bull.",
        3: "Gemini (Mithuna): The Twins.",
        4: "Cancer (Karka): The Crab.",
        5: "Leo (Simha): The Lion.",
        6: "Virgo (Kanya): The Maiden.",
        7: "Libra (Tula): The Scale.",
        8: "Scorpio (Vrishchika): The Scorpion.",
        9: "Sagittarius (Dhanu): The Archer.",
        10: "Capricorn (Makara): The Sea-Goat.",
        11: "Aquarius (Kumbha): The Water-Bearer.",
        12: "Pisces (Meena): The Fishes."
    }

    PLANET_NATURE = {
        "Sun": {
            "karaka": "Atma Karaka (Soul)",
            "desc": "The SOURCE. It represents consistency, authority, and the fire of existence."
        },
        "Moon": {
            "karaka": "Mana Karaka (Mind)",
            "desc": "The REFLECTOR. It represents fluid intelligence, emotions, and public connection."
        },
        "Mars": {
            "karaka": "Bhatru Karaka (Energy)",
            "desc": "The WARRIOR. It represents logic, engineering, land, and one-pointed focus."
        },
        "Mercury": {
            "karaka": "Vidya Karaka (Intellect)",
            "desc": "The MESSENGER. It represents discriminative intelligence, speech, and trade."
        },
        "Jupiter": {
            "karaka": "Guru (Wisdom)",
            "desc": "The EXPANDER. It represents ether, dharma, luck, and adherence to law."
        },
        "Venus": {
            "karaka": "Kalatra Karaka (Desire)",
            "desc": "The DIPLOMAT. It represents decisions, valuation, relationships, and semen/ojas."
        },
        "Saturn": {
            "karaka": "Karma Karaka (Action)",
            "desc": "The JUDGE. It represents boundaries, time, delay, and the structure of reality."
        },
         "Rahu": {
            "karaka": "Chaya Graha (Illusion)",
            "desc": "The OBSERVER. It represents expansion, foreign engineering, and breaking taboos."
        },
         "Ketu": {
            "karaka": "Moksha Karaka (Liberation)",
            "desc": "The ASCETIC. It represents contraction, mathematics, and flagless existence."
        }
    }

    # Current Transits (Jan 2026 Reference)
    # Ideally this comes from a service, but for "Principles" demonstration we define the current context.
    CURRENT_TRANSITS = {
        "Saturn": 12,  # Pisces
        "Jupiter": 3,  # Gemini
        "Rahu": 11,    # Aquarius
        "Ketu": 5      # Leo
    }

    
    def predict_transit_impacts(self, rashi_data: Dict[str, Any]) -> List[str]:
        # Legacy method placeholder or remove if unused. 
        # Kept for compatibility but not primary anymore.
        pass

    def __init__(self):
        # Initialize Native AI Engine (No API Key required)
        from .llm_engine import LLMEngine
        
        # Always available
        self.llm = LLMEngine()

    # Future Major Transits (Hardcoded for Demo Accuracy)
    # Source: Standard Ephemeris
    FUTURE_TRANSITS = [
        {
            "planet": "Jupiter",
            "current_rashi": 3, # Gemini
            "next_rashi": 4,    # Cancer
            "transition_date": "2026-06-02", # Approx date
            "description": "Jupiter moves from Gemini to Cancer"
        },
        {
            "planet": "Saturn",
            "current_rashi": 12, # Pisces
            "next_rashi": 1,     # Aries
            "transition_date": "2028-02-23",
            "description": "Saturn moves from Pisces to Aries"
        },
        {
            "planet": "Rahu",
            "current_rashi": 11, # Aquarius
            "next_rashi": 10,    # Capricorn (Retrograde)
            "transition_date": "2026-10-17",
            "description": "Rahu moves from Aquarius to Capricorn"
        }
    ]

    def analyze_transit_shift(self, rashi_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyzes the SHIFT in fortune.
        """
        forecasts = []
        
        for transit in self.FUTURE_TRANSITS:
            p = transit['planet']
            # Use Integers for lookup as Analyzer produces Integer keys
            curr_r = int(transit['current_rashi'])
            next_r = int(transit['next_rashi'])
            
            # Get Karaka info
            karaka_info = self.PLANET_NATURE.get(p, {"karaka": "General factor", "desc": "Influence"})
            karaka_str = karaka_info['karaka']
            
            # Scores (Default to 25 if data missing)
            # Try both int and str to be safe, but Analyzer likely returns Int keys
            def get_score(rid):
                if rid in rashi_data: return rashi_data[rid].get('mean_score', 25)
                if str(rid) in rashi_data: return rashi_data[str(rid)].get('mean_score', 25)
                return 25
                
            curr_score = get_score(curr_r)
            next_score = get_score(next_r)
            
            # 1. Determine Zone Quality
            def get_zone_type(s):
                if s >= 30: return "GOLDEN"
                if s >= 25: return "AVERAGE"
                return "WEAK"
                
            curr_zone = get_zone_type(curr_score)
            next_zone = get_zone_type(next_score)
            
            # 2. Determine Trend Logic
            trend = ""
            details = ""
            
            if curr_zone == "GOLDEN" and next_zone == "GOLDEN":
                trend = "SUSTAINED PROSPERITY"
                details = (f"You are moving from one Powerhouse ({curr_score:.1f}) to another ({next_score:.1f}). "
                           f"This is a rare, extended period of high achievement for **{karaka_str}**. "
                           f"Expect consistent growth in {karaka_info['desc']}.")
            elif curr_zone == "WEAK" and next_zone == "WEAK":
                trend = "PROLONGED CHALLENGE"
                details = (f"The testing phase continues. You move from a low-energy zone ({curr_score:.1f}) to another ({next_score:.1f}). "
                           f"Matters related to **{karaka_str}** will require extra patience. "
                           f"Focus on preservation rather than expansion in {karaka_info['desc']}.")
            elif curr_zone == "WEAK" and next_zone == "GOLDEN":
                trend = "MAJOR BREAKTHROUGH"
                details = (f"Relief is here. You leave a struggle zone ({curr_score:.1f}) and enter a zone of abundance ({next_score:.1f}). "
                           f"This is a specific turning point for **{karaka_str}**. "
                           f"Expect sudden luck and expansion in {karaka_info['desc']}.")
            elif curr_zone == "GOLDEN" and next_zone == "WEAK":
                trend = "SUDDEN DROP / CAUTION"
                details = (f"Prepare for a cooldown. You leave a peak phase ({curr_score:.1f}) for a restrictive one ({next_score:.1f}). "
                           f"Protect your gains related to **{karaka_str}**. "
                           f"Do not take new risks in {karaka_info['desc']}.")
            elif next_score > curr_score:
                trend = "IMPROVING"
                details = (f"Conditions improve slightly ({curr_score:.1f} -> {next_score:.1f}). "
                           f"Better resource availability for **{karaka_str}**.")
            elif next_score < curr_score:
                trend = "DECLINING"
                details = (f"Conditions tighten slightly ({curr_score:.1f} -> {next_score:.1f}). "
                           f"Expect to work harder for benefits related to **{karaka_str}**.")
            else:
                trend = "STABLE"
                details = f"Conditions remain steady ({curr_score:.1f} -> {next_score:.1f}) for all matters of **{karaka_str}**."
                
            forecasts.append({
                "header": f"{transit['description']} ({transit['transition_date']})",
                "trend": trend,
                "current_score": curr_score,
                "next_score": next_score,
                "analysis": details,
                "karaka_context": karaka_info['karaka']
            })
            
        return forecasts

    # Tithi Meanings Map
    TITHI_MEANINGS = {
        "Pratipada": "The First Step. Good for planning and inception.",
        "Dwitiya": "Expansion. Good for laying foundations.",
        "Tritiya": "Energy/Power. Good for bold actions.",
        "Chaturthi": "Obstacle Removal. Good for overcoming enemies (but avoid good works).",
        "Panchami": "Healing/Lakshmi. Good for medicine and wealth.",
        "Shashthi": "Victory. Good for stubborn tasks.",
        "Saptami": "Health/Partnership. Good for journey and socializing.",
        "Ashtami": "Conflict/Strength. Good for battles, bad for auspicious start.",
        "Navami": "Aggression. Good for debating and competing.",
        "Dashami": "Virtue/Dharma. Good for noble deeds and government work.",
        "Ekadashi": "Fasting/Spirituality. Good for detox and prayer.",
        "Dwadashi": "Renown/Vision. Good for big goals and fame.",
        "Trayodashi": "Victory/Pradosha. Good for overcoming guilt and karma.",
        "Chaturdashi": "Cruelty/Force. Good for destructive actions or cleaning.",
        "Purnima": "Fullness/Completion. Peak creative energy.",
        "Amavasya": "Ancestors/Void. Good for meditation and secret works."
    }

    def generate_narrative(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a comprehensive narrative report.
        """
        narrative = {
            "universal_identity": [],  # Common Links
            "karma_classification": [], # Phase 5: Fixed vs Variable
            "strategic_strengths": [], # Rashi Scores (Detailed)
            "karmic_challenges": [],   # Weak Rashis (Detailed)
            "transit_timeline": []     # Future Forecast
        }
        
        # 0. Phase 5: Karma Classification (Sanchita vs Prarabdha)
        rashi_data = analysis_results.get("rashi_analysis", {})
        bav_breakdown_all = analysis_results.get("bav_breakdown", {})

        for r_id_int, stats in rashi_data.items():
            fixed_status = stats['key_insights'].get('fixed_status', 'VARIABLE')
            r_name = self.RASHI_NATURE.get(int(r_id_int), f"Rashi {r_id_int}").split(":")[0]
            
            # BAV Analysis
            bav_scores = bav_breakdown_all.get(r_id_int, {})
            # Sort planets by contribution
            top_contributors = sorted(bav_scores.items(), key=lambda x: x[1], reverse=True)
            # Filter score > 0
            contributors_str = ", ".join([f"{p} ({s})" for p, s in top_contributors if s > 0])
            
            # Generate Dynamic BAV Insight
            top_3_planets = [p for p, s in top_contributors[:3] if s > 0]
            if top_3_planets:
                planet_influence_desc = f"Fueled by **{', '.join(top_3_planets)}**."
            else:
                planet_influence_desc = "Low planetary support."

            if fixed_status == "FIXED":
                classification = "**Sanchita** (Fixed/Universal)"
                insight = (f"**Fixed Asset**. This area is supported by immutable planetary forces ({planet_influence_desc}). "
                           "The score is universally high for your generation, indicating a shared resource.")
            else:
                classification = "**Prarabdha** (Variable/Individual)"
                insight = f"**Variable Outcome**. While {planet_influence_desc}, the final strength of this house heavily depends on your specific Ascendant."
                
            narrative["karma_classification"].append({
                "rashi": r_name,
                "status": classification,
                "insight": insight,
                "bav_details": contributors_str
            })
        
        # 1. Full Common Links Analysis
        common_links = analysis_results.get("common_links", {})
        nakshatras = common_links.get("nakshatra_positions", [])
        
        for item in nakshatras:
            planet = item['planet']
            nak_id = item['nakshatra_id']
            # Get Nakshatra name, meaning, and Shakti
            raw_nak_text = self.NAKSHATRA_MEANINGS.get(nak_id, f"Nakshatra {nak_id}")
            nak_name = raw_nak_text.split(":")[0]
            
            # Extract Shakti if present (it's in the text)
            shakti_segment = "Unknown Power"
            if "**Shakti**:" in raw_nak_text:
                parts = raw_nak_text.split("**Shakti**:")
                if len(parts) > 1:
                    shakti_segment = parts[1].split("\n")[0].strip()

            p_nature_info = self.PLANET_NATURE.get(planet, {"karaka": "Influence", "desc": "General Energy"})
            
            # Concise interpretation
            entry = (
                f"**{planet} in {nak_name}** - {p_nature_info['karaka']}: "
                f"{p_nature_info['desc']} Your generation channels {planet}'s energy through {shakti_segment}"
            )
            narrative["universal_identity"].append(entry)
                
        # 2. Strategic Strengths & Challenges (Detailed Elaboration)
        rashi_data = analysis_results.get("rashi_analysis", {})
        sorted_rashis = sorted(rashi_data.items(), key=lambda x: x[1]['mean_score'], reverse=True)
        
        top3 = sorted_rashis[:3]
        bot3 = sorted_rashis[-3:]
        
        # Helper for Detailed Explanations
        def explain_strength(r_id, driver):
            # Dynamic text generation based on Rashi nature
            elem = "Fire" if r_id in [1,5,9] else "Earth" if r_id in [2,6,10] else "Air" if r_id in [3,7,11] else "Water"
            desc = "intuition and emotional connection." # Default for Water
            if elem == "Fire": desc = "action and initiative."
            elif elem == "Earth": desc = "tangible assets and stability."
            elif elem == "Air": desc = "ideas and networks."
            
            return (f"This zone is a natural powerhouse for you. Because it is supported by **{driver}**, "
                    f"efforts placed here yield maximum return with minimal friction. "
                    f"As a {elem} sign, expect results to manifest through {desc}")

        def explain_weakness(r_id, driver):
             elem = "Fire" if r_id in [1,5,9] else "Earth" if r_id in [2,6,10] else "Air" if r_id in [3,7,11] else "Water"
             impact = "growth/optimism" # Default
             if driver == "Mars": impact = "confidence/startups"
             elif driver == "Venus": impact = "money/relationships"
             elif driver == "Mercury": impact = "communication/contracts"
             elif driver == "Moon": impact = "emotional peace"
             elif driver == "Sun": impact = "authority/ego"
             elif driver == "Saturn": impact = "structure/career"
             elif driver == "Jupiter": impact = "growth/optimism"
             
             return (f"This is a 'Karmic Bottleneck'. The energy here is restricted or requires double the effort. "
                     f"Since **{driver}** is the ruler, you may face delays in matters of {impact}. "
                     "Remedial measure: Patience and deliberate planning.")

        for r_id_str, stats in top3:
            r_id = int(r_id_str)
            score = stats['mean_score']
            r_name = self.RASHI_NATURE.get(r_id, f"Rashi {r_id}")
            driver = stats['key_insights']['primary_driver']
            
            narrative["strategic_strengths"].append(
                f"**{r_name} (Score: {score:.1f})**: Top-Tier Zone.\n"
                f"> {explain_strength(r_id, driver)}"
            )

        for r_id_str, stats in bot3:
            r_id = int(r_id_str)
            score = stats['mean_score']
            if score < 26: 
                r_name = self.RASHI_NATURE.get(r_id, f"Rashi {r_id}")
                driver = stats['key_insights']['primary_driver']
                narrative["karmic_challenges"].append(
                    f"**{r_name} (Score: {score:.1f})**: Resistance Zone.\n"
                    f"> {explain_weakness(r_id, driver)}"
                )

        # 3. Kingmaker
        p_power = analysis_results.get("planet_power", {})
        if p_power:
            sorted_power = sorted(p_power.items(), key=lambda x: x[1], reverse=True)
            top_planet, top_score = sorted_power[0]
            p_nature = self.PLANET_NATURE.get(top_planet, {"karaka": "Influence", "desc": "Power"})
            narrative["power_rank"] = {
                "kingmaker": f"**{top_planet}** is the Kingmaker ({top_score} Bindus).",
                "insight": f"It is the single biggest contributor to the chart's strength. Success comes through {p_nature['desc']}"
            }

        # 4. Transit Timeline
        narrative["transit_timeline"] = self.analyze_transit_shift(rashi_data)
        
        # 5. Elemental Balance
        elem_counts = analysis_results.get("elemental_balance", {})
        total_planets = sum(elem_counts.values())
        if total_planets > 0:
            dominant_elem = max(elem_counts, key=elem_counts.get)
            percent = (elem_counts[dominant_elem] / total_planets) * 100
            desc_map = {
                "Fire": "Driven by action and intuition.",
                "Earth": "Focused on results and stability.",
                "Air": "Intellectual and social.",
                "Water": "Emotional and sensitive."
            }
            narrative["elemental_analysis"] = {
                "dominant": dominant_elem,
                "percentage": round(percent, 1),
                "insight": f"With {percent:.1f}% planets in {dominant_elem}, the core temperament is **{dominant_elem.upper()}**. {desc_map.get(dominant_elem, '')}"
            }
            
        # 6. Peak Times (Ascendant Scenarios)
        # Format as list of dicts: {asc, time, score}
        peak_raw = analysis_results.get("peak_times", [])
        peak_narrative = []
        for p in peak_raw:
            r_id = p['ascendant']
            r_name = self.RASHI_NATURE.get(r_id, f"Rashi {r_id}").split(":")[0] 
            peak_narrative.append({
                "ascendant": r_name,
                "time": p['time'],
                "score": p['score']
            })
        narrative["peak_times_table"] = peak_narrative

        # 7. Directional Strength
        narrative["directional_strength"] = analysis_results.get("directional_strength", {})
        
        # 8. Yogas
        narrative["yogas"] = analysis_results.get("yogas", [])
        
        # 9. Tithi
        tithi_data = analysis_results.get("tithi_info", {})
        tithi_name = tithi_data.get("tithi", "").split(" ")[0] # extract "Dwadashi"
        tithi_meaning = self.TITHI_MEANINGS.get(tithi_name, "A phase of the moon.")
        
        tithi_data["meaning"] = tithi_meaning
        narrative["tithi_info"] = tithi_data
        
        # 10. Life Activation Windows
        narrative["life_activation_windows"] = analysis_results.get("life_activation_windows", [])
        
        # 11. Planetary Strength
        narrative["planetary_strength"] = analysis_results.get("planetary_strength", {})
        
        # 12. Dasha Periods
        narrative["dasha_periods"] = analysis_results.get("dasha_periods", [])
        
        
        # 13. Personalized Remedies (based on weak planets)
        planetary_strength = analysis_results.get("planetary_strength", {})
        narrative["remedies"] = self.generate_remedies(planetary_strength)
        
        # 14. Deep Stats for Radar Chart (Shad Bala Based)
        def get_strength(planet, default=50):
            val = planetary_strength.get(planet, default)
            if isinstance(val, str):
                try: val = float(val)
                except: val = default
            return min(98, max(20, int(val)))
        
        sun = get_strength("Sun")
        moon = get_strength("Moon")
        mars = get_strength("Mars")
        mercury = get_strength("Mercury")
        jupiter = get_strength("Jupiter")
        venus = get_strength("Venus")
        saturn = get_strength("Saturn")
        
        narrative["deep_stats"] = {
            "willpower": int((sun + mars) / 2),
            "intellect": int((mercury + jupiter) / 2),
            "intuition": int((moon + saturn) / 2),
            "leadership": int((sun + saturn) / 2),
            "wealth_iq": int((jupiter + venus) / 2),
            "empathy": int((venus + moon) / 2)
        }
        
        # 14. AI Deep Dive (If available)
        if self.llm:
            narrative["ai_insight"] = self.llm.generate_insight(narrative)
        else:
            narrative["ai_insight"] = None

        return narrative
    
    def generate_remedies(self, planetary_strength: Dict[str, int]) -> List[Dict[str, Any]]:
        """
        Generates personalized remedies based on weak planets (strength < 50).
        """
        remedy_map = {
            "Sun": {"gemstone": "Ruby", "mantra": "Om Suryaya Namaha", "color": "Orange/Red", "day": "Sunday"},
            "Moon": {"gemstone": "Pearl", "mantra": "Om Chandraya Namaha", "color": "White/Silver", "day": "Monday"},
            "Mars": {"gemstone": "Red Coral", "mantra": "Om Mangalaya Namaha", "color": "Red", "day": "Tuesday"},
            "Mercury": {"gemstone": "Emerald", "mantra": "Om Budhaya Namaha", "color": "Green", "day": "Wednesday"},
            "Jupiter": {"gemstone": "Yellow Sapphire", "mantra": "Om Gurave Namaha", "color": "Yellow", "day": "Thursday"},
            "Venus": {"gemstone": "Diamond/White Sapphire", "mantra": "Om Shukraya Namaha", "color": "White", "day": "Friday"},
            "Saturn": {"gemstone": "Blue Sapphire", "mantra": "Om Shanaye Namaha", "color": "Blue/Black", "day": "Saturday"}
        }
        
        weak_planets = [(p, s) for p, s in planetary_strength.items() if s < 50]
        weak_planets.sort(key=lambda x: x[1])  # Sort by strength ascending
        
        remedies = []
        for planet, strength in weak_planets[:3]:  # Top 3 weakest
            if planet in remedy_map:
                remedy = remedy_map[planet].copy()
                remedy["planet"] = planet
                remedy["strength"] = strength
                remedies.append(remedy)
                
        return remedies

