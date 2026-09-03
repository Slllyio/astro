"""H8.L.1 and H8.L.5: the `afflicted` slot is a STRENGTH label, not an affliction label.

An engine-blind doctrine review returned REVERSAL on both rules. The defect was a name pun.
`rule_firing._branch` selects `afflicted` on WEAK Shadbala — `is_powerful` against the
GBB-8:303 minimum-required table — so the slot means "the branch subject is weak". Raman's
affliction-gated sentences ("If the 8th lord is severely afflicted", "If the affliction is
heavy") were filed there, and his actual weak-lord sentence sat in `fortified`. Both branches
therefore showed a reading whose own stated antecedent was false for the chart being read:

* a STRONG 8th lord was told "misfortune reduced **when the 8th lord is weak**"
* a WEAK 8th lord was told the severe-affliction outcome, chosen by a test that never looked
  at a single afflicter.

That weak and severely-afflicted are different conditions is settled inside the same table,
not inferred: at HTJAH-II:3001-3009 Raman runs three tiers over one entry — "in strength… If
the 8th lord is **weak**, he may have no serious troubles but may not also enjoy any luck… If
the 8th lord is **afflicted**, the native will fail in his undertakings" — three antecedents,
three non-nested outcomes. HTJAH-II:273-276 repeats the pattern on the 7th lord.

Nothing was deleted. Every displaced clause was re-homed: the Navamsa-placement mitigations
became real predicates (H8.L.1a, H8.L.5a — the first corpus rules to reach a varga through
the generic condition), the affliction-gated clauses became descriptive records awaiting an
8th-lord affliction predicate (H8.L.1b, H8.L.5b), and the separate paragraph at HTJAH-II:2972
became its own rule (H8.L.5c) instead of riding as a branch of H8.L.5.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets import ALL_RULES
from app.raman_saab.primitives import relationships as _rel

_R = {r.id: r for r in ALL_RULES}


def _lords(asc_sign: int):
    def L(h: int) -> str:
        return SIGN_LORDS[((asc_sign - 1) + h - 1) % 12 + 1]
    return L


class TestTheSlotsNowMatchTheAntecedents:
    def test_h8_l1_weak_branch_carries_ramans_weak_lord_sentence(self) -> None:
        """HTJAH-II:2904 — "If the 8th lord is weak … the intensity of misfortune is
        reduced". This is the ONLY sentence in the entry gated on the 8th lord's strength,
        so it is the only one the weak branch may show."""
        r = _R["H8.L.1"]
        assert "weak" in r.afflicted and "reduced" in r.afflicted
        assert "severely afflicted" not in (r.afflicted or "")

    def test_h8_l1_strong_branch_no_longer_asserts_a_falsehood(self) -> None:
        """Raman writes no strong-lord sentence here. The licensed reading is the
        unconditioned one at full force — the only mitigation offered is conditioned on
        weakness, so its absence leaves the misfortune undiminished."""
        r = _R["H8.L.1"]
        assert "undiminished" in r.fortified
        assert "when 8th lord is weak" not in r.fortified

    def test_h8_l5_has_no_weak_lord_reading_at_all(self) -> None:
        """Unlike H8.L.1, this entry offers no "weak or" disjunct — its mitigation is
        placement-only. So nothing legitimately occupies the weak branch, and the slot is
        empty rather than borrowing a sentence from another antecedent."""
        assert _R["H8.L.5"].afflicted is None

    def test_h8_l5_strong_branch_keeps_only_the_strength_half(self) -> None:
        """The old slot held a mitigation and an intensification in one sentence — two
        clauses pointing opposite ways, shown together to the same chart."""
        f = _R["H8.L.5"].fortified
        assert "intensified" in f
        assert "Navamsa" not in f and "mitigat" not in f

    def test_the_father_strand_dropped_by_the_old_general_slot_is_restored(self) -> None:
        """HTJAH-II:2960 — "Or the native and his father may develop misunderstandings" was
        absent from the old `general` text."""
        assert "father" in _R["H8.L.5"].general

    def test_no_slot_anywhere_in_the_pair_still_holds_the_wrong_antecedent(self) -> None:
        """The regression this whole file exists to prevent: an affliction-gated sentence
        sitting in a strength slot."""
        for rid in ("H8.L.1", "H8.L.5"):
            r = _R[rid]
            for slot in ("fortified", "afflicted"):
                text = getattr(r, slot) or ""
                assert "affliction is heavy" not in text, f"{rid}.{slot}"
                assert "severely afflicted" not in text, f"{rid}.{slot}"


class TestNothingWasDeleted:
    """Re-homing, not removal. Moving a clause out of a wrong slot without giving it a home
    trades a false display for a missing one — a real Raman conclusion would vanish."""

    @pytest.mark.parametrize("rid", ["H8.L.1a", "H8.L.1b", "H8.L.5a", "H8.L.5b", "H8.L.5c"])
    def test_the_rehomed_record_exists_and_is_cited(self, rid) -> None:
        r = _R[rid]
        assert r.source.work == "HTJAH-II" and r.source.line > 0
        assert any((getattr(r, s) or "").strip() for s in ("general", "fortified", "afflicted"))

    def test_the_severe_affliction_text_survives(self) -> None:
        assert "disease and disfiguration" in _R["H8.L.1b"].afflicted

    def test_the_heavy_affliction_text_survives(self) -> None:
        assert "may die as soon as it is born" in _R["H8.L.5b"].afflicted

    def test_the_ninth_lord_combination_is_its_own_rule_not_a_branch(self) -> None:
        """The worst display error in the file: any chart with merely a weak 8th lord — no
        9th lord involved, Lagna lord in fine dignity — was told it had "no knowledge or
        wealth, lustful, reviled". A missing rule masquerading as a branch."""
        r = _R["H8.L.5c"]
        assert r.kind == "evaluable" and r.condition is not None
        assert "neither knowledge nor wealth" in r.afflicted
        assert "9th and 8th lords" not in (_R["H8.L.5"].afflicted or "")

    def test_the_two_descriptive_records_say_what_predicate_they_await(self) -> None:
        for rid in ("H8.L.1b", "H8.L.5b"):
            assert _R[rid].kind == "descriptive"
            assert "TODO(predicate:" in _R[rid].afflicted


