"""Text renderer for the general-varga reading (`judges/general_varga_reading.py`).

REPORT-ONLY strength/character snapshot for a matterless varga. UTF-8.
"""
from __future__ import annotations

from app.raman_saab.judges.general_varga_reading import GeneralVargaReading
from app.raman_saab.judges.saptamsa_reading import Tagged

_SIGN = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


def _tag(t: Tagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def to_text(r: GeneralVargaReading) -> str:
    L: list[str] = []
    L.append("=" * 72)
    L.append(f"D-{r.varga} {r.varga_name}  —  general strength / character reading")
    L.append("=" * 72)
    for n in r.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append(f"  lagna : {_sign(r.lagna_sign)} (lord {r.lagna_lord}, {r.lagna_lord_dignity} in "
             f"this varga)")
    L.append(f"  on the lagna : "
             + (f"benefics {', '.join(r.benefics_on_lagna) or '-'}; "
                f"malefics {', '.join(r.malefics_on_lagna) or '-'}"))
    L.append(f"  strong here (exalt/own): {', '.join(r.strong_planets) or '(none)'}")
    L.append(f"  weak here (debilitated): {', '.join(r.weak_planets) or '(none)'}")
    L.append("=" * 72)
    return "\n".join(L)
