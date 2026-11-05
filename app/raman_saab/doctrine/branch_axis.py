"""Which axis Raman's qualifier word puts each lord-in-house reading on -- INFLUENCE or STRENGTH.

Raman's fortified / well disposed / favourably disposed / afflicted / ill disposed are INFLUENCE
words (see doctrine/disposition.py for his definitions); strong / powerful / in strength / weak
are STRENGTH words. The lord-in-house tables mix them, often within one entry ("If fortified ...
When the lord is weak", HTJAH-I:6116-6118 style), and the word usually sits in Raman's sentence,
not in the encoded text. So every entry whose displayed text depends on the choice was TAGGED
from the source by two independent engine-blind reviews (2026-10-13). Only the 56/58 slots both
reviews tagged identically are listed; the rest keep the old strength-only selection:
- split between the reviews: H8.L.5 ("fortified in a kendra or trikona": position vs influence),
  H8.L.8 (two separate sentences merged into one slot);
- unclear in Raman: H6.L.11 (bare "If benefice / If malefic"), H10.L.3 and H12.L.4 ("well placed"),
  H8.L.3's fortified condition (a conjunction with named lords);
- H8.L.7's fortified condition is on TWO lords ("If the 7th and 8th lords are strong"), which the
  single-subject selection cannot test;
- fortified texts that only repeat Raman's unconditioned reading (H7.L.6, H11.L.11, H12.L.6,
  H12.L.8; and H7.L.5 / H8.L.1 on the fortified side) -- there is nothing to choose.

Each value is (fortified axis, afflicted axis); None leaves that slot unselectable by axis.
"both" is Raman's conjoined "weak and afflicted" (HTJAH-I:5121; HTJAH-I:6089-6098 style).
"""
from __future__ import annotations

from typing import Final, Optional

_I, _S, _B = "influence", "strength", "both"

QUALIFIER_AXIS: Final[dict[str, tuple[Optional[str], Optional[str]]]] = {
    # House 1
    "H1.L.1": (_I, None), "H1.L.2": (_I, None), "H1.L.3": (_I, None), "H1.L.5": (_I, None),
    "H1.L.6": (_I, None), "H1.L.9": (_I, None),
    # House 2
    "H2.L.3": (_I, None), "H2.L.4": (_I, None), "H2.L.5": (_I, None), "H2.L.6": (_I, None),
    "H2.L.8": (_S, None), "H2.L.11": (_I, None),
    # House 3
    "H3.L.1": (_I, None), "H3.L.3": (_I, None), "H3.L.5": (_I, None), "H3.L.6": (_I, None),
    "H3.L.7": (_I, None), "H3.L.9": (_I, None), "H3.L.11": (_I, None),
    # House 4
    "H4.L.1": (_S, _S),
    # House 5
    "H5.L.1": (_I, _I), "H5.L.2": (_I, _B), "H5.L.3": (_I, _I), "H5.L.4": (_I, _I),
    "H5.L.5": (_I, _I), "H5.L.6": (_I, _I), "H5.L.7": (_I, _I), "H5.L.9": (None, _I),
    "H5.L.10": (_I, _I),
    # House 6
    "H6.L.1": (_I, _B), "H6.L.3": (_I, _B), "H6.L.4": (_I, _B), "H6.L.8": (_I, _I),
    "H6.L.9": (_I, _I), "H6.L.10": (_I, _S), "H6.L.12": (_I, _I),
    # House 7
    "H7.L.5": (None, _S),
    # House 8
    "H8.L.3": (None, _I), "H8.L.11": (_I, _I),
    # Houses 10-12
    "H10.L.4": (_S, None), "H10.L.8": (_I, None), "H11.L.1": (_S, _S), "H11.L.7": (_I, None),
    "H12.L.2": (None, _I),
}
