"""Lagna-keyed Nadi context extractor (N-3).

The original Nadi extractor (`extract_nadi_corpus.py`, N-1) extracts
horoscope-format Saptarishi leaves — yielded 37 leaves, all Aries-Lagna
(because Saptarishi-Nadi-Aries is the only horoscope-by-horoscope text
we have).

But Deva Keralam vol 1-3 + several other Nadi texts contain over 1,600
Lagna-mention contexts across ALL 12 ascendants:

   vol1: Ari 29 Tau 35 Gem 13 Can 31 Leo 8 Vir 6 Lib 54 Sco 36 Sag 54 Cap 67 Aqu 51 Pis 48
   vol2: Ari 13 Tau 13 Gem 111 Can 32 Leo 92 Vir 2 Lib 133 Sco 38 Sag 11 Cap 74 Aqu 71 Pis 26
   vol3: Ari 31 Tau 28 Gem 46 Can 43 Leo 37 Vir 5 Lib 80 Sco 111 Sag 60 Cap 49 Aqu 34 Pis 35

These contexts aren't full horoscopes but they ARE Lagna-specific Nadi
pattern statements — exactly what `lookup_nadi_pattern()` queries on
ASC sign. By extracting them as a SECONDARY corpus we close the
"only Aries Lagna" gap that was blocking the master-reading framework.

Each output record:
  {
    "source": "deva_keralam_vol1",
    "context_id": 42,
    "asc_sign": 8,
    "nadiamsa": "Sudha",          # if mentioned in the context
    "context_text": "...500-2000 char window around the Lagna mention",
    "tradition": "Deva Keralam (Chandra Kala Nadi)",
    "extraction_format": "lagna_keyed_context",
  }

We write to ``data/knowledge_library/nadi_lagna_contexts.jsonl`` (sibling
to nadi_corpus.jsonl, kept distinct so the lookup contract for full
horoscope leaves stays clean).

Usage:
    python -m app.medini.etl.extract_nadi_lagna_contexts
    python -m app.medini.etl.extract_nadi_lagna_contexts --source deva_keralam_vol1
    python -m app.medini.etl.extract_nadi_lagna_contexts --window-chars 1500
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR: Final = Path("data/knowledge_library/sources")
DEFAULT_OUTPUT: Final = Path("data/knowledge_library/nadi_lagna_contexts.jsonl")

# Nadi sources that carry Lagna-keyed predictions worth harvesting.
# Filtered to texts that actually USE per-Lagna section structure or
# heavy per-Lagna mentions. Source names match knowledge-library dirs.
LAGNA_NADI_SOURCES: Final[tuple[str, ...]] = (
    "deva_keralam_vol1",
    "deva_keralam_vol2",
    "deva_keralam_vol3",
    "horoscope_saptarishi_nadi",
    "jyotish_saptarishi_nadi",
    "nadi_jyothisha_v1",
    "nadi_jyothisha_v2",
    "nadi_jyotisha_vol1",
    "chandra_nadi_tsgk",
    "chandrakala_nadi_full",
    "nadi_astrological_researches",
    "decoding_nadiamsha",
    "meena_nadi",
)

# Tradition attribution for each source.
_TRADITION: Final[dict[str, str]] = {
    "deva_keralam_vol1": "Deva Keralam (Chandra Kala Nadi) Vol I",
    "deva_keralam_vol2": "Deva Keralam (Chandra Kala Nadi) Vol II",
    "deva_keralam_vol3": "Deva Keralam (Chandra Kala Nadi) Vol III",
    "horoscope_saptarishi_nadi": "Saptarishi Nadi Horoscopes",
    "jyotish_saptarishi_nadi": "Jyotish Saptarishi Nadi",
    "nadi_jyothisha_v1": "Nadi Jyothisha Stellar System v1",
    "nadi_jyothisha_v2": "Nadi Jyothisha Stellar System v2",
    "nadi_jyotisha_vol1": "Nadi Jyotisha Vol I",
    "chandra_nadi_tsgk": "Chandra Nadi (TSGK)",
    "chandrakala_nadi_full": "Chandra Kala Nadi",
    "nadi_astrological_researches": "Nadi Astrological Researches",
    "decoding_nadiamsha": "Decoding Nadiamsha",
    "meena_nadi": "Meena Nadi",
}

# Sign name → 1..12. Includes Sanskrit + English forms.
_SIGN_NAMES: Final[dict[str, int]] = {
    "mesha": 1, "aries": 1,
    "vrishabha": 2, "vrish": 2, "vrishaba": 2, "rishabha": 2, "taurus": 2,
    "mithuna": 3, "gemini": 3,
    "kataka": 4, "karka": 4, "karkataka": 4, "cancer": 4,
    "simha": 5, "sinha": 5, "leo": 5,
    "kanya": 6, "virgo": 6,
    "tula": 7, "thula": 7, "libra": 7,
    "vrischika": 8, "vrischik": 8, "vrishchika": 8, "scorpio": 8,
    "dhanus": 9, "dhanur": 9, "sagittarius": 9,
    "makara": 10, "capricorn": 10,
    "kumbha": 11, "aquarius": 11,
    "meena": 12, "mina": 12, "pisces": 12,
}

# Compile the regex once. Sorted longest-first so e.g. "Vrischika" matches
# before "Vrish".
_SIGN_PATTERN = re.compile(
    r"\b(" + "|".join(sorted(_SIGN_NAMES, key=len, reverse=True)) + r")\s+"
    r"(?:Lagna|Ascendant|Asc|lagna|ascendant)\b",
    re.IGNORECASE,
)

# Nadiamsa detector (Deva Keralam structure: "X Lagna - Y Nadiamsa")
_NADIAMSA_PATTERN = re.compile(
    r"-\s*([A-Za-z]+)\s+Nadi[ -]?amsa", re.IGNORECASE,
)

# Skip contexts < this many chars (likely TOC entries with no real content)
_MIN_CONTEXT_CHARS = 150


@dataclass
class LagnaContext:
    """One Lagna-keyed Nadi context record."""
    source: str
    context_id: int
    asc_sign: int
    asc_sign_name: str
    nadiamsa: str | None
    context_text: str
    tradition: str
    extraction_format: str = "lagna_keyed_context"
    chapter_id: str | None = None


def _extract_from_text(
    source: str, text: str, window_chars: int,
) -> list[LagnaContext]:
    """Pull every Lagna-mention context out of one source's text."""
    out: list[LagnaContext] = []
    tradition = _TRADITION.get(source, source)
    seen_contexts: set[tuple[int, str]] = set()  # dedup by (asc_sign, snippet-key)

    for ctx_id, m in enumerate(_SIGN_PATTERN.finditer(text)):
        sign_token = m.group(1).lower()
        asc_sign = _SIGN_NAMES.get(sign_token)
        if not asc_sign:
            continue

        start = max(0, m.start() - window_chars // 4)
        end = min(len(text), m.end() + (3 * window_chars) // 4)
        ctx = text[start:end]

        # Clean up whitespace; collapse multi-space + linebreaks
        ctx_clean = " ".join(ctx.split())
        if len(ctx_clean) < _MIN_CONTEXT_CHARS:
            continue

        # Dedup: use first 80 chars as key
        key = (asc_sign, ctx_clean[:80])
        if key in seen_contexts:
            continue
        seen_contexts.add(key)

        # Try to extract the Nadiamsa name if present in this context
        nadiamsa = None
        nm = _NADIAMSA_PATTERN.search(ctx)
        if nm:
            nadiamsa = nm.group(1)

        # Capitalised sign-name for human display
        sign_display = {
            1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer",
            5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio",
            9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces",
        }[asc_sign]

        out.append(LagnaContext(
            source=source,
            context_id=ctx_id,
            asc_sign=asc_sign,
            asc_sign_name=sign_display,
            nadiamsa=nadiamsa,
            context_text=ctx_clean,
            tradition=tradition,
        ))
    return out


def extract_source(
    source: str, window_chars: int = 1200,
) -> list[LagnaContext]:
    """Extract Lagna-contexts from one knowledge-library source directory."""
    src_dir = KNOWLEDGE_DIR / source
    if not src_dir.is_dir():
        logger.warning("Source dir missing: %s", src_dir)
        return []

    md_files = sorted(src_dir.glob("*.md"))
    if not md_files:
        logger.warning("No .md files in %s", src_dir)
        return []

    all_contexts: list[LagnaContext] = []
    for md in md_files:
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            logger.warning("Read failed for %s: %s", md, exc)
            continue

        # Strip frontmatter if present (between --- ... ---)
        if text.startswith("---"):
            end_fm = text.find("\n---\n", 4)
            if end_fm > 0:
                text = text[end_fm + 5:]

        ctxs = _extract_from_text(source, text, window_chars)
        # Annotate chapter id so we keep provenance
        for c in ctxs:
            c.chapter_id = md.stem
        all_contexts.extend(ctxs)

    return all_contexts


def extract_all(window_chars: int = 1200) -> list[LagnaContext]:
    """Extract from every registered Lagna-Nadi source."""
    out: list[LagnaContext] = []
    for source in LAGNA_NADI_SOURCES:
        ctxs = extract_source(source, window_chars=window_chars)
        logger.info("%-32s %5d contexts extracted", source, len(ctxs))
        out.extend(ctxs)
    return out


def write_jsonl(contexts: list[LagnaContext], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for ctx in contexts:
            d = asdict(ctx)
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    logger.info("Wrote %d Lagna contexts to %s", len(contexts), out_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="Single source slug; default = all")
    parser.add_argument("--window-chars", type=int, default=1200,
                        help="Context window around Lagna mention (default 1200)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    if args.source:
        contexts = extract_source(args.source, window_chars=args.window_chars)
    else:
        contexts = extract_all(window_chars=args.window_chars)

    # Coverage summary
    from collections import Counter
    sign_counts = Counter(c.asc_sign for c in contexts)
    src_counts = Counter(c.source for c in contexts)
    logger.info("Lagna distribution (sign:count):")
    for s in range(1, 13):
        logger.info("  %2d (%-11s): %d", s,
                    {1:"Aries",2:"Taurus",3:"Gemini",4:"Cancer",5:"Leo",
                     6:"Virgo",7:"Libra",8:"Scorpio",9:"Sagittarius",
                     10:"Capricorn",11:"Aquarius",12:"Pisces"}[s],
                    sign_counts.get(s, 0))
    logger.info("Per-source counts: %s", dict(src_counts))
    logger.info("TOTAL: %d contexts across %d sources, %d distinct Lagnas",
                len(contexts), len(src_counts), len(sign_counts))

    if not args.dry_run:
        write_jsonl(contexts, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
