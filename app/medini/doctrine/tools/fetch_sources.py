"""Fetch B. V. Raman source texts (archive.org `_djvu.txt` OCR) with QC.

Downloads the OCR dumps for every book in ``MANIFEST`` into a local
directory (the session scratchpad — full texts are never committed; the
repo carries only fair-use page-cited excerpts per the established policy),
verifies each against a QC gate, builds mechanical page maps, and emits the
rows for ``docs/raman_doctrine/SOURCES.md``.

QC gate (per text):
  * english_ratio  — fraction of non-blank lines carrying >=2 latin words.
    Guards against the hpa2.txt precedent (a Devanagari-OCR scan of HPA
    with zero usable English lines).
  * marker hits    — every book lists known chapter/title phrases that a
    correct, complete scan must contain.
  * page map       — near-monotonic folio chain must reach a plausible
    max page and accept a healthy fraction of folio candidates.

CLI:
    python -m app.medini.doctrine.tools.fetch_sources \
        --dest <scratchpad>/raman_sources \
        --page-maps data/raman_doctrine/page_maps \
        --report data/raman_doctrine/sources_qc.json
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import logging
import re
import time
import urllib.parse
from pathlib import Path

import requests

from app.medini.doctrine.tools.page_map import (
    STANDALONE_FOLIO,
    build_page_map,
    save_page_map,
)

logger = logging.getLogger(__name__)

METADATA_URL = "https://archive.org/metadata/{item}"
DOWNLOAD_URL = "https://archive.org/download/{item}/{name}"

# HTJAH prints its folio in running heads, not standalone lines:
# verso "50 How to Judge a Horoscope", recto "Concerning the Seventh House 51".
_HTJAH_FOLIOS = (
    STANDALONE_FOLIO,
    r"^(\d{1,3})\s+How to Judge",
    r"(?:House|Horoscope)\s+(\d{1,3})\s*$",
)


@dataclasses.dataclass(frozen=True)
class SourceSpec:
    key: str            # canonical book key used across the compendium
    title: str
    item: str           # archive.org item identifier
    filename: str       # exact _djvu.txt name within the item
    markers: tuple[str, ...]  # phrases a correct scan must contain (casefolded match)
    min_pages: int      # plausibility floor for the page map's max page
    folio_patterns: tuple[str, ...] = (STANDALONE_FOLIO,)
    # Where the print carries its page number: standalone folios sit at the
    # page FOOT ("bottom"), running heads at the page HEAD ("top"). Decides
    # prev-vs-next anchor when resolving an offset to a page.
    folio_at: str = "bottom"


MANIFEST: tuple[SourceSpec, ...] = (
    SourceSpec(
        key="hpa",
        title="Hindu Predictive Astrology",
        # NOT jmbQ_hindu-predictive-astrology-b.-v.-raman: that item is a
        # Devanagari-script scan (english_ratio 0.0, the hpa2.txt precedent).
        item="hindupredictiveastrologyofbvraman",
        filename="Hindu Predictive Astrology of B V Raman_djvu.txt",
        markers=("hindu predictive astrology", "ashtakavarga", "ayurdaya"),
        min_pages=250,
    ),
    SourceSpec(
        key="htjah_vol1",
        title="How to Judge a Horoscope, Vol. 1 (houses I-VI)",
        item="raman-how-to-judge-horoscope-2",
        filename="raman-how-to-judge-horoscope-1_djvu.txt",
        markers=("how to judge a horoscope", "first house"),
        min_pages=150,
        folio_patterns=_HTJAH_FOLIOS,
        folio_at="top",
    ),
    SourceSpec(
        key="htjah_vol2",
        title="How to Judge a Horoscope, Vol. 2 (houses VII-XII)",
        item="raman-how-to-judge-horoscope-2",
        filename="raman-how-to-judge-horoscope-2_djvu.txt",
        markers=("how to judge a horoscope", "seventh house"),
        min_pages=150,
        folio_patterns=_HTJAH_FOLIOS,
        folio_at="top",
    ),
    SourceSpec(
        key="three_hundred",
        title="Three Hundred Important Combinations",
        item="ThreeHundredImportantCombinationsInVedicAstrology",
        filename="Three Hundred Important Combinations in Vedic Astrology_djvu.txt",
        markers=("three hundred important combinations", "yoga"),
        min_pages=150,
    ),
    SourceSpec(
        key="notable_horoscopes",
        title="Notable Horoscopes",
        item="NotableHoroscopesBVR",
        filename="Notable Horoscopes_djvu.txt",
        markers=("notable horoscopes",),
        min_pages=200,
    ),
    SourceSpec(
        key="jaimini_studies",
        title="Studies in Jaimini Astrology",
        item="studies-in-jaimini-astrology-by-b-v-raman-127930441",
        filename="Studies-in-jaimini-astrology-by-b-v-raman-127930441_djvu.txt",
        markers=("jaimini", "karaka"),
        min_pages=100,
    ),
    SourceSpec(
        key="graha_bhava_balas",
        title="Graha and Bhava Balas",
        item="gzwo_graha-and-bhava-balas-by-b-v-raman-english-sanskrit-astrology-hindu-astrolo",
        filename=(
            "Graha And Bhava Balas by B V Raman English Sanskrit Astrology "
            "Hindu Astrology Bangalore 1942 - Raman Publications_djvu.txt"
        ),
        markers=("bhava", "shadbala"),
        min_pages=80,
        folio_patterns=(
            STANDALONE_FOLIO,
            r"^(\d{1,3})\s+GRAHA AND BHAVA",
            r"GRAHA AND BHAVA BALAS\s+(\d{1,3})\s*$",
        ),
        folio_at="top",
    ),
    SourceSpec(
        key="muhurtha",
        title="Muhurtha (Electional Astrology)",
        item="in.ernet.dli.2015.128092",
        filename="2015.128092.Muhurtha-Or-Electional-Astrology_djvu.txt",
        markers=("muhurtha", "electional"),
        min_pages=100,
    ),
    SourceSpec(
        key="prasna_marga_1",
        title="Prasna Marga, Part 1",
        item="PrasnaMargaBVR",
        filename="Prasna Marga 1_djvu.txt",
        markers=("prasna",),
        min_pages=150,
    ),
    SourceSpec(
        key="prasna_marga_2",
        title="Prasna Marga, Part 2",
        # PrasnaMargaBVR's "Prasna Marga 2_djvu.txt" loses most folio lines
        # (19 usable anchors); this scan keeps 72 and reads cleaner.
        item="prasna-marga-part-2-by-bv-raman",
        filename="Prasna Marga Part 2 by BV Raman_djvu.txt",
        markers=("prasna",),
        min_pages=300,  # Part 2 continues Part 1's pagination (starts ~p.280)
    ),
    SourceSpec(
        key="manual_hindu_astrology",
        title="A Manual of Hindu Astrology",
        item="ISVP_a-manual-of-hindu-astrology-by-venkat-raman-english-raman-publications-banglore",
        filename=(
            "A Manual Of Hindu Astrology By Venkat Raman English - "
            "Raman Publications, Banglore_djvu.txt"
        ),
        markers=("hindu astrology", "bhava"),
        min_pages=80,
        folio_patterns=(STANDALONE_FOLIO, r"^(\d{1,3})\s+A MANUAL OF"),
        folio_at="top",
    ),
)

# Titles Raman wrote that have no retrievable archive.org text; recorded in
# SOURCES.md so "complete" coverage claims stay honest.
UNAVAILABLE_TITLES: tuple[str, ...] = (
    "Ashtakavarga System of Prediction",
    "A Catechism of Astrology",
    "My Experiences in Astrology",
    "Hindu Astrology and the West",
    "Bhavartha Ratnakara (translation)",
)

_WORD_RE = re.compile(r"[A-Za-z]{2,}")


@dataclasses.dataclass
class QCResult:
    key: str
    sha256: str
    bytes: int
    english_ratio: float
    markers_missing: list[str]
    page_max: int
    page_anchors: int
    page_monotonic_fraction: float
    passed: bool
    error: str | None = None


def english_ratio(text: str) -> float:
    """Fraction of non-blank lines that contain at least two latin words."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return 0.0
    hits = sum(1 for ln in lines if len(_WORD_RE.findall(ln)) >= 2)
    return hits / len(lines)


def missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    folded = re.sub(r"\s+", " ", text.casefold())
    return [m for m in markers if m not in folded]


def qc_text(spec: SourceSpec, text: str) -> QCResult:
    ratio = english_ratio(text)
    missing = missing_markers(text, spec.markers)
    pmap = build_page_map(text, patterns=spec.folio_patterns)
    passed = (
        ratio >= 0.5
        and not missing
        and pmap.max_page >= spec.min_pages
        and len(pmap.anchors) >= 30
    )
    return QCResult(
        key=spec.key,
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        bytes=len(text.encode("utf-8")),
        english_ratio=round(ratio, 4),
        markers_missing=missing,
        page_max=pmap.max_page,
        page_anchors=len(pmap.anchors),
        page_monotonic_fraction=round(pmap.monotonic_fraction, 4),
        passed=passed,
    )


def fetch_text(spec: SourceSpec, session: requests.Session, timeout: float = 120.0) -> str:
    url = DOWNLOAD_URL.format(
        item=spec.item, name=urllib.parse.quote(spec.filename)
    )
    resp = session.get(url, timeout=timeout)
    if resp.status_code == 404:
        # File names inside items rot occasionally; fall back to the item's
        # metadata listing when it carries exactly one OCR dump.
        meta = session.get(METADATA_URL.format(item=spec.item), timeout=timeout)
        meta.raise_for_status()
        djvus = [
            f["name"] for f in meta.json().get("files", [])
            if f["name"].endswith("_djvu.txt")
        ]
        if len(djvus) != 1:
            resp.raise_for_status()
        logger.warning("%s: filename %r gone; using %r", spec.key, spec.filename, djvus[0])
        resp = session.get(
            DOWNLOAD_URL.format(item=spec.item, name=urllib.parse.quote(djvus[0])),
            timeout=timeout,
        )
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text


