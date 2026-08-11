"""Shashtiamsa (D60) — the 1/60th division, encoded verbatim from Raman's own Manual.

Raman points to this source himself (3HC combo 264's Remark: "For details about
shashtiamsas, see my book A MANUAL OF HINDU ASTROLOGY"). The Manual, Art. 127
(MANUAL chapter_012:1212-1263): "When a sign is divided into 60 equal parts, each is
called a Shastiamsa. The Bhachakra contains 60 x 12 = 720 Shastiamsas. In case of odd
signs, the sixty Shastiamsas are thus named: [the 60 names below]. In case of even
signs, the order of naming must be reversed."

Cross-source consistency, MEASURED: 3HC combo 234's Remark states Mridwamsa "will be
the 19th part (9 to 9-1/2 deg) of this division in an odd sign or the 42nd (20-1/2 to
21 deg) part in an even sign" — exactly what the Manual's rule computes (19th forward
in odd; 61-19 = 42nd in even). The two Raman texts agree; the test pins it.

THE CRUEL/BENIGN CLASS (added 2026-08-11, USER-APPROVED band decision — "do all
three"): Raman's corpus names the sixty but never tabulates their natures, so the
classification is CLASSICAL CORROBORATION, quoted from Phaladeepika ch. 3 (the on-disk
copy, chapter_05:109-112): "Krura Shashtyamsas or unpropitious portions are 1st, 2nd,
8th, 9th, 10th, 11th, 12th, 15th, 16th, 30th, 31st, 32nd, 33rd, 34th, 35th, 39th,
40th, 42nd, 43rd, 44th, 48th, 51st, 52nd and 59th. The rest are Saumya or propitious
ones. In the case of even signs, it is reverse" — which, because the NAMES also
reverse in even signs (Manual Art. 127), means the nature attaches to the NAME-index,
exactly what ``shashtiamsa_index`` returns. THE CONSISTENCY GATE, test-pinned: the
classical table must agree with every one of Raman's own applied rulings (Rakshas #2
cruel, Preta Puriha #12 cruel, Mridwamsa #19 benign) — it corroborates him, it never
overrides him.

Usage:
    from app.raman_saab.primitives.shashtiamsa import shashtiamsa_index, shashtiamsa_name
"""
from __future__ import annotations

from typing import Final

#: The 60 names for ODD signs, in order, from the Manual Art. 127 (chapter_012:1218-1258).
#: OCR corrections against the printed sequence: "(341 Chora" is 34; the run "(36) Satya,
#: (36) Amrita" double-prints 36 for what are positions 36 and 37 (the count and the
#: reversal rule fix the sequence); "Vishapradagdha" (39) and "Ootpatha" (43) keep the
#: Manual's own spellings.
SHASHTIAMSA_NAMES: Final[tuple[str, ...]] = (
    "Ghora", "Rakshas", "Devabhaga", "Kubera", "Rakshogana",
    "Kinnara", "Hrusta", "Kalagnana", "Garala", "Agnighatha",
    "Mayamsa", "Preta Puriha", "Apampathy", "Devaganasa", "Kala",
    "Sarpa", "Amritha", "Chandra", "Mridwamsa", "Komalamsa",
    "Padma", "Lakshmisa", "Vageesa", "Digambara", "Devamsa",
    "Indra", "Kalinasa", "Kshitiswara", "Kamalakara", "Mandatmaja",
    "Mrityu", "Kala", "Davagnya", "Chora", "Yamakantaka",
    "Satya", "Amrita", "Paripurna", "Vishapradagdha", "Kulanasa",
    "Mukhya", "Vamsakshya", "Ootpatha", "Kalarupa", "Soumya",
    "Mrudvamsa", "Susithala", "Damshtra", "Seethabja", "Indumukha",
    "Poorna", "Kalagnya", "Dandayudha", "Nirmala", "Shuba",
    "Ashuba", "Atishuba", "Sudhapayodhi", "Dhyumani", "Indurekha",
)

#: Raman's own APPLIED judgments — pointwise, each with the passage where he applies it.
#: This is NOT a classification table; it records only what Raman himself has ruled.
RAMAN_APPLIED_NATURE: Final[dict[str, str]] = {
    # 3HC Chart 135 (combo 273's example): "Saturn has joined Kethu in a cruel
    # shashtiamsa (Rakshasa)."
    "Rakshas": "cruel",
    # 3HC combo 264's definition uses Mars "in the shashtiamsa of Preta Puriha" as an
    # ear-affliction cause, and its Remark calls Rahu-in-cruel-shashtiamsa "a sure
    # indication" — an affliction amsa.
    "Preta Puriha": "cruel",
    # 3HC combo 234 uses Mridwamsa ("the mild amsa") for the gift of seership — benign.
    "Mridwamsa": "benign",
}


#: Phaladeepika ch. 3's Krura (unpropitious) name-indices, verbatim (see the module
#: docstring for the quote, the band decision, and the consistency gate).
CRUEL_SHASHTIAMSAS: Final[frozenset[int]] = frozenset(
    {1, 2, 8, 9, 10, 11, 12, 15, 16, 30, 31, 32, 33, 34, 35,
     39, 40, 42, 43, 44, 48, 51, 52, 59})


def is_cruel_shashtiamsa(lon: float) -> bool:
    """True when ``lon`` falls in a Krura shashtiamsa (Phaladeepika ch. 3 by name-index;
    nature attaches to the name, so the even-sign reversal is already handled by
    ``shashtiamsa_index``)."""
    return shashtiamsa_index(lon) in CRUEL_SHASHTIAMSAS


def shashtiamsa_index(lon: float) -> int:
    """1-based Shashtiamsa index (1..60) for a sidereal longitude, per Manual Art. 127.

    Each part spans 0.5 deg. Odd signs count forward; even signs REVERSE the naming
    order, which is equivalent to reversing the index (61 - forward).
    """
    lon = lon % 360.0
    sign = int(lon // 30.0) + 1
    part = int((lon % 30.0) // 0.5) + 1  # floor division: the nakshatra-cusp rule
    if part > 60:  # lon % 30.0 == 30.0 cannot occur, but guard the float edge
        part = 60
    return part if sign % 2 == 1 else 61 - part


def shashtiamsa_name(lon: float) -> str:
    """The Shashtiamsa name at ``lon`` — the Manual's odd-sign order, reversed for even."""
    return SHASHTIAMSA_NAMES[shashtiamsa_index(lon) - 1]
