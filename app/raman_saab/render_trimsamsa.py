"""Text renderer for the Trimsāṁśa (D-30) health reading (`judges/trimsamsa_health_reading.py`).

ASCII-safe. Keeps the doctrinal split explicit: the core block is the AUTHORITATIVE health
picture (Raman's real single-chart method); the D-30 block is provenance-tagged corroboration.
NOT a medical statement — the caveats print with the reading.

Usage:
    from app.raman_saab.render_trimsamsa import to_text
    print(to_text(build_trimsamsa_health_reading(chart)))
"""
from __future__ import annotations

from app.raman_saab.judges.saptamsa_reading import Tagged
from app.raman_saab.judges.trimsamsa_health_reading import TrimsamsaHealthReading

_SIGN = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


def _tag(t: Tagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def to_text(reading: TrimsamsaHealthReading) -> str:
    c = reading.core
    ov = reading.overlay
    L: list[str] = []
    L.append("=" * 72)
    L.append("TRIMSAMSA (D-30) HEALTH READING  —  NOT A MEDICAL DIAGNOSIS")
    L.append("=" * 72)
    for n in reading.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append("-- RAMAN CORE (authoritative - his real single-chart method decides) --")
    L.append(f"  Lagna       : {_sign(c.lagna_sign)} (lord {c.lagna_lord} in house "
             f"{c.lagna_lord_house}, {c.lagna_lord_dignity}) - constitution")
    L.append(f"  Health (H1) : {c.health_verdict.upper()}")
    L.append(f"  Disease (H6): {c.disease_verdict.upper()}")
    L.append(f"  Longevity(H8): {c.longevity_verdict.upper()}   "
             f"(the engine defers lifespan; this is a lean, not a verdict)")
    bal = "APPLIES" if c.balarishta_applies else "does not apply"
    if c.balarishta_applies and c.balarishta_cancelled:
        bal += " but CANCELLED (antidote present)"
    L.append(f"  Balarishta  : {bal}")
    for r in c.balarishta_reasons:
        L.append(f"        - {r}")
    L.append(f"  Moon (mind) : house {c.moon_house}, {c.moon_dignity}"
             + (f"; afflicted by {', '.join(c.moon_afflictions)}" if c.moon_afflictions
                else "; no malefic affliction"))
    L.append(f"  Mercury     : house {c.mercury_house}, {c.mercury_dignity}"
             + (f"; afflicted by {', '.join(c.mercury_afflictions)}" if c.mercury_afflictions
                else "; no malefic affliction")
             + "   (nervous-system / intellect / speech karaka)")
    L.append("")
    L.append("-- D-30 OVERLAY (report-only corroboration) --")
    L.append(f"  D-30 lagna : {_sign(ov.lagna_sign)} (lord {ov.lagna_lord})"
             + (f", occupied by {', '.join(ov.lagna_occupants)}" if ov.lagna_occupants else ""))
    L.append(f"  D-30 6th   : {_sign(ov.sixth_sign)}    D-30 8th: {_sign(ov.eighth_sign)}")
    L.append(f"  Moon D-30  : {_sign(ov.moon_sign)} ({ov.moon_dignity})   "
             f"Mercury D-30: {_sign(ov.mercury_sign)} ({ov.mercury_dignity})")
    if ov.lagna_afflictions:
        for a in ov.lagna_afflictions:
            L.append(f"        - {_tag(a)}")
    else:
        L.append("        (no malefic on the D-30 lagna)")
    L.append("=" * 72)
    return "\n".join(L)
