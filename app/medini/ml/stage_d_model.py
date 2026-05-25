"""Fork-A Stage D — Dynamic-DeepHit competing-risks hazard model.

Shared MLP encoder (3 × FC(256) + BN + ReLU + Dropout) feeds 30 cause-
specific per-class hazard heads; each head outputs K_BINS=50 hazard
logits. Final softmax across all (class × bin) + 1 censored bucket
yields a joint PMF.

Loss = α · NLL + (1−α) · ranking_loss with α=0.5 (DeepHit default).

See spec §3.
"""
from __future__ import annotations

from pathlib import Path

import torch
from torch import nn

from app.medini.ml.stage_d_dataset import K_BINS as _DEFAULT_K_BINS
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

N_CLASSES = len(QUALIFYING_EVENT_CLASSES)  # 30


class _PerClassHead(nn.Module):
    def __init__(self, hidden: int = 256, k_bins: int = _DEFAULT_K_BINS) -> None:
        super().__init__()
        self.fc1 = nn.Linear(hidden, 128)
        self.act = nn.ReLU(inplace=True)
        self.fc2 = nn.Linear(128, k_bins)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc2(self.act(self.fc1(x)))


class StageDModel(nn.Module):
    def __init__(self, n_features: int, hidden: int = 256, dropout: float = 0.3,
                 k_bins: int = _DEFAULT_K_BINS) -> None:
        super().__init__()
        # k_bins captured at __init__ so a Task 19.5 sensitivity run that
        # constructs the model with a non-default value actually changes
        # the head output dimensions. Don't fall back to the imported
        # K_BINS constant inside heads — pass the value through.
        self.k_bins = k_bins
        layers = []
        in_dim = n_features
        for _ in range(3):
            layers += [
                nn.Linear(in_dim, hidden),
                nn.BatchNorm1d(hidden),
                nn.ReLU(inplace=True),
                nn.Dropout(dropout),
            ]
            in_dim = hidden
        self.encoder = nn.Sequential(*layers)
        self.heads = nn.ModuleList(
            [_PerClassHead(hidden, k_bins=k_bins) for _ in range(N_CLASSES)]
        )
        self.censored_logit = nn.Linear(hidden, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Returns PMF of shape (batch, N_CLASSES * k_bins + 1)."""
        h = self.encoder(x)
        per_class = torch.cat([head(h) for head in self.heads], dim=1)  # (b, 30*k_bins)
        cens = self.censored_logit(h)  # (b, 1)
        logits = torch.cat([per_class, cens], dim=1)  # (b, 30*k_bins + 1)
        return torch.softmax(logits, dim=1)

    # Task 13 — save/load MUST be inside the class body (the plan's
    # earlier monkey-patch approach broke @classmethod descriptor binding).
    def save(self, path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), path)

    @classmethod
    def load(cls, path, *, n_features: int, hidden: int = 256,
             dropout: float = 0.3, k_bins: int = _DEFAULT_K_BINS) -> "StageDModel":
        model = cls(n_features=n_features, hidden=hidden, dropout=dropout, k_bins=k_bins)
        model.load_state_dict(torch.load(path, map_location="cpu"))
        return model


def deephit_loss(
    pmf: torch.Tensor,
    time_bins: torch.Tensor,
    event_classes: torch.Tensor,
    *,
    k_bins: int = _DEFAULT_K_BINS,
    alpha: float = 0.5,
) -> torch.Tensor:
    """DeepHit-style: α · NLL + (1−α) · ranking loss.

    NLL = -log(prob of correct (class, bin) cell).
    Ranking = pairwise margin loss encouraging earlier-event subjects to
    have higher cumulative hazard than later-event subjects of the same class.

    `k_bins` MUST match the model's k_bins (the pmf layout depends on it).
    Callers should pass `model.k_bins`.
    """
    censored_mask = event_classes == 0

    # NLL: pick the right cell per row.
    # event_classes is 0 (censored) or 1..N_CLASSES.
    cell_idx = torch.where(
        censored_mask,
        torch.full_like(event_classes, N_CLASSES * k_bins),  # censored bucket
        (event_classes - 1) * k_bins + time_bins,
    )
    cell_prob = pmf.gather(1, cell_idx.unsqueeze(1)).squeeze(1).clamp(min=1e-10)
    nll = -torch.log(cell_prob).mean()

    # Ranking: only meaningful between non-censored pairs of same class.
    # Simplified: skip ranking for batches with <2 same-class events.
    ranking = torch.tensor(0.0, device=pmf.device)
    for cls in range(1, N_CLASSES + 1):
        cls_mask = event_classes == cls
        if cls_mask.sum() < 2:
            continue
        idx = cls_mask.nonzero(as_tuple=True)[0]
        # Cumulative hazard for class `cls` at each subject's event bin.
        start = (cls - 1) * k_bins
        cls_pmf = pmf[:, start:start + k_bins]
        cum = torch.cumsum(cls_pmf, dim=1)
        bins_i = time_bins[idx]
        cum_at_event = cum[idx, bins_i]
        # Pairs: subject with earlier event should have higher cum.
        order = torch.argsort(bins_i)
        ordered = cum_at_event[order]
        diffs = ordered[:-1] - ordered[1:]  # should be >= 0
        ranking = ranking + torch.clamp(0.1 - diffs, min=0).mean()

    return alpha * nll + (1 - alpha) * ranking
