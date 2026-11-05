"""The classical shelf of the cited library: Parashari texts that are NOT Raman's.

Every book here is indexed for reading and corroboration only. Each passage carries the scope
label ``classical, not Raman`` so the library can never present it as Raman's doctrine, and the
natal engine never cites any of them (they are not in ``doctrine/book_registry``; this list is
the library's own, so adding a book here changes no engine verdict and no source lock).

Texts are the copies already on the project PC under ``data/knowledge_library/sources``
(gitignored; never committed). One copy per work: where the PC holds several, the choice and the
reason are recorded on the entry. Nothing here is downloaded.

Citation tokens follow the corpus convention ``TAG-N:first-last`` (N = the file's number), so
``corpus.passage`` reads every hit back verbatim. On top of the line token each passage gets a
human location, ``ch. 12, vv. 4-9``, read from the text itself:

* chapter: from the file name where the split is known to follow the book's chapters
  (``chapter_from="file"``, or ``"file-title"`` for names like ``chapter_05_chapter-3-...``),
  otherwise from chapter headings found in the text (``"heading"``); blank when neither works.
* verse: the sloka numbers printed at the start of lines (``12.``, ``12-14.``, ``Sloka 12``),
  accepted only when they run forward within a chapter, so page numbers and list items rarely
  pass. They are OCR'd numbers: the label says where to look, the line token is the authority.

Usage:
    python -m app.raman_saab.cited library shelf      # per-book files, passages, label coverage
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

SCOPE = "classical, not Raman"


@dataclass(frozen=True)
class Classic:
    tag: str            # citation stem, e.g. "SARAV" -> "SARAV-12:34-40"
    slug: str           # folder under data/knowledge_library/sources/
    title: str
    translator: str
    chapter_from: str   # "file" | "file-title" | "heading" | "none"
    unit: str = "ch."   # what the book calls a chapter, for the label
    note: str = ""      # why this copy, known defects


SHELF: tuple[Classic, ...] = (
    Classic("BPHS-S", "bphs_santhanam_full", "Brihat Parashara Hora Shastra", "R. Santhanam",
            "file",
            note="The fuller of the two BPHS copies on the PC (92 chapter files, about 18,700 "
                 "distinct long lines against 12,100 in data/.../bphs, which it nearly contains). "
                 "Copied unchanged from the Parashara engine's copy; a few chapters are merged "
                 "into their neighbour (file numbers 54, 65, 81, 83, 94 absent)."),
    Classic("SARAV", "saravali", "Saravali (Kalyana Varma)", "R. Santhanam", "file",
            note="55 chapters, one file each; the cleanest OCR on the shelf."),
    Classic("JP", "jataka_parijata", "Jataka Parijata (Vaidyanatha Dikshita)",
            "V. Subrahmanya Sastri", "heading", unit="adhyaya",
            note="Vols I-II, archive.org OCR; the 10 files are scan splits, not adhyayas, so the "
                 "adhyaya comes from headings in the text."),
    Classic("UK", "uttara_kalamrita", "Uttara Kalamrita (Kalidasa)", "P. S. Sastri", "heading",
            unit="khanda", note="8 files; the split is not verified against the khandas."),
    Classic("PD", "phaladeepika", "Phaladeepika (Mantreswara)", "V. Subrahmanya Sastri",
            "file-title",
            note="The complete 28 chapters (wisdomlib transcription, not OCR), chosen over the two "
                 "OCR copies. The engine's PHALA tag cites only its ch.3 from this same folder."),
    Classic("BJ", "brihat_jataka", "Brihat Jataka (Varahamihira)", "Swami Vijnanananda",
            "heading", note="OCR; files follow the scan, chapter headings mostly present."),
    Classic("LP", "laghu_parashari_verma_v2", "Laghu Parashari", "O. P. Verma", "heading",
            note="Unsplit OCR; the v2 scan (less OCR noise than v1)."),
    Classic("HSARA", "hora_sara_santhanam", "Hora Sara (Prithuyasas)", "R. Santhanam", "file",
            note="OCR with heavy Sanskrit garble; English portions searchable."),
    Classic("HRAT", "hora_ratnam_santhanam", "Hora Ratnam (Bala Bhadra), Part One",
            "R. Santhanam", "heading", note="PDF text layer; files are page ranges."),
)

#: Corroboration books in the engine registry that the shelf replaces in the library, so each
#: work is indexed once (their tokens still read back through ``corpus.passage``).
REPLACES: frozenset[str] = frozenset({"BPHS", "PHALA"})


@dataclass(frozen=True)
class ShelfFile:
    prefix: str
    book: str
    title: str
    scope: str
    path: Path
    classic: Classic
    file_no: int


_FILE_NO = re.compile(r"chapter_(\d+)_")
_FILE_TITLE = re.compile(r"chapter_\d+_chapter-(\d+)\b", re.I)


def shelf_files(sources: Path) -> list[ShelfFile]:
    """Every shelf file on disk, in book order. ``N`` in ``TAG-N`` is the ``chapter_NNN`` number
    when the folder's numbers are unique, else the file's 1-based position in name order."""
    out: list[ShelfFile] = []
    for c in SHELF:
        folder = sources / c.slug
        if not folder.is_dir():
            continue
        files = sorted(p for p in folder.glob("*.md") if p.is_file())
        nums = [(_FILE_NO.match(p.name) or None) for p in files]
        use_num = all(nums) and len({int(m.group(1)) for m in nums}) == len(files)
        for i, p in enumerate(files, start=1):
            n = int(nums[i - 1].group(1)) if use_num else i
            out.append(ShelfFile(f"{c.tag}-{n}", c.tag, f"{c.title}, tr. {c.translator}",
                                 SCOPE, p, c, n))
    return out


# -- chapter and verse ------------------------------------------------------------------------

_ROMAN = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100}


def _roman(s: str) -> Optional[int]:
    s = s.lower()
    if not s or any(ch not in _ROMAN for ch in s):
        return None
    total = 0
    for a, b in zip(s, s[1:] + " "):
        v = _ROMAN[a]
        total += -v if b in _ROMAN and _ROMAN[b] > v else v
    return total if 0 < total < 200 else None


_WORDNUM = {w: i for i, w in enumerate(
    "first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth "
    "thirteenth fourteenth fifteenth sixteenth seventeenth eighteenth nineteenth twentieth".split(),
    start=1)}

_HEADING = re.compile(
    r"^\s*#*\s*(?:chapter|adhyaya|adhyay|khanda|kanda|ch\.)\s*[:.\-]?\s*"
    r"(?P<n>\d{1,3}|[ivxlc]{1,8}|[a-z]+)\b(?P<rest>.*)$", re.I)


def chapter_heading(line: str) -> Optional[int]:
    """The chapter number a short heading line announces ("CHAPTER XII", "Adhyaya 3",
    "Chapter Third"), or None. Long lines are prose that merely mention a chapter."""
    s = line.strip()
    if not s or len(s) > 70:
        return None
    m = _HEADING.match(s)
    if not m:
        return None
    raw = m.group("n")
    rest = m.group("rest").strip()
    if rest[:1].isalpha() and rest.split(" ", 1)[0].lower() in {"of", "in", "and", "the", "is"}:
        return None                         # "chapter of the book ..." is prose
    if raw.isdigit():
        n = int(raw)
    else:
        n = _roman(raw) if len(raw) <= 8 else None
        if n is None:
            n = _WORDNUM.get(raw.lower())
    return n if n and 0 < n < 120 else None


_VERSE = re.compile(r"^\s*(?:sloka|sl\.|verse|st\.|stanza)?\s*(\d{1,3})(?:\s*[-–&,]\s*(\d{1,3}))?"
                    r"\s*[.)]\s*(?:[-—:]\s*)?(?=[A-Za-z\"'(])", re.I)


def verse_at(line: str) -> Optional[tuple[int, int]]:
    """(first, last) verse number printed at the start of a line, or None."""
    m = _VERSE.match(line)
    if not m:
        return None
    a = int(m.group(1))
    b = int(m.group(2)) if m.group(2) else a
    if a == 0 or b < a or b - a > 12:
        return None
    return a, b


def _file_chapter(f: ShelfFile) -> Optional[int]:
    if f.classic.chapter_from == "file":
        return f.file_no if _FILE_NO.match(f.path.name) else None
    if f.classic.chapter_from == "file-title":
        m = _FILE_TITLE.match(f.path.name)
        return int(m.group(1)) if m else None
    return None


def line_locations(f: ShelfFile, lines: tuple[str, ...]) -> list[tuple[Optional[int], Optional[int]]]:
    """For each line (0-based), the (chapter, verse) in force there: the chapter from the file
    or the last heading, the verse from the last accepted verse number. A verse number is
    accepted when it is 1 (a chapter restarting) or runs forward by at most 40 from the last."""
    ch: Optional[int] = _file_chapter(f)
    use_heads = f.classic.chapter_from == "heading"
    last_v: Optional[int] = None
    out: list[tuple[Optional[int], Optional[int]]] = []
    for line in lines:
        if use_heads:
            h = chapter_heading(line)
            if h is not None and h != ch:
                ch, last_v = h, None
        v = verse_at(line)
        if v is not None:
            a, b = v
            if a == 1 or last_v is None or last_v < a <= last_v + 40:
                last_v = b
        out.append((ch, last_v))
    return out


def label(f: ShelfFile, locs: list[tuple[Optional[int], Optional[int]]], lo: int, hi: int,
          lines: tuple[str, ...]) -> str:
    """The human location of lines ``lo..hi`` (1-based): "ch. 12, vv. 4-9", "ch. 12, v. 4
    (cont.)", "ch. 12" or ""."""
    ch = locs[lo - 1][0]
    opened = [v for i in range(lo - 1, hi) if (v := verse_at(lines[i])) is not None
              and locs[i][1] == v[1]]
    if opened:
        a, b = opened[0][0], opened[-1][1]
        vtxt = f"v. {a}" if a == b else f"vv. {a}-{b}"
    elif locs[lo - 1][1] is not None:
        vtxt = f"v. {locs[lo - 1][1]} (cont.)"
    else:
        vtxt = ""
    ctxt = f"{f.classic.unit} {ch}" if ch is not None else ""
    return ", ".join(x for x in (ctxt, vtxt) if x)


