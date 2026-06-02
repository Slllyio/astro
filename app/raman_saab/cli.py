from __future__ import annotations
import argparse, dataclasses, json, sys
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData

def _parse(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="app.raman_saab", description="Raman Saab chart")
    ap.add_argument("--name", required=True); ap.add_argument("--date", required=True)   # YYYY-MM-DD
    ap.add_argument("--time", required=True)                                              # HH:MM
    ap.add_argument("--tz", type=float, required=True)
    ap.add_argument("--lat", type=float, required=True); ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--ayanamsa", default="raman", choices=["raman", "lahiri"])
    ap.add_argument("--format", default="json", choices=["json", "text"])
    return ap.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    a = _parse(argv)
    y, mo, d = (int(x) for x in a.date.split("-")); hh, mm = (int(x) for x in a.time.split(":"))
    birth = BirthData(a.name, y, mo, d, hh, mm, a.tz, a.lat, a.lon)
    chart = cast_chart(birth, ayanamsa=a.ayanamsa)
    payload = {
        "ayanamsa": chart.ayanamsa, "asc_sign": chart.asc_sign, "asc_lon": round(chart.asc_lon, 4),
        "planets": {n: {"lon": round(p.lon, 4), "sign": p.sign, "rasi_house": p.rasi_house,
                        "bhava": p.bhava, "navamsa_sign": p.navamsa_sign,
                        "retrograde": p.retrograde} for n, p in chart.planets.items()},
    }
    if a.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"Lagna: sign {chart.asc_sign} ({chart.asc_lon:.2f}°)  [ayanamsa={chart.ayanamsa}]")
        for n, p in chart.planets.items():
            print(f"  {n:8} {p.lon:7.2f}°  sign {p.sign:2}  bhava {p.bhava:2}  "
                  f"{'(R)' if p.retrograde else '   '}")
    return 0
