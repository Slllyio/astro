"""Krishnamurti's descriptive tables in KP Reader 4, read from the library at run time.

Two tables are keyed on a cusp sub-lord (CSL) and a sign:

* **The partner** (KPR4 pp.86-97, citation ``KPR4-PARTNER``): "Note the
  sub-lord of the 7th cusp. Find out in which sign the sub-lord is posited."
  Seven blocks (Sun ... Saturn), twelve signs each. Every block heading reads
  "if the sub-lord of the 7th cusp is <planet> ... or if the lord of the
  constellation is <planet> in which the sub-lord of 7 is", so the engine
  reads both the CSL and its star lord, each in the sign it occupies. A node
  is read through the planet conjoined with it, else the planet aspecting it,
  else its star lord (``KPR4-PARTNER-NODES``, p.97).
* **Love and life** (KPR4 pp.156-170, ``KPR4-LOVE``): "If the sub lord of
  the 5th cusp is in <sign>", with a Male and a Female paragraph.

The book text is not in the repository (``data/`` is gitignored and the books
are copyrighted), so these tables are parsed from the OCR file when it is
present (``KP_READER4`` or ``citations.READER4_FILE``) and return ``None``
otherwise. The text is OCR and is returned as printed. Descriptive only;
never a validated prediction.

Usage:
    from app.kp.chart import Birth, cast
    from app.kp.descriptions import describe_partner, love_and_life
    c = cast(Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59))
    print(describe_partner(c)); print(love_and_life(c, "male"))
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final

from app.kp.chart import NODES, KPChart, sign_index
from app.kp.citations import READER4_FILE
from app.kp.significators import _aspects

SIGNS: Final = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
                "Sagittarius", "Capricorn", "Aquarius", "Pisces")
SEVEN: Final = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_SIGN_RE = re.compile(r"(?mi)^\s*(" + "|".join(SIGNS) + r")\b\s*[:;.\-—]*")
_HEAD_RE = re.compile(
    r"(?is)if\s+the\s+sub\s*-?\s*lord\s+of\s+the\s+(?:7\w*|seventh)\s+cusp\s+is\s+(?:rushed\s+by\s+)?"
    r"(sun|moon|mars|mercury|jupiter|[vy]enus|saturn)\b")


def _source() -> Path | None:
    for cand in (os.environ.get("KP_READER4"), READER4_FILE):
        if cand and Path(cand).is_file():
            return Path(cand)
    return None


def _clean(s: str) -> str:
    s = re.sub(r"<!--.*?-->", " ", s)
    s = re.sub(r"(?m)^\s*\d{1,3}\s*$", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _split_signs(block: str) -> dict[int, str]:
    marks = list(_SIGN_RE.finditer(block))
    out: dict[int, str] = {}
    for k, m in enumerate(marks):
        end = marks[k + 1].start() if k + 1 < len(marks) else len(block)
        idx = [s.lower() for s in SIGNS].index(m.group(1).lower())
        out.setdefault(idx, _clean(block[m.end():end]))
    return out


@lru_cache(maxsize=1)
def partner_table() -> dict[tuple[str, int], str] | None:
    """``(planet, sign index) -> description`` for the 84 partner entries, or None without the book."""
    path = _source()
    if path is None:
        return None
    text = path.read_text(encoding="utf-8")
    a = text.find("Find out in which sign the sub-lord is posited")
    b = text.find("HEIGHT OF MY HUSBAND", a)
    sec = text[a:b]
    heads = list(_HEAD_RE.finditer(sec))
    table: dict[tuple[str, int], str] = {}
    for k, h in enumerate(heads):
        planet = h.group(1).capitalize().replace("Yenus", "Venus")
        end = heads[k + 1].start() if k + 1 < len(heads) else sec.find("either Rahu or Kethu")
        body = sec[h.end():end]
        body = body[body.find("\n\n"):]  # skip the rest of the heading sentence
        for s, d in _split_signs(body).items():
            table.setdefault((planet, s), d)
    return table


@lru_cache(maxsize=1)
def love_table() -> dict[tuple[int, str], str] | None:
    """``(sign index, "male"|"female") -> paragraph`` from "Love and Life", or None without the book."""
    path = _source()
    if path is None:
        return None
    text = path.read_text(encoding="utf-8")
    a = text.find("LOVE AND LIFE")
    b = text.find("LETTER TO THE AUTHOR", a)
    sec = re.sub(r"(?i)IF THE SUB\s*LORD OF (?:THE )?\S+ CUSP IS I[NS]", "\n", text[a:b])
    out: dict[tuple[int, str], str] = {}
    for s, body in _split_signs(sec).items():
        parts = re.split(r"(?i)\b(Male|Female)\s*[:;]", body)
        for k in range(1, len(parts) - 1, 2):
            out.setdefault((s, parts[k].lower()), parts[k + 1].strip())
    return out


def _resolve_node(chart: KPChart, node: str) -> tuple[str, str]:
    """KPR4 p.97: the conjoined planet, else the aspecting planet, else the node's star lord."""
    s = sign_index(chart.planets[node].longitude)
    for p in SEVEN:
        if sign_index(chart.planets[p].longitude) == s:
            return p, "conjoined with " + node
    for p in SEVEN:
        if _aspects(chart, p, node):
            return p, "aspects " + node
    return chart.planets[node].star_lord, "star lord of " + node


@dataclass(frozen=True, slots=True)
class Description:
    role: str        # "7th sub-lord" or "its star lord"
    planet: str      # planet whose block is read
    via: str         # how a node was resolved, else ""
    sign: str
    text: str | None
    citation: str = "KPR4-PARTNER"


def describe_partner(chart: KPChart) -> tuple[Description, ...] | None:
    """The partner as Krishnamurti tabulates it, read for the 7th CSL and for its star lord."""
    table = partner_table()
    if table is None:
        return None
    csl = chart.cusp(7).sub_lord
    out = []
    for role, p in (("7th sub-lord", csl), ("its star lord", chart.planets[csl].star_lord)):
        via = ""
        if p in NODES:
            p, via = _resolve_node(chart, p)
            if p in NODES:
                continue
        s = sign_index(chart.planets[p].longitude)
        d = Description(role, p, via, SIGNS[s], table.get((p, s)),
                        "KPR4-PARTNER-NODES" if via else "KPR4-PARTNER")
        if d not in out:
            out.append(d)
    return tuple(out)


def love_and_life(chart: KPChart, sex: str) -> str | None:
    """The "Love and Life" paragraph for the sign of the 5th CSL; ``sex`` is "male" or "female"."""
    table = love_table()
    if table is None:
        return None
    s = sign_index(chart.planets[chart.cusp(5).sub_lord].longitude)
    return table.get((s, sex.lower()))


__all__ = ["SIGNS", "partner_table", "love_table", "Description", "describe_partner", "love_and_life"]
