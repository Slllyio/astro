"""Render a `RamanReading` as a deterministic, book-style worksheet (plain text /
markdown). ASCII-safe (no characters outside CP1252) so it prints on any console.
"""
from __future__ import annotations

from app.raman_saab.judges.house_template import HouseProforma
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
         "×": "x", "½": "1/2", "¾": "3/4", "¼": "1/4",
         "·": "-", "±": "+-"}

# Decorative emoji (the plain-terms avastha analogies) fold to nothing rather than "?"
# mojibake; the emoji+space form first so no stray double space is left behind, and the
# bare VS-16 selector last so any emoji already stripped leaves no invisible residue.
for _e in ("⚠️", "⚠", "❌", "🌤", "🌫", "💪", "🔥", "😌", "🙂"):
    _REPL[_e + " "] = ""
    _REPL[_e] = ""
_REPL["️"] = ""
del _e


def _ascii(s: str) -> str:
    for k, v in _REPL.items():
        s = s.replace(k, v)
    return s.encode("ascii", "replace").decode("ascii")


# Metadata keys surfaced in the per-house "notes" block (un-stranded from the modern judge:
# graded degree, yoga modulations, ayurdaya span, beeja/kshetra fertility, drekkana cause,
# and the Dasha event-timing — death_window / active_periods).
_NOTE_LABELS = {
    "ayurdaya": "longevity span", "death_window": "death-prone Dasha", "active_periods": "active Dasha",
    "beeja_kshetra": "fertility sphutas", "drekkana22_lord": "22nd-drekkana lord",
    "decanate_cause": "cause-of-end decanate", "marital_bond": "marital bond"}


def _house_block(p: HouseProforma) -> list[str]:
    hv = p.as_house_verdict()
    lines = [f"House {hv.house} - {_HOUSE_NAMES[hv.house]}: {hv.verdict.upper()}",
             f"  pillars: lord {hv.lord} ({_FLAG[hv.lord_strong]}), "
             f"karaka {hv.karaka} ({_FLAG[hv.karaka_strong]})"]
    evidence = list(hv.benefic) + list(hv.malefic) + list(hv.neutral)
    if not evidence:
        lines.append("  (no rule fired - insufficient evidence)")
    for fr in evidence:
        lines.append(f"  - [{fr.branch}] {fr.text}  ({fr.rule.source.work}:{fr.rule.source.line})")
    for key, val in p.metadata:
        lines.append(f"  * {_NOTE_LABELS.get(key, key)}: {val}")
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
    for p in reading.proformas:
        out += _house_block(p)
        out.append("")
    out.append("Every line cites a verse of B.V. Raman's *How to Judge a Horoscope*.")
    return _ascii("\n".join(out))


def to_markdown(reading: RamanReading) -> str:
    b = reading.birth
    out = [f"# Raman Saab reading - {b.name}",
           f"**Lagna:** {_SIGNS[reading.asc_sign - 1]} ({reading.asc_lon:.2f} deg) - "
           f"ayanamsa {reading.ayanamsa}", ""]
    for p in reading.proformas:
        hv = p.as_house_verdict()
        out.append(f"## House {hv.house} - {_HOUSE_NAMES[hv.house]}: {hv.verdict}")
        out.append(f"*Lord {hv.lord} ({_FLAG[hv.lord_strong]}), "
                   f"Karaka {hv.karaka} ({_FLAG[hv.karaka_strong]})*")
        for fr in list(hv.benefic) + list(hv.malefic) + list(hv.neutral):
            out.append(f"- **[{fr.branch}]** {fr.text} "
                       f"(`{fr.rule.source.work}:{fr.rule.source.line}`)")
        for key, val in p.metadata:
            out.append(f"- _{_NOTE_LABELS.get(key, key)}:_ {val}")
        out.append("")
    return _ascii("\n".join(out))


# ---------------------------------------------------------------------------
# Dasha-driven (temporally-prioritized) reading — the snapshot + life-narrative.
# These build their OWN blocks (never _house_block) and surface no per-matter
# `active_periods` note, so they don't double up with the static all-house reading.
# ---------------------------------------------------------------------------

def _jd_to_date(jd: float) -> str:
    import swisseph as swe
    y, m, d, _h = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _activates_clause(a) -> str:
    """'activated by MD Saturn (well) AND Bhukti Mercury (well)' — only the lord(s) that fire."""
    parts: list[str] = []
    if a.md_activates:
        parts.append(f"MD {a.md_lord} ({a.md_quality.tag})")
    if a.antar_activates and a.antar_lord is not None and a.antar_quality is not None:
        parts.append(f"Bhukti {a.antar_lord} ({a.antar_quality.tag})")
    return "activated by " + " AND ".join(parts)


