"""Text renderer for the soul-destiny reading (`judges/soul_reading.py`).

Keeps the doctrinal split explicit: the Parashari CORE is authoritative; the Jaimini overlay and
nakshatra signature are provenance-tagged corroboration. Emits UTF-8 (reconfigure stdout when
piping to a console). NOT a fixed-fate statement — the caveats print with the reading.

Usage:
    from app.raman_saab.render_soul import to_text
    print(to_text(build_soul_reading(chart)))
"""
from __future__ import annotations

from app.raman_saab.judges.soul_reading import SoulReading, SoulTagged

_SIGN = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


def _tag(t: SoulTagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def to_text(reading: SoulReading) -> str:
    c = reading.core
    ov = reading.jaimini_overlay
    L: list[str] = []
    L.append("=" * 76)
    L.append("SOUL-DESTINY READING  —  a scripted-soul reading, NOT a fixed fate")
    L.append("=" * 76)
    for n in reading.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append("-- SOUL-PURPOSE (the scripted essence) --")
    L.append(f"  {reading.narrative}")
    L.append("")
    L.append("-- PARASHARI SOUL CORE (authoritative - Raman's own doctrine decides) --")
    for line in c.lines:
        L.append(f"  - {_tag(line)}")
    L.append("")
    L.append("-- JAIMINI SOUL-SCRIPT (report-only; citations experiment-unlocked) --")
    L.append(f"  Atmakaraka {ov.atmakaraka}  |  Karakamsa {_sign(ov.karakamsa_sign)}  |  "
             f"Arudha Lagna {_sign(ov.arudha_lagna_sign)}")
    L.append(f"  Ishta-Devata (moksha-deity): {ov.ishta_devata}")
    for line in ov.lines:
        L.append(f"  - {_tag(line)}")
    L.append("")
    L.append("-- NAKSHATRA SOUL-SIGNATURE (deity classical / archetype editorial) --")
    for e in reading.nakshatra_signature.entries:
        L.append(f"  - {_tag(e)}")
    L.append("=" * 76)
    return "\n".join(L)
