"""Unit tests for app.medini.ml.retag_rag_chunks.

Builds tiny synthetic manifest + chunks parquets in a tmp dir, runs the
retag, verifies the topics column is updated without touching vectors.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.medini.ml.retag_rag_chunks import retag


@pytest.fixture
def tmp_index(tmp_path: Path) -> tuple[Path, Path]:
    """Fresh manifest + chunks parquet pair on disk."""
    manifest_path = tmp_path / "manifest.parquet"
    chunks_path = tmp_path / "chunks.parquet"

    # Two artefacts in the manifest. Artefact "a" has 2 topics; "b" has 1.
    manifest = pd.DataFrame([
        {"id": "art-a", "source": "bphs", "title": "A",
         "topics": np.array(["dasha.vimshottari", "primitives.planets"], dtype=object)},
        {"id": "art-b", "source": "phaladeepika", "title": "B",
         "topics": np.array(["yogas.raja_yogas"], dtype=object)},
    ])
    manifest.to_parquet(manifest_path, index=False)

    # Three chunks: 2 from artefact a (different chunk_idx), 1 from b.
    # Chunks' existing topics are STALE (older tag set) — the retag should
    # bring them in sync with the manifest.
    chunks = pd.DataFrame([
        {"chunk_id": "art-a#0", "artefact_id": "art-a", "chunk_idx": 0,
         "text": "x", "topics": np.array(["meta.source_texts"], dtype=object)},
        {"chunk_id": "art-a#1", "artefact_id": "art-a", "chunk_idx": 1,
         "text": "y", "topics": np.array(["meta.source_texts"], dtype=object)},
        {"chunk_id": "art-b#0", "artefact_id": "art-b", "chunk_idx": 0,
         "text": "z", "topics": np.array(["yogas.raja_yogas"], dtype=object)},
    ])
    chunks.to_parquet(chunks_path, index=False)
    return manifest_path, chunks_path


class TestRetag:
    def test_dry_run_reports_deltas_without_writing(
        self, tmp_index: tuple[Path, Path],
    ) -> None:
        """Dry-run must not touch the file — clients can preview the impact
        before committing the change."""
        manifest, chunks = tmp_index
        before = pd.read_parquet(chunks).copy()
        stats = retag(manifest, chunks, dry_run=True)
        assert stats["dry_run"] == 1
        after = pd.read_parquet(chunks)
        # Compare topics column element-wise — list equality
        for a, b in zip(before["topics"], after["topics"]):
            assert list(a) == list(b)

    def test_retag_updates_stale_chunks(
        self, tmp_index: tuple[Path, Path],
    ) -> None:
        """Both art-a chunks should switch to the manifest's [dasha.vimshottari,
        primitives.planets] tag set; art-b stays unchanged."""
        manifest, chunks = tmp_index
        stats = retag(manifest, chunks)
        assert stats["dry_run"] == 0
        assert stats["n_changed"] == 2  # both art-a chunks were stale
        after = pd.read_parquet(chunks)
        a_chunks = after[after["artefact_id"] == "art-a"]
        for _, row in a_chunks.iterrows():
            assert set(row["topics"]) == {"dasha.vimshottari", "primitives.planets"}
        b_chunk = after[after["artefact_id"] == "art-b"].iloc[0]
        assert set(b_chunk["topics"]) == {"yogas.raja_yogas"}

    def test_chunk_count_unchanged(
        self, tmp_index: tuple[Path, Path],
    ) -> None:
        """Retag must NEVER add/remove rows — only update one column."""
        manifest, chunks = tmp_index
        before_n = len(pd.read_parquet(chunks))
        retag(manifest, chunks)
        after_n = len(pd.read_parquet(chunks))
        assert before_n == after_n

    def test_chunks_for_unknown_artefact_preserved(
        self, tmp_path: Path,
    ) -> None:
        """If a chunk's artefact_id isn't in the manifest, keep its existing
        topics rather than clobbering — defends against accidental data
        loss during an in-progress manifest rebuild."""
        manifest_path = tmp_path / "manifest.parquet"
        chunks_path = tmp_path / "chunks.parquet"
        pd.DataFrame([
            {"id": "art-known", "source": "bphs", "title": "k",
             "topics": np.array(["dasha.vimshottari"], dtype=object)},
        ]).to_parquet(manifest_path, index=False)
        pd.DataFrame([
            {"chunk_id": "art-orphan#0", "artefact_id": "art-orphan",
             "chunk_idx": 0, "text": "x",
             "topics": np.array(["yogas.raja_yogas"], dtype=object)},
        ]).to_parquet(chunks_path, index=False)
        retag(manifest_path, chunks_path)
        after = pd.read_parquet(chunks_path)
        assert list(after.iloc[0]["topics"]) == ["yogas.raja_yogas"]