def _activated_lines(rows: tuple) -> list[str]:
    lines: list[str] = []
    active_houses = {a.house for a in rows}
    for a in rows:
        lines.append(f"[{a.grade.replace('_', '-')}] House {a.house} - {_HOUSE_NAMES[a.house]}: "
                     f"{a.natal_verdict.upper()} ({a.natal_degree})")
        lines.append(f"    {_activates_clause(a)}")
    dormant = [h for h in range(1, 13) if h not in active_houses]
    if dormant:
        lines.append(f"Dormant this period: {', '.join(map(str, dormant))}  "
                     f"({len(dormant)} not lit)")
    return lines


def snapshot_to_text(snap) -> str:
    """Render a `DashaSnapshot`: the houses the running period lights up, par-excellence first."""
    b = snap.birth
    period = (f"{snap.period.maha} / {snap.period.antar}" if snap.period and snap.period.antar
              else (snap.period.maha if snap.period else "n/a"))
    out = ["=" * 72,
           f"RAMAN SAAB - Dasha Snapshot for {b.name} on {_jd_to_date(snap.jd)}",
           f"Running period: {period}    [ayanamsa = {snap.promise.ayanamsa}]",
           "=" * 72, "",
           "ACTIVE HOUSES (par-excellence first; natal promise + activating lord)"]
    out += _activated_lines(snap.activated) if snap.activated else ["(no house lit - check date)"]
    out += ["", "The natal verdict is the standing promise; the Dasha selects what is active now."]
    return _ascii("\n".join(out))


def snapshot_to_markdown(snap) -> str:
    b = snap.birth
    period = (f"{snap.period.maha}/{snap.period.antar}" if snap.period and snap.period.antar
              else (snap.period.maha if snap.period else "n/a"))
    out = [f"# Dasha Snapshot - {b.name} ({_jd_to_date(snap.jd)})",
           f"**Running period:** {period}", "", "## Active houses (par-excellence first)"]
    for a in snap.activated:
        out.append(f"- **[{a.grade.replace('_', '-')}] House {a.house} - {_HOUSE_NAMES[a.house]}:** "
                   f"{a.natal_verdict} ({a.natal_degree}) - _{_activates_clause(a)}_")
    if not snap.activated:
        out.append("- (no house lit)")
    return _ascii("\n".join(out))


def timeline_to_text(tl) -> str:
    """Render a `DashaTimeline`: Raman's Dasha-by-Dasha narrative — each period's active houses."""
    b = tl.birth
    out = ["=" * 72, f"RAMAN SAAB - Dasha Life-Narrative for {b.name}",
           f"[ayanamsa = {tl.promise.ayanamsa}]  (natal promise x running-period activation)",
           "=" * 72]
    for tp in tl.periods:
        label = f"{tp.period.maha}/{tp.period.antar}" if tp.period.antar else f"{tp.period.maha} Dasha"
        out.append("")
        out.append(f"=== {label}  ({_jd_to_date(tp.period.start_jd)} .. "
                   f"{_jd_to_date(tp.period.end_jd)}) ===")
        pe = [a for a in tp.activated if a.grade == "par_excellence"]
        lim = [a for a in tp.activated if a.grade == "limited"]
        if pe:
            for a in pe:
                out.append(f"  [par-excellence] House {a.house} ({_HOUSE_NAMES[a.house]}): "
                           f"{a.natal_verdict} ({a.natal_degree})")
        else:
            out.append("  (no par-excellence house this period)")
        if lim:
            out.append(f"  limited: {', '.join(str(a.house) for a in lim)}")
    return _ascii("\n".join(out))


def timeline_to_markdown(tl) -> str:
    out = [f"# Dasha Life-Narrative - {tl.birth.name}", ""]
    for tp in tl.periods:
        label = f"{tp.period.maha}/{tp.period.antar}" if tp.period.antar else f"{tp.period.maha} Dasha"
        out.append(f"## {label} ({_jd_to_date(tp.period.start_jd)} .. {_jd_to_date(tp.period.end_jd)})")
        pe = [a for a in tp.activated if a.grade == "par_excellence"]
        for a in pe:
            out.append(f"- **House {a.house} ({_HOUSE_NAMES[a.house]}):** "
                       f"{a.natal_verdict} ({a.natal_degree})")
        lim = [a.house for a in tp.activated if a.grade == "limited"]
        if lim:
            out.append(f"- _limited:_ {', '.join(map(str, lim))}")
        out.append("")
    return _ascii("\n".join(out))
