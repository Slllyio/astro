"""The interpretation guide (report v18) — which section governs when two overlap.

CHART-INDEPENDENT doctrine metadata: every precedence rule below is a rule the report
ALREADY states somewhere (collected by the 2026-08-03 coherence audit), gathered into one
machine-readable structure so both readers and downstream consumers (LLM grounding, API
users) know which feature governs. Where no rule exists the pair is a PARALLEL LENS —
reported side by side, never averaged (the Measured-Truth default). Nothing here re-judges
anything (PREC-10 applies to this module too).

The `relation` field is a CLOSED vocabulary — governs / corroborates / different_grain /
re_read_of / parallel — so `report_explainer` can branch deterministically instead of
parsing prose. `authority` entries are repo `path:line` pointers; `citations` are corpus
WORK:line tokens (the frontend's click-to-source regex lifts them automatically).

PREC-1 is the one DERIVED rule (dashboard vs house-by-house grain) — doctrine-reviewed
before shipping; the grain distinction is PROJECT GOVERNANCE describing the encoded
mechanics, not a Raman citation, and says so in its rule text.
"""
from __future__ import annotations

from typing import Any, Final

INTERPRETATION_GUIDE: Final[dict[str, Any]] = {
    "version": "v18",
    "preamble": (
        "Sections in this report answer different questions at different grains. Where two "
        "disagree, one of the rules below governs; where no rule is listed, they are "
        "parallel lenses and are reported side by side (never averaged)."),

    "reading_order": [
        {"step": 1, "section_id": "plain_reading", "title": "Your Reading",
         "answers": "What does this chart say, in plain English?",
         "adds": "Hand-written prose built from the dashboard, the running period and the "
                 "distinctive entries.", "caveat_ref": "PREC-1"},
        {"step": 2, "section_id": "dashboard", "title": "The twelve matters at a glance",
         "answers": "Is THIS matter favourable?",
         "adds": "The authoritative per-matter verdict from each matter's dedicated "
                 "Raman-method reader.", "caveat_ref": "PREC-1"},
        {"step": 3, "section_id": "info_content", "title": "Information content + What stands out",
         "answers": "How much of that is about ME?",
         "adds": "The honesty gate: near-universal readings, inverted channels, and the few "
                 "entries that genuinely distinguish this chart. Read before believing "
                 "step 2.", "caveat_ref": "PREC-9"},
        {"step": 4, "section_id": "houses", "title": "House-by-house reading",
         "answers": "WHY does it read that way?",
         "adds": "Lord/karaka/navamsa/Bhava Bala per house, split-status notes, the "
                 "inverted-channel warning, and the population context.",
         "caveat_ref": "PREC-3"},
        {"step": 5, "section_id": "timeline", "title": "Life-narrative and Life-chapters",
         "answers": "WHEN?",
         "adds": "The four-tier fructification grade per bhukti; Life-chapters merges the "
                 "companion lenses into one prose chapter per Mahadasha, natal first, "
                 "transits last.", "caveat_ref": "PREC-6"},
    ],

    "precedence": [
        {"id": "PREC-1", "cluster": "house_matter_verdicts", "relation": "different_grain",
         "governs": [], "subordinate": [],
         "sections": ["dashboard", "houses"],
         "rule_text": (
             "The twelve matters at a glance gives ONE named signification, judged by its "
             "dedicated Raman-method reader (health = H6 disease_chronic; wealth = H2 "
             "wealth). House-by-house gives the whole bhava, graded by its WEAKEST DECIDED "
             "signification. A house can read afflicted while its headline matter reads "
             "favourable, and neither is wrong — ask the dashboard for a matter, the house "
             "block for a bhava. (The grain distinction is project governance describing "
             "the encoded mechanics, not a Raman citation.)"),
         "authority": ["app/raman_saab/judges/matter_varga_dashboard.py:100-103",
                       "app/raman_saab/judges/house_template.py:1918-1930",
                       "app/raman_saab/detailed_report.py ROLLUP_RULE"],
         "citations": []},
        {"id": "PREC-2", "cluster": "house_matter_verdicts", "relation": "governs",
         "governs": ["houses"], "subordinate": ["house_strength", "shadbala", "ashtakavarga"],
         "sections": ["houses", "house_strength", "shadbala", "ashtakavarga"],
         "rule_text": (
             "The verdict governs direction; Bhava Bala / Shadbala / SAV are magnitude: "
             "\"Neither measure changes the verdict shown above — they say whether it is "
             "well-supported or sits on thinner ground.\" (Bhava Drig Bala is signed by "
             "benefic/malefic aspect, GBB-9:180-219, so the axis is mostly — not perfectly "
             "— independent.)"),
         "authority": ["app/raman_saab/detailed_report.py:2730-2731"],
         "citations": ["HTJAH-I:468", "GBB-9:32", "GBB-9:332"]},
        {"id": "PREC-3", "cluster": "house_matter_verdicts", "relation": "governs",
         "governs": ["houses"], "subordinate": ["preponderance"],
         "sections": ["houses", "preponderance"],
         "rule_text": (
             "A headline is never its own witness: \"The Verdict column is the "
             "authoritative House-by-house verdict, unchanged — and it is deliberately NOT "
             "counted among its own witnesses.\" A most-contested flag means read that "
             "house with extra care, never flip the verdict."),
         "authority": ["app/raman_saab/detailed_report.py:2773-2775"],
         "citations": ["HTJAH-I:983", "HTJAH-I:495"]},
        {"id": "PREC-4", "cluster": "timing_lenses", "relation": "governs",
         "governs": ["timeline", "houses", "longevity"],
         "subordinate": ["av_dasha_seat", "ashtakavarga", "dasa_kakshya"],
         "sections": ["timeline", "av_dasha_seat", "ashtakavarga"],
         "rule_text": (
             "The AV tier never outranks a Raman-band reading: \"Ashtakavarga method is "
             "equally important. But, it does not seem to be quite reliable\" "
             "(HTJAH-II:4453-4456). An AV reading never overrides a Raman-band reading "
             "elsewhere in this report."),
         "authority": ["app/raman_saab/detailed_report.py:3025-3029",
                       "app/raman_saab/doctrine/synthesis_rules.py:1050-1051"],
         "citations": ["HTJAH-II:4453"]},
        {"id": "PREC-5", "cluster": "timing_lenses", "relation": "governs",
         "governs": ["timeline"], "subordinate": ["synthesis"],
         "sections": ["timeline", "synthesis"],
         "rule_text": (
             "The classical (Laghu Parashari) band yields to Raman: \"the two measure "
             "different things and can legitimately read differently for the same period; "
             "per this project's own governance, Raman's own grading is authoritative "
             "wherever they diverge.\""),
         "authority": ["app/raman_saab/doctrine/synthesis_rules.py:872-877"],
         "citations": ["HTJAH-I:1588", "HTJAH-I:2588"]},
        {"id": "PREC-6", "cluster": "transits", "relation": "governs",
         "governs": ["timeline", "life_chapters"],
         "subordinate": ["gochara", "dasha_transit"],
         "sections": ["timeline", "gochara", "dasha_transit"],
         "rule_text": (
             "Transits are secondary to the dasha, always: \"Transits are always secondary "
             "in importance. They are like catalytic agents. All conclusions must be "
             "primarily drawn on the basis of Dasa-vichara\" — a transit only catalyses "
             "what the running period permits."),
         "authority": ["app/raman_saab/detailed_report.py:878-882"],
         "citations": ["HTJAH-II:4679", "HTJAH-I:8410", "HPA-34:369"]},
        {"id": "PREC-7", "cluster": "timing_lenses", "relation": "governs",
         "governs": ["timeline"], "subordinate": ["dasa_kakshya"],
         "sections": ["timeline", "dasa_kakshya"],
         "rule_text": (
             "Dasha Kakshya is \"a timing lens, never a verdict\" — Raman reports the "
             "scheme from other scholars and works it over his own signature."),
         "authority": ["app/raman_saab/detailed_report.py:3054-3055"],
         "citations": ["ASP-12:174"]},
        {"id": "PREC-8", "cluster": "longevity_health", "relation": "governs",
         "governs": ["longevity"],
         "subordinate": ["maraka", "maraka_saturn", "health_readout"],
         "sections": ["longevity", "maraka", "maraka_saturn", "health_readout"],
         "rule_text": (
             "Longevity: band first, marakas second, the number is a cross-check: "
             "\"Raman's order: first establish the band by combination, THEN fix the "
             "period by the marakas. The numeric span is a cross-check, never a prediction "
             "of death.\""),
         "authority": ["app/raman_saab/detailed_report.py:2833-2836"],
         "citations": ["HTJAH-II:4465"]},
        {"id": "PREC-9", "cluster": "empirical_overlay", "relation": "corroborates",
         "governs": ["houses"], "subordinate": ["info_content", "stands_out"],
         "sections": ["houses", "info_content", "stands_out"],
         "rule_text": (
             "The empirical overlay never moves a verdict, but it can invert your "
             "confidence: each house states Raman's verdict, then discloses how it "
             "compares with 16,450 real charts. On the two atlas-proven INVERTED channels "
             "the overlay outranks the verdict as skepticism — \"treat this house's "
             "headline with maximal skepticism\" — never as a re-judgment."),
         "authority": ["app/raman_saab/detailed_report.py:2398-2402",
                       "app/raman_saab/judges/calibrated_reading.py:11-17"],
         "citations": []},
        {"id": "PREC-10", "cluster": "identity_synthesis", "relation": "re_read_of",
         "governs": [], "subordinate": [],
         "sections": ["plain_reading", "nichod", "synthesis", "ruler", "health_readout",
                      "preponderance", "life_chapters"],
         "rule_text": (
             "Every summary is a re-read; the section it summarizes is the source: "
             "\"NOTHING here is a new judgment: every clause selects, counts, or quotes "
             "something the rest of the report has already computed and disclosed.\" If a "
             "summary contradicts its source section, that is a defect, not a reading to "
             "adjudicate."),
         "authority": ["app/raman_saab/detailed_report.py Nichod docstring"],
         "citations": []},
        {"id": "PREC-11", "cluster": "house_matter_verdicts", "relation": "corroborates",
         "governs": ["dashboard"], "subordinate": ["divisional"],
         "sections": ["dashboard", "divisional"],
         "rule_text": ("The D1 Raman core decides; the divisional corroborates: \"The "
                       "Raman core is authoritative; the varga block corroborates "
                       "(report-only).\""),
         "authority": ["app/raman_saab/detailed_report.py:3195-3196"],
         "citations": []},
        {"id": "PREC-12", "cluster": "parallel_systems", "relation": "different_grain",
         "governs": [], "subordinate": [],
         "sections": ["houses", "pitru"],
         "rule_text": (
             "Non-Raman screens are a different layer, not a contradiction: the pitru "
             "curse-yogas are narrow technical gates about progeny/lineage, so a "
             "favourable House 9 or 4 can coexist with a curse-yoga firing — no "
             "contradiction to resolve."),
         "authority": ["app/raman_saab/judges/pitru_dosha_reading.py:516-524"],
         "citations": []},
    ],

    "parallel_lenses": [
        {"id": "PAR-1", "sections": ["ishta_kashta", "md_condition"],
         "why": "Two natal-fixed lenses painted across the same Mahadasha timeline; "
                "neither is ranked above the other."},
        {"id": "PAR-2", "sections": ["deeptadi", "shadbala", "houses", "ishta_kashta"],
         "why": "State, magnitude, direction and tendency are different axes: \"These "
                "axes are not meant to always agree — a planet can be strong yet in a "
                "hard state, or favourable yet thin — and reading two of them apart is "
                "not a contradiction to resolve.\""},
        {"id": "PAR-3", "sections": ["karakamsa", "soul", "houses", "timeline"],
         "why": "Jaimini's sign-based system runs parallel to Parashari + Vimshottari; "
                "no precedence is stated anywhere in the corpus the project encodes."},
        {"id": "PAR-4", "sections": ["career", "dashboard", "houses"],
         "why": "Three career readings at three grains (HTJAH-II navamsa-dispositor "
                "line, the D-10 dashboard core, the H10 rollup); PREC-1's grain rule "
                "applies, no ranking exists."},
    ],

    "axes": [
        {"axis": "verdict", "means": "direction", "sections": ["houses", "dashboard"],
         "citation": "HTJAH-I:468"},
        {"axis": "bhava_bala", "means": "magnitude",
         "sections": ["house_strength", "shadbala"], "citation": "GBB-9:32",
         "qualification": "Bhava Drig Bala is signed by benefic/malefic aspect "
                          "(GBB-9:180-219), so magnitude is not perfectly independent of "
                          "direction."},
        {"axis": "avastha", "means": "state", "sections": ["deeptadi"],
         "citation": "HPA-7:1"},
        {"axis": "ishta_kashta", "means": "tendency", "sections": ["ishta_kashta"],
         "citation": "GBB-10:134"},
        {"axis": "ashtakavarga", "means": "corroborating tier (lower reliability)",
         "sections": ["ashtakavarga", "av_dasha_seat"], "citation": "HTJAH-II:4453"},
    ],

    "not_a_contradiction": [
        {"a": "dashboard", "b": "houses",
         "why": "The dashboard grades one named signification; the house headline grades "
                "the whole bhava by its weakest decided one.",
         "precedence_id": "PREC-1"},
        {"a": "pitru", "b": "houses",
         "why": "A different threshold on the same ground — narrow progeny/lineage gates "
                "vs the full multi-factor house judgment.",
         "precedence_id": "PREC-12"},
    ],

    "relation_vocabulary": ["governs", "corroborates", "different_grain", "re_read_of",
                            "parallel"],
}
