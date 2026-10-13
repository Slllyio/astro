"""Book source text: citation parsing, numbered passages, OCR-normalised quote matching."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Final

DEFAULT_SOURCES_ROOT: Final[Path] = Path("data/knowledge_library/sources")

#: Citation prefix -> source directory (same files the extractors read).
BOOK_DIRS: Final[dict[str, str]] = {
    "HTJAH-I": "how_to_judge_a_horoscope_raman",
    "HTJAH-II": "how_to_judge_horoscope_raman2",
    "NH": "notable_horoscopes_raman",
    "3HC": "three_hundred_combinations_raman",
}
_FILE: Final[str] = "chapter_001_full-text-unsplit.md"
_CITATION_RE: Final = re.compile(r"^\s*([A-Za-z0-9-]+):(\d+)(?:-(\d+))?\s*$")
MIN_QUOTE_WORDS: Final[int] = 4


def book_path(root: Path, book: str) -> Path:
    path = root / BOOK_DIRS[book] / _FILE
    if not path.is_file():
        raise FileNotFoundError(f"source text for {book} not found at {path} "
                                f"(gitignored; pass --sources-root)")
    return path


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def parse_citation(citation: str) -> tuple[str, int, int]:
    m = _CITATION_RE.match(citation)
    if not m:
        raise ValueError(f"unparseable citation: {citation!r}")
    start = int(m.group(2))
    end = int(m.group(3) or start)
    if end < start:
        raise ValueError(f"inverted range: {citation!r}")
    return m.group(1), start, end


def passage(lines: list[str], start: int, end: int, context: int = 40) -> str:
    """1-based inclusive span plus context, each line prefixed with its book line number."""
    lo, hi = max(1, start - context), min(len(lines), end + context)
    return "\n".join(f"{n}| {lines[n - 1]}" for n in range(lo, hi + 1))


def windows(item: dict) -> list[list[int]]:
    """The item's located 1-based inclusive windows (set by extract); the ONE packet window rule.
    Citation line numbers are never used: they predate a rewrite of the source files."""
    return item["windows"]


def passage_multi(lines: list[str], wins: list[list[int]]) -> str:
    """The item's stored windows, line-numbered; non-adjacent blocks split by '...'."""
    return "\n...\n".join("\n".join(f"{n}| {lines[n - 1]}" for n in range(lo, hi + 1))
                          for lo, hi in wins)


def quote_in_windows(lines: list[str], quote: str, wins: list[list[int]]) -> bool:
    """True only if `quote` occurs inside one of the exact windows the packet rendered."""
    q = normalise(quote)
    if len(q.split()) < MIN_QUOTE_WORDS:
        return False
    return any(q in normalise("\n".join(lines[lo - 1:hi])) for lo, hi in wins)


def normalise(text: str) -> str:
    text = re.sub(r"-\s*\n\s*", "", text)          # de-hyphenate across hard wraps
    text = re.sub(r"(?<=\w)-(?=\w)", "", text)    # compound words wrapped at their hyphen
    text = re.sub(r"[^\w]+", " ", text.lower())    # punctuation/quotes/dashes -> space
    return " ".join(text.split())


def quote_found(lines: list[str], quote: str, line: int, window: int = 60) -> bool:
    """True when `quote` occurs in the source within `window` lines of `line`."""
    q = normalise(quote)
    if len(q.split()) < MIN_QUOTE_WORDS:
        return False
    lo, hi = max(0, line - 1 - window), min(len(lines), line + window)
    return q in normalise("\n".join(lines[lo:hi]))


# --- Locating an item's passage by CONTENT (citation line numbers predate a source rewrite) ---

HEAD_WORDS: Final[int] = 8
MAX_BLOCK: Final[int] = 250
#: HTJAH lines kept before a record's own header (Raman discusses the chart BEFORE presenting it).
MAX_BEFORE: Final[int] = 200
_HTJAH_CHART: Final = re.compile(r"Chart\s*No\.?\s*(\d(?:\s?\d)*)", re.IGNORECASE)
#: A presentation has "Born" (OCR: "Bom", "Male born") right after its number; a mention
#: ("In Chart No. 98, the native was born") does not.
_HTJAH_BORN: Final = re.compile(r"[^A-Za-z0-9]*(?:(?:fe)?male\s+)?B[o0](?:rn|m)\b",
                                re.IGNORECASE)
_NH_HEADER: Final = re.compile(r"^\s*No\.?\s*([0-9Il]{1,3})(?![0-9])[^A-Za-z0-9]*"
                               r"([A-Z][A-Z .,'’&()-]{2,})\s*$")


def _words(lines: list[str]) -> tuple[str, list[int]]:
    """Normalised word stream (hard-wrap hyphens re-joined) and each word's 1-based line."""
    words: list[str] = []
    at: list[int] = []
    carry: tuple[str, int] | None = None
    for n, raw in enumerate(lines, 1):
        toks = normalise(raw).split()
        here = [n] * len(toks)
        if carry and toks:
            toks[0], here[0] = carry[0] + toks[0], carry[1]
        elif carry:
            words.append(carry[0]); at.append(carry[1])
        carry = None
        if toks and re.search(r"\w-\s*$", raw):
            carry = (toks.pop(), here.pop())
        words.extend(toks); at.extend(here)
    if carry:
        words.append(carry[0]); at.append(carry[1])
    return " " + " ".join(words) + " ", at


