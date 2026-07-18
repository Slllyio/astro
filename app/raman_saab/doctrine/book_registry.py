"""Book registry — the single source of truth mapping a citation tag to its on-disk corpus
folder, and recording each book's SCOPE.

The raman_saab engine is **strictly Raman, Parashari natal**. A book is either:
  * ``live``                      — a Parashari-natal Raman source; its tag is CITABLE.
  * ``catalog-only-out-of-scope`` — present on disk but a DIFFERENT system (Jaimini / horary /
                                    electional / annual); its tag is **NON-citable**.

The non-citable rule is the divergence firewall: `sources._resolve_file` consults this registry
and returns None for any non-live tag, so no rule can ever cite an out-of-scope book. The
guarantee is pinned by `tests/raman_saab/doctrine/test_book_registry.py`.

Citation-tag convention (see `sources` + `00_method_overview`):
  * single-file legacy book:  ``TAG:line``        (e.g. HTJAH-I:1586)
  * multi-chapter book:       ``TAG-CH:line``     (e.g. HPA-20:65 -> chapter_020_*.md)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BookEntry:
    tag: str                    # citation prefix: exact tag (single-file) or stem before '-CH'
    slug: str                   # folder under data/knowledge_library/sources/
    multi_chapter: bool         # True -> 'TAG-CH:line' resolves chapter_{CH:03d}_*.md
    status: str                 # "live" (citable) | "catalog-only-out-of-scope" (non-citable)
    fixed_file: Optional[str] = None   # single-file books: exact filename; None -> first *.md
    title: str = ""
    archive_identifier: str = ""        # provenance (for re-import)


# The whole Raman corpus the project recognises. Order is the resolution order.
BOOKS: tuple[BookEntry, ...] = (
    # --- LIVE: Parashari-natal Raman, citable ---
    BookEntry("HTJAH-I", "how_to_judge_a_horoscope_raman", False, "live",
              "chapter_001_full-text-unsplit.md", "How to Judge a Horoscope, Vol I",
              "how-to-judge-a-horoscope-r.-santhanam"),
    BookEntry("HTJAH-II", "how_to_judge_horoscope_raman2", False, "live",
              "chapter_001_full-text-unsplit.md", "How to Judge a Horoscope, Vol II"),
    BookEntry("3HC", "three_hundred_combinations_raman", False, "live",
              None, "Three Hundred Important Combinations"),
    BookEntry("HPA", "hindu_predictive_astrology_raman", True, "live",
              None, "Hindu Predictive Astrology"),
    BookEntry("GBB", "graha_bhava_balas_raman", True, "live",
              None, "Graha and Bhava Balas"),
    BookEntry("NH", "notable_horoscopes_raman", False, "live",
              "chapter_001_full-text-unsplit.md", "Notable Horoscopes", "NotableHoroscopesBVR"),
    # AFB added 2026-07-18 (rectification module P1): Raman's own Parashari-natal primer.
    # Its ch.9-10 event->dasha-lord lists (marriage AFB-9:98, children AFB-9:142, the
    # per-lord Dasa menu AFB-10:449-476) are the corpus's sharpest event-timing statements
    # and anchor the rectification EVENT_TAXONOMY. In-scope: natal, Parashari, Raman.
    # (Its ch.11 horary / ch.12 gochara chapters are simply never cited — the tag being
    # live does not admit out-of-scope CONTENT; rules cite specific lines.)
    BookEntry("AFB", "astrology_for_beginners_raman", True, "live",
              None, "Astrology for Beginners", "AstrologyForBeginners_201705"),
    # --- CATALOG-ONLY, OUT OF SCOPE (different systems): present, NON-citable (divergence firewall) ---
    BookEntry("JAIMINI", "studies_jaimini_raman", True, "catalog-only-out-of-scope",
              None, "Studies in Jaimini Astrology (Jaimini system)"),
    BookEntry("PRASNA", "prasna_tantra_raman", True, "catalog-only-out-of-scope",
              None, "Prasna Tantra (horary)"),
    BookEntry("MUHURTHA", "muhurtha_raman", True, "catalog-only-out-of-scope",
              None, "Muhurtha (electional)"),
    BookEntry("VARSHA", "varshaphal_raman", True, "catalog-only-out-of-scope",
              None, "Varshaphal (annual)"),
)

_LIVE: tuple[BookEntry, ...] = tuple(b for b in BOOKS if b.status == "live")


def entry_for(work: str) -> Optional[BookEntry]:
    """The LIVE BookEntry a citation work-tag maps to, or None if the tag is unknown OR
    out-of-scope. Out-of-scope tags never match -> they are NON-citable (the firewall)."""
    for b in _LIVE:
        if b.multi_chapter:
            if work.startswith(b.tag + "-"):
                return b
        elif work == b.tag:
            return b
    return None
