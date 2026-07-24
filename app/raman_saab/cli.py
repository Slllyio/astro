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
    ap.add_argument("--format", default="json",
                    choices=["json", "text", "reading", "markdown", "synthesis", "report", "html"])
    ap.add_argument("--at")                # YYYY-MM-DD: Dasha snapshot (what is active on this date)
    ap.add_argument("--timeline", action="store_true")   # Dasha-by-Dasha life-narrative
    ap.add_argument("--bhuktis", action="store_true")    # expand the timeline to MD->Bhukti (needs --timeline)
    args = ap.parse_args(argv)
    if args.bhuktis and not args.timeline:
        ap.error("--bhuktis requires --timeline")
    return args

def main(argv: list[str] | None = None) -> int:
    a = _parse(argv)
    y, mo, d = (int(x) for x in a.date.split("-")); hh, mm = (int(x) for x in a.time.split(":"))
    birth = BirthData(a.name, y, mo, d, hh, mm, a.tz, a.lat, a.lon)
    if a.format == "synthesis":                            # unified per-matter reading (Raman-style)
        from app.raman_saab.synthesis import synthesize, to_text
        on = tuple(int(x) for x in a.at.split("-")) if a.at else None
        print(to_text(synthesize(birth, on=on, ayanamsa=a.ayanamsa)))
        return 0
    if a.format in ("report", "html"):                     # full detailed report + honesty overlay
        from app.raman_saab.detailed_report import build_detailed_report, to_markdown
        on = tuple(int(x) for x in a.at.split("-")) if a.at else None
        report = build_detailed_report(birth, on=on, ayanamsa=a.ayanamsa)
        if a.format == "html":
            from app.raman_saab.report_html import standalone_html
            try:
                import sys
                sys.stdout.reconfigure(encoding="utf-8")   # HTML is UTF-8 (IAST diacritics)
            except Exception:
                pass
            print(standalone_html(report))
        else:
            print(to_markdown(report))
        return 0
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
        print(f"Lagna: sign {chart.asc_sign} ({chart.asc_lon:.2f} deg)  [ayanamsa={chart.ayanamsa}]")
        for n, p in chart.planets.items():
            print(f"  {n:8} {p.lon:7.2f} deg  sign {p.sign:2}  bhava {p.bhava:2}  "
                  f"{'(R)' if p.retrograde else '   '}")
    return 0
