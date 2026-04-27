

import os
# Configuration for Temporal & Spatial Sampling Engine

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Temporal Segmentation: 24 intervals of 60 minutes = 24 hours (Optimized for Free Tier)
TIME_SLICES = 24
TIME_INTERVAL_MINUTES = 60

# Spatial Segmentation: 5 Major Anchor Locations in India (Optimized for Free Tier)
# Format: {"name": "Name", "lat": Latitude, "lon": Longitude}
ANCHOR_LOCATIONS = [
    {"name": "Srinagar", "lat": 34.0837, "lon": 74.7973, "region": "North"},
    {"name": "Bhuj", "lat": 23.2420, "lon": 69.6669, "region": "West"},
    {"name": "Guwahati", "lat": 26.1445, "lon": 91.7362, "region": "East"},
    {"name": "Kanyakumari", "lat": 8.0883, "lon": 77.5385, "region": "South"},
    {"name": "New Delhi", "lat": 28.6139, "lon": 77.2090, "region": "North"}
]

# Astrological Constants
HOUSES_COUNT = 12
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
KAKSHYA_ZONES_PER_RASHI = 8
KAKSHYA_DEGREES = 3.75 # 30 degrees / 8
KAKSHYA_RULERS = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna"]
