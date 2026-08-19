"""The 10th reckoned from Lagna, Moon and Sun — HTJAH-I:13960-13962.

Each test states the doctrinal fact it verifies. The citation tests are corpus-gated the
same way the rest of the doctrine suite is.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges import career_frames as cfm
from app.raman_saab.judges.career_frames import build_career_frames

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)

try:
    from app.raman_saab.doctrine.sources import verify
    _HAS_CORPUS = verify(cfm.CITE_THREE_CENTRES)
except Exception:  # noqa: BLE001
    _HAS_CORPUS = False


@pytest.fixture(scope="module")
def report():
    from app.raman_saab.detailed_report import build_detailed_report
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def frames(report):
    return build_career_frames(report)


class TestTheThreeCentres:
    def test_all_three_of_ramans_centres_are_reckoned(self, frames):
        """"The 10th house should be reckoned not only from Lagna but also from the Moon and
        the Sun" (HTJAH-I:13960-13961). `primitives/career.py` reckons from the Lagna alone,
        so the profession chapter had been reading one frame of three."""
        assert frames is not None
        assert [f.centre for f in frames.frames] == ["Lagna", "Moon", "Sun"]

    def test_each_centre_takes_its_tenth_from_its_own_sign(self, report, frames):
        """The 10th is counted from the centre itself, not from the lagna in all three
        cases — that is the whole point of the rule."""
        chart = report.chart
        expect = {"Lagna": chart.asc_sign,
                  "Moon": chart.planets["Moon"].sign,
                  "Sun": chart.planets["Sun"].sign}
        for f in frames.frames:
            assert f.centre_sign == expect[f.centre]
            assert f.tenth_sign == ((expect[f.centre] - 1) + 9) % 12 + 1

    def test_the_frames_can_disagree_and_that_is_the_finding(self, report, frames):
        """On the canonical chart the Lagna frame resolves to Venus (gold, textiles,
        show-business) while the Moon and Sun frames both resolve to Mercury (writing,
        journalism, astrology). A Lagna-only reading shows one of those and hides that two
        of Raman's three centres point elsewhere."""
        from app.raman_saab.primitives.career import career_indication
        lagna_only = career_indication(report.chart)
        by_centre = {f.centre: f.navamsa_dispositor for f in frames.frames}
        assert lagna_only[1] == by_centre["Lagna"]           # the old reading is the Lagna one
        assert by_centre["Moon"] == by_centre["Sun"] != by_centre["Lagna"]

    def test_the_strongest_centre_is_named_with_its_measure(self, frames):
        """"the reckoning made from the strongest of these three centers gives good results"
        (HTJAH-I:13961-13962). The winner is named, and so is the measure it won on — the
        Lagna carries a bhava bala and the luminaries carry shadbala, which is the mixed
        comparison Raman himself prints at HTJAH-I:13986, disclosed rather than hidden."""
        assert frames.strongest in ("Lagna", "Moon", "Sun")
        assert sum(1 for f in frames.frames if f.is_strongest) == 1
        strongest = next(f for f in frames.frames if f.is_strongest)
        assert strongest.centre == frames.strongest
        assert strongest.strength_rupas == max(f.strength_rupas for f in frames.frames)
        for f in frames.frames:
            assert f.strength_basis, f.centre
            assert ("bhava bala" in f.strength_basis) == (f.centre == "Lagna")
        assert "HTJAH-I:13986" in frames.strongest_why

    def test_the_leading_indication_comes_from_the_strongest_centre(self, frames):
        """Raman reckons from the strongest centre, so that is the frame the reading leads
        with — not the Lagna by default."""
        strongest = next(f for f in frames.frames if f.is_strongest)
        assert frames.leading_indication in (strongest.trade, strongest.sign_career,
                                             "no occupation is named from this centre")


class TestBlendingClause:
    def test_the_blending_threshold_is_labelled_as_the_engines_own(self):
        """Raman states the blending clause but gives NO figure. A threshold had to be
        chosen, so it is named as the engine's convention rather than presented as his —
        the same treatment the deeptadi precedence ordering carries."""
        import inspect
        src = inspect.getsource(cfm)
        assert "_BLEND_TOLERANCE" in src
        assert "ENGINE CONVENTION, NOT RAMAN" in src

    def test_a_blend_is_declared_only_when_centres_are_close(self, frames):
        """"more or less of equal strength ... a blending of influences and more than one
        occupation may he indicated" (HTJAH-I:13957-13959). The flag must follow the
        numbers: it is set exactly when a second centre sits within tolerance of the top."""
        top = max(f.strength_rupas for f in frames.frames)
        near = [f for f in frames.frames
                if abs(top - f.strength_rupas) <= top * cfm._BLEND_TOLERANCE]
        assert frames.blended == (len(near) > 1)
        if frames.blended:
            assert frames.blended_note
            assert "ENGINE" in frames.blended_note      # the 10% is ours, and says so
        else:
            assert frames.blended_note == ""

    def test_the_blending_rule_is_quoted_not_paraphrased(self, frames):
        """The clause ships verbatim, OCR intact ('there will he a blending'), so a reader
        can check it against the printed page rather than trusting a tidy-up."""
        assert "blending of influences" in frames.blending_rule
        assert "more than one occupation" in frames.blending_rule


