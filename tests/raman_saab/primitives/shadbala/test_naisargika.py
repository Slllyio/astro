from __future__ import annotations

from app.raman_saab.primitives.shadbala.naisargika import naisargika_bala


def test_naisargika_constants():
    assert naisargika_bala("Sun") == 60.0
    assert abs(naisargika_bala("Saturn") - 8.57) < 0.01
    assert abs(naisargika_bala("Moon") - 51.43) < 0.01
    assert naisargika_bala("Rahu") == 0.0
