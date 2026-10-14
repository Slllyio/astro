"""Inventory Three Hundred Important Combinations: acquired vs encoded, combination by combination.

The source-expansion research named 3HC completion as the largest pure-Raman coverage gain
available. Building this inventory measured the claim and CORRECTED it: both on-disk
digitizations are the SAME truncated scan, ending at combination 162 ("Jada Yoga", the ToC's
own last entry). Combinations 163-300 are not in the corpus at all. The honest arithmetic is
therefore: ~114 combinations on disk and unencoded (the immediately-workable frontier), ~138
requiring procurement of a complete edition first.

Parses the body headings ("N. NAME YOGA" after the ToC/preface), cross-references the encoded
yoga registry (`doctrine/yogas.py`) by its 3HC citations, and writes the inventory to
docs/raman_saab/THREE_HUNDRED_INVENTORY.md.

Usage:
    py -3.12 tools/raman_saab/inventory_3hc.py
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "data/knowledge_library/sources/three_hundred_combinations_raman/"
                 "chapter_001_full-text-unsplit.md")
#: the cleaner HOCR copy (user-supplied 2026-08-08; SAME 1-162 truncation, far better line
#: structure) — merged as a second anchor source under its own citation tag
SOURCE_HOCR = (ROOT / "data/knowledge_library/sources/three_hundred_combinations_hocr/"
                      "chapter_001_full-text-unsplit.md")
#: THE COMPLETE EDITION (user's Drive scan, 2026-08-08) — the only copy with 163-300.
#: Anchors carry the 3HCC tag (negative-offset -1_000_000 - line to distinguish from 3HCH).
SOURCE_COMPLETE = (ROOT / "data/knowledge_library/sources/three_hundred_combinations_complete/"
                          "chapter_001_full-text-unsplit.md")
YOGAS = ROOT / "app/raman_saab/doctrine/yogas.py"
OUT = ROOT / "docs/raman_saab/THREE_HUNDRED_INVENTORY.md"

#: body headings only — the ToC ends before line ~1300 and lists page numbers, not content
_BODY_START = 1300
#: numbered heading; the OCR renders the dot as "." or "," half the time
_HEAD = re.compile(r"^\s*(\d{1,3})[.,]\s+([A-Z][A-Za-z0-9' \-]{2,60}?)\.?\s*$")
#: Raman GROUPS combinations under one heading — "33 to 44. Malika Yoga" is twelve numbers.
#: The residual runs the first inventory called "illegible" were mostly these groups.
#: body group headings end at the name ("122 to 126. DHANA YOGAS") — greedy, end-anchored.
#: (The first version was non-greedy against a permissive tail and captured "DHA", which the
#: yoga-word filter then rejected — a parser that silently skipped every group it existed for.)
#: the far half also PAIRS combinations ("189 and 190. Ayatna Griha Prapta Yogas",
#: "193 and 194...", OCR "gnd" for "and") — same expansion semantics as "to".
_RANGE = re.compile(
    r"^\s*(\d{1,3})\s+(?:to|and|&|gnd)\s+(\d{1,3})[.,]?\s+([A-Za-z][A-Za-z0-9' \-]{2,60})\.?\s*$")
#: a ToC row: "47. Matsya Yoga ... ... 56"
#: dot-leaders come out of OCR as "...", "…", "••", ", ,," and mixes — accept any run of them
_TOC = re.compile(
    r"^\s*(\d{1,3})\.\s+([A-Za-z][A-Za-z0-9' \-]{2,60}?)\s*(?:[.•,‥…]\s*){2,}.*$")


#: OCR substitutes digits for letters inside names ("R0GA6RASTHA YOGA") — map the common
#: swaps before normalizing, so the yoga-word filter and name search survive them
_DIGIT_SWAPS = str.maketrans("015689", "oisgbg")

#: ...and letters for digits in the NUMBER token ("2O9. Vahana", "22O gnd 221") — applied
#: only to a line's leading number-ish token, never to names
_NUM_SWAPS = str.maketrans("OoIl", "0011")


def _fix_leading_number(line: str) -> str:
    line = re.sub(
        r"^(\s*)([0-9OoIl]{1,3})(\s+(?:to|and|&|gnd)\s+)([0-9OoIl]{1,3})(?=[.,\s])",
        lambda m: (m.group(1) + m.group(2).translate(_NUM_SWAPS)
                   + m.group(3) + m.group(4).translate(_NUM_SWAPS)),
        line)
    return re.sub(
        r"^(\s*)([0-9OoIl]{1,3})(?=[.,])",
        lambda m: m.group(1) + m.group(2).translate(_NUM_SWAPS),
        line)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower().translate(_DIGIT_SWAPS))


def parse_combinations() -> tuple[list[tuple[int, str, int]], list[tuple[int, str]]]:
    """Two-source join, because the OCR presents headings in at least three shapes.

    The TABLE OF CONTENTS is the authoritative number->name map (the book prints it clean).
    Body anchors come from numbered headings where they parsed, else from the first bare
    occurrence of the name in the body. Returns (anchored, unanchored) — an unanchored entry
    is a true OCR gap: the ToC promises it, the body text never shows it legibly.
    """
    lines = SOURCE.read_text(encoding="utf-8", errors="replace").splitlines()

    toc: dict[int, str] = {}
    for ln in lines[:_BODY_START]:
        m = _TOC.match(ln)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 300 and n not in toc and "yoga" in _norm(m.group(2)):
                toc[n] = m.group(2).strip().rstrip(".")

    body: dict[int, tuple[str, int]] = {}
    for i in range(_BODY_START, len(lines)):
        norm = re.sub(r"\s+", " ", lines[i]).strip()
        r = _RANGE.match(norm)
        if r and "yoga" in _norm(r.group(3)):
            a, b = int(r.group(1)), int(r.group(2))
            if 1 <= a < b <= 300 and (b - a) <= 30:
                name = r.group(3).strip().rstrip(".")
                for n in range(a, b + 1):
                    if n not in body:
                        body[n] = (f"{name} (group {a}-{b})", i + 1)
                continue
        m = _HEAD.match(norm)
        if m:
            n = int(m.group(1))
            # every one of the 300 is a named Yoga (the ToC confirms it) — the filter that
            # keeps the introduction's own numbered list ("1. The good and evil lords...")
            # from stealing the low numbers
            if 1 <= n <= 300 and n not in body and "yoga" in _norm(m.group(2)):
                body[n] = (m.group(2).strip().rstrip("."), i + 1)

    # ToC numbers with no numbered body heading: anchor on the name's first body occurrence
    body_norm = [(_norm(l), i + 1) for i, l in enumerate(lines) if i >= _BODY_START]
    anchored: dict[int, tuple[int, str, int]] = {
        n: (n, name, line) for n, (name, line) in body.items()}
    unanchored: list[tuple[int, str]] = []
    for n, name in sorted(toc.items()):
        if n in anchored:
            continue
        key = _norm(name)
        hit = next((line for txt, line in body_norm if key and key in txt), None)
        if hit:
            anchored[n] = (n, name, hit)
        else:
            unanchored.append((n, name))
    # ── merge the cleaner HOCR copy: same book, same span, far fewer OCR casualties. Its
    # anchors carry the 3HCH tag so encoding work cites the copy the text actually came from.
    if SOURCE_HOCR.is_file():
        hlines = SOURCE_HOCR.read_text(encoding="utf-8", errors="replace").splitlines()
        # HOCR quirks: runs of spaces ("162.  jADA  YOGA") and case-mangled first letters
        # ("jADA"). Collapse whitespace and accept any-case names — the mandatory yoga-word
        # carries the filtering burden.
        hocr_head = re.compile(r"^\s*(\d{1,3})\.\s+([A-Za-z][A-Za-z0-9' \-]{2,60}?)\.?\s*$")
        for i, ln in enumerate(hlines, 1):
            norm = re.sub(r"\s+", " ", ln).strip()
            r = _RANGE.match(norm)
            if r and "yoga" in _norm(r.group(3)):
                a, b = int(r.group(1)), int(r.group(2))
                if 1 <= a < b <= 300 and (b - a) <= 30:
                    name = r.group(3).strip().rstrip(".").upper()
                    for n in range(a, b + 1):
                        if n not in anchored:
                            anchored[n] = (n, f"{name} (group {a}-{b})", -i)
                    continue
            m = hocr_head.match(norm)
            if not m:
                continue
            n = int(m.group(1))
            if 1 <= n <= 300 and n not in anchored and "yoga" in _norm(m.group(2)):
                anchored[n] = (n, m.group(2).strip().rstrip(".").upper(), -i)
        unanchored = [(n, name) for n, name in unanchored if n not in anchored]
    # ── the complete edition: same two heading forms, one more OCR quirk (the em-dash after
    # "Definition" renders as ".-"), numbering runs 1-300. Fills everything the truncated
    # scans cannot, and backfills stragglers for 1-162 as a third opinion.
    if SOURCE_COMPLETE.is_file():
        clines = SOURCE_COMPLETE.read_text(encoding="utf-8", errors="replace").splitlines()
        chead = re.compile(r"^\s*(\d{1,3})[.,]\s+([A-Za-z][A-Za-z0-9' \-]{2,60}?)\.?\s*$")
        # The book's own alphabetical index ("APPENDIX II - INDEX OF YOGAS") numbers yogas
        # by INDEX POSITION, not combination number. Parsing past it once polluted the
        # inventory with wrong-numbered rows ("192. Netranasa", "196. Obhayachari") that
        # SHADOWED the true combinations at those numbers — stop at the appendix. The
        # edition's own ToC (before combination 1's body heading at line 1020) shadows the
        # same way with WORSE OCR ("Hapta" for "Prapta") — skip it too.
        index_start = next(
            (i for i, ln in enumerate(clines, 1)
             if re.search(r"IND[BE]X OF YOGAS", ln)), len(clines) + 1)
        complete_body_start = 1000
        for i, ln in enumerate(clines, 1):
            if i < complete_body_start:
                continue
            if i >= index_start:
                break
            norm = _fix_leading_number(re.sub(r"\s+", " ", ln).strip())
            r = _RANGE.match(norm)
            if r and "yoga" in _norm(r.group(3)):
                a, b = int(r.group(1)), int(r.group(2))
                if 1 <= a < b <= 300 and (b - a) <= 30:
                    name = r.group(3).strip().rstrip(".").title()
                    for n in range(a, b + 1):
                        if n not in anchored:
                            anchored[n] = (n, f"{name} (group {a}-{b})", -1_000_000 - i)
                    continue
            m = chead.match(norm)
            if not m:
                continue
            n = int(m.group(1))
            if 1 <= n <= 300 and n not in anchored and "yoga" in _norm(m.group(2)):
                anchored[n] = (n, m.group(2).strip().rstrip("."), -1_000_000 - i)
        unanchored = [(n, name) for n, name in unanchored if n not in anchored]
    return [anchored[k] for k in sorted(anchored)], unanchored


def encoded_yoga_names() -> set[str]:
    """Normalized names of every registered yoga citing ANY 3HC-family tag (3HC/3HCH/3HCC).

    The original cross-reference counted legacy 3HC:line cites inside a combination's span —
    blind to the newer copies' tags, so it undercounted (28 while the registry held 84).
    Names are the stable join key across three differently-numbered editions."""
    text = YOGAS.read_text(encoding="utf-8")
    names: set[str] = set()
    for m in re.finditer(
            r'name="([^"]+)".*?source=Citation\("(3HC[CH]?)"', text, re.S):
        names.add(_norm(re.sub(r"(?i)yogas?", "", m.group(1))))
    return names


def encoded_citation_lines() -> set[int]:
    """Every legacy-3HC line number the registry cites (kept for span diagnostics)."""
    text = YOGAS.read_text(encoding="utf-8")
    return {int(m) for m in re.findall(r"3HC[:-](\d+)", text)}


def main() -> int:
    combos, unanchored = parse_combinations()
    enc_names = encoded_yoga_names()
    if not combos:
        print("no combinations parsed — source layout changed?", file=sys.stderr)
        return 1

    # a combination counts as encoded when a registered yoga citing any 3HC-family tag
    # matches it by normalized name (the stable key across three editions)
    def _edit1(a: str, b: str) -> bool:
        """Levenshtein distance <= 1 — absorbs single-letter OCR variants
        (sonapha/sunapha, keraadruma/kemadruma-adjacent) without fuzz libraries."""
        if abs(len(a) - len(b)) > 1:
            return False
        if len(a) > len(b):
            a, b = b, a
        i = j = diff = 0
        while i < len(a) and j < len(b):
            if a[i] == b[j]:
                i += 1; j += 1
            else:
                diff += 1
                if diff > 1:
                    return False
                if len(a) == len(b):
                    i += 1
                j += 1
        return diff + (len(b) - j) <= 1

    def _is_encoded(name: str) -> bool:
        # A GROUP row ("245 to 263. Raja Yogas", 19 members) must not be credited whole
        # by one name match — one encoded "Raja Yoga" would tick 19 boxes and hide the
        # frontier. Small groups (<=4, e.g. Sarpasapa 212-215) stay name-creditable; the
        # registry's skip records remain the per-arm authority either way.
        g = re.search(r"\(group (\d+)-(\d+)\)", name)
        if g and int(g.group(2)) - int(g.group(1)) + 1 > 4:
            return False
        # the yoga-suffix strip must be case-insensitive: legacy scans SHOUT ("...YOGA"),
        # the complete edition title-cases ("Grihanasa Yogas") — the uppercase-only strip
        # left the suffix on and silently failed every complete-edition join
        base = _norm(re.sub(r"(?i)yogas?", "", re.sub(r"\(group.*?\)", "", name)))
        if not base:
            return False
        for k in enc_names:
            if not k:
                continue
            if k == base or _edit1(k, base):
                return True
            # containment only for long names of comparable length ("sakata" inside
            # "sakata akriti" is real; "gaja" inside "gajakesari" is not)
            if ((k in base or base in k)
                    and min(len(k), len(base)) >= 6
                    and min(len(k), len(base)) / max(len(k), len(base)) >= 0.7):
                return True
        return False
    rows = [(n, name, line, _is_encoded(name)) for n, name, line in combos]

    acquired = {n for n, *_ in rows}
    last = 300 if SOURCE_COMPLETE.is_file() else 162
    known = acquired | {n for n, _ in unanchored}
    gaps = unanchored
    illegible = sorted(set(range(1, last + 1)) - known)
    missing = sorted(range(last + 1, 301))
    encoded = [r for r in rows if r[3]]
    pending = [r for r in rows if not r[3]]

    lines = [
        "# Three Hundred Important Combinations — the inventory",
        "",
        f"*Generated by `tools/raman_saab/inventory_3hc.py`. Source: the on-disk digitization "
        f"(both copies are the same truncated scan).*",
        "",
        "## The arithmetic",
        "",
        f"| | count |",
        f"|---|---|",
        f"| combinations in the book | 300 |",
        f"| **acquired on disk** | **{len(acquired)}** (1-{max(acquired)}) |",
        f"| encoded in `doctrine/yogas.py` (by 3HC citation) | {len(encoded)} |",
        f"| **on disk, awaiting encoding — the workable frontier** | **{len(pending)}** |",
        f"| in the ToC but illegible in the body (true OCR gaps) | {len(gaps)} |",
        f"| invisible to the parser entirely — manual-audit list below | {len(illegible)} |",
        f"| **beyond the scan — procurement needed** | **{len(missing)}** "
        f"({missing[0]}-{missing[-1]}) |" if missing else "| beyond the scan | 0 |",
        "",
        ("**The complete edition is acquired** (user's Drive scan, Motilal ed., ingested "
         "2026-08-08 as `3HCC`) — the first copy containing 163-300; every earlier circulating "
         "scan truncated at 162. Cite 3HCC for the far half, 3HCH for 1-162 where its OCR is "
         "cleaner." if SOURCE_COMPLETE.is_file() else
         "Both truncated scans end at combination 162; a complete edition must be procured."),
        "",
        "**Group-row caveat:** a grouped heading (\"202 to 204. Kapata Yogas\") is credited "
        "as encoded when ANY registered yoga matches it by name — so a group with a "
        "deliberately-skipped arm (204's Gulika clause) still shows encoded. The skip "
        "record in `doctrine/yogas.py` is the authority on per-arm coverage.",
        "",
        "## On disk, not yet encoded",
        "",
        "| # | name | source line |",
        "|---|---|---|",
    ]
    def _tag(line: int) -> str:
        if line <= -1_000_000:
            return f"3HCC:{-line - 1_000_000}"
        if line < 0:
            return f"3HCH:{-line}"
        return f"3HC:{line}"
    lines += [f"| {n} | {name} | {_tag(line)} |" for n, name, line, _ in pending]
    if illegible:
        lines += ["", "## Not machine-legible (numbers the OCR hides — audit by hand)", "",
                  ", ".join(str(n) for n in illegible)]
    if gaps:
        lines += ["", "## In the ToC, never found in the body", "",
                  ", ".join(f"{n} ({name})" for n, name in gaps)]
    lines += ["", "## Already encoded (citation inside the combination's span)", "",
              "| # | name | source line |", "|---|---|---|"]
    lines += [f"| {n} | {name} | {_tag(line)} |" for n, name, line, _ in encoded]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"acquired {len(acquired)} | encoded {len(encoded)} | pending {len(pending)} | "
          f"absent {len(missing)}")
    print(f"written: {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
