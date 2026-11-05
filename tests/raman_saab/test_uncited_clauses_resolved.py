"""The three clauses that used to ship with no citation — settled 2026-08-19.

Each was logged in the backlog as "needs a verified citation before it can be encoded".
With the corpus mounted all three are now settled, and two of the three answers are
NEGATIVE — the passage does not exist. Those answers are worth locking down harder than
the positive one, because a negative result is exactly what a future session will be
tempted to go re-hunt for.
"""
from __future__ import annotations

import inspect

import pytest

from app.raman_saab.chart.model import BirthData

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)

try:
    from app.raman_saab.doctrine.sources import Citation, verify
    _HAS_CORPUS = verify(Citation("HPA-13", 130))
except Exception:  # noqa: BLE001
    _HAS_CORPUS = False


@pytest.fixture(scope="module")
def report():
    from app.raman_saab.detailed_report import build_detailed_report
    return build_detailed_report(_CANONICAL)


class TestBalanceOfDashaIsCited:
    def test_the_row_label_carries_the_anchor(self, report):
        """The row shipped as disclosed JD arithmetic with no citation because Raman's
        casting passage was unpinned. It is HPA-13:130-160 — he deducts the expired portion
        of the birth nakshatra from the lord's full dasa by proportion and prints the result
        as "Balance of the dasa of Mars at birth"."""
        from app.raman_saab.report_json import to_report_dict
        fg = dict(to_report_dict(report)["signature_first_glance"])
        key = next(k for k in fg if k.startswith("Balance of dasha at birth"))
        assert "HPA-13:130-160" in key

    def test_the_citation_rides_the_label_not_the_value(self, report):
        """A citation spliced into the VALUE would leak into every consumer that parses
        it — and two tests were reading that value directly. The label carries it."""
        from app.raman_saab.report_json import to_report_dict
        fg = dict(to_report_dict(report)["signature_first_glance"])
        key = next(k for k in fg if k.startswith("Balance of dasha at birth"))
        assert "HPA" not in fg[key]

    @pytest.mark.skipif(not _HAS_CORPUS, reason="doctrine corpus not mounted")
    def test_the_anchor_really_states_the_proportional_deduction(self):
        """The whole citation rests on this passage, so it is read back rather than
        trusted: the expired portion is deducted by proportion, and the remainder is
        printed as the balance at birth."""
        import re
        from app.raman_saab.doctrine.sources import _resolve_file
        lines = _resolve_file("HPA-13").read_text(
            encoding="utf-8", errors="replace").splitlines()
        window = re.sub(r"\s+", " ", " ".join(lines[125:161])).casefold()
        assert "must be deducted out of the dasa" in window
        assert "balance of the dasa" in window


class TestDeeptadiPrecedenceIsSettledAsAbsent:
    def test_the_primitive_records_that_raman_states_no_precedence(self):
        """HPA-7:39-44 is the opposite of a precedence rule: the avasthas are "ten in
        number. Each Avastha produces its own results. In the judgment of a horoscope all
        these details have to be fully considered." The dignity-first ordering exists only
        because the function must return one string, and the docstring has to say so —
        otherwise a reader takes it for Raman's ranking."""
        from app.raman_saab.primitives import deeptadi
        doc = inspect.getdoc(deeptadi.state) or ""
        assert "HPA-7:39-44" in doc
        assert "NO precedence" in doc or "states NO precedence" in doc
        assert "ENGINE'S OWN CONVENTION" in doc

    def test_the_rendered_disclosure_does_not_present_the_order_as_ramans(self, report):
        """The markdown said the "dignity-first priority order names the dominant one",
        which reads as doctrine. It now names the order as the engine's own and quotes
        Raman asking for every state to be considered."""
        from app.raman_saab.detailed_report import to_markdown
        md = to_markdown(report)
        i = md.find("## Deeptadi avasthas")
        assert i > 0
        block = md[i:i + 4000]
        assert "HPA-7:39-44" in block
        assert "this engine's own convention" in block
        assert "all these details have to be fully considered" in block

    @pytest.mark.skipif(not _HAS_CORPUS, reason="doctrine corpus not mounted")
    def test_the_anchor_really_says_consider_them_all(self):
        """A negative finding is only as good as the passage it rests on."""
        import re
        from app.raman_saab.doctrine.sources import _resolve_file
        lines = _resolve_file("HPA-7").read_text(
            encoding="utf-8", errors="replace").splitlines()
        window = re.sub(r"\s+", " ", " ".join(lines[38:45])).casefold()
        assert "ten in number" in window
        assert "all these details have to be fully considered" in window


class TestModeratingFactorIsSettledAsTheJudgesOwn:
    def test_the_clause_declares_it_is_not_a_rule_of_ramans(self, report):
        """No general "the affliction is considerably reduced by..." device exists in the
        corpus — searching returns only specific rules (HTJAH-I:9658-9659, :12825, :12866).
        The clause is the judge disclosing what it already credited, and now says so on its
        face so nobody reads it as doctrine."""
        from app.raman_saab.detailed_report import house_moderating_clause
        found = [house_moderating_clause(report, h) for h in range(1, 13)]
        emitted = [t for t in found if t]
        if not emitted:
            pytest.skip("no moderating factor fires on the canonical chart")
        for t in emitted:
            assert "the judge's own disclosure" in t
            assert "not a separate rule of Raman's" in t

    def test_the_parivartana_arm_carries_ramans_counter_examples(self, report):
        """Raman's exchanges run both ways — mutually benefiting at HTJAH-I:8837, but
        transmitting affliction at HTJAH-I:9119 and undesirable at HTJAH-I:9143. The arm
        used to read as though an exchange were relief as such."""
        from app.raman_saab.detailed_report import house_moderating_clause
        texts = [t for t in (house_moderating_clause(report, h) for h in range(1, 13))
                 if t and "parivartana" in t]
        if not texts:
            pytest.skip("no parivartana arm fires on the canonical chart")
        for t in texts:
            assert "HTJAH-I:8837" in t
            assert "HTJAH-I:9119" in t and "HTJAH-I:9143" in t
            assert "does not look at the partner's condition" in t

    def test_the_verdict_path_defect_is_logged_not_silently_changed(self):
        """The judge credits `parivartana_resilient` as flat relief regardless of the
        partner's condition, which is verdict-path behaviour and would move the ratchet.
        It is recorded for doctrine review rather than changed here — and the record has to
        exist, or the finding is lost."""
        import pathlib
        backlog = (pathlib.Path(__file__).resolve().parents[2]
                   / "docs" / "raman_saab" / "DOCTRINE_BACKLOG.md")
        text = backlog.read_text(encoding="utf-8")
        assert "Directional parivartana" in text
        assert "HTJAH-I:9119" in text and "HTJAH-I:9143" in text
        assert "needs doctrine review" in text.lower()
