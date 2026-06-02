from __future__ import annotations
import contextlib
from typing import Final, Iterator
import swisseph as swe

AYANAMSA: Final[dict[str, int]] = {"raman": swe.SIDM_RAMAN, "lahiri": swe.SIDM_LAHIRI}

@contextlib.contextmanager
def sidereal_mode(name: str) -> Iterator[None]:
    """Set the swisseph sidereal mode for the duration, then restore the prior mode.
    Keeps Raman Saab from corrupting the repo's global (Lahiri) ayanamsa.

    NOTE: pyswisseph 2.10.x has NO ``get_sid_mode()``; when absent we restore the
    repo default (Lahiri) — which is what ``app/core`` re-asserts on every call anyway.
    Verified against the installed build: Raman vs Lahiri differ ~1.45° at J2000."""
    if name not in AYANAMSA:
        raise ValueError(f"unknown ayanamsa {name!r}; expected one of {sorted(AYANAMSA)}")
    has_get = hasattr(swe, "get_sid_mode")
    prior = swe.get_sid_mode() if has_get else None
    try:
        swe.set_sid_mode(AYANAMSA[name])
        yield
    finally:
        if prior is None:
            swe.set_sid_mode(swe.SIDM_LAHIRI)            # repo global default
        elif isinstance(prior, (tuple, list)):
            swe.set_sid_mode(*prior)
        else:
            swe.set_sid_mode(prior)
