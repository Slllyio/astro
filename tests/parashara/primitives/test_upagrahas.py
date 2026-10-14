"""The five Sun-derived upagrahas — BPHS ch.3 sl.61-64.

Pins the arithmetic chain, Parashara's closing verification identity (Upaketu + 1 sign == Sun), the
individual offsets, sign derivation, and that the citation resolves to real doctrine.
"""
from __future__ import annotations

import pytest

from app.parashara.primitives.upagrahas import (
    SOURCE,
    UPAGRAHA_NAMES,
    demo,
    upagraha_signs,
    upagrahas,
)
from app.parashara.doctrine.sources import verify


class TestChain:
    def test_all_five_present(self):
        up = upagrahas(100.0)
        assert set(up) == set(UPAGRAHA_NAMES) and len(up) == 5

    def test_dhuma_is_sun_plus_133_20(self):
        assert upagrahas(0.0)["Dhuma"] == pytest.approx(133.0 + 20 / 60.0)

    def test_vyatipata_is_360_minus_dhuma(self):
        up = upagrahas(50.0)
        assert up["Vyatipata"] == pytest.approx((360.0 - up["Dhuma"]) % 360.0)

    def test_parivesha_is_vyatipata_plus_180(self):
        up = upagrahas(50.0)
        assert up["Parivesha"] == pytest.approx((up["Vyatipata"] + 180.0) % 360.0)

    def test_indrachapa_is_360_minus_parivesha(self):
        up = upagrahas(50.0)
        assert up["Indrachapa"] == pytest.approx((360.0 - up["Parivesha"]) % 360.0)

    def test_all_in_range(self):
        for sun in (0.0, 123.4, 359.99):
            for lon in upagrahas(sun).values():
                assert 0.0 <= lon < 360.0


class TestVerificationIdentity:
    def test_upaketu_plus_one_sign_equals_sun(self):
        # Parashara's own closing check (BPHS-3:1173)
        for sun in (0.0, 12.97, 173.99, 288.5, 359.9):
            assert (upagrahas(sun)["Upaketu"] + 30.0) % 360.0 == pytest.approx(sun % 360.0)

    def test_demo_self_check_passes(self):
        demo()   # asserts the identity internally; must not raise


class TestSignsAndCitation:
    def test_signs_are_1_to_12(self):
        for s in upagraha_signs(200.0).values():
            assert 1 <= s <= 12

    def test_source_resolves(self):
        assert verify(SOURCE) and SOURCE.work == "BPHS-3"
