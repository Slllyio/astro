"""Multi-planet conjunction (yoga) effects — Saravali ch.15 (pairs) and ch.16 (triples).

For every pair (ch.15, 21 = C(7,2)) and every triple (ch.16, 35 = C(7,3)) of the grahas sharing a
house, Saravali gives an effect. BPHS has no such clean multi-graha grid, so this is allied doctrine
(citable where the root is silent). Each cell is read verbatim and cited to its line; the corpus is
parsed by the grahas NAMED (not the numbered-sloka index), because OCR mangled several sloka numbers
(ch.15's Moon-Venus scanned as roman "II."; five ch.16 triples carry no "YOGA" keyword) — keying on
the graha names recovers all 21 pairs and all 35 triples.

Conjunction = sharing a sign, the project's locked whole-sign convention.
"""
from __future__ import annotations

import re
from functools import lru_cache
from itertools import combinations
from typing import Final, Mapping, Optional

from app.parashara.doctrine.corpus_index import Sloka
from app.parashara.doctrine.sources import Citation, resolve_file

_WORK: Final[str] = "SARAVALI-15"
_GRAHAS: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
#: OCR-tolerant name patterns — the scan sees "J UPITER", "SUN - MOON", etc.
_PAT: Final[Mapping[str, "re.Pattern[str]"]] = {
    g: re.compile(r"\b" + r"\s*".join(g.upper()) + r"\b") for g in _GRAHAS
}


@lru_cache(maxsize=1)
def _grid() -> dict[frozenset, Sloka]:
    path = resolve_file(_WORK)
    if path is None:
        return {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    heads: list[tuple[int, frozenset]] = []
    for i, ln in enumerate(lines):
        if "YOGA" not in ln.upper():
            continue
        named = frozenset(g for g in _GRAHAS if _PAT[g].search(ln.upper()))
        if len(named) == 2:
            heads.append((i, named))
    out: dict[frozenset, Sloka] = {}
    for k, (i0, pair) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        text = re.sub(r"\s+", " ", " ".join(lines[i0:end])).strip()
        out[pair] = Sloka(work=_WORK, number=len(out) + 2, topic="-".join(sorted(pair)),
                          text=text, source=Citation(_WORK, i0 + 1))
    return out


def conjunction_effect(planet_a: str, planet_b: str) -> Optional[Sloka]:
    """Saravali's effect for `planet_a` conjunct `planet_b` (order-independent), or None."""
    if planet_a not in _GRAHAS or planet_b not in _GRAHAS or planet_a == planet_b:
        raise ValueError("both must be distinct grahas Sun..Saturn")
    return _grid().get(frozenset({planet_a, planet_b}))


def all_conjunctions() -> Mapping[frozenset, Sloka]:
    """The whole 21-pair conjunction grid (SARAVALI-15)."""
    return dict(_grid())


@lru_cache(maxsize=1)
def _triple_grid() -> dict[frozenset, Sloka]:
    """{frozenset of 3 grahas: Sloka} from ch.16. Blocks are grouped by the graha-triple each line
    names (a header line and/or the effect sentence), since five triples lack the 'YOGA' keyword."""
    path = resolve_file("SARAVALI-16")
    if path is None:
        return {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    def triple_of(ln: str) -> Optional[frozenset]:
        u = re.sub(r"\s+", " ", ln).upper()
        named = frozenset(g for g in _GRAHAS if _PAT[g].search(u))
        return named if len(named) == 3 else None

    out: dict[frozenset, Sloka] = {}
    cur: Optional[frozenset] = None
    start = 0
    for i, ln in enumerate(lines):
        t = triple_of(ln)
        if t is not None and t != cur and t not in out:
            if cur is not None:
                out[cur] = _slice_sloka("SARAVALI-16", lines, start, i, cur)
            cur, start = t, i
    if cur is not None:
        out[cur] = _slice_sloka("SARAVALI-16", lines, start, len(lines), cur)
    return out


def _slice_sloka(work: str, lines: list[str], start: int, end: int, key: frozenset) -> Sloka:
    text = re.sub(r"\s+", " ", " ".join(lines[start:end])).strip()
    return Sloka(work=work, number=start + 1, topic="-".join(sorted(key)),
                 text=text, source=Citation(work, start + 1))


def triple_conjunction_effect(a: str, b: str, c: str) -> Optional[Sloka]:
    """Saravali's effect for three grahas conjunct (order-independent), or None (SARAVALI-16)."""
    trio = {a, b, c}
    if len(trio) != 3 or not trio <= set(_GRAHAS):
        raise ValueError("need three distinct grahas Sun..Saturn")
    return _triple_grid().get(frozenset(trio))


def all_triple_conjunctions() -> Mapping[frozenset, Sloka]:
    """The whole 35-triple conjunction grid (SARAVALI-16)."""
    return dict(_triple_grid())


def active_triple_conjunctions(longitudes: Mapping[str, float]) -> list[tuple[frozenset, Sloka]]:
    """Every three-graha conjunction present — triples of the seven sharing one sign — with its
    Saravali effect. Four grahas in a sign yield each of their four triples."""
    signs = {g: int(longitudes[g] % 360.0 // 30) + 1 for g in _GRAHAS if g in longitudes}
    out: list[tuple[frozenset, Sloka]] = []
    for a, b, c in combinations(_GRAHAS, 3):
        if all(p in signs for p in (a, b, c)) and signs[a] == signs[b] == signs[c]:
            eff = _triple_grid().get(frozenset({a, b, c}))
            if eff is not None:
                out.append((frozenset({a, b, c}), eff))
    return out


def active_conjunctions(longitudes: Mapping[str, float]) -> list[tuple[frozenset, Sloka]]:
    """Every two-graha conjunction actually present — pairs of the seven sharing a sign — with its
    Saravali effect, in a stable order. Three grahas in one sign yield each of their three pairs."""
    signs = {g: int(longitudes[g] % 360.0 // 30) + 1 for g in _GRAHAS if g in longitudes}
    out: list[tuple[frozenset, Sloka]] = []
    for a, b in combinations(_GRAHAS, 2):
        if a in signs and b in signs and signs[a] == signs[b]:
            eff = _grid().get(frozenset({a, b}))
            if eff is not None:
                out.append((frozenset({a, b}), eff))
    return out
