"""Tests for Fork-A Stage D Dynamic-DeepHit model."""
from __future__ import annotations

import pytest

pytest.importorskip("torch")  # Stage-D heavy dep — see requirements-stage-d.txt

import torch
import pytest

from app.medini.ml.stage_d_model import StageDModel


class TestStageDModel:
    def test_forward_pass_shape(self) -> None:
        """Output is PMF over (30 classes × 50 bins + 1 censored) = 1501 logits."""
        model = StageDModel(n_features=300)
        x = torch.randn(8, 300)  # batch of 8 (BatchNorm requires >1)
        out = model(x)
        assert out.shape == (8, 30 * 50 + 1)

    def test_forward_pmf_normalized(self) -> None:
        """Output rows sum to 1 (it's a PMF after softmax)."""
        model = StageDModel(n_features=300)
        model.eval()
        x = torch.randn(8, 300)
        out = model(x)
        row_sums = out.sum(dim=1)
        assert torch.allclose(row_sums, torch.ones(8), atol=1e-5)

    def test_loss_finite_on_random_inputs(self) -> None:
        """F9 catch — loss is finite on 100 random samples."""
        from app.medini.ml.stage_d_model import deephit_loss

        torch.manual_seed(42)
        model = StageDModel(n_features=300)
        x = torch.randn(100, 300)
        time_bins = torch.randint(0, 50, (100,))
        event_classes = torch.randint(0, 31, (100,))  # 0 = censored, 1..30 = class
        pmf = model(x)
        loss = deephit_loss(pmf, time_bins, event_classes, k_bins=model.k_bins)
        assert torch.isfinite(loss).item()


class TestSaveLoad:
    def test_round_trip_identical(self, tmp_path) -> None:
        """Save + load + forward = bit-identical output (Task 13)."""
        torch.manual_seed(7)
        model = StageDModel(n_features=128)
        model.eval()
        # Use batch>1 to satisfy BatchNorm1d expectations even in eval mode
        # (eval bypasses running-stats but the path still allocates buffers).
        x = torch.randn(4, 128)
        out_before = model(x)

        save_path = tmp_path / "model.pt"
        model.save(save_path)
        loaded = StageDModel.load(save_path, n_features=128)
        loaded.eval()
        out_after = loaded(x)
        assert torch.equal(out_before, out_after)
