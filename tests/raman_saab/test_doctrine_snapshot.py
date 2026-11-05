"""Standing guard: nothing in the doctrine layer moves without someone saying why.

The golden ratchet scores 397 rows and is blind to everything else. It cannot see which of
Raman's readings a rule chose to display, because `_bucket_fired` buckets by `rule.polarity`
and never looks at the branch. So a change can leave the ratchet at exactly 286/362/35 while
altering what hundreds of charts actually SAY — which is the product.

`tools/raman_saab/doctrine_snapshot.py` freezes three levels for every castable golden
(varga signs, fired rules with their branch and text hash, per-signification verdicts). This
test asserts the live engine still matches. Regenerating requires an explicit `--note`, so a
re-freeze is always a recorded decision rather than a silent overwrite.

**When this test fails, that is the tool working.** Read the diff:

* only `PREDICATE` lines  -> presentation moved; no verdict changed. Check it was intended,
  then re-freeze with a note saying what moved and why.
* any `VERDICT` line      -> the engine's judgement changed. The ratchet may still be green
  (a verdict can move without crossing a scored row); this is your only warning.
* any `PRIMITIVE` line    -> an ephemeris or varga computation changed. Almost never intended.

    py -3.12 -m tools.raman_saab.doctrine_snapshot --check --verbose
    py -3.12 -m tools.raman_saab.doctrine_snapshot --write --note "why this moved"
"""
from __future__ import annotations

import json

import pytest

from tools.raman_saab import doctrine_snapshot as ds


@pytest.fixture(scope="module")
def live() -> dict:
    return ds.build_snapshot()


class TestTheCorpusHasNotDrifted:
    def test_the_snapshot_exists(self) -> None:
        assert ds.SNAPSHOT_PATH.is_file(), (
            "no frozen doctrine snapshot; create one with "
            "`py -3.12 -m tools.raman_saab.doctrine_snapshot --write --note '<why>'`")

    def test_nothing_changed_across_the_whole_golden_corpus(self, live) -> None:
        frozen = ds.decode(json.loads(ds.SNAPSHOT_PATH.read_text(encoding="utf-8")))
        diffs = ds.diff(frozen, live)
        kinds = sorted({d.split()[0] for d in diffs})
        assert not diffs, (
            f"{len(diffs)} difference(s) from the frozen doctrine snapshot "
            f"(kinds: {', '.join(kinds)}). If deliberate, re-freeze with a note; if not, "
            f"this is the regression. First few:\n"
            + "\n".join(f"  {d}" for d in diffs[:15]))

    def test_every_level_is_populated(self, live) -> None:
        """A level that silently records nothing reads as 'identical' forever. The first
        version of the tool defaulted a wrong attribute name to {} on all 346 charts and
        reported success; this is the assertion that would have caught it."""
        charts = live["charts"]
        assert len(charts) > 300
        for level in ("varga_signs", "fired", "verdicts"):
            populated = sum(1 for c in charts.values() if c[level])
            assert populated == len(charts), f"{level} empty on {len(charts) - populated} charts"

    def test_the_snapshot_carries_its_lineage(self) -> None:
        """Every deliberate re-freeze appends a note. A baseline that can be overwritten
        silently is not a baseline — it is whatever the last run produced."""
        frozen = json.loads(ds.SNAPSHOT_PATH.read_text(encoding="utf-8"))
        lineage = frozen.get("lineage", [])
        assert lineage, "the snapshot has no lineage; it was written without --note"
        assert all(isinstance(x, str) and x.strip() for x in lineage)


class TestTheDiffReportsWhatMatters:
    """The diff is the instrument an engineer reads at 2am; it must not lie by omission."""

    def test_a_changed_verdict_is_reported_as_a_verdict(self) -> None:
        old = {"charts": {"c1": {"varga_signs": {}, "fired": [], "verdicts": {"H8/death": "a"}}}}
        new = {"charts": {"c1": {"varga_signs": {}, "fired": [], "verdicts": {"H8/death": "b"}}}}
        d = ds.diff(old, new)
        assert len(d) == 1 and d[0].startswith("VERDICT")

    def test_a_changed_branch_is_reported_even_when_the_rule_still_fires(self) -> None:
        """The subtle case: same rule, same chart, different reading shown. Invisible to the
        ratchet, and the whole reason this snapshot records the branch."""
        old = {"charts": {"c1": {"varga_signs": {}, "fired": [["R1", "afflicted", "h"]],
                                 "verdicts": {}}}}
        new = {"charts": {"c1": {"varga_signs": {}, "fired": [["R1", "general", "h"]],
                                 "verdicts": {}}}}
        d = ds.diff(old, new)
        assert len(d) == 2
        assert any("no longer" in x and "afflicted" in x for x in d)
        assert any("newly" in x and "general" in x for x in d)

    def test_changed_text_is_caught_even_when_rule_and_branch_are_identical(self) -> None:
        """Editing a rule's prose without touching its id or branch still changes the
        reading; the text hash is what makes that visible."""
        old = {"charts": {"c1": {"varga_signs": {}, "fired": [["R1", "general", "aaa"]],
                                 "verdicts": {}}}}
        new = {"charts": {"c1": {"varga_signs": {}, "fired": [["R1", "general", "bbb"]],
                                 "verdicts": {}}}}
        assert len(ds.diff(old, new)) == 2

    def test_a_chart_that_stops_casting_is_reported_not_skipped(self) -> None:
        old = {"charts": {"c1": {"varga_signs": {}, "fired": [], "verdicts": {}}}}
        assert any("NO LONGER castable" in x for x in ds.diff(old, {"charts": {}}))

    def test_identical_snapshots_produce_no_diff(self, live) -> None:
        assert ds.diff(live, live) == []


class TestThePersistenceFormatIsLossless:
    """`encode`/`decode` exist so the file can shrink without the diff losing precision.
    That claim is only worth anything if the round trip is exact — otherwise compaction
    would quietly weaken the guard it was meant to preserve."""

    def test_round_trip_reproduces_the_rich_form_exactly(self, live) -> None:
        assert ds.decode(ds.encode(live)) == live

    def test_a_round_tripped_snapshot_diffs_clean_against_itself(self, live) -> None:
        """The end-to-end property: storing and reloading must not manufacture a diff."""
        assert ds.diff(ds.decode(ds.encode(live)), live) == []

    def test_a_stale_format_fails_loudly_instead_of_diffing(self) -> None:
        """A format mismatch would otherwise surface as hundreds of phantom doctrine
        changes — the most misleading failure this tool could produce."""
        with pytest.raises(ValueError, match="format"):
            ds.decode({"format": 0, "tables": {}, "charts": {}})

    def test_the_tables_stay_greppable(self) -> None:
        """Interning is only acceptable if a human can still find a rule by name."""
        compact = json.loads(ds.SNAPSHOT_PATH.read_text(encoding="utf-8"))
        fired = compact["tables"]["fired"]
        assert any(e.startswith("H8.P.Mars|") for e in fired), "rule ids must remain searchable"
        assert all(e.count("|") == 2 for e in fired), "each entry is ruleId|branch|textHash"

    def test_the_file_is_small_enough_to_carry_in_the_repo(self) -> None:
        """It is regenerated on every deliberate doctrine change, so size is history size."""
        kb = ds.SNAPSHOT_PATH.stat().st_size / 1024
        assert kb < 1500, f"snapshot is {kb:,.0f} KB — compaction regressed"
