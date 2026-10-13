"""Apply reviewed slot changes to a lord-in-house rule file, by rule id, without text matching.

Every hand edit of these files in the strength-slot sweep broke at least once on a wrapped
string literal (adjacent literals, an em-dash, a re-wrapped line). This edits through the AST
instead: it locates each `RuleRecord(id=...)` call, replaces the exact source span of each slot
keyword's value, inserts a keyword the record lacks, and appends new records before the closing
paren of `RULES`. Edits are applied bottom-up so earlier spans stay valid, and the result is
re-imported and checked against the spec before the tool reports success.

Spec (a Python file defining `FILE` and `CHANGES`):

    FILE = "app/raman_saab/doctrine/rule_sets/house_01_lagna/lord_in_12.py"
    CHANGES = {
        "H1.L.3": {"note": "why", "general": "text", "fortified": None},  # omit = unchanged
    }
    NEW = [  # optional
        {"id": "H1.L.3a", "after": "H1.L.3", "kind": "descriptive", "condition": None,
         "slot": "general", "text": "...", "src": 1050, "polarity": "neutral",
         "note": "why", "varga": "D1", "frame": "LAGNA", "group": "lord_in_house"},
    ]

Usage:
    py -3.12 -m tools.raman_saab.apply_slot_changes path/to/spec.py
"""
from __future__ import annotations

import ast
import importlib
import json
import logging
import runpy
import sys
import textwrap
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[2]
_SLOTS = ("general", "fortified", "afflicted")
_WIDTH = 92


def literal(text: str | None, indent: int) -> str:
    """A Python expression for `text`, wrapped as adjacent string literals.

    Every chunk but the last keeps its trailing space — adjacent literals concatenate with NO
    separator, which fused words together the last time this was done by hand.
    """
    if text is None:
        return "None"
    room = max(_WIDTH - indent - 2, 30)
    lines = textwrap.wrap(text, room, break_long_words=False, break_on_hyphens=False) or [""]
    parts = [ln + " " for ln in lines[:-1]] + [lines[-1]]
    out = [json.dumps(p, ensure_ascii=False) for p in parts]
    return ("\n" + " " * indent).join(out)


def _record_calls(tree: ast.AST) -> dict[str, ast.Call]:
    calls: dict[str, ast.Call] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "RuleRecord":
            for kw in node.keywords:
                if kw.arg == "id" and isinstance(kw.value, ast.Constant):
                    calls[kw.value.value] = node
    return calls


def _offset(lines: list[str], lineno: int, col: int) -> int:
    """Character offset of an AST position. `col` is a UTF-8 BYTE offset — the rule files
    contain "→" and "—" (3 bytes, 1 character each), and treating bytes as characters cut two
    characters past a span's end and ate the trailing comma."""
    char_col = len(lines[lineno - 1].encode("utf-8")[:col].decode("utf-8"))
    return sum(len(ln) for ln in lines[: lineno - 1]) + char_col


def _new_record(spec: dict[str, Any]) -> str:
    slots = {s: None for s in _SLOTS}
    slots[spec["slot"]] = spec["text"]
    cond = spec.get("condition") or "None"
    note = "".join(f"    # {ln}\n" for ln in textwrap.wrap(spec.get("note", ""), _WIDTH - 6))
    body = [
        f'        id="{spec["id"]}", house={spec["house"]}, '
        f'signification="{spec["signification"]}", group="{spec.get("group", "lord_in_house")}",',
        f'        kind="{spec["kind"]}",',
        f"        condition={cond},",
    ]
    for s in _SLOTS:
        body.append(f"        {s}={literal(slots[s], 8 + len(s) + 1)},")
    body.append(f'        frame="{spec.get("frame", "LAGNA")}", varga="{spec.get("varga", "D1")}", '
                f'polarity="{spec["polarity"]}", source=Citation("{spec["work"]}", {spec["src"]})),')
    return note + "    RuleRecord(\n" + "\n".join(body) + "\n"


