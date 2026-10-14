"""Jagradadi avastha — awake/dreaming/sleeping (BPHS ch.45 sl.5)."""
from __future__ import annotations

import pytest

from app.parashara.doctrine.sources import passage, verify
from app.parashara.primitives import jagradadi_avastha as J
from app.parashara.primitives.relationships import EXALTATION


class TestStates:
    def test_own_sign_is_jagrat(self):
        assert J.jagradadi_avastha("Mars", 1).state == "jagrat"      # Aries, own
        assert J.jagradadi_avastha("Saturn", 11).state == "jagrat"   # Aquarius, own

    def test_exaltation_is_jagrat(self):
        for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            assert J.jagradadi_avastha(p, EXALTATION[p]).state == "jagrat", p

    def test_debilitation_is_sushupti(self):
        """Debilitation (7th from exaltation) -> sleeping."""
        for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            debil = ((EXALTATION[p] - 1 + 6) % 12) + 1
            assert J.jagradadi_avastha(p, debil).state == "sushupti", p

    def test_friend_or_neutral_sign_is_swapna(self):
        """Jupiter in Cancer is exalt (jagrat); in a friend's sign like Aries (Mars, a friend) it
        dreams. Pick a case that is neither own/exalt/debil."""
        # Sun in Sagittarius (Jupiter's sign; Jupiter is the Sun's friend) -> swapna.
        assert J.jagradadi_avastha("Sun", 9).state == "swapna"

    def test_enemy_sign_is_sushupti(self):
        """Sun in Saturn's sign (Saturn is the Sun's enemy) -> sleeping. Capricorn (10) is Saturn's
        own and not the Sun's own/exalt/debil."""
        assert J.jagradadi_avastha("Sun", 10).state == "sushupti"


class TestGrades:
    def test_grades_full_medium_nil(self):
        assert J.RESULT_GRADE == {"jagrat": 1.0, "swapna": 0.5, "sushupti": 0.0}

    def test_grade_matches_state(self):
        a = J.jagradadi_avastha("Mars", 1)
        assert a.grade == 1.0 and a.state == "jagrat"


class TestConsistencyWithBhavaJudgment:
    def test_jagrat_coincides_with_ch11_prabuddha(self):
        """ch.11's prosperity clause (d) 'lord in own or exaltation (Prabuddha)' is exactly the
        jagrat condition — the two must agree, since Prabuddha IS Jagrad (BPHS-45:77)."""
        # own or exalt -> jagrat; anything else -> not jagrat.
        assert J.jagradadi_avastha("Mars", 1).state == "jagrat"           # own
        assert J.jagradadi_avastha("Mars", EXALTATION["Mars"]).state == "jagrat"  # exalt
        assert J.jagradadi_avastha("Sun", 9).state != "jagrat"            # friend's sign


class TestGuards:
    def test_nodes_rejected(self):
        with pytest.raises(ValueError):
            J.jagradadi_avastha("Rahu", 5)

    def test_bad_sign_rejected(self):
        with pytest.raises(ValueError):
            J.jagradadi_avastha("Mars", 13)

    def test_source_resolves(self):
        assert verify(J.STATE_SOURCE)
        assert "AWAKENING" in passage("BPHS-45:77")["text"].upper() or \
               "DREAMING" in passage("BPHS-45:77")["text"].upper()
