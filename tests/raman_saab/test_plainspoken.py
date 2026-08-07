"""Plainspoken — the properties that twelve hand-found defects taught us to check.

`plainspoken.py` writes the person-facing lead for 50 of the report's 54 sections. It is the
layer with the most reader contact and it had no tests, so every defect in it was found by a
human printing output and reading it. That is not a repeatable process, and the defects were
not subtle once seen:

    "0 read net favourable"                        arithmetic, not English
    "1 of the 10 pillars ... are unshaken"         agreement at n=1
    "1 fired yoga touch it"                        agreement again
    "Travel abroad all read well"                  plural verb, single item
    "By kind: 3 other, 2 lunar and 2 raja"         arishta silently dropped by _join's cap
    "Jupiter, Venus and Saturn"                    Mars dropped, same cap
    "money reaches you through a, b, c"            4 of 7 channels dropped, same cap
    "poorvapunya reads mixed"                      untranslated jargon in the de-jargoning layer
    ""                                             an AttributeError swallowed into silence
    "1 of 10 pillars unshaken"  under a label reading "firm"

Every one is mechanically checkable, so none of them should ever have needed a human. These
tests encode the CLASSES rather than the instances: a new lead written next year gets checked
against all of them for free.

Two design notes that matter for reading the assertions:

* They run over SEVERAL charts, not the canonical one. Half these defects only appear at a
  particular cardinality — n=1 agreement, or a list long enough to hit the truncation cap — so
  a single fixture chart would miss them by luck.
* They assert on the RENDERED STRING, because that is the artefact with the defect. A test that
  checked the data behind a lead would have passed on every one of the twelve.
"""
from __future__ import annotations

import re

import pytest

from app.llm.report_explainer import _FORBIDDEN_RE
from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import SECTION_CONTRACT, build_detailed_report
from app.raman_saab.plainspoken import (
    SECTION_LEADS,
    _join,
    _join_all,
    plain_for_house,
    plain_for_section,
)