def apply(file: Path, changes: dict[str, dict[str, Any]], new: list[dict[str, Any]]) -> str:
    src = file.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    calls = _record_calls(ast.parse(src))
    new_ids = {n["id"] for n in new}

    def root(anchor: str) -> str:
        """Follow `after` through new records to the existing record the chain hangs off."""
        seen = set()
        while anchor in new_ids:
            if anchor in seen:
                raise ValueError(f"cyclic 'after' chain at {anchor}")
            seen.add(anchor)
            anchor = next(n["after"] for n in new if n["id"] == anchor)
        return anchor

    missing = [rid for rid in changes if rid not in calls] + \
              [n["after"] for n in new if root(n["after"]) not in calls]
    if missing:
        raise KeyError(f"rule ids not found in {file.name}: {missing}")

    edits: list[tuple[int, int, str]] = []          # (start, end, replacement)
    for rid, spec in changes.items():
        call = calls[rid]
        kws = {kw.arg: kw for kw in call.keywords}
        for slot in _SLOTS:
            if slot not in spec:
                continue
            if slot in kws:
                v = kws[slot].value
                a = _offset(lines, v.lineno, v.col_offset)
                b = _offset(lines, v.end_lineno, v.end_col_offset)
                edits.append((a, b, literal(spec[slot], v.col_offset)))
            else:                                   # insert before `frame=`
                anchor = kws["frame"]               # a keyword node starts at its NAME
                a = _offset(lines, anchor.lineno, anchor.col_offset)
                edits.append((a, a, f"{slot}={literal(spec[slot], 8 + len(slot) + 1)},\n        "))
        if spec.get("note"):
            id_kw = kws["id"]
            line_end = _offset(lines, id_kw.lineno + 1, 0)
            note = "".join(f"        # {ln}\n" for ln in textwrap.wrap(spec["note"], _WIDTH - 10))
            edits.append((line_end, line_end, note))

    blocks: dict[str, str] = {}                     # existing anchor -> chained new records
    for spec in new:                                # spec order is output order
        blocks[root(spec["after"])] = blocks.get(root(spec["after"]), "") + _new_record(spec)
    for anchor_id, text in blocks.items():
        anchor = calls[anchor_id]
        pos = _offset(lines, anchor.end_lineno, anchor.end_col_offset)
        nl = src.index("\n", pos) + 1               # past the trailing "),"
        edits.append((nl, nl, text))

    for a, b, rep in sorted(edits, key=lambda e: (e[0], e[1]), reverse=True):
        src = src[:a] + rep + src[b:]
    try:
        ast.parse(src)                              # refuse to write broken Python
    except SyntaxError as exc:
        ctx = src.splitlines()[max(0, (exc.lineno or 1) - 8):(exc.lineno or 1) + 2]
        raise SyntaxError(f"generated code does not parse (nothing written): {exc.msg} at line "
                          f"{exc.lineno}\n" + "\n".join(ctx)) from None
    return src


def verify(module: str, changes: dict[str, dict[str, Any]], new: list[dict[str, Any]]) -> None:
    """Re-import and confirm every slot reads back exactly as specified."""
    mod = importlib.reload(importlib.import_module(module))
    recs = {r.id: r for r in mod.RULES}
    for rid, spec in changes.items():
        for slot in _SLOTS:
            if slot in spec:
                got = getattr(recs[rid], slot)
                assert got == spec[slot], f"{rid}.{slot}: {got!r} != {spec[slot]!r}"
    for spec in new:
        r = recs[spec["id"]]
        assert getattr(r, spec["slot"]) == spec["text"], spec["id"]
        assert r.polarity == spec["polarity"], spec["id"]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ns = runpy.run_path(sys.argv[1])
    file = _ROOT / ns["FILE"]
    changes, new = ns.get("CHANGES", {}), ns.get("NEW", [])
    file.write_text(apply(file, changes, new), encoding="utf-8")
    module = ".".join(Path(ns["FILE"]).with_suffix("").parts)
    sys.path.insert(0, str(_ROOT))
    verify(module, changes, new)
    logger.info("%s: %d records edited, %d added, verified", file.name, len(changes), len(new))


if __name__ == "__main__":
    main()
