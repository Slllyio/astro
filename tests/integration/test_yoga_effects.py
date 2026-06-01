"""M5 tests: yoga_effect_translator."""

from __future__ import annotations

import pytest

from app.integration.yoga_effects import (
    YogaEffect,
    _YOGA_EFFECTS,
    translate_yoga_effects,
)
from app.reading.proforma import compute as track_a_compute
from app.reading.schema import ChartInput


@pytest.fixture(scope="module")
def mainpuri_reading():
    return track_a_compute(
        ChartInput(dob="1989-10-12", time="10:02", tz="+05:30",
                   lat=27.23, lon=79.03),
        enrich=False,
    )


# ---------------------------------------------------------------------------
# Curated effect table
# ---------------------------------------------------------------------------

class TestCuratedEffects:
    def test_adhi_has_effect_text(self):
        text, source = _YOGA_EFFECTS["adhi"]
        assert "leader" in text.lower() or "counsel" in text.lower()
        assert "BPHS" in source

    def test_all_curated_effects_have_source(self):
        for key, (text, source) in _YOGA_EFFECTS.items():
            assert len(text) > 10
            assert len(source) > 5

    def test_pancha_mahapurusha_yogas_present(self):
        for yk in ("hamsa", "malavya", "ruchaka", "bhadra", "sasa"):
            assert yk in _YOGA_EFFECTS


# ---------------------------------------------------------------------------
# Mainpuri yoga effects
# ---------------------------------------------------------------------------

class TestMainpuriYogaEffects:
    @pytest.fixture(scope="class")
    def effects(self, mainpuri_reading):
        return translate_yoga_effects(mainpuri_reading)

    def test_returns_list(self, effects):
        assert isinstance(effects, list)
        assert all(isinstance(e, YogaEffect) for e in effects)

    def test_adhi_has_classical_effect(self, effects):
        adhi = next((e for e in effects if e.yoga_name == "adhi"), None)
        assert adhi is not None
        assert adhi.classical_effect != ""
        assert "leader" in adhi.classical_effect.lower() or "counsel" in adhi.classical_effect.lower()

    def test_adhi_detected_by_both(self, effects):
        adhi = next((e for e in effects if e.yoga_name == "adhi"), None)
        assert adhi.detected_by == "both"

    def test_each_effect_has_detected_by_label(self, effects):
        for e in effects:
            assert e.detected_by in ("both", "track_a_only", "track_b_only")

    def test_uncurated_yoga_emits_empty_effect_with_note(self, effects):
        """Yogas without curated effect text get an empty effect + a note."""
        uncurated = [e for e in effects if e.classical_effect == ""]
        for e in uncurated:
            assert any("no curated effect" in n.lower() for n in e.notes)

    def test_at_least_one_yoga_has_effect_text(self, effects):
        with_effect = [e for e in effects if e.classical_effect]
        assert len(with_effect) >= 1


class TestSerialization:
    def test_yoga_effect_roundtrip(self, mainpuri_reading):
        import json
        effects = translate_yoga_effects(mainpuri_reading)
        for e in effects[:3]:
            text = json.dumps(e.model_dump(mode="json"))
            revived = YogaEffect.model_validate(json.loads(text))
            assert revived.yoga_name == e.yoga_name
            assert revived.detected_by == e.detected_by
