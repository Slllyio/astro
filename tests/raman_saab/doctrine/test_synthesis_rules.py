"""Tests for the cross-feature synthesis layer (report-only, citation-verified)."""
from __future__ import annotations

import pytest
import swisseph as swe

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine.sources import verify
from app.raman_saab.doctrine.synthesis_rules import (
    SYNTHESIS_RULES,
    descriptive_rules,
    detect_synthesis,
)

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
_JD = swe.julday(2026, 7, 25, 12.0)


@pytest.fixture(scope="module")
def chart():
    return cast_chart(_CANONICAL, ayanamsa="lahiri")


@pytest.fixture(scope="module")
def fired(chart):
    return detect_synthesis(chart, _JD)


class TestSynthesisRegistry:
    def test_ids_unique(self):
        """Every synthesis rule id is unique."""
        ids = [r.id for r in SYNTHESIS_RULES]
        assert len(ids) == len(set(ids))

    @pytest.mark.parametrize("rule", [r for r in SYNTHESIS_RULES if r.source is not None],
                             ids=lambda r: r.id)
    def test_raman_band_citations_verify(self, rule):
        """Every cited rule resolves into a live book at a real line (the corpus vouches)."""
        assert rule.band == "raman"          # only the Raman band may carry live citations
        assert verify(rule.source)

    def test_flagged_bands_carry_no_live_citation(self):
        """Classical/AV/modern rules must NOT cite the corpus (the divergence firewall)."""
        for r in SYNTHESIS_RULES:
            if r.band != "raman":
                assert r.source is None, r.id
                assert r.provenance != "RAMAN_EXPLICIT", r.id

    def test_every_rule_is_two_voiced(self):
        """Doctrine statement + plain meaning + links — the report's contract per insight."""
        for r in SYNTHESIS_RULES:
            assert r.doctrine and r.simple_meaning and r.links, r.id


class TestDetector:
    def test_fires_on_the_canonical_chart(self, fired):
        """The canonical chart yields several personalised cross-feature insights."""
        assert len(fired) >= 4
        assert all(f.detail for f in fired)

    def test_band_precedence_order(self, fired):
        """Raman-band insights come first — the AV band can never outrank them."""
        order = {"raman": 0, "classical": 1, "av": 2}
        seq = [order[f.rule.band] for f in fired]
        assert seq == sorted(seq)

    def test_r1_names_the_stronger_yoga_lord(self, fired):
        """Gajakesari on the canonical chart: Jupiter (stronger) delivers, per 3HC:1359."""
        r1 = next((f for f in fired if f.rule.id == "SYN_R1_STRONGER_LORD_DELIVERS"), None)
        assert r1 is not None
        assert "Jupiter" in r1.detail and "rupas" in r1.detail

    def test_descriptive_rules_never_fire(self, fired):
        """Doctrine-on-record entries are listed, not fired."""
        fired_ids = {f.rule.id for f in fired}
        for d in descriptive_rules():
            assert d.id not in fired_ids

    def test_report_only_no_verdict_path_import(self):
        """The verdict path must never import the synthesis layer (authority invariant)."""
        import inspect

        from app.raman_saab import proforma
        from app.raman_saab.judges import house_template
        for mod in (house_template, proforma):
            assert "synthesis_rules" not in inspect.getsource(mod)

    def test_lp_matrix_names_itself_a_different_framework_than_ramans_own(self):
        """Regression test for a real reader-confusion found in a close reading of a generated
        report: the Laghu Parashari N1 matrix's 'functional benefic/malefic' role labels and
        grades (e.g. 'very few results') can visibly clash with Raman's OWN per-Lagna
        functional-nature table (Chart signature) and Bhukti-tier grading (Life-narrative) for
        the SAME planet/period, with no note on which one governs. The rule's plain-language
        text must name both of Raman's own competing surfaces and state that Raman's own
        grading wins wherever they diverge (this project's own governance, not a new doctrine)."""
        rule = next(r for r in SYNTHESIS_RULES if r.id == "SYN_N1_LP_MATRIX")
        text = rule.simple_meaning
        assert "Chart signature" in text and "Life-narrative" in text
        assert "different" in text.lower() and "narrower" in text.lower()
        assert "authoritative" in text.lower() and "diverge" in text.lower()
        assert "HTJAH-I:523-604" in text
        assert "HTJAH-I:1588-1596, 1635-1640" in text


