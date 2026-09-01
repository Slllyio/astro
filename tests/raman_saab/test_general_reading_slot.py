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

    def test_undetermined_rules_were_left_untouched(self) -> None:
        """H10.L.1's `afflicted` text does not appear at HTJAH-II:9459-9465 or anywhere in
        the tenth-lord section — it is neither Raman's general reading nor a genuine
        afflicted one, and looks encoder-supplied. Relocating it would have LAUNDERED
        unsourced prose into the general slot, so it is deliberately untouched pending its
        own investigation (DOCTRINE_BACKLOG)."""
        rule = _rule("H10.L.1")
        assert rule.general is None
        assert rule.afflicted is not None


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
