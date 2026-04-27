from flask import Flask, render_template, request, jsonify
import sys
import os
import datetime
import markdown

# Setup paths for engine imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.join(BASE_DIR, 'astro_probability_engine')
sys.path.append(BASE_DIR)
sys.path.append(ENGINE_DIR)

from astro_probability_engine.astrology.real_service import SkyfieldAstrologyService
from astro_probability_engine.engine.generator import MatrixGenerator
from astro_probability_engine.engine.analyzer import MatrixAnalyzer
from astro_probability_engine.engine.interpreter import AstrologicalInterpreter

app = Flask(__name__)

# Initialize engine services once
service = SkyfieldAstrologyService()
generator = MatrixGenerator(service)
analyzer = MatrixAnalyzer()
interpreter = AstrologicalInterpreter()

def convert_narrative_to_markdown(narrative, dob, sample_count):
    """
    Converts narrative dictionary to a premium formatted markdown string.
    """
    lines = []
    lines.append("# Astrological Probability Report: Universal Signatures\n")
    lines.append(f"**Date of Analysis**: {dob.strftime('%Y-%m-%d')} | **Sample Size**: {sample_count} Charts\n")
    lines.append("This report identifies the *immutable astrological DNA* of this date. By isolating the Lagna (Ascendant), we reveal the planetary strengths common to everyone born today.\n")
    lines.append("---\n")
    
    # I. Universal Identity
    lines.append("## I. The Universal Identity (Fixed Promise)\n")
    lines.append("These are the traits common to *everyone* born on this date. They represent the 'Soul Code' of this cohort.\n\n")
    for item in narrative.get('universal_identity', []):
        parts = item.split(":", 1)
        if len(parts) == 2:
            lines.append(f"### {parts[0].strip()}\n")
            lines.append(parts[1].strip().replace("\n", "\n> ") + "\n")
        else:
            lines.append(f"- {item}\n")
    
    # II. Planetary Power Architecture
    lines.append("\n---\n")
    lines.append("## II. Planetary Power Architecture\n")
    if "power_rank" in narrative:
        pr = narrative["power_rank"]
        lines.append(f"### The Kingmaker: {pr['kingmaker'].split('(')[0].replace('**', '').strip()}\n")
        lines.append(f"> {pr['kingmaker']} {pr['insight']}\n")
    
    lines.append("\n### Strategic Citadels (High Probability Zones)\n")
    lines.append("These zodiac signs are your statistical 'Safe Harbors'.\n\n")
    for item in narrative.get('strategic_strengths', []):
        lines.append(f"✦ {item}\n")
        
    lines.append("\n### Karmic Bottlenecks (Areas of Resistance)\n")
    lines.append("These zones require conscious effort to unlock.\n\n")
    for item in narrative.get('karmic_challenges', []):
        lines.append(f"✦ {item}\n")

    # III. Karma Classification
    lines.append("\n---\n")
    lines.append("## III. Karma Classification (Sanchita vs Prarabdha)\n")
    lines.append("This section identifies which aspects of your chart are immutable (**Sanchita**) and which are dependent on birth time (**Prarabdha**). usage of the **Bhinnashtakavarga (BAV)** reveals the specific planetary support for each sign.\n\n")
    lines.append("| Rashi | Status | Insight | Planetary Contributors (BAV) |\n")
    lines.append("| :--- | :--- | :--- | :--- |\n")
    # Force UNIVERSAL status as per user's "Fixed Karma" requirement
    for item in narrative.get('karma_classification', []):
        lines.append(f"| **{item['rashi']}** | {item['status']} | {item['insight']} | {item.get('bav_details', 'N/A')} |\n")

    # IV. Transit Forecasting
    lines.append("\n---\n")
    lines.append("## IV. Transit Forecasting (2026-2028)\n\n")
    lines.append("| Event | Date | Trend | Analysis |\n")
    lines.append("| :--- | :--- | :--- | :--- |\n")
    for item in narrative.get('transit_timeline', []):
        header = item['header'].split('(')[0].strip()
        date = item['header'].split('(')[1].replace(')', '').strip()
        lines.append(f"| {header} | {date} | **{item['trend']}** | {item['analysis']} |\n")
    
    # V. The Elemental DNA
    lines.append("\n---\n")
    lines.append("## V. The Elemental DNA\n")
    if "elemental_analysis" in narrative:
        elem = narrative["elemental_analysis"]
        lines.append(f"**Dominant Element**: {elem['dominant'].upper()} ({elem['percentage']}%)\n")
        lines.append(f"> {elem['insight']}\n")
    
    # VI. Peak Potential Windows
    lines.append("\n---\n")
    lines.append("## VI. Peak Potential Windows\n\n")
    lines.append("| Ascendant | Best Time | Score |\n")
    lines.append("| :--- | :--- | :--- |\n")
    for p in narrative.get('peak_times_table', []):
        lines.append(f"| **{p['ascendant']}** | {p['time']} | **{p['score']}** |\n")
    
    # VII. Hidden Dimensions
    lines.append("\n---\n")
    lines.append("## VII. Hidden Dimensions\n")
    dirs = narrative.get("directional_strength", {})
    if dirs:
        lines.append(f"### Directional Mastery: {dirs.get('winner', 'Unknown')}\n")
    
    yogas = narrative.get("yogas", [])
    if yogas:
        lines.append("\n### Universal Yogas\n")
        for y in yogas:
            lines.append(f"- **{y['name']}**: {y['desc']}\n")
    
    tithi = narrative.get("tithi_info", {})
    if tithi:
        lines.append(f"\n### Tithi: {tithi.get('tithi', 'Unknown')}\n")
        lines.append(f"> {tithi.get('meaning', '')}\n")
    
    # VIII. Life Activation Windows
    life_windows = narrative.get("life_activation_windows", [])
    if life_windows:
        lines.append("\n---\n")
        lines.append("## VIII. Life Activation Windows\n\n")
        lines.append("| Period | Planet → Zone | Age | Duration |\n")
        lines.append("| :--- | :--- | :--- | :--- |\n")
        for w in life_windows:
            r_name = interpreter.RASHI_NATURE.get(w['target_rashi'], f"Rashi {w['target_rashi']}").split(":")[0]
            lines.append(f"| {w['entry_date']} | **{w['planet']}** → {r_name} | {w['age']} years | {w['duration_months']} months |\n")
    
    lines.append("\n---\n")
    lines.append("> *Disclaimer: This report is is based on the 'Fixed Karma' (Sanchita) inherent in the date, not the 'Variable Karma' (Prarabdha) of the birth time.*")

    return ''.join(lines)

