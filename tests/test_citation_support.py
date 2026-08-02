"""Citation SUPPORT — `app/llm/citation_support.py`.

`provenance_check` scores citation PRESENCE; this layer scores whether the cited fact actually
contains the number/planet/sign/yoga the sentence asserts. Measured on the Phase-2 teacher
corpus (2026-08-02): 12.8% of checkable single-cite sentences failed this check, 78% of them by
pointing at the wrong fact rather than by inventing anything — which is why repair and refusal
are separate paths here.
"""
from __future__ import annotations

from app.llm.citation_support import (
    audit_citations,
    checkable_tokens,
    fact_supports,
    repair_citations,
)
from app.llm.report_explainer import Evidence, Fact


def _ev(*texts: str) -> Evidence:
    return Evidence(scope="test",
                    facts=tuple(Fact(n=i, text=t) for i, t in enumerate(texts, start=1)))


class TestCheckableTokens:
    def test_extracts_numbers_planets_signs_nakshatras_and_yogas(self):
        """Every entity class the evidence can assert is checkable."""
        toks = checkable_tokens("Scorpio Lagna, Moon in Dhanishta, 5 of 6 witnesses, Amala Yoga.")
        assert {"Scorpio", "Moon", "Dhanishta", "#5", "#6", "Amala Yoga"} <= toks

    def test_citation_markers_do_not_leak_their_digits_as_claims(self):
        """[Fact 7] is a pointer, not an assertion of the number seven."""
        assert checkable_tokens("The ruler is Mars [Fact 7].") == frozenset({"Mars"})

    def test_non_vedic_bodies_are_checkable_so_they_can_never_pass(self):
        """Raman's system has no outer planets — no fact can support one, so a model importing
        Pluto from its general astrology training must be caught, not silently accepted."""
        assert "Pluto" in checkable_tokens("Your ruler is shadowed by Pluto.")

    def test_number_words_are_not_checked(self):
        """'one of the clearest strengths' is idiom, not a count — scoring it only false-fires."""
        assert checkable_tokens("This is one of the clearest strengths here.") == frozenset()


class TestFactSupports:
    def test_small_numbers_must_match_exactly(self):
        """House 5 vs House 6 is the very error being hunted — no tolerance below 10."""
        assert fact_supports("#5", "House 5 is the most-contested house.")
        assert not fact_supports("#6", "House 5 is the most-contested house.")

    def test_large_numbers_tolerate_the_engine_s_own_rounding(self):
        """'about 72 years' renders a 72.4-year longevity — +-1 keeps that from reading as an error."""
        assert fact_supports("#72", "The longevity band is purna — about 71 years.")
        assert not fact_supports("#72", "The longevity band is purna — about 84 years.")

    def test_entity_names_match_case_insensitively_on_word_boundaries(self):
        assert fact_supports("Mars", "the lagna lord is mars.")
        assert not fact_supports("Mars", "The strongest planet by Shadbala is Mercury.")


class TestAuditCitations:
    def test_a_correctly_cited_sentence_is_clean(self):
        ev = _ev("The ruler of the nativity (the Lagna lord) is Mars.")
        assert audit_citations("Your chart's ruler is Mars [Fact 1].", ev).is_clean

    def test_a_token_living_in_another_fact_is_mis_attribution_not_fabrication(self):
        """The claim is true of the evidence; only the pointer is wrong."""
        ev = _ev("The ruler of the nativity (the Lagna lord) is Mars.",
                 "Chart identity: Scorpio Lagna, MOON is the stronger frame.")
        audit = audit_citations("Your rising sign is Scorpio [Fact 1].", ev)
        assert audit.mis_attributed == (("Scorpio", 1, 2),)
        assert not audit.unsupported

    def test_a_token_in_no_fact_is_unsupported(self):
        """Nothing in the evidence computed this — the safety case."""
        ev = _ev("The ruler of the nativity (the Lagna lord) is Mars.")
        audit = audit_citations("Your rising sign is Gemini [Fact 1].", ev)
        assert audit.unsupported == (("Gemini", 1),)
        assert not audit.mis_attributed

    def test_multi_citation_sentences_are_skipped_as_ambiguous(self):
        """Which half of the claim belongs to which fact is unknowable — never guess."""
        ev = _ev("The ruler is Mars.", "The strongest planet by Shadbala is Mercury.")
        audit = audit_citations("Mars rules while Gemini rises [Fact 1] [Fact 2].", ev)
        assert audit.checked_sentences == 0
        assert audit.is_clean

    def test_an_out_of_range_citation_is_left_to_the_bad_anchor_guard(self):
        ev = _ev("The ruler is Mars.")
        assert audit_citations("Your ruler is Mars [Fact 9].", ev).checked_sentences == 0


class TestRepairCitations:
    def test_a_wholly_misaimed_citation_is_moved_to_the_supporting_fact(self):
        """One fact covers every token in the sentence — the pointer was simply wrong."""
        ev = _ev("The ruler of the nativity (the Lagna lord) is Mars.",
                 "Chart identity: Scorpio Lagna, MOON is the stronger frame.")
        fixed, n = repair_citations("Your rising sign is Scorpio [Fact 1].", ev)
        assert n == 1
        assert fixed == "Your rising sign is Scorpio [Fact 2]."
        assert audit_citations(fixed, ev).is_clean

    def test_a_sentence_drawing_on_two_facts_gains_the_second_citation(self):
        """The cited fact backs the Mahadasha, another backs the sub-period lord — anchor both."""
        ev = _ev("You are currently in the Rahu Mahadasha: Rahu's Mahadasha is in view "
                 "Nov 2014 to Nov 2032.",
                 "The current sub-period lord is Venus.")
        fixed, n = repair_citations(
            "You are in Rahu's Mahadasha with Venus as the sub-period lord [Fact 1].", ev)
        assert n == 1
        assert "[Fact 1] [Fact 2]" in fixed
        assert audit_citations(fixed, ev).is_clean

    def test_a_fabricated_token_is_never_papered_over(self):
        """No fact supports it, so there is nothing honest to point at — leave it for refusal."""
        ev = _ev("The ruler of the nativity (the Lagna lord) is Mars.")
        text = "Your rising sign is Gemini [Fact 1]."
        fixed, n = repair_citations(text, ev)
        assert (fixed, n) == (text, 0)
        assert audit_citations(fixed, ev).unsupported

    def test_an_ambiguously_supported_token_is_left_alone(self):
        """Two facts mention Mercury — guessing which one the claim meant would invent an error."""
        ev = _ev("The ruler of the nativity (the Lagna lord) is Mars.",
                 "The strongest planet by Shadbala is Mercury.",
                 "You are currently in the Mercury Mahadasha.")
        text = "Mercury is the running period lord [Fact 1]."
        fixed, n = repair_citations(text, ev)
        assert (fixed, n) == (text, 0)
        assert audit_citations(text, ev).mis_attributed == (("Mercury", 1, None),)

    def test_repair_leaves_a_clean_answer_untouched(self):
        ev = _ev("The ruler of the nativity (the Lagna lord) is Mars.")
        text = "Your chart's ruler is Mars [Fact 1]."
        assert repair_citations(text, ev) == (text, 0)
