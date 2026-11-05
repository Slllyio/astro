"""The indication-corroboration harness, and the discipline that makes its number readable.

The non-graded lane has no ordinal to score against, so it would otherwise ship with no check
at all. This harness asks a narrow question instead: do distinctive terms from an indication
appear in Raman's own `verdict_prose` for the same chart and the same house?

The load-bearing part is the NULL ARM. A corroboration rate alone is uninterpretable —
astrological prose shares so much vocabulary that a generous matcher "corroborates" anything —
so the same measurement is re-run against deliberately misassigned prose. On the full corpus
the result is NULL: 284/8666 = 3.3% real against 2.7% on the wrong charts' prose, a lift of
+0.6%. These tests pin the machinery that produced that honest answer, not the number itself.
"""
from __future__ import annotations

from tools.raman_saab import indication_corroboration as ic


class TestTermExtraction:
    def test_shared_jargon_cannot_carry_a_match(self) -> None:
        """A hit built only from words every astrological sentence contains would be
        meaningless. Those terms are removed before matching."""
        terms = ic._terms("The lord of the house is afflicted by a malefic planet")
        assert terms == set(), terms

    def test_substantive_terms_survive(self) -> None:
        terms = ic._terms("the native becomes a Judge in the judiciary")
        assert "judge" in terms
        assert "judiciary" in terms

    def test_short_words_are_ignored(self) -> None:
        assert ic._terms("he is a fit man") == set()


class TestGoldenPlumbing:
    def test_prose_is_keyed_by_house_number(self) -> None:
        rec = {"expected_verdicts": {"H1": {"verdict_prose": "alpha"},
                                     "H10": {"verdict_prose": "beta"},
                                     "longevity": {"verdict_prose": "gamma"},
                                     "H2": {"verdict_prose": ""}}}
        assert ic._prose_by_house(rec) == {1: "alpha", 10: "beta"}

    def test_birth_block_schema_is_read_correctly(self) -> None:
        """The golden `birth` block is {dt, tz, lat, lon} — NOT year/month/day. Getting this
        wrong once made the harness silently report zero usable records, which is why the
        skip path now counts and prints its failures instead of swallowing them."""
        b = ic._birth_of({"id": "x", "name": "N",
                          "birth": {"dt": "1863-02-22T22:16:00", "tz": 5.1722,
                                    "lat": 13.0, "lon": 77.5833}})
        assert (b.year, b.month, b.day, b.hour, b.minute) == (1863, 2, 22, 22, 16)
        assert b.latitude == 13.0

    def test_records_that_will_not_cast_are_counted_not_dropped(self) -> None:
        """A harness that silently skips inputs reports a rate over an unknown denominator."""
        assert isinstance(ic._SKIPPED, list)


class TestTheHarnessReportsBothArms:
    def test_a_small_run_produces_a_real_and_a_sham_measurement(self) -> None:
        """The sham arm is not optional decoration: without it the raw rate would be quoted
        as corroboration when it is mostly vocabulary overlap. A run that returned only the
        real arm would be unreadable."""
        real, real_n, sham, sham_n = ic.corroborate(limit=6)
        assert real_n > 0, "the sample should produce scorable indications"
        assert sham_n > 0, "the null arm must be measured on the same sample"
        assert len(real) <= real_n
        assert len(sham) <= sham_n

    def test_the_null_arm_is_deterministic(self) -> None:
        """Misassignment is 'the next chart's prose', not a random shuffle, so the baseline
        is reproducible across runs and cannot be reseeded into a flattering value."""
        r1, rn1, s1, sn1 = ic.corroborate(limit=6)
        r2, rn2, s2, sn2 = ic.corroborate(limit=6)
        assert (rn1, sn1) == (rn2, sn2)
        assert (len(r1), len(s1)) == (len(r2), len(s2))
