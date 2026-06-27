from __future__ import annotations
import argparse, json
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.proforma import read_chart
from app.raman_saab import render

def _parse(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="app.raman_saab", description="Raman Saab chart")
    ap.add_argument("--name", required=True); ap.add_argument("--date", required=True)   # YYYY-MM-DD
    ap.add_argument("--time", required=True)                                              # HH:MM
    ap.add_argument("--tz", type=float, required=True)
    ap.add_argument("--lat", type=float, required=True); ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--ayanamsa", default="lahiri", choices=["raman", "lahiri"])
    ap.add_argument("--format", default="json", choices=["json", "text", "reading", "markdown"])
    ap.add_argument("--at")                # YYYY-MM-DD: Dasha snapshot (what is active on this date)
    ap.add_argument("--timeline", action="store_true")   # Dasha-by-Dasha life-narrative
    ap.add_argument("--bhuktis", action="store_true")    # expand the timeline to MD->Bhukti
    return ap.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    a = _parse(argv)
    y, mo, d = (int(x) for x in a.date.split("-")); hh, mm = (int(x) for x in a.time.split(":"))
    birth = BirthData(a.name, y, mo, d, hh, mm, a.tz, a.lat, a.lon)
    if a.at or a.timeline:                                  # Dasha-driven prioritized reading
        from app.raman_saab import reading_timeline as rt
        md = a.format == "markdown"
        if a.timeline:
            tl = rt.reading_timeline(birth, ayanamsa=a.ayanamsa, expand_bhuktis=a.bhuktis)
            print(render.timeline_to_markdown(tl) if md else render.timeline_to_text(tl))
        else:
            ay, am, ad = (int(x) for x in a.at.split("-"))
            from app.raman_saab.primitives.vimshottari import date_to_jd
            snap = rt.read_chart_on_date(birth, date_to_jd(ay, am, ad), ayanamsa=a.ayanamsa)
            print(render.snapshot_to_markdown(snap) if md else render.snapshot_to_text(snap))
        return 0
    if a.format in ("reading", "markdown"):                 # full house-by-house judgment
        reading = read_chart(birth, ayanamsa=a.ayanamsa)
        print(render.to_markdown(reading) if a.format == "markdown" else render.to_text(reading))
        return 0
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
