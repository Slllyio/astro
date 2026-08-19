"""The mind screen, the Kemadruma attribution, and the Jaimini gap — settled 2026-08-19.

Three backlog items resolved against the mounted corpus. One produced code (the mind
screen); two produced corrections to what the engine CLAIMS rather than what it does, plus
backlog entries for the verdict-path questions they exposed.
"""
from __future__ import annotations

import inspect
import pathlib

import pytest

from app.raman_saab.chart.model import BirthData

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
_BACKLOG = (pathlib.Path(__file__).resolve().parents[2]
            / "docs" / "raman_saab" / "DOCTRINE_BACKLOG.md")

try:
    from app.raman_saab.doctrine.sources import Citation, verify
    _HAS_CORPUS = verify(Citation("HTJAH-I", 10077))
except Exception:  # noqa: BLE001
    _HAS_CORPUS = False


@pytest.fixture(scope="module")
def report():
    from app.raman_saab.detailed_report import build_detailed_report
    return build_detailed_report(_CANONICAL)


class TestMindScreen:
    def test_the_screen_reports_present_or_absent_never_silence(self, report):
        """A screen that only speaks when it fires leaves a reader unable to tell "checked
        and clear" from "not checked". This one always reports."""
        ps = report.psych
        assert ps.mind_screen
        for _name, finding, cite in ps.mind_screen:
            assert finding.startswith(("present:", "absent:"))
            assert cite.startswith("HTJAH-I:")

    def test_the_screen_never_speaks_in_the_decree_voice(self, report):
        """Raman's own wording is "the native WILL SUFFER FROM mental disorders". That is
        his voice for a combination; the engine does not repeat it as a claim about the
        person reading the report. Every string is checked against the decree guard."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        ps = report.psych
        for name, finding, _cite in ps.mind_screen:
            for text in (name, finding):
                m = _FORBIDDEN_RE.search(text)
                assert m is None, f"decree voice {m.group(0)!r} in: {text[:80]}"
        assert _FORBIDDEN_RE.search(ps.mind_caution) is None

    def test_it_refuses_the_diagnostic_register(self, report):
        """Mental-health content carries the same wall the medical read does."""
        ps = report.psych
        assert "nothing here is a diagnosis" in ps.mind_caution
        assert "classical combinations" in ps.mind_caution

    def test_ramans_own_caution_travels_with_it(self, report):
        """He hedges this material himself and the hedge is not droppable."""
        ps = report.psych
        assert "No slip-shod interpretation should be made" in ps.mind_caution
        assert "HTJAH-I:4297-4299" in ps.mind_caution

    @pytest.mark.skipif(not _HAS_CORPUS, reason="doctrine corpus not mounted")
    def test_both_anchors_say_what_the_screen_claims(self):
        """The combination and the caution are both quotations, so both are read back."""
        import re
        from app.raman_saab.doctrine.sources import _resolve_file
        lines = _resolve_file("HTJAH-I").read_text(
            encoding="utf-8", errors="replace").splitlines()
        combo = re.sub(r"\s+", " ", " ".join(lines[10076:10079])).casefold()
        assert "moon conjoins with a" in combo and "malefic" in combo
        assert "rahu is in the 8th" in combo
        assert "mental disorders" in combo
        caution = re.sub(r"\s+", " ", " ".join(lines[4296:4300])).casefold()
        assert "no slip-shod interpretation should be made" in caution


class TestKemadrumaAttributionCorrected:
    def test_the_docstring_quotes_the_dismissal_it_used_to_stop_before(self):
        """The engine cited 3HC:2182-2185 as though Raman asserted the cancellation. He
        attributes it to "some authors", and the same Remark ends "but these observations
        are not generally acceptable" (3HC:2188). The anchor is now quoted in full."""
        from app.raman_saab.primitives import bhangas
        doc = inspect.getdoc(bhangas.kemadruma_bhanga) or ""
        assert "NOT GENERALLY" in doc.upper()
        assert "3HC:2188" in doc
        assert "ATTRIBUTES" in doc.upper()

    def test_the_benefic_drishti_branch_stays_labelled_not_ramans(self):
        """The backlog asked: if Raman states the extended branch elsewhere, pin it and
        relabel. He does not — Kemadruma appears in the mounted 3HC only at :2170-2266."""
        from app.raman_saab.primitives import bhangas
        doc = inspect.getdoc(bhangas.kemadruma_bhanga) or ""
        assert "NOT attributable to 3HC" in doc
        assert "He does not state it" in doc

    def test_the_verdict_path_question_is_logged_not_silently_changed(self):
        """Narrowing the branches would move the ratchet, so it is a review question."""
        text = _BACKLOG.read_text(encoding="utf-8")
        assert "Kemadruma bhanga attribution" in text
        assert "3HC:2188" in text
        assert "needs doctrine review" in text.lower()

    @pytest.mark.skipif(not _HAS_CORPUS, reason="doctrine corpus not mounted")
    def test_the_dismissal_really_is_on_the_page(self):
        import re
        from app.raman_saab.doctrine.sources import _resolve_file
        lines = _resolve_file("3HC").read_text(
            encoding="utf-8", errors="replace").splitlines()
        window = re.sub(r"\s+", " ", " ".join(lines[2181:2189])).casefold()
        assert "some authors say" in window
        assert "not generally" in window and "acceptable" in window


class TestJaiminiPairingRecordedAsUnavailable:
    def test_the_gap_is_recorded_as_an_import_gap_not_a_doctrine_gap(self):
        """The chara x karakamsa pairing cannot be composed from the mounted subset. The
        record has to say WHY — a partial import, not an absent doctrine — or the next
        session repeats the hunt and reaches the same dead end."""
        text = _BACKLOG.read_text(encoding="utf-8")
        assert "Chara dasa x Karakamsa pairing" in text
        assert "NOT ENCODABLE from the mounted text" in text
        assert "PARTIAL" in text

    def test_the_recorded_evidence_matches_the_mounted_files(self):
        """The record claims karakamsa appears only in chapter 9 and never in the Chara
        Dasa chapter. That claim is checked, not trusted."""
        root = (pathlib.Path(__file__).resolve().parents[2] / "data"
                / "knowledge_library" / "sources" / "studies_jaimini_raman")
        if not root.is_dir():
            pytest.skip("JAIMINI corpus not mounted")
        hits = {f.name: f.read_text(encoding="utf-8", errors="replace").lower().count(
            "karakamsa") for f in sorted(root.glob("*.md"))}
        chara = next((n for n in hits if "planetary-and-rasi-strengths" in n), None)
        assert chara is not None, "the Chara Dasa chapter is not mounted"
        assert hits[chara] == 0, "chapter 4 now mentions karakamsa — re-open the item"
        assert any(v > 0 for n, v in hits.items() if "summary" in n)