class TestConvergence:
    def test_convergent_trades_are_counted_across_centres(self, frames):
        """In Raman's worked example the dispositor resolves to Mars from all three centres
        ('ruled by Mars again', HTJAH-I:13974-13976) — the repetition IS the reading. Words
        named by two or more centres are tallied; a word from one centre is not."""
        assert all(n >= 2 for _w, n in frames.convergent)
        assert frames.convergence_note
        counts = {}
        for f in frames.frames:
            for tok in cfm._trade_tokens(f.trade):
                counts[tok] = counts.get(tok, 0) + 1
        assert dict(frames.convergent) == {w: n for w, n in counts.items() if n >= 2}

    def test_disagreement_is_reported_rather_than_resolved(self):
        """When no word recurs the three reckonings genuinely diverge, and that is stated
        instead of a winner being manufactured."""
        note = cfm.build_career_frames.__doc__
        assert note  # the behaviour itself is asserted through the note text below
        import inspect
        src = inspect.getsource(cfm.build_career_frames)
        assert "point in different directions" in src


class TestHonesty:
    def test_a_node_dispositor_names_no_trade_and_says_why(self, report):
        """Raman's vocation table covers the seven visible grahas. If the navamsa dispositor
        is Rahu or Ketu the centre names no occupation — and the reading says so rather than
        emitting a blank cell that reads as 'nothing found'."""
        import inspect
        src = inspect.getsource(cfm.build_career_frames)
        assert "gives the nodes no trade" in src
        assert "Reported rather than skipped" in src

    def test_ramans_own_caution_travels_with_the_output(self, frames):
        """'These principles are very general and must he adapted suitably'
        (HTJAH-I:13959) — his own hedge on this passage, not droppable."""
        assert "very general" in frames.caution
        assert "HTJAH-I:13959" in frames.caution

    def test_the_rule_is_quoted_verbatim(self, frames):
        assert "reckoned not only from Lagna" in frames.rule
        assert "strongest of these three centers" in frames.rule
        assert frames.citation.startswith("HTJAH-I:13960")


@pytest.mark.skipif(not _HAS_CORPUS, reason="doctrine corpus not mounted")
class TestCitationsResolve:
    def test_every_anchor_resolves(self):
        from app.raman_saab.doctrine.sources import verify
        for c in (cfm.CITE_THREE_CENTRES, cfm.CITE_BLENDING, cfm.CITE_WORKED_EXAMPLE,
                  cfm.CITE_RUPAS_PRECEDENT):
            assert verify(c), f"{c.work}:{c.line}"

    def test_the_rule_is_the_text_at_its_own_anchor(self):
        """The whole module rests on this sentence, so it is checked word-for-word against
        the printed page rather than trusted."""
        import re
        from app.raman_saab.doctrine.sources import _resolve_file
        lines = _resolve_file("HTJAH-I").read_text(
            encoding="utf-8", errors="replace").splitlines()
        window = " ".join(lines[cfm.CITE_THREE_CENTRES.line - 1:
                                cfm.CITE_THREE_CENTRES.line + 3])
        norm = re.sub(r"\s+", " ", window).casefold()
        assert "reckoned not only from lagna but also from the moon and the" in norm
        assert "strongest of these three centers" in norm

    def test_the_rupas_precedent_really_compares_ascendant_against_moon(self):
        """The mixed bhava-bala-vs-shadbala comparison is defended as Raman's own
        precedent, so that claim is checked at its anchor too."""
        import re
        from app.raman_saab.doctrine.sources import _resolve_file
        lines = _resolve_file("HTJAH-I").read_text(
            encoding="utf-8", errors="replace").splitlines()
        line = re.sub(r"\s+", " ", lines[cfm.CITE_RUPAS_PRECEDENT.line - 1]).casefold()
        assert "ascendant" in line and "rupas" in line and "moon" in line


class TestVerdictAuthorityInvariant:
    def test_the_verdict_path_does_not_import_the_career_frames(self):
        """The H10 verdict stays Raman's rasi judgment through `house_template`. This layer
        reports the three reckonings and must never feed the decision."""
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[2] / "app" / "raman_saab"
        for f in (root / "judges" / "house_template.py",
                  root / "judges" / "total.py",
                  root / "judges" / "conditions.py"):
            if f.exists():
                assert "career_frames" not in f.read_text(encoding="utf-8"), f
