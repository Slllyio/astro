"""Two-planet conjunction (yoga) effects — Saravali ch.15, the 21-pair grid.

For every pair of the seven grahas sharing a house, Saravali gives an effect ("Sun and Moon together
-> ...", 21 = C(7,2) pairs). BPHS has no such clean two-graha grid, so this is allied doctrine
(citable where the root is silent). Each pair is read verbatim from its "{P1}-{P2} YOGA" header and
cited to that line; the headers are parsed directly (not via the numbered-sloka index) because one
sloka's number was OCR-mangled to "II." — the header itself is clean, so keying on it recovers all 21.

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
