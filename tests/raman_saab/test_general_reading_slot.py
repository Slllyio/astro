"""Raman's UNCONDITIONED reading has its own slot, and never poses as an affliction.

In HTJAH-I:995-1082 ("Results of Lord of First House Occupying Different Houses") Raman
writes each placement in two paragraphs: a GENERAL statement, then one conditioned on
FORTIFICATION. An engine-blind doctrine review counted NINE fortification openers in that
section and ZERO affliction openers — he gives no afflicted reading for these placements at
all — and he states the design himself at HTJAH-I:1003-1007: "the combination is of general
application... The same rules apply to all Bhava."

With only `fortified` and `afflicted` to write into, the corpus filed that general paragraph
under `afflicted`. Since `rule_firing._branch` picks the slot by the house-lord's Shadbala,
a weak-lord chart was shown Raman's BASE reading under an "afflicted" heading — on H1.L.3
and H1.L.9 that means a blessing ("highly courageous, fortunate... intelligent, happy")
presented as an affliction.

The same review ruled H5/H7/H9 CORRECTLY encoded (Raman really does give afflicted readings
there), so these tests also pin that House 1's repair was not swept across them.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import (build_detailed_report, house_general_readings,
                                            to_markdown)
from app.raman_saab.doctrine.rule_sets import ALL_RULES
from app.raman_saab.report_html import to_html

#: Lagna lord in the 4th, so H1.L.4 fires and its general reading is distinct from the
#: fortified text. The canonical baseline cannot exercise this: its lord falls in the 11th,
#: one of the three placements where Raman gives no conditioned paragraph at all.
LORD_IN_4TH = BirthData("general-slot probe", 1990, 7, 15, 0, 0, 5.5, 12.97, 77.59)


def _rule(rule_id: str):
    return next(r for r in ALL_RULES if r.id == rule_id)


class TestHouseOneSlotMapping:
    def test_no_house_one_lord_rule_hides_a_blessing_under_afflicted(self) -> None:
        """The two rules that made the defect visible. Their text is Raman's general
        reading and must no longer sit in the afflicted slot."""
        for rid, opening in (("H1.L.3", "highly courageous"),
                             ("H1.L.9", "generally fortunate")):
            rule = _rule(rid)
            assert rule.general and rule.general.startswith(opening), rid
            assert rule.afflicted is None, rid

    def test_every_house_one_lord_rule_records_its_general_reading(self) -> None:
        for n in range(1, 13):
            rule = _rule(f"H1.L.{n}")
            assert rule.general, f"H1.L.{n} lost Raman's general reading"

    def test_the_one_genuine_afflicted_clause_is_preserved(self) -> None:
        """H1.L.1's old slot text ENDED with a real afflicted reading Raman gives at
        HTJAH-I:1088-1089 ("If the ascendant lord is posited in the Lagna subject to evil
        combinations, the native will not be physically happy"). A wholesale relocation
        would have destroyed it; the review caught that, and this pins it."""
        rule = _rule("H1.L.1")
        assert rule.afflicted is not None
        assert "evil combinations" in rule.afflicted
        assert "not physically happy" in rule.afflicted
        assert "lives by own exertion" in (rule.general or "")
        assert "lives by own exertion" not in rule.afflicted


class TestCorrectlyEncodedHousesWereNotTouched:
    """The review ruled Houses 5, 7 and 9 CORRECT — Raman does give afflicted readings
    there in his own words. A blanket sweep of the House-1 fix would have destroyed real
    doctrine, so the absence of a `general` slot on those rules is the assertion."""

    @pytest.mark.parametrize("rule_id", ["H5.L.1", "H5.L.2", "H5.L.3",
                                         "H9.L.2", "H9.L.3", "H9.L.4"])
    def test_afflicted_reading_still_present(self, rule_id: str) -> None:
        rule = _rule(rule_id)
        assert rule.afflicted, f"{rule_id} lost its genuine afflicted reading"
        assert rule.general is None, f"{rule_id} was swept up by the House-1 fix"


#: Whole `afflicted` slot was Raman's general reading (review list A).
RELOCATED_WHOLE = ["H8.L.2", "H8.L.11", "H11.L.1", "H11.L.12",
                   "H12.L.4", "H12.L.5", "H12.L.7", "H12.L.9", "H12.L.10", "H12.L.11"]
#: Slot MIXED a general reading with a genuine afflicted clause; split, not moved (list B).
SPLIT = ["H8.L.1", "H8.L.3", "H8.L.4", "H8.L.5", "H8.L.6", "H8.L.7", "H8.L.10",
         "H10.L.12", "H11.L.7", "H11.L.8", "H12.L.2", "H12.L.3"]
#: Raman really does give an afflicted reading here (list C). Untouched, by construction.
LEFT_ALONE = ["H6.L.1", "H6.L.2", "H6.L.3", "H6.L.7", "H6.L.12",
              "H8.L.8", "H8.L.9", "H8.L.12",
              "H10.L.2", "H10.L.3", "H10.L.4", "H10.L.7", "H10.L.11",
              "H11.L.2", "H11.L.3", "H11.L.5", "H11.L.6", "H11.L.10",
              "H12.L.6", "H12.L.12"]


class TestHouses8To12SlotMapping:
    """A second engine-blind review classified Houses 6, 8, 10, 11 and 12, which the first
    did not reach. House 6 came back EXPLICIT-AFFLICTED (ten fortification openers, twelve
    affliction openers — correctly encoded throughout); Houses 8, 11 and 12 came back MIXED.
    The lists below are that classification, and these tests pin that it was applied
    exactly — the whole point being that a blanket sweep would have destroyed real
    doctrine."""

    @pytest.mark.parametrize("rule_id", RELOCATED_WHOLE)
    def test_whole_slot_relocated(self, rule_id: str) -> None:
        rule = _rule(rule_id)
        assert rule.general, rule_id
        assert rule.afflicted is None, rule_id
        assert rule.fortified, f"{rule_id} must keep prose to render when it fires"

    @pytest.mark.parametrize("rule_id", SPLIT)
    def test_split_kept_both_halves(self, rule_id: str) -> None:
        """The general half moved; the clause Raman really does condition on affliction
        stayed. Losing either half would be a fidelity regression."""
        rule = _rule(rule_id)
        assert rule.general, f"{rule_id} lost Raman's general reading"
        assert rule.afflicted, f"{rule_id} lost its genuine afflicted clause"
        assert rule.general != rule.afflicted, rule_id

    @pytest.mark.parametrize("rule_id", LEFT_ALONE)
    def test_correctly_encoded_rules_were_not_swept_up(self, rule_id: str) -> None:
        rule = _rule(rule_id)
        assert rule.afflicted, f"{rule_id} lost its genuine afflicted reading"
        assert rule.general is None, f"{rule_id} was wrongly relocated"

    def test_the_one_unsourced_slot_was_removed_not_relocated(self) -> None:
        """H10.L.1 was held back from the relocation sweep and sent for its own provenance
        audit, which read HTJAH-II:9456-9465 in full and searched BOTH volumes: "modest" and
        "little distinction" appear nowhere, and the cited paragraph is four unconditioned
        favourable sentences with no conditional clause at all. Verdict: encoder-supplied.

        So the slot is cleared, NOT moved to `general` — relocating it would have laundered
        unsourced prose into a slot that asserts Raman said it. The rule itself survives
        because its `fortified` text is sourced verbatim; deleting the rule would discard
        genuine doctrine to punish an invented sentence, and both deletion and demotion to
        `descriptive` would stop it firing and move the ratchet."""
        rule = _rule("H10.L.1")
        assert rule.afflicted is None
        assert rule.fortified, "the sourced half of the record is kept"
        assert rule.condition is not None, "the rule still fires on the same charts"
        # The unsourced words must not reappear in ANY slot. (This assertion replaced an
        # earlier `general is None` on 2026-09-01: the record has since been given a
        # `general` slot holding Raman's real base reading, which is a separate and correct
        # change. What matters is not that the slot is empty but that the invented text is
        # gone from all of them.)
        for slot in ("general", "fortified", "afflicted"):
            text = getattr(rule, slot) or ""
            assert "modest attainment" not in text, slot
            assert "little distinction" not in text, slot


#: Houses 2, 3 and H9.L.12, from the third review's fragment-level map.
H2_RELOCATED = ["H2.L.1", "H2.L.3", "H2.L.5", "H2.L.7", "H2.L.8", "H2.L.9", "H2.L.11"]
H2_SPLIT = ["H2.L.2", "H2.L.4", "H2.L.6", "H2.L.10", "H2.L.12"]
H3_RELOCATED = ["H3.L.1", "H3.L.2", "H3.L.5", "H3.L.7", "H3.L.8", "H3.L.10",
                "H3.L.11", "H3.L.12"]
H3_SPLIT = ["H3.L.4", "H3.L.6", "H3.L.9"]


class TestHouses2And3AndH9L12:
    """The last houses in the slot-mapping arc. House 2 closes with Raman's own "These
    combinations are AGAIN of general application" (HTJAH-I:2423), whose "again"
    back-references the design statement at 1003-1007 and settles the whole table."""

    @pytest.mark.parametrize("rule_id", H2_RELOCATED + H3_RELOCATED)
    def test_general_reading_relocated(self, rule_id: str) -> None:
        rule = _rule(rule_id)
        assert rule.general, rule_id
        assert rule.afflicted is None, rule_id
        assert rule.fortified, f"{rule_id} must keep prose to render when it fires"

    @pytest.mark.parametrize("rule_id", H2_SPLIT + H3_SPLIT)
    def test_split_kept_ramans_real_afflicted_clause(self, rule_id: str) -> None:
        rule = _rule(rule_id)
        assert rule.general, f"{rule_id} lost Raman's general reading"
        assert rule.afflicted, f"{rule_id} lost its genuine afflicted clause"

    def test_h3_l3_is_flagged_not_relocated(self) -> None:
        """Its three sibling-death clauses (HTJAH-I:3352-3354) are conditioned on PLANET
        IDENTITY — which planet happens to be the 3rd lord — with no affliction test in
        them at all. They are misfiled, but they are NOT a general reading, so relocating
        them would be a second error on top of the first. The slot is annotated instead;
        the real repair is a configuration predicate, which is a CONDITION change and would
        move the ratchet."""
        rule = _rule("H3.L.3")
        assert rule.general is None
        assert rule.afflicted and "planet identity" in rule.afflicted

    def test_h9_flat_base_readings_are_repaired(self) -> None:
        """CORRECTED 2026-09-01. This test originally asserted H9.L.12 was the LONE entry in
        House 9 needing repair, and pinned `general is None` on all eleven others. That was
        false, and the assertion made the error durable: the condition-fidelity audit read
        all twelve entries in full and found H9.L.6 (HTJAH-II:7340, "The ninth lord in the
        sixth house gives a sickly father afflicted with chronic diseases") and H9.L.8 (7359,
        "The native may lose his father early in life") are ALSO flat unconditioned bases
        with no benefic/malefic opener, both filed under `afflicted`.

        The original claim came from sampling the entries that DO have explicit openers
        rather than reading every one — the same first-entry sampling error the audit was
        designed to catch. Three entries need the repair, not one."""
        for rid in ("H9.L.6", "H9.L.8", "H9.L.12"):
            assert _rule(rid).general, rid
        assert _rule("H9.L.12").afflicted is None
        # L.6 and L.8 keep a genuine conditioned clause; only their flat base moved.
        for rid in ("H9.L.6", "H9.L.8"):
            assert _rule(rid).afflicted, f"{rid} lost its genuine conditioned clause"
        # The nine entries with explicit openers stay untouched.
        for n in (1, 2, 3, 4, 5, 7, 9, 10, 11):
            assert _rule(f"H9.L.{n}").general is None, f"H9.L.{n} was wrongly swept up"


class TestPlanetInHouseSweep:
    """The `planet_in_house` group, swept 2026-09-01 after four parallel engine-blind reviews.

    These tables are structured differently from the lord tables, and the project's own
    methodology docs say so: their modifier column is headed "Aspect / association modifiers",
    not fortified/afflicted. Raman states the axis himself at HTJAH-I:1480-1481 — a planet's
    effects "by house position, as given below, are subjected to modification" by aspect and
    conjunction. Encoders collapsed that two-column (effect | configuration) table into the
    two-slot (fortified | afflicted) record BY SENTIMENT, repeatedly cutting single sentences
    at their own "but".
    """

    def test_every_at_risk_rule_was_classified(self) -> None:
        """79 rules carried both slots. All but one now record a general reading; the
        exception is H8.P.Ketu, which the review ruled correctly encoded — both of Raman's
        openers there are explicit ("If Ketu in the 8th is aspected by a benefic" / "If Ketu
        is afflicted") and both slots track them exactly."""
        unswept = [r.id for r in ALL_RULES
                   if r.group == "planet_in_house" and r.fortified and r.afflicted
                   and not r.general]
        assert unswept == ["H8.P.Ketu"], unswept

    def test_h8_ketu_kept_its_genuine_branches(self) -> None:
        rule = _rule("H8.P.Ketu")
        assert rule.general is None
        assert rule.fortified and rule.afflicted

    @pytest.mark.parametrize("rule_id,fragment", [
        # Raman's own "but"/"nevertheless"/"however" hinges, which had been used as the
        # slot boundary. Each must now sit intact inside one reading.
        ("H6.P.Ketu", "nevertheless his moral character will be loose"),
        ("H3.P.Ketu", "strong and adventurous but funky"),
        ("H12.P.Rahu", "prosperous, immoral, but of a helpful nature"),
        ("H8.P.Jupiter", "unhappy but generous-hearted"),
        ("H11.P.Mars", "clever and rich but lustful"),
        ("H9.P.Rahu", "but he may become famous and acquire much wealth"),
        ("H2.P.Mars", "good earning powers but usually miserly"),
    ])
    def test_torn_sentences_are_whole_again(self, rule_id: str, fragment: str) -> None:
        assert fragment in (_rule(rule_id).general or ""), rule_id

    @pytest.mark.parametrize("rule_id,gone", [
        # The three unsourced / cross-frame claims removed by the sweep.
        ("H3.P.Sun", "spiritually strong"),
        ("H6.P.Sun", "Govt trouble"),
        ("H7.P.Mars", "partnership"),
        ("H12.P.Ketu", "karakamsa"),
    ])
    def test_unsourced_claims_are_gone_from_every_slot(self, rule_id: str, gone: str) -> None:
        """Removed, never relocated — moving unsourced prose into `general` would launder it
        into a slot that asserts Raman said it."""
        rule = _rule(rule_id)
        for slot in ("general", "fortified", "afflicted"):
            assert gone not in (getattr(rule, slot) or ""), f"{rule_id}.{slot}"

    def test_positive_results_are_no_longer_filed_as_afflictions(self) -> None:
        """Two conjunction results Raman states favourably had been rendered under an
        "afflicted" heading, telling the reader the opposite of his sentence."""
        assert "ELEVATED" in (_rule("H1.P.Moon").afflicted or "")
        moon9 = _rule("H9.P.Moon").afflicted or ""
        assert "RULER" in moon9
        assert "(mixed)" not in moon9, "the interpolated hedge is not Raman's"

    def test_invented_positive_complements_are_cleared(self) -> None:
        """H7.K.1/2/3 encode the affliction IN THE CONDITION, so they only ever fire in the
        malefic case — yet each asserted a positive `fortified` result that `_branch` would
        surface on a strong karaka, stating the inverse of Raman."""
        for rid in ("H7.K.1", "H7.K.2", "H7.K.3"):
            rule = _rule(rid)
            assert rule.fortified is None, rid
            assert rule.afflicted, f"{rid} must keep Raman's actual reading"


class TestGeneralReadingReachesTheReader:
    @pytest.fixture(scope="class")
    def report(self):
        return build_detailed_report(LORD_IN_4TH)

    def test_composed_for_a_chart_that_exercises_it(self, report) -> None:
        rows = house_general_readings(report, 1)
        assert rows, "H1.L.4 should fire on this chart and carry a general reading"
        assert any(rid == "H1.L.4" for _s, rid, _t, _c in rows)

    def test_surfaces_in_markdown_and_html(self, report) -> None:
        rows = house_general_readings(report, 1)
        md, html = to_markdown(report), to_html(report)
        assert "general reading" in md
        assert "general reading" in html
        for _sig, _rid, text, _cite in rows:
            assert text in md

    def test_not_duplicated_when_it_equals_the_fired_text(self) -> None:
        """Where Raman gave no conditioned paragraph (H1.L.10/11/12), `fortified` carries
        the same sentence; printing it twice would be noise, not completeness. The
        canonical baseline is exactly that case."""
        canon = build_detailed_report(
            BirthData("canon", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59))
        assert canon.chart.planets[canon.proformas[0].lord].rasi_house == 11
        assert house_general_readings(canon, 1) == ()


class TestGeneralSlotIsVerdictInert:
    def test_polarity_and_conditions_untouched(self) -> None:
        """The repair moved TEXT between slots. `_bucket_fired` buckets by `polarity` and
        firing is by `condition`; neither was edited, which is why the golden ratchet did
        not move."""
        for n in range(1, 13):
            rule = _rule(f"H1.L.{n}")
            assert rule.condition is not None
            assert rule.polarity in ("benefic", "malefic", "neutral", "maraka")
            assert rule.kind == "evaluable"
