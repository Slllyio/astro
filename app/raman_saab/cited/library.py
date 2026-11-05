"""The classical library: ask a question, get the exact passages, the rules that encode them, and
Raman's worked charts where he applied them.

What is indexed (one SQLite FTS5 file, ``data/library/library.sqlite``, gitignored):

* **passages**  every book file ``corpus.book_files`` finds, cut into paragraph-sized pieces,
  each carrying the citation token of its exact lines (``HTJAH-I:1586-1597``), its book title
  and scope (``Raman, natal``, ``horary``, ``KP, a separate system`` ...). Books on the
  classical shelf (``classics.py``, scope ``classical, not Raman``) also carry their chapter and
  verse as printed (``Saravali ... ch. 12, vv. 4-9``).
* **rules**     every RuleRecord in the engine's rule store, with its reading and citation.
* **examples**  every CONFIRMED conclusion Raman reached on one of his worked charts (the golden
  fixture), with the line where he wrote it when that can be found verbatim.

This is retrieval, not an answer engine: it returns what the books say and where, ranked by
plain word matching (BM25), and never paraphrases them. No model is involved and nothing is
sent anywhere.

Query words are widened with a small, fixed list of Sanskrit/English equivalents and ordinal
spellings (``7th`` / ``seventh``) because the OCR texts use both; the list is ``SYNONYMS`` below
and every search reports which words it actually searched for.
"""
from __future__ import annotations

import itertools
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

from app.raman_saab.cited import classics, corpus

INDEX: Path = corpus.ROOT / "data" / "library" / "library.sqlite"
KINDS = ("passage", "rule", "example")

_MAX_LINES = 24          # longest passage, in source lines
_MIN_LINES = 6           # paragraphs are merged until a passage has at least this many lines
_MIN_LETTERS = 40        # pieces with fewer letters (page numbers, chart grids) are skipped

_ORDINALS = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth",
             "ninth", "tenth", "eleventh", "twelfth")
_SUFFIX = {1: "st", 2: "nd", 3: "rd"}


def _ordinal_pairs() -> dict[str, str]:
    out = {}
    for i, w in enumerate(_ORDINALS, start=1):
        num = f"{i}{_SUFFIX.get(i if i < 4 else 0, 'th')}"
        out[w], out[num] = num, w
    return out


_ORD = _ordinal_pairs()

#: Fixed equivalence groups. Typing any member searches for all of them.
SYNONYMS: tuple[tuple[str, ...], ...] = (
    ("marriage", "married", "wife", "husband", "spouse", "kalatra"),
    ("children", "child", "progeny", "issue", "putra", "sons"),
    ("profession", "career", "occupation", "livelihood", "karma"),
    ("wealth", "money", "riches", "dhana", "rich"),
    ("longevity", "ayus", "ayurdaya", "death"),
    ("mother", "matru"),
    ("father", "pitru"),
    ("brothers", "brother", "sahaja", "coborn", "siblings"),
    ("education", "learning", "vidya"),
    ("disease", "diseases", "illness", "roga", "sickness"),
    ("enemies", "enemy", "satru"),
    ("ascendant", "lagna"),
    ("navamsa", "navamsha"),
    ("dasa", "dasha", "mahadasa"),
    ("bhukti", "bhukthi", "antardasa"),
    ("exalted", "exaltation", "uchcha"),
    ("debilitated", "debilitation", "neecha"),
    ("aspect", "aspects", "aspected", "drishti"),
)
_SYN = {w: g for g in SYNONYMS for w in g}

_STOP = frozenset("""a an the of in on at to for and or is are be by with from as it its this that
what which who whom when where how why does do did can could should would will shall about into
than then there their his her he she they them was were has have had not no if any all some
say says said raman tell me give show""".split())

_HOUSE_WORDS = frozenset({"house", "houses", "bhava", "bhavas"})

_TOKEN = re.compile(r'"[^"]+"|[A-Za-z0-9]+')


# -- building ---------------------------------------------------------------------------------

def _is_noise(line: str) -> bool:
    s = line.strip()
    return s.startswith("<!--") and s.endswith("-->")


def chunk_lines(lines: tuple[str, ...]) -> Iterator[tuple[int, int, str]]:
    """(first line, last line, text) for each passage of a file. Line numbers are 1-based and
    exactly those of the file, so the token ``WORK:first-last`` reads back the same text.
    YAML front matter is skipped."""
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, min(len(lines), 400)):
            if lines[i].strip() == "---":
                start = i + 1
                break
    paras: list[tuple[int, int, bool]] = []   # (first, last, follows a hard break)
    i, n = start, len(lines)
    brk = True
    while i < n:
        if not lines[i].strip():
            i += 1
            continue
        if _is_noise(lines[i]):                    # page markers: never merge across one
            brk = True
            i += 1
            continue
        j = i
        while j < n and lines[j].strip() and not _is_noise(lines[j]) and j - i < _MAX_LINES:
            j += 1
        paras.append((i, j - 1, brk))           # 0-based inclusive
        brk = False
        i = j
    cur: Optional[list[int]] = None
    for lo, hi, hard in paras:
        if cur is None:
            cur = [lo, hi]
        elif not hard and (cur[1] - cur[0] + 1) < _MIN_LINES and hi - cur[0] < _MAX_LINES:
            cur[1] = hi
        else:
            yield from _emit(lines, cur)
            cur = [lo, hi]
    if cur is not None:
        yield from _emit(lines, cur)


