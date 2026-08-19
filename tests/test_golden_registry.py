"""Tests for the Run-5 golden-case registry (loader, OCR validator, split)."""
from __future__ import annotations

import copy

import pytest

from app.medini.ml.raman_saab.golden_registry import (
    REGISTRY_PATH, SPLIT_SEED, GoldenCaseV2, _dms_to_deg, load_registry,
    split, validate_case,
)


@pytest.fixture(scope="module")
def registry():
    return load_registry(REGISTRY_PATH)


class TestLoader:
    def test_dms_parsing(self):
        assert _dms_to_deg([349, 15]) == pytest.approx(349.25)
        assert _dms_to_deg([0, 30]) == pytest.approx(0.5)

    def test_registry_loads_with_ketu_derived(self, registry):
        tilak = next(c for c in registry if c.key == "tilak")
        assert tilak.positions["Ketu"] == pytest.approx(
            (tilak.positions["Rahu"] + 180.0) % 360.0)

    def test_excluded_cases_flagged(self, registry):
        ex = {c.key for c in registry if c.exclude}
        assert {"hitler", "franco", "dalmia", "farouk", "shaw"} <= ex


class TestValidator:
    def test_known_good_run4_cases_validate(self, registry):
        # The four run-4 Tier-A charts must pass the MD anchor.
        for key in ("tilak", "ramana", "einstein", "gandhi"):
            case = validate_case(copy.deepcopy(
                next(c for c in registry if c.key == key)))
            assert case.valid, f"{key}: {case.fail_reason}"

    def test_corrupted_moon_rejected(self, registry):
        case = copy.deepcopy(next(c for c in registry if c.key == "tilak"))
        case.positions["Moon"] = (case.positions["Moon"] + 90.0) % 360.0
        case = validate_case(case)
        assert not case.valid

    def test_ad_flag_recorded_not_gating(self, registry):
        # Gandhi: MD anchors, AD famously disagrees with Raman's own
        # arithmetic (run-4 finding) -> valid with ad_anchor_ok False.
        case = validate_case(copy.deepcopy(
            next(c for c in registry if c.key == "gandhi")))
        assert case.valid and case.ad_anchor_ok is False

    def test_marx_date_repair(self, registry):
        # Printed "15th May 1818"; positions fit the historical 5 May.
        case = validate_case(copy.deepcopy(
            next(c for c in registry if c.key == "marx")))
        assert case.valid and case.date_repaired

    def test_predictive_cases_stay_excluded(self, registry):
        case = validate_case(copy.deepcopy(
            next(c for c in registry if c.key == "hitler")))
        assert not case.valid and "pre-excluded" in case.fail_reason


class TestSplit:
    def test_split_deterministic_and_disjoint(self, registry):
        cases = [validate_case(copy.deepcopy(c)) for c in registry]
        c1, h1 = split(cases, seed=SPLIT_SEED)
        c2, h2 = split(cases, seed=SPLIT_SEED)
        assert [c.key for c in c1] == [c.key for c in c2]
        assert [c.key for c in h1] == [c.key for c in h2]
        assert not ({c.key for c in c1} & {c.key for c in h1})
        # both halves usable
        assert len(c1) >= 15 and len(h1) >= 15
        assert all(c.valid and c.tier == "A" for c in c1 + h1)
