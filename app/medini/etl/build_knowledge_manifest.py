"""Walk ``data/knowledge_library/sources/`` and emit a searchable manifest parquet.

The manifest is a single Parquet with one row per artefact:

  id, source, title, author, channel, language, content_type, quality,
  scraped_at, n_words, n_chars, duration_seconds, view_count,
  source_url, local_path, topics (list[str]), classical_refs (list[str]),
  sha256

Use cases:
  - Topic-filtered retrieval: ``df[df["topics"].apply(lambda ts: "dasha.vimshottari" in ts)]``
  - De-duplication: group by sha256
  - Quality filtering: ``df[df["quality"].isin({"manual_captions", "written_article"})]``
  - Provenance auditing: every row has source_url + scraped_at

Format on disk:
  - YouTube source: a ``.json`` (yt-dlp metadata) + a ``.txt`` (transcript).
    The pair is treated as one artefact identified by the JSON's ``id`` field.
  - Markdown source: a single ``.md`` with YAML frontmatter; the frontmatter
    fields populate the manifest directly.

Topic-tagging:
  - For sources whose frontmatter declares topics, use those.
  - For YouTube videos with no frontmatter, apply the lightweight
    ``_lexicon_topic_tag()`` rule that scans title + description + first 500
    transcript chars for taxonomy keywords. This is precision-first; some
    videos may end up with empty topics if no keyword matches.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Topic lexicon — keyword → topic-path                                         #
# --------------------------------------------------------------------------- #
# Each (regex, topic_paths) entry says: if regex matches the text (title +
# description + first 500 transcript chars), add these topics. Multiple
# entries can match. Keys are *raw regex* strings, matched case-insensitively.

_TOPIC_LEXICON: list[tuple[str, list[str]]] = [
    # Primitives
    (r"\bnakshatra(s)?\b", ["primitives.nakshatras"]),
    (r"\bashwini|bharani|rohini|ardra|punarvasu|pushya|ashlesha|magha|hasta|chitra|swati|vishakha|anuradha|jyestha|moola|purvashadha|uttarashadha|shravana|dhanishta|shatabhisha|purvabhadrapada|uttarabhadrapada|revati\b", ["primitives.nakshatras"]),
    (r"\bpanchang(a)?\b|\btithi\b|\byoga(s)?\b|\bkarana\b", ["primitives.panchanga"]),
    (r"\baspect(s)?|\bdrishti\b", ["primitives.aspects"]),
    (r"\b(own|exalted|debilitated|moolatrikona)\b|\bdignity\b|\bdignit(ies|y)\b", ["primitives.dignities"]),

    # Planets
    (r"\bsun\b|\bsurya\b|\bravi\b", ["primitives.planets"]),
    (r"\bmoon\b|\bchandra\b", ["primitives.planets"]),
    (r"\bmars\b|\bmangal\b|\bkuja\b", ["primitives.planets"]),
    (r"\bmercury\b|\bbudh(a)?\b", ["primitives.planets"]),
    (r"\bjupiter\b|\bguru\b|\bbrihaspati\b", ["primitives.planets"]),
    (r"\bvenus\b|\bshukra\b", ["primitives.planets"]),
    (r"\bsaturn\b|\bshani\b", ["primitives.planets"]),
    (r"\brahu\b", ["primitives.planets"]),
    (r"\bketu\b", ["primitives.planets"]),

    # Houses — also tag chapters titled "Bhavas" or naming kendra/trikona/
    # dusthana / artha quadruplicities, which classical texts use as
    # primary terminology and which the literal "house" wouldn't catch.
    (r"\b1st house|first house|lagna\b|\bascendant\b", ["primitives.houses"]),
    (r"\b(2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th) house", ["primitives.houses"]),
    (r"\bhouses?\b|\bbhava(s)?\b|\bbhavadhipati\b", ["primitives.houses"]),
    (r"\bkendra\b|\btrikona\b|\bdusthana\b|\bupachaya\b|\bmaraka\b|\bbadhaka\b",
        ["primitives.houses"]),
    (r"\bartha\s+trikona\b|\bdharma\s+trikona\b|\bkama\s+trikona\b|\bmoksha\s+trikona\b",
        ["primitives.houses"]),

    # Strength
    (r"\bshadbala\b|\bbalas?\b", ["strength_bala.shadbala"]),

    # Divisional charts
    (r"\bnavamsa\b|\bnavamsha\b|\bd9\b|\bd-9\b", ["divisional.d9_navamsa"]),
    (r"\bdasamsa\b|\bdasamsha\b|\bd10\b|\bd-10\b", ["divisional.d10_dasamsa"]),
    (r"\bd60\b|\bshashtiamsa\b", ["divisional.d60"]),

    # Dasha — broaden to catch BPHS / Phaladeepika chapters that teach
    # the system without ever using the literal word "vimshottari". Common
    # missing tags before: chapters using "mahadasa" + "antardasa" together,
    # "udu dasa" (= nakshatra-period = vimshottari by another name),
    # and the transliteration "dasa" (no 'h').
    (r"\bvimshottari\b|\bvimsottari\b", ["dasha.vimshottari"]),
    (r"\bnakshatra\s+dasa(s)?\b|\budu\s?dasa\b|\budu-?dasha\b",
        ["dasha.vimshottari"]),
    (r"\b(?:mah[aā])?dasa\s+(?:and\s+)?antar(?:dasa|dasha)\b",
        ["dasha.vimshottari"]),
    (r"\b(120[\s-]?year|hundred(\s|\s?and\s?)twenty[\s-]?year)\s+(period|dasha|dasa|cycle)\b",
        ["dasha.vimshottari"]),
    # Per-planet mahadasha results chapters in BPHS Ch.46-47 + Phaladeepika
    # don't say "vimshottari" — they jump straight to "Effects of the Dasa
    # of X". This pattern catches those + tags them with mahadasha_results.
    (r"(?i)(effects?|results?|phala)\s+of\s+(?:the\s+)?(?:maha[\s-]?)?dasa\b",
        ["dasha.mahadasha_results", "dasha.vimshottari"]),
    (r"(?i)dasaphala\b|\bdashaphala\b|\bphal[ad]asha?\b",
        ["dasha.mahadasha_results", "dasha.vimshottari"]),

    (r"\byogini\s+dasa(?:ha)?\b|\byogini\s?dasha\b", ["dasha.yogini"]),
    (r"\bchara\s+dasa(?:ha)?\b|\bjaimini\s+dasa(?:ha)?\b",
        ["dasha.chara_jaimini"]),
    (r"\bkalachakra\b|\bkaal\s?chakra\b|\bkala-?chakra\s+dasa\b",
        ["dasha.kalachakra"]),
    (r"\bashtottari\b|\bashtotari\b", ["dasha.ashtottari"]),
    (r"\bmahadasha\b|\bmaha[\s-]?dasha\b|\bmaha[\s-]?dasa\b|\bmajor\s+period\b",
        ["dasha.mahadasha_results", "dasha.vimshottari"]),
    (r"\bantar[\s-]?dasha\b|\bantar[\s-]?dasa\b|\bbhukti\b|\bsub[\s-]?period\b",
        ["dasha.antardasha_combinations", "dasha.vimshottari"]),
    (r"\bpratyantar\b|\bpratyantar[\s-]?dasha\b|\bpratyantar[\s-]?dasa\b",
        ["dasha.pratyantar", "dasha.vimshottari"]),
    # Generic fallback — anything just saying "dasha" / "dasa" gets the
    # vimshottari tag. Has the side effect of over-tagging some non-
    # vimshottari content but that's the design tradeoff (precision-favored
    # exact patterns above, recall-fallback last).
    (r"\bdasha\b|\bdasa\b(?![a-z])", ["dasha.vimshottari"]),

    # Yogas
    (r"\braj(a)?\s?yoga\b", ["yogas.raja_yogas"]),
    (r"\bdhana\s?yoga\b", ["yogas.dhana_yogas"]),
    (r"\bvipareeta\b|\bharsha\b|\bsarala\b|\bvimala\b", ["yogas.vipareeta_raj_yogas"]),
    (r"\bpanch(a)?\s?mahapurusha\b|\bruchaka\b|\bbhadra\b|\bhamsa\b|\bmalavya\b|\bsasa\b", ["yogas.mahapurusha"]),
    (r"\bsunapha\b|\banapha\b|\bdurudhura\b|\bkemadruma\b|\bgajakesari\b", ["yogas.moon_yogas"]),
    (r"\bkal\s?sarpa\b", ["yogas.kalsarpa"]),
    (r"\bnabhasa\b", ["yogas.nabhasa"]),
    (r"\bneech\s?bhanga\b|\bcancellation of debilitation\b", ["yogas.neech_bhanga"]),

    # Predictive event classes
    (r"\bmarriage\b|\bvivah(a)?\b|\bwedding\b", ["predictive.marriage_timing"]),
    (r"\bcareer\b|\bprofession\b|\bjob\b", ["predictive.career_timing"]),
    (r"\bdeath\b|\bmrityu\b|\bayur\b|\blongevity\b", ["predictive.death_timing"]),
    (r"\bdisease\b|\billness\b|\bhealth\b", ["predictive.health_disease"]),
    (r"\bwealth\b|\bmoney\b|\bfinance\b", ["predictive.wealth"]),
    (r"\bchildren\b|\bsantana\b|\boffspring\b", ["predictive.children"]),
    (r"\btravel\b|\bforeign\b|\babroad\b", ["predictive.travel"]),

    # Remedies
    (r"\bmantra(s)?\b|\bchant(ing)?\b", ["remedies.mantras"]),
    (r"\bgem\s?stone(s)?\b|\brashi-ratna\b|\bratna\b", ["remedies.gemstones"]),
    (r"\bvrat(a)?\b|\bfast(ing)?\b", ["remedies.vrats"]),
    (r"\bdaan(a)?m?\b|\bcharity\b|\bcharitable\b", ["remedies.charitable_acts"]),

    # Techniques
    (r"\bjaimini\b", ["techniques.jaimini_principles"]),
    (r"\btajak(a)?\b|\bvarshaphala\b|\bsolar return\b|\bannual chart\b", ["techniques.varshaphala"]),
    (r"\bprashna\b|\bhorary\b", ["techniques.prashna_horary"]),
    (r"\bmundane\b|\bnational chart\b|\bingress\b", ["techniques.mundane"]),

    # Transits
    (r"\btransit(s)?\b|\bgochara\b", ["techniques.varshaphala"]),  # closest match
    (r"\bsade\s?sati\b|\bsadesati\b", ["techniques.varshaphala"]),
    (r"\bSaturn\s+return\b", ["techniques.varshaphala"]),

    # Yogas — broaden so chapters teaching the *system* of yogas (not
    # naming a single one) still get yogas.raja_yogas (the lead branch).
    (r"\byogadhipati\b|\byogakaraka\b|\bgrah[a-z]*\s+yoga\b",
        ["yogas.raja_yogas"]),
]

_COMPILED_LEXICON = [(re.compile(p, re.IGNORECASE), t) for p, t in _TOPIC_LEXICON]


def _lexicon_topic_tag(text: str) -> list[str]:
    """Return de-duplicated topic-paths whose lexicon regex matches ``text``."""
    if not text:
        return []
    matched: set[str] = set()
    for pattern, topics in _COMPILED_LEXICON:
        if pattern.search(text):
            matched.update(topics)
    return sorted(matched)


# --------------------------------------------------------------------------- #
# Frontmatter parsing                                                          #
# --------------------------------------------------------------------------- #

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(md_text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter_dict, remaining_body). Empty dict if no frontmatter."""
    m = _FRONTMATTER_RE.match(md_text)
    if not m:
        return {}, md_text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception:
        fm = {}
    body = md_text[m.end():]
    return fm, body


