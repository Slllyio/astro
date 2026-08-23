"""Split BPHS ch.75 (Panchamahapurusha) out of the ch.74 (Sudarshana Chakra) file.

The archive.org OCR scan crammed ch.75 into the tail of the ch.74 file (the two-line heading shape
the importer anchors on was lost for ch.75 — only a bare "Chapter 7$" marker survived). The
Mahapurusha doctrine (`app/parashara/doctrine/mahapurusha.py`) cites `BPHS-75`, so ch.75 must exist
as its own `chapter_075_*.md`. The corpus is gitignored (provisioned per machine), so this repair is
committed instead of the file: run it once after provisioning the BPHS corpus.

Idempotent and content-keyed (finds the boundary by the marker, not a hard line number), so it is a
no-op once split and survives small scan drift. This is the "split on demand" pattern the corpus
coverage doc describes for the other absorbed chapters (54, 65, 81, 83, 94).

Usage:
    py -3.12 -m tools.parashara.repair_corpus_ch75
"""
from __future__ import annotations

import glob
import re
from pathlib import Path

_BPHS = Path("data/knowledge_library/sources/bphs")
_CH75_NAME = "chapter_075_characteristic-features-of-panchamahapurushas.md"

_FRONTMATTER = """---
id: bphs-ch075
source: bphs
title: "Brihat Parashara Hora Shastra (Vol II) — Chapter 75: Characteristic Features of Panchamahapurushas"
book: "Brihat Parashara Hora Shastra (Vol II)"
author: "Maharshi Parashara"
translator: "R. Santhanam"
chapter_index: 75
language: en
content_type: classical_text
quality: ocr_text
source_url: https://archive.org/download/BPHSEnglish/BPHS%20-%202%20RSanthanam_djvu.txt
scraped_at: 2026-08-22T00:00:00+00:00
topics:
  - meta.source_texts
classical_refs:
  - BPHS.75
---

# Brihat Parashara Hora Shastra (Vol II) — Chapter 75
_Characteristic Features of Panchamahapurushas_
"""

#: the ch.75 boundary inside the ch.74 file: a bare "Chapter 7x" marker whose next few lines mention
#: Panchamahapurusha (so we never split on the ch.74 running-header "Chapter 74").
_MARKER = re.compile(r"^\s*Chapter\s*7", re.IGNORECASE)


def _boundary(lines: list[str]) -> int | None:
    """0-indexed line where ch.75 begins, or None if not found."""
    for i, ln in enumerate(lines):
        if not _MARKER.match(ln):
            continue
        window = " ".join(lines[i:i + 8]).lower()
        if "panchamahapurush" in window or "mahapurush" in window:
            return i
    return None


def repair() -> str:
    ch74_hits = glob.glob(str(_BPHS / "chapter_074_*.md"))
    if not ch74_hits:
        return "ch.74 file not found — nothing to do (is the BPHS corpus provisioned?)"
    ch74 = Path(ch74_hits[0])
    ch75 = _BPHS / _CH75_NAME
    if ch75.exists():
        return f"{ch75.name} already exists — no-op"

    lines = ch74.read_text(encoding="utf-8").splitlines()
    cut = _boundary(lines)
    if cut is None:
        return "no Panchamahapurusha boundary in the ch.74 file — already split, or scan differs"

    ch75.write_text(_FRONTMATTER + "\n" + "\n".join(lines[cut:]) + "\n", encoding="utf-8")
    ch74.write_text("\n".join(lines[:cut]) + "\n", encoding="utf-8")
    return f"split: wrote {ch75.name} ({len(lines) - cut} lines) and truncated {ch74.name} to {cut}"


if __name__ == "__main__":
    print(repair())
