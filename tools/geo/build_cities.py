"""Build the bundled city→coordinates dataset for the report's birth-place picker.

The detailed-report book (`app/medini/templates/report.html`) lets a user pick a CITY / TOWN
instead of typing raw latitude/longitude. This script is the curated source of truth for that
list: India comprehensively (all state/UT capitals + metros + many well-known cities & district
HQs + a few pilgrimage/astro-relevant towns; tz +5.5 throughout) plus major world cities with
their STANDARD (non-DST) UTC offset. City-center coordinates (±~0.1°, a few km) are ample for a
birth chart — the ascendant is governed by birth *time*, not sub-km location — and the form keeps
lat/lon editable so any place off this list can still be entered by hand.

Usage:
    py -3.12 tools/geo/build_cities.py
    # writes app/templates/static/data/cities.json  (served at /static/data/cities.json)
"""
from __future__ import annotations

import json
from pathlib import Path

# India — (name, state/UT, lat, lon); tz is +5.5 for all.
_INDIA: tuple[tuple[str, str, float, float], ...] = (
    ("New Delhi", "Delhi", 28.61, 77.21), ("Delhi", "Delhi", 28.66, 77.23),
    ("Mumbai", "Maharashtra", 19.08, 72.88), ("Navi Mumbai", "Maharashtra", 19.03, 73.03),
    ("Thane", "Maharashtra", 19.22, 72.98), ("Kalyan", "Maharashtra", 19.24, 73.13),
    ("Pune", "Maharashtra", 18.52, 73.86), ("Nashik", "Maharashtra", 20.00, 73.78),
    ("Nagpur", "Maharashtra", 21.15, 79.09), ("Aurangabad", "Maharashtra", 19.88, 75.34),
    ("Solapur", "Maharashtra", 17.66, 75.91), ("Kolhapur", "Maharashtra", 16.70, 74.24),
    ("Sangli", "Maharashtra", 16.85, 74.58), ("Satara", "Maharashtra", 17.69, 74.02),
    ("Ahmednagar", "Maharashtra", 19.09, 74.75), ("Jalgaon", "Maharashtra", 21.01, 75.56),
    ("Akola", "Maharashtra", 20.71, 77.00), ("Amravati", "Maharashtra", 20.93, 77.75),
    ("Latur", "Maharashtra", 18.40, 76.58), ("Nanded", "Maharashtra", 19.15, 77.32),
    ("Kolkata", "West Bengal", 22.57, 88.36), ("Howrah", "West Bengal", 22.59, 88.31),
    ("Siliguri", "West Bengal", 26.73, 88.40), ("Durgapur", "West Bengal", 23.55, 87.32),
    ("Asansol", "West Bengal", 23.68, 86.98), ("Kharagpur", "West Bengal", 22.35, 87.32),
    ("Bardhaman", "West Bengal", 23.25, 87.86), ("Malda", "West Bengal", 25.01, 88.14),
    ("Chennai", "Tamil Nadu", 13.08, 80.27), ("Coimbatore", "Tamil Nadu", 11.02, 76.97),
    ("Madurai", "Tamil Nadu", 9.93, 78.12), ("Salem", "Tamil Nadu", 11.66, 78.15),
    ("Tiruchirappalli", "Tamil Nadu", 10.79, 78.70), ("Tirunelveli", "Tamil Nadu", 8.71, 77.76),
    ("Vellore", "Tamil Nadu", 12.92, 79.13), ("Erode", "Tamil Nadu", 11.34, 77.72),
    ("Thanjavur", "Tamil Nadu", 10.79, 79.14), ("Kanchipuram", "Tamil Nadu", 12.84, 79.70),
    ("Dindigul", "Tamil Nadu", 10.36, 77.98), ("Nagercoil", "Tamil Nadu", 8.18, 77.43),
    ("Bengaluru", "Karnataka", 12.97, 77.59), ("Mysuru", "Karnataka", 12.30, 76.64),
    ("Mangaluru", "Karnataka", 12.91, 74.86), ("Hubli", "Karnataka", 15.36, 75.12),
    ("Belagavi", "Karnataka", 15.85, 74.50), ("Kalaburagi", "Karnataka", 17.33, 76.83),
    ("Davanagere", "Karnataka", 14.47, 75.92), ("Ballari", "Karnataka", 15.14, 76.92),
    ("Shivamogga", "Karnataka", 13.93, 75.57), ("Udupi", "Karnataka", 13.34, 74.75),
    ("Hyderabad", "Telangana", 17.38, 78.49), ("Warangal", "Telangana", 17.97, 79.60),
    ("Nizamabad", "Telangana", 18.67, 78.10), ("Karimnagar", "Telangana", 18.44, 79.13),
    ("Khammam", "Telangana", 17.25, 80.15),
    ("Visakhapatnam", "Andhra Pradesh", 17.69, 83.22), ("Vijayawada", "Andhra Pradesh", 16.51, 80.65),
    ("Guntur", "Andhra Pradesh", 16.31, 80.44), ("Nellore", "Andhra Pradesh", 14.44, 79.99),
    ("Tirupati", "Andhra Pradesh", 13.63, 79.42), ("Rajahmundry", "Andhra Pradesh", 17.00, 81.80),
    ("Kakinada", "Andhra Pradesh", 16.99, 82.25), ("Kurnool", "Andhra Pradesh", 15.83, 78.04),
    ("Anantapur", "Andhra Pradesh", 14.68, 77.60), ("Kadapa", "Andhra Pradesh", 14.47, 78.82),
    ("Ahmedabad", "Gujarat", 23.03, 72.58), ("Surat", "Gujarat", 21.17, 72.83),
    ("Vadodara", "Gujarat", 22.31, 73.18), ("Rajkot", "Gujarat", 22.30, 70.80),
    ("Bhavnagar", "Gujarat", 21.76, 72.15), ("Jamnagar", "Gujarat", 22.47, 70.06),
    ("Junagadh", "Gujarat", 21.52, 70.46), ("Gandhinagar", "Gujarat", 23.22, 72.65),
    ("Anand", "Gujarat", 22.56, 72.95), ("Bharuch", "Gujarat", 21.70, 72.99),
    ("Navsari", "Gujarat", 20.95, 72.92), ("Porbandar", "Gujarat", 21.64, 69.61),
    ("Dwarka", "Gujarat", 22.24, 68.97),
    ("Jaipur", "Rajasthan", 26.91, 75.79), ("Jodhpur", "Rajasthan", 26.24, 73.02),
    ("Udaipur", "Rajasthan", 24.58, 73.71), ("Kota", "Rajasthan", 25.21, 75.86),
    ("Ajmer", "Rajasthan", 26.45, 74.64), ("Bikaner", "Rajasthan", 28.02, 73.31),
    ("Bhilwara", "Rajasthan", 25.35, 74.64), ("Alwar", "Rajasthan", 27.55, 76.63),
    ("Sikar", "Rajasthan", 27.61, 75.14), ("Bharatpur", "Rajasthan", 27.22, 77.49),
    ("Sri Ganganagar", "Rajasthan", 29.92, 73.88), ("Pushkar", "Rajasthan", 26.49, 74.55),
    ("Lucknow", "Uttar Pradesh", 26.85, 80.95), ("Kanpur", "Uttar Pradesh", 26.45, 80.33),
    ("Agra", "Uttar Pradesh", 27.18, 78.01), ("Varanasi", "Uttar Pradesh", 25.32, 82.97),
    ("Prayagraj", "Uttar Pradesh", 25.44, 81.85), ("Meerut", "Uttar Pradesh", 28.98, 77.71),
    ("Ghaziabad", "Uttar Pradesh", 28.67, 77.45), ("Noida", "Uttar Pradesh", 28.54, 77.39),
    ("Aligarh", "Uttar Pradesh", 27.88, 78.08), ("Bareilly", "Uttar Pradesh", 28.35, 79.42),
    ("Moradabad", "Uttar Pradesh", 28.84, 78.77), ("Saharanpur", "Uttar Pradesh", 29.97, 77.55),
    ("Gorakhpur", "Uttar Pradesh", 26.76, 83.37), ("Jhansi", "Uttar Pradesh", 25.45, 78.57),
    ("Mathura", "Uttar Pradesh", 27.49, 77.67), ("Ayodhya", "Uttar Pradesh", 26.80, 82.20),
    ("Firozabad", "Uttar Pradesh", 27.16, 78.40), ("Mainpuri", "Uttar Pradesh", 27.23, 79.03),
    ("Rae Bareli", "Uttar Pradesh", 26.22, 81.24), ("Sultanpur", "Uttar Pradesh", 26.26, 82.07),
    ("Gwalior", "Madhya Pradesh", 26.22, 78.18), ("Indore", "Madhya Pradesh", 22.72, 75.86),
    ("Bhopal", "Madhya Pradesh", 23.26, 77.41), ("Jabalpur", "Madhya Pradesh", 23.18, 79.99),
    ("Ujjain", "Madhya Pradesh", 23.18, 75.78), ("Sagar", "Madhya Pradesh", 23.84, 78.74),
    ("Ratlam", "Madhya Pradesh", 23.33, 75.04), ("Satna", "Madhya Pradesh", 24.60, 80.83),
    ("Rewa", "Madhya Pradesh", 24.53, 81.30),
    ("Patna", "Bihar", 25.59, 85.14), ("Gaya", "Bihar", 24.80, 85.00),
    ("Muzaffarpur", "Bihar", 26.12, 85.39), ("Bhagalpur", "Bihar", 25.24, 87.00),
    ("Darbhanga", "Bihar", 26.15, 85.90),
    ("Ranchi", "Jharkhand", 23.34, 85.31), ("Jamshedpur", "Jharkhand", 22.80, 86.20),
    ("Dhanbad", "Jharkhand", 23.80, 86.43), ("Bokaro", "Jharkhand", 23.67, 86.15),
    ("Bhubaneswar", "Odisha", 20.30, 85.82), ("Cuttack", "Odisha", 20.46, 85.88),
    ("Rourkela", "Odisha", 22.26, 84.85), ("Sambalpur", "Odisha", 21.47, 83.97),
    ("Berhampur", "Odisha", 19.31, 84.79), ("Puri", "Odisha", 19.81, 85.83),
    ("Raipur", "Chhattisgarh", 21.25, 81.63), ("Bhilai", "Chhattisgarh", 21.21, 81.38),
    ("Bilaspur", "Chhattisgarh", 22.08, 82.15), ("Korba", "Chhattisgarh", 22.35, 82.68),
    ("Durg", "Chhattisgarh", 21.19, 81.28),
    ("Thiruvananthapuram", "Kerala", 8.52, 76.94), ("Kochi", "Kerala", 9.93, 76.27),
    ("Kozhikode", "Kerala", 11.25, 75.78), ("Thrissur", "Kerala", 10.53, 76.21),
    ("Kollam", "Kerala", 8.89, 76.61), ("Kottayam", "Kerala", 9.59, 76.52),
    ("Palakkad", "Kerala", 10.79, 76.65), ("Kannur", "Kerala", 11.87, 75.37),
    ("Guruvayur", "Kerala", 10.59, 76.04),
    ("Chandigarh", "Chandigarh", 30.73, 76.78), ("Ludhiana", "Punjab", 30.90, 75.86),
    ("Amritsar", "Punjab", 31.63, 74.87), ("Jalandhar", "Punjab", 31.33, 75.58),
    ("Patiala", "Punjab", 30.34, 76.39), ("Bathinda", "Punjab", 30.21, 74.94),
    ("Mohali", "Punjab", 30.70, 76.72), ("Pathankot", "Punjab", 32.27, 75.65),
    ("Gurugram", "Haryana", 28.46, 77.03), ("Faridabad", "Haryana", 28.41, 77.31),
    ("Panipat", "Haryana", 29.39, 76.97), ("Karnal", "Haryana", 29.69, 76.99),
    ("Hisar", "Haryana", 29.15, 75.72), ("Rohtak", "Haryana", 28.90, 76.61),
    ("Ambala", "Haryana", 30.38, 76.78), ("Kurukshetra", "Haryana", 29.97, 76.88),
    ("Dehradun", "Uttarakhand", 30.32, 78.03), ("Haridwar", "Uttarakhand", 29.95, 78.16),
    ("Rishikesh", "Uttarakhand", 30.09, 78.27), ("Nainital", "Uttarakhand", 29.38, 79.46),
    ("Haldwani", "Uttarakhand", 29.22, 79.51), ("Roorkee", "Uttarakhand", 29.87, 77.89),
    ("Shimla", "Himachal Pradesh", 31.10, 77.17), ("Dharamshala", "Himachal Pradesh", 32.22, 76.32),
    ("Mandi", "Himachal Pradesh", 31.71, 76.93), ("Solan", "Himachal Pradesh", 30.91, 77.10),
    ("Srinagar", "Jammu & Kashmir", 34.08, 74.80), ("Jammu", "Jammu & Kashmir", 32.73, 74.87),
    ("Leh", "Ladakh", 34.16, 77.58),
    ("Guwahati", "Assam", 26.14, 91.74), ("Dibrugarh", "Assam", 27.47, 94.91),
    ("Silchar", "Assam", 24.83, 92.78), ("Jorhat", "Assam", 26.75, 94.22),
    ("Shillong", "Meghalaya", 25.58, 91.89), ("Imphal", "Manipur", 24.82, 93.94),
    ("Aizawl", "Mizoram", 23.73, 92.72), ("Kohima", "Nagaland", 25.67, 94.11),
    ("Itanagar", "Arunachal Pradesh", 27.10, 93.62), ("Agartala", "Tripura", 23.83, 91.28),
    ("Gangtok", "Sikkim", 27.34, 88.61),
    ("Panaji", "Goa", 15.49, 73.83), ("Margao", "Goa", 15.27, 73.96),
    ("Puducherry", "Puducherry", 11.93, 79.83), ("Port Blair", "Andaman & Nicobar", 11.62, 92.73),
)

