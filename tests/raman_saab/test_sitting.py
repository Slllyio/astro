"""The Sitting — the continuous reading, and the flow mechanisms it carries.

Measured before it was built (one generated Mainpuri reading): the honesty hedge restated 26
times, "Jupiter" named 211 times with zero accumulated identity, no backward references at
all, and timing prose that put the mechanism before the life. Raman's own NH prose does the
opposite on every count, and the Sitting imitates his arc: grip, striking feature, cast, life
told forward, callback close.

What these tests pin, beyond guard-cleanliness:

* **The callback is real and testable** — the closing repeats `grip_key`, and the weave in the
  house leads fires only as a genuine cross-reference (never the circular "the same Saturn,
  the deciding voice in house 3, carries house 3", which shipped for one iteration).
* **Epithets are earned** — every clause traces to a computed fact in `basis`, and no epithet
  smuggles a verdict word into what should be identity, not judgment.
* **Event-first is pinned as a shape**, not a vibe: timing prose opens on the life, not on a
  planet name.
* **The hedge census** — the consolidation decision (2026-08-07): the frame speaks once plus
  the guard trio, not 26 times.
"""
from __future__ import annotations

import re

import pytest

from app.llm.report_explainer import _FORBIDDEN_RE
from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report, to_markdown
from app.raman_saab.sitting import build_sitting