def _emit(lines: tuple[str, ...], span: list[int]) -> Iterator[tuple[int, int, str]]:
    lo, hi = span
    text = "\n".join(lines[lo:hi + 1]).strip()
    if sum(c.isalpha() for c in text) >= _MIN_LETTERS:
        yield lo + 1, hi + 1, text


def _schema(db: sqlite3.Connection) -> None:
    db.executescript("""
        DROP TABLE IF EXISTS docs;
        DROP TABLE IF EXISTS meta;
        CREATE VIRTUAL TABLE docs USING fts5(
            kind UNINDEXED, cite UNINDEXED, book UNINDEXED, scope UNINDEXED, house UNINDEXED,
            title, body, detail, tokenize = 'porter unicode61');
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
    """)


def _cite(prefix: str, lo: int, hi: int) -> str:
    return f"{prefix}:{lo}" if lo == hi else f"{prefix}:{lo}-{hi}"


def _passage_rows(files: Iterable[corpus.BookFile]) -> Iterator[tuple]:
    for f in files:
        for lo, hi, text in chunk_lines(corpus.lines_of(f.path)):
            yield ("passage", _cite(f.prefix, lo, hi), f.book, f.scope, None, f.title, text, "")


def _shelf_rows(sources: Path) -> Iterator[tuple]:
    """Classical-shelf passages. The title carries the printed chapter/verse; detail says
    which copy and translator, so a hit always names its source."""
    files = classics.shelf_files(sources)
    for f, lo, hi, text, where in classics.passages(files, corpus.lines_of, chunk_lines):
        title = f"{f.title}, {where}" if where else f.title
        detail = f"{where or 'location not printed'}; {classics.SCOPE}"
        yield ("passage", _cite(f.prefix, lo, hi), f.book, f.scope, None, title, text, detail)


def _rule_rows() -> Iterator[tuple]:
    for r in corpus.iter_rules():
        body = "\n".join(x for x in (r.general, r.fortified, r.afflicted) if x)
        title = (f"{r.id}: house {r.house}, {r.signification.replace('_', ' ')}, "
                 f"{r.polarity} ({r.kind})")
        cite = corpus.rule_cite(r)
        f = corpus.file_for(cite.rsplit(":", 1)[0])
        yield ("rule", cite, cite.rsplit(":", 1)[0], f.scope if f else "Raman, natal", r.house,
               title, body, str(r.condition) if r.condition is not None else "")


def _example_rows() -> Iterator[tuple]:
    for rec in corpus.worked_examples():
        for htag, e in sorted(rec.get("expected_verdicts", {}).items(), key=lambda kv: int(kv[0][1:])):
            if not corpus.is_confirmed(e):
                continue
            where = corpus.locate(e.get("verdict_prose", ""), rec)
            cite = where or corpus.discussion_span(rec) or rec["id"]
            title = (f"{rec.get('name', rec['id'])} ({rec['id']}), {htag} "
                     f"{e['signification'].replace('_', ' ')}: Raman says {e['verdict']}")
            note = "Raman's words, located" if where else "reviewer's summary; see his discussion"
            yield ("example", cite, rec.get("book", ""), "Raman, natal", int(htag[1:]), title,
                   e.get("verdict_prose", ""), f"{rec['id']} {note}")


