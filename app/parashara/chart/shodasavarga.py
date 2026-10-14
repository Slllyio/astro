"""The Shodasavarga — the sixteen divisional-chart signs of each body (BPHS ch.6-7).

BPHS ch.6 ("The Sixteen Divisions Of A Sign") defines all sixteen vargas; ch.7 sets the shodasavarga
set and its use. The engine already computes these divisions internally (Vimsopaka, Sthana bala,
Vargottama); this exposes the full per-body table so a reading shows every varga sign — the Navamsa
(D9, marriage/dharma), Dasamsa (D10, career), Shashtiamsa (D60), and the rest — not just the ones a
strength score happens to consume.

Pure arithmetic over the shared varga substrate (no doctrine transcribed, only the division math),
cited to the shodasavarga's own sloka. Self-checking: D1 is always the Rasi sign, and a body in the
same sign in D1 and D9 is Vargottama.
"""
from __future__ import annotations

from typing import Final, Mapping

from app.raman_saab.chart import varga as _varga     # substrate: pure division arithmetic
from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.vimsopaka import SCHEME_SOURCE, SHODASAVARGA

SOURCE: Final[Citation] = SCHEME_SOURCE["shodasavarga"]      # BPHS-7:265, the shodasavarga set
DIVISIONS_SOURCE: Final[Citation] = Citation("BPHS-6", 44)   # ch.6 sl.2-4, "NAMES OF THE 16 VARGAS"
DOMAINS_SOURCE: Final[Citation] = Citation("BPHS-7", 48)     # ch.7 sl.1-8, "USE OF THE 16 DIVISIONS"

#: tag -> the life-matter that varga is read for (BPHS-7:1-8). What each division is FOR.
VARGA_DOMAINS: Final[Mapping[str, str]] = {
    "D1": "physique / body", "D2": "wealth", "D3": "siblings (co-born)", "D4": "fortunes",
    "D7": "progeny", "D9": "spouse", "D10": "power & position (career)", "D12": "parents",
    "D16": "conveyances", "D20": "worship / devotion", "D24": "learning", "D27": "strength & weakness",
    "D30": "evils / misfortune", "D40": "auspicious & inauspicious effects",
    "D45": "all indications", "D60": "all indications",
}

#: tag -> (division number, classical name), in the canonical shodasavarga order.
VARGAS: Final[tuple[tuple[str, int, str], ...]] = (
    ("D1", 1, "Rasi"), ("D2", 2, "Hora"), ("D3", 3, "Drekkana"), ("D4", 4, "Chaturthamsa"),
    ("D7", 7, "Saptamsa"), ("D9", 9, "Navamsa"), ("D10", 10, "Dasamsa"), ("D12", 12, "Dwadasamsa"),
    ("D16", 16, "Shodasamsa"), ("D20", 20, "Vimsamsa"), ("D24", 24, "Siddhamsa"),
    ("D27", 27, "Bhamsa"), ("D30", 30, "Trimsamsa"), ("D40", 40, "Khavedamsa"),
    ("D45", 45, "Akshavedamsa"), ("D60", 60, "Shashtiamsa"),
)

# The set of tags must be exactly the shodasavarga scheme's — a guard against drift.
assert {t for t, _, _ in VARGAS} == set(SHODASAVARGA), "shodasavarga tag set mismatch"
assert set(VARGA_DOMAINS) == set(SHODASAVARGA), "varga-domain map must cover every varga"


def shodasavarga(longitude: float) -> dict[str, int]:
    """The sixteen divisional signs (1..12) of a body at `longitude`, keyed by tag (D1..D60)."""
    lon = longitude % 360.0
    return {tag: _varga.varga_sign(lon, n) for tag, n, _ in VARGAS}


def shodasavarga_all(longitudes: Mapping[str, float]) -> dict[str, dict[str, int]]:
    """Every body's sixteen divisional signs (planet/point -> {tag: sign})."""
    return {body: shodasavarga(lon) for body, lon in longitudes.items()}
