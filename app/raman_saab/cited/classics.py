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
    chapter_from: str   # "file" | "file-title" | "heads" | "ends" | "footers" | "none"
    verse: str = "numbered"   # "numbered" (bare "12." lines) | "sloka" ("Sloka 12.") | "none"
    unit: str = "ch."   # what the book calls a chapter, for the label
    max_ch: int = 120   # a heading above this is an OCR misread
    heads: str = ""     # "" | "generic" | "adhyaya" | "hora-ratnam": which heading lines to trust
    near_file: int = 0  # >0: a heading is trusted only within this many of the file's number
    carry: bool = False # the chapter in force carries over from one file to the next
    skip: str = ""      # file names matching this regex are left out (prefaces, indexes)
    note: str = ""      # why this copy, known defects


# Every labelling choice below was checked by eye against the PC texts (2026-11-05 spot check).
# Where a label could not be made reliable it is switched OFF: a blank location is honest, a
# wrong one is not. The line token is always exact.
SHELF: tuple[Classic, ...] = (
    Classic("BPHS-S", "bphs_santhanam_full", "Brihat Parashara Hora Shastra", "R. Santhanam",
            "file", heads="generic", max_ch=97,
            note="The fuller of the two BPHS copies on the PC (92 chapter files, about 18,700 "
                 "distinct long lines against 12,100 in data/.../bphs, which it nearly contains). "
                 "Copied unchanged from the Parashara engine's copy. Chapters 54, 65, 81, 83, 94 "
                 "are merged into the file before them; their running heads relabel them."),
    Classic("SARAV", "saravali", "Saravali (Kalyana Varma)", "R. Santhanam", "file", max_ch=55,
            note="55 chapters, one file each; the cleanest OCR on the shelf."),
    Classic("JP", "jataka_parijata", "Jataka Parijata (Vaidyanatha Dikshita)",
            "V. Subrahmanya Sastri", "heads", verse="sloka", unit="adhyaya", max_ch=18,
            heads="adhyaya",
            note="Vols I-II, archive.org OCR. The 10 files are scan splits, interleaved by volume, "
                 "so the adhyaya comes from the 'Adh. N' running heads and 'end of the Nth "
                 "Adhyaya' lines; verses only from explicit 'Sloka N' lines."),
    Classic("UK", "uttara_kalamrita", "Uttara Kalamrita (Kalidasa)", "P. S. Sastri", "none",
            verse="none", unit="kanda",
            note="8 files whose order is not the book's (by printed pages the first file is the "
                 "end of the book) and with almost no kanda heads, so no chapter or verse is "
                 "labelled: cite by line token. Much of the text is the translator's commentary."),
    Classic("PD", "phaladeepika", "Phaladeepika (Mantreswara)", "V. Subrahmanya Sastri",
            "file-title", verse="sloka", max_ch=28,
            skip=r"preface|contents|anukramanika|index",
            note="The complete 28 chapters (wisdomlib transcription, not OCR), chosen over the two "
                 "OCR copies; prefaces and indexes left out. The engine's PHALA tag cites only "
                 "its ch.3 from this same folder."),
    Classic("BJ", "brihat_jataka", "Brihat Jataka (Varahamihira)", "Swami Vijnanananda",
            "ends", max_ch=28,
            note="OCR; the files do not follow the chapters (BJ-2 holds chs. 3-5), so the chapter "
                 "comes only from the 'Thus ends the Nth Chapter' colophons; text after a file's "
                 "last colophon (e.g. the appendix after ch. 28) is left unlabelled."),
    Classic("LP", "laghu_parashari_verma_v2", "Laghu Parashari", "O. P. Verma", "none",
            verse="none",
            note="Unsplit OCR, the v2 scan (less noise than v1). Bare numbers here are page and "
                 "list numbers as often as slokas, so no verse is labelled: cite by line token."),
    Classic("HSARA", "hora_sara_santhanam", "Hora Sara (Prithuyasas)", "R. Santhanam", "ends",
            verse="none", max_ch=38,
            note="OCR with heavy Sanskrit garble. File names are page numbers, so the chapter comes "
                 "from the 'Thus ends the Nth Chapter' colophons; verse numbers sit in the Sanskrit "
                 "and are not labelled."),
    Classic("HRAT", "hora_ratnam_santhanam", "Hora Ratnam (Bala Bhadra), Part One",
            "R. Santhanam", "footers", carry=True, max_ch=10,
            note="PDF text layer; files are page ranges. The chapter comes only from the "
                 "'Hora Ratnam / Chapter N' page footers (a footer closes its page); the "
                 "scraper's '# ... Chapter N (pages ...)' file headers are file numbers and ignored."),
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
            if c.skip and re.search(c.skip, p.name, re.I):
                continue
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
for _i, _w in enumerate("first second third fourth fifth sixth seventh eighth ninth".split(), start=1):
    _WORDNUM[f"twenty-{_w}"] = _WORDNUM[f"twenty {_w}"] = 20 + _i

_PROSE = frozenset("of in and the is as see supra above below vol verse verses sloka slokas aloka "
                   "stanza also well where which".split())


def _number(raw: str) -> Optional[int]:
    """A chapter number as printed: digits (OCR 'l'/'I' for 1 allowed), roman, or a word."""
    r = re.sub(r"(?<=[0-9l])(?:st|nd|rd|th)$", "", raw.strip(" .:,").lower())
    if not r:
        return None
    if r in _WORDNUM:
        return _WORDNUM[r]
    digits = r.replace("l", "1") if re.fullmatch(r"[0-9l]+", r) else r
    if digits.isdigit():
        return int(digits)
    n = _roman(r) if len(r) <= 8 else None
    return n if n is not None else _WORDNUM.get(r)


_GENERIC = (
    re.compile(r"^\W*(?:[a-z]\s+)?(?:chapter|ch\.?)\s*[.:]?\s*(?P<n>\d{1,3}|[ivxlc]{1,8}|[a-z]+)\b(?P<rest>.*)$", re.I),
    re.compile(r"[—–-]\s*chapter\s+(?P<n>\d{1,3})\s*$(?P<rest>)", re.I),   # file headers
)
_ADHYAYA = (
    re.compile(r"^\W*(?:adh[a-z\-]{0,8}|chapter)\s*[.:]?\s*(?P<n>[ivxl1]{1,6}|\d{1,2})\b\.?(?P<rest>.*)$", re.I),
)
_ADH_END = re.compile(r"\b(?:end of the|thus ends the)\s+(?P<n>[0-9lI]{1,2})(?:st|nd|rd|th)\s+adhy", re.I)
# footers as OCR'd: "Hora Ratnam / Chapter 5", "Hora Ratnara / ...", "flora Ratnam / ...", "/ Chapter 4"
_HRAT = (re.compile(r"/\s*chapter\s+(?P<n>\d{1,2})\s*$(?P<rest>)", re.I),
         re.compile(r"r\w{2,4}n\w{0,2}m\W{0,6}chapter\s+(?P<n>\d{1,2})\b(?P<rest>)", re.I))
_HEADS = {"generic": _GENERIC, "adhyaya": _ADHYAYA, "hora-ratnam": _HRAT}
_ENDS = re.compile(r"thus ends\s+(?:the\s+)?(?P<n>\d{1,2}(?:st|nd|rd|th)?|twenty[\s-][a-z]+|[a-z]+)\s+chapter",
                   re.I)


def chapter_heading(line: str, kind: str = "generic") -> Optional[int]:
    """The chapter number a short heading line announces ("CHAPTER XII", "Adh. XVII.",
    "Hora Ratnam / Chapter 5", "... — Chapter 28"), or None. Long lines, and lines where the
    word after the number makes it prose ("chapter 1 supra", "ch. 1 as well"), are not headings."""
    s = line.strip()
    if not s or len(s) > 70:
        return None
    for rx in _HEADS[kind]:
        m = rx.search(s)
        if not m:
            continue
        rest = m.group("rest").strip(" .:,;-—").split()
        if rest and rest[0].lower().strip("(),.") in _PROSE:
            return None
        if ")" in m.group(0)[:m.end("n") - m.start() + 2]:
            return None
        n = _number(m.group("n"))
        return n if n and 0 < n < 200 else None
    return None


_VERSE = re.compile(r"^\s*(?P<sl>sloka|s[il1!]okas?|sl\.|verse|st\.|stanza)?\s*(\d{1,3})"
                    r"(?:\s*[-–&,]\s*(\d{1,3}))?\s*[.)]\s*(?:[-—:]\s*)?(?=[A-Za-z\"'(])", re.I)
_SLOKA = re.compile(r"(?:^|[\s|*'\"])(?:s[il1!]ok\S{0,2}|sl\.)\s*(\d{1,3})(?:\s*[-–&,]\s*(\d{1,3}))?"
                    r"\s*[.:)\-\u2013]", re.I)


def verse_at(line: str, mode: str = "numbered") -> Optional[tuple[int, int, bool]]:
    """(first, last, explicit) verse number printed at the start of a line, or None.
    ``explicit`` is True when the line says "Sloka", so a lower number is a real restart."""
    if mode == "none":
        return None
    m = _SLOKA.match(line) if mode == "numbered" else _SLOKA.search(line)
    if m and (mode == "sloka" or m.start() == 0):
        a, b, explicit = int(m.group(1)), int(m.group(2) or m.group(1)), True
    elif mode == "numbered" and (m := _VERSE.match(line)):
        a, b, explicit = int(m.group(2)), int(m.group(3) or m.group(2)), bool(m.group("sl"))
    else:
        return None
    if a == 0 or b < a or b - a > 12:
        return None
    return a, b, explicit


def _file_chapter(f: ShelfFile) -> Optional[int]:
    if f.classic.chapter_from == "file":
        return f.file_no if _FILE_NO.match(f.path.name) else None
    if f.classic.chapter_from == "file-title":
        m = _FILE_TITLE.match(f.path.name)
        return int(m.group(1)) if m else None
    return None


def _footer_chapters(lines: tuple[str, ...], max_ch: int, start: Optional[int]) -> list[Optional[int]]:
    """Chapter per line from page footers ('Hora Ratnam / Chapter N'): a footer closes its page,
    so the lines before it are chapter N. The scraper's own '# ...' header lines are ignored and
    footers may only stay or rise by one. A 'Thus ends the Nth Chapter' colophon closes chapter
    N: what follows it is unlabelled until a footer names a later chapter (so back matter after
    the last chapter, which still carries the old footer, is left blank)."""
    out: list[Optional[int]] = [None] * len(lines)
    prev, cur, closed = 0, start, None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            continue
        m = _ENDS.search(line)
        if m and (n := _number(m.group("n"))) and cur is not None and n == cur:
            for j in range(prev, i + 1):
                out[j] = n
            prev, closed = i + 1, n
            continue
        n = chapter_heading(line, "hora-ratnam")
        if n is None or n > max_ch or (cur is not None and not cur <= n <= cur + 1):
            continue
        if closed is not None and n <= closed:
            prev = i + 1                       # an old footer on back matter: stays blank
            continue
        for j in range(prev, i + 1):
            out[j] = n
        prev, cur, closed = i + 1, n, None
    if closed is None:
        for j in range(prev, len(lines)):
            out[j] = cur
    return out


def _ends_chapters(lines: tuple[str, ...], max_ch: int) -> list[Optional[int]]:
    """Chapter per line from colophons: the lines up to 'Thus ends the Nth Chapter' are chapter
    N; lines after the file's last colophon are left unknown."""
    out: list[Optional[int]] = [None] * len(lines)
    prev = 0
    for i, line in enumerate(lines):
        m = _ENDS.search(line)
        if not m:
            continue
        n = _number(m.group("n"))
        if n and 0 < n <= max_ch:
            for j in range(prev, i + 1):
                out[j] = n
            prev = i + 1
    return out


Loc = tuple[Optional[int], Optional[int], bool]   # chapter, verse in force, verse opened here


def line_locations(f: ShelfFile, lines: tuple[str, ...], start_ch: Optional[int] = None) -> list[Loc]:
    """For each line (0-based), the (chapter, verse) in force there.

    Chapter: from the file name, the colophons, or a trusted heading. A heading moves the
    chapter only forward, by at most 3 (running heads repeat; OCR invents numbers), never above
    the book's chapter count, and for ``near_file`` books only near the file's own number.
    Verse: the last accepted verse number. A bare number must run forward by at most 40 from
    the last (so list items in the Notes, which restart at 1, do not reset it); after a run of
    rejections, two close rising numbers re-anchor it. An explicit "Sloka N" is always
    accepted. Both reset with the chapter."""
    c = f.classic
    if c.chapter_from == "ends":
        chs = _ends_chapters(lines, c.max_ch)
    elif c.chapter_from == "footers":
        chs = _footer_chapters(lines, c.max_ch, start_ch)
    else:
        chs = None
    ch: Optional[int] = _file_chapter(f) if c.chapter_from in ("file", "file-title") else start_ch
    last_v: Optional[int] = None
    pending: Optional[int] = None
    out: list[Loc] = []
    for i, line in enumerate(lines):
        if chs is not None:
            if chs[i] != ch:
                ch, last_v = chs[i], None
        elif c.heads:
            h = chapter_heading(line, c.heads)
            if h is None and c.heads == "adhyaya" and (m := _ADH_END.search(line)):
                n = _number(m.group("n"))
                h = n + 1 if n else None              # text after "end of the Nth" is N+1
            ok = (h is not None and h <= c.max_ch and h != ch
                  and (ch is None or ch < h <= ch + 3)
                  and (not c.near_file or abs(h - f.file_no) <= c.near_file))
            if ok:
                ch, last_v = h, None
        v = verse_at(line, c.verse)
        opened = False
        if v is not None:
            a, b, explicit = v
            if explicit or last_v is None or last_v < a <= last_v + 40:
                last_v, pending, opened = b, None, True
            elif a > last_v + 40 and pending is not None and pending < a <= pending + 5:
                last_v, pending, opened = b, None, True   # a stuck counter re-anchors
            elif a > last_v:
                pending = b
        out.append((ch, last_v, opened))
    return out


def label(f: ShelfFile, locs: list[Loc], lo: int, hi: int, lines: tuple[str, ...]) -> str:
    """The human location of lines ``lo..hi`` (1-based): "ch. 12, vv. 4-9", "ch. 12, from
    before v. 4", "ch. 12", "ch. 12-13" (crosses a boundary) or ""."""
    mode = f.classic.verse
    opened_at = [i for i in range(lo - 1, hi) if locs[i][2]]
    opened = [verse_at(lines[i], mode) for i in opened_at]
    # the chapter of the first verse the passage opens (a passage can start just before a
    # chapter heading), else the chapter in force at its first line
    ch = locs[opened_at[0]][0] if opened_at else locs[lo - 1][0]
    # Only verse numbers PRINTED in the passage are named. A carried "v. N (cont.)" was tried
    # and failed the by-eye check (a counter carried across OCR noise drifts), so a passage
    # that opens no verse names none; one that starts mid-verse says "from before v. N".
    if opened:
        a, b = opened[0][0], opened[-1][1]
        vtxt = f"v. {a}" if a == b else f"vv. {a}-{b}"
        lead = sum(ch_.isalpha() for i in range(lo - 1, opened_at[0]) for ch_ in lines[i]) >= 25
        if lead:
            vtxt = f"from before {vtxt}"
    else:
        vtxt = ""
    if ch is None and f.classic.chapter_from == "footers":
        vtxt = ""                         # back matter after the last colophon: lists, not verses
    ctxt = f"{f.classic.unit} {ch}" if ch is not None else ""
    spanned = list(dict.fromkeys(c for c, _, _ in locs[lo - 1:hi] if c is not None))
    if len(spanned) > 1:                  # the passage crosses a chapter boundary
        ctxt, vtxt = f"{f.classic.unit} {spanned[0]}-{spanned[-1]}", ""
    return ", ".join(x for x in (ctxt, vtxt) if x)


def passages(files: list[ShelfFile], lines_of, chunk) -> Iterator[tuple[ShelfFile, int, int, str, str]]:
    """(file, first, last, text, location label) for every passage on the shelf."""
    carried: dict[str, Optional[int]] = {}
    for f in files:
        lines = lines_of(f.path)
        if not lines:
            continue
        locs = line_locations(f, lines, carried.get(f.book) if f.classic.carry else None)
        carried[f.book] = locs[-1][0] if locs else None
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
        chs = sorted({int(r[4].split(",")[0].split()[-1].split("-")[0]) for r in rows
                      if r[4].startswith(c.unit)})
        out.append(f"{c.tag:7} {c.title}, tr. {c.translator}  [{c.slug}]")
        out.append(f"        {len(fs)} files, {n} passages; chapter on {with_ch} ({100 * with_ch // max(n, 1)}%), "
                   f"verse on {with_v} ({100 * with_v // max(n, 1)}%); {len(chs)} distinct {c.unit} "
                   f"{chs[0] if chs else '-'}..{chs[-1] if chs else '-'}")
        for r in rows[:: max(1, n // 4)][:4]:
            out.append(f"        e.g. {r[0].prefix}:{r[1]}-{r[2]}  {r[4] or '(no location)'}")
        if c.note:
            out.append(f"        note: {c.note}")
    return "\n".join(out)
