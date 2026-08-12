"""Empirical ratchet — hash guards for the tournament's commitments.

Deliberately **separate from the golden ratchet**. The golden ratchet protects
Raman textbook fidelity; this one protects the empirical program's
pre-registration, its frozen holdout, and its survivor list. They must never be
able to move each other: a change in one subsystem's numbers is not a licence to
re-baseline the other.

Follows the ``tests/raman_saab/test_astrobank_ratchet.py`` pattern:

* Artifacts that live only under gitignored ``data/`` make the test **skip
  cleanly** — CI has no corpus and must not fail for lacking one.
* A hash mismatch **skips loudly** rather than passing or failing silently. A
  baseline is re-recorded consciously, never as a side effect of a run.
* Only when hashes match are the floors asserted.

The registry itself is committed, so its checks always run.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.empirical.tournament.prereg import (
    MANDATORY_CONTROL_ARMS,
    Status,
    load_registry,
    registry_fingerprint,
    scorable,
)

_REGISTRY = Path("tools/empirical/prereg.csv")
_BASELINE = Path("tools/empirical/empirical_baseline.json")
_HOLDOUT_MANIFEST = Path("data/empirical/holdout_manifest.json")
_SURVIVORS = Path("data/empirical/survivors.json")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestRegistryIntegrity:
    """The pre-registration is committed, so these always run."""

    def test_registry_parses(self):
        """A malformed registry must break the build, not a later run."""
        assert load_registry(_REGISTRY)

    def test_every_locked_row_carries_the_mandatory_arms(self):
        """Locking without the full control set is refused at write time.

        Re-asserted here because a hand-edit to the CSV bypasses the API that
        normally enforces it.
        """
        for reg in load_registry(_REGISTRY):
            if reg.status is Status.LOCKED:
                missing = MANDATORY_CONTROL_ARMS - set(reg.control_arms)
                assert not missing, f"{reg.test_id} locked without {sorted(missing)}"

    def test_every_chart_bank_names_a_chartless_baseline(self):
        """A chart bank with no twin has nothing to be scored against."""
        for reg in load_registry(_REGISTRY):
            if reg.feature_bank != "chartless":
                assert reg.baseline_model.strip(), f"{reg.test_id} has no baseline_model"

    def test_baseline_ids_resolve(self):
        """A baseline_model must point at a row that exists."""
        registry = load_registry(_REGISTRY)
        ids = {r.test_id for r in registry}
        for reg in registry:
            if reg.baseline_model:
                assert reg.baseline_model in ids, (
                    f"{reg.test_id} names baseline {reg.baseline_model!r}, which is not a row"
                )

    def test_baseline_rows_are_the_chartless_bank(self):
        """Being scored against another chart bank would prove nothing."""
        registry = load_registry(_REGISTRY)
        by_id = {r.test_id: r for r in registry}
        for reg in registry:
            if reg.baseline_model:
                assert by_id[reg.baseline_model].feature_bank == "chartless"


class TestRegistryRatchet:
    """Once a row locks, the registry's hash is evidence."""

    def test_registry_hash_matches_baseline_when_recorded(self):
        """A registry edited after locking must be detectable.

        Skips until a baseline is consciously recorded — there is nothing to
        ratchet against while every row is still a draft.
        """
        if not _BASELINE.is_file():
            pytest.skip("no empirical_baseline.json recorded yet — nothing locked")
        baseline = json.loads(_BASELINE.read_text(encoding="utf-8"))
        recorded = baseline.get("registry_sha256")
        if recorded is None:
            pytest.skip("baseline records no registry hash")
        assert recorded == registry_fingerprint(_REGISTRY), (
            "PREREG CHANGED vs baseline. If this was intentional, re-record the baseline "
            "consciously — never let a scoring run silently ratchet onto an edited registry."
        )

    def test_locked_row_count_never_decreases(self):
        """Rows can be added and retired, but a lock is not quietly undone."""
        if not _BASELINE.is_file():
            pytest.skip("no empirical_baseline.json recorded yet")
        baseline = json.loads(_BASELINE.read_text(encoding="utf-8"))
        floor = baseline.get("n_locked")
        if floor is None:
            pytest.skip("baseline records no locked-row floor")
        assert len(scorable(load_registry(_REGISTRY))) >= floor


