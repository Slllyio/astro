"""Book registry — the single source of truth mapping a citation tag to its on-disk corpus
folder, and recording each book's SCOPE.

The NATAL verdict engine is **strictly Raman, Parashari natal**. Since 2026-08-03 (user
decision) the project ALSO carries two walled non-natal subsystems — horary
(`app/raman_saab/horary/`) and electional (`app/raman_saab/electional/`) — whose sources are
live here but whose content natal rules still never cite. A book is either:
  * ``live``                      — a Raman source; its tag is CITABLE (by the subsystem whose
                                    scope it belongs to — natal books by natal rules, PRASNA/
                                    MUHURTHA by their own subsystems only).
  * ``catalog-only-out-of-scope`` — present on disk but out of every admitted scope
                                    (Jaimini / annual); its tag is **NON-citable**.

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
    BookEntry("JAIMINI", "studies_jaimini_raman", True, "catalog-only-out-of-scope",
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
