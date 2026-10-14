"""Extract Raman's OWN attention from *Notable Horoscopes* — the salience benchmark.

The engine computes ~50 true statements per chart and has no idea which three matter. That is
the faculty this corpus can measure: for each of his worked charts Raman *chose* what to
discuss, and the choosing is the expertise. This tool turns his prose into a per-chart set of
factors he actually named, so a salience ranking can be scored against it.

What it does NOT do: touch life outcomes. The target here is expert attention, which is why it
sits clear of the astrobank firewall and does not relitigate the measured-null generalization
axis. See `docs/raman_saab/REAL_OUTCOME_GENERALIZATION.md`.

Section shape in the source (stable across the book):

    No. 2.— SRI GAUTAMA BUDDHA
    Birth Details. — *14th April 623 B.C, at about midday (Lat. ..., long. ...)
    Planetary Positions. — The Sun 21°; the Moon 197° 5'; ...
    Balance of <graha> Dasa ...
    <the reading — this is where the attention lives>
    Important Events. — ...

Usage:
    py -3.12 tools/raman_saab/extract_notable_attention.py \
        --source "data/Notable Horoscopes BV Raman.txt" \
        --out tests/fixtures/notable_attention.json
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Final, Optional

logger = logging.getLogger(__name__)

GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

#: Raman names houses both by ordinal and by their Sanskrit bhava names; both are attention.
HOUSE_NAMES: Final[dict[str, int]] = {
    "lagna": 1, "ascendant": 1, "thanu": 1,
    "dhana": 2, "kutumba": 2,
    "sahaja": 3, "bhratru": 3,
    "sukha": 4, "bandhu": 4, "matru": 4,
    "putra": 5, "poorvapunya": 5,
    "ari": 6, "shatru": 6, "roga": 6,
    "kalatra": 7, "jaya": 7,
    "randhra": 8, "ayur": 8,
    "bhagya": 9, "dharma": 9, "pitru": 9,
    "karma": 10, "karmasthana": 10, "rajya": 10,
    "labha": 11, "aya": 11,
    "vyaya": 12, "moksha": 12, "mokshasthana": 12,
}

#: Phrases where Raman is explicitly flagging what matters. A factor named inside one of these
#: sentences is attention he underlined, not attention he merely passed through.
EMPHASIS_MARKERS: Final[tuple[str, ...]] = (
    "it will be seen", "most important", "mark the fact", "i must emphasize",
    "most formidable", "most powerful", "chiefly", "predominant", "noteworthy",
    "it is significant", "the most", "specially", "particularly",
)

#: Raman constantly counts houses FROM a reference frame — "the 5th from Lagna", "the 9th from
#: the Moon". The subject there is the 5th and the 9th; Lagna and the Moon are the yardstick.
#: Counting them as attention put H1 top of the emphasis table by artefact (12% of all "Lagna"
#: and a full 30% of all "Moon" mentions are this construction), so the frame phrase is
#: neutralised before factors are tallied. The ordinal is matched separately and survives.
_FRAME_RE = re.compile(
    r"\bfrom\s+(?:the\s+)?(?:Chandra\s+)?(?:Lagna|Moon|Ascendant|Chandra)\b", re.I)

#: An ordinal is a HOUSE unless it is counting time. "in his 16th year", "the 6th day of Lous",
#: "the 4th century", "22nd July" are dates and ages, not bhavas — caught while hand-checking
#: Alexander, whose 6th-house score was partly "the 6th day of Lous". Two-digit dates were
#: already excluded by the 1..12 filter; this catches the ones that were not.
_NOT_A_HOUSE: Final[str] = (
    r"(?!\s+(?:year|day|month|century|January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\b)")
_ORDINAL_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\b" + _NOT_A_HOUSE, re.I)

_SIGNS: Final[frozenset[str]] = frozenset({
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"})

#: Raman names the rising sign in prose, in English or Sanskrit, often both.
_SIGN_ALIASES: Final[dict[str, str]] = {
    "mesha": "Aries", "vrishabha": "Taurus", "mithuna": "Gemini", "kataka": "Cancer",
    "karka": "Cancer", "simha": "Leo", "kanya": "Virgo", "thula": "Libra", "tula": "Libra",
    "vrischika": "Scorpio", "dhanus": "Sagittarius", "makara": "Capricorn",
    "kumbha": "Aquarius", "meena": "Pisces",
}
_LAGNA_RE = re.compile(
    r"Lagna\s+is\s+(?:the\s+)?([A-Za-z]+)", re.I)
_YOGA_RE = re.compile(r"\b([A-Z][a-zA-Z]+)\s+Yoga\b")
_RAJAYOGA_RE = re.compile(r"\bRaja\s*yogas?\b", re.I)
_LORD_RE = re.compile(r"lord of the (\d{1,2})(?:st|nd|rd|th)", re.I)
_SECTION_RE = re.compile(r"^No\.\s*([IVXLC0-9]+)\s*[.\-—:]*\s*[-—]?\s*(.+?)\s*$")
_SUN_LON_RE = re.compile(r"[Tt]he Sun\s+(\d{1,3})\s*[°ºO]\s*(\d{1,2})?", re.U)
_LAT_RE = re.compile(r"[Ll]at\.?\s*(\d{1,2})\s*[°ºO]\s*(\d{1,2})?\s*'?\s*([NS])", re.U)
_LON_RE = re.compile(r"[Ll]ong\.?\s*(\d{1,3})\s*[°ºO]\s*(\d{1,2})?\s*'?\s*([EW])", re.U)


@dataclass
class ChartAttention:
    """One worked chart: who it is, whether it is castable, and what Raman actually named."""

    number: str
    name: str
    line_start: int
    line_end: int
    birth_details: str = ""
    positions_raw: str = ""
    balance_of_dasa: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sun_longitude: Optional[float] = None
    #: the Lagna Raman states in prose ("The Lagna is Taurus or Vrishabha"). This is the ONLY
    #: printed value that actually tests the coordinates — planetary longitudes depend on time
    #: alone, so they admit a chart cast at the wrong place.
    stated_lagna: str = ""
    prose_chars: int = 0
    #: factor -> times named. The ranking target.
    houses: dict[int, int] = field(default_factory=dict)
    grahas: dict[str, int] = field(default_factory=dict)
    yogas: dict[str, int] = field(default_factory=dict)
    #: factors named inside an emphasis sentence — Raman underlining his own point.
    emphasised_houses: list[int] = field(default_factory=list)
    emphasised_grahas: list[str] = field(default_factory=list)


def _dms(deg: str, minute: Optional[str], hemi: str = "") -> float:
    val = float(deg) + (float(minute) / 60.0 if minute else 0.0)
    return -val if hemi.upper() in ("S", "W") else val


def _split_sections(lines: list[str]) -> list[tuple[str, str, int, int]]:
    """(number, name, start, end) per chart. A heading with no name is OCR noise, skipped."""
    heads: list[tuple[str, str, int]] = []
    for i, line in enumerate(lines):
        m = _SECTION_RE.match(line.strip())
        if not m:
            continue
        number, name = m.group(1).strip(), m.group(2).strip(" .-—")
        # the trailing pages of the scan contain bare "No." lines; a real heading names someone
        if not name or len(name) < 3 or not re.search(r"[A-Za-z]{3}", name):
            continue
        heads.append((number, name, i))
    out = []
    for idx, (number, name, start) in enumerate(heads):
        end = heads[idx + 1][2] if idx + 1 < len(heads) else len(lines)
        out.append((number, name, start, end))
    return out


def _labelled(body: str, label: str) -> str:
    """The text following a `Label. —` marker, up to the next blank-ish break."""
    m = re.search(re.escape(label) + r"\s*[.:]?\s*[-—]*\s*(.{0,400})", body, re.S | re.I)
    return " ".join(m.group(1).split()) if m else ""


def _count_factors(prose: str, rec: ChartAttention) -> None:
    """Tally every house / graha / yoga Raman names, and flag the emphasised ones.

    Ordinals are counted from the ORIGINAL text (``the 5th from Lagna`` is attention on the
    5th); everything else is counted from the frame-stripped text, so the yardstick is not
    mistaken for the subject.
    """
    deframed = _FRAME_RE.sub(" ", prose)

    for g in GRAHAS:
        n = len(re.findall(rf"\b{g}\b", deframed))
        if n:
            rec.grahas[g] = n

    for m in _ORDINAL_RE.finditer(prose):
        h = int(m.group(1))
        if 1 <= h <= 12:
            rec.houses[h] = rec.houses.get(h, 0) + 1
    for word, h in HOUSE_NAMES.items():
        n = len(re.findall(rf"\b{word}", deframed, re.I))
        if n:
            rec.houses[h] = rec.houses.get(h, 0) + n
    for m in _LORD_RE.finditer(deframed):
        h = int(m.group(1))
        if 1 <= h <= 12:
            rec.houses[h] = rec.houses.get(h, 0) + 1

    for m in _YOGA_RE.finditer(deframed):
        y = m.group(1)
        if y.lower() in ("raja", "the", "a", "this", "another", "powerful"):
            continue
        rec.yogas[y] = rec.yogas.get(y, 0) + 1
    n_raja = len(_RAJAYOGA_RE.findall(prose))
    if n_raja:
        rec.yogas["Rajayoga"] = rec.yogas.get("Rajayoga", 0) + n_raja

    # emphasis: only factors named in a sentence Raman flagged
    for sentence in re.split(r"(?<=[.!?])\s+", prose):
        low = sentence.lower()
        desent = _FRAME_RE.sub(" ", sentence)
        if not any(mk in low for mk in EMPHASIS_MARKERS):
            continue
        for m in _ORDINAL_RE.finditer(sentence):
            h = int(m.group(1))
            if 1 <= h <= 12 and h not in rec.emphasised_houses:
                rec.emphasised_houses.append(h)
        for word, h in HOUSE_NAMES.items():
            if re.search(rf"\b{word}", sentence, re.I) and h not in rec.emphasised_houses:
                rec.emphasised_houses.append(h)
        for g in GRAHAS:
            if re.search(rf"\b{g}\b", sentence) and g not in rec.emphasised_grahas:
                rec.emphasised_grahas.append(g)


def extract(source: Path) -> list[ChartAttention]:
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    records: list[ChartAttention] = []

    for number, name, start, end in _split_sections(lines):
        body = "\n".join(lines[start:end])
        rec = ChartAttention(number=number, name=name, line_start=start + 1, line_end=end)

        # "The Lagna is aspected by…" / "is fairly strong" are not sign names; only take a hit
        # that actually resolves to one of the twelve.
        for lg in _LAGNA_RE.finditer(body):
            word = lg.group(1).lower()
            sign = _SIGN_ALIASES.get(word) or (word.title() if word.title() in _SIGNS else "")
            if sign:
                rec.stated_lagna = sign
                break

        rec.birth_details = _labelled(body, "Birth Details")
        rec.positions_raw = _labelled(body, "Planetary Positions")
        bal = re.search(r"Balance of\s+(.{0,120}?)Dasa", body, re.S | re.I)
        rec.balance_of_dasa = " ".join(bal.group(1).split()) if bal else ""

        where = rec.birth_details or body[:1200]
        if (m := _LAT_RE.search(where)):
            rec.latitude = _dms(m.group(1), m.group(2), m.group(3))
        if (m := _LON_RE.search(where)):
            rec.longitude = _dms(m.group(1), m.group(2), m.group(3))
        if (m := _SUN_LON_RE.search(rec.positions_raw or body)):
            rec.sun_longitude = _dms(m.group(1), m.group(2))

        # the reading itself: everything after the positions/dasa preamble
        cut = 0
        for marker in ("Balance of", "Planetary Positions"):
            j = body.find(marker)
            if j > cut:
                cut = j
        prose = body[cut:]
        rec.prose_chars = len(prose)
        _count_factors(prose, rec)
        records.append(rec)

    return records


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default="data/Notable Horoscopes BV Raman.txt")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    recs = extract(Path(args.source))
    castable = [r for r in recs if r.latitude is not None and r.longitude is not None]
    with_factors = [r for r in recs if r.houses or r.grahas]

    print(f"sections found        : {len(recs)}")
    print(f"with lat+long (castable): {len(castable)}")
    print(f"with named factors    : {len(with_factors)}")
    print(f"with printed Sun lon  : {sum(1 for r in recs if r.sun_longitude is not None)}")
    print()
    print(f"{'name':34s} {'lat':>8s} {'lon':>9s} {'houses':>7s} {'grahas':>7s} "
          f"{'yogas':>6s} {'emph':>5s}")
    for r in recs[:14]:
        print(f"{r.name[:34]:34s} {str(r.latitude or '—')[:8]:>8s} "
              f"{str(r.longitude or '—')[:9]:>9s} {len(r.houses):7d} {len(r.grahas):7d} "
              f"{len(r.yogas):6d} {len(r.emphasised_houses) + len(r.emphasised_grahas):5d}")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps([asdict(r) for r in recs], indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
