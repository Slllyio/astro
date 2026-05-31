"""Extract Nadi corpus from local sources into JSONL leaves (N-1).

We have several Nadi-tradition texts already scraped in
``data/knowledge_library/sources/``:

  * saptarishi_nadi_aries/         — Saptarishi Nadi (Aries Asc collection)
  * brighu_nadi_sangraha/          — Bhrigu Nadi Sangraha
  * chandrakala_nadi_full/         — Chandra Kala Nadi
  * deva_keralam_vol1/2/3/         — Deva Keralam (a primary Nadi text)
  * nadi_jyothisha_v1/v2/, nadi_jyotisha_vol1/ — Three Nadi Jyotisha vols
  * nadi_astrological_researches/  — research compilation

This ETL parses the structured horoscopes out of these markdown files
into a JSONL corpus that ``app/core/nadi_lookup.py`` can load. Each
output line is one Nadi "leaf":

  {
    "source": "saptarishi_nadi_aries",
    "horoscope_id": 1,
    "chart": {
      "asc_sign": 1,
      "planet_signs": {"Sun": 8, "Moon": 6, "Mars": 11, ...}
    },
    "events": {"Marriage": 18, "Father's death": 37, ...},
    "dasa_at_birth": "Mars dasa, 6 years 2 months",
    "raw_text": "(the surrounding paragraph for provenance)"
  }

This is REAL Nadi data — not synthetic. Predictions are tied to
SPECIFIC chart patterns from palm-leaf transcripts. The lookup contract
in nadi_lookup.py becomes meaningful once this corpus loads.

## OCR caveats

These are OCR'd from palm-leaf manuscripts then English-translated.
The OCR has noise (Tamil interspersed, broken layout, page-number
artifacts). The extractor skips any horoscope where:

  * Fewer than 6 of 9 grahas can be parsed (insufficient pattern key)
  * Lagna sign can't be determined

So the output is a SUBSET of leaves where the chart is cleanly
extractable.

Usage:
    python -m app.medini.etl.extract_nadi_corpus
    python -m app.medini.etl.extract_nadi_corpus --source saptarishi_nadi_aries
    python -m app.medini.etl.extract_nadi_corpus --dry-run
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
DEFAULT_OUTPUT: Final = Path("data/knowledge_library/nadi_corpus.jsonl")

# Sources known to have horoscope-by-horoscope structure
NADI_SOURCES: Final[tuple[str, ...]] = (
    "saptarishi_nadi_aries",
    "brighu_nadi_sangraha",
    "chandrakala_nadi_full",
    "deva_keralam_vol1",
    "deva_keralam_vol2",
    "deva_keralam_vol3",
)

# Sign name → 1..12
_SIGN_NAMES: Final[dict[str, int]] = {
    "aries": 1, "taurus": 2, "gemini": 3, "cancer": 4,
    "leo": 5, "virgo": 6, "libra": 7, "scorpio": 8,
    "sagittarius": 9, "capricorn": 10, "aquarius": 11, "pisces": 12,
}

# Planet name normalisation (Nadi texts use varied spellings)
_PLANET_NORMS: Final[dict[str, str]] = {
    "sun": "Sun", "surya": "Sun", "ravi": "Sun",
    "moon": "Moon", "chandra": "Moon", "luna": "Moon",
    "mars": "Mars", "mangal": "Mars", "kuja": "Mars",
    "mercury": "Mercury", "budha": "Mercury",
    "jupiter": "Jupiter", "guru": "Jupiter", "brihaspati": "Jupiter",
    "venus": "Venus", "shukra": "Venus", "sukra": "Venus",
    "saturn": "Saturn", "shani": "Saturn", "sani": "Saturn",
    "rahu": "Rahu",
    "ketu": "Ketu",
}


@dataclass
class NadiLeaf:
    """One extracted Nadi-leaf record."""
    source: str
    horoscope_id: int
    asc_sign: int | None = None
    planet_signs: dict[str, int] = field(default_factory=dict)
    events: dict[str, int] = field(default_factory=dict)
    dasa_at_birth: str = ""
    raw_text: str = ""


# ─── Parsing helpers ────────────────────────────────────────────────


# Match "(planet[, planet ...] (is|are)) in (sign)" patterns. Greedy on planet
# list, captures sign name.
_PLANET_LIST_RE = re.compile(
    r"(?:^|[.\s,])([A-Z][a-z]+(?:\s+(?:and|,)\s+[A-Z][a-z]+)*)"
    r"\s+(?:is|are)\s+in\s+([A-Z][a-z]+)",
    re.MULTILINE,
)

# Match the standalone ascendant line: "The ascendant is X" or "Ascendant: X"
_ASC_RE = re.compile(
    r"(?:The\s+ascendant\s+is|Ascendant:?)\s+([A-Z][a-z]+)",
    re.IGNORECASE,
)

# Event-timing table: a row like "Marriage 18" or "Jataka's death 54"
# We match a label followed by a small integer (1..120 for ages)
_EVENT_RE = re.compile(
    r"^([A-Z][\w'\s]{2,30}?)\s+(\d{1,3})\s*$",
    re.MULTILINE,
)


def _extract_chart_from_text(text: str) -> tuple[int | None, dict[str, int]]:
    """Parse a Nadi horoscope chart paragraph into (asc_sign, planet_signs).

    Returns (None, {}) when nothing clean was found.
    """
    asc_sign: int | None = None
    planet_signs: dict[str, int] = {}

    # Find the Lagna
    asc_match = _ASC_RE.search(text)
    if asc_match:
        sign_name = asc_match.group(1).lower()
        asc_sign = _SIGN_NAMES.get(sign_name)

    # Find all "(planets) in (sign)" claims
    for m in _PLANET_LIST_RE.finditer(text):
        planet_list_str = m.group(1)
        sign_name = m.group(2).lower()
        sign = _SIGN_NAMES.get(sign_name)
        if sign is None:
            continue
        # Split planet list on "and" or ","
        for part in re.split(r"\s+and\s+|,\s+", planet_list_str):
            part_norm = part.strip().lower()
            planet = _PLANET_NORMS.get(part_norm)
            if planet:
                planet_signs[planet] = sign

    return (asc_sign, planet_signs)


def _extract_events_from_text(text: str) -> dict[str, int]:
    """Parse 'Event: age' rows from a horoscope's timing table."""
    events: dict[str, int] = {}
    for m in _EVENT_RE.finditer(text):
        label = m.group(1).strip()
        try:
            age = int(m.group(2))
            # Ages typically 1..120; reject obvious page-number / OCR junk
            if 1 <= age <= 120 and len(label) > 2:
                events[label] = age
        except (ValueError, TypeError):
            continue
    return events


