"""Tests for ``app.reading.computations.arudha_upapada``.

Doctrine lock D-2: Arudha exception rule
   The 1st-or-7th-from-bhava shift to the 10th from the pada is applied
   uniformly to A1..A12, UL, and UL2 (per Sanjay Rath's Crux of Vedic
   Astrology, BPHS Vol.I Ch.29 vv.4-5).

Algorithm summary:
    For bhava B with lord L, where L sits in sign S_L:
        - count_from_B = (S_L - S_B) mod 12 + 1 (1-indexed houses)
        - raw_pada = (S_L + count_from_B - 1) mod 12 + 1 -- same step from L
        - equivalent closed form: pada = (2 * S_L - S_B - 1) mod 12 + 1
    Exception (D-2):
        Let rel_to_B = ((pada - S_B) mod 12) + 1  -- house of pada from bhava
        If rel_to_B == 1 (same sign as bhava) OR rel_to_B == 7 (opposite),
        shift pada to 10th from itself: pada' = ((pada + 9 - 1) mod 12) + 1

Bangalore baseline trace (Virgo Lagna, all D1 signs above):
    Lagna lord Mercury -> in Cancer (sign 4)
    AL raw = 2*4 - 6 = 2 (Taurus). 2 from Lagna(6): (2-6) mod 12 + 1 = 9.
    9th from Lagna -> not 1st or 7th -> no exception.
    AL = Taurus (2).
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Bangalore baseline fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bangalore_chart() -> dict:
    from app.core.ephemeris_engine import calculate_all_charts

    return calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0,
        tz_offset=5.5, latitude=12.97, longitude=77.59,
    )


@pytest.fixture(scope="module")
def d1_chart(bangalore_chart) -> dict:
    return bangalore_chart["d1"]


@pytest.fixture(scope="module")
def asc_sign(bangalore_chart) -> int:
    """Ascendant sign (1-indexed) for the Bangalore baseline."""
    return bangalore_chart["ascendant"]["sign"]


_EXPECTED_KEYS = (
    "al", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9", "a10",
    "a11", "a12", "ul", "ul2",
)


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestComputeArudhaPadas:

    def test_returns_mapping_with_all_padas(self, d1_chart, asc_sign):
        from app.reading.computations.arudha_upapada import compute_arudha_padas

        result = compute_arudha_padas(d1_chart, asc_sign)
        assert isinstance(result, dict)
        assert set(result.keys()) == set(_EXPECTED_KEYS)

    def test_emits_findings(self, d1_chart, asc_sign):
        from app.reading.computations.arudha_upapada import compute_arudha_padas
        from app.reading.schema import Finding

        result = compute_arudha_padas(d1_chart, asc_sign)
        for key, finding in result.items():
            assert isinstance(finding, Finding), f"{key} is not a Finding"

    def test_id_grammar(self, d1_chart, asc_sign):
        from app.reading.computations.arudha_upapada import compute_arudha_padas

        result = compute_arudha_padas(d1_chart, asc_sign)
        for key, finding in result.items():
            assert finding.id == f"primitive.arudha.{key}", (
                f"unexpected id {finding.id!r} for key {key!r}"
            )

    def test_classification_is_primitive(self, d1_chart, asc_sign):
        from app.reading.computations.arudha_upapada import compute_arudha_padas

        result = compute_arudha_padas(d1_chart, asc_sign)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdicts_under_140_chars(self, d1_chart, asc_sign):
        from app.reading.computations.arudha_upapada import compute_arudha_padas

        result = compute_arudha_padas(d1_chart, asc_sign)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_al_verdict_mentions_arudha_lagna(self, d1_chart, asc_sign):
        from app.reading.computations.arudha_upapada import compute_arudha_padas

        result = compute_arudha_padas(d1_chart, asc_sign)
        assert "Arudha Lagna" in result["al"].verdict


# ---------------------------------------------------------------------------
# Bangalore baseline pinned values
# ---------------------------------------------------------------------------


class TestBangaloreBaselineArudhaValues:
    """Hand-traced pada signs for Bangalore (Virgo Lagna).

    Sign indices in this trace are 1-indexed (1 = Aries .. 12 = Pisces).
    Bhava sign = (asc_sign - 1 + (bhava - 1)) mod 12 + 1.
    For Virgo Lagna (asc=6):
        B1=Vir(6),  B2=Lib(7), B3=Sco(8),  B4=Sag(9),  B5=Cap(10), B6=Aqu(11),
        B7=Pis(12), B8=Ari(1), B9=Tau(2), B10=Gem(3), B11=Can(4), B12=Leo(5).
    Lord signs from chart:
        Mercury(L6)=Cancer(4)   -> for L1 (Virgo) and L10 (Gemini)
        Venus (L7)=Gemini(3)    -> for L2 (Libra) and L9 (Taurus)
        Mars(L1,L8)=Aries(1)    -> for L3 (Scorpio) and L8 (Aries-as-bhava)
        Jupiter(L9,L12)=Gemini(3) -> for L4 (Sagittarius) and L7 (Pisces)
        Saturn(L10,L11)=Sagittarius(9) -> for L5 (Capricorn) and L6 (Aquarius)
        Sun(L5)=Gemini(3)
        Moon(L4)=Pisces(12)

    Pada formula: P = (2*L - B - 1) mod 12 + 1, then exception D-2.
    """

    def test_arudha_lagna_for_virgo_ascendant(self, d1_chart, asc_sign):
        """AL = 2*4 - 6 = 2 (Taurus). Not in 1st/7th -> no shift."""
        from app.reading.computations.arudha_upapada import compute_arudha_padas

        result = compute_arudha_padas(d1_chart, asc_sign)
        # Verdict like 'Arudha Lagna in Taurus' or 'Arudha Lagna in Taurus (...)'
        verdict = result["al"].verdict
        assert "Taurus" in verdict, f"AL verdict was {verdict!r}"

    def test_a7_pada_bangalore(self, d1_chart, asc_sign):
        """A7: bhava=Pisces(12), lord Jupiter sits in Gemini(3).
        Raw pada = (2*3 - 12 - 1) mod 12 + 1 = -7 mod 12 + 1 = 5+1 = 6 (Virgo).
        Relative to B7(=12): ((6-12) mod 12) + 1 = 6+1 = 7 -> EXCEPTION fires.
        Shift to 10th from pada(6): ((6+9-1) mod 12) + 1 = 14 mod 12 + 1 = 3
        -> Gemini (3)."""
        from app.reading.computations.arudha_upapada import compute_arudha_padas

        result = compute_arudha_padas(d1_chart, asc_sign)
        verdict = result["a7"].verdict
        assert "Gemini" in verdict, f"A7 verdict was {verdict!r}"

    def test_upapada_lagna_bangalore(self, d1_chart, asc_sign):
        """UL is the Arudha pada of the 12th house (B12 = Leo, lord Sun in Gemini).
        Raw = (2*3 - 5 - 1) mod 12 + 1 = 0 mod 12 + 1 = 1 (Aries).
        Relative to B12(=5): ((1-5) mod 12) + 1 = 8+1 = 9 -> not 1/7.
        UL = Aries (1)."""
        from app.reading.computations.arudha_upapada import compute_arudha_padas

        result = compute_arudha_padas(d1_chart, asc_sign)
        verdict = result["ul"].verdict
        assert "Aries" in verdict, f"UL verdict was {verdict!r}"


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestArudhaPadaProperties:

    def test_all_padas_in_valid_sign_range(self, d1_chart, asc_sign):
        """Every pada sign must be in 1..12 (Aries..Pisces)."""
        from app.reading.computations.arudha_upapada import compute_arudha_padas

        result = compute_arudha_padas(d1_chart, asc_sign)
        # The pada sign is embedded in the verdict; the evidence carries
        # 'pada_sign=<n>' explicitly.
        for key, finding in result.items():
            sign_str = None
            for line in finding.evidence:
                if line.startswith("pada_sign="):
                    sign_str = line.split("=", 1)[1]
                    break
            assert sign_str is not None, f"{key} missing pada_sign evidence"
            sign_n = int(sign_str)
            assert 1 <= sign_n <= 12, (
                f"{key} pada_sign {sign_n} out of range 1..12"
            )

    def test_d2_exception_blocks_self_referential_pada(self, d1_chart, asc_sign):
        """Per D-2 invariant: after exception, no pada should equal its bhava
        sign (1st-from-bhava case)."""
        from app.reading.computations.arudha_upapada import compute_arudha_padas

        result = compute_arudha_padas(d1_chart, asc_sign)
        # A1..A12 only; UL/UL2 are bhava-padas of B12 (already covered).
        bhava_map = {f"a{i}": i for i in range(2, 13)}
        bhava_map["al"] = 1
        for key, bhava_n in bhava_map.items():
            finding = result[key]
            for line in finding.evidence:
                if line.startswith("pada_sign="):
                    pada_sign = int(line.split("=", 1)[1])
                    break
            bhava_sign = (asc_sign - 1 + (bhava_n - 1)) % 12 + 1
            # After exception, pada must not equal bhava sign.
            assert pada_sign != bhava_sign, (
                f"{key} pada_sign {pada_sign} == bhava_sign {bhava_sign}; "
                "D-2 exception (1st-from-bhava) should have shifted it"
            )
            # After exception, pada must not be 7th from bhava either.
            seventh = ((bhava_sign - 1 + 6) % 12) + 1
            assert pada_sign != seventh, (
                f"{key} pada_sign {pada_sign} == 7th-from-bhava {seventh}; "
                "D-2 exception (7th-from-bhava) should have shifted it"
            )
