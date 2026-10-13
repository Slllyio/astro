"""The 81-pair antardasa verse table (BPHS ch.52-60) — coverage, citation integrity, evaluation."""
from __future__ import annotations

from app.parashara.doctrine.antardasa_verses import all_citations, grade_pair, verses
from app.parashara.doctrine.sources import verify

_LORDS = ("Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu", "Venus")


class TestCoverage:
    def test_all_81_pairs_present(self):
        """Every Vimshottari (dasa, antardasa) pair has its own BPHS section."""
        assert set(verses()) == {(m, a) for m in _LORDS for a in _LORDS}

    def test_every_clause_citation_resolves(self):
        """All clause lines point at real corpus lines (465 clauses)."""
        cites = all_citations()
        assert len(cites) >= 400
        assert all(verify(c) for c in cites)


class TestGrading:
    def test_saturn_venus_good_clause_needs_benefic_contact(self):
        """BPHS-57:237's good clause requires Venus 'associated with or aspected by benefics': with
        that contact it fires (-> mixed with the :292 dasa-lord-frame bad clause); without it,
        only the bad clause fires (-> adverse); with no context it is unevaluated, never guessed."""
        from app.parashara.doctrine.antardasa_verses import QualifierContext
        kw = dict(asc_sign=8, signs={"Saturn": 9, "Venus": 8, "Sun": 6},
                  longitudes={"Saturn": 250.0, "Venus": 215.0, "Sun": 170.0})
        with_b = grade_pair("Saturn", "Venus", **kw, ctx=QualifierContext(True, True, False, False, True))
        assert {("good", 237), ("bad", 292)} <= {(f.kind, f.source.line) for f in with_b.fired}
        assert with_b.quality == "mixed"
        without = grade_pair("Saturn", "Venus", **kw, ctx=QualifierContext(False, False, False, False, True))
        assert without.quality == "adverse"
        unknown = grade_pair("Saturn", "Venus", **kw)
        assert all(f.source.line != 237 for f in unknown.fired) and unknown.unevaluated >= 1

    def test_exalted_antardasa_lord_fires_a_good_clause(self):
        """Sun's own antardasa with the Sun exalted (Aries): ch.52's good clause fires."""
        g = grade_pair("Sun", "Sun", asc_sign=4, signs={"Sun": 1},
                       longitudes={"Sun": 10.0})
        assert g is not None and any(f.kind == "good" for f in g.fired)

    def test_required_qualifier_is_unevaluated_not_fired(self):
        """A clause with a REQUIRED qualifier never fires on placement alone (review 2026-10-13)."""
        from app.parashara.doctrine.antardasa_verses import _clause_holds
        c = {"houses": [1, 4, 7, 10], "frame": "lagna", "requires_qualifier": True}
        assert _clause_holds(c, 1, 1, set(), set(), 1) is None

    def test_unconditional_clause_always_holds(self):
        """A general result stated with no condition (Sun/Ketu BPHS-52:458) always holds."""
        g = grade_pair("Sun", "Ketu", asc_sign=1, signs={"Sun": 1, "Ketu": 3},
                       longitudes={"Sun": 5.0, "Ketu": 65.0})
        assert g is not None and any(f.kind == "bad" and f.source.line == 458 for f in g.fired)

    def test_rahu_rahu_needs_its_named_sign(self):
        """Rahu/Rahu :49 good needs BOTH an upachaya AND Cancer/Scorpio/Virgo/Sagittarius."""
        from app.parashara.doctrine.antardasa_verses import _clause_holds, verses
        c = next(x for x in verses()[("Rahu", "Rahu")]["good"] if x["line"] == 49)
        assert _clause_holds(c, 3, 1, set(), set(), sign=4) is True     # 3rd house, Cancer
        assert _clause_holds(c, 3, 1, set(), set(), sign=1) is False    # 3rd house, Aries

    def test_lacking_words_read_as_weak_not_strong(self):
        """'bereft of strength' / 'deprived of strength' mean WEAK — they used to invert."""
        from app.parashara.doctrine.antardasa_verses import QualifierContext, _qualifier_holds
        strong = QualifierContext(False, False, False, False, True)
        for q in ("bereft of strength", "deprived of strength", "without strength", "weak"):
            assert _qualifier_holds(q, strong) is False, q

    def test_extra_and_conjunct_is_not_dropped(self):
        """'deprived of strength and dignity' / 'weak and be associated with Saturn...' carry a
        second requirement this reader does not check -> unevaluated, never half-read."""
        from app.parashara.doctrine.antardasa_verses import QualifierContext, _qualifier_holds
        ctx = QualifierContext(True, True, True, True, False)
        assert _qualifier_holds("deprived of strength and dignity", ctx) is None
        assert _qualifier_holds("be weak and be associated with Saturn, , Mars and Rahu", ctx) is None

    def test_association_and_aspect_are_kept_apart(self):
        """'associated with malefics' = conjunction only; 'aspected by benefics' = drishti only;
        'associated with or aspected by' = either."""
        from app.parashara.doctrine.antardasa_verses import QualifierContext, _qualifier_holds
        aspect_only = QualifierContext(False, True, False, True, True)
        assert _qualifier_holds("associated with malefics", aspect_only) is False
        assert _qualifier_holds("aspected by benefics", aspect_only) is True
        assert _qualifier_holds("associated with or aspected by malefics", aspect_only) is True

    def test_missing_planet_falls_back(self):
        """No position for a lord -> no verse grade (the caller uses the generic rule)."""
        assert grade_pair("Sun", "Moon", asc_sign=1, signs={"Sun": 1}, longitudes={"Sun": 5.0}) is None
