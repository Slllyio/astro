"""Marriage timing — HTJAH-II:852-883, the giving lords and the two delay factors.

Each test states the doctrinal fact it verifies. Citation tests are corpus-gated.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges import marriage_timing as mtm
from app.raman_saab.judges.marriage_timing import build_marriage_timing

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)

try:
    from app.raman_saab.doctrine.sources import verify
    _HAS_CORPUS = verify(mtm.CITE_GIVERS)
except Exception:  # noqa: BLE001
    _HAS_CORPUS = False


@pytest.fixture(scope="module")
def report():
    from app.raman_saab.detailed_report import build_detailed_report
    return build_detailed_report(_CANONICAL)


@pytest.fixture(scope="module")
def timing(report):
    return build_marriage_timing(report)


class TestGivingLords:
    def test_the_roster_is_built_and_ranked_by_strength(self, timing):
        """"The strongest of these lords gives marriage in his Dasa" (HTJAH-II:856). The
        roster is ranked, and the named winner is the strongest RANKED entry."""
        assert timing is not None and timing.givers
        ranked = [g for g in timing.givers if g.ranked]
        assert ranked
        assert timing.strongest == max(ranked, key=lambda g: g.strength_rupas).planet
        # ranked entries sort before unranked ones, strongest first
        assert [g.ranked for g in timing.givers] == sorted(
            [g.ranked for g in timing.givers], reverse=True)

    def test_every_giver_names_the_clause_that_nominated_it(self, timing):
        """A roster entry with no clause is an assertion without a reason. Each carries at
        least one of Raman's clauses and an anchor into the passage that states it."""
        for g in timing.givers:
            assert g.clauses, g.planet
            assert g.citations, g.planet
            assert all(c.startswith("HTJAH-II:") for c in g.citations), g.planet

    def test_a_planet_nominated_several_ways_keeps_every_clause(self, timing):
        """Several of Raman's clauses can land on one graha — on the canonical chart Venus
        qualifies as the karaka, as the 2nd lord, as the navamsa ruler of the 2nd lord's
        sign, and as the 9th lord. Collapsing those to the first would hide real support."""
        multi = [g for g in timing.givers if len(g.clauses) > 1]
        assert multi, "the canonical chart nominates at least one graha several ways"
        for g in multi:
            assert len(set(g.clauses)) == len(g.clauses), f"{g.planet}: duplicate clause"
            assert len(g.citations) == len(g.clauses)

    def test_the_conditional_lords_are_listed_but_not_ranked(self, timing):
        """Raman admits the 9th and 10th lords only "if the earlier Dasas are fruitless" —
        a condition about a life the engine has not seen. They are reported, and kept out of
        the strongest-of ranking rather than silently promoted."""
        conditional = [g for g in timing.givers if not g.ranked]
        for g in conditional:
            assert g.condition, g.planet
            assert "fruitless" in g.condition or "fruitless" in " ".join(g.clauses)
        assert timing.strongest not in [g.planet for g in conditional]

    def test_a_conditional_clause_never_erases_an_unconditional_one(self, timing):
        """If a graha already qualifies without Raman's caveat, a later conditional clause
        landing on it must not demote it — the unconditional nomination still stands, and
        the conditional clause is recorded alongside with its condition written into the
        clause text so it survives the merge."""
        for g in timing.givers:
            if g.ranked and any("fruitless" in c for c in g.clauses):
                assert len(g.clauses) > 1, (
                    f"{g.planet} is ranked on a conditional clause alone")

    def test_the_nodes_are_never_nominated(self, timing):
        """Raman's roster is of sign lords and the two luminaries. Rahu and Ketu own no
        sign and are not karakas of the 7th, so they cannot enter it."""
        assert all(g.planet not in ("Rahu", "Ketu") for g in timing.givers)


