"""Phase 1 — corpus acquisition.

Sources are fetched once, cached under ``data/empirical/raw/``, and carry their
provenance into every row. Birth-time quality is recorded honestly per record
rather than assumed from the source's reputation: a registry-sourced corpus still
contains clerically-rounded times, and those cannot evidence a transit.

Modules:
  gauquelin_import  the CURA-published Gauquelin series A (professional
                    notabilities) — registry-timed births with profession labels
"""

from __future__ import annotations

__all__ = ["gauquelin_import"]
