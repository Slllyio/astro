"""Tests for ``app.reading.computations.jaimini_drishti``.

Doctrine source: Jaimini Sutras Adhyaya 1, Pada 4 (Rashi-drishti).

Jaimini introduces a sign-based aspect scheme that is fundamentally
different from the Parashari graha-drishti:

  - Movable (Chara) signs   {1, 4, 7, 10} aspect all FIXED signs EXCEPT
                            the immediately-following sign (their 2nd
                            house from themselves).
  - Fixed (Sthira) signs    {2, 5, 8, 11} aspect all MOVABLE signs EXCEPT
                            the immediately-preceding sign (their 12th
                            house from themselves).
  - Dual (Dwiswabhava)      {3, 6, 9, 12} aspect all OTHER dual signs.

Worked example -- Aries (movable, sign 1):
  - Aries aspects Leo (5), Scorpio (8), Aquarius (11)
  - Aries does NOT aspect Taurus (2, the immediately-following fixed sign)
  - Aries does NOT aspect any movable sign or any dual sign

Symmetric / mutual property:
  - For movable M and fixed F: M aspects F iff F aspects M.
    Proof: M aspects F iff F is fixed and F != M+1 (mod 12).
           F aspects M iff M is movable and M != F-1 (mod 12).
    These two conditions are equivalent.
  - For dual D1, D2: D1 aspects D2 iff D2 aspects D1 (both are dual,
    excluding self-aspect).
"""
from __future__ import annotations

import pytest

from app.reading.schema import Finding


_MOVABLE = (1, 4, 7, 10)
_FIXED = (2, 5, 8, 11)
_DUAL = (3, 6, 9, 12)


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestComputeJaiminiDrishti:

    def test_returns_dict(self):
        from app.reading.computations.jaimini_drishti import (
            compute_jaimini_drishti,
        )

        result = compute_jaimini_drishti({}, asc_sign=1)
        assert isinstance(result, dict)

    def test_emits_finding_per_sign(self):
        """One Finding per sign (12 total)."""
        from app.reading.computations.jaimini_drishti import (
            compute_jaimini_drishti,
        )

        result = compute_jaimini_drishti({}, asc_sign=1)
        expected = {f"sign_{n}" for n in range(1, 13)}
        assert set(result.keys()) == expected

    def test_all_values_are_findings(self):
        from app.reading.computations.jaimini_drishti import (
            compute_jaimini_drishti,
        )

        result = compute_jaimini_drishti({}, asc_sign=1)
        for finding in result.values():
            assert isinstance(finding, Finding)

    def test_id_grammar(self):
        from app.reading.computations.jaimini_drishti import (
            compute_jaimini_drishti,
        )

        result = compute_jaimini_drishti({}, asc_sign=1)
        for n in range(1, 13):
            key = f"sign_{n}"
            assert result[key].id == f"foundation.jaimini_drishti.{key}"

    def test_classification_is_primitive(self):
        from app.reading.computations.jaimini_drishti import (
            compute_jaimini_drishti,
        )

        result = compute_jaimini_drishti({}, asc_sign=1)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdict_under_140_chars(self):
        from app.reading.computations.jaimini_drishti import (
            compute_jaimini_drishti,
        )

        result = compute_jaimini_drishti({}, asc_sign=1)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_doctrine_sentinel_in_evidence(self):
        from app.reading.computations.jaimini_drishti import (
            compute_jaimini_drishti,
        )

        result = compute_jaimini_drishti({}, asc_sign=1)
        for finding in result.values():
            joined = " ".join(finding.evidence)
            assert "Jaimini" in joined


# ---------------------------------------------------------------------------
# Rule correctness (Jaimini Sutras 1.4)
# ---------------------------------------------------------------------------