class TestSatisfiableByConstruction:
    """These rules fire on ZERO of the 346 goldens, because their parents are already rare
    (3 and 1 firings) and they are strictly narrower. A rule the corpus never exercises
    cannot be validated by the ratchet — playbook rule 4's coverage-gap blindness — so
    satisfiability is proved by construction instead of assumed.
    """

    def test_h8_l1a_can_fire(self) -> None:
        """Witness: Taurus ascendant, 8th lord Jupiter at 47° (rasi house 1, with the Lagna
        lord), navamsa Gemini — the 6th from a Capricorn navamsa Lagna."""
        found = None
        for asc in range(0, 360, 6):
            a = int(asc // 30) + 1
            L = _lords(a)
            l1, l8 = L(1), L(8)
            if l8 == l1:
                continue
            for step in range(60):
                lon = (a - 1) * 30 + step * 0.5
                ch = RamanChart.from_stated_positions(
                    {l8: {"lon": lon, "bhava": 1}, l1: {"lon": lon + 0.1, "bhava": 1}},
                    asc_lon=float(asc), ayanamsa="raman")
                if _R["H8.L.1a"].condition.evaluate(C.EvalContext(ch)):
                    found = (asc, l8, lon)
                    break
            if found:
                break
        assert found, "H8.L.1a is unsatisfiable — it would be a dead rule"

    def test_h8_l5a_can_fire(self) -> None:
        found = None
        for asc in range(0, 360, 6):
            a = int(asc // 30) + 1
            L = _lords(a)
            l5, l8 = L(5), L(8)
            if l8 == l5:
                continue
            for step in range(60):
                lon = ((a - 1 + 4) % 12) * 30 + step * 0.5
                ch = RamanChart.from_stated_positions(
                    {l8: {"lon": lon, "bhava": 5}, l5: {"lon": lon + 0.1, "bhava": 5}},
                    asc_lon=float(asc), ayanamsa="raman")
                if _R["H8.L.5a"].condition.evaluate(C.EvalContext(ch)):
                    found = (asc, l8, lon)
                    break
            if found:
                break
        assert found, "H8.L.5a is unsatisfiable — it would be a dead rule"

    def test_h8_l5c_can_fire(self) -> None:
        """Witness: Taurus ascendant — Lagna lord Venus debilitated in Virgo, 8th lord
        Jupiter and 9th lord Saturn conjunct in the 5th."""
        found = None
        for asc in range(0, 360, 6):
            a = int(asc // 30) + 1
            L = _lords(a)
            l1, l8, l9 = L(1), L(8), L(9)
            if len({l1, l8, l9}) < 3:
                continue
            deb = _rel.DEBILITATION[l1][0]
            lon = ((a - 1 + 4) % 12) * 30 + 10.0
            ch = RamanChart.from_stated_positions(
                {l8: {"lon": lon, "bhava": 5}, l9: {"lon": lon + 0.2, "bhava": 5},
                 l1: {"lon": (deb - 1) * 30 + 15.0, "bhava": 1}},
                asc_lon=float(asc), ayanamsa="raman")
            if _R["H8.L.5c"].condition.evaluate(C.EvalContext(ch)):
                found = (asc, l1, l8, l9)
                break
        assert found, "H8.L.5c is unsatisfiable — it would be a dead rule"

    def test_the_navamsa_rules_reach_a_varga_through_the_generic_condition(self) -> None:
        """The milestone's own proof: before the varga gate opened, a rule could only touch
        a division through a hand-rolled local Condition subclass (the two D3 drekkana rules
        in house_08_ayur/combinations.py). These two use the shared, reviewable predicate."""
        for rid in ("H8.L.1a", "H8.L.5a"):
            assert _R[rid].varga == "D9"
            assert any(isinstance(p, C.InVargaHouseFrom) for p in _R[rid].condition.conds)


class TestTheSweepAcrossTheRestOfTheSection:
    """The same defect ran through five more entries. A second engine-blind review found
    **zero of ten** populated strength slots in H8.L.2/6/9/10/12 gated on the 8th lord's
    strength — the branch subject. Three shapes, in rising severity:

    * a NAVAMSA PLACEMENT in a strength slot (H8.L.2) — untestable by any branch;
    * an UNCONDITIONED headline in `fortified` (H8.L.6's Rajayoga, H8.L.10's "may ALSO
      confer unexpected gains") — not a false claim but a wrong WITHHOLDING, since weak-lord
      charts never saw Raman's main reading;
    * a slot gated on ANOTHER PLANET entirely (H8.L.9's Sun and 9th lord, H8.L.10's 2nd lord).
    """

    @pytest.mark.parametrize("rid", ["H8.L.2", "H8.L.6", "H8.L.10", "H8.L.12"])
    def test_no_strength_slot_survives_where_raman_gates_on_something_else(self, rid) -> None:
        r = _R[rid]
        assert r.fortified is None, f"{rid}.fortified is not strength-gated in Raman"
        assert r.afflicted is None, f"{rid}.afflicted is not strength-gated in Raman"
        assert (r.general or "").strip(), f"{rid} must still say what Raman says unconditionally"

    def test_the_withheld_headlines_are_now_shown_to_every_chart(self) -> None:
        """H8.L.6's Rajayoga and H8.L.10's unexpected gains were in `fortified`, so a weak
        8th lord never saw them. Both are unconditioned in the text."""
        assert "Rajayoga" in _R["H8.L.6"].general
        assert "unexpected gains" in _R["H8.L.10"].general

    def test_h8_l10_recovers_the_half_antecedent_that_was_dropped(self) -> None:
        """The old slot read "the 2nd lord also afflicted"; Raman requires the 2nd lord to be
        afflicted AND to join the 8th lord (HTJAH-II:3034). The encoded sentence was a
        strictly weaker claim than his."""
        assert "JOINING" in _R["H8.L.10a"].afflicted

    def test_h8_l9_is_gone_and_its_content_is_not(self) -> None:
        """Not one sentence in that entry was gated on the 8th lord's strength, and Raman
        states no unconditioned reading for it — so the base record had nothing legitimate
        to say. Removing it is only honest if every clause found a home."""
        assert "H8.L.9" not in _R
        for heir in ("H8.L.9a", "H8.L.9b", "H8.L.9c", "H8.L.9d", "H8.L.9e"):
            assert heir in _R, heir

    def test_the_material_raman_states_but_the_corpus_never_carried(self) -> None:
        """Four clauses were MISSING entirely, not merely mis-slotted — three D9 mitigations
        and the 6th-lord relief. Reading the source found them; a slot audit alone would not
        have."""
        assert "overcomes all his troubles" in _R["H8.L.6b"].fortified
        for rid in ("H8.L.9e", "H8.L.10b"):
            assert "Navamsa Lagna" in _R[rid].general

    def test_the_kendra_trikona_tag_stays_prose_and_never_becomes_a_predicate(self) -> None:
        """Settled by a review that surveyed ~160 kendra/trikona occurrences across both
        volumes: every one that names a frame names a RASI origin, and the ~120 navamsa
        references are always marked and always use bare ordinals. Under D1 the tag is
        unsatisfiable here (the entry stipulates the 8th lord in the 6th); under D9 it would
        be the only unmarked-navamsa reference in the corpus. It is Raman's idiom for
        "strong" — HTJAH-II:7923, "in a kendra ... or is otherwise fortified"."""
        r = _R["H8.L.6a"]
        assert r.condition is None and r.kind == "descriptive"
        assert "idiom for" in r.afflicted

    def test_h8_l12b_drops_the_conjunction_because_raman_reopens_the_antecedent(self) -> None:
        """HTJAH-II:3061 restarts with "If the 8th lord is in the 12th house", dropping "with
        the 12th lord". That matters: under the conjunction the 12th lord is in the 12th by
        construction, and the 12th is neither trine nor quadrant, so the clause was
        UNSATISFIABLE as previously encoded — a display promise that could never be met."""
        conds = _R["H8.L.12b"].condition.conds
        assert not any(isinstance(c, C.LordsConjunct) for c in conds)
        assert any(isinstance(c, C.LordIn) for c in conds)


class TestInHouseClassResolvesADynamicSubject:
    """`InHouseClass` read `chart.planets` directly, so a "LORD_OF:n" subject resolved to
    None and the condition was SILENTLY ALWAYS FALSE. H8.L.12b would have been a dead rule
    that looks alive. Every sibling condition already used `_resolve_planet`."""

    def test_a_lord_of_subject_now_resolves(self) -> None:
        """Taurus ascendant (asc_sign 2): the 12th house is Aries, so the 12th lord is Mars.
        Put Mars in Leo — the 4th from Taurus, a kendra. Before the fix this returned False
        for every chart ever cast, because `planets.get("LORD_OF:12")` is None.
        """
        asc_lon = 35.0                                   # Taurus
        assert SIGN_LORDS[1] == "Mars", "the 12th from Taurus is Aries"
        chart = RamanChart.from_stated_positions(
            {"Mars": {"lon": 130.0, "bhava": 4}}, asc_lon=asc_lon, ayanamsa="raman")
        assert chart.planets["Mars"].rasi_house == 4      # a kendra
        ctx = C.EvalContext(chart)
        assert C.InHouseClass("LORD_OF:12", "kendra").evaluate(ctx) is True
        assert C.InHouseClass("LORD_OF:12", "trikona").evaluate(ctx) is False

    def test_an_unresolvable_subject_is_false_not_an_error(self) -> None:
        chart = RamanChart.from_stated_positions(
            {"Sun": {"lon": 10.0, "bhava": 1}}, asc_lon=0.0, ayanamsa="raman")
        assert C.InHouseClass("LORD_OF:7", "kendra").evaluate(C.EvalContext(chart)) is False

    def test_static_names_are_unchanged_by_the_fix(self) -> None:
        """The fix must be a strict generalisation — no shipped rule may change behaviour."""
        chart = RamanChart.from_stated_positions(
            {"Mars": {"lon": 200.0, "bhava": 7}}, asc_lon=0.0, ayanamsa="raman")
        assert C.InHouseClass("Mars", "kendra").evaluate(C.EvalContext(chart)) is True
        assert C.InHouseClass("Mars", "trikona").evaluate(C.EvalContext(chart)) is False