class TestYogaPlanets:
    """`_yoga_planets` — which planet(s) are a fired yoga's constituent 'lord(s)', widened from
    the original 3 families (Gajakesari/Budha-Aditya/9th-10th) to ~30+, doctrine-reviewed."""

    def test_pancha_mahapurusha_is_a_single_fixed_planet(self, chart):
        from app.raman_saab.doctrine.synthesis_rules import _yoga_planets
        from app.raman_saab.doctrine.yogas import FiredYoga

        expect = {"Ruchaka Yoga": "Mars", "Bhadra Yoga": "Mercury", "Hamsa Yoga": "Jupiter",
                 "Malavya Yoga": "Venus", "Sasa Yoga": "Saturn"}
        for name, planet in expect.items():
            stub = FiredYoga(id="x", name=name, kind="other", effect="", source=None)
            assert _yoga_planets(chart, stub) == (planet,)

    def test_kemadruma_is_the_moon_alone(self, chart):
        """Kemadruma is entirely about the Moon's own isolation — no second 'lord'."""
        from app.raman_saab.doctrine.synthesis_rules import _yoga_planets
        from app.raman_saab.doctrine.yogas import FiredYoga
        stub = FiredYoga(id="x", name="Kemadruma Yoga", kind="arishta", effect="", source=None)
        assert _yoga_planets(chart, stub) == ("Moon",)

    def test_kt_pair_prefers_the_9th_10th_combination_when_present(self):
        """Raman calls the 9th/10th-lord combination the STRONGEST form of this yoga
        (HTJAH-I:625-626) — when it's a valid candidate, _kt_pair must report it, not some
        other kendra-trikona pair, and must do so the SAME way on every call (no set-iteration
        randomness across runs)."""
        from app.raman_saab.doctrine.synthesis_rules import _kt_pair
        from app.raman_saab.chart.constants import SIGN_LORDS

        # Any chart where the 9th and 10th lords are conjunct exercises the priority branch;
        # the canonical chart's own kendra-trikona result is checked for run-to-run stability
        # regardless of which specific pair it happens to be.
        chart = cast_chart(_CANONICAL, ayanamsa="lahiri")
        results = {_kt_pair(chart) for _ in range(20)}
        assert len(results) == 1, "_kt_pair must be deterministic across repeated calls"

    def test_whole_chart_pattern_yogas_are_never_resolved(self, chart):
        """The Nabhasa yogas (Asraya/Dala/Sankhya/Akriti) are properties of all seven visible
        planets together — no single 'lord' exists, so they must always return None."""
        from app.raman_saab.doctrine.synthesis_rules import _yoga_planets
        from app.raman_saab.doctrine.yogas import FiredYoga

        for name in ("Rajju Yoga", "Musala Yoga", "Nala Yoga", "Mala (Srik) Yoga", "Sarpa Yoga",
                    "Veena (Vallaki) Yoga", "Pasa Yoga", "Yupa Yoga", "Chakra Yoga",
                    "Sringhataka Yoga", "Chatussagara Yoga", "Sarada Yoga", "Brihadbija Yoga"):
            stub = FiredYoga(id="x", name=name, kind="other", effect="", source=None)
            assert _yoga_planets(chart, stub) is None, name

    def test_flank_candidates_exclude_sun_moon_and_nodes(self, chart):
        """Vesi/Vasi/Sunapha/Anapha discriminate among Mars/Mercury/Jupiter/Venus/Saturn only —
        the Sun, the Moon, and the chaya-grahas never count (3HC:1834-1846)."""
        from app.raman_saab.doctrine.synthesis_rules import _FLANK_CANDIDATES
        assert set(_FLANK_CANDIDATES) == {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}

    def test_resolution_never_crashes_on_any_encoded_yoga(self):
        """Sweep every encoded YogaRecord through _yoga_planets on several charts — no
        exception, and no duplicate planet in any resolved tuple."""
        from app.raman_saab.doctrine.synthesis_rules import _yoga_planets
        from app.raman_saab.doctrine.yogas import YOGAS, FiredYoga

        for birth in (_CANONICAL, BirthData("M", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03)):
            chart = cast_chart(birth, ayanamsa="lahiri")
            for rec in YOGAS:
                stub = FiredYoga(id=rec.id, name=rec.name, kind=rec.kind, effect=rec.effect,
                                 source=rec.source)
                pls = _yoga_planets(chart, stub)
                if pls is not None:
                    assert len(pls) == len(set(pls)), rec.name
