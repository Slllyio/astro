"""Tests for MasterReading composer — unified 13-layer integration."""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart
from app.core.dkp_modulation import Ashrama, DKPContext
from app.core.master_reading import (
    MasterReading, compose_master_reading, format_master_reading_text,
)


def _baseline_chart() -> Chart:
    return Chart(
        asc_sign=6, asc_lon=173.99,
        planet_signs={"Sun": 3, "Moon": 12, "Mars": 4, "Mercury": 3,
                      "Jupiter": 4, "Venus": 4, "Saturn": 9,
                      "Rahu": 12, "Ketu": 6},
        planet_houses={"Sun": 10, "Moon": 7, "Mars": 11, "Mercury": 10,
                       "Jupiter": 11, "Venus": 11, "Saturn": 4,
                       "Rahu": 7, "Ketu": 1},
        planet_lons={"Sun": 88.6, "Moon": 351.0, "Mars": 120.5,
                     "Mercury": 95.2, "Jupiter": 101.8, "Venus": 102.0,
                     "Saturn": 268.4, "Rahu": 348.5, "Ketu": 168.5},
        person_id="bangalore-baseline",
    )


class TestMinimalCompose:
    def test_returns_master_reading(self):
        """Minimal call (just chart) returns a MasterReading."""
        mr = compose_master_reading(_baseline_chart())
        assert isinstance(mr, MasterReading)

    def test_base_reading_present(self):
        """Base 9-phase reading is always included."""
        mr = compose_master_reading(_baseline_chart())
        assert mr.base_reading is not None
        assert len(mr.base_reading.bhava_claims) == 12

    def test_ashtakavarga_always_present(self):
        """Gap A — Ashtakavarga predictive needs only chart, always populated."""
        mr = compose_master_reading(_baseline_chart())
        assert mr.ashtakavarga is not None
        assert len(mr.ashtakavarga.sav_per_bhava) == 12

    def test_varga_confirmations_unknown_without_input(self):
        """Gap B — without varga_pillar_scores, all 12 confirmations land UNKNOWN."""
        mr = compose_master_reading(_baseline_chart())
        for conf in mr.varga_confirmations.values():
            assert conf.confirmation_label == "UNKNOWN"

    def test_arudhas_always_present(self):
        """Gap D arudhas always computable from chart."""
        mr = compose_master_reading(_baseline_chart())
        assert mr.arudha_lagna.bhava == 1
        assert mr.upapada_lagna.bhava == 12
        assert mr.dara_pada.bhava == 7
        assert len(mr.all_arudhas) == 12

    def test_sensitive_points_present(self):
        """Gap E — Bhrigu Bindu, Pranapada, Upagrahas always available."""
        mr = compose_master_reading(_baseline_chart())
        assert mr.sensitive_points.bhrigu_bindu is not None
        assert mr.sensitive_points.pranapada is not None
        assert len(mr.sensitive_points.upagrahas) == 5

    def test_avastha_present(self):
        """Gap F — Baladi + Deeptadi for visible planets."""
        mr = compose_master_reading(_baseline_chart())
        assert len(mr.avastha.baladi) >= 7
        assert len(mr.avastha.deeptadi) >= 7
        assert "Sun" in mr.avastha_multipliers

    def test_vimsopaka_present_d1_fallback(self):
        """Gap G — Vimsopaka with D1-only fallback when no varga signs provided."""
        mr = compose_master_reading(_baseline_chart())
        assert "Sun" in mr.vimsopaka
        # D1-only Vimsopaka caps at 5 (since D1 weight = 5/20)
        for r in mr.vimsopaka.values():
            assert r.composite_rupas <= 5.5

    def test_bhavat_chains_present(self):
        """Gap J — Bhāvāt Bhāvam common chains always present."""
        mr = compose_master_reading(_baseline_chart())
        assert len(mr.bhavat_chains) >= 10
        assert len(mr.triple_lagna_per_bhava) == 12


class TestOptionalLayers:
    def test_karakamsa_none_without_ak(self):
        """Karakamsa requires atmakaraka + d9 sign."""
        mr = compose_master_reading(_baseline_chart())
        assert mr.karakamsa is None

    def test_karakamsa_populated_with_ak(self):
        """When AK + AK D9 sign provided, Karakamsa is populated."""
        # Mercury at sign 3 (Gemini) in baseline; D9 sign approximation = 4
        mr = compose_master_reading(
            _baseline_chart(),
            atmakaraka="Mercury", atmakaraka_d9_sign=4,
        )
        assert mr.karakamsa is not None
        assert mr.karakamsa.atmakaraka == "Mercury"
        assert mr.karakamsa.karakamsa_sign == 4

    def test_yogini_none_without_moon_nakshatra(self):
        """Yogini dasha requires Moon's nakshatra index."""
        mr = compose_master_reading(_baseline_chart(), birth_jd=2447988.0, target_jd=2459580.0)
        assert mr.yogini_active is None
        assert mr.ashtottari_active is None

    def test_yogini_populated_with_full_inputs(self):
        """With moon_nakshatra + birth_jd + target_jd, Yogini activates."""
        mr = compose_master_reading(
            _baseline_chart(),
            birth_jd=2447988.0, target_jd=2459580.0,
            moon_nakshatra_index=11,  # Moon at Pisces ~351° = Revati area
        )
        assert mr.yogini_active is not None
        assert mr.ashtottari_active is not None

    def test_tara_none_without_target_nakshatra(self):
        """Tara Chakra needs both moon_nakshatra + target_nakshatra."""
        mr = compose_master_reading(
            _baseline_chart(), moon_nakshatra_index=11,
        )
        assert mr.tara_at_target is None

    def test_tara_present_with_both_nakshatras(self):
        mr = compose_master_reading(
            _baseline_chart(),
            moon_nakshatra_index=11, target_nakshatra_index=13,
        )
        assert mr.tara_at_target is not None

    def test_maandi_none_without_day_of_week(self):
        """Maandi requires day_of_week + is_day_birth."""
        mr = compose_master_reading(_baseline_chart())
        assert mr.sensitive_points.maandi is None

    def test_maandi_present_with_metadata(self):
        mr = compose_master_reading(
            _baseline_chart(), day_of_week=0, is_day_birth=True,
        )
        assert mr.sensitive_points.maandi is not None