class TestHoldoutRatchet:
    """The frozen split is a commitment; corpus drift under it is detectable."""

    def test_holdout_manifest_matches_baseline(self):
        """A re-rolled holdout invalidates every confirmatory result taken on it."""
        if not _HOLDOUT_MANIFEST.is_file():
            pytest.skip("holdout manifest absent (local-only, gitignored)")
        if not _BASELINE.is_file():
            pytest.skip("no empirical_baseline.json recorded yet")
        baseline = json.loads(_BASELINE.read_text(encoding="utf-8"))
        recorded = baseline.get("holdout_manifest_sha256")
        if recorded is None:
            pytest.skip("baseline records no holdout hash")
        assert recorded == _sha(_HOLDOUT_MANIFEST), (
            "HOLDOUT CHANGED vs baseline — the frozen split moved. Confirmatory results "
            "taken against the old split do not transfer; re-register before re-running."
        )


class TestSurvivorsRatchet:
    """Shipped claims may not appear without having cleared the gates."""

    def test_survivors_file_matches_baseline(self):
        """The shipped claim set is hash-pinned like any other artifact."""
        if not _SURVIVORS.is_file():
            pytest.skip("survivors.json absent — nothing has been confirmed yet")
        if not _BASELINE.is_file():
            pytest.skip("no empirical_baseline.json recorded yet")
        baseline = json.loads(_BASELINE.read_text(encoding="utf-8"))
        recorded = baseline.get("survivors_sha256")
        if recorded is None:
            pytest.skip("baseline records no survivors hash")
        assert recorded == _sha(_SURVIVORS)

    def test_every_survivor_traces_to_a_locked_confirmatory_row(self):
        """A claim that was never registered, or never locked, cannot ship.

        The empty-survivor case passes trivially and is the expected outcome —
        an engine with no claims is a designed result, not a failure.
        """
        if not _SURVIVORS.is_file():
            pytest.skip("survivors.json absent — nothing has been confirmed yet")
        survivors = json.loads(_SURVIVORS.read_text(encoding="utf-8")).get("survivors", [])
        confirmatory = {
            r.test_id for r in scorable(load_registry(_REGISTRY), stage="confirmatory")
        }
        for claim in survivors:
            assert claim["test_id"] in confirmatory, (
                f"survivor {claim['test_id']} has no locked confirmatory registration"
            )

    def test_every_survivor_beat_its_chartless_twin(self):
        """A shipped claim must carry a positive delta, not a raw statistic."""
        if not _SURVIVORS.is_file():
            pytest.skip("survivors.json absent — nothing has been confirmed yet")
        survivors = json.loads(_SURVIVORS.read_text(encoding="utf-8")).get("survivors", [])
        for claim in survivors:
            assert claim["delta"] > 0.0, f"{claim['test_id']} shipped with delta {claim['delta']}"


class TestSubsystemSeparation:
    """The two ratchets must not be able to move each other."""

    def test_empirical_baseline_is_not_the_golden_baseline(self):
        """Distinct files, so re-recording one cannot touch the other."""
        golden = Path("tests/fixtures/golden_accuracy_baseline.json")
        assert _BASELINE != golden

    def test_ratchet_does_not_import_raman_doctrine(self):
        """This test module must not be able to perturb the golden ratchet.

        Parsed, not grepped: the module discusses the Raman subsystem by name in
        its own prose, and a substring check would match its own assertion.
        """
        import ast

        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"), filename=__file__)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not any(name.startswith("app.raman_saab") for name in imported)
