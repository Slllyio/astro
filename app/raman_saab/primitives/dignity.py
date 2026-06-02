from __future__ import annotations
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.primitives import relationships as r


def _in_range(deg: float, lo: float, hi: float) -> bool:
    return lo <= deg < hi


def dignity(planet: str, chart: RamanChart) -> str:
    """Compound dignity in {exalt, debil, moolatrikona, own, friend, neutral, enemy}.

    exalt/debil/moolatrikona/own are positional; friend/neutral/enemy use compound relation.
    """
    if planet in ("Rahu", "Ketu"):
        return "neutral"                      # Raman treats nodes by sign/conjunction, not dignity
    p = chart.planets[planet]
    sign, deg = p.sign, p.lon % 30.0
    # Categorical dignity is by SIGN (whole exaltation/debilitation sign). The deep-exaltation
    # DEGREE in the table is used only for the ayus arc (Phase 4) and uchcha-bala (Phase 1c).
    if sign == r.EXALTATION[planet][0]:
        return "exalt"
    if sign == r.DEBILITATION[planet][0]:
        return "debil"
    mt_s, mt_lo, mt_hi = r.MOOLATRIKONA[planet]
    if sign == mt_s and _in_range(deg, mt_lo, mt_hi):
        return "moolatrikona"
    if SIGN_LORDS[sign] == planet:
        return "own"
    return _compound_relation(planet, SIGN_LORDS[sign], chart)


def _temporal(of: str, towards: str, chart: RamanChart) -> str:
    a, b = chart.planets[of].rasi_house, chart.planets[towards].rasi_house
    dist = ((b - a) % 12) + 1
    return "friend" if dist in (2, 3, 4, 10, 11, 12) else "enemy"


_COMPOUND: dict[tuple[str, str], str] = {
    ("friend", "friend"): "friend", ("friend", "enemy"): "neutral",
    ("enemy", "friend"): "neutral", ("enemy", "enemy"): "enemy",
    ("friend", "neutral"): "friend", ("neutral", "friend"): "friend",
    ("enemy", "neutral"): "enemy", ("neutral", "enemy"): "enemy",
    ("neutral", "neutral"): "neutral",
}


def _compound_relation(of: str, lord: str, chart: RamanChart) -> str:
    if lord in ("Rahu", "Ketu") or of == lord:
        return "neutral"
    nat = r.naisargika(of, lord)
    tmp = _temporal(of, lord, chart)
    return _COMPOUND[(nat, tmp)]
