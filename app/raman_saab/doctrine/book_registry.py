"""Book registry — the single source of truth mapping a citation tag to its on-disk corpus
folder, and recording each book's SCOPE.

The NATAL verdict engine is **strictly Raman, Parashari natal**. Since 2026-08-03 (user
decision) the project ALSO carries two walled non-natal subsystems — horary
(`app/raman_saab/horary/`) and electional (`app/raman_saab/electional/`) — whose sources are
live here but whose content natal rules still never cite. A book is either:
  * ``live``                      — a Raman source; its tag is CITABLE (by the subsystem whose
                                    scope it belongs to — natal books by natal rules, PRASNA/
                                    MUHURTHA by their own subsystems only).
  * ``corroboration``             — a CLASSICAL non-Raman source (BPHS, Phaladeepika) admitted
                                    2026-08-21 for the VARGA-interpretation module only. Its tag
                                    RESOLVES (click-to-source works) but it is **not natal-citable**
                                    — natal rules/yogas/significations cite ``live`` tags ONLY,
                                    a guarantee re-expressed as its own guard
                                    (`test_natal_citations_are_raman_only`) now that resolution no
                                    longer implies citability. Where Raman speaks, Raman wins;
                                    classical corroborates, it never overrides.
  * ``catalog-only-out-of-scope`` — present on disk but out of every admitted scope
                                    (annual / different systems); its tag is **NON-resolvable**.

Two predicates, deliberately split (this is the 2026-08-21 change):
  * RESOLUTION  — `_RESOLVABLE` = live + corroboration. `entry_for`/`sources._resolve_file`
                  resolve these to on-disk text, so a corroboration verse renders click-to-source.
  * NATAL-CITABILITY — `_LIVE` = live only. The divergence firewall for the strictly-Raman house
                  engine is now the natal-only citation guard, NOT "non-live ⇒ non-resolvable".
Out-of-scope / lineage tags are in neither set: unknown to `entry_for`, so still non-resolvable.
The guarantees are pinned by `tests/raman_saab/doctrine/test_book_registry.py`.

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
    status: str                 # "live" (natal-citable + resolvable) | "corroboration" (classical,
                                # resolvable but NOT natal-citable; varga module only) |
                                # "catalog-only-out-of-scope" (non-resolvable)
                                # | "lineage-catalog" (B. Suryanarain Rao shelf — Raman's
                                #   grandfather and teacher; recorded and findable, NON-citable
                                #   until rules earn them through the review gate. Where Rao and
                                #   Raman differ, Raman wins: he revised his grandfather
                                #   deliberately. SOURCE_EXPANSION_RESEARCH.md, 2026-08-08)
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
    # ASP added 2026-08-03 (user-supplied scan, Eighth Edition UBS, ISBN 978-81-85674-25-4;
    # first edition 1962). Raman's dedicated Ashtakavarga treatise — the book HPA-26's own
    # Trikona footnote defers to ("for reasons we have dealt with in our book on Ashtakavarga").
    # Unlocks the doctrine HPA only gestures at: the transit Kakshya scheme + worked 1962 table
    # (ASP-13:421-451), the bindus/8 transit-proportion law (ASP-13:265-284, 416), the 8-part
    # Kakshya-order Dasa division (ASP-12), and the Rasi-not-Bhava reckoning lock stated in the
    # first-edition preface. In-scope: natal/transit Parashari Ashtakavarga, Raman's own text.
    # OCR NOTE (fidelity): the ch.13 prose sentence listing the Kakshya order (ASP-13:424-425)
    # omits Mars IN THE PRINT ITSELF (7 names for 8 parts, a printer's slip); Raman's own
    # longitude table 18 lines later (ASP-13:443-451) carries all 8 with Mars third — the table
    # is the authority, exactly as with HPA-26's OCR-damaged worked example.
    BookEntry("ASP", "ashtakavarga_system_raman", True, "live",
              None, "Ashtakavarga System of Prediction"),
    # --- CATALOG-ONLY, OUT OF SCOPE (different systems): present, NON-citable (divergence firewall) ---
    # NOTE (2026-07-24, merge re-review): the soul-destiny experiment temporarily made JAIMINI + JS
    # `live` on its branch. RE-LOCKED at merge per the pre-registered re-review: the firewall below
    # is authoritative again; the report-only soul layer's Jaimini references remain as free-text
    # provenance (Tagged.cite) only — the corpus no longer vouches for them (its citation test
    # skips gracefully).
    # JAIMINI firewall LIFTED 2026-08-04 (explicit user decision via AskUserQuestion, the
    # karmic-evolution chapter) — the LAST firewall. Same walled-subsystem scope as
    # PRASNA/MUHURTHA/VARSHA: citable by the karmic-evolution layer only; natal verdict
    # code never imports it; the 2026-07-24 merge re-lock's CONCERN (Jaimini doctrine
    # leaking into natal verdicts) remains enforced by the content-scope rule + walls,
    # not by the registry status. Corpus re-ingested complete 2026-08-04 (filename
    # mismatch fixed — the prasna precedent); chapter numbering is OCR-artifact cosmetic.
    # Karakamsa doctrine: JAIMINI-9 (the karakamsa-combination summary block).
    BookEntry("JAIMINI", "studies_jaimini_raman", True, "live",
              None, "Studies in Jaimini Astrology (Jaimini system)"),
    # PRASNA + MUHURTHA firewall LIFTED 2026-08-03 (explicit user decision via AskUserQuestion;
    # DOCTRINE_BACKLOG "Firewall lift" record). Scope rule: horary/electional are SEPARATE
    # SUBSYSTEMS (app/raman_saab/horary/, app/raman_saab/electional/) — never imported by natal
    # verdict code; outputs carry the Measured-Truth framing. The lift also releases the
    # content-scope quarantine on horary/electional chapters inside live books (HPA-27, AFB-11,
    # ASP-15 rules 1-22) FOR THOSE SUBSYSTEMS ONLY — natal rules still never cite them.
    # PRASNA corpus note: full text re-ingested 2026-08-03 (was 5 partial chapters from a
    # filename mismatch; same 5 files, now complete). The "chapter_049" file is an OCR-artifact
    # heading label for the main Bhava-Prasna body — the number is cosmetic, citations are
    # stable. Tajika yoga definitions: PRASNA-4:1068-1330 (Ithasala/Easarapha/Naktha/Yamaya/
    # Kamboola); Deeptamsa orb table: PRASNA-2:258-270. Saham FORMULAS are NOT in this book
    # (Raman defers to his Varshaphal, PRASNA-2:288-291) — VARSHA stays firewalled, so sahams
    # are non-citable until that separate decision.
    BookEntry("PRASNA", "prasna_tantra_raman", True, "live",
              None, "Prasna Tantra (horary)"),
    # MUHURTHA corpus note: first actual ingestion 2026-08-03 (dir was empty since registration —
    # the registered archive.org item was access-restricted; repointed to the open DLI scan
    # in.ernet.dli.2015.128092, 16 chapters). Rahu Kalam weekday table, Raja/Agni/Chora
    # Panchaka, Tarabala/Chandrabala, Durmuhurtha all present.
    BookEntry("MUHURTHA", "muhurtha_raman", True, "live",
              None, "Muhurtha (electional)"),
    # VARSHA firewall LIFTED 2026-08-03 (second explicit user decision, same day as PRASNA/
    # MUHURTHA): needed because Raman's Prasna Tantra defers the Tajika machinery to his
    # Varshaphal (PRASNA-2:288-291) — the Saham formula table and the fullest yoga definitions
    # live in VARSHA-7. Citable by the walled horary/electional subsystems ONLY; natal rules
    # still never cite it. JAIMINI is now the only firewalled book.
    BookEntry("VARSHA", "varshaphal_raman", True, "live",
              None, "Varshaphal (annual)"),
    # ── registered 2026-08-08 (SOURCE_EXPANSION_RESEARCH.md — "register what is already
    # here"). PM-I/PM-II are Raman's own translation of Prasna Marga WITH HIS NOTES — the same
    # walled-horary content scope as PRASNA: citable by the horary subsystem ONLY, natal rules
    # never cite them (the wall is the import direction, tested both ways).
    BookEntry("PM1", "prasna_marga_vol1", True, "live",
              None, "Prasna Marga, Vol I (Raman's translation & notes)"),
    BookEntry("PM2", "prasna_marga_vol2", True, "live",
              None, "Prasna Marga, Vol II (Raman's translation & notes)"),
    # THE COMPLETE 3HC (user's Drive scan, Motilal Banarsidass, 350pp, 2026-08-08) — the first
    # corpus copy containing combinations 163-300; every circulating scan before it truncated
    # at 162. Canonical citation target for encoding the far half.
    BookEntry("3HCC", "three_hundred_combinations_complete", False, "live",
              "chapter_001_full-text-unsplit.md",
              "Three Hundred Important Combinations (COMPLETE, Motilal ed.)"),
    # A cleaner OCR of 3HC (user-supplied HOCR searchtext, 2026-08-08). SAME truncation as the
    # existing copies — the circulating scan family ends at combination 162 — but headings and
    # the Definition/Results/Remarks paragraphs come out on single lines, so NEW yoga encodings
    # should cite 3HCH; the 58 existing 3HC cites stay against the old file untouched.
    BookEntry("3HCH", "three_hundred_combinations_hocr", False, "live",
              "chapter_001_full-text-unsplit.md",
              "Three Hundred Important Combinations (HOCR searchtext, 1-162)"),
    # Raman's first book (1935) — natal casting mechanics; cross-checks HPA. Ordinary live scope.
    BookEntry("MANUAL", "manual_hindu_astrology_raman_1935", True, "live",
              None, "A Manual of Hindu Astrology (1935)",
              "AManualOfHinduAstrologyBVRaman1935Edition"),
    # ── the lineage shelf: B. Suryanarain Rao. Recorded, findable, NON-citable (status gates
    # them out of _LIVE, so the existing firewall tests cover them automatically). The empty
    # chappanna_prasana_sastra_row_1946 dir is NOT registered — nothing to resolve; re-import
    # first (noted in SOURCE_EXPANSION_RESEARCH.md).
    BookEntry("ROW-SELF", "astro_self_instructor_row_1893", True, "lineage-catalog",
              None, "The Astrological Self-Instructor (B. Suryanarain Rao, 1893)"),
    BookEntry("ROW-BJ", "brihat_jataka_row_1919", True, "lineage-catalog",
              None, "Brihat Jataka, Rao translation (1919)"),
    BookEntry("ROW-SC", "sarvartha_chintamani_row_1899", True, "lineage-catalog",
              None, "Sarvartha Chintamani, Rao translation (1899)"),
    BookEntry("ROW-INTRO", "intro_astrology_row_1900", True, "lineage-catalog",
              None, "Introduction to the Study of Astrology (B. Suryanarain Rao, 1900)"),
    # --- CORROBORATION: classical non-Raman, resolvable for the VARGA module, NOT natal-citable
    #     (admitted 2026-08-21; the strictly-Raman house engine keeps its own natal-only guard) ---
    BookEntry("BPHS", "bphs", True, "corroboration",
              None, "Brihat Parashara Hora Shastra (Santhanam)", "BPHSEnglish"),
    BookEntry("PHALA", "phaladeepika", False, "corroboration",
              "chapter_05_chapter-3-divisions-of-the-zodiac.md",
              "Phaladeepika ch.3 — Divisions of the Zodiac (Mantreswara)"),
)

# NATAL-CITABLE: only Raman ``live`` books may be cited by the natal verdict engine.
_LIVE: tuple[BookEntry, ...] = tuple(b for b in BOOKS if b.status == "live")
# RESOLVABLE: live + corroboration. These resolve to on-disk text (click-to-source); admitting a
# corroboration tag here does NOT make it natal-citable — that is guarded separately
# (`test_natal_citations_are_raman_only`). Out-of-scope / lineage books are in neither set.
_RESOLVABLE: tuple[BookEntry, ...] = tuple(
    b for b in BOOKS if b.status in ("live", "corroboration"))


def entry_for(work: str) -> Optional[BookEntry]:
    """The RESOLVABLE BookEntry a citation work-tag maps to, or None if the tag is unknown /
    out-of-scope. Resolution spans ``live`` + ``corroboration``; being resolvable does NOT make a
    tag natal-citable (that is `is_natal_citable` / the natal-only guard)."""
    for b in _RESOLVABLE:
        if b.multi_chapter:
            if work.startswith(b.tag + "-"):
                return b
        elif work == b.tag:
            return b
    return None


def is_natal_citable(work: str) -> bool:
    """True only if ``work`` maps to a ``live`` (Raman) book — the natal verdict engine cites
    these alone. Corroboration tags resolve but return False here; the strictly-Raman guard
    (`test_natal_citations_are_raman_only`) asserts no natal citation is anything but live."""
    entry = entry_for(work)
    return entry is not None and entry.status == "live"