class TestDelayFactors:
    def test_both_of_ramans_screens_are_reported_fired_or_not(self, timing):
        """Two delay factors, always both reported. A screen that is silent is a finding —
        reporting only the ones that fire would leave a reader unable to tell 'checked and
        clear' from 'not checked'."""
        assert len(timing.delays) == 2
        assert {d.fired for d in timing.delays} <= {True, False}
        for d in timing.delays:
            assert d.rule and d.citation.startswith("HTJAH-II:")

    def test_a_fired_screen_names_the_specific_contacts(self, timing):
        """"Saturn's aspect on the 7th house and 7th lord ... and on Venus" — when it fires,
        the reading says WHICH of those contacts was found, not merely that it fired."""
        for d in timing.delays:
            if d.fired:
                assert d.because, d.name
            else:
                assert d.because == ()

    def test_ramans_conditionals_travel_with_every_firing(self, timing):
        """The Saturn screen delays marriage only "if the Dasa lord is not very strong", and
        the dusthana screen rules out EARLY marriage rather than marriage. Dropping either
        qualifier would turn a hedged classical statement into a flat claim."""
        by_name = {d.name: d for d in timing.delays}
        sat = next(d for d in by_name.values() if "Saturn" in d.name)
        dus = next(d for d in by_name.values() if "6th" in d.name)
        assert "not very strong" in sat.condition
        assert "early marriage" in dus.condition or "timing" in dus.condition
        assert "if the Dasa lord is not very strong" in sat.rule
        assert "rules out early marriage" in dus.rule

    def test_the_lean_never_claims_earliness_from_an_absence(self, timing):
        """Raman gives delay rules and no positive 'early marriage' rule here. When neither
        screen fires that is the ABSENCE of a delay indication, not evidence of earliness —
        a distinction the summary has to make explicitly."""
        if all(not d.fired for d in timing.delays):
            assert "not an indication of earliness" in timing.lean
        else:
            assert "delaying or ruling out EARLY marriage" in timing.lean
            assert "not as a denial of marriage" in timing.lean


class TestJupiterTransitMethod:
    def test_both_sphutas_are_computed_with_their_trines(self, timing):
        """Two resultants (HTJAH-II:869-873): Lagna-lord + 7th-lord, and Moon + 7th-lord.
        Jupiter transiting the resultant rasi OR ITS TRINES is favourable, so the trines are
        named too — a resultant without them is two thirds of the rule."""
        assert len(timing.jupiter_sphutas) == 2
        labels = {lbl for lbl, _s, _t in timing.jupiter_sphutas}
        assert labels == {"Lagna lord + 7th lord", "Moon + 7th lord"}
        for _lbl, sign, trines in timing.jupiter_sphutas:
            assert sign
            assert len(trines.split(", ")) == 2

    def test_the_transit_method_carries_ramans_own_subordination(self, timing):
        """He subordinates it himself one line later, and that sentence ships with it —
        the same standing PREC-6 already gives transits."""
        assert "Primary importance" in timing.subordination
        assert "secondary consideration to transiting planets" in timing.subordination