def _extract_dasa_from_text(text: str) -> str:
    """Find the 'X dasa, Y years Z months' line if present."""
    m = re.search(
        r"([A-Z][a-z]+)\s+dasa,?\s+(\d+\s+years?(?:\s+\d+\s+months?)?)",
        text,
    )
    if m:
        return f"{m.group(1)} dasa, {m.group(2)}"
    return ""


# ─── Bhrigu rule-extractor (different format from horoscope-leaves) ──


# Bhrigu Nadi Sangraha is structured as CONDITIONAL RULES not horoscope
# examples. Each rule says "(planetary condition) -> (outcome)". The
# rule format is more like classical-doctrine shloka than Nadi-leaf.
# We extract these as a separate corpus: bhrigu_rules.jsonl.

@dataclass
class BhriguRule:
    """One Bhrigu Nadi conditional rule."""
    source: str
    rule_id: int
    condition: str               # "When Saturn touches 8th from Sun in 2nd transit"
    outcome: str                 # "death of the father of the native is denoted"
    raw_text: str                # the whole sentence for provenance


# Sentences with this pattern are likely Bhrigu rules. We require:
#   - mentions a planet name early
#   - contains a "shows / denotes / will be / occurs / is denoted" verb
_BHRIGU_RULE_VERBS = (
    "shows", "denotes", "will be", "occurs", "is denoted",
    "is signified", "will have", "indicates", "gives", "becomes",
    "is going to", "you can be sure",
)


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs (multiple consecutive newlines)."""
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _is_bhrigu_rule_sentence(s: str) -> bool:
    """Heuristic: sentence mentions a planet AND a rule-verb in ≤300 chars."""
    if len(s) < 30 or len(s) > 400:
        return False
    s_lower = s.lower()
    # Must mention at least one classical planet
    planets_mentioned = sum(
        1 for p in ("sun", "moon", "mars", "mercury", "jupiter",
                    "venus", "saturn", "rahu", "ketu")
        if p in s_lower
    )
    if planets_mentioned < 1:
        return False
    # Must contain a rule-verb
    if not any(v in s_lower for v in _BHRIGU_RULE_VERBS):
        return False
    # Skip TOC / header noise
    if any(noise in s_lower for noise in
           ("contents", "table of", "chapter", "page no",
            "copyright", "all rights", "publisher", "translated by")):
        return False
    return True


def _split_into_sentences(text: str) -> list[str]:
    """Split on . / ! / ? followed by whitespace + capital letter."""
    # Simple heuristic — Bhrigu's sentences are short, period-delimited
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [s.strip() for s in sentences if s.strip()]


def extract_bhrigu_rules(source_name: str, file_path: Path) -> list[BhriguRule]:
    """Extract conditional-rule sentences from a Bhrigu-style Nadi text."""
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    paragraphs = _split_paragraphs(text)
    rules: list[BhriguRule] = []
    rule_id = 0
    for para in paragraphs:
        for s in _split_into_sentences(para):
            if not _is_bhrigu_rule_sentence(s):
                continue
            # Split rule into condition + outcome on common rule-conjunctions
            # The simplest split: find a verb like "shows / denotes / is denoted"
            # and split there
            condition = s
            outcome = ""
            for verb in _BHRIGU_RULE_VERBS:
                m = re.search(rf"\b{re.escape(verb)}\b", s, re.IGNORECASE)
                if m:
                    condition = s[: m.start()].strip(" ,;:-")
                    outcome = s[m.start():].strip()
                    break
            rule_id += 1
            rules.append(BhriguRule(
                source=source_name, rule_id=rule_id,
                condition=condition[:300],
                outcome=outcome[:300] if outcome else s[:300],
                raw_text=s[:500],
            ))
    return rules


def _split_into_horoscope_sections(text: str) -> list[tuple[int, str]]:
    """Split a Nadi text into (horoscope_id, section_text) pairs.

    A section runs from one 'Horoscope N' header to the next.
    """
    pattern = re.compile(
        r"^Horoscope\s+(\d{1,3})\s*$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    sections: list[tuple[int, str]] = []
    for i, m in enumerate(matches):
        hid = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((hid, text[start:end]))
    return sections


def extract_from_file(source_name: str, file_path: Path) -> list[NadiLeaf]:
    """Extract all parseable Nadi leaves from one markdown source file."""
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    sections = _split_into_horoscope_sections(text)
    # Skip the TOC-style early sections — they list horoscope summaries
    # without the full chart paragraph. Keep horoscopes that occurred
    # at least twice in the file (TOC + content).
    seen_ids: dict[int, int] = {}
    for hid, _ in sections:
        seen_ids[hid] = seen_ids.get(hid, 0) + 1

    leaves: list[NadiLeaf] = []
    handled_ids: set[int] = set()
    for hid, section_text in sections:
        if hid in handled_ids:
            continue
        # If this id appeared twice (TOC + content), prefer the LATER occurrence
        # which usually has the chart paragraph.
        if seen_ids.get(hid, 0) > 1:
            later_sections = [
                (h, t) for h, t in sections if h == hid
            ]
            if len(later_sections) >= 2:
                section_text = later_sections[-1][1]
        handled_ids.add(hid)

        asc, planets = _extract_chart_from_text(section_text)
        events = _extract_events_from_text(section_text)
        dasa = _extract_dasa_from_text(section_text)

        # Quality gate: need Lagna + ≥6 planet placements
        if asc is None or len(planets) < 6:
            continue

        leaves.append(NadiLeaf(
            source=source_name,
            horoscope_id=hid,
            asc_sign=asc,
            planet_signs=planets,
            events=events,
            dasa_at_birth=dasa,
            raw_text=section_text[:600].strip(),
        ))
    return leaves


def extract_all(
    knowledge_dir: Path, output_path: Path,
    sources: tuple[str, ...] = NADI_SOURCES,
    *, dry_run: bool = False,
) -> tuple[int, int]:
    """Extract all available Nadi sources to one JSONL file.

    Returns (n_leaves_extracted, n_sources_processed).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_leaves: list[NadiLeaf] = []
    n_sources_processed = 0

    for source_name in sources:
        source_dir = knowledge_dir / source_name
        if not source_dir.is_dir():
            logger.info("Source missing on disk: %s", source_name)
            continue
        md_files = sorted(source_dir.glob("*.md"))
        if not md_files:
            logger.info("No .md files in %s", source_dir)
            continue
        n_sources_processed += 1
        source_leaves = 0
        for md_file in md_files:
            try:
                leaves = extract_from_file(source_name, md_file)
                all_leaves.extend(leaves)
                source_leaves += len(leaves)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to parse %s: %s", md_file, exc)
        logger.info("%-30s  %d leaves extracted", source_name, source_leaves)

    if not dry_run:
        with output_path.open("w", encoding="utf-8") as fh:
            for leaf in all_leaves:
                fh.write(json.dumps(asdict(leaf), ensure_ascii=False) + "\n")
        logger.info("Wrote %d leaves to %s", len(all_leaves), output_path)
    else:
        logger.info("DRY RUN — would write %d leaves to %s",
                    len(all_leaves), output_path)

    return (len(all_leaves), n_sources_processed)


