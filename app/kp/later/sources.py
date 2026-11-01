"""The later-author KP books the walled ``app.kp.later`` layer cites.

None of these is by K. S. Krishnamurti. They were written after him by his son,
his students and the KP community, and the engine keeps them apart from his own
Readers (the user's decision of 2026-11-01, "Separate labelled layer"). Every
rule built from them carries its author and book (rulings LR1-LR6 in
``docs/kp/KP_RULINGS.md``).

The texts are uncorrected OCR (tesseract 5, 2026-11-01) of the page scans in
``data/knowledge_library/sources/kp-readers/``, saved to the library as
``kp_later_<id>/chapter_001_full-text-unsplit.md``. Pages are cited by the
file's ``<!-- page N (scan NNNN) -->`` marker, where N is the scan number, not
the printed folio. ``data/`` is gitignored; tests read a book from its library
path or from the env var ``KP_LATER_<ID>`` and skip when neither exists.

Usage:
    from app.kp.later.sources import SOURCES
    SOURCES["EZN"].author
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class LaterSource:
    """One later-author book: id, title, author line and library path."""

    id: str
    title: str
    author: str
    path: str

    @property
    def env(self) -> str:
        """Env var that may point at the book's text instead of ``path``."""
        return f"KP_LATER_{self.id}"


def _p(i: str) -> str:
    return f"data/knowledge_library/sources/kp_later_{i.lower()}/chapter_001_full-text-unsplit.md"


_S = LaterSource
SOURCES: Final[dict[str, LaterSource]] = {s.id: s for s in (
    _S("SPK", "Sublord Speaks, Parts 1-3", "K. M. Subramaniam (edited by K. Subramaniam)", _p("SPK")),
    _S("AS1", "Astro Secrets and Krishnamurti Padhdhati, Part 1", "M. P. Shanmugam", _p("AS1")),
    _S("AS2", "Astro Secrets and Krishnamurti Padhdhati, Part 2",
       "K. Subramaniam (ed.), articles by various KP authors", _p("AS2")),
    _S("AS3", "Astro Secrets and Krishnamurti Padhdhati, Part 3",
       "K. Subramaniam (ed.), articles by various KP authors", _p("AS3")),
    _S("AS4", "Astro Secrets and Krishnamurti Padhdhati, Part 4",
       "K. Subramaniam (ed.), articles by various KP authors", _p("AS4")),
    _S("AS5", "Astro Secrets and Krishnamurti Padhdhati, Part 5",
       "K. Subramaniam (ed.), articles by various KP authors", _p("AS5")),
    _S("AS6", "Astro Secrets and Krishnamurti Padhdhati, Part 6", "K. Subramaniam", _p("AS6")),
    _S("KNR", "KP Navratnamala", "compiled by Kanak Bosmia (House Grouping tables by Tin Win)", _p("KNR")),
    _S("AFB", "Astrology for Beginners, Vols 1-6", "K. Subramaniam", _p("AFB")),
    _S("EZN", "KP E-zine, November 2020 - December 2021",
       "KP E-zine contributors (ed. Kanak Bosmia)", _p("EZN")),
)}

__all__ = ["LaterSource", "SOURCES"]
