"""Name normalization + birth-time quality tiers for the astrobank corpus.

The corpora mix three name conventions ('Last, First' in holos/wayback; 'First Last' in
lunarastro/lapaas), pervasive cp1252/utf-8 mojibake (Fran<?>ois), and namesake collisions. This
module is the single source of truth for the join key and the time-quality tiers, shared by
profile_corpus / build_person_master / build_labels.
"""
from __future__ import annotations

import hashlib
import unicodedata

_REPL = "�"


def repair_mojibake(text: str) -> str:
    """Attempt the cp1252->utf-8 round-trip repair; keep the result only if it strictly reduces
    replacement characters (never makes things worse)."""
    if _REPL not in text:
        return text
    try:
        fixed = text.encode("cp1252", errors="strict").decode("utf-8", errors="strict")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    return fixed if fixed.count(_REPL) < text.count(_REPL) else text


def normalize_name(raw: str) -> str:
    """The canonical join key: mojibake-repaired, 'Last, First' -> 'first last', NFKD
    diacritic-stripped, casefolded, whitespace-collapsed. Replacement chars are dropped LAST so
    'Fran<?>ois' and 'Francois' converge when repair fails."""
    s = repair_mojibake(raw or "").strip()
    if "," in s:
        last, _, first = s.partition(",")
        s = f"{first.strip()} {last.strip()}"
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c) and c != _REPL)
    return " ".join(s.casefold().split())


def person_id(name_norm: str, birth_date_iso: str) -> str:
    """Stable person id: same name + same date -> same person; different date -> different person
    (handles common-given-name collisions like 'yuto' x12)."""
    return hashlib.sha1(f"{name_norm}|{birth_date_iso}".encode()).hexdigest()[:16]


def time_precision(time_str: str) -> str:
    """'minute' | 'quarter' | 'round_hour' | 'noon_default' | 'missing'. Pre-registered tiers:
    A = minute; B = minute|quarter; C = any non-noon known time."""
    t = (time_str or "").strip()
    if not t or len(t) < 5:
        return "missing"
    if t.startswith("12:00"):
        return "noon_default"
    mm = t[3:5]
    if mm == "00":
        return "round_hour"
    if mm in ("15", "30", "45"):
        return "quarter"
    return "minute"


_TIER_OK = {
    "A": {"minute"},
    "B": {"minute", "quarter"},
    "C": {"minute", "quarter", "round_hour"},
}
_TIER_RATINGS = {
    "A": {"AA"},
    "B": {"AA", "A"},
    "C": {"AA", "A", "B"},
}


def quality_tier(rodden: str, precision: str) -> str | None:
    """The best tier ('A' < 'B' < 'C') this record qualifies for, or None (excluded outright —
    noon-default/missing times never qualify)."""
    r = (rodden or "").strip().upper()
    for tier in ("A", "B", "C"):
        if r in _TIER_RATINGS[tier] and precision in _TIER_OK[tier]:
            return tier
    return None
