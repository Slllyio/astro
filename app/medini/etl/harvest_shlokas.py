"""Classical shloka harvester (S-H) — multi-source rule extraction.

The Translation Engine cites ~50 unique classical references across its
27 records, but we have 88 source-text directories — many with scraped
content we never extracted into the rule-corpus pipeline. This module
harvests RULE-STATEMENT sentences from the foundational classical texts:

  * brihat_jataka (Varahamihira)        — 19 chapters / 19K lines
  * brihat_samhita_iyer                  — 59 chapters / 18K lines
  * saravali (Kalyana Varma)             — 55 chapters / 11K lines
  * phaladeepika (Mantreshvara)          — 34 chapters / 15K lines
  * crux_of_vedic_astrology_rath         — 1 file / 24K lines
  * advance_techniques_kn_rao            — KN Rao patterns
  * studies_jaimini_raman                — Jaimini Sutras + commentary

Plus optional secondary:
  * fundamentals_vedic_astrology
  * fundamentals_vedic_behari_v1
  * ashtakavarga_patel
  * art_practice_braha
  * jaimini_sutras
  * astrology_seers_frawley
  * etc.

## Output format

JSONL at `data/knowledge_library/classical_shloka_rules.jsonl`. One
line per extracted rule:

  {
    "source": "brihat_jataka",
    "chapter": "chapter_007",
    "rule_id": 142,
    "condition": "Mars in 7H aspected by Saturn",
    "outcome": "marital discord and delay in marriage",
    "topics": ["marriage", "Mars", "Saturn"],
    "raw_text": "(full sentence for provenance)"
  }

Consumed by ``app.core.shloka_lookup`` for per-domain pattern queries
alongside the Nadi corpus.

## Quality caveats

  * OCR-extracted text has noise (broken lines, Tamil/Sanskrit mixed in)
  * Some rule sentences are TOC entries or commentary not actual shlokas
  * The rule-detection regex is permissive; downstream consumers should
    treat each rule as "candidate doctrinal pattern" not "verified shloka"
  * For the Translation Engine canonical 27 records, consult that registry
    directly — it has cleaner provenance per record

Usage:
    python -m app.medini.etl.harvest_shlokas
    python -m app.medini.etl.harvest_shlokas --source brihat_jataka
    python -m app.medini.etl.harvest_shlokas --dry-run
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

KNOWLEDGE_LIBRARY_DIR: Final = Path("data/knowledge_library/sources")
DEFAULT_OUTPUT: Final = Path("data/knowledge_library/classical_shloka_rules.jsonl")

# Sources with substantial scraped content for shloka harvesting.
# Ranked roughly by classical authority (BPHS/Phaladeepika/Brihat Jataka first).
SHLOKA_SOURCES: Final[tuple[str, ...]] = (
    "brihat_jataka",                 # 19K lines
    "phaladeepika",                  # 15K lines
    "brihat_samhita_iyer",           # 18K lines
    "saravali",                      # 11K lines
    "crux_of_vedic_astrology_rath",  # 24K lines
    "advance_techniques_kn_rao",
    "studies_jaimini_raman",
    "jaimini_sutras",
    "ashtakavarga_patel",
    "art_practice_braha",
    "fundamentals_vedic_astrology",
    "fundamentals_vedic_behari_v1",
    "astrology_seers_frawley",
)


@dataclass
class ShlokaRule:
    """One extracted classical pattern-rule."""
    source: str
    chapter: str                     # filename without .md
    rule_id: int
    condition: str
    outcome: str
    topics: list[str] = field(default_factory=list)
    raw_text: str = ""


# ─── Pattern detection ──────────────────────────────────────────────


# Classical-rule verbs that signal an outcome-statement
_RULE_VERBS: Final[tuple[str, ...]] = (
    "indicates", "denotes", "signifies", "shows",
    "produces", "gives", "confers", "bestows",
    "leads to", "results in", "causes",
    "is denoted", "is indicated", "is signified",
    "will be", "will have", "will get", "will obtain",
    "becomes", "the native becomes",
    "the person will", "the native will",
    "the native is", "one becomes",
    "will suffer", "will lose",
)

# Planet/house/sign tokens that mark a sentence as doctrinal
_DOCTRINAL_TOKENS: Final[frozenset[str]] = frozenset({
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
    "rahu", "ketu",
    "surya", "chandra", "kuja", "budha", "guru", "shukra", "shani",
    "lagna", "ascendant", "lord", "house", "bhava",
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    "aspect", "drishti", "conjunct", "exalted", "debilitated",
    "navamsha", "navamsa", "dasamsa", "trimsamsa",
})

# Domain keywords for topic tagging
_DOMAIN_KEYWORDS: Final[dict[str, frozenset[str]]] = {
    "marriage": frozenset({"marriage", "wife", "husband", "spouse", "wedding",
                            "vivaha", "kalathra", "partner"}),
    "wealth":   frozenset({"wealth", "money", "riches", "fortune", "dhana",
                            "lakshmi", "prosperity", "income"}),
    "career":   frozenset({"career", "profession", "occupation", "rajya",
                            "service", "employment", "business", "trade"}),
    "children": frozenset({"children", "son", "daughter", "putra", "santana",
                            "progeny", "issue"}),
    "health":   frozenset({"health", "disease", "illness", "roga", "ailment",
                            "fever", "suffering", "weakness"}),
    "longevity": frozenset({"longevity", "death", "lifespan", "age", "long life",
                            "ayur", "ayus", "mrityu"}),
    "father":   frozenset({"father", "pitru", "paternal", "father's"}),
    "mother":   frozenset({"mother", "matri", "maternal", "mother's"}),
    "education": frozenset({"education", "learning", "study", "knowledge",
                             "vidya", "scholar"}),
    "travel":   frozenset({"travel", "journey", "foreign", "abroad", "yatra",
                            "pilgrimage"}),
    "dharma":   frozenset({"dharma", "righteousness", "virtue", "religious",
                            "spiritual", "moksha"}),
}


def _planets_mentioned(text_lower: str) -> set[str]:
    """Which planets does this sentence mention?"""
    found = set()
    aliases = {
        "sun": "Sun", "surya": "Sun", "ravi": "Sun",
        "moon": "Moon", "chandra": "Moon",
        "mars": "Mars", "kuja": "Mars", "mangal": "Mars",
        "mercury": "Mercury", "budha": "Mercury",
        "jupiter": "Jupiter", "guru": "Jupiter", "brihaspati": "Jupiter",
        "venus": "Venus", "shukra": "Venus", "sukra": "Venus",
        "saturn": "Saturn", "shani": "Saturn",
        "rahu": "Rahu", "ketu": "Ketu",
    }
    for alias, canon in aliases.items():
        if re.search(rf"\b{alias}\b", text_lower):
            found.add(canon)
    return found


def _tag_domains(text_lower: str) -> list[str]:
    """Return list of domain tags that match this rule."""
    return sorted([
        domain for domain, kws in _DOMAIN_KEYWORDS.items()
        if any(kw in text_lower for kw in kws)
    ])


def _is_shloka_rule_sentence(s: str) -> bool:
    """Heuristic: sentence is a doctrinal rule."""
    if len(s) < 25 or len(s) > 500:
        return False
    s_lower = s.lower()
    # Must mention at least one doctrinal token
    if not any(tok in s_lower for tok in _DOCTRINAL_TOKENS):
        return False
    # Must contain a rule-verb
    if not any(v in s_lower for v in _RULE_VERBS):
        return False
    # Skip TOC / header / commentary noise
    skip_markers = (
        "table of contents", "contents:", "preface", "foreword",
        "copyright", "all rights reserved", "publisher", "isbn",
        "translator's note", "introduction to chapter",
        "see chapter", "see section", "page no", "footnote",
    )
    if any(noise in s_lower for noise in skip_markers):
        return False
    # Skip short fragments that are sub-headings
    if s.endswith(":") and len(s) < 60:
        return False
    return True


def _split_into_sentences(text: str) -> list[str]:
    """Split on sentence-end punctuation."""
    # Collapse internal newlines within paragraphs first
    text = re.sub(r"(?<=[a-z])\n(?=[a-z])", " ", text)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [s.strip() for s in sentences if s.strip()]


def _split_condition_outcome(s: str) -> tuple[str, str]:
    """Split a rule sentence at the rule-verb into condition/outcome."""
    for verb in _RULE_VERBS:
        m = re.search(rf"\b{re.escape(verb)}\b", s, re.IGNORECASE)
        if m:
            cond = s[: m.start()].strip(" ,;:-")
            outc = s[m.start():].strip()
            return (cond[:300], outc[:300])
    return (s[:300], "")


def extract_from_file(source_name: str, file_path: Path) -> list[ShlokaRule]:
    """Extract candidate shloka-rules from one markdown file."""
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    chapter = file_path.stem
    rules: list[ShlokaRule] = []
    rule_id = 0
    for s in _split_into_sentences(text):
        if not _is_shloka_rule_sentence(s):
            continue
        rule_id += 1
        cond, outc = _split_condition_outcome(s)
        s_lower = s.lower()
        topics = _tag_domains(s_lower)
        # Also add planet names to topics for downstream filtering
        topics.extend(sorted(_planets_mentioned(s_lower)))
        rules.append(ShlokaRule(
            source=source_name, chapter=chapter, rule_id=rule_id,
            condition=cond, outcome=outc, topics=topics,
            raw_text=s[:500],
        ))
    return rules


def extract_all(
    knowledge_dir: Path, output_path: Path,
    sources: tuple[str, ...] = SHLOKA_SOURCES,
    *, dry_run: bool = False,
) -> int:
    """Harvest shlokas from all foundational sources to a single JSONL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_rules: list[ShlokaRule] = []
    for source_name in sources:
        source_dir = knowledge_dir / source_name
        if not source_dir.is_dir():
            logger.info("Source missing on disk: %s", source_name)
            continue
        md_files = sorted(source_dir.glob("*.md"))
        if not md_files:
            logger.info("No .md files in %s", source_dir)
            continue
        source_rules = 0
        for md_file in md_files:
            try:
                rules = extract_from_file(source_name, md_file)
                # Re-number rule_ids globally per source
                for r in rules:
                    r.rule_id = len(all_rules) + 1
                    all_rules.append(r)
                source_rules += len(rules)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to parse %s: %s", md_file, exc)
        logger.info("%-34s  %5d rules harvested", source_name, source_rules)

    if not dry_run:
        with output_path.open("w", encoding="utf-8") as fh:
            for rule in all_rules:
                fh.write(json.dumps(asdict(rule), ensure_ascii=False) + "\n")
        logger.info("Wrote %d shloka rules to %s", len(all_rules), output_path)
    else:
        logger.info("DRY RUN — would write %d rules", len(all_rules))
    return len(all_rules)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-dir", type=Path, default=KNOWLEDGE_LIBRARY_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source", type=str, default=None,
                        help="Process only this one source.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    if args.source:
        sources = (args.source,)
    else:
        sources = SHLOKA_SOURCES

    n = extract_all(args.knowledge_dir, args.output, sources, dry_run=args.dry_run)
    logger.info("DONE: %d shloka rules harvested", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
