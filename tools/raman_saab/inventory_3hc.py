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
YOGAS = ROOT / "app/raman_saab/doctrine/yogas.py"
OUT = ROOT / "docs/raman_saab/THREE_HUNDRED_INVENTORY.md"

#: body headings only — the ToC ends before line ~1300 and lists page numbers, not content
_BODY_START = 1300
#: numbered heading, optional trailing period the OCR adds half the time
_HEAD = re.compile(r"^\s*(\d{1,3})\.\s+([A-Z][A-Za-z' \-]{2,60}?)\.?\s*$")
#: a ToC row: "47. Matsya Yoga ... ... 56"
#: dot-leaders come out of OCR as "...", "…", "••", ", ,," and mixes — accept any run of them
_TOC = re.compile(
    r"^\s*(\d{1,3})\.\s+([A-Za-z][A-Za-z' \-]{2,60}?)\s*(?:[.•,‥…]\s*){2,}.*$")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower())


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
            if 1 <= n <= 300 and n not in toc and "yoga" in m.group(2).lower():
                toc[n] = m.group(2).strip().rstrip(".")

    body: dict[int, tuple[str, int]] = {}
    for i in range(_BODY_START, len(lines)):
        m = _HEAD.match(lines[i])
        if m:
            n = int(m.group(1))
            # every one of the 300 is a named Yoga (the ToC confirms it) — the filter that
            # keeps the introduction's own numbered list ("1. The good and evil lords...")
            # from stealing the low numbers
            if 1 <= n <= 300 and n not in body and "yoga" in m.group(2).lower():
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
    return [anchored[k] for k in sorted(anchored)], unanchored


def encoded_citation_lines() -> set[int]:
    """Every 3HC line number the yoga registry cites."""
    text = YOGAS.read_text(encoding="utf-8")
    return {int(m) for m in re.findall(r"3HC[:-](\d+)", text)}


def main() -> int:
    combos, unanchored = parse_combinations()
    cites = encoded_citation_lines()
    if not combos:
        print("no combinations parsed — source layout changed?", file=sys.stderr)
        return 1

    # a combination counts as encoded when a registry citation lands inside its line-span
    spans = [(n, name, line,
              combos[idx + 1][2] if idx + 1 < len(combos) else 10 ** 9)
             for idx, (n, name, line) in enumerate(combos)]
    rows = [(n, name, line, any(line <= c < end for c in cites))
            for n, name, line, end in spans]

    acquired = {n for n, *_ in rows}
    last = 162  # the scan's own final combination (its ToC ends there)
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
        "Both `three_hundred_combinations_raman` and `..._1947` hold the same scan, ending at "
        "combination 162 (the ToC's own final entry). Encoding beyond 162 requires acquiring a "
        "complete edition (in print; UBS) — recorded in SOURCE_EXPANSION_RESEARCH.md.",
        "",
        "## On disk, not yet encoded",
        "",
        "| # | name | source line |",
        "|---|---|---|",
    ]
    lines += [f"| {n} | {name} | 3HC:{line} |" for n, name, line, _ in pending]
    if illegible:
        lines += ["", "## Not machine-legible (numbers the OCR hides — audit by hand)", "",
                  ", ".join(str(n) for n in illegible)]
    if gaps:
        lines += ["", "## In the ToC, never found in the body", "",
                  ", ".join(f"{n} ({name})" for n, name in gaps)]
    lines += ["", "## Already encoded (citation inside the combination's span)", "",
              "| # | name | source line |", "|---|---|---|"]
    lines += [f"| {n} | {name} | 3HC:{line} |" for n, name, line, _ in encoded]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"acquired {len(acquired)} | encoded {len(encoded)} | pending {len(pending)} | "
          f"absent {len(missing)}")
    print(f"written: {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