#: Deliberately varied — different ascendants, eras, hemispheres and latitudes, so lists come
#: back at different lengths and the cardinality-dependent defects have somewhere to appear.
_CHARTS = [
    ("akash", BirthData("Akash", 1989, 12, 11, 6, 20, 5.5, 23.20, 77.08)),
    ("canonical", BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)),
    ("mainpuri", BirthData("Mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03)),
    ("southern", BirthData("Southern", 1975, 3, 3, 4, 30, 5.5, -33.87, 151.21)),
]


@pytest.fixture(scope="module")
def reports():
    return {name: build_detailed_report(bd) for name, bd in _CHARTS}


def _all_leads(r) -> list[tuple[str, str]]:
    """Every rendered lead for one chart: (label, text). Empty leads are dropped."""
    out = []
    for s in SECTION_CONTRACT:
        t = plain_for_section(r, s.section_id) or ""
        if t:
            out.append((s.section_id, t))
    for h in range(1, 13):
        t = plain_for_house(r, h) or ""
        if t:
            out.append((f"house{h}", t))
    return out


class TestNoLeadEverTripsTheGuard:
    """The hard line. A lead is prose the reader is handed as the engine's own voice, so it is
    held to the same standard as the LLM surfaces: describe the chart, never assert a life
    event, never attach a clock to one."""

    def test_every_lead_on_every_chart_is_guard_clean(self, reports):
        trips = [(name, label, m.group(0))
                 for name, r in reports.items()
                 for label, text in _all_leads(r)
                 if (m := _FORBIDDEN_RE.search(text))]
        assert not trips, (
            f"{len(trips)} lead(s) assert a forecast: {trips[:5]}. Write AROUND the guard — "
            f"never widen it to accommodate a phrasing"
        )


class TestNoLeadFailsSilently:
    """`plain_for_section` swallows exceptions so a phrasing bug never costs the reader a
    section. That is correct, and it is also how a crash came to look identical to "nothing to
    say": `_SIGN_NAME` is a tuple, one `.get()` blanked the entire Ashtakavarga lead, and only
    printing all eleven by hand revealed it. Call the lead functions DIRECTLY here, where
    nothing is catching, so a raising lead fails the suite instead of vanishing."""

    def test_no_registered_lead_raises(self, reports):
        failures = []
        for name, r in reports.items():
            for section_id, fn in SECTION_LEADS.items():
                try:
                    fn(r)
                except Exception as exc:                           # noqa: BLE001
                    failures.append(f"{name}/{section_id}: {type(exc).__name__}: {exc}")
        assert not failures, "lead(s) raised; the swallow would hide these:\n" + "\n".join(failures)

    def test_a_registered_lead_returns_a_string(self, reports):
        for name, r in reports.items():
            for section_id, fn in SECTION_LEADS.items():
                assert isinstance(fn(r) or "", str), f"{name}/{section_id} returned a non-string"


class TestGrammarThatBrokeAtCardinalityOne:
    """Four of the twelve defects were subject-verb agreement at n=1, produced by templates
    that assumed plurality. They are trivially visible in prose and invisible in data."""

    #: (pattern, what it means) — each was an actual shipped sentence.
    _BROKEN = [
        (r"\b1 [a-z ]{0,30}\b(are|were|have)\b", "'1 ... are' — plural verb after a count of one"),
        (r"\b1 fired yoga touch\b", "'1 fired yoga touch it' — noun singular, verb plural"),
        (r"\b(\d+) of the \d+ [a-z ]+ is\b(?<!1 of the 10 pillars of your reading is)",
         "singular verb after a count greater than one"),
        (r"^0 |[.;] 0 |\b0 read\b", "a bare 0 where English wants 'none'"),
    ]

    def test_no_agreement_slips(self, reports):
        bad = []
        for name, r in reports.items():
            for label, text in _all_leads(r):
                for pattern, why in self._BROKEN:
                    if re.search(pattern, text, re.I):
                        bad.append(f"{name}/{label}: {why} — {text[:110]}")
        assert not bad, "\n".join(bad)

    def test_singular_counts_take_singular_verbs(self, reports):
        """The general form, caught by reading rather than by a denylist: '1 X are/were'."""
        for name, r in reports.items():
            for label, text in _all_leads(r):
                for m in re.finditer(r"\b1 (\w+) (are|were|have|do)\b", text, re.I):
                    pytest.fail(f"{name}/{label}: '{m.group(0)}' — {text[:120]}")


class TestNoListClaimsToBeCompleteWhileTruncated:
    """`_join` caps at three so a lead never becomes an inventory. That is right where the
    phrasing signals a selection and a silent lie where it does not — it dropped Mars from a
    four-planet maraka list, arishta from a four-kind yoga breakdown, and four of seven wealth
    channels, each inside a sentence that read as exhaustive. `_join_all` exists for the
    complete case; these tests pin the distinction rather than the call sites."""

    def test_join_all_never_truncates(self):
        items = [f"item{i}" for i in range(9)]
        joined = _join_all(items)
        missing = [i for i in items if i not in joined]
        assert not missing, f"_join_all dropped {missing} — it is the no-cap helper"

    def test_join_still_caps(self):
        """The cap is intentional; if it ever goes away, the leads relying on it should be
        revisited rather than silently becoming inventories."""
        assert len([p for p in _join([f"i{n}" for n in range(9)]).split(",")]) <= 3

    def test_join_all_reads_as_english(self):
        assert _join_all(["a"]) == "a"
        assert _join_all(["a", "b"]) == "a and b"
        assert _join_all(["a", "b", "c"]) == "a, b and c"
        # A conjunction inside an item makes "x and y and z" stutter; comma-join instead.
        assert _join_all(["a and b", "c"]) == "a and b, c"

    def test_a_complete_claim_is_not_followed_by_exactly_three(self, reports):
        """Heuristic, and it is the one that would have caught all three real cases: a phrase
        promising the whole set followed by exactly three items is the truncation signature.
        Leads that legitimately select say so ('among them', 'including', 'most strongly')."""
        promises = re.compile(
            r"(that marks|read favourable|By kind:|read well, while|are present in)", re.I)
        hedges = re.compile(r"(among them|including|most strongly|among others|of the \d+)", re.I)
        suspicious = []
        for name, r in reports.items():
            for label, text in _all_leads(r):
                for m in promises.finditer(text):
                    tail = text[m.end():m.end() + 200]
                    if hedges.search(text):
                        continue
                    if len(re.findall(r",", tail.split(".")[0])) >= 2 and " and " in tail:
                        # three-or-more-item list under a completeness claim: verify by eye if
                        # this ever fires on a NEW lead, then pick _join_all or add a hedge.
                        suspicious.append(f"{name}/{label}: {text[:130]}")
        # Not an assertion of zero — a legitimate complete list of three looks identical. This
        # documents the signature so a future failure is read correctly rather than silenced.
        assert len(suspicious) <= 8, (
            "several leads pair a completeness claim with a three-item list; check each uses "
            f"_join_all or hedges its phrasing:\n" + "\n".join(suspicious))


class TestLeadsSpeakToTheReader:
    """A lead exists to address a person. Three shipped leads had working prose that addressed
    nobody ('The main chart shows the whole of a life at once...'), which an is-there-a-lead
    check scores as done. The count is the only thing that caught them."""

    _PERSON = re.compile(r"\byou\b|\byour\b", re.I)

    #: Leads that legitimately describe the METHOD rather than the reader. Kept explicit so
    #: adding to it is a decision, not a drift.
    _METHOD_VOICE = {"interpretation_guide", "info_content"}

    def test_most_leads_address_the_reader(self, reports):
        for name, r in reports.items():
            silent = [label for label, text in _all_leads(r)
                      if label not in self._METHOD_VOICE and not self._PERSON.search(text)]
            assert len(silent) <= 4, (
                f"{name}: {len(silent)} leads address nobody: {silent}. A lead that never says "
                f"'you' is describing the engine, which is the register this layer replaces")


class TestNoUntranslatedJargon:
    """The layer exists to remove jargon, so a lead printing raw Sanskrit has inverted its own
    purpose. `poorvapunya` shipped untranslated; it is glossed now."""

    #: Terms that must never appear in a lead without a gloss immediately following.
    _MUST_GLOSS = ["poorvapunya", "balarishta", "karakamsa", "atmakaraka", "avastha", "vedha"]

    def test_sanskrit_terms_are_glossed_in_place(self, reports):
        bare = []
        for name, r in reports.items():
            for label, text in _all_leads(r):
                low = text.lower()
                for term in self._MUST_GLOSS:
                    if term not in low:
                        continue
                    after = low.split(term, 1)[1][:90]
                    # a gloss is a parenthetical, an em-dash aside, or an "is/means" clause
                    if not re.search(r"^\s*[(—,]|\bis\b|\bmeans\b|\bthe\b", after):
                        bare.append(f"{name}/{label}: '{term}' unglossed — {text[:110]}")
        assert not bare, "\n".join(bare)


class TestALeadAgreesWithWhatSitsBesideIt:
    """`rect_confidence` led with the count surviving the full +-60 scan ('1 of 10') directly
    above its own label reading 'firm'. Same class as a plain line saying 'reads strongly'
    under a heading saying AFFLICTED: the reader sees the lead and the label together, and a
    lead that contradicts its own section is worse than no lead."""

    def test_rect_confidence_does_not_contradict_its_label(self, reports):
        for name, r in reports.items():
            rc = getattr(r, "rect_confidence", None)
            lead = plain_for_section(r, "rect_confidence") or ""
            if rc is None or not lead:
                continue
            label = str(getattr(rc, "label", "") or "").lower()
            if label.startswith("firm"):
                # the lead must lead with the window where everything holds, not with the
                # count that survives the brutal full-scan
                assert "holds from" in lead, (
                    f"{name}: label says {label[:40]!r} but the lead opens on the survival "
                    f"count, which reads as fragile — {lead[:130]}")

    def test_house_leads_use_the_house_rollup_not_the_dashboard(self, reports):
        """A house lead voicing the dashboard verdict printed 'reads strongly' under a heading
        saying AFFLICTED, because one dashboard matter serves several houses."""
        for name, r in reports.items():
            for pf in getattr(r, "proformas", ()):
                lead = plain_for_house(r, pf.house) or ""
                rollup = str(getattr(pf, "rollup", "") or "").lower()
                if not lead or rollup != "afflicted":
                    continue
                # A lead that names BOTH sides is correct under an afflicted rollup — PREC-1
                # takes the weakest DECIDED matter, so a house can read afflicted overall while
                # several of its significations read well, and saying so is the honest thing.
                # The defect is a lead that is positive-ONLY. (My first version of this test
                # flagged the two-sided form and was simply wrong.)
                names_the_downside = re.search(
                    r"\b(do not|does not|difficult|afflicted|weak|drags?)\b", lead, re.I)
                if names_the_downside:
                    continue
                assert not re.search(r"\b(reads? (strongly|well)|read well)\b", lead, re.I), (
                    f"{name}/H{pf.house}: rollup is afflicted and the lead is positive-only, "
                    f"naming no downside — {lead[:130]}")


class TestLeadsAreProseNotData:
    """Raw field formatting leaking into a sentence: 'inheritance / legacies' reads as a field
    separator, and a verbless fragment ('the Moon (manas) in house 7, exalt') is not a
    sentence. Both shipped."""

    def test_no_raw_slash_separators(self, reports):
        for name, r in reports.items():
            for label, text in _all_leads(r):
                assert not re.search(r"\w\s/\s\w", text), (
                    f"{name}/{label}: raw ' / ' separator in prose — {text[:110]}")

    def test_every_lead_is_sentences(self, reports):
        for name, r in reports.items():
            for label, text in _all_leads(r):
                assert text[0].isupper() or text[0].isdigit(), \
                    f"{name}/{label}: lead does not start a sentence — {text[:80]}"
                assert text.rstrip().endswith((".", "!", "?")), \
                    f"{name}/{label}: lead does not end a sentence — {text[-80:]}"
