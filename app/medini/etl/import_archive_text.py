"""Generic archive.org djvu-text importer for classical Jyotisha books.

archive.org hosts hundreds of public-domain classical texts as OCR'd
``*_djvu.txt`` files. This script generalises the BPHS importer to handle
any of them — Jataka Parijata, Saravali, Brihat Jataka, Jaimini Sutras,
Uttara Kalamrita, Sripatipaddhati, Bhrigu Samhita, Sarvartha Chintamani,
etc.

Usage:
    # Single book
    python -m app.medini.etl.import_archive_text \\
        --identifier JatakaParijataVolIOfIIByVSubrahmanyaSastri \\
        --filename "Jataka Parijata Vol I of II by V Subrahmanya Sastri_djvu.txt" \\
        --book-slug jataka_parijata \\
        --book-title "Jataka Parijata" \\
        --author "Vaidyanatha Dikshita" \\
        --translator "V. Subrahmanya Sastri" \\
        --classical-ref-prefix JatakaParijata

    # Or run the whole bundled set:
    python -m app.medini.etl.import_archive_text --bundle classical_jyotisha

The script:
  1. Downloads the djvu.txt from archive.org.
  2. Splits by chapter using the configured regex pattern (chapter,
     adhyaya, sutra-pada, sloka-group, etc.).
  3. De-duplicates overlapping chapter headers (TOC vs body).
  4. Drops segments under min-words (likely OCR junk).
  5. Saves one markdown per chapter with frontmatter to
     ``data/knowledge_library/sources/<book_slug>/``.
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Pattern
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}

# Common chapter-header patterns in OCR'd Jyotisha texts. The default is
# permissive enough to catch BPHS, Phaladeepika-style, Jataka Parijata, etc.
# Override per-book via --header-regex when the canonical text uses something
# different (e.g. "Sutra X.Y" for Jaimini, "Verse N" for Brihat Jataka).

# Combined chapter-header regex that matches:
#   "Chapter N"          (arabic numerals)
#   "Chapter VII"        (roman numerals - many older OCR'd texts)
#   "Adhyaya N"
#   "CHAPTER I.-Title"   (with optional " - <title>" tail)
# Roman numerals match {I, II, III, IV, V, VI, VII, VIII, IX, X, XI, ..., XXXIX, XL, ...}
# We accept up to LIX (59) which covers all classical Jyotisha chapter counts.
_ROMAN_PATTERN = r"[IVXLCDM]+"
_ARABIC_PATTERN = r"\d{1,3}"
_DEFAULT_HEADER_REGEX = (
    rf"(?:^|\n)\s*(?:chapter|adhyaya|adhyāya)\s+"
    rf"(?P<numpart>{_ROMAN_PATTERN}|{_ARABIC_PATTERN})"
    rf"\s*[.\-:]?\s*(?P<title>[^\n]*?)\s*$"
)
_ADHYAYA_REGEX = _DEFAULT_HEADER_REGEX  # same now — combined pattern covers both
_PADA_REGEX = (
    rf"(?:^|\n)\s*(?:pada|sutra|chapter|adhyaya)\s+"
    rf"(?P<numpart>{_ROMAN_PATTERN}|{_ARABIC_PATTERN})"
    rf"\s*[.\-:]?\s*(?P<title>[^\n]*?)\s*$"
)


# Roman numeral -> int (small range)
_ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def _roman_to_int(s: str) -> int:
    s = s.upper()
    total = 0
    prev = 0
    for ch in reversed(s):
        v = _ROMAN_VALUES.get(ch, 0)
        if v < prev:
            total -= v
        else:
            total += v
        prev = v
    return total


def _parse_chapter_num(num_str: str) -> int | None:
    s = num_str.strip()
    if s.isdigit():
        n = int(s)
        return n if 1 <= n <= 200 else None
    # Roman numeral
    try:
        n = _roman_to_int(s)
        return n if 1 <= n <= 200 else None
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Bundled classical book set                                                   #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class _Book:
    identifier: str           # archive.org identifier
    filename: str             # _djvu.txt filename
    book_slug: str            # local dir name
    book_title: str           # frontmatter title prefix
    author: str
    translator: str
    classical_ref_prefix: str  # e.g. "BPHS" -> classical_refs become BPHS.1, BPHS.2
    header_regex: str = _DEFAULT_HEADER_REGEX


_CLASSICAL_BUNDLE: tuple[_Book, ...] = (
    _Book(
        identifier="JatakaParijataVolIOfIIByVSubrahmanyaSastri",
        filename="Jataka Parijata Vol I of II by V Subrahmanya Sastri_djvu.txt",
        book_slug="jataka_parijata",
        book_title="Jataka Parijata Vol I",
        author="Vaidyanatha Dikshita",
        translator="V. Subrahmanya Sastri",
        classical_ref_prefix="JatakaParijata",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="JatakaParijataVolIIOfIIByVSubrahmanyaSastri",
        filename="Jataka Parijata Vol II of II by V Subrahmanya Sastri_djvu.txt",
        book_slug="jataka_parijata",
        book_title="Jataka Parijata Vol II",
        author="Vaidyanatha Dikshita",
        translator="V. Subrahmanya Sastri",
        classical_ref_prefix="JatakaParijata",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    # 2026-05-24 update: replaced the Sanskrit-script edition
    # (saravaliofkalyanavarmasanthanamr.astrology_202003_28_Z, 66% ASCII)
    # with the 100% ASCII English Santhanam translation.
    _Book(
        identifier="KalyanaVarmasSaravali_201707",
        filename="Kalyana Varmas Saravali_djvu.txt",
        book_slug="saravali",
        book_title="Saravali",
        author="Kalyana Varma",
        translator="R. Santhanam",
        classical_ref_prefix="Saravali",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="BrihatJatakaOfVarahamihiraBySwamiVijnananda",
        filename="Brihat Jataka of Varahamihira By Swami Vijnananda_djvu.txt",
        book_slug="brihat_jataka",
        book_title="Brihat Jataka (Swami Vijnananda)",
        author="Varahamihira",
        translator="Swami Vijnananda",
        classical_ref_prefix="BrihatJataka",
        header_regex=_ADHYAYA_REGEX,
    ),
    _Book(
        identifier="uttkalamrita-kalidas-ps-sastri",
        filename="Uttkalamrita-kalidas-ps-sastri_djvu.txt",
        book_slug="uttara_kalamrita",
        book_title="Uttara Kalamrita",
        author="Kalidasa",
        translator="P. Subrahmanya Sastri",
        classical_ref_prefix="UttaraKalamrita",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="sripati-paddhati",
        filename="sripati-paddhati_djvu.txt",
        book_slug="sripatipaddhati",
        book_title="Sripatipaddhati",
        author="Sripati",
        translator="(unknown / Sanskrit)",
        classical_ref_prefix="Sripatipaddhati",
        header_regex=_ADHYAYA_REGEX,
    ),
    _Book(
        identifier="Astrology_Books_by_B_Suryanarayana_Row",
        filename="Jaimini Sutras - B Suryanarain Rao 1955_djvu.txt",
        book_slug="jaimini_sutras",
        book_title="Jaimini Sutras",
        author="Jaimini Maharshi",
        translator="B. Suryanarain Rao",
        classical_ref_prefix="Jaimini",
        header_regex=_PADA_REGEX,
    ),
    _Book(
        identifier="Astrology_Books_by_B_Suryanarayana_Row",
        filename="Sarvartha Chintamani with English Translation - B Suryanarayana Row 1899_djvu.txt",
        book_slug="sarvartha_chintamani",
        book_title="Sarvartha Chintamani",
        author="Venkatesha Sharma",
        translator="B. Suryanarayana Row",
        classical_ref_prefix="SarvarthaChintamani",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="Astrology_Books_by_B_Suryanarayana_Row",
        filename="Stri Jataka or Female Horoscopy - B Suryanarain Rao 1931 LR_djvu.txt",
        book_slug="stri_jataka",
        book_title="Stri Jataka (Female Horoscopy)",
        author="(traditional)",
        translator="B. Suryanarain Rao",
        classical_ref_prefix="StriJataka",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="Astrology_Books_by_B_Suryanarayana_Row",
        filename="Jataka Chandrika - B Suryanarayana Row 1900_djvu.txt",
        book_slug="jataka_chandrika",
        book_title="Jataka Chandrika",
        author="(traditional)",
        translator="B. Suryanarayana Row",
        classical_ref_prefix="JatakaChandrika",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    # ─── Round-2 additions (2026-05-24): broader classical + modern foundational ─── #
    _Book(
        identifier="varahamihira-brihat-samhita-panditabhushana-v-subrahmanya-sastri-1946-with-english-ocr-layer",
        filename="Varahamihira-Brihat-Samhita-Panditabhushana-V-Subrahmanya-Sastri-1946-with-English-OCR-layer_djvu.txt",
        book_slug="brihat_samhita_sastri",
        book_title="Brihat Samhita (Subrahmanya Sastri 1946)",
        author="Varahamihira",
        translator="V. Subrahmanya Sastri",
        classical_ref_prefix="BrihatSamhita",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="bihatsahitvarah00iyergoog",
        filename="bihatsahitvarah00iyergoog_djvu.txt",
        book_slug="brihat_samhita_iyer",
        book_title="The Brihat Samhita of Varahamihira (Iyer ed.)",
        author="Varahamihira",
        translator="N. Chidambaram Iyer",
        classical_ref_prefix="BrihatSamhita",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="in.ernet.dli.2015.351583",
        filename="2015.351583.Brihat-Samhita_djvu.txt",
        book_slug="brihat_samhita_dli",
        book_title="Brihat Samhita Part II (DLI)",
        author="Varahamihira",
        translator="(DLI edition)",
        classical_ref_prefix="BrihatSamhita",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="NotableHoroscopesBVR",
        filename="Notable Horoscopes_djvu.txt",
        book_slug="notable_horoscopes_raman",
        book_title="Notable Horoscopes",
        author="B. V. Raman",
        translator="(original English)",
        classical_ref_prefix="Raman.NH",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="hindupredictiveastrologyofbvraman",
        filename="Hindu Predictive Astrology of B V Raman_djvu.txt",
        book_slug="hindu_predictive_astrology_raman",
        book_title="Hindu Predictive Astrology",
        author="B. V. Raman",
        translator="(original English)",
        classical_ref_prefix="Raman.HPA",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="AstrologyForBeginners_201705",
        filename="Astrology For Beginners BVRaman_djvu.txt",
        book_slug="astrology_for_beginners_raman",
        book_title="Astrology for Beginners",
        author="B. V. Raman",
        translator="(original English)",
        classical_ref_prefix="Raman.AFB",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    # ASP (2026-08-03): NOT an archive.org import — the chapters were OCR'd locally from a
    # user-supplied scan (easyocr, two-pages-per-sheet split at the gutter; provenance in each
    # chapter's front-matter). Listed here because every LIVE registry book must be known to
    # this bundle (test_registry_slugs_coupled_to_etl_bundle); `identifier`/`filename` record
    # the local pipeline rather than an archive identifier, and a re-import would re-run that
    # OCR pipeline, not this ETL.
    _Book(
        identifier="(local-scan; no archive.org identifier)",
        filename="89c0f204-478806521ashtakavargaBVRamanpdf.pdf",
        book_slug="ashtakavarga_system_raman",
        book_title="Ashtakavarga System of Prediction",
        author="B. V. Raman",
        translator="(original English)",
        classical_ref_prefix="Raman.ASP",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="how-to-judge-a-horoscope-r.-santhanam",
        filename="How to Judge a Horoscope - R. Santhanam_djvu.txt",
        book_slug="how_to_judge_a_horoscope_raman",
        book_title="How To Judge A Horoscope",
        author="B. V. Raman",
        translator="R. Santhanam",
        classical_ref_prefix="Raman.HJaH",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="how-to-judge-a-horoscope-r.-santhanam",
        filename="Crux Of Vedic Astrology - Timing Of Events - Sanjay Rath_djvu.txt",
        book_slug="crux_of_vedic_astrology_rath",
        book_title="Crux of Vedic Astrology — Timing of Events",
        author="Sanjay Rath",
        translator="(original English)",
        classical_ref_prefix="Rath.Crux",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="314068300ThreeHundredImportantCombinationsOfBVRaman1947Ed",
        filename="314068300-Three-Hundred-Important-Combinations-of-B-V-Raman-1947-ed_djvu.txt",
        book_slug="three_hundred_combinations_raman",
        book_title="Three Hundred Important Combinations",
        author="B. V. Raman",
        translator="(original English)",
        classical_ref_prefix="Raman.300IC",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="PrasnaMargaBVR",
        filename="Prasna Marga 1_djvu.txt",
        book_slug="prasna_marga_vol1",
        book_title="Prasna Marga Vol I",
        author="(traditional Kerala)",
        translator="B. V. Raman",
        classical_ref_prefix="PrasnaMarga",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="PrasnaMargaBVR",
        filename="Prasna Marga 2_djvu.txt",
        book_slug="prasna_marga_vol2",
        book_title="Prasna Marga Vol II",
        author="(traditional Kerala)",
        translator="B. V. Raman",
        classical_ref_prefix="PrasnaMarga",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="ashtakavarga",
        filename="Ashtakavarga 1957 Ed. by C S Patel & Aiyar_djvu.txt",
        book_slug="ashtakavarga_patel",
        book_title="Ashtakavarga",
        author="(traditional)",
        translator="C. S. Patel & V. K. Aiyar",
        classical_ref_prefix="Ashtakavarga",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="LalKitabEdition1952Part1Of3",
        filename="lal kitab edition 1952 - part 1 of 3_djvu.txt",
        book_slug="lal_kitab_vol1",
        book_title="Lal Kitab 1952 Part I",
        author="(traditional Persian-Vedic synthesis)",
        translator="(1952 edition)",
        classical_ref_prefix="LalKitab",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="LalKitabEdition1952Part2Of3",
        filename="lal kitab edition 1952 - part 2 of 3_djvu.txt",
        book_slug="lal_kitab_vol2",
        book_title="Lal Kitab 1952 Part II",
        author="(traditional Persian-Vedic synthesis)",
        translator="(1952 edition)",
        classical_ref_prefix="LalKitab",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="LalKitabEdition1952Part3Of3",
        filename="lal kitab edition 1952 - part 3 of 3_djvu.txt",
        book_slug="lal_kitab_vol3",
        book_title="Lal Kitab 1952 Part III",
        author="(traditional Persian-Vedic synthesis)",
        translator="(1952 edition)",
        classical_ref_prefix="LalKitab",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="NadiJyotishaVol1EnglishEdition",
        filename="Nadi Jyotisha Vol 1 (English Edition)_djvu.txt",
        book_slug="nadi_jyotisha_vol1",
        book_title="Nadi Jyotisha Vol I",
        author="(traditional Nadi)",
        translator="(English Edition)",
        classical_ref_prefix="NadiJyotisha",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="NADIASTROLOGICALRESEARCHESGROUPII",
        filename="NADI ASTROLOGICAL RESEARCHES GROUP-II_djvu.txt",
        book_slug="nadi_astrological_researches",
        book_title="Nadi Astrological Researches Group II",
        author="(Nadi research group)",
        translator="(original English)",
        classical_ref_prefix="NadiResearch",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    # ─── Round-3 additions (2026-05-24): Hora Sara family + Nadi + Modern ─── #
    _Book(
        identifier="HoraSaraRSanthanamEng",
        filename="Hora Sara of Prithuyasas - Prof R Santhanam_djvu.txt",
        book_slug="hora_sara_santhanam",
        book_title="Hora Sara of Prithuyasas (Santhanam)",
        author="Prithuyasas",
        translator="R. Santhanam",
        classical_ref_prefix="HoraSara",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="horasara-of-prithuyasas-by-v.-subrahmanya-sastri",
        filename="Horasara of Prithuyasas by V. Subrahmanya Sastri_djvu.txt",
        book_slug="hora_sara_sastri",
        book_title="Horasara of Prithuyasas (V.S. Sastri)",
        author="Prithuyasas",
        translator="V. Subrahmanya Sastri",
        classical_ref_prefix="HoraSara",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="IndianHoraryShatpanchashikaVAKAyer",
        filename="Indian Horary Astrology - V.A.K. Ayer_djvu.txt",
        book_slug="indian_horary_ayer",
        book_title="Indian Horary Astrology (Shatpanchashika)",
        author="(traditional)",
        translator="V.A.K. Ayer",
        classical_ref_prefix="Shatpanchashika",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="DaivajnaVallabha",
        filename="Daivajna Vallabha_djvu.txt",
        book_slug="daivajna_vallabha",
        book_title="Daivajna Vallabha",
        author="Varahamihira (attrib.)",
        translator="(English ed.)",
        classical_ref_prefix="DaivajnaVallabha",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="krishneeyam-translation-by-me",
        filename="Krishneeyam Translation_djvu.txt",
        book_slug="krishneeyam",
        book_title="Krishneeyam",
        author="(traditional Kerala)",
        translator="(modern English)",
        classical_ref_prefix="Krishneeyam",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="in.ernet.dli.2015.282421",
        filename="2015.282421.The-Vidyamadhaviyam_djvu.txt",
        book_slug="vidyamadhaviyam",
        book_title="Vidyamadhaviyam Part I",
        author="Vidya Madhava",
        translator="(DLI ed.)",
        classical_ref_prefix="Vidyamadhaviyam",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="deva-keralam-1-chandrakala-nadi_202309",
        filename="Deva Keralam 1 Chandrakala Nadi_djvu.txt",
        book_slug="deva_keralam_vol1",
        book_title="Deva Keralam (Chandrakala Nadi) Vol I",
        author="(traditional Nadi)",
        translator="(modern English)",
        classical_ref_prefix="DevaKeralam",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="deva-keralam-2-chandrakala-nadi_202309",
        filename="Deva Keralam 2 Chandrakala Nadi_djvu.txt",
        book_slug="deva_keralam_vol2",
        book_title="Deva Keralam (Chandrakala Nadi) Vol II",
        author="(traditional Nadi)",
        translator="(modern English)",
        classical_ref_prefix="DevaKeralam",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="deva-keralam-3-chandrakala-nadi_202309",
        filename="Deva Keralam 3 Chandrakala Nadi_djvu.txt",
        book_slug="deva_keralam_vol3",
        book_title="Deva Keralam (Chandrakala Nadi) Vol III",
        author="(traditional Nadi)",
        translator="(modern English)",
        classical_ref_prefix="DevaKeralam",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="ckn-3",
        filename="ckn-3_djvu.txt",
        book_slug="chandrakala_nadi_full",
        book_title="Chandrakala Nadi (full)",
        author="(traditional Nadi)",
        translator="(modern English)",
        classical_ref_prefix="ChandrakalaNadi",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="UJrg_prasna-tantra-by-b.-v.-raman-raman-publication",
        # Filename corrected 2026-08-03 to the exact name the item serves ("B.V.Raman",
        # no spaces) — the earlier spelling is why only a partial ingest ever landed.
        filename="Prasna Tantra by B.V.Raman - Raman Publication_djvu.txt",
        book_slug="prasna_tantra_raman",
        book_title="Prasna Tantra",
        author="(traditional Kerala)",
        translator="B. V. Raman",
        classical_ref_prefix="PrasnaTantra",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="advance-techniques-of-astrology-prediction-k.-n.-rao",
        filename="Advance Techniques Of Astrology Prediction K. N. Rao_djvu.txt",
        book_slug="advance_techniques_kn_rao",
        book_title="Advance Techniques Of Astrology Prediction",
        author="K. N. Rao",
        translator="(original English)",
        classical_ref_prefix="Rao.AdvanceTech",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="systemsapproachf0000chou",
        filename="systemsapproachf0000chou_djvu.txt",
        book_slug="systems_approach_choudhry",
        book_title="Systems' Approach for Interpreting Horoscopes",
        author="V. K. Choudhry",
        translator="(original English)",
        classical_ref_prefix="Choudhry.SA",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="astrology-of-the-seers-david-frawley_sri-vamadeva-shastri",
        filename="Astrology of the Seers - David Frawley (Sri Vamadeva Shastri)_djvu.txt",
        book_slug="astrology_seers_frawley",
        book_title="Astrology of the Seers",
        author="David Frawley (Vamadeva Shastri)",
        translator="(original English)",
        classical_ref_prefix="Frawley.AOS",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="david-frawley-ayurvedic-astrology-self-healing-through-the-stars_202305",
        filename="David Frawley - Ayurvedic Astrology - Self Healing Through the Stars_djvu.txt",
        book_slug="ayurvedic_astrology_frawley",
        book_title="Ayurvedic Astrology",
        author="David Frawley",
        translator="(original English)",
        classical_ref_prefix="Frawley.AA",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="VarshaphalOrTheHinduProgressedHoroscope",
        filename="Varshaphal or The Hindu Progressed Horoscope_djvu.txt",
        book_slug="varshaphal_raman",
        book_title="Varshaphal — The Hindu Progressed Horoscope",
        author="B. V. Raman",
        translator="(original English)",
        classical_ref_prefix="Raman.Varshaphal",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        # Repointed 2026-08-03: bwb_P9-EAH-659 is access-restricted (401 on its _djvu.txt),
        # which is why this book's corpus dir stayed empty. The DLI scan is open.
        identifier="in.ernet.dli.2015.128092",
        filename="2015.128092.Muhurtha-Or-Electional-Astrology_djvu.txt",
        book_slug="muhurtha_raman",
        book_title="Muhurtha — Electional Astrology",
        author="B. V. Raman",
        translator="(original English)",
        classical_ref_prefix="Raman.Muhurtha",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="gzwo_graha-and-bhava-balas-by-b-v-raman-english-sanskrit-astrology-hindu-astrolo",
        filename="Graha and Bhava Balas By B V Raman - English Sanskrit Astrology Hindu Astrology Astronomy Indo-Aryan Religion Hindu_djvu.txt",
        book_slug="graha_bhava_balas_raman",
        book_title="Graha and Bhava Balas",
        author="B. V. Raman",
        translator="(original English)",
        classical_ref_prefix="Raman.GBB",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="rojr_the-astrological-magazine-volume-75-monthly-journal-edited-by-b-v-raman-ast",
        filename="The Astrological Magazine Volume 75 - Monthly journal edited by B V Raman_djvu.txt",
        book_slug="astrological_magazine_v75_raman",
        book_title="The Astrological Magazine Vol 75 (Raman ed.)",
        author="B. V. Raman (ed.)",
        translator="(original English)",
        classical_ref_prefix="Raman.AMv75",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="raman-how-to-judge-horoscope-2",
        filename="How to judge horoscope by B. V. RAMAN_djvu.txt",
        book_slug="how_to_judge_horoscope_raman2",
        book_title="How to Judge a Horoscope (Raman, 2nd alt)",
        author="B. V. Raman",
        translator="(original English)",
        classical_ref_prefix="Raman.HJaH2",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="studies-in-jaimini-astrology-by-b-v-raman-127930441",
        filename="Studies in Jaimini Astrology by B V Raman_djvu.txt",
        book_slug="studies_jaimini_raman",
        book_title="Studies in Jaimini Astrology",
        author="B. V. Raman",
        translator="(original English)",
        classical_ref_prefix="Raman.SJA",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="c.-s.-patel-navamsa-in-astrology",
        filename="C. S. Patel - Navamsa in Astrology_djvu.txt",
        book_slug="navamsa_patel",
        book_title="Navamsa in Astrology",
        author="C. S. Patel",
        translator="(original English)",
        classical_ref_prefix="Patel.Navamsa",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="fundamentals-of-vedic-astrology-vedic-astrologers-handbook-vol.-i",
        filename="Fundamentals of Vedic Astrology - Vedic Astrologers' Handbook Vol. I_djvu.txt",
        book_slug="fundamentals_vedic_astrology",
        book_title="Fundamentals of Vedic Astrology (Vol I)",
        author="(modern compilation)",
        translator="(original English)",
        classical_ref_prefix="VAH",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
    _Book(
        identifier="bepin-behari-vedic-occultism",
        filename="Bepin Behari - Vedic Occultism_djvu.txt",
        book_slug="vedic_occultism_behari",
        book_title="Vedic Occultism",
        author="Bepin Behari",
        translator="(original English)",
        classical_ref_prefix="Behari.VO",
        header_regex=_DEFAULT_HEADER_REGEX,
    ),
)


# --------------------------------------------------------------------------- #
# Chapter-splitting + cleaning                                                 #
# --------------------------------------------------------------------------- #

def _clean_ocr(text: str, *, book_title_pattern: str | None = None) -> str:
    """Strip OCR boilerplate: page-numbers, repeated header-banners."""
    text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)
    if book_title_pattern:
        text = re.sub(book_title_pattern, "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def split_by_chapter(
    text: str,
    *,
    header_regex: Pattern,
    book_title_pattern: str | None = None,
) -> list[dict]:
    matches = list(header_regex.finditer(text))
    if not matches:
        return []
    chapters: list[dict] = []
    for i, m in enumerate(matches):
        num_str = m.group("numpart") if "numpart" in (m.groupdict() or {}) else m.group(1)
        ch_num = _parse_chapter_num(num_str)
        if ch_num is None:
            continue
        try:
            title_raw = m.group("title")
        except (IndexError, KeyError):
            title_raw = m.group(2) if (m.lastindex and m.lastindex >= 2) else ""
        ch_title = (title_raw or "").strip().rstrip(".") or f"Chapter {ch_num}"
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = _clean_ocr(text[start:end], book_title_pattern=book_title_pattern)
        existing = next((c for c in chapters if c["chapter_num"] == ch_num), None)
        if existing:
            if len(body) > len(existing["body"]):
                existing["body"] = body
                existing["title"] = ch_title
            continue
        chapters.append({
            "chapter_num": ch_num,
            "title": ch_title,
            "body": body,
            "n_words": len(body.split()),
        })
    return chapters


def fallback_single_artefact(
    text: str, *, book_title_pattern: str | None = None,
) -> list[dict]:
    """Wrap the whole text as a single artefact when chapter-split finds nothing."""
    body = _clean_ocr(text, book_title_pattern=book_title_pattern)
    if not body or len(body.split()) < 100:
        return []
    return [{
        "chapter_num": 1,
        "title": "Full text (unsplit)",
        "body": body,
        "n_words": len(body.split()),
    }]


def _ascii_ratio(text: str) -> float:
    if not text:
        return 0.0
    return sum(1 for c in text if ord(c) < 128) / len(text)


# --------------------------------------------------------------------------- #
# Markdown output                                                              #
# --------------------------------------------------------------------------- #

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(s: str) -> str:
    return _SLUG_RE.sub("-", s.lower()).strip("-")[:60] or "chapter"


def _yaml_quote(s: str) -> str:
    """Wrap a YAML string value in double quotes, escaping inner quotes.

    Required when the value contains ':' or other YAML-significant characters
    (e.g. OCR'd titles like 'Chapter 2: of the animals' would otherwise be
    parsed as a nested mapping and break the frontmatter parser).
    """
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def write_chapter(chapter: dict, output_dir: Path, *, book: _Book, source_url: str, scraped_at: str) -> Path:
    name = f"chapter_{chapter['chapter_num']:03d}_{_slug(chapter['title'])}.md"
    path = output_dir / name
    title_full = f"{book.book_title} — Chapter {chapter['chapter_num']}: {chapter['title']}"
    frontmatter = "\n".join([
        "---",
        f"id: {book.book_slug}-ch{chapter['chapter_num']:03d}",
        f"source: {book.book_slug}",
        f"title: {_yaml_quote(title_full)}",
        f"book: {_yaml_quote(book.book_title)}",
        f"author: {_yaml_quote(book.author)}",
        f"translator: {_yaml_quote(book.translator)}",
        f"chapter_index: {chapter['chapter_num']}",
        f"language: en",
        f"content_type: classical_text",
        f"quality: ocr_text",
        f"source_url: {source_url}",
        f"scraped_at: {scraped_at}",
        f"topics:",
        f"  - meta.source_texts",
        f"classical_refs:",
        f"  - {book.classical_ref_prefix}.{chapter['chapter_num']}",
        f"---",
    ])
    body = (
        f"\n\n# {book.book_title} — Chapter {chapter['chapter_num']}\n"
        f"_{chapter['title']}_\n\n"
        + chapter["body"]
        + "\n"
    )
    path.write_text(frontmatter + body, encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def _book_url(identifier: str, filename: str) -> str:
    return f"https://archive.org/download/{identifier}/{quote(filename)}"


def import_book(
    book: _Book,
    output_root: Path,
    *,
    session: requests.Session,
    min_words: int = 50,
) -> dict:
    out_dir = output_root / book.book_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    url = _book_url(book.identifier, book.filename)
    logger.info("downloading %s (%s)", book.book_title, url)
    r = session.get(url, timeout=60)
    if r.status_code != 200:
        logger.warning("%s: HTTP %s", book.book_title, r.status_code)
        return {"book": book.book_slug, "error": f"HTTP {r.status_code}"}
    text = r.text
    # Skip books that are <90% ASCII — these are Sanskrit-script editions whose OCR
    # is unusable as English knowledge content (e.g. Saravali Sanskrit-only edition).
    ascii_pct = _ascii_ratio(text)
    if ascii_pct < 0.90:
        logger.warning("%s: only %.1f%% ASCII — likely Sanskrit-script OCR garbage, skipping",
                       book.book_slug, ascii_pct * 100)
        return {"book": book.book_slug, "ascii_pct": ascii_pct, "skipped": True}

    book_title_pattern = (
        rf"^\s*{re.escape(book.book_title.split('—')[0].strip())}.*$"
    )
    header_re = re.compile(book.header_regex, re.MULTILINE | re.IGNORECASE)
    chapters = split_by_chapter(text, header_regex=header_re, book_title_pattern=book_title_pattern)
    if len(chapters) < 2:
        logger.info("%s: chapter-split found %d, falling back to single-artefact wrap",
                    book.book_slug, len(chapters))
        chapters = fallback_single_artefact(text, book_title_pattern=book_title_pattern)
    scraped_at = dt.datetime.now(dt.timezone.utc).isoformat()

    n_persisted = 0
    n_dropped = 0
    for ch in chapters:
        if ch["n_words"] < min_words:
            n_dropped += 1
            continue
        write_chapter(ch, out_dir, book=book, source_url=url, scraped_at=scraped_at)
        n_persisted += 1
    logger.info(
        "%s: split=%d persisted=%d dropped=%d -> %s",
        book.book_slug, len(chapters), n_persisted, n_dropped, out_dir,
    )
    return {
        "book": book.book_slug,
        "n_chapters_split": len(chapters),
        "n_persisted": n_persisted,
        "n_dropped": n_dropped,
        "output_dir": str(out_dir),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.import_archive_text",
        description="Mirror classical Jyotisha texts from archive.org into the knowledge library.",
    )
    parser.add_argument("--bundle", choices=["classical_jyotisha"], default=None,
                        help="Run the pre-configured bundle of 10 classical books.")
    parser.add_argument("--identifier", type=str, default=None)
    parser.add_argument("--filename", type=str, default=None)
    parser.add_argument("--book-slug", type=str, default=None)
    parser.add_argument("--book-title", type=str, default=None)
    parser.add_argument("--author", type=str, default="(unknown)")
    parser.add_argument("--translator", type=str, default="(unknown)")
    parser.add_argument("--classical-ref-prefix", type=str, default=None)
    parser.add_argument("--header-regex", type=str, default=_DEFAULT_HEADER_REGEX)
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("data/knowledge_library/sources"),
    )
    parser.add_argument("--min-words", type=int, default=50)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    if args.bundle == "classical_jyotisha":
        books = _CLASSICAL_BUNDLE
    elif args.identifier and args.filename and args.book_slug:
        books = (_Book(
            identifier=args.identifier,
            filename=args.filename,
            book_slug=args.book_slug,
            book_title=args.book_title or args.book_slug,
            author=args.author,
            translator=args.translator,
            classical_ref_prefix=args.classical_ref_prefix or args.book_slug,
            header_regex=args.header_regex,
        ),)
    else:
        parser.error("either --bundle classical_jyotisha or "
                     "(--identifier, --filename, --book-slug) is required")
        return 2

    results = []
    for book in books:
        try:
            r = import_book(book, args.output_root, session=session, min_words=args.min_words)
            results.append(r)
        except Exception as e:
            logger.warning("%s failed: %s", book.book_slug, e)
            results.append({"book": book.book_slug, "error": str(e)})

    print()
    print("=== Import summary ===")
    total_persisted = 0
    for r in results:
        if r.get("error"):
            print(f"  [ERR]  {r['book']:<25} {r['error']}")
        elif r.get("skipped"):
            ratio = r.get("ascii_pct", 0.0)
            print(f"  [SKIP] {r['book']:<25} ASCII={ratio*100:.1f}% — sanskrit-script OCR")
        else:
            n_split = r.get("n_chapters_split", 0)
            n_p = r.get("n_persisted", 0)
            n_d = r.get("n_dropped", 0)
            print(f"  [OK]   {r['book']:<25} chapters={n_split:<4} "
                  f"persisted={n_p:<4} dropped={n_d}")
            total_persisted += n_p
    print(f"\nTotal chapters persisted across all books: {total_persisted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