_CHARTS = [
    ("mainpuri", BirthData("Mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03)),
    ("akash", BirthData("Akash", 1989, 12, 11, 6, 20, 5.5, 23.20, 77.08)),
    ("canonical", BirthData("Canonical", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)),
    ("southern", BirthData("Southern", 1975, 3, 3, 4, 30, 5.5, -33.87, 151.21)),
    # the pre-1906 case: the Sitting must render, with the timing paragraph degrading honestly
    ("victoria", BirthData("Queen Victoria", 1819, 5, 24, 4, 15, 0.0, 51.51, -0.14)),
]


@pytest.fixture(scope="module")
def reports():
    return {n: build_detailed_report(bd) for n, bd in _CHARTS}


def _all_text(s) -> str:
    return " ".join([s.grip, s.closing] + [t for _h, t in s.paragraphs])


class TestEverySentenceIsGuardSafe:
    def test_no_paragraph_trips_the_guard(self, reports):
        trips = []
        for name, r in reports.items():
            s = r.sitting
            m = _FORBIDDEN_RE.search(_all_text(s))
            if m:
                trips.append((name, m.group(0)))
        assert not trips, f"the Sitting asserts a forecast: {trips}"


class TestTheCallbackIsReal:
    def test_the_closing_answers_the_grip(self, reports):
        """The whole point of a close: it returns to the thesis. Pinned on `grip_key`, which
        both the grip's frame and the closing must carry — asserted, not assumed."""
        for name, r in reports.items():
            s = r.sitting
            assert s.grip_key, name
            assert s.grip_key in s.closing, (
                f"{name}: the closing does not repeat the grip's key phrase — the reading "
                f"opens a thesis it never returns to")

    def test_the_weave_is_never_circular(self, reports):
        """'the same Saturn, the deciding voice in house 3, carries house 3' shipped for one
        iteration. An epithet earned FROM a house may not be called back IN that house."""
        from app.raman_saab.plainspoken import plain_for_house
        for name, r in reports.items():
            for h in range(1, 13):
                lead = plain_for_house(r, h) or ""
                m = re.search(r"the same \w+, the deciding voice in house (\d+)", lead)
                if m:
                    assert int(m.group(1)) != h, f"{name}/H{h}: circular callback — {lead[-160:]}"

    def test_the_weave_fires_somewhere(self, reports):
        """Across five charts at least one genuine cross-reference must appear; a weave that
        never weaves is dead code wearing a feature's name."""
        from app.raman_saab.plainspoken import plain_for_house
        hits = [f"{name}/H{h}"
                for name, r in reports.items()
                for h in range(1, 13)
                if "the same " in (plain_for_house(r, h) or "")]
        assert hits, "no house lead ever calls back to a cast member on any chart"


class TestTheCastIsEarned:
    def test_bounded_and_never_nodes(self, reports):
        for name, r in reports.items():
            cast = r.sitting.cast
            assert 1 <= len(cast) <= 3, name
            assert not {m.planet for m in cast} & {"Rahu", "Ketu"}, (
                f"{name}: a node entered the cast — nodes carry no lordship and no Atmakaraka "
                f"role (the Chara-Karaka lock)")

    def test_every_epithet_has_a_basis(self, reports):
        for name, r in reports.items():
            for m in r.sitting.cast:
                assert m.basis, f"{name}/{m.planet}: an epithet with no computed fact behind it"

    def test_epithets_carry_identity_not_judgment(self, reports):
        """An epithet says WHO the planet is in this chart, never how its matters turned out.
        Verdict words in an epithet would smuggle judgment into every callback."""
        for name, r in reports.items():
            for m in r.sitting.cast:
                assert not re.search(r"\b(favourable|afflicted|good|bad|weak|strong(?!est))\b",
                                     m.epithet, re.I), f"{name}: {m.epithet!r}"

    def test_supporting_cast_members_are_distinct(self, reports):
        """Victoria's Jupiter and Saturn both read 'a steady presence...' before the lordship
        fallback existed. Two cast members may never share one anonymous epithet."""
        for name, r in reports.items():
            eps = [m.epithet.split(", ", 1)[1] for m in r.sitting.cast if ", " in m.epithet]
            assert len(eps) == len(set(eps)), f"{name}: duplicate epithets {eps}"


class TestEventFirstShape:
    def test_the_in_time_paragraph_opens_on_the_life(self, reports):
        """Raman: 'In his 16th year, Gautama was married... Mark the fact that Saturn owns the
        7th.' The window or the life opens; the mechanism follows. A planet name opening the
        paragraph is the old engine order."""
        for name, r in reports.items():
            text = dict(r.sitting.paragraphs).get("In time", "")
            if not text:
                continue
            assert not re.match(r"^(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b",
                                text), f"{name}: mechanism-first — {text[:80]}"

    def test_victoria_degrades_honestly(self, reports):
        s = reports["victoria"].sitting
        text = dict(s.paragraphs).get("In time", "")
        assert "does not reach" in text, "the out-of-span case must be disclosed, not omitted"
        assert "(beyond computed sequence)" not in _all_text(s), "sentinel leaked into prose"


class TestTheHedgeCensus:
    """The consolidation decision: the frame speaks once (the header legend) plus the guard
    trio (longevity, arishta, maraka) and the medical line — not 26 times."""

    _HEDGE = re.compile(
        r"not a prediction|never a forecast|not a forecast|not a statement about your life",
        re.I)

    def test_the_family_is_consolidated(self, reports):
        md = to_markdown(reports["mainpuri"])
        n = len(self._HEDGE.findall(md))
        assert n <= 8, (
            f"the hedge family appears {n} times — the consolidation decision caps it at 8 "
            f"(one frame + the guard trio + structural)")

    def test_the_guard_trio_still_carries_it(self, reports):
        """Consolidation must never strip the three sections whose subject demands the line."""
        from app.raman_saab.plainspoken import plain_for_section
        r = reports["mainpuri"]
        assert "not a statement about your life" in (plain_for_section(r, "longevity") or "")
        assert "nothing here is timed against your life" in (plain_for_section(r, "maraka") or "")


class TestTheSectionRendersEverywhere:
    def test_markdown_carries_the_sitting(self, reports):
        md = to_markdown(reports["mainpuri"])
        assert "## The reading, as one sitting" in md
        assert reports["mainpuri"].sitting.grip[:60] in md

    def test_html_carries_the_sitting(self, reports):
        from app.raman_saab.report_html import to_html
        ht = to_html(reports["mainpuri"])
        assert 'id="sitting"' in ht

    def test_json_carries_the_sitting(self, reports):
        from app.raman_saab.report_json import to_report_dict
        d = to_report_dict(reports["mainpuri"])
        assert d["sitting"] and d["sitting"]["grip"] and d["sitting"]["cast"]
