"""House 5, swept UNBIASED — and the result was deliberately allowed to come back clean.

House 8 returned 7 of 7 defective, but House 8 is where a defect had already been found.
Extrapolating that rate would have repeated the selected-pool error this project has paid for
once (the "88.4% ceiling" that turned out to be a ceiling on a pool selected to contain
agreements). House 5 was chosen for volume, not suspicion, and the reviewer was told in the
prompt that "all twelve are correctly encoded" would be a useful answer.

**It came back 5 of 12 correctly encoded, with ZERO inversions.** That is the number that
matters: House 8's seven defects were inversions — a reading asserting of a chart the opposite
of what the branch had just measured. House 5 has none. Its seven are milder and of four
kinds, each pinned below:

* text dropped by SENTIMENT (L.1 lost "will have foes" from a favourable arm),
* a THIRD TIER the binary branch cannot express (L.4's "moderately strong"),
* an ENCODER-INVENTED slot (L.8's "no specific benefit noted", in neither volume),
* UNCONDITIONED readings misfiled as strength-conditioned (L.9, L.11, L.12),
* and one SEPARATE combination folded into a fortification arm (L.10's Sun aspect).

Four of the seven repeat repairs this project had already shipped elsewhere for the identical
textual shape, which is corroboration rather than reviewer over-reach.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets import ALL_RULES

_R = {r.id: r for r in ALL_RULES}

#: The five the review VALIDATED. Pinned so a later sweep cannot quietly "fix" what is right.
CORRECT = ["H5.L.2", "H5.L.3", "H5.L.5", "H5.L.6", "H5.L.7"]


class TestTheFiveThatWereAlreadyRight:
    @pytest.mark.parametrize("rid", CORRECT)
    def test_both_poles_kept_and_no_general_invented(self, rid) -> None:
        """Raman gives an explicit favourable opener and its complement in these five, and no
        unconditioned base. Inventing a `general` here would assert prose he never wrote."""
        r = _R[rid]
        assert r.fortified and r.afflicted, rid
        assert r.general is None, f"{rid} has no unconditioned reading in Raman"

    def test_the_entry_that_proves_weak_and_afflicted_differ_in_htjah_i_too(self) -> None:
        """HTJAH-I:5121 reads "Lord weak AND afflicted" — a conjunction of two qualifiers,
        where every other entry says plain "afflicted". Raman would not conjoin synonyms, so
        the weak/afflicted distinction established in HTJAH-II holds in this volume as well.
        H5.L.2 fires on a superset of his antecedent (weak alone) but never inverts."""
        assert _R["H5.L.2"].fortified and _R["H5.L.2"].afflicted


class TestTextDroppedBySentiment:
    def test_h5_l1_regains_the_negative_item_deleted_from_its_favourable_arm(self) -> None:
        """HTJAH-I:5114 lists "will have foes" BETWEEN "few children" and "gives happiness to
        others". The encoding kept both flanking items and deleted the one in the middle —
        the signature of trimming by sentiment rather than by antecedent."""
        f = _R["H5.L.1"].fortified
        assert "will have foes" in f
        assert "few children" in f and "gives happiness to others" in f


class TestTheThirdTierTheBranchCannotExpress:
    """Raman partitions three ways in this table; `_branch` is binary. The middle tier cannot
    be encoded, so it must be recorded as unreachable rather than welded into a pole."""

    def test_h5_l4_afflicted_holds_only_the_affliction_clause(self) -> None:
        """It welded "The lord, afflicted, causes death of children" (5134) to "The lord,
        moderately strong, confers daughters and no sons" (5134-5135). Under the binary
        branch both displayed together — telling one reader that children die AND that
        daughters are born, outcomes Raman assigns to different tiers."""
        a = _R["H5.L.4"].afflicted
        assert "death of children" in a
        assert "moderate" not in a and "daughters" not in a

    def test_the_moderate_tiers_are_recorded_as_unreachable_not_lost(self) -> None:
        """H5.L.1a is on the NATURE axis ("moderately good"), H5.L.4a on the STRENGTH axis
        ("moderately strong"). Both are stated by Raman and neither is encodable today."""
        for rid in ("H5.L.1a", "H5.L.4a"):
            r = _R[rid]
            assert r.kind == "descriptive" and r.condition is None, rid
            assert "TODO(predicate:" in r.general, rid
        # 2026-10-13 research: the blocker is doctrine (Raman prints no middle level), not a
        # missing Shadbala band -- the TODO now says so, to stop anyone building one.
        assert "PARKED by research" in _R["H5.L.4a"].general
        assert "Do NOT build a Shadbala band" in _R["H5.L.4a"].general


class TestTheInventedSlot:
    def test_h5_l8_no_longer_asserts_an_editorial_remark_as_ramans_reading(self) -> None:
        """`fortified` read "no specific benefit noted" — a phrase in neither volume. Cleared,
        NOT relocated, per the H10.L.1 precedent: moving unsourced prose into `general` would
        launder it into a slot asserting Raman said it."""
        r = _R["H5.L.8"]
        for slot in ("general", "fortified", "afflicted"):
            assert "no specific benefit" not in (getattr(r, slot) or ""), slot

    def test_h5_l8_now_shows_ramans_only_reading_to_every_chart(self) -> None:
        """HTJAH-I:5153-5154 is four flat declaratives with no conditional clause anywhere.
        Every strong-5th-lord chart was previously shown the editorial line INSTEAD of it."""
        r = _R["H5.L.8"]
        assert r.fortified is None and r.afflicted is None
        assert "paternal property" in r.general and "lung troubles" in r.general


class TestUnconditionedReadingsMisfiledAsStrengthConditioned:
    def test_h5_l9_base_reading_reaches_weak_lord_charts(self) -> None:
        """No favourable opener exists — Raman states the teacher/preceptor results flatly and
        only then introduces "If the lord is afflicted". Identical in shape to H9.L.6 and
        H9.L.8, repaired on 2026-09-01. A weak-5th-lord chart previously saw ONLY "earns
        divine wrath"."""
        r = _R["H5.L.9"]
        assert r.fortified is None
        assert "teacher or preceptor" in r.general
        assert "divine wrath" in r.afflicted

    @pytest.mark.parametrize("rid", ["H5.L.11", "H5.L.12"])
    def test_ungated_entries_carry_a_general_reading(self, rid) -> None:
        """These entries contain no gate of any kind. `fortified` is KEPT alongside `general`
        per the H1.L.10/11/12 precedent — the defect was the LABEL, not the display."""
        r = _R[rid]
        assert r.general and r.fortified
        assert r.general == r.fortified


