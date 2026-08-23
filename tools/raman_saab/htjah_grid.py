"""Read Raman's PRINTED chart grids out of a digitally-typeset HTJAH PDF.

Why this exists
---------------
`extract_htjah_goldens` fresh-casts a nativity from its printed birth line. That is a
reconstruction, and it is not what Raman himself worked from: he prepared his charts with the
ephemerides and hand methods of his era, so a modern Swiss-Ephemeris cast of the same birth
moment does NOT necessarily reproduce his placements. The golden schema already encodes that
preference — `printed_degree` / `sign_midpoint` positions are the primary Track-B input and
`fresh_cast` is the fallback — and the corpus bears it out: its strongest records carry Raman's
own printed figures.

The scanned corpus made printed positions unusable: the chart grids OCR into fragments
("Jupiter p tagna", "Moan Saturn Venus"). A digitally-typeset PDF does not have that problem —
every planet name is a real text span with real page coordinates, and the grid rules are vector
rectangles. So the grid can be reconstructed geometrically and read as Raman printed it.

Format
------
Raman's charts are **South Indian**: a 4x4 square with the twelve signs FIXED to the perimeter
cells and the four centre cells carrying the "Rashi"/"Navamsha" label. Sign order runs clockwise
from Pisces in the top-left corner::

    Pisces(12)   Aries(1)    Taurus(2)   Gemini(3)
    Aquarius(11)  <-- centre label -->   Cancer(4)
    Capricorn(10) <-- centre label -->   Leo(5)
    Sagittarius(9) Scorpio(8) Libra(7)   Virgo(6)

Because the signs are fixed, a planet's cell IS its sign — no house arithmetic is needed to read
the chart, and the Lagna is simply whichever cell carries the "Lagna" token.

Validation
----------
The reading is checked against Raman's own prose, not against the engine. Vol I Chart No. 2
reconstructs to Lagna in Leo with Mars and Jupiter; Raman writes of that chart "the combination
of Mars and Jupiter in the ascendant has produced a Raja yoga… Mars by himself is a yoga Karaka
as he is lord of the 4th and 9th" — and from Leo, Mars (ruling Aries and Scorpio) is precisely
lord of the 9th and 4th. Both claims independently confirm the geometry.

STATUS — EXPERIMENTAL, not yet a production extractor
-----------------------------------------------------
The reading is CORRECT where a square is found (see the validation above), but a square is only
found where every one of its five rules per axis is drawn in the vector data. Measured over the
first 120 pages of Vol I: 65 pages carry chart rectangles, and only 3 yield a located grid. The
strictness is deliberate — extrapolating a missing outer rule shifts the cell edges and lands
grahas one row out, which shows up as the same graha in two signs of one chart — but it means
the geometry needs more work (most likely: recovering the missing rule from the cell pitch of
the axis that IS complete) before this can mine the corpus at scale.

It is committed now because it already earned its keep: it produced the printed grid that
established how far a modern ephemeris cast diverges from Raman's own chart preparation
(DOCTRINE_BACKLOG, "Raman's chart preparation vs a modern ephemeris").

Usage:
    py -3.12 -m tools.raman_saab.htjah_grid --pdf "<file>.pdf" --page 15
    py -3.12 -m tools.raman_saab.htjah_grid --pdf "<file>.pdf" --audit
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
#: Tokens the scans print for a graha or the ascendant, mapped to a canonical name. Raman's
#: typesetting abbreviates freely inside the cramped grid cells.
_TOKEN: dict[str, str] = {
    "sun": "Sun", "moon": "Moon", "moo": "Moon", "mars": "Mars", "mar": "Mars",
    "mercury": "Mercury", "merc": "Mercury", "mere": "Mercury", "mer": "Mercury",
    "jupiter": "Jupiter", "jupit": "Jupiter", "jup": "Jupiter",
    "venus": "Venus", "ven": "Venus", "saturn": "Saturn", "sat": "Saturn",
    "rahu": "Rahu", "ketu": "Ketu", "lagna": "Lagna", "asc": "Lagna", "ascendant": "Lagna",
}
#: South Indian fixed-sign layout, row-major over the 4x4 grid. 0 marks a centre cell.
_LAYOUT: tuple[tuple[int, ...], ...] = (
    (12, 1, 2, 3),
    (11, 0, 0, 4),
    (10, 0, 0, 5),
    (9, 8, 7, 6),
)


@dataclass
class Grid:
    """One printed 4x4 chart square and the grahas read out of it."""
    x0: float
    y0: float
    x1: float
    y1: float
    kind: str = "?"                                   # "Rashi" | "Navamsha" | "?"
    by_sign: dict[int, list[str]] = field(default_factory=dict)

    @property
    def lagna_sign(self) -> Optional[int]:
        for sign, names in self.by_sign.items():
            if "Lagna" in names:
                return sign
        return None

    def grahas(self) -> dict[str, int]:
        """{graha: sign} for the nine grahas only (the Lagna token is excluded)."""
        out: dict[str, int] = {}
        for sign, names in self.by_sign.items():
            for n in names:
                if n in _GRAHAS:
                    out[n] = sign
        return out


def _cluster(vals: list[float], tol: float = 6.0) -> list[float]:
    """Collapse near-identical coordinates (the rules are drawn as overlapping tick rects)."""
    out: list[float] = []
    for v in sorted(vals):
        if not out or v - out[-1] > tol:
            out.append(v)
        else:
            out[-1] = (out[-1] + v) / 2.0
    return out


def grids_on_page(page: Any) -> list[Grid]:
    """Every 4x4 chart square on a page, located from the vector rules.

    The grid is drawn as many short segments rather than long lines, so the squares are found by
    clustering the segment corners into candidate row/column rules and keeping runs of five
    consecutive, evenly-spaced boundaries (five boundaries = four cells)."""
    # Only rectangle items carry a bbox; other primitives (lines, curves) hand back Points, and
    # some pages mix them, so filter by op code rather than assuming.
    rects = [it[1] for dr in page.get_drawings() for it in dr["items"]
             if it[0] == "re" and hasattr(it[1], "x0")]
    if not rects:
        return []
    xs = _cluster([r.x0 for r in rects] + [r.x1 for r in rects])
    ys = _cluster([r.y0 for r in rects] + [r.y1 for r in rects])

    def runs(vals: list[float]) -> list[list[float]]:
        """Five evenly-spaced boundaries — one chart square each.

        The rules are drawn as PAIRED ticks (an outer and an inner edge a few points apart), so
        the true cell boundaries are not consecutive entries in the sorted list; requiring
        consecutiveness finds only the squares whose pairing happens to collapse under
        clustering. Instead each candidate origin is probed for partners at +s, +2s, +3s, +4s
        for a plausible cell size s, which is indifferent to whatever noise sits between them."""
        out: list[list[float]] = []
        used: list[tuple[float, float]] = []
        for i, a in enumerate(vals):
            for j in range(i + 1, len(vals)):
                step = vals[j] - a
                if not (30.0 <= step <= 90.0):              # plausible cell edge
                    continue
                tol = max(4.0, 0.12 * step)
                window = [a]
                missing = 0
                for k in range(1, 5):
                    target = a + k * step
                    hit = min(vals, key=lambda v: abs(v - target))
                    if abs(hit - target) <= tol:
                        window.append(hit)
                    else:
                        missing += 1
                        window.append(target)
                # Every boundary must be a rule that is actually DRAWN. Extrapolating even one
                # was tried and rejected: where a square's outer rule is missing from the vector
                # data the cell edges shift, and planets land one row out — observed as the same
                # graha appearing in two signs of one chart, which is astronomically impossible
                # and therefore a usable self-check. A square we cannot locate exactly is
                # skipped, never guessed.
                if missing or len(window) != 5:
                    continue
                out.append(window)
                break
        # Candidate squares overlap: the rules are drawn as paired ticks, so the same square is
        # found once from its outer edges and again from its inner ones, offset by part of a
        # cell. Position alone cannot choose between them — both are plausible grids — so each
        # candidate is SCORED by how many drawn rule edges actually sit on its boundaries. The
        # true cell boundaries carry a rule at every one; a phantom run carries far fewer.
        def score(w: list[float]) -> int:
            return sum(1 for b in w for v in vals if abs(v - b) <= 2.5)

        accepted: list[list[float]] = []
        for w in sorted(out, key=lambda w: (-score(w), w[0])):
            if any(w[0] < acc[-1] - 1 and acc[0] < w[-1] - 1 for acc in accepted):
                continue
            accepted.append(w)
        return sorted(accepted, key=lambda w: w[0])

    out: list[Grid] = []
    for xr in runs(xs):
        for yr in runs(ys):
            w, h = xr[-1] - xr[0], yr[-1] - yr[0]
            # A South Indian chart is drawn SQUARE. Requiring that discards the spurious runs
            # the paired-tick geometry throws up (a 4-step run of the wrong stride still looks
            # like a grid in one axis, but never squares up against the other).
            if abs(w - h) > 0.18 * max(w, h):
                continue
            out.append(Grid(x0=xr[0], y0=yr[0], x1=xr[-1], y1=yr[-1]))
    return out


def fill_grids(page: Any, grids: list[Grid]) -> None:
    """Assign every graha/Lagna word on the page to the cell — hence the sign — it sits in."""
    for w in page.get_text("words"):
        x0, y0, x1, y1, word = w[0], w[1], w[2], w[3], w[4]
        name = _TOKEN.get(re.sub(r"[^A-Za-z]", "", word).lower())
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        for g in grids:
            if not (g.x0 <= cx <= g.x1 and g.y0 <= cy <= g.y1):
                continue
            col = min(3, max(0, int((cx - g.x0) / ((g.x1 - g.x0) / 4))))
            row = min(3, max(0, int((cy - g.y0) / ((g.y1 - g.y0) / 4))))
            sign = _LAYOUT[row][col]
            low = word.strip().lower()
            if sign == 0:                                   # centre cells carry the chart label
                if low.startswith("rashi") or low.startswith("rasi"):
                    g.kind = "Rashi"
                elif low.startswith("navamsa") or low.startswith("navamsha"):
                    g.kind = "Navamsha"
                break
            if name:
                g.by_sign.setdefault(sign, [])
                if name not in g.by_sign[sign]:
                    g.by_sign[sign].append(name)
            break


def charts_on_page(page: Any) -> list[Grid]:
    """Filled grids for one page, ordered top-to-bottom then left-to-right."""
    gs = grids_on_page(page)
    fill_grids(page, gs)
    gs = [g for g in gs if g.by_sign or g.kind != "?"]
    return sorted(gs, key=lambda g: (round(g.y0 / 40), g.x0))


def rashi_grids(doc: Any) -> list[tuple[int, Grid]]:
    """(page_index, grid) for every Rashi square in the document.

    A square is taken as the Rashi when it is labelled so, or — where the label did not land in a
    centre cell — when it is the left-hand member of a side-by-side pair, which is how Raman
    prints them (Rashi left, Navamsha right)."""
    out: list[tuple[int, Grid]] = []
    for i, page in enumerate(doc):
        gs = charts_on_page(page)
        rows: dict[int, list[Grid]] = {}
        for g in gs:
            rows.setdefault(round(g.y0 / 40), []).append(g)
        for _, row in sorted(rows.items()):
            row.sort(key=lambda g: g.x0)
            labelled = [g for g in row if g.kind == "Rashi"]
            if labelled:
                out.extend((i, g) for g in labelled)
            elif row:
                out.append((i, row[0]))
    return out


def _chart_numbers_on_page(page: Any) -> list[tuple[int, float]]:
    """(chart_number, y) for each 'Chart No. N' heading, so a grid can be attributed."""
    out: list[tuple[int, float]] = []
    for w in page.get_text("words"):
        pass
    text_spans = page.get_text("dict")["blocks"]
    for b in text_spans:
        for line in b.get("lines", []):
            txt = "".join(s["text"] for s in line.get("spans", []))
            m = re.search(r"Chart\s*No\.?\s*(\d+)", txt, re.IGNORECASE)
            if m:
                out.append((int(m.group(1)), line["bbox"][1]))
    return out


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")            # type: ignore[attr-defined]
    except Exception:                                        # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--page", type=int, help="dump one page's grids")
    ap.add_argument("--audit", action="store_true",
                    help="count how many charts yield a complete printed grid")
    a = ap.parse_args(argv)
    import fitz

    doc = fitz.open(a.pdf)
    if a.page is not None:
        page = doc[a.page]
        for n, y in _chart_numbers_on_page(page):
            print(f"  heading: Chart No. {n} at y={y:.0f}")
        for g in charts_on_page(page):
            print(f"\n[{g.kind}] box=({g.x0:.0f},{g.y0:.0f})-({g.x1:.0f},{g.y1:.0f}) "
                  f"lagna={g.lagna_sign}")
            for sign in sorted(g.by_sign):
                print(f"   sign {sign:2d}: {', '.join(g.by_sign[sign])}")
        return 0

    total = complete = with_lagna = 0
    for _i, g in rashi_grids(doc):
        total += 1
        if g.lagna_sign:
            with_lagna += 1
        if len(g.grahas()) == 9:
            complete += 1
    print(f"[grid] Rashi squares found      : {total}")
    print(f"[grid] with a Lagna cell        : {with_lagna}")
    print(f"[grid] with ALL NINE grahas read: {complete}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