def local_path(dest: Path, spec: SourceSpec) -> Path:
    return dest / f"{spec.key}.txt"


def run(dest: Path, page_maps_dir: Path, report_path: Path, rate_limit: float = 1.0) -> list[QCResult]:
    dest.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "astro-doctrine-fetch/1.0 (research; polite)"
    results: list[QCResult] = []
    for spec in MANIFEST:
        target = local_path(dest, spec)
        try:
            if target.exists() and target.stat().st_size > 0:
                logger.info("%s: cached (%s)", spec.key, target)
                text = target.read_text(encoding="utf-8")
            else:
                logger.info("%s: fetching %s / %s", spec.key, spec.item, spec.filename)
                text = fetch_text(spec, session)
                target.write_text(text, encoding="utf-8")
                time.sleep(rate_limit)
        except requests.RequestException as exc:
            logger.error("%s: fetch failed: %s", spec.key, exc)
            results.append(QCResult(
                key=spec.key, sha256="", bytes=0, english_ratio=0.0,
                markers_missing=list(spec.markers), page_max=0, page_anchors=0,
                page_monotonic_fraction=0.0, passed=False, error=str(exc),
            ))
            continue
        qc = qc_text(spec, text)
        results.append(qc)
        if qc.passed:
            save_page_map(
                build_page_map(text, patterns=spec.folio_patterns),
                page_maps_dir / f"{spec.key}.json",
            )
        logger.info(
            "%s: %s (english=%.2f, pages<=%d, anchors=%d, missing=%s)",
            spec.key, "PASS" if qc.passed else "FAIL",
            qc.english_ratio, qc.page_max, qc.page_anchors, qc.markers_missing,
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps([dataclasses.asdict(r) for r in results], indent=1),
        encoding="utf-8",
    )
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, required=True)
    parser.add_argument("--page-maps", type=Path, default=Path("data/raman_doctrine/page_maps"))
    parser.add_argument("--report", type=Path, default=Path("data/raman_doctrine/sources_qc.json"))
    parser.add_argument("--rate-limit", type=float, default=1.0)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = run(args.dest, args.page_maps, args.report, args.rate_limit)
    failed = [r.key for r in results if not r.passed]
    if failed:
        logger.error("QC FAILED for: %s", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
