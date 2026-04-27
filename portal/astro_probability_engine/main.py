
import datetime
import json
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from astrology.real_service import SkyfieldAstrologyService
from engine.generator import MatrixGenerator
from engine.purifier import ChartPurifier
from engine.analyzer import MatrixAnalyzer

def main():
    print("Initializing Astro Probability Engine...")
    
    # 1. Setup
    # service = MockAstrologyService()
    service = SkyfieldAstrologyService()
    generator = MatrixGenerator(service)
    purifier = ChartPurifier()
    analyzer = MatrixAnalyzer()
    
    # 2. Input
    dob = datetime.date(1989, 10, 12) # Sample DOB
    print(f"Processing for DOB: {dob}")
    
    # 3. Generate Matrix
    print("Phase 1: Generating Matrix (96 Slices x 20 Locations)...")
    matrix = generator.generate_matrix(dob)
    print(f"Generated {len(matrix)} charts.")
    
    # 4. Purify
    print("Phase 2: Purifying Charts (Shodhana)...")
    purifier.process_matrix(matrix)
    
    # 5. Analyze
    print("Phase 3 & 4: Analyzing & Overlaying...")
    results = analyzer.analyze(matrix, dob=dob)
    
    # 6. Output
    print("Phase 5: Final Findings:")
    print(json.dumps(results, indent=2, default=str))

if __name__ == "__main__":
    main()
