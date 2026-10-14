"""Saravali ch.45 — the "N planets share a dignity" concentration verdicts.

BPHS ch.3 gives the dignity TABLES (which sign exalts which graha); it has no verdict for how many
grahas simultaneously hold a dignity. Saravali ch.45 does, and it is striking doctrine: two exalted
-> rich and famous; all seven exalted -> "an emperor ruling over the land surrounded by seas." Five
such ladders exist — exaltation, moolatrikona, own, friendly, and fall (debilitation).

ch.45's per-sloka numbering is OCR-collapsed (the whole chapter indexes as one sloka), so this
sections the chapter by its CAPS "EFFECTS OF MORE PLANETS IN ..." headers and reads each count rung
verbatim, citing the section header's own line (which `verify()` resolves).

DEFERRED, not faked (no silent approximation): the chapter's *single-planet* dignity effects
(sl.1-18) are also present but their per-graha sentences are split by OCR-inserted spaces inside the
names ("J upiter", "Mer cury"), so a clean per-planet extraction is not yet reliable. The
concentration ladders key on the count-word alone, so they are unaffected.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Final, Mapping, Optional

from app.parashara.doctrine.corpus_index import Sloka
from app.parashara.doctrine.sources import Citation, resolve_file
from app.parashara.primitives.relationships import (
    EXALTATION,
    GRAHAS,
    MOOLATRIKONA,
    SIGN_LORDS,
    naisargika,
)

_WORK: Final[str] = "SARAVALI-45"

#: CAPS header fragment -> dignity key, for the five concentration ladders.
_MORE_HEADERS: Final[tuple[tuple[str, str], ...]] = (
    ("MORE PLANETS IN EXALTATION", "exalted"),
    ("MORE PLANETS IN MOOLATRIKONA", "moolatrikona"),
    ("MORE PLANETS IN OWN", "own"),
    ("MORE PLANETS IN FRIENDLY", "friendly"),
    ("MORE PLANETS IN FALL", "debilitated"),
)

#: count-word -> how many planets (Saravali writes 7 as either "seven" or "all").
_COUNT_WORD: Final[Mapping[str, int]] = {
    "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "all": 7,
}


def _norm(line: str) -> str:
    """Collapse the OCR's doubled spaces so header fragments match."""
    return re.sub(r"\s+", " ", line).strip()


@lru_cache(maxsize=1)
def _concentration_grid() -> dict[tuple[str, int], Sloka]:
    """{(dignity, count 2..7): Sloka} read verbatim from ch.45's five concentration sections."""
    path = resolve_file(_WORK)
    if path is None:
        return {}
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()

    # Find each MORE-section's start line (1-indexed) and dignity key, in file order.
    starts: list[tuple[int, str]] = []
    for i, line in enumerate(raw, start=1):
        norm = _norm(line).upper()
        for frag, key in _MORE_HEADERS:
            if frag in norm:
                starts.append((i, key))
    starts.sort()

    out: dict[tuple[str, int], Sloka] = {}
    for idx, (start_line, key) in enumerate(starts):
        end_line = starts[idx + 1][0] - 1 if idx + 1 < len(starts) else len(raw)
        body = _norm(" ".join(raw[start_line - 1:end_line]))
        # Drop the header clause so its own words ("EXALTATION") aren't scanned as content.
        body = re.split(r"EFFECTS OF MORE PLANETS IN [A-Z]+", body, maxsplit=1)[-1]
        for sentence in re.split(r"(?<=[.])\s+", body):
            count = _count_in(sentence)
            if count is not None and (key, count) not in out:
                out[(key, count)] = Sloka(
                    work=_WORK,
                    number=count,
                    topic=key,
                    text=sentence.strip(),
                    source=Citation(_WORK, start_line),
                )
    return out


def _count_in(sentence: str) -> Optional[int]:
    """The number of planets a rung sentence speaks of, from its count-word (or None)."""
    for word in re.findall(r"[a-z]+", sentence.lower()):
        if word in _COUNT_WORD:
            return _COUNT_WORD[word]
    return None


def concentration_effect(dignity: str, count: int) -> Optional[Sloka]:
    """Saravali's verdict for `count` planets simultaneously in `dignity`, or None (SARAVALI-45)."""
    if dignity not in {k for _, k in _MORE_HEADERS}:
        raise ValueError(f"dignity must be one of {[k for _, k in _MORE_HEADERS]}, got {dignity!r}")
    if not 2 <= count <= 7:
        raise ValueError("concentration verdicts run from 2 to 7 planets")
    return _concentration_grid().get((dignity, count))


def all_concentration_effects() -> Mapping[tuple[str, int], Sloka]:
    """The whole dignity x count concentration grid (SARAVALI-45)."""
    return dict(_concentration_grid())


def _fall_sign(planet: str) -> int:
    """Debilitation sign = 7th from exaltation."""
    return ((EXALTATION[planet] + 6 - 1) % 12) + 1


def graha_dignity(planet: str, sign: int) -> str:
    """The single highest dignity `planet` holds in `sign`, as one partition bucket.

    Priority exalted > moolatrikona (its exact MT sign) > own (another owned sign) > debilitated >
    friendly > neutral. ponytail: MT is counted for the whole MT sign, not the MT degree-span
    (sloka 55 is sign-only per relationships.py); refine to degrees if a chart needs it.
    """
    if sign == EXALTATION[planet]:
        return "exalted"
    if sign == MOOLATRIKONA[planet]:
        return "moolatrikona"
    if SIGN_LORDS[sign] == planet:
        return "own"
    if sign == _fall_sign(planet):
        return "debilitated"
    if naisargika(planet, SIGN_LORDS[sign]) == "mitra":
        return "friendly"
    return "neutral"


def dignity_counts(signs_by_graha: Mapping[str, int]) -> dict[str, int]:
    """{dignity: how many of the 7 grahas hold it} — the input to the concentration verdicts."""
    counts = {"exalted": 0, "moolatrikona": 0, "own": 0, "friendly": 0, "debilitated": 0}
    for g in GRAHAS:
        sign = signs_by_graha.get(g)
        if sign is None:
            continue
        bucket = graha_dignity(g, sign)
        if bucket in counts:
            counts[bucket] += 1
    return counts


def active_concentrations(signs_by_graha: Mapping[str, int]) -> dict[str, tuple[int, Sloka]]:
    """For each dignity with >=2 grahas, its (count, Saravali verdict). The chart-facing entry."""
    out: dict[str, tuple[int, Sloka]] = {}
    for dignity, n in dignity_counts(signs_by_graha).items():
        if n >= 2:
            eff = concentration_effect(dignity, min(n, 7))
            if eff is not None:
                out[dignity] = (n, eff)
    return out