class TestTheFoldedCombination:
    def test_h5_l10_no_longer_promises_the_intelligence_service_to_every_strong_lord(self) -> None:
        """"If aspected by the Sun" (5162-5163) is a separate antecedent with its own outcome,
        folded into the fortification arm — so a strong 5th lord with no solar aspect anywhere
        was told it may join the intelligence department."""
        assert "intelligence" not in _R["H5.L.10"].fortified
        assert "Raja Yoga" in _R["H5.L.10"].fortified
        assert "intelligence department" in _R["H5.L.10a"].general

    def test_h5_l10a_tests_the_aspect_raman_names(self) -> None:
        conds = _R["H5.L.10a"].condition.conds
        assert any(isinstance(c, C.Aspects) and c.a == "Sun" and c.b == "LORD_OF:5"
                   for c in conds)

    def test_h5_l10a_is_satisfiable_though_no_golden_fires_it(self) -> None:
        """It fires on ZERO of the 346 goldens, so the ratchet cannot validate it — playbook
        rule 4's coverage-gap blindness. Witness: Taurus ascendant, 5th lord Mercury in the
        10th, with the Sun placed to cast a drishti on it.

        This rule is ALSO the reason `Aspects` was fixed: it resolved "LORD_OF:5" against
        `chart.planets` and returned False for every chart ever cast, so without that repair
        this test would fail and the rule would be dead on arrival.
        """
        found = None
        for asc in range(0, 360, 3):
            a = int(asc // 30) + 1
            l5 = SIGN_LORDS[((a - 1) + 4) % 12 + 1]
            if l5 == "Sun":
                continue
            lon = ((a - 1 + 9) % 12) * 30 + 10.0
            for shift in range(12):
                ch = RamanChart.from_stated_positions(
                    {l5: {"lon": lon, "bhava": 10},
                     "Sun": {"lon": ((a - 1 + shift) % 12) * 30 + 10.0, "bhava": 1}},
                    asc_lon=float(asc), ayanamsa="raman")
                if _R["H5.L.10a"].condition.evaluate(C.EvalContext(ch)):
                    found = (asc, l5, shift)
                    break
            if found:
                break
        assert found, "H5.L.10a is unsatisfiable — it would be a dead rule"


class TestTheTableWideAxisQuestionIsRecordedNotDecided:
    """HTJAH-I:5173-5175 closes this table by naming its axis — "the benefic, malefic, or
    MODERATING nature of the lord qualified or modified by the ASSOCIATION or ASPECT of the
    other planets and lords". Three tiers, on a nature-plus-association axis, not Shadbala.

    That is a corpus-wide interpretive question touching all 132 lord-in-house rules, and the
    project has a standing contrary convention adopted deliberately. It needs user sign-off,
    not a reviewer's verdict on twelve records — and counting it here would have reported
    "0 of 12", a number that says nothing about House 5. It is recorded in the backlog and
    deliberately NOT acted on.
    """

    def test_the_conditions_were_not_narrowed(self) -> None:
        """HTJAH-I:5173's "quite general" is one of the section-closing disclaimers the
        2026-09-01 condition-fidelity audit relied on. All twelve stay bare `LordIn(5, k)`."""
        for n in range(1, 13):
            r = _R[f"H5.L.{n}"]
            assert isinstance(r.condition, C.LordIn), f"H5.L.{n} must not be narrowed"
