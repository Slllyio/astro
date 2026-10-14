"""Bhava karakas (BPHS ch.32 sl.31-34) — the natural significator of each house.

Pinned to Parashara's stated order: Sun, Jupiter, Mars, Moon, Jupiter, Mars, Venus, Saturn, Jupiter,
Mercury, Jupiter, Saturn. Citation must resolve to root text.
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine import bhava_karaka as K
from app.parashara.doctrine.sources import verify


def test_full_order_matches_parashara():
    order = [K.karaka_of(h) for h in range(1, 13)]
    assert order == ["Sun", "Jupiter", "Mars", "Moon", "Jupiter", "Mars",
                     "Venus", "Saturn", "Jupiter", "Mercury", "Jupiter", "Saturn"]


def test_key_karakas():
    assert K.karaka_of(1) == "Sun"       # soul/self
    assert K.karaka_of(4) == "Moon"      # mother
    assert K.karaka_of(7) == "Venus"     # spouse
    assert K.karaka_of(8) == "Saturn"    # longevity
    assert K.karaka_of(10) == "Mercury"  # honour/karma


def test_out_of_range_raises():
    with pytest.raises(ValueError):
        K.karaka_of(0)
    with pytest.raises(ValueError):
        K.karaka_of(13)


def test_citation_resolves():
    assert verify(K.SOURCE)