# World — (name, country, lat, lon, standard UTC offset in hours).
_WORLD: tuple[tuple[str, str, float, float, float], ...] = (
    ("London", "United Kingdom", 51.51, -0.13, 0.0),
    ("New York", "United States", 40.71, -74.01, -5.0),
    ("Washington", "United States", 38.90, -77.04, -5.0),
    ("Chicago", "United States", 41.88, -87.63, -6.0),
    ("Houston", "United States", 29.76, -95.37, -6.0),
    ("Los Angeles", "United States", 34.05, -118.24, -8.0),
    ("San Francisco", "United States", 37.77, -122.42, -8.0),
    ("Seattle", "United States", 47.61, -122.33, -8.0),
    ("Boston", "United States", 42.36, -71.06, -5.0),
    ("Toronto", "Canada", 43.65, -79.38, -5.0), ("Vancouver", "Canada", 49.28, -123.12, -8.0),
    ("Mexico City", "Mexico", 19.43, -99.13, -6.0),
    ("Sao Paulo", "Brazil", -23.55, -46.63, -3.0), ("Buenos Aires", "Argentina", -34.60, -58.38, -3.0),
    ("Dubai", "UAE", 25.20, 55.27, 4.0), ("Abu Dhabi", "UAE", 24.45, 54.38, 4.0),
    ("Doha", "Qatar", 25.29, 51.53, 3.0), ("Kuwait City", "Kuwait", 29.38, 47.99, 3.0),
    ("Riyadh", "Saudi Arabia", 24.71, 46.68, 3.0), ("Jeddah", "Saudi Arabia", 21.49, 39.19, 3.0),
    ("Muscat", "Oman", 23.59, 58.41, 4.0), ("Manama", "Bahrain", 26.23, 50.59, 3.0),
    ("Tehran", "Iran", 35.69, 51.39, 3.5), ("Kabul", "Afghanistan", 34.53, 69.17, 4.5),
    ("Karachi", "Pakistan", 24.86, 67.01, 5.0), ("Lahore", "Pakistan", 31.55, 74.34, 5.0),
    ("Islamabad", "Pakistan", 33.68, 73.05, 5.0),
    ("Kathmandu", "Nepal", 27.72, 85.32, 5.75), ("Colombo", "Sri Lanka", 6.93, 79.85, 5.5),
    ("Dhaka", "Bangladesh", 23.81, 90.41, 6.0), ("Thimphu", "Bhutan", 27.47, 89.64, 6.0),
    ("Yangon", "Myanmar", 16.87, 96.20, 6.5), ("Bangkok", "Thailand", 13.76, 100.50, 7.0),
    ("Singapore", "Singapore", 1.35, 103.82, 8.0), ("Kuala Lumpur", "Malaysia", 3.14, 101.69, 8.0),
    ("Jakarta", "Indonesia", -6.21, 106.85, 7.0), ("Manila", "Philippines", 14.60, 120.98, 8.0),
    ("Ho Chi Minh City", "Vietnam", 10.82, 106.63, 7.0), ("Hong Kong", "Hong Kong", 22.32, 114.17, 8.0),
    ("Beijing", "China", 39.90, 116.41, 8.0), ("Shanghai", "China", 31.23, 121.47, 8.0),
    ("Tokyo", "Japan", 35.68, 139.65, 9.0), ("Osaka", "Japan", 34.69, 135.50, 9.0),
    ("Seoul", "South Korea", 37.57, 126.98, 9.0),
    ("Sydney", "Australia", -33.87, 151.21, 10.0), ("Melbourne", "Australia", -37.81, 144.96, 10.0),
    ("Perth", "Australia", -31.95, 115.86, 8.0), ("Auckland", "New Zealand", -36.85, 174.76, 12.0),
    ("Paris", "France", 48.86, 2.35, 1.0), ("Berlin", "Germany", 52.52, 13.40, 1.0),
    ("Frankfurt", "Germany", 50.11, 8.68, 1.0), ("Amsterdam", "Netherlands", 52.37, 4.90, 1.0),
    ("Brussels", "Belgium", 50.85, 4.35, 1.0), ("Rome", "Italy", 41.90, 12.50, 1.0),
    ("Madrid", "Spain", 40.42, -3.70, 1.0), ("Zurich", "Switzerland", 47.37, 8.54, 1.0),
    ("Vienna", "Austria", 48.21, 16.37, 1.0), ("Stockholm", "Sweden", 59.33, 18.07, 1.0),
    ("Moscow", "Russia", 55.76, 37.62, 3.0), ("Istanbul", "Turkey", 41.01, 28.98, 3.0),
    ("Cairo", "Egypt", 30.04, 31.24, 2.0), ("Nairobi", "Kenya", -1.29, 36.82, 3.0),
    ("Johannesburg", "South Africa", -26.20, 28.05, 2.0), ("Lagos", "Nigeria", 6.52, 3.38, 1.0),
    ("Port Louis", "Mauritius", -20.16, 57.50, 4.0), ("Suva", "Fiji", -18.14, 178.44, 12.0),
)


def build() -> list[dict]:
    out: list[dict] = []
    for n, a, lat, lon in _INDIA:
        out.append({"n": n, "a": a + ", India", "lat": lat, "lon": lon, "tz": 5.5})
    for n, a, lat, lon, tz in _WORLD:
        out.append({"n": n, "a": a, "lat": lat, "lon": lon, "tz": tz})
    out.sort(key=lambda c: c["n"])
    return out


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    dest = repo / "app" / "templates" / "static" / "geo" / "cities.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = build()
    dest.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {len(data)} cities -> {dest}")


if __name__ == "__main__":
    main()
