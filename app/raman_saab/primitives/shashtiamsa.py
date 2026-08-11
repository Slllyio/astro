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

WHAT THIS MODULE DELIBERATELY DOES NOT EXPORT: a full cruel/benign (krura/saumya)
classification of the 60. Raman's corpus on disk names the amsas but never tabulates
their natures; only his APPLIED, pointwise judgments exist (RAMAN_APPLIED_NATURE below,
each with its citation). Yogas that require the cruel CLASS as such (3HC 272/273/275/
276/277, 195/201, 248) therefore stay deferred until the classification question is
settled — importing a classical table would be a band decision, not a default. A test
asserts the class predicate's absence (the vaiseshikamsa precedent: absences that
matter get tests).

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