def passages(files: list[ShelfFile], lines_of, chunk) -> Iterator[tuple[ShelfFile, int, int, str, str]]:
    """(file, first, last, text, location label) for every passage on the shelf."""
    for f in files:
        lines = lines_of(f.path)
        if not lines:
            continue
        locs = line_locations(f, lines)
        for lo, hi, text in chunk(lines):
            yield f, lo, hi, text, label(f, locs, lo, hi, lines)


def shelf_report(sources: Optional[Path] = None) -> str:
    """Per book: which copy, files, passages, and how many passages got a chapter / a verse."""
    from app.raman_saab.cited import corpus, library
    sources = sources or corpus.SOURCES
    files = shelf_files(sources)
    out = [f"Classical shelf under {sources}  (scope: {SCOPE})", ""]
    for c in SHELF:
        fs = [f for f in files if f.classic is c]
        if not fs:
            out.append(f"{c.tag:7} {c.title}: NOT ON THIS MACHINE (folder {c.slug})")
            continue
        rows = list(passages(fs, corpus.lines_of, library.chunk_lines))
        n = len(rows)
        with_ch = sum(1 for r in rows if r[4].startswith(c.unit))
        with_v = sum(1 for r in rows if "v." in r[4])
        chs = sorted({int(r[4].split(",")[0].split()[-1]) for r in rows if r[4].startswith(c.unit)})
        out.append(f"{c.tag:7} {c.title}, tr. {c.translator}  [{c.slug}]")
        out.append(f"        {len(fs)} files, {n} passages; chapter on {with_ch} ({100 * with_ch // max(n, 1)}%), "
                   f"verse on {with_v} ({100 * with_v // max(n, 1)}%); {len(chs)} distinct {c.unit} "
                   f"{chs[0] if chs else '-'}..{chs[-1] if chs else '-'}")
        for r in rows[:: max(1, n // 4)][:4]:
            out.append(f"        e.g. {r[0].prefix}:{r[1]}-{r[2]}  {r[4] or '(no location)'}")
        if c.note:
            out.append(f"        note: {c.note}")
    return "\n".join(out)
