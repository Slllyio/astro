"""Guard tests for app/raman_saab/doctrine/significations.py.

Spec (Phase A1):
  1. Every Signification.source is a real on-disk corpus line.
  2. Every alternate_frame_core / primary_karaka is a canonical planet name.
  3. Mandatory karaka-as-Lagna frames are wired (H4 mother, H7 spouse, H9 father).
  4. All 12 houses are covered, each with at least one Signification.
  5. Every rule_tag appears as a real signification= value in rule_sets/.

Usage:
    py -3.12 -m pytest tests/raman_saab/doctrine/test_significations.py -v
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module under test (import deferred so RED run gives ImportError, not a crash
# in the collection phase — still counts as a failure)
# ---------------------------------------------------------------------------
from app.raman_saab.doctrine.significations import (
    SIGNIFICATIONS,
    Signification,
    significations_of,
    karaka_for,
)
from app.raman_saab.doctrine.sources import verify, Citation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_CANONICAL_PLANETS: frozenset[str] = frozenset(
    {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
)

_RULE_SETS_DIR: Path = (
    Path(__file__).resolve().parents[3]
    / "app" / "raman_saab" / "doctrine" / "rule_sets"
)


def _all_rule_set_significations() -> frozenset[str]:
    """Collect every signification= string value in rule_sets/house_* modules.

    A house rule-set may be a flat module (house_02_dhana.py) or a subpackage of
    group modules (house_01_lagna/ since the Stage-1 split) — recurse into both.
    """
    pattern = re.compile(r'signification\s*=\s*["\']([^"\']+)["\']')
    found: set[str] = set()
    for entry in _RULE_SETS_DIR.glob("house_*"):
        py_files = sorted(entry.rglob("*.py")) if entry.is_dir() else [entry]
        for py_file in py_files:
            for match in pattern.finditer(py_file.read_text(encoding="utf-8")):
                found.add(match.group(1))
    return frozenset(found)


def _all_significations() -> list[Signification]:
    sigs: list[Signification] = []
    for tup in SIGNIFICATIONS.values():
        sigs.extend(tup)
    return sigs


# ---------------------------------------------------------------------------
# Test 1 — every source is a real on-disk corpus line
# ---------------------------------------------------------------------------
class TestEverySignificationCitesARealCorpusLine:
    """Every Signification.source must pass verify()."""

    def test_every_signification_cites_a_real_corpus_line(self) -> None:
        """verify(sig.source) is True for every signification across all 12 houses."""
        bad: list[tuple[int, str, Citation]] = []
        for house, sigs in SIGNIFICATIONS.items():
            for sig in sigs:
                if not verify(sig.source):
                    bad.append((house, sig.key, sig.source))

        if bad:
            lines = "\n  ".join(
                f"H{h} '{k}': {c}" for h, k, c in bad
            )
            pytest.fail(
                f"{len(bad)} unverifiable citation(s):\n  {lines}"
            )


# ---------------------------------------------------------------------------
# Test 2 — frame_core / primary_karaka are canonical planets (no Rahu/Ketu)
# ---------------------------------------------------------------------------
class TestFrameCoresAreCanonicalPlanets:
    """alternate_frame_core and primary_karaka must be in the 7-planet set (or None)."""

    def test_frame_cores_are_canonical_planets(self) -> None:
        """No Rahu, Ketu, or invented name may appear as a karaka/frame core."""
        bad: list[tuple[int, str, str, str]] = []
        for house, sigs in SIGNIFICATIONS.items():
            for sig in sigs:
                for field_name, value in (
                    ("primary_karaka", sig.primary_karaka),
                    ("alternate_frame_core", sig.alternate_frame_core),
                ):
                    if value is not None and value not in _CANONICAL_PLANETS:
                        bad.append((house, sig.key, field_name, value))

        if bad:
            lines = "\n  ".join(
                f"H{h} '{k}' {fn}={v!r}" for h, k, fn, v in bad
            )
            pytest.fail(
                f"{len(bad)} non-canonical planet name(s):\n  {lines}"
            )


# ---------------------------------------------------------------------------
# Test 3 — mandatory karaka-as-Lagna frames are present
# ---------------------------------------------------------------------------
class TestMandatoryFramesPresent:
    """H4 mother, H7 spouse, H9 father each require alternate_frame_core set."""

    @pytest.mark.parametrize(
        "house, key, expected_core",
        [
            (4, "mother", "Moon"),
            (7, "spouse", "Venus"),
            (9, "father", "Sun"),
        ],
    )
    def test_mandatory_frame_core(
        self, house: int, key: str, expected_core: str
    ) -> None:
        """Mandatory karaka-as-Lagna frames must encode the correct alternate_frame_core."""
        sigs = SIGNIFICATIONS.get(house, ())
        matching = [s for s in sigs if s.key == key]
        assert matching, (
            f"No Signification with key={key!r} found in house {house}"
        )
        sig = matching[0]
        assert sig.alternate_frame_core == expected_core, (
            f"H{house} key={key!r}: expected alternate_frame_core={expected_core!r}, "
            f"got {sig.alternate_frame_core!r}"
        )


# ---------------------------------------------------------------------------
# Test 4 — all 12 houses covered with at least one signification
# ---------------------------------------------------------------------------
class TestAll12HousesHaveSignifications:
    """SIGNIFICATIONS must be a complete 12-house map, each non-empty."""

    def test_all_12_houses_covered(self) -> None:
        """set(SIGNIFICATIONS) == set(range(1, 13)) and each tuple non-empty."""
        missing = set(range(1, 13)) - set(SIGNIFICATIONS)
        assert not missing, f"Houses missing from SIGNIFICATIONS: {sorted(missing)}"

    def test_each_house_non_empty(self) -> None:
        """Each house has at least one Signification record."""
        empty = [h for h, sigs in SIGNIFICATIONS.items() if not sigs]
        assert not empty, f"Houses with empty signification tuples: {sorted(empty)}"


# ---------------------------------------------------------------------------
# Test 5 — rule_tags reference existing rule_set signification= values
# ---------------------------------------------------------------------------
class TestRuleTagsMatchExistingBuckets:
    """Every rule_tag in every Signification must exist as a signification= value."""

    def test_rule_tags_match_existing_buckets(self) -> None:
        """No rule_tag that doesn't appear in rule_sets/house_*.py files."""
        known = _all_rule_set_significations()
        bad: list[tuple[int, str, str]] = []
        for house, sigs in SIGNIFICATIONS.items():
            for sig in sigs:
                for tag in sig.rule_tags:
                    if tag not in known:
                        bad.append((house, sig.key, tag))

        if bad:
            lines = "\n  ".join(
                f"H{h} '{k}': unknown tag {t!r}" for h, k, t in bad
            )
            pytest.fail(
                f"{len(bad)} rule_tag(s) not in rule_sets:\n  {lines}\n"
                f"Known tags: {sorted(known)}"
            )

    def test_every_authored_signification_is_reachable(self) -> None:
        """REVERSE direction: every signification= a rule is authored under must appear in SOME
        Signification's rule_tags, else those rules fire and are silently discarded by _bucket_fired
        (the dead-rule class the audit found: H2 speech/vision/family + H3 courage)."""
        authored = _all_rule_set_significations()
        reachable: set[str] = set()
        for sigs in SIGNIFICATIONS.values():
            for sig in sigs:
                reachable.update(sig.rule_tags)
        unreachable = sorted(authored - reachable)
        assert not unreachable, (
            f"{len(unreachable)} rule signification(s) are in NO Signification.rule_tags -> their "
            f"rules fire but are discarded: {unreachable}")