class TestFraming:
    def test_the_caveat_refuses_the_forecast_register(self, timing):
        assert "never a forecast" in timing.caveat
        assert "Nothing here states that a marriage occurs, or when" in timing.caveat

    def test_the_output_is_clean_under_the_decree_guard(self, timing):
        """Timed indications in the classical voice are allowed; the decree voice is not.
        Every free-text field this layer emits is checked."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        texts = [timing.lean, timing.caveat, timing.subordination, timing.strongest_rule]
        texts += [c for g in timing.givers for c in g.clauses]
        texts += [g.condition for g in timing.givers]
        texts += [d.rule for d in timing.delays] + [d.condition for d in timing.delays]
        texts += [b for d in timing.delays for b in d.because]
        for t in texts:
            if not t:
                continue
            m = _FORBIDDEN_RE.search(t)
            assert m is None, f"decree voice {m.group(0)!r} in: {t[:90]}"


@pytest.mark.skipif(not _HAS_CORPUS, reason="doctrine corpus not mounted")
class TestCitationsResolve:
    def test_every_anchor_resolves(self):
        from app.raman_saab.doctrine.sources import verify
        for c in (mtm.CITE_GIVERS, mtm.CITE_STRONGEST, mtm.CITE_JUPITER_TRANSIT,
                  mtm.CITE_DELAY, mtm.CITE_SUBORDINATION):
            assert verify(c), f"{c.work}:{c.line}"

    def test_the_quoted_rules_are_the_text_at_their_anchors(self):
        """Four sentences are quoted verbatim and the whole layer rests on them, so each is
        checked word-for-word against the printed page."""
        import re
        from app.raman_saab.doctrine.sources import _resolve_file
        lines = _resolve_file("HTJAH-II").read_text(
            encoding="utf-8", errors="replace").splitlines()

        def window(start: int, span: int = 8) -> str:
            return re.sub(r"\s+", " ", " ".join(lines[start - 1:start + span])).casefold()

        assert "strongest of these lords gives marriage in his dasa" in window(
            mtm.CITE_STRONGEST.line)
        assert "delays marriage if the dasa lord is not very strong" in window(
            mtm.CITE_DELAY.line)
        assert "rules out early marriage" in window(mtm.CITE_DELAY.line)
        assert "when jupiter transits the resultant rasi or" in window(
            mtm.CITE_JUPITER_TRANSIT.line)
        assert "only secondary consideration to transiting planets" in window(
            mtm.CITE_SUBORDINATION.line)


class TestVerdictAuthorityInvariant:
    def test_the_verdict_path_does_not_import_the_timing_layer(self):
        """The H7 verdict stays Raman's rasi judgment through `house_template`."""
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[2] / "app" / "raman_saab"
        # The verdict path, by its real paths. `judges/total.py` and `judges/conditions.py`
        # do not exist — EvalContext lives in `doctrine/conditions.py` and the Shadbala total
        # in `primitives/shadbala/total.py` — so the old tuple resolved to one file and the
        # `if f.exists()` guard silently skipped the rest. A guard that inspects nothing
        # passes, which is the one thing an invariant test must never do.
        verdict_path = (
            root / "judges" / "house_template.py",
            root / "judges" / "house_judge.py",
            root / "doctrine" / "conditions.py",
            root / "primitives" / "shadbala" / "total.py",
        )
        read = 0
        for f in verdict_path:
            assert f.exists(), f"the verdict path moved: {f}"
            read += 1
            src = f.read_text(encoding="utf-8")
            assert "marriage_timing" not in src, f
        assert read == len(verdict_path)


class TestAnUnmeasuredChartNamesNoStrongestGiver:
    """Raman names "the strongest of these lords", and `_rupas` returns 0.0 for a planet that
    carries no Shadbala. On a chart where no ranked giver has a measured strength every giver
    scores 0.0, `max` returns whichever was built first, and both renderers print that planet
    as "**(strongest)**" and "Here that is X" — a ranking asserted from construction order.
    """

    def test_all_zero_strengths_name_no_strongest(self, report, monkeypatch):
        """Without a measure there is no strongest, and the field says so by being empty."""
        monkeypatch.setattr(mtm, "_rupas", lambda chart, planet: 0.0)
        out = build_marriage_timing(report)
        assert out is not None
        assert out.strongest == ""
        assert any(g.ranked for g in out.givers), "the givers themselves must survive"

    def test_a_measured_chart_still_names_its_strongest(self, timing):
        """The canonical chart carries Shadbala, so the ranking is real and is kept."""
        ranked = [g for g in timing.givers if g.ranked]
        if not ranked or not any(g.strength_rupas > 0.0 for g in ranked):
            pytest.skip("this chart carries no measured giver strength")
        assert timing.strongest
        best = max(ranked, key=lambda g: g.strength_rupas)
        assert timing.strongest == best.planet
