"""Freeze what the doctrine layer currently SAYS, so a refactor can prove it said nothing new.

This is the Gate-0 instrument of the varga-language milestone. A refactor that changes how a
value is *computed* — routing navamsa lookups through a named varga API, say — must be provable
as behaviour-preserving before any doctrine rides on it. A green ratchet does not prove that:
the ratchet only sees the 397 scored rows, and a rule can change which of Raman's readings it
displays without moving a single verdict (`_bucket_fired` buckets by `rule.polarity`, so branch
selection is invisible to the score).

So the snapshot records three levels, the same three the milestone's acceptance names:

* **primitive** — every planet's varga sign per chart, keyed by varga name.
* **predicate** — every rule that FIRES on every chart, with the branch it selected and a hash
  of the text it rendered. This is where branch drift would show.
* **verdict**  — the graded verdict per (house, signification), i.e. what the ratchet sees.

Comparing a live run against a frozen snapshot answers "did anything at all change?", which is
a strictly stronger question than "did the score hold?".

Usage:
    py -3.12 -m tools.raman_saab.doctrine_snapshot --write
    py -3.12 -m tools.raman_saab.doctrine_snapshot --check
    py -3.12 -m tools.raman_saab.doctrine_snapshot --check --verbose
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util as _ilu
import json
import logging
from pathlib import Path
from typing import Any

from app.raman_saab.chart import varga as _varga
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges import rule_firing as rf

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[2]
_HARNESS = _ROOT / "tests" / "raman_saab" / "test_goldens.py"
SNAPSHOT_PATH = _ROOT / "tests" / "fixtures" / "doctrine_snapshot.json"

_spec = _ilu.spec_from_file_location("_raman_golden_harness_snapshot", _HARNESS)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    raise ImportError(f"cannot load golden harness from {_HARNESS}")
_h = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_h)

#: The vargas the snapshot pins. D9 is the only one any rule can test today; the rest are
#: recorded so that opening the gate to them is provably additive rather than disruptive.
PINNED_VARGAS: tuple[str, ...] = ("D1", "D3", "D7", "D9", "D10", "D12", "D16", "D30")


def _digest(text: str | None) -> str:
    """Short content hash. The snapshot stores hashes, not prose, so it stays reviewable in a
    diff: a changed reading shows as one changed hash rather than a wall of moved text."""
    return hashlib.sha1((text or "").encode("utf-8")).hexdigest()[:12]


def varga_signs(chart: RamanChart) -> dict[str, str]:
    """{varga name: digest of every planet's sign in it} — the primitive level.

    A DIGEST rather than the per-planet map, deliberately. Storing ~25,000 individual signs
    cost roughly a third of the file to guard against something that should never happen at
    all: a change here means the ephemeris or a varga formula moved, which is catastrophic
    and investigated by hand, not skimmed. Chart+varga granularity is enough to start that
    investigation, and the per-planet detail is one command away from the live engine
    (`varga.varga_sign(p.lon, n)`), so nothing is actually lost.
    """
    out: dict[str, str] = {}
    for name in PINNED_VARGAS:
        n = int(name[1:])
        row = [f"{pname}={_varga.varga_sign(float(p.lon), n)}"
               for pname, p in sorted(chart.planets.items())
               if getattr(p, "lon", None) is not None]
        out[name] = _digest(",".join(row))
    return out


def fired_rules(chart: RamanChart) -> list[list[str]]:
    """[[rule_id, branch, text-hash]] for every rule that fires — the predicate level.

    Sorted by rule id so the snapshot is order-independent: a change in *iteration* order is
    not a change in doctrine, and pinning it would produce false alarms.
    """
    rows = [[fr.rule.id, fr.branch, _digest(fr.text)] for fr in rf.fire_rules(chart)]
    return sorted(rows)


def house_verdicts(chart: RamanChart) -> dict[str, str]:
    """{"H{n}/{signification}": verdict} and {"H{n}": rollup} — the verdict level.

    Delegates to the golden harness's own `evidence_snapshot`, which is the project's
    canonical per-house evidence dict (rollup + fired ids + citations + significations).
    Reusing it means this tool and the golden tests can never disagree about what a
    verdict IS — a second hand-rolled reader would be free to drift.

    Flattened to `{key: str}` on purpose: a flat map diffs to one line per changed
    verdict, where a nested dict diffs to a wall of context.
    """
    out: dict[str, str] = {}
    snap = _h.evidence_snapshot(chart)
    for house_key, block in snap.items():
        out[house_key] = str(block["rollup"])
        for sig, sv in block["significations"].items():
            out[f"{house_key}/{sig}"] = f"{sv['verdict']}|{sv['degree']}|{sv['lead_frame']}"
    return out


def build_snapshot() -> dict[str, Any]:
    """Walk every castable golden and record all three levels."""
    charts: dict[str, Any] = {}
    skipped: list[str] = []
    for rec in _h.load_goldens():
        cid = _h._id(rec)
        try:
            chart = _h.build_chart(rec)
        except Exception as exc:
            # Not silent: a chart that stops casting is itself a regression worth seeing.
            skipped.append(f"{cid}:{type(exc).__name__}")
            continue
        charts[cid] = {
            "varga_signs": varga_signs(chart),
            "fired": fired_rules(chart),
            "verdicts": house_verdicts(chart),
        }
    # A level that silently records nothing is worse than no snapshot at all: it reads as
    # "identical" forever. The first version of this tool did exactly that, defaulting a
    # wrong attribute name to {} on all 346 charts. Fail loudly instead.
    for level in ("varga_signs", "fired", "verdicts"):
        if not any(c[level] for c in charts.values()):
            raise RuntimeError(
                f"snapshot level {level!r} is empty on every chart — the reader is broken, "
                f"not the doctrine. Refusing to write a snapshot that cannot detect change.")

    return {
        "_comment": (
            "Gate-0 freeze for the varga-language milestone. Primitive/predicate/verdict "
            "levels for every castable golden. Regenerate ONLY with a deliberate, reviewed "
            "doctrine change — this file existing is what makes 'nothing changed' provable."
        ),
        "pinned_vargas": list(PINNED_VARGAS),
        "chart_count": len(charts),
        "skipped": sorted(skipped),
        "charts": charts,
    }


#: Bumped whenever `encode` changes shape, so a stale snapshot fails loudly instead of
#: producing a diff that is really a format mismatch dressed up as a doctrine change.
FORMAT = 2


def encode(rich: dict[str, Any]) -> dict[str, Any]:
    """Compact the snapshot for storage, losslessly.

    The rich form repeats itself enormously: ~880 rule ids and a few dozen verdict values
    recur across 346 charts, and at `indent=1` every one costs a line. Interning the repeated
    strings into tables and referencing them by index took the file from 3.5 MB to well under
    a megabyte with no loss — `decode` reconstructs the rich form exactly, which is what
    `diff` consumes, so the tool reports precisely what it always did.

    The tables stay plain and greppable: to find a rule, search `tables.fired` for its id and
    the index is its position.
    """
    fired_tab: dict[str, int] = {}
    vkey_tab: dict[str, int] = {}
    vval_tab: dict[str, int] = {}

    def intern(tab: dict[str, int], s: str) -> int:
        if s not in tab:
            tab[s] = len(tab)
        return tab[s]

    charts: dict[str, Any] = {}
    for cid, c in rich["charts"].items():
        fired = " ".join(str(intern(fired_tab, "|".join(row))) for row in c["fired"])
        verdicts = " ".join(f"{intern(vkey_tab, k)}={intern(vval_tab, v)}"
                            for k, v in sorted(c["verdicts"].items()))
        charts[cid] = {"v": c["varga_signs"], "f": fired, "d": verdicts}

    out = {k: v for k, v in rich.items() if k != "charts"}
    out["format"] = FORMAT
    out["legend"] = {
        "v": "varga name -> digest of every planet's sign in that division",
        "f": "space-separated indices into tables.fired, each 'ruleId|branch|textHash'",
        "d": "space-separated 'keyIdx=valIdx' into tables.vkey / tables.vval",
    }
    out["tables"] = {
        "fired": [k for k, _ in sorted(fired_tab.items(), key=lambda kv: kv[1])],
        "vkey": [k for k, _ in sorted(vkey_tab.items(), key=lambda kv: kv[1])],
        "vval": [k for k, _ in sorted(vval_tab.items(), key=lambda kv: kv[1])],
    }
    out["charts"] = charts
    return out


def decode(compact: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct the rich form `diff` consumes. Inverse of `encode`."""
    got = compact.get("format")
    if got != FORMAT:
        raise ValueError(
            f"snapshot format {got!r} but this tool writes {FORMAT}. Regenerate it: "
            f"`py -3.12 -m tools.raman_saab.doctrine_snapshot --write --note '<why>'`")
    tabs = compact["tables"]
    fired_tab, vkey, vval = tabs["fired"], tabs["vkey"], tabs["vval"]
    charts: dict[str, Any] = {}
    for cid, c in compact["charts"].items():
        fired = [fired_tab[int(i)].split("|") for i in c["f"].split()] if c["f"] else []
        verdicts = {}
        for pair in c["d"].split():
            k, _, v = pair.partition("=")
            verdicts[vkey[int(k)]] = vval[int(v)]
        charts[cid] = {"varga_signs": c["v"], "fired": fired, "verdicts": verdicts}
    out = {k: v for k, v in compact.items()
           if k not in ("charts", "tables", "legend", "format")}
    out["charts"] = charts
    return out


def diff(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    """Human-readable differences, most structural first. Empty list == identical.

    Operates on the RICH form, never the stored one — persistence is `encode`/`decode`'s
    business. That separation is why compacting the file changed nothing about what this
    reports.
    """
    out: list[str] = []
    o_charts, n_charts = old.get("charts", {}), new.get("charts", {})
    gone = sorted(set(o_charts) - set(n_charts))
    added = sorted(set(n_charts) - set(o_charts))
    if gone:
        out.append(f"charts NO LONGER castable ({len(gone)}): {', '.join(gone[:8])}")
    if added:
        out.append(f"charts newly castable ({len(added)}): {', '.join(added[:8])}")

    for cid in sorted(set(o_charts) & set(n_charts)):
        o, n = o_charts[cid], n_charts[cid]
        ov, nv = o.get("varga_signs", {}), n.get("varga_signs", {})
        for varga in sorted(set(ov) | set(nv)):
            if ov.get(varga) != nv.get(varga):
                out.append(
                    f"PRIMITIVE {cid} {varga} signs changed — an ephemeris or varga-formula "
                    f"move, not a doctrine change. Get the per-planet detail with "
                    f"varga.varga_sign(p.lon, {varga[1:]})")
        o_fired = {tuple(r) for r in o.get("fired", [])}
        n_fired = {tuple(r) for r in n.get("fired", [])}
        for row in sorted(o_fired - n_fired):
            out.append(f"PREDICATE {cid} no longer fires/renders: {row[0]} "
                       f"(branch={row[1]})")
        for row in sorted(n_fired - o_fired):
            out.append(f"PREDICATE {cid} newly fires/renders: {row[0]} (branch={row[1]})")
        ov_, nv_ = o.get("verdicts", {}), n.get("verdicts", {})
        for key in sorted(set(ov_) | set(nv_)):
            if ov_.get(key) != nv_.get(key):
                out.append(f"VERDICT   {cid} {key}: {ov_.get(key)} -> {nv_.get(key)}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="(re)generate the snapshot")
    mode.add_argument("--check", action="store_true", help="compare live output to it")
    ap.add_argument("--verbose", action="store_true", help="print every difference")
    ap.add_argument("--note", help="why this re-freeze happened; required to overwrite")
    args = ap.parse_args()

    snap = build_snapshot()
    if args.write:
        # Lineage survives every re-freeze. A snapshot that can be silently overwritten is
        # not a baseline — it is whatever the last run happened to produce. Each deliberate
        # re-freeze must say what moved and why, the same standard the golden baseline keeps.
        lineage: list[str] = []
        if SNAPSHOT_PATH.is_file():
            prior = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
            lineage = list(prior.get("lineage", []))
            if not args.note:
                raise SystemExit(
                    "refusing to overwrite an existing snapshot without --note: say what "
                    "changed and why, e.g. --note '2026-09-02 branch fallback prefers "
                    "general; 198 instances afflicted->general, 0 verdicts moved'")
        if args.note:
            lineage.append(args.note)
        snap["lineage"] = lineage
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(
            json.dumps(encode(snap), indent=1, sort_keys=True) + "\n", encoding="utf-8")
        kb = SNAPSHOT_PATH.stat().st_size / 1024
        print(f"wrote {SNAPSHOT_PATH.relative_to(_ROOT)}: {snap['chart_count']} charts, "
              f"{sum(len(c['fired']) for c in snap['charts'].values())} fired rules, "
              f"{len(snap['skipped'])} uncastable, {kb:,.0f} KB")
        return

    if not SNAPSHOT_PATH.is_file():
        raise SystemExit(f"no snapshot at {SNAPSHOT_PATH}; run --write first")
    old = decode(json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8")))
    diffs = diff(old, snap)
    if not diffs:
        print(f"IDENTICAL across {snap['chart_count']} charts "
              f"(primitive + predicate + verdict).")
        return
    print(f"{len(diffs)} DIFFERENCE(S) from the frozen snapshot:")
    for line in (diffs if args.verbose else diffs[:40]):
        print(f"  {line}")
    if not args.verbose and len(diffs) > 40:
        print(f"  ... {len(diffs) - 40} more (--verbose for all)")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