def build(path: Path = INDEX, *, sources: Path = corpus.SOURCES) -> dict[str, int]:
    """(Re)build the index. Returns how many documents of each kind went in."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    if tmp.exists():
        tmp.unlink()
    db = sqlite3.connect(tmp)
    try:
        _schema(db)
        files = [f for f in corpus.book_files(sources) if f.book not in classics.REPLACES]
        shelf = classics.shelf_files(sources)
        counts: dict[str, int] = {}
        per_book: dict[str, int] = {}
        for kind, rows in (("passage", itertools.chain(_passage_rows(files), _shelf_rows(sources))),
                           ("rule", _rule_rows()), ("example", _example_rows())):
            n = 0
            for row in rows:
                db.execute("INSERT INTO docs VALUES (?,?,?,?,?,?,?,?)", row)
                n += 1
                if kind == "passage":
                    per_book[row[2]] = per_book.get(row[2], 0) + 1
            counts[kind] = n
        db.executemany("INSERT INTO meta VALUES (?,?)", [
            ("built_at", time.strftime("%Y-%m-%d %H:%M:%S")),
            ("books", ", ".join(sorted({f.book for f in files} | {f.book for f in shelf}))),
            *((f"count_{k}", str(v)) for k, v in counts.items()),
            *((f"passages_{b}", str(v)) for b, v in sorted(per_book.items()))])
        db.commit()
    finally:
        db.close()
    tmp.replace(path)
    return counts


# -- searching --------------------------------------------------------------------------------

@dataclass(frozen=True)
class Hit:
    kind: str
    cite: str
    title: str
    scope: str
    house: Optional[int]
    snippet: str
    detail: str
    score: float


@dataclass(frozen=True)
class Result:
    query: str
    searched: tuple[tuple[str, ...], ...]   # the word groups actually searched
    mode: str                               # "all words" | "any word"
    hits: tuple[Hit, ...]


def expand(query: str) -> list[tuple[str, ...]]:
    """The query as word groups: each group is one concept and its fixed equivalents. Quoted
    phrases stay whole."""
    groups: list[tuple[str, ...]] = []
    for tok in _TOKEN.findall(query):
        if tok.startswith('"'):
            phrase = tok.strip('"').strip()
            if phrase:
                groups.append((phrase,))
            continue
        w = tok.lower()
        if w in _STOP or (len(w) < 2 and not w.isdigit()):
            continue
        g = list(_SYN.get(w, (w,)))
        if w in _ORD:
            g.append(_ORD[w])
        groups.append(tuple(dict.fromkeys(g)))
    # "house" adds nothing once an ordinal names the house, and requiring it hides verses that
    # omit it ("If the 7th lord is in the 8th ..."), so it is dropped when an ordinal is present
    if any(g[0] in _ORD for g in groups):
        groups = [g for g in groups if g[0] not in _HOUSE_WORDS] or groups
    return groups


def _fts(groups: list[tuple[str, ...]], joiner: str) -> str:
    def q(term: str) -> str:
        return '"' + term.replace('"', '""') + '"'
    return f" {joiner} ".join("(" + " OR ".join(q(t) for t in g) + ")" for g in groups)


def connect(path: Path = INDEX) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(
            f"no library index at {path}; build it with: python -m app.raman_saab.cited library build")
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def search(query: str, *, kinds: tuple[str, ...] = KINDS, scope: str = "", house: Optional[int] = None,
           limit: int = 10, path: Path = INDEX) -> Result:
    """Search the library. ``scope`` keeps hits whose scope label contains it (e.g. ``natal``,
    ``KP``); ``house`` keeps rules and examples for that house. Every word group must match
    ("all words"); if that finds nothing, any group may ("any word"), and the result says so."""
    groups = expand(query)
    if not groups:
        return Result(query, (), "all words", ())
    db = connect(path)
    try:
        hits: list[Hit] = []
        mode = "all words"
        for mode, joiner in (("all words", "AND"), ("any word", "OR")):
            hits = _run(db, _fts(groups, joiner), kinds, scope, house, limit)
            if hits or len(groups) == 1:
                break
        return Result(query, tuple(groups), mode, tuple(hits))
    finally:
        db.close()


def _run(db: sqlite3.Connection, match: str, kinds, scope, house, limit) -> list[Hit]:
    out: list[Hit] = []
    for kind in kinds:
        sql = ("SELECT kind, cite, title, scope, house, "
               "snippet(docs, 6, '[[', ']]', ' ... ', 40), detail, "
               "bm25(docs, 0, 0, 0, 0, 0, 2.0, 1.0, 0.3) AS s "
               "FROM docs WHERE docs MATCH ? AND kind = ?")
        args: list = [match, kind]
        if scope:
            sql += " AND scope LIKE ?"
            args.append(f"%{scope}%")
        if house is not None and kind != "passage":
            sql += " AND house = ?"
            args.append(house)
        sql += " ORDER BY s LIMIT ?"
        args.append(limit)
        for row in db.execute(sql, args):
            out.append(Hit(row[0], row[1], row[2], row[3],
                           int(row[4]) if row[4] not in (None, "") else None,
                           row[5], row[6], row[7]))
    return out


def meta(path: Path = INDEX) -> dict[str, str]:
    db = connect(path)
    try:
        return dict(db.execute("SELECT key, value FROM meta"))
    finally:
        db.close()


def to_text(res: Result, *, with_text: bool = False) -> str:
    """Plain-text rendering for the terminal."""
    out = [f'Search: "{res.query}"',
           "Searched for: " + " AND ".join("(" + " | ".join(g) + ")" for g in res.searched)
           + f"   [{res.mode}]", ""]
    if not res.hits:
        out.append("Nothing found. Try fewer or plainer words.")
    heads = {"passage": "PASSAGES FROM THE BOOKS", "rule": "RULES IN THE ENGINE THAT ENCODE THEM",
             "example": "RAMAN'S WORKED CHARTS"}
    for kind in KINDS:
        hs = [h for h in res.hits if h.kind == kind]
        if not hs:
            continue
        out.append(heads[kind])
        for h in hs:
            out.append(f"  {h.cite}  [{h.scope}]  {h.title}")
            snip = " ".join(h.snippet.split()).replace("[[", "*").replace("]]", "*")
            out.append(f"      {snip}")
            if with_text and kind == "passage":
                p = corpus.passage(h.cite)
                if p:
                    out.extend("      | " + ln for ln in p["text"].splitlines())
        out.append("")
    return "\n".join(out)
