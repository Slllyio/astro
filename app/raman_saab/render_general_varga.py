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


#: The one domain word each general varga's report header already names (the _DIVISIONAL
#: labels: "D-27 Strength", "D-40 Auspiciousness", "D-45 Character", "D-60 Totality") —
#: Wave-2 (2026-08-18): the body previously named the domain in the header and never spoke
#: to it; the domain sentence below ties the varga-lagna-lord's condition to this word.
_DOMAIN_WORD = {27: "general strength", 40: "auspiciousness",
                45: "character and conduct", 60: "totality (the accumulated karma)"}

#: Varga-lagna-lord dignity -> the classical seating phrase + the domain lean word. Pure
#: restatement of the dignity the lagna line above already prints — no new judgment scale.
_DIGNITY_READ = {
    "exalt": ("exalted", "classically well-seated"),
    "own": ("in own sign", "classically well-seated"),
    "friend": ("in a friend's sign", "supported"),
    "neutral": ("in a neutral sign", "evenly placed"),
    "enemy": ("in an enemy's sign", "under strain"),
    "debil": ("debilitated", "undermined"),
}


def _domain_sentence(r: GeneralVargaReading) -> str:
    """One domain-verdict sentence tying the varga lagna-lord's condition (already printed in
    the lagna line) to the domain word the section header names, with the module's existing
    HPA-11 cite. Indication idiom only; report-only like everything in this renderer."""
    seat, lean = _DIGNITY_READ.get(r.lagna_lord_dignity, ("placed", "evenly placed"))
    cite = next((n.cite for n in r.notes if n.cite), "HPA-11")
    return (f"  domain reading : with the varga lagna lord {r.lagna_lord} {seat} in this "
            f"varga, the {_DOMAIN_WORD.get(r.varga, 'general strength')} this D-{r.varga} "
            f"maps reads as {lean} here ({cite}) - a report-only re-read of the lagna line "
            f"above; no D1 verdict is touched.")


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
    L.append(_domain_sentence(r))
    L.append("=" * 72)
    return "\n".join(L)