class TestVargaConfirmationsWithInput:
    def test_with_varga_scores_yields_real_confirmation(self):
        """Caller-provided varga_pillar_scores produce CONFIRMED/AFFLICTED labels."""
        varga_scores = {7: 0.4, 10: -0.3, 5: 0.2}
        mr = compose_master_reading(
            _baseline_chart(), varga_pillar_scores=varga_scores,
        )
        # Bhava 7 should have a real confirmation label
        assert mr.varga_confirmations[7].confirmation_label != "UNKNOWN"
        # Bhava 1 still UNKNOWN (not in dict)
        assert mr.varga_confirmations[1].confirmation_label == "UNKNOWN"


class TestPrescribedRemedies:
    def test_remedies_list_present(self):
        """Prescriptions field is always a tuple (may be empty)."""
        mr = compose_master_reading(_baseline_chart())
        assert isinstance(mr.prescribed_remedies, tuple)

    def test_prescriptions_have_rationale(self):
        """Each prescription carries rationale + caveat."""
        mr = compose_master_reading(_baseline_chart())
        for rx in mr.prescribed_remedies:
            assert rx.rationale
            assert rx.gemstone_caveat in ("PROCEED", "TRIAL_REQUIRED", "AVOID")

    def test_prescriptions_capped_at_three(self):
        """Doctrinal rule: a real astrologer prescribes at most 3 remedies.

        Even when every visible graha would individually qualify (e.g. when
        running with D1-only Vimsopaka where all 7 grahas land in WEAK),
        the rank-and-cap step in _build_prescriptions must keep total at ≤3.
        """
        from app.core.master_reading import MAX_PRESCRIPTIONS
        mr = compose_master_reading(_baseline_chart())
        assert len(mr.prescribed_remedies) <= MAX_PRESCRIPTIONS

    def test_unique_planets_no_duplicates(self):
        """Same planet should never appear twice in the prescription list."""
        mr = compose_master_reading(_baseline_chart())
        planets = [rx.planet for rx in mr.prescribed_remedies]
        assert len(planets) == len(set(planets))

    def test_prescriptions_ordered_by_severity(self):
        """Top-of-list prescription should be for the worst-afflicted graha.

        Verifies the rank step actually sorts — not just truncates.
        """
        from app.core.master_reading import _planet_weakness_score
        mr = compose_master_reading(_baseline_chart())
        if len(mr.prescribed_remedies) < 2:
            return  # nothing to compare
        scores = []
        for rx in mr.prescribed_remedies:
            vlabel = mr.vimsopaka[rx.planet].strength_label
            amult = mr.avastha_multipliers[rx.planet]
            in_dushtana = (_baseline_chart().house_of(rx.planet) in {6, 8, 12})
            scores.append(_planet_weakness_score(vlabel, amult, in_dushtana))
        for a, b in zip(scores, scores[1:]):
            assert a >= b, "prescriptions not sorted by weakness desc"


class TestFormatMasterReading:
    def test_format_returns_string(self):
        mr = compose_master_reading(_baseline_chart())
        text = format_master_reading_text(mr)
        assert isinstance(text, str)
        assert len(text) > 100

    def test_format_includes_all_sections(self):
        mr = compose_master_reading(
            _baseline_chart(),
            atmakaraka="Mercury", atmakaraka_d9_sign=4,
            day_of_week=0, is_day_birth=True,
        )
        text = format_master_reading_text(mr)
        # Check headline sections appear
        for section in ["MASTER ASTROLOGER", "CHART STRENGTH", "ACTIVE DASHAS",
                        "KARAKAMSA", "ARUDHAS", "SENSITIVE POINTS",
                        "STRENGTH PER PLANET", "ASHTAKAVARGA",
                        "PER-BHAVA VERDICTS"]:
            assert section in text, f"missing section: {section}"

    def test_format_shows_maandi_when_provided(self):
        mr = compose_master_reading(
            _baseline_chart(), day_of_week=0, is_day_birth=True,
        )
        text = format_master_reading_text(mr)
        assert "Maandi" in text


class TestEndToEndIntegration:
    def test_full_inputs_no_crash(self):
        """Fully-loaded master reading composes without error."""
        ctx = DKPContext(
            ashrama=Ashrama.GRIHASTHA, age_years=35,
            marital_status="married", prashna="career direction",
        )
        transits = {
            "Sun": 1, "Moon": 5, "Mars": 8, "Mercury": 2,
            "Jupiter": 6, "Venus": 4, "Saturn": 6,
            "Rahu": 12, "Ketu": 6,
        }
        mr = compose_master_reading(
            _baseline_chart(), ctx,
            target_jd=2459580.0, birth_jd=2447988.0,
            atmakaraka="Mercury", atmakaraka_d9_sign=4,
            moon_nakshatra_index=11, target_nakshatra_index=13,
            day_of_week=0, is_day_birth=True,
            vimshottari_md_lord="Mercury",
            transit_signs=transits,
        )
        assert mr.base_reading is not None
        assert mr.karakamsa is not None
        assert mr.yogini_active is not None
        assert mr.tara_at_target is not None
        assert mr.sensitive_points.maandi is not None
