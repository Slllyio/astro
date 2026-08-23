"""The four Ayurdaya haranas — BPHS ch.43, applied to Nisargayu.

Pins each reduction's cited rule (with its exemptions), the "highest reduction only" combination,
and that the chart applier reduces the pre-reduction span, honours the combination, and flags the
Ascendant contribution as not-yet-added. Every harana citation must resolve.
"""
from __future__ import annotations

from app.parashara.chart.cast import cast
from app.parashara.primitives import haranas as hr
from app.parashara.primitives.longevity import nisargayu_after_haranas, nisargayu_span
from app.parashara.doctrine.sources import verify


class TestAstangata:
    def test_combust_loses_half(self):
        assert hr.astangata_fraction("Mars", combust=True) == 0.5

    def test_venus_and_saturn_exempt(self):
        assert hr.astangata_fraction("Venus", combust=True) == 0.0
        assert hr.astangata_fraction("Saturn", combust=True) == 0.0

    def test_not_combust_no_reduction(self):
        assert hr.astangata_fraction("Mars", combust=False) == 0.0


class TestSatruKshetra:
    def test_enemy_sign_loses_a_third(self):
        assert hr.satru_kshetra_fraction(in_enemy_sign=True, retrograde=False) == 1 / 3

    def test_retrograde_exempt(self):
        assert hr.satru_kshetra_fraction(in_enemy_sign=True, retrograde=True) == 0.0


class TestVyayadi:
    def test_malefic_house_ladder(self):
        assert hr.vyayadi_fraction(12, is_benefic=False) == 1.0
        assert hr.vyayadi_fraction(7, is_benefic=False) == 1 / 6

    def test_benefic_loses_half(self):
        assert hr.vyayadi_fraction(12, is_benefic=True) == 0.5

    def test_houses_one_to_six_no_reduction(self):
        for h in range(1, 7):
            assert hr.vyayadi_fraction(h, is_benefic=False) == 0.0


class TestKroorodaya:
    def test_only_malefics_in_lagna(self):
        assert hr.kroorodaya_fraction("Jupiter", in_lagna=True, asc_longitude=180.0,
                                      benefic_aspect=False) == 0.0
        assert hr.kroorodaya_fraction("Saturn", in_lagna=False, asc_longitude=180.0,
                                      benefic_aspect=False) == 0.0

    def test_fraction_is_asc_over_360(self):
        assert hr.kroorodaya_fraction("Sun", in_lagna=True, asc_longitude=180.0,
                                      benefic_aspect=False) == 0.5

    def test_benefic_aspect_halves(self):
        assert hr.kroorodaya_fraction("Sun", in_lagna=True, asc_longitude=180.0,
                                      benefic_aspect=True) == 0.25


class TestCombination:
    def test_highest_only(self):
        assert hr.net_fraction(0.5, 1 / 3, 0.25, 0.0) == 0.5

    def test_nothing_applies(self):
        assert hr.net_fraction(0.0, 0.0, 0.0, 0.0) == 0.0

    def test_longevity_benefics(self):
        assert hr.is_longevity_benefic("Mercury") and hr.is_longevity_benefic("Moon")
        assert not hr.is_longevity_benefic("Sun") and not hr.is_longevity_benefic("Saturn")


class TestCitations:
    def test_all_resolve(self):
        for c in (hr.APPLIES_TO_NISARGAYU, hr.ASTANGATA_SOURCE, hr.SATRU_SOURCE,
                  hr.VYAYADI_SOURCE, hr.KROORODAYA_SOURCE, hr.HIGHEST_ONLY_SOURCE):
            assert verify(c) and c.work == "BPHS-43", c


class TestApplier:
    def _chart(self):
        return cast(year=1990, month=7, day=15, hour=12, minute=0,
                    tz_offset=5.5, latitude=12.97, longitude=77.59)

    def test_reduces_the_pre_reduction_span(self):
        ch = self._chart()
        pre = nisargayu_span(ch.longitudes).natural_years
        post = nisargayu_after_haranas(ch)
        assert post.planetary_years <= pre
        assert post.ascendant_added is False

    def test_each_net_is_the_highest_of_its_four(self):
        post = nisargayu_after_haranas(self._chart())
        for r in post.per_planet.values():
            assert r.net == hr.net_fraction(r.astangata, r.satru_kshetra, r.vyayadi, r.kroorodaya)

    def test_reason_names_the_winning_harana(self):
        post = nisargayu_after_haranas(self._chart())
        for r in post.per_planet.values():
            if r.net > 0:
                assert r.reason in ("Astangata", "Satru Kshetra", "Vyayadi", "Kroorodaya")
