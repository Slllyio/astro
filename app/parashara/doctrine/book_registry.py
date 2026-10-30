"""Book registry for the Parashara engine — BPHS is the ROOT authority.

This is the deliberate mirror image of `app/raman_saab/doctrine/book_registry.py`. There, Raman's
books are `live` and BPHS is `corroboration`. **Here BPHS is `live`/root and everyone else —
including Raman — is at most corroboration.** Same machinery, inverted authority; that inversion
is the reason the two engines exist separately.

A book is one of:
  * ``root``          — BPHS itself. Parashara's own words. Where root and any other source
                        disagree, **root wins**, always, without argument.
  * ``allied``        — the classical Parashari lineage that transmits and elaborates BPHS
                        (Phaladeepika, Saravali, Brihat Jataka, Jataka Parijata, Hora Sara,
                        Uttara Kalamrita). CITABLE, but only where BPHS is silent or ambiguous —
                        never to overturn a root sloka.
  * ``corroboration`` — outside the Parashari root lineage but useful as agreement evidence
                        (notably Raman's own books: he follows Parashara closely, so his
                        agreement is real corroboration — but he is NOT the authority here).
  * ``out-of-scope``  — a different system entirely (KP, Tajika, western). NON-resolvable.

Three predicates, deliberately distinct (the lesson learned in the raman_saab registry, where
conflating "resolves" with "may be cited" made a firewall change risky):
  * ``entry_for``          — resolution: root + allied + corroboration resolve to on-disk text.
  * ``is_citable``         — a doctrine rule may cite root + allied.
  * ``is_root``            — only BPHS. A rule that CONTRADICTS a root sloka is a defect,
                             whatever else corroborates it.

Citation-tag convention (identical to the raman_saab engine, so the shared `sources` machinery
works unchanged):
  * multi-chapter book:  ``TAG-CH:line``   e.g. ``BPHS-7:220`` -> bphs/chapter_007_*.md line 220
  * single-file book:    ``TAG:line``
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

#: Status values. `root` is a set of exactly one book by construction — if a second book ever
#: claims root, the engine has lost its authority model.
ROOT: Final[str] = "root"
ALLIED: Final[str] = "allied"
CORROBORATION: Final[str] = "corroboration"
OUT_OF_SCOPE: Final[str] = "out-of-scope"

_STATUSES: Final[frozenset[str]] = frozenset({ROOT, ALLIED, CORROBORATION, OUT_OF_SCOPE})


@dataclass(frozen=True)
class BookEntry:
    tag: str                  # citation prefix: exact tag, or the stem before '-CH'
    slug: str                 # folder under data/knowledge_library/sources/
    multi_chapter: bool       # True -> 'TAG-CH:line' resolves chapter_{CH:03d}_*.md
    status: str               # root | allied | corroboration | out-of-scope
    title: str = ""
    fixed_file: Optional[str] = None   # single-file books: exact filename
    note: str = ""


BOOKS: Final[tuple[BookEntry, ...]] = (
    # --- ROOT: Parashara's own text. The authority. ---
    BookEntry("BPHS", "bphs", True, ROOT,
              "Brihat Parashara Hora Shastra (R. Santhanam)",
              note="92 of 97 chapters on disk; ch.1-45 complete, ch.46-97 has 47 of 52 "
                   "(ch.75 split out of the ch.74 file, 2026-08-24). "
                   "Per-chapter record: docs/parashara/BPHS_CORPUS_COVERAGE.md"),

    # --- ALLIED: the classical Parashari lineage. Citable where BPHS is silent. ---
    BookEntry("PHALA", "phaladeepika", True, ALLIED,
              "Phaladeepika (Mantreswara, tr. V. Subrahmanya Sastri)",
              note="INCOMPLETE — only ONE chapter is on disk: the printed ch.3 'Divisions of the "
                   "Zodiac' (chapter_05_*.md). The rest was never scraped, so Phaladeepika is NOT "
                   "generally citable through the engine and is not cited anywhere today. "
                   "NUMBERING TRAP for the one file present: the wisdomlib scrape counted "
                   "front-matter, so printed ch.3 is chapter_05_*.md — cite it as PHALA-5, not "
                   "PHALA-3. Always confirm the file a tag resolves to before pinning a line."),
    BookEntry("SARAVALI", "saravali", True, ALLIED,
              "Saravali (Kalyana Varma, tr. R. Santhanam)",
              note="Complete, 55 chapters."),
    BookEntry("BJ", "brihat_jataka", True, ALLIED,
              "Brihat Jataka (Varahamihira, tr. Swami Vijnananda)"),
    BookEntry("JP", "jataka_parijata", True, ALLIED,
              "Jataka Parijata (Vaidyanatha Dikshita)"),
    BookEntry("UK", "uttara_kalamrita", True, ALLIED,
              "Uttara Kalamrita (Kalidasa)", note="Complete, 8 khandas."),
    BookEntry("HORASARA", "hora_sara_santhanam", True, ALLIED,
              "Hora Sara (Prithuyasas, tr. R. Santhanam)"),
    BookEntry("JAIMINI", "jaimini_sutras", True, ALLIED,
              "Jaimini Sutras (tr. and notes B. Suryanarain Rao)",
              note="Only five chapter files on disk (pada 2, pada 4 and three mis-titled splits). Cited "
                   "for chara dasha conventions where BPHS-46 is silent or ambiguous "
                   "(docs/parashara/CHARA_DASHA_RULINGS.md); most of what it says there is the "
                   "translator's NOTES, not sutra text."),

    # --- CORROBORATION: agreement evidence, never authority. ---
    # Raman follows Parashara closely, so his agreement is genuine corroboration for a BPHS
    # reading — but in THIS engine he cannot settle a question. Where Raman revised Parashara
    # (he did, deliberately), the divergence is recorded, and BPHS wins.
    BookEntry("HPA", "hindu_predictive_astrology_raman", True, CORROBORATION,
              "Hindu Predictive Astrology (B. V. Raman)"),
    BookEntry("HTJAH-I", "how_to_judge_a_horoscope_raman", False, CORROBORATION,
              "How to Judge a Horoscope, Vol I (B. V. Raman)",
              fixed_file="chapter_001_full-text-unsplit.md"),
    BookEntry("HTJAH-II", "how_to_judge_horoscope_raman2", False, CORROBORATION,
              "How to Judge a Horoscope, Vol II (B. V. Raman)",
              fixed_file="chapter_001_full-text-unsplit.md"),
    BookEntry("SJ", "studies_jaimini_raman", True, CORROBORATION,
              "Studies in Jaimini Astrology (B. V. Raman)"),
)

#: Resolution set — these tags resolve to on-disk text (click-to-source works).
_RESOLVABLE: Final[tuple[BookEntry, ...]] = tuple(
    b for b in BOOKS if b.status in (ROOT, ALLIED, CORROBORATION))
#: Citation set — a doctrine rule may cite these.
_CITABLE: Final[frozenset[str]] = frozenset({ROOT, ALLIED})


def entry_for(work: str) -> Optional[BookEntry]:
    """The resolvable BookEntry a citation work-tag maps to, or None.

    Resolution spans root + allied + corroboration. Being resolvable does NOT make a tag citable
    (see `is_citable`) and certainly does not make it authoritative (see `is_root`).
    """
    for b in _RESOLVABLE:
        if b.multi_chapter:
            if work.startswith(b.tag + "-"):
                return b
        elif work == b.tag:
            return b
    return None


def is_citable(work: str) -> bool:
    """True if a Parashara doctrine rule may carry this tag — root or allied lineage only.

    Corroboration tags (Raman) resolve for display but must never be a rule's authority.
    """
    entry = entry_for(work)
    return entry is not None and entry.status in _CITABLE


def is_root(work: str) -> bool:
    """True only for BPHS — Parashara's own words, which outrank everything else in this engine."""
    entry = entry_for(work)
    return entry is not None and entry.status == ROOT


def status_of(work: str) -> Optional[str]:
    """The registry status behind a tag, or None if the tag is unknown/out-of-scope."""
    entry = entry_for(work)
    return entry.status if entry else None
