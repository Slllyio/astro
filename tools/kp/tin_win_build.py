"""Classify Tin Win's KP House Grouping rows and write the encodable ones as Python data.

Input is the by-eye transcription of KNR scans 151-172 (printed pp.70-91), kept with the book
text under ``data/`` (gitignored). Output: ``app/kp/later/tin_win_rows.py`` (the encoded rows) and
``docs/kp/KP_TIN_WIN_ROWS_2026-11-02.md`` (every row, encoded or left out with the reason).
Rulings LR8-LR10 in ``docs/kp/KP_RULINGS.md`` say how a row is read.

Usage:
    python -m tools.kp.tin_win_build --rows data/kp_later/tin_win_rows.tsv
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEATH = re.compile(r"death|demise|long life|short life|middle life|suicide|danger to life|calamity|"
                   r"longevity|early death|life of father", re.I)
MORAL = re.compile(r"illicit|criminative|dacoit|raping|timid|keep|premarital|imprison|detention|jail|"
                   r"bail|speaks truth|illegal|pleasurable sex|scandalous|affair with one", re.I)
NUM = re.compile(r"^\d{1,2}(,\d{1,2})*$")
HOUSE_LIST = re.compile(r"(\d{1,2}(?:\s*,\s*\d{1,2})*)")
NOT_CONN = re.compile(r"^(?:\*\s*)?(?:If\s+)?not connected to ([\d,\s]+?)(?:\s*\(.*\))?[.;]?$", re.I)
JOINT_ANY_TWO = re.compile(r"should operate jointly|jointly signified;", re.I)


def _houses(s: str) -> tuple[int, ...]:
    return tuple(int(x) for x in s.replace(" ", "").split(","))


def classify(row: dict) -> tuple[str, dict | str]:
    """Return ("encode", spec) or ("skip", reason)."""
    subj, c4, rem = row["subject"], row["col4"].strip(), row["remark"]
    if row["page"] == 70 and "Lagna Lord" in subj:
        return "skip", "reads the Lagna lord's own placement, not a cusp sub-lord"
    if DEATH.search(subj):
        return "skip", "death, lifespan or danger to life (ruling LR3)"
    if MORAL.search(subj):
        return "skip", "moral character or punishment (ruling LR7)"
    if not c4:
        return "skip", "Column 4 is empty (Column 5 only gives timing)"
    main = re.sub(r"\([^)]*\)", "", c4).replace("*", "").strip().rstrip(",").strip()
    side = re.findall(r"\(([^)]*)\)", c4)
    spec: dict = {"side": [s.strip() for s in side]}
    if main.lower().startswith("mainly"):
        return "skip", "'Mainly 7, then 11' gives a priority, not a house group"
    if re.search(r"\bor\b|/", main):
        return "skip", "alternative groups ('or'), each needing its own reading"
    if re.search(r"[A-Za-z]", main):
        return "skip", "names a planet, sign, Badhaka or Maraka beside the houses"
    if main.count("&") > 1:
        return "skip", "several '&' pairs listed as alternatives"
    parts = [p.strip().strip(",").strip() for p in main.split("&")]
    if not all(NUM.match(p.replace(" ", "")) for p in parts):
        return "skip", "Column 4 is not a plain house list"
    groups = tuple(_houses(p) for p in parts)
    if rem and re.search(r"\b6&11 jointly\b", rem):
        groups = ((6,), (11,))
    spec["groups"] = groups
    spec["two"] = bool(JOINT_ANY_TWO.search(rem)) and len(groups) == 1
    m = NOT_CONN.match(rem.strip()) if rem else None
    if m:
        spec["not"] = _houses(m.group(1).strip().rstrip(","))
    star = re.search(r"\*\s*(?:If\s+)?not connected to ([\d,\s]+)", rem or "", re.I)
    if star and "not" not in spec:
        spec["not"] = _houses(star.group(1).strip().rstrip(","))
    if "*" in c4 and "not" not in spec:
        return "skip", "starred condition ties the row to a planet or sign"
    spec["context"] = "horary" if re.search(r"horary", rem or "", re.I) else "natal"
    return "encode", spec


def read(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split("\t") + [""] * 6
        rows.append({"page": int(f[0]), "cusp": int(f[1]), "subject": f[2].strip(), "col4": f[3].strip(),
                     "col5": f[4].strip(), "remark": f[5].strip()})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--py", default="app/kp/later/tin_win_rows.py")
    ap.add_argument("--doc", default="docs/kp/KP_TIN_WIN_ROWS_2026-11-02.md")
    a = ap.parse_args()
    rows = read(Path(a.rows))
    enc, doc = [], []
    for i, r in enumerate(rows, 1):
        kind, spec = classify(r)
        if kind == "encode":
            enc.append((i, r, spec))
            how = " + ".join("any of " + ",".join(map(str, g)) for g in spec["groups"])
            if spec["two"]:
                how = "two or more of " + ",".join(map(str, spec["groups"][0]))
            if spec.get("not"):
                how += "; none of " + ",".join(map(str, spec["not"]))
            if spec["side"]:
                how += f"; bracketed {', '.join(spec['side'])} not required"
            status = f"encoded ({spec['context']}): {how}"
        else:
            status = f"left out: {spec}"
        doc.append(f"| {i} | {r['page']} | {r['cusp']} | {r['subject']} | {r['col4'] or '—'} | "
                   f"{r['col5'] or '—'} | {status} |")
    py = ['"""Tin Win\'s KP House Grouping rows that are encoded (generated by tools/kp/tin_win_build.py).',
          "",
          "One tuple per row: (row number, printed page, cusp, subject, groups, at_least_two, not_houses,",
          "context). Do not edit by hand; edit the transcription and re-run the builder.",
          '"""', "", "from __future__ import annotations", "", "from typing import Final", "",
          "ROWS: Final[tuple[tuple, ...]] = ("]
    for i, r, s in enc:
        py.append(f"    ({i}, {r['page']}, {r['cusp']}, {r['subject']!r}, {s['groups']!r}, {s['two']!r}, "
                  f"{tuple(s.get('not', ()))!r}, {s['context']!r}),")
    py += [")", "", '__all__ = ["ROWS"]', ""]
    Path(a.py).write_text("\n".join(py), encoding="utf-8")
    head = ["# Tin Win's KP House Grouping tables, row by row (2026-11-02)", "",
            f"Source: *KP Navratnamala* (KNR), scans 151-172, printed pp.70-91. All {len(rows)} rows were "
            "transcribed by eye from the scans (the book's own OCR of these pages is unusable) and are "
            f"listed here. {len(enc)} are encoded in `app/kp/later/tin_win.py`; the rest are left out "
            "with the reason. Readings: rulings LR8-LR10 in `KP_RULINGS.md`.", "",
            "Column 4 = houses the cusp sub-lord must signify for the event to be promised; Column 5 = "
            "houses whose significators' joint period times it (shown, not used).", "",
            "| # | Page | Cusp | Event (Column 3) | Column 4 | Column 5 | Status |", "|---|---|---|---|---|---|---|"]
    Path(a.doc).write_text("\n".join(head + doc) + "\n", encoding="utf-8")
    print(f"{len(rows)} rows, {len(enc)} encoded")


if __name__ == "__main__":
    main()
