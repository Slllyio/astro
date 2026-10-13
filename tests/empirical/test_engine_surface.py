"""The shipped engine — what it will serve, and what it refuses to.

The load-bearing tests here are the refusals. An engine that can be talked into
serving an unvalidated claim is worse than one with no claims at all, because a
null is honest and a false positive is not.
"""

from __future__ import annotations

import json

import pytest

from app.empirical.engine.report import FRAMING, claim_sentence, render, to_markdown
from app.empirical.engine.survivors import (
    CalibrationBin,
    Claim,
    SurvivorSet,
    from_screening_report,
    load_survivors,
    write_survivors,
)


def _claim(**overrides) -> Claim:
    base = dict(
        test_id="T001", feature_bank="western", target="marriage",
        delta=0.031, ci_low=0.008, ci_high=0.054, p_value=0.004,
        n=2344, base_rate=0.41, coverage=0.18,
    )
    base.update(overrides)
    return Claim(**base)


class TestClaimRefusals:
    """A claim must have earned its place before it can exist at all."""

    def test_nonpositive_delta_rejected(self):
        """Matching the chartless twin is not beating it."""
        with pytest.raises(ValueError, match="beat its chartless twin"):
            _claim(delta=0.0)

    def test_negative_delta_rejected(self):
        """Losing to the baseline is a finding, but never a claim."""
        with pytest.raises(ValueError, match="beat its chartless twin"):
            _claim(delta=-0.02)

    def test_impossible_base_rate_rejected(self):
        """A rate outside [0,1] means the pipeline is broken upstream."""
        with pytest.raises(ValueError, match="base_rate"):
            _claim(base_rate=1.4)

    def test_malformed_claim_rejected_at_load(self, tmp_path):
        """Hand-editing the JSON must not smuggle a claim past validation."""
        path = tmp_path / "survivors.json"
        path.write_text(json.dumps({
            "claims": [{
                "test_id": "BAD", "feature_bank": "western", "target": "x",
                "delta": -0.5, "ci_low": -1.0, "ci_high": 0.0, "p_value": 0.001,
                "n": 100, "base_rate": 0.2, "coverage": 0.5,
            }],
            "stage": "confirmatory",
        }))
        with pytest.raises(ValueError, match="beat its chartless twin"):
            load_survivors(path)


class TestShippability:
    """Screening candidates are not claims."""

    def test_screening_stage_is_not_shippable(self):
        """The holdout has not been read, so nothing is established."""
        assert not SurvivorSet(stage="screening").is_shippable

    def test_confirmatory_stage_is_shippable(self):
        """Only a confirmatory set may serve claims."""
        assert SurvivorSet(stage="confirmatory").is_shippable

    def test_screening_set_never_carries_claims(self):
        """from_screening_report must not promote survivors to claims.

        Promotion without a confirmatory run is precisely the failure the frozen
        holdout exists to prevent.
        """
        report = {
            "n_registered": 18, "n_survivors": 4,
            "survivors": [{"test_id": "SCR-western-military", "delta": 0.058}],
            "verdict": "4 of 18 registered tests survived.",
        }
        built = from_screening_report(report, corpus="test")
        assert built.claims == ()
        assert not built.is_shippable

    def test_screening_payload_says_so_on_its_face(self):
        """A reader must not have to infer that nothing is established."""
        built = from_screening_report({"n_registered": 18}, corpus="test")
        payload = render(built)
        assert payload["result"] == "screening_only"
        assert "nothing here is a finding" in payload["caveat"]


