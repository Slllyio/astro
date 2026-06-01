"""Spike B — measure RAG encode latency at N={1, 10, 50, 100, 200} to validate batching strategy."""
from __future__ import annotations
import time

print("Spike B: RAG batch-encode latency")
print("=" * 70)
print("Loading knowledge_search service (cold)...")

boot_start = time.perf_counter()
try:
    from app.medini.services.knowledge_search import get_default_service
    svc = get_default_service()
    svc.ensure_loaded()
except Exception as e:  # pragma: no cover
    print(f"  IMPORT/LOAD FAILED: {e!r}")
    raise SystemExit(1)
boot_elapsed = time.perf_counter() - boot_start
print(f"  Cold-boot: {boot_elapsed*1000:.0f}ms")
print()

queries = ["Saturn in 6th house"] * 200

print("Batch sizes vs latency:")
for n in (1, 10, 50, 100, 200):
    batch = queries[:n]
    start = time.perf_counter()
    _ = svc._model.encode(batch, normalize_embeddings=True)
    elapsed = time.perf_counter() - start
    per_q = (elapsed * 1000) / n
    print(f"  N={n:3d}: {elapsed*1000:7.0f}ms total, {per_q:6.1f}ms/query")