class TestMovableSignAspects:
    """Movable signs aspect fixed signs except the immediately-following one."""

    def test_aries_aspects(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        # Aries (1) aspects Leo (5), Scorpio (8), Aquarius (11)
        # Does NOT aspect Taurus (2, immediately-following fixed sign)
        result = _signs_aspected_by(1)
        assert set(result) == {5, 8, 11}

    def test_cancer_aspects(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        # Cancer (4) aspects Scorpio (8), Aquarius (11), Taurus (2)
        # Does NOT aspect Leo (5, immediately-following)
        result = _signs_aspected_by(4)
        assert set(result) == {8, 11, 2}

    def test_libra_aspects(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        # Libra (7) aspects Aquarius (11), Taurus (2), Leo (5)
        # Does NOT aspect Scorpio (8, immediately-following)
        result = _signs_aspected_by(7)
        assert set(result) == {11, 2, 5}

    def test_capricorn_aspects(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        # Capricorn (10) aspects Taurus (2), Leo (5), Scorpio (8)
        # Does NOT aspect Aquarius (11, immediately-following)
        result = _signs_aspected_by(10)
        assert set(result) == {2, 5, 8}


class TestFixedSignAspects:
    """Fixed signs aspect movable signs except the immediately-preceding one."""

    def test_taurus_aspects(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        # Taurus (2) aspects Cancer (4), Libra (7), Capricorn (10)
        # Does NOT aspect Aries (1, immediately-preceding)
        result = _signs_aspected_by(2)
        assert set(result) == {4, 7, 10}

    def test_leo_aspects(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        # Leo (5) aspects Libra (7), Capricorn (10), Aries (1)
        # Does NOT aspect Cancer (4, immediately-preceding)
        result = _signs_aspected_by(5)
        assert set(result) == {7, 10, 1}

    def test_scorpio_aspects(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        # Scorpio (8) aspects Capricorn (10), Aries (1), Cancer (4)
        # Does NOT aspect Libra (7, immediately-preceding)
        result = _signs_aspected_by(8)
        assert set(result) == {10, 1, 4}

    def test_aquarius_aspects(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        # Aquarius (11) aspects Aries (1), Cancer (4), Libra (7)
        # Does NOT aspect Capricorn (10, immediately-preceding)
        result = _signs_aspected_by(11)
        assert set(result) == {1, 4, 7}


class TestDualSignAspects:
    """Dual signs aspect every other dual sign."""

    def test_gemini_aspects(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        # Gemini (3) aspects Virgo (6), Sagittarius (9), Pisces (12)
        result = _signs_aspected_by(3)
        assert set(result) == {6, 9, 12}

    def test_virgo_aspects(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        result = _signs_aspected_by(6)
        assert set(result) == {3, 9, 12}

    def test_sagittarius_aspects(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        result = _signs_aspected_by(9)
        assert set(result) == {3, 6, 12}

    def test_pisces_aspects(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        result = _signs_aspected_by(12)
        assert set(result) == {3, 6, 9}


# ---------------------------------------------------------------------------
# Symmetry property (the killer one)
# ---------------------------------------------------------------------------


class TestSymmetry:
    """If sign A aspects sign B then sign B must aspect sign A."""

    def test_aspect_graph_is_symmetric(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        for a in range(1, 13):
            for b in _signs_aspected_by(a):
                back = _signs_aspected_by(b)
                assert a in back, (
                    f"sign {a} aspects {b} but {b} does not aspect {a}"
                )


class TestPropertyExactAspectCount:
    """Each sign aspects exactly 3 others under Jaimini rashi-drishti."""

    def test_every_sign_aspects_exactly_three(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        for sign in range(1, 13):
            assert len(_signs_aspected_by(sign)) == 3, (
                f"sign {sign} aspects "
                f"{_signs_aspected_by(sign)} (expected 3)"
            )

    def test_no_self_aspect(self):
        from app.reading.computations.jaimini_drishti import _signs_aspected_by

        for sign in range(1, 13):
            assert sign not in _signs_aspected_by(sign)


# ---------------------------------------------------------------------------
# Sign category helper
# ---------------------------------------------------------------------------


class TestSignCategory:

    def test_movable_signs(self):
        from app.reading.computations.jaimini_drishti import _sign_category

        for s in _MOVABLE:
            assert _sign_category(s) == "movable"

    def test_fixed_signs(self):
        from app.reading.computations.jaimini_drishti import _sign_category

        for s in _FIXED:
            assert _sign_category(s) == "fixed"

    def test_dual_signs(self):
        from app.reading.computations.jaimini_drishti import _sign_category

        for s in _DUAL:
            assert _sign_category(s) == "dual"


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------


class TestArgumentValidation:

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.jaimini_drishti import (
            compute_jaimini_drishti,
        )

        with pytest.raises(ValueError):
            compute_jaimini_drishti({}, asc_sign=0)
        with pytest.raises(ValueError):
            compute_jaimini_drishti({}, asc_sign=13)

    def test_invalid_sign_in_helper_raises(self):
        from app.reading.computations.jaimini_drishti import (
            _signs_aspected_by, _sign_category,
        )

        with pytest.raises(ValueError):
            _signs_aspected_by(0)
        with pytest.raises(ValueError):
            _signs_aspected_by(13)
        with pytest.raises(ValueError):
            _sign_category(0)
