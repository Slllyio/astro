"""Render a `RamanReading` as a deterministic, book-style worksheet (plain text /
markdown). ASCII-safe (no characters outside CP1252) so it prints on any console.
"""
from __future__ import annotations

from app.raman_saab.judges.house_judge import HouseVerdict
from app.raman_saab.proforma import RamanReading

_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")

_HOUSE_NAMES = {
    1: "Self / Body", 2: "Wealth / Family", 3: "Siblings / Courage", 4: "Mother / Home",
    5: "Children / Intellect", 6: "Enemies / Health / Debt", 7: "Marriage / Partner",
    8: "Longevity / Death", 9: "Fortune / Father / Dharma", 10: "Career / Karma",
    11: "Gains / Income", 12: "Loss / Expenditure / Moksha"}

_FLAG = {True: "strong", False: "weak", None: "n/a"}

# Rule text is transcribed from the corpus and may carry unicode punctuation; normalise to
# ASCII so the worksheet prints on any console (incl. Windows CP1252).
_REPL = {"→": "->", "←": "<-", "—": "-", "–": "-", "‘": "'",
         "’": "'", "“": '"', "”": '"', "…": "...", "°": " deg",
         "×": "x", "½": "1/2", "¾": "3/4", "¼": "1/4"}


def _ascii(s: str) -> str:
    for k, v in _REPL.items():
        s = s.replace(k, v)
    return s.encode("ascii", "replace").decode("ascii")


def _house_block(hv: HouseVerdict) -> list[str]:
    lines = [f"House {hv.house} - {_HOUSE_NAMES[hv.house]}: {hv.verdict.upper()}",
             f"  pillars: lord {hv.lord} ({_FLAG[hv.lord_strong]}), "
             f"karaka {hv.karaka} ({_FLAG[hv.karaka_strong]})"]
    evidence = list(hv.benefic) + list(hv.malefic) + list(hv.neutral)
    if not evidence:
        lines.append("  (no rule fired - insufficient evidence)")
    for fr in evidence:
        lines.append(f"  - [{fr.branch}] {fr.text}  ({fr.rule.source.work}:{fr.rule.source.line})")
    return lines


def to_text(reading: RamanReading) -> str:
    b = reading.birth
    out = [
        "=" * 72,
        f"RAMAN SAAB - House-by-House Reading for {b.name}",
        f"Born {b.year:04d}-{b.month:02d}-{b.day:02d} {b.hour:02d}:{b.minute:02d} "
        f"(tz {b.tz_offset:+}), lat {b.latitude}, lon {b.longitude}",
        f"Lagna: {_SIGNS[reading.asc_sign - 1]} ({reading.asc_lon:.2f} deg)  "
        f"[ayanamsa = {reading.ayanamsa}]",
        "=" * 72,
        "",
    ]
    for hv in reading.houses:
        out += _house_block(hv)
        out.append("")
    out.append("Every line cites a verse of B.V. Raman's *How to Judge a Horoscope*.")
    return _ascii("\n".join(out))


def to_markdown(reading: RamanReading) -> str:
    b = reading.birth
    out = [f"# Raman Saab reading - {b.name}",
           f"**Lagna:** {_SIGNS[reading.asc_sign - 1]} ({reading.asc_lon:.2f} deg) - "
           f"ayanamsa {reading.ayanamsa}", ""]
    for hv in reading.houses:
        out.append(f"## House {hv.house} - {_HOUSE_NAMES[hv.house]}: {hv.verdict}")
        out.append(f"*Lord {hv.lord} ({_FLAG[hv.lord_strong]}), "
                   f"Karaka {hv.karaka} ({_FLAG[hv.karaka_strong]})*")
        for fr in list(hv.benefic) + list(hv.malefic) + list(hv.neutral):
            out.append(f"- **[{fr.branch}]** {fr.text} "
                       f"(`{fr.rule.source.work}:{fr.rule.source.line}`)")
        out.append("")
    return _ascii("\n".join(out))
