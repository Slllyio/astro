"""Synthesis layer — fuse the engine's separate layers into ONE Raman-style reading per matter.

For each bhava it combines: the D1 verdict (the promise), the navamsa testimony (the fruit), the
matter-specific divisional chart (D7 children / D10 career / D12 parents / D30 health), the
Ashtakavarga house-strength, the Vimshottari activation windows, the running Vimshottari + Jaimini
Chara dasha, and the current transits (Gochara + Sade-Sati). This is the layer that turns "the
engine HAS all of Raman's tools" into "the engine READS like Raman." It is pure assembly over
already-computed data — it never re-judges a verdict.

Usage:
    from app.raman_saab.synthesis import synthesize, to_text
    print(to_text(synthesize(birth)))                       # today
    print(to_text(synthesize(birth, on=(2030, 1, 1))))
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import swisseph as swe

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.proforma import read_chart
from app.raman_saab.primitives import vimshottari as vim
from app.raman_saab.primitives import transits as tr
from app.raman_saab.primitives import chara_dasha as cd
from app.raman_saab.primitives import special_points as sp

_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
          "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_HOUSE = {1: "Self/Body", 2: "Wealth/Family", 3: "Siblings/Courage", 4: "Mother/Home",
          5: "Children/Mind", 6: "Health/Enemies", 7: "Spouse/Partnership", 8: "Longevity",
          9: "Father/Fortune", 10: "Career", 11: "Gains", 12: "Loss/Moksha/Spirituality"}


@dataclass(frozen=True)
class MatterReading:
    house: int
    name: str
    verdict: str
    navamsa: str
    matter_varga: Optional[str]
    ashtakavarga: Optional[str]
    activation: tuple[str, ...]
    transit_note: Optional[str]
    reading: str


@dataclass(frozen=True)
class Synthesis:
    lagna: str
    atmakaraka: str
    arudha_lagna: str
    navamsa_lagna: str
    running_md: str
    running_ad: str
    chara: str
    sade_sati: Optional[str]
    matters: tuple[MatterReading, ...]


def _birth_jd(b: BirthData) -> float:
    return swe.julday(b.year, b.month, b.day, b.hour + b.minute / 60.0 - b.tz_offset)


def _compose(verdict: str, navamsa: str, varga: Optional[str], sav: Optional[str],
             transit_note: Optional[str]) -> str:
    parts = [f"the rashi reads **{verdict}**"]
    parts.append({"confirms": "and the navamsa confirms it (delivered)",
                  "weakens": "but the navamsa qualifies/withholds it (delivery in doubt)",
                  "neutral": "the navamsa is neutral",
                  "unknown": ""}.get(navamsa, ""))
    if varga:                                       # "varga_D10=Sun:own|Mercury:neutral"
        body = varga.split("=", 1)[-1]
        parts.append(f"the matter-varga shows {body}")
    if sav:
        n, band = sav.split(":")
        parts.append(f"Ashtakavarga {band} ({n} bindus)")
    if transit_note:
        parts.append(transit_note)
    return "; ".join(p for p in parts if p)


def synthesize(birth: BirthData, *, on: Optional[tuple[int, int, int]] = None,
               ayanamsa: str = "lahiri") -> Synthesis:
    chart: RamanChart = cast_chart(birth, ayanamsa=ayanamsa)
    reading = read_chart(birth, ayanamsa=ayanamsa)
    y, m, d = on if on is not None else _today()
    jd = swe.julday(y, m, d, 6.5)
    age = (jd - _birth_jd(birth)) / 365.2425

    period = vim.dasha_on(chart, jd)
    active = {a.house for a in vim.active_houses(chart, jd) if a.grade == "par_excellence"}
    transits = tr.gochara(chart, y, m, d, ayanamsa=ayanamsa)
    by_house: dict[int, list[tr.TransitRow]] = {}
    for t in transits:
        by_house.setdefault(t.house_from_lagna, []).append(t)

    matters: list[MatterReading] = []
    for pf in reading.proformas:
        h = pf.house
        led = pf.significations[0].ledger
        md = dict(pf.metadata)
        varga = next((f"{k}={v}" for k, v in pf.metadata if k.startswith("varga_")), None)
        sav = md.get("sav_bindus")
        activ = tuple(v for k, v in pf.metadata if k == "active_periods")
        here = by_house.get(h, [])
        tnote = None
        if here:
            tnote = "current transit: " + ", ".join(
                f"{t.planet}{' (supported)' if t.supported else ''}" for t in here)
        active_now = " — ACTIVE in the running period" if h in active else ""
        matters.append(MatterReading(
            house=h, name=_HOUSE[h], verdict=pf.rollup, navamsa=led.navamsa_status,
            matter_varga=varga, ashtakavarga=sav, activation=activ, transit_note=tnote,
            reading=_compose(pf.rollup, led.navamsa_status, varga, sav, tnote) + active_now))

    al = sp.arudha_lagna(chart).sign
    return Synthesis(
        lagna=_SIGNS[chart.asc_sign - 1], atmakaraka=sp.atmakaraka(chart),
        arudha_lagna=_SIGNS[al - 1], navamsa_lagna=_SIGNS[sp.navamsa_lagna(chart).sign - 1],
        running_md=period.maha, running_ad=period.antar,
        chara=_SIGNS[(cd.chara_dasha_on(chart, age) or (chart.asc_sign, 0))[0] - 1],
        sade_sati=tr.sade_sati(chart, y, m, d, ayanamsa=ayanamsa), matters=tuple(matters))


def to_text(s: Synthesis) -> str:
    out = ["=" * 76,
           f"SYNTHESIS — Lagna {s.lagna} | Atmakaraka {s.atmakaraka} | Arudha Lagna {s.arudha_lagna}"
           f" | Navamsa Lagna {s.navamsa_lagna}",
           f"Running: Vimshottari {s.running_md} MD / {s.running_ad} AD | Chara dasha {s.chara}"
           + (f" | {s.sade_sati}" if s.sade_sati else ""),
           "=" * 76]
    for mr in s.matters:
        out.append(f"H{mr.house:2} {mr.name}: {mr.reading}")
    return "\n".join(out)


def _today() -> tuple[int, int, int]:
    import datetime
    t = datetime.date.today()
    return (t.year, t.month, t.day)
