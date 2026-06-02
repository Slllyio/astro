from __future__ import annotations
from app.raman_saab.primitives import relationships as r


def test_exaltation_signs_and_degrees():
    # Classical deep-exaltation points (sign, degree).
    assert r.EXALTATION["Sun"] == (1, 10.0)      # Aries 10
    assert r.EXALTATION["Saturn"] == (7, 20.0)   # Libra 20
    assert r.EXALTATION["Venus"] == (12, 27.0)   # Pisces 27


def test_debilitation_is_opposite_sign_same_degree():
    for p, (sign, deg) in r.EXALTATION.items():
        dsign, ddeg = r.DEBILITATION[p]
        assert dsign == ((sign + 6 - 1) % 12) + 1
        assert ddeg == deg


def test_naisargika_friendship_is_consistent():
    # Sun's friends include Moon/Mars/Jupiter; enemies Venus/Saturn; Mercury neutral.
    assert r.naisargika("Sun", "Jupiter") == "friend"
    assert r.naisargika("Sun", "Venus") == "enemy"
    assert r.naisargika("Sun", "Mercury") == "neutral"