class TestNullState:
    """A null is a result and must read as one."""

    def test_empty_confirmatory_set_renders_a_measured_null(self):
        """No claims after a real run is a measurement, not a blank."""
        payload = render(SurvivorSet(stage="confirmatory"))
        assert payload["result"] == "null"
        assert "measured result" in payload["headline"]
        assert payload["n_claims"] == 0

    def test_null_still_discloses_what_was_tested(self):
        """'We looked and found nothing' must be distinguishable from 'we did not look'."""
        built = SurvivorSet(
            stage="confirmatory",
            tested=({"test_id": "T1", "delta": -0.01, "outcome": "tested_no_effect"},),
            controls=("sham_target", "chartless_baseline"),
        )
        payload = render(built)
        assert payload["tests_run"] == 1
        assert payload["controls_every_test_faced"] == ["sham_target", "chartless_baseline"]

    def test_unbuilt_is_not_reported_as_a_null(self):
        """Nothing measured here is a different statement from measured-nothing."""
        payload = render(SurvivorSet(stage="unbuilt", notes="nothing built"))
        assert payload["result"] == "screening_only"
        assert not payload["shippable"]

    def test_framing_is_attached_to_every_payload(self):
        """The disclosure travels with the result, claims or null alike."""
        for stage in ("screening", "confirmatory", "unbuilt"):
            assert render(SurvivorSet(stage=stage))["framing"] == FRAMING


class TestClaimRendering:
    """A served claim states its own information content."""

    def test_sentence_names_the_baseline_it_beat(self):
        """A raw statistic would overstate the finding."""
        assert "birthplace and birth date" in claim_sentence(_claim())

    def test_sentence_carries_n_and_transfer_warning(self):
        """Population association is not an individual prediction."""
        sentence = claim_sentence(_claim())
        assert "2,344" in sentence
        assert "may not transfer to you" in sentence

    def test_sentence_shows_base_rate_and_lift(self):
        """"Raised the rate" is meaningless without the rate it was raised from."""
        assert "41.0%" in claim_sentence(_claim())

    def test_confirmatory_claims_are_served(self):
        """The happy path still works."""
        payload = render(SurvivorSet(claims=(_claim(),), stage="confirmatory"))
        assert payload["result"] == "claims"
        assert payload["n_claims"] == 1

    def test_calibration_table_reaches_the_payload(self):
        """A probability without its calibration is a model score in disguise."""
        claim = _claim(calibration=(CalibrationBin(0.0, 0.5, 0.30, 812),))
        payload = render(SurvivorSet(claims=(claim,), stage="confirmatory"))
        assert payload["claims"][0]["calibration"][0]["n"] == 812


class TestMarkdown:
    """The markdown surface loses nothing the JSON carries."""

    def test_null_markdown_shows_the_headline_and_the_search(self):
        """Report completeness applies to the null path too."""
        built = SurvivorSet(
            stage="confirmatory",
            tested=({"test_id": "T1", "delta": -0.01, "outcome": "tested_no_effect"},),
            controls=("sham_target",),
        )
        text = to_markdown(built)
        assert "measured result" in text
        assert "What was tested" in text
        assert "sham_target" in text

    def test_claim_markdown_includes_the_calibration_rows(self):
        """No collapsing a table to a count."""
        claim = _claim(calibration=(CalibrationBin(0.0, 0.5, 0.30, 812),))
        text = to_markdown(SurvivorSet(claims=(claim,), stage="confirmatory"))
        assert "observed rate" in text
        assert "812" in text

    def test_markdown_always_carries_the_framing(self):
        """The disclosure is not optional on the human-readable surface."""
        assert FRAMING in to_markdown(SurvivorSet(stage="confirmatory"))


class TestRoundTrip:
    """Persistence must not launder a claim past its validation."""

    def test_round_trip_preserves_a_valid_claim(self, tmp_path):
        """Write then read returns what went in."""
        path = tmp_path / "s.json"
        original = SurvivorSet(claims=(_claim(),), stage="confirmatory", corpus="c")
        write_survivors(path, original)
        assert load_survivors(path).claims[0].delta == pytest.approx(0.031)

    def test_round_trip_preserves_the_tested_record(self, tmp_path):
        """The evidence behind a null must survive persistence."""
        path = tmp_path / "s.json"
        write_survivors(path, SurvivorSet(
            stage="confirmatory",
            tested=({"test_id": "T1", "outcome": "tested_no_effect"},),
        ))
        assert len(load_survivors(path).tested) == 1