def _occurrences(joined: str, phrase: str) -> list[int]:
    """Word indices where `phrase` (normalised) starts."""
    out, pos, needle = [], joined.find(" " + phrase + " "), " " + phrase + " "
    while pos != -1:
        out.append(joined.count(" ", 0, pos + 1) - 1)
        pos = joined.find(needle, pos + 1)
    return out


def _blocks(starts: list[tuple[int, int]], n_lines: int) -> list[tuple[int, int, int]]:
    """(number, header line, last line) per presentation: to the next one, capped."""
    starts = sorted(starts, key=lambda s: s[1])
    nxt = [s[1] - 1 for s in starts[1:]] + [n_lines]
    return [(no, ln, min(end, ln + MAX_BLOCK - 1)) for (no, ln), end in zip(starts, nxt)]


def _htjah_window(starts: list[tuple[int, int]], ln: int, n_lines: int) -> tuple[int, int]:
    """From just after the previous presentation header, through the record's own header
    at `ln`, to the next one; at most MAX_BEFORE lines before `ln` and MAX_BLOCK in total."""
    prev = max((s for _, s in starts if s < ln), default=0)
    nxt = min((s for _, s in starts if s > ln), default=n_lines + 1)
    lo = max(prev + 1, ln - MAX_BEFORE)
    return lo, min(nxt - 1, lo + MAX_BLOCK - 1)


def _born_on(text: str, dt: str) -> bool:
    y, m, d = (int(x) for x in dt[:10].split("-"))
    return bool(re.search(rf"(?<!\d)(?:\d{{1,2}}\s*/\s*)?0?{d}(?:\s*/\s*\d{{1,2}})?\s*[-./]\s*"
                          rf"0?{m}\s*[-./]\s*{y}(?!\d)", text))


def _htjah_header(lines: list[str], record: dict) -> tuple[int, int] | None:
    pres = []
    for i, line in enumerate(lines):
        m = _HTJAH_CHART.search(line)
        if m and _HTJAH_BORN.match("\n".join([line[m.end():], *lines[i + 1:i + 3]])):
            pres.append((int(m.group(1).replace(" ", "")), i + 1))
    blocks = _blocks(pres, len(lines))
    num = re.search(r"\d+", str(record.get("name") or ""))
    no = int(num.group()) if num else None
    dt = (record.get("birth") or {}).get("dt")
    if dt:  # the record's own birth date is decisive; the number only breaks ties
        cands = [b for b in blocks if _born_on("\n".join(lines[b[1] - 1:b[1] + 2]), dt)]
        cands = [b for b in cands if b[0] == no] or cands
    else:
        cands = [b for b in blocks if b[0] == no]
    return _htjah_window(pres, cands[0][1], len(lines)) if len(cands) == 1 else None


def _name_ok(header: str, name: str) -> bool:
    sig = [w for w in normalise(name).split() if len(w) >= 4 and w not in {"chart", "extracted"}]
    flat = normalise(header).replace(" ", "")
    return not sig or any(w in flat for w in sig)


def _nh_header(lines: list[str], record: dict) -> tuple[int, int] | None:
    num = re.search(r"chart_(\d+)$", record["id"])
    if not num:
        return None
    heads = []
    for i, line in enumerate(lines):
        m = _NH_HEADER.match(line)
        if m:
            no = int(m.group(1).replace("I", "1").replace("l", "1"))
            heads.append((no, i + 1))
    cands = [b for b in _blocks(heads, len(lines)) if b[0] == int(num.group(1))
             and _name_ok(lines[b[1] - 1], str(record.get("name") or ""))]
    return (cands[0][1], cands[0][2]) if len(cands) == 1 else None


def chart_header(item: dict, lines: list[str], record: dict) -> tuple[int, int] | None:
    """This record's own chart presentation block, or None when absent or ambiguous."""
    if item["book"] == "NH":
        return _nh_header(lines, record)
    if item["book"] in ("HTJAH-I", "HTJAH-II"):
        return _htjah_header(lines, record)
    return None  # 3HC: no per-record chart presentation format known


def locate(item: dict, lines: list[str], record: dict) -> tuple[str, list[list[int]]]:
    """('verbatim'|'chart_header'|'NOT_LOCATED', windows). Never uses citation line numbers."""
    joined, at = _words(lines)
    prose = normalise(item.get("verdict_prose") or "").split()
    block = chart_header(item, lines, record)
    hits: list[int] = []
    if len(prose) >= MIN_QUOTE_WORDS + 1:
        hits = _occurrences(joined, " ".join(prose[:HEAD_WORDS]))
        if len(hits) > 1:  # repeated opening: the WHOLE prose decides first
            whole = set(_occurrences(joined, " ".join(prose)))
            hits = [h for h in hits if h in whole] or hits
        if len(hits) > 1 and block:  # repeated phrase: keep the one inside our own chart
            hits = [h for h in hits if block[0] <= at[h] <= block[1]]
    if len(hits) == 1:
        start = at[hits[0]]
        whole = hits[0] in _occurrences(joined, " ".join(prose))
        end = at[hits[0] + len(prose) - 1] if whole else start
        return "verbatim", [[max(1, start - 40), min(len(lines), max(start + 40, end))]]
    if block:
        return "chart_header", [[block[0], block[1]]]
    return "NOT_LOCATED", []