def extract_bhrigu_all(
    knowledge_dir: Path, output_path: Path,
    *, dry_run: bool = False,
) -> int:
    """Extract Bhrigu-style rule corpus from rule-format Nadi texts."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Sources that use rule-format (not horoscope-format)
    rule_sources = ("brighu_nadi_sangraha",)
    all_rules: list[BhriguRule] = []
    for source_name in rule_sources:
        source_dir = knowledge_dir / source_name
        if not source_dir.is_dir():
            logger.info("Rule source missing on disk: %s", source_name)
            continue
        for md_file in sorted(source_dir.glob("*.md")):
            try:
                rules = extract_bhrigu_rules(source_name, md_file)
                all_rules.extend(rules)
                logger.info("%-30s  %d rules extracted", source_name, len(rules))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to parse %s: %s", md_file, exc)

    if not dry_run:
        with output_path.open("w", encoding="utf-8") as fh:
            for rule in all_rules:
                fh.write(json.dumps(asdict(rule), ensure_ascii=False) + "\n")
        logger.info("Wrote %d Bhrigu rules to %s", len(all_rules), output_path)
    else:
        logger.info("DRY RUN — would write %d Bhrigu rules", len(all_rules))
    return len(all_rules)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-dir", type=Path, default=KNOWLEDGE_LIBRARY_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bhrigu-output", type=Path,
                        default=Path("data/knowledge_library/bhrigu_rules.jsonl"),
                        help="Output JSONL for Bhrigu rule-format extraction.")
    parser.add_argument("--source", type=str, default=None,
                        help="Process only this one source (horoscope-format only).")
    parser.add_argument("--skip-bhrigu", action="store_true",
                        help="Skip the Bhrigu rule extraction.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    if args.source:
        sources = (args.source,)
    else:
        sources = NADI_SOURCES

    n_leaves, n_sources = extract_all(
        args.knowledge_dir, args.output, sources, dry_run=args.dry_run,
    )
    logger.info("Horoscope-format: %d leaves across %d sources",
                n_leaves, n_sources)

    if not args.skip_bhrigu:
        n_rules = extract_bhrigu_all(
            args.knowledge_dir, args.bhrigu_output, dry_run=args.dry_run,
        )
        logger.info("Rule-format (Bhrigu): %d rules", n_rules)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