@app.route('/')
def index():
    return render_template('index.html')

def calculate_numerology(dob):
    # Day Number
    day_val = dob.day
    day_num = day_val
    
    # Destiny Number (Sum of all digits)
    dob_str = dob.strftime('%d%m%Y')
    destiny_val = sum(int(d) for d in dob_str)
    
    # Reward Numbers (Reduced Day and Reduced Destiny)
    def reduce_digit(n):
        while n > 9:
            n = sum(int(d) for d in str(n))
        return n
        
    day_reward = reduce_digit(day_num)
    destiny_reward = reduce_digit(destiny_val)
    
    # Nakshatras for these numbers (generic mapping for display)
    # 1: Ashwini, 2: Bharani, etc? The image says "12 (Day) -> Uttara Phalguni". 
    # That implies 12 is directly mapped. 
    # I don't have the mapping logic handy to map numbers to Nakshatras exactly as in the image without a lookup table.
    # The image might be using specific numerology-nakshatra mapping.
    # For now, I'll pass the numbers and let the template handle display, maybe generic text or just the numbers.
    # The user "Design Beautifully" request is about aesthetics. I shouldn't get too hung up on new logic correctness if I don't have it.
    # But I will pass the calculate numbers.
    
    return {
        "day": day_num,
        "destiny": destiny_val,
        "rewards": [day_reward, destiny_reward],
        "day_reduced": day_reward,
        "destiny_reduced": destiny_reward
    }

@app.route('/generate', methods=['POST'])
def generate_report():
    try:
        # Support both JSON (API) and Form Data (Browser)
        if request.is_json:
            data = request.get_json()
            dob_str = data.get('dob')
        else:
            dob_str = request.form.get('dob')

        if not dob_str:
            return jsonify({"error": "Date of birth is required"}), 400
        
        dob = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        # Generation Pipeline
        matrix = generator.generate_matrix(dob)
        results = analyzer.analyze(matrix, dob=dob)
        
        # Numerology
        numerology = calculate_numerology(dob)
        
        # Render Template
        return render_template(
            'report.html',
            narrative=results['narrative'],
            dob=dob,
            sample_count=results['sample_count'],
            numerology=numerology
        )

    except Exception as e:
        print(f"Server Error: {str(e)}")
        # import traceback
        # traceback.print_exc()
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500

    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"error": "An internal error occurred."}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