# --------------------------------------------------------------------------- #
# Source-specific adapters                                                     #
# --------------------------------------------------------------------------- #

def _scan_youtube_dir(youtube_dir: Path) -> list[dict[str, Any]]:
    """Pair each ``<id>.json`` (yt-dlp metadata) with its ``<id>.txt`` transcript."""
    rows: list[dict[str, Any]] = []
    for meta_path in sorted(youtube_dir.glob("*.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("could not parse %s: %s", meta_path, e)
            continue
        vid = meta.get("id") or meta_path.stem
        transcript_path = youtube_dir / f"{vid}.txt"
        transcript = transcript_path.read_text(encoding="utf-8") if transcript_path.exists() else ""
        # Topic tag from title + description + first 500 transcript chars.
        tag_text = " ".join([
            meta.get("title", "") or "",
            meta.get("description", "") or "",
            " ".join(meta.get("tags") or []),
            transcript[:500],
        ])
        topics = _lexicon_topic_tag(tag_text)
        sha = hashlib.sha256(transcript.encode("utf-8")).hexdigest()
        n_words = len(transcript.split())
        rows.append({
            "id": f"lunarastro-yt-{vid}",
            "source": "lunarastro/youtube",
            "title": meta.get("title"),
            "author": meta.get("channel"),
            "channel": meta.get("channel"),
            "language": meta.get("language"),
            "content_type": "video_transcript",
            "quality": meta.get("transcript_quality") or "none",
            "scraped_at": None,  # yt-dlp doesn't carry our scrape time
            "n_words": n_words,
            "n_chars": meta.get("transcript_chars") or len(transcript),
            "duration_seconds": meta.get("duration"),
            "view_count": meta.get("view_count"),
            "source_url": meta.get("webpage_url"),
            "local_path": str(transcript_path),
            "metadata_path": str(meta_path),
            "topics": topics,
            "classical_refs": [],
            "sha256": sha,
        })
    return rows


def _scan_markdown_tree(root: Path) -> list[dict[str, Any]]:
    """Walk a directory tree for ``.md`` artefacts and parse their frontmatter."""
    rows: list[dict[str, Any]] = []
    for md_path in sorted(root.rglob("*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning("could not read %s: %s", md_path, e)
            continue
        fm, body = _parse_frontmatter(text)
        if not fm:
            continue  # No frontmatter → don't index as artefact (likely topic README)
        # Always union frontmatter topics with the lexicon scan. Earlier this
        # was a fallback (lexicon only ran when frontmatter had zero topics),
        # but most archive.org imports come with `topics: [meta.source_texts]`
        # from the importer, which trivially passed the truthy check and
        # then masked the lexicon — so BPHS Ch.46 ("Effects of the Dasa of
        # X" with 48 dasa-mentions) only ever got the meta tag. Scan now
        # always runs and is unioned on top.
        frontmatter_topics = list(fm.get("topics") or [])
        # Lexicon scan reads title + body (truncated for perf; ~5k chars is
        # enough for the chapter's intent without scoring every word).
        lexicon_topics = _lexicon_topic_tag(
            f"{fm.get('title', '') or ''}\n{body[:5000]}"
        )
        topics = sorted(set(frontmatter_topics) | set(lexicon_topics))
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        n_words = len(body.split())
        rows.append({
            "id": fm.get("id") or md_path.stem,
            "source": fm.get("source"),
            "title": fm.get("title"),
            "author": fm.get("author"),
            "channel": fm.get("channel"),
            "language": fm.get("language"),
            "content_type": fm.get("content_type") or "markdown_article",
            "quality": fm.get("quality") or "written_article",
            "scraped_at": fm.get("scraped_at"),
            "n_words": n_words,
            "n_chars": len(body),
            "duration_seconds": None,
            "view_count": None,
            "source_url": fm.get("source_url"),
            "local_path": str(md_path),
            "metadata_path": str(md_path),
            "topics": topics,
            "classical_refs": list(fm.get("classical_refs") or []),
            "sha256": sha,
        })
    return rows


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def build_manifest(library_root: Path) -> pd.DataFrame:
    """Scan the full library and return a manifest DataFrame."""
    sources = library_root / "sources"
    rows: list[dict[str, Any]] = []

    youtube_dir = sources / "lunarastro" / "youtube"
    if youtube_dir.exists():
        n_before = len(rows)
        rows.extend(_scan_youtube_dir(youtube_dir))
        logger.info("scanned lunarastro/youtube: +%d artefacts", len(rows) - n_before)

    # Markdown trees under any source (bphs/, phaladeepika/, raman/, etc.)
    for src_dir in sources.iterdir() if sources.exists() else []:
        if not src_dir.is_dir():
            continue
        if src_dir.name == "lunarastro":
            continue  # handled above
        n_before = len(rows)
        rows.extend(_scan_markdown_tree(src_dir))
        if len(rows) > n_before:
            logger.info("scanned %s: +%d artefacts", src_dir, len(rows) - n_before)

    return pd.DataFrame(rows)


def write_manifest(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info("wrote %s (rows=%d cols=%d)", output_path, len(df), df.shape[1])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.build_knowledge_manifest",
        description="Build the searchable manifest for the knowledge library.",
    )
    parser.add_argument(
        "--library-root", type=Path,
        default=Path("data/knowledge_library"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/knowledge_library/manifest.parquet"),
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    df = build_manifest(args.library_root)
    if df.empty:
        print("WARNING: manifest is empty — no artefacts found.")
    write_manifest(df, args.output)

    # Print summary
    print(f"\n=== Manifest summary ===")
    print(f"  Total artefacts: {len(df)}")
    if not df.empty:
        print(f"  By source:")
        for src, n in df["source"].value_counts().items():
            print(f"    {src:<30} {n}")
        print(f"  By content_type:")
        for ct, n in df["content_type"].value_counts().items():
            print(f"    {ct:<30} {n}")
        print(f"  By transcript quality:")
        for q, n in df["quality"].value_counts().items():
            print(f"    {q:<30} {n}")
        # Top topics
        all_topics: list[str] = []
        for ts in df["topics"]:
            all_topics.extend(ts)
        if all_topics:
            from collections import Counter
            top = Counter(all_topics).most_common(15)
            print(f"  Top topics tagged:")
            for topic, n in top:
                print(f"    {topic:<35} {n}")
        print(f"  Total words: {int(df['n_words'].sum()):,}")
        print(f"  Output: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
