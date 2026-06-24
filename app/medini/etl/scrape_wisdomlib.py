"""Mirror a wisdomlib.org book into the knowledge library as markdown.

Wisdomlib hosts public-domain English translations of many classical Indian
texts. This scraper:

  1. Reads the book TOC URL (e.g. `/hinduism/book/phaladeepika-...`).
  2. Discovers all chapter URLs under `/d/docNNNNNNN.html`.
  3. For each chapter, fetches the HTML, strips OCR warnings and navigation,
     and saves the cleaned content as markdown with YAML frontmatter.
  4. Output goes to `sources/<book_slug>/chapter_NN_<slug>.md` —
     auto-discovered by `build_knowledge_manifest.py`.

The scraper is polite (0.6s delay default), resume-safe (skips chapters with
existing output files), and uses a desktop browser User-Agent.

Usage:
    # Phaladeepika
    python -m app.medini.etl.scrape_wisdomlib \\
        --book-url https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation \\
        --output-dir data/knowledge_library/sources/phaladeepika \\
        --book-slug phaladeepika \\
        --topic-default classical_texts.phaladeepika
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# --------------------------------------------------------------------------- #
# TOC discovery                                                                #
# --------------------------------------------------------------------------- #

def list_chapters(book_url: str, *, session: requests.Session) -> list[dict[str, str]]:
    """Walk the book TOC and return [{title, url}, ...] for every chapter page.

    A "chapter" is any link under `/d/docNNNNNNN.html` whose path is a child
    of the book URL. The TOC also includes prefaces and indexes; we keep them
    all and let the chapter parser figure out what to extract.
    """
    r = session.get(book_url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Identify the book path prefix (e.g. /hinduism/book/phaladeepika-...)
    book_path = book_url.replace("https://www.wisdomlib.org", "").rstrip("/")

    chapters: list[dict[str, str]] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/d/doc" not in href:
            continue
        if book_path not in href and not href.startswith(book_path):
            continue
        full = href if href.startswith("http") else "https://www.wisdomlib.org" + href
        if full in seen:
            continue
        seen.add(full)
        title = a.get_text(strip=True) or "(untitled)"
        chapters.append({"title": title, "url": full})
    return chapters


# --------------------------------------------------------------------------- #
# Chapter content extraction                                                   #
# --------------------------------------------------------------------------- #

_OCR_CLASS_KILL = ("ocr",)
_NAV_CLASS_KILL = ("alert", "alert-warning", "btn", "no-gutters")


def _clean_article(article) -> str:
    """Strip noisy elements and return plain text of the article content."""
    # Drop OCR warnings, navigation buttons, popovers, scripts
    kill_targets: list = []
    for cls in _OCR_CLASS_KILL + _NAV_CLASS_KILL:
        kill_targets.extend(article.find_all(class_=cls))
    for el in article.find_all(["script", "style", "form", "button"]):
        kill_targets.append(el)
    # Definition-link tooltips (modal popups in wisdomlib)
    for el in article.find_all(attrs={"data-bs-toggle": True}):
        # Keep the anchor text but drop the modal data
        for attr in list(el.attrs):
            if attr.startswith("data-"):
                del el.attrs[attr]
    for el in kill_targets:
        try:
            el.decompose()
        except Exception:
            pass

    text = article.get_text(separator="\n")
    # Collapse runs of whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return text


def fetch_chapter(url: str, *, session: requests.Session) -> dict[str, Any]:
    """Fetch and parse a chapter page. Returns {title, body, raw_html_len}."""
    r = session.get(url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    article = soup.find("article")
    if article is None:
        # Fall back to main content
        article = soup.find("main") or soup.find("body")
    if article is None:
        raise RuntimeError(f"no article element in {url}")
    # Title: take first h1 in article, else use page <title>
    h1 = article.find(["h1", "h2"])
    title = h1.get_text(strip=True) if h1 else (soup.title.get_text(strip=True) if soup.title else "(untitled)")
    body = _clean_article(article)
    return {
        "title": title,
        "body": body,
        "raw_html_len": len(r.text),
        "n_chars": len(body),
        "n_words": len(body.split()),
    }


# --------------------------------------------------------------------------- #
# Output formatting                                                            #
# --------------------------------------------------------------------------- #

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    s = _SLUG_RE.sub("-", text.lower()).strip("-")
    return s[:60] if len(s) > 60 else s


def _format_markdown(
    *,
    chapter_idx: int,
    book_slug: str,
    source_url: str,
    title: str,
    body: str,
    topics: list[str],
    scraped_at: str,
    translator: str | None = None,
) -> str:
    """Build the final .md content with YAML frontmatter + body."""
    artefact_id = f"{book_slug}-ch{chapter_idx:02d}"
    fm_lines = [
        "---",
        f"id: {artefact_id}",
        f"source: {book_slug}",
        f"title: {title}",
        f"chapter_index: {chapter_idx}",
    ]
    if translator:
        fm_lines.append(f"translator: {translator}")
    fm_lines.extend([
        f"language: en",
        f"content_type: classical_text",
        f"quality: written_article",
        f"source_url: {source_url}",
        f"scraped_at: {scraped_at}",
        f"topics:",
    ])
    for t in topics:
        fm_lines.append(f"  - {t}")
    fm_lines.extend([
        "classical_refs: []",
        "---",
        "",
        f"# {title}",
        "",
        body,
        "",
    ])
    return "\n".join(fm_lines)


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run(
    book_url: str,
    output_dir: Path,
    *,
    book_slug: str,
    topic_default: str | None = None,
    translator: str | None = None,
    delay: float = 0.6,
    limit: int | None = None,
) -> dict[str, int]:
    """Mirror the full book into ``output_dir`` as one .md per chapter."""
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    logger.info("listing chapters from %s ...", book_url)
    chapters = list_chapters(book_url, session=session)
    logger.info("found %d chapter links", len(chapters))
    if limit:
        chapters = chapters[:limit]

    topics = [topic_default] if topic_default else []

    n_persisted = 0
    n_skipped = 0
    n_failed = 0
    for idx, ch in enumerate(chapters):
        out_name = f"chapter_{idx:02d}_{_slug(ch['title'])}.md"
        out_path = output_dir / out_name
        if out_path.exists():
            logger.debug("skip cached %s", out_name)
            n_skipped += 1
            continue
        try:
            data = fetch_chapter(ch["url"], session=session)
        except Exception as e:
            n_failed += 1
            logger.warning("failed %s (%s): %s", ch["title"], ch["url"], e)
            time.sleep(delay)
            continue
        md = _format_markdown(
            chapter_idx=idx,
            book_slug=book_slug,
            source_url=ch["url"],
            title=data["title"],
            body=data["body"],
            topics=topics,
            scraped_at=dt.datetime.now(dt.timezone.utc).isoformat(),
            translator=translator,
        )
        out_path.write_text(md, encoding="utf-8")
        n_persisted += 1
        logger.info("[%d/%d] saved %s (%d words)",
                    idx + 1, len(chapters), out_name, data["n_words"])
        time.sleep(delay)

    return {
        "book_url": book_url,
        "n_chapters_total": len(chapters),
        "n_persisted": n_persisted,
        "n_skipped_cached": n_skipped,
        "n_failed": n_failed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.scrape_wisdomlib",
        description="Mirror a wisdomlib.org book into the knowledge library.",
    )
    parser.add_argument(
        "--book-url", required=True,
        help="Full URL of the wisdomlib book TOC page.",
    )
    parser.add_argument(
        "--book-slug", required=True,
        help="Directory name under sources/ (e.g. 'phaladeepika', 'bphs').",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        help="Output directory (default: data/knowledge_library/sources/<book-slug>).",
    )
    parser.add_argument(
        "--topic-default", type=str, default=None,
        help="Topic-path tag added to every chapter's frontmatter.",
    )
    parser.add_argument(
        "--translator", type=str, default=None,
        help="Translator name (e.g. 'V. Subrahmanya Sastri').",
    )
    parser.add_argument("--delay", type=float, default=0.6)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    output_dir = args.output_dir or Path(f"data/knowledge_library/sources/{args.book_slug}")

    stats = run(
        args.book_url, output_dir,
        book_slug=args.book_slug,
        topic_default=args.topic_default,
        translator=args.translator,
        delay=args.delay,
        limit=args.limit,
    )
    print(
        f"Mirror complete: chapters_found={stats['n_chapters_total']} "
        f"persisted={stats['n_persisted']} cached={stats['n_skipped_cached']} "
        f"failed={stats['n_failed']} -> {output_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
