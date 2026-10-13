"""Pre-registration: only locked rows score, and locking demands the control arms.

These tests exist because every rule they check is one that discipline alone has
already failed to enforce somewhere in this project's history.
"""

from __future__ import annotations

import pytest

from app.empirical.tournament.prereg import (
    MANDATORY_CONTROL_ARMS,
    Registration,
    RegistrationError,
    Status,
    load_registry,
    lock,
    registry_fingerprint,
    scorable,
    validate,
    write_registry,
)

_ARMS = tuple(sorted(MANDATORY_CONTROL_ARMS))


def _reg(**overrides) -> Registration:
    base = dict(
        test_id="T001",
        feature_bank="western",
        target="marriage",
        statistic="auc",
        baseline_model="chartless_v1",
        control_arms=_ARMS,
        min_n=500,
        tier_requirement="A",
        stage="screening",
        direction="greater",
        status=Status.DRAFT,
        notes="",
    )
    base.update(overrides)
    return Registration(**base)


class TestValidation:
    """Malformed rows must fail loudly at load, not silently at scoring."""

    def test_valid_row_passes(self):
        """The happy path."""
        validate(_reg())

    def test_unknown_feature_bank_rejected(self):
        """Only the four declared banks exist."""
        with pytest.raises(RegistrationError, match="feature_bank"):
            validate(_reg(feature_bank="astrology_vibes"))

    def test_unknown_statistic_rejected(self):
        """The statistic is registered in advance, not chosen after the fact."""
        with pytest.raises(RegistrationError, match="statistic"):
            validate(_reg(statistic="whatever_looks_best"))

    def test_direction_must_be_registered(self):
        """Registering the direction stops a negative result being reread as positive."""
        with pytest.raises(RegistrationError, match="direction"):
            validate(_reg(direction="either"))

    def test_nonpositive_min_n_rejected(self):
        """A test with no sample floor has no floor to fall through."""
        with pytest.raises(RegistrationError, match="min_n"):
            validate(_reg(min_n=0))

    def test_unknown_control_arm_rejected(self):
        """Arms are a closed vocabulary; a typo must not silently disable a control."""
        with pytest.raises(RegistrationError, match="unknown control arms"):
            validate(_reg(control_arms=_ARMS + ("sham_targt",)))

    def test_unknown_tier_rejected(self):
        """Birth-time tiers are a fixed ladder."""
        with pytest.raises(RegistrationError, match="tier_requirement"):
            validate(_reg(tier_requirement="whenever"))


class TestLocking:
    """Locking is the moment a row becomes evidence."""

    def test_cannot_lock_without_mandatory_arms(self):
        """A test missing its sham gate is not a test."""
        partial = _reg(control_arms=("sham_target",))
        with pytest.raises(RegistrationError, match="mandatory control arms"):
            lock((partial,), "T001")

    def test_missing_arm_named_in_the_error(self):
        """The message must say which arm, or the fix is guesswork."""
        partial = _reg(control_arms=tuple(a for a in _ARMS if a != "chartless_baseline"))
        with pytest.raises(RegistrationError, match="chartless_baseline"):
            lock((partial,), "T001")

    def test_chart_bank_must_name_a_chartless_baseline(self):
        """A chart bank scored against nothing has beaten nothing."""
        with pytest.raises(RegistrationError, match="chartless baseline"):
            lock((_reg(baseline_model="  "),), "T001")

    def test_chartless_bank_needs_no_baseline(self):
        """The baseline itself is exempt — it is what others are scored against."""
        row = _reg(feature_bank="chartless", baseline_model="")
        locked = lock((row,), "T001")
        assert locked[0].status is Status.LOCKED

    def test_locking_is_idempotent_guarded(self):
        """Re-locking is an error, not a no-op — it usually means a stale script."""
        locked = lock((_reg(),), "T001")
        with pytest.raises(RegistrationError, match="already locked"):
            lock(locked, "T001")

    def test_unknown_test_id_rejected(self):
        """Locking something that does not exist is a typo worth surfacing."""
        with pytest.raises(RegistrationError, match="no such test_id"):
            lock((_reg(),), "T999")

    def test_lock_leaves_other_rows_untouched(self):
        """Locking one row must not disturb its neighbours."""
        rows = (_reg(test_id="T001"), _reg(test_id="T002"))
        locked = lock(rows, "T001")
        assert {r.test_id: r.status for r in locked} == {
            "T001": Status.LOCKED,
            "T002": Status.DRAFT,
        }


class TestScorable:
    """The only sanctioned route from registry to scoring."""

    def test_draft_rows_are_not_scorable(self):
        """A draft can still be edited, so it cannot be evidence."""
        assert scorable((_reg(status=Status.DRAFT),)) == ()

    def test_retired_rows_are_not_scorable(self):
        """Retirement removes a row from the family."""
        assert scorable((_reg(status=Status.RETIRED),)) == ()

    def test_locked_rows_are_scorable(self):
        """Locked is the one scorable state."""
        assert len(scorable((_reg(status=Status.LOCKED),))) == 1

    def test_stage_filter(self):
        """Screening and confirmatory are scored in separate passes."""
        rows = (
            _reg(test_id="T001", status=Status.LOCKED, stage="screening"),
            _reg(test_id="T002", status=Status.LOCKED, stage="confirmatory"),
        )
        assert [r.test_id for r in scorable(rows, stage="confirmatory")] == ["T002"]

    def test_unknown_stage_rejected(self):
        """A typo'd stage must not silently return an empty family."""
        with pytest.raises(RegistrationError, match="unknown stage"):
            scorable((_reg(),), stage="screenning")


class TestRoundTripAndFingerprint:
    """The registry is content-addressed, so its bytes must be stable."""

    def test_round_trip_preserves_rows(self, tmp_path):
        """Write then read must return what went in."""
        rows = (_reg(test_id="T001"), _reg(test_id="T002", feature_bank="vedic_timing"))
        path = tmp_path / "prereg.csv"
        write_registry(path, rows)
        assert load_registry(path) == tuple(sorted(rows, key=lambda r: r.test_id))

    def test_fingerprint_is_order_independent(self, tmp_path):
        """Appending rows in a different order must not change the hash."""
        rows = (_reg(test_id="T001"), _reg(test_id="T002"))
        a, b = tmp_path / "a.csv", tmp_path / "b.csv"
        write_registry(a, rows)
        write_registry(b, tuple(reversed(rows)))
        assert registry_fingerprint(a) == registry_fingerprint(b)

    def test_fingerprint_changes_when_a_row_changes(self, tmp_path):
        """An edit after locking must be detectable."""
        path = tmp_path / "prereg.csv"
        write_registry(path, (_reg(min_n=500),))
        before = registry_fingerprint(path)
        write_registry(path, (_reg(min_n=400),))
        assert registry_fingerprint(path) != before

    def test_duplicate_test_id_rejected(self, tmp_path):
        """Two rows with one id makes the family ambiguous."""
        path = tmp_path / "prereg.csv"
        write_registry(path, (_reg(test_id="T001"),))
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"T001,western,marriage,auc,chartless_v1,{'|'.join(_ARMS)},500,A,screening,greater,draft,\n")
        with pytest.raises(RegistrationError, match="duplicate"):
            load_registry(path)
