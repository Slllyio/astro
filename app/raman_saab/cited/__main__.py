"""Command line for the cited tools. See ``app/raman_saab/cited/__init__.py``."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional


def _utf8() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")   # Windows consoles: IAST diacritics, quotes
    except Exception:
        pass


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.raman_saab.cited")
    sub = ap.add_subparsers(dest="cmd", required=True)

    rd = sub.add_parser("read", help="cited reading of one chart")
    rd.add_argument("--golden", default="", help="one of Raman's worked charts, by record id")
    for k in ("name", "date", "time"):
        rd.add_argument(f"--{k}")
    for k in ("tz", "lat", "lon"):
        rd.add_argument(f"--{k}", type=float)
    rd.add_argument("--ayanamsa", default="raman", choices=["raman", "lahiri"])
    rd.add_argument("--format", default="html", choices=["html", "md"])
    rd.add_argument("--no-stability", action="store_true")
    rd.add_argument("--out", default="", help="file to write (default: print)")

    lib = sub.add_parser("library", help="build or search the classical library")
    lsub = lib.add_subparsers(dest="lcmd", required=True)
    lsub.add_parser("build", help="(re)build data/library/library.sqlite from the book texts")
    ls = lsub.add_parser("search", help="search the library")
    ls.add_argument("query")
    ls.add_argument("--kind", choices=["passage", "rule", "example"])
    ls.add_argument("--scope", default="", help="e.g. 'natal', 'horary', 'KP'")
    ls.add_argument("--house", type=int)
    ls.add_argument("--limit", type=int, default=8)
    ls.add_argument("--full", action="store_true", help="print each passage in full")
    lp = lsub.add_parser("passage", help="read a citation token back, e.g. HTJAH-I:1586")
    lp.add_argument("cite")
    lp.add_argument("--context", type=int, default=5)

    st = sub.add_parser("study", help="write the study site (Raman's charts beside the engine)")
    st.add_argument("--out", default="data/study")
    st.add_argument("--only", default="", help="comma-separated record ids")
    st.add_argument("--readings", action="store_true", help="also write a cited reading per chart (slow)")

    sb = sub.add_parser("spread-baseline", help="regenerate the random-chart spread baseline")
    sb.add_argument("--n", type=int, default=2000)
    sb.add_argument("--seed", type=int, default=20261105)

    sv = sub.add_parser("serve", help="all three tools in the browser, on this machine only")
    sv.add_argument("--port", type=int, default=8765)

    a = ap.parse_args(argv)
    _utf8()

    if a.cmd == "read":
        from app.raman_saab.cited import reading as R
        if a.golden:
            r = R.from_golden(a.golden, stability=not a.no_stability)
        else:
            missing = [k for k in ("name", "date", "time", "tz", "lat", "lon") if getattr(a, k) is None]
            if missing:
                ap.error("read needs --golden, or all of --name --date --time --tz --lat --lon "
                         f"(missing: {', '.join(missing)})")
            r = R.from_birth(a.name, a.date, a.time, a.tz, a.lat, a.lon, ayanamsa=a.ayanamsa,
                             stability=not a.no_stability)
        text = R.to_html(r) if a.format == "html" else R.to_markdown(r)
        if a.out:
            Path(a.out).write_text(text, encoding="utf-8")
            print(f"wrote {a.out}")
        else:
            print(text)
        return 0

    if a.cmd == "library":
        from app.raman_saab.cited import corpus, library as L
        if a.lcmd == "build":
            counts = L.build()
            print(f"built {L.INDEX}: " + ", ".join(f"{v} {k}s" for k, v in counts.items()))
            return 0
        if a.lcmd == "search":
            kinds = (a.kind,) if a.kind else L.KINDS
            res = L.search(a.query, kinds=kinds, scope=a.scope, house=a.house, limit=a.limit)
            print(L.to_text(res, with_text=a.full))
            return 0
        p = corpus.passage(a.cite, context=a.context)
        if p is None:
            print(f"{a.cite}: cannot be read here (unknown book, bad token, or text not on disk)")
            return 1
        print(f"{p['title']}  [{p['scope']}]  lines {p['lo']}-{p['hi']}\n")
        print(p["text"])
        return 0

    if a.cmd == "study":
        from app.raman_saab.cited import study as S
        only = tuple(x.strip() for x in a.only.split(",") if x.strip())
        res = S.write_site(Path(a.out), only=only, readings=a.readings)
        print(f"wrote {a.out}/index.html: {res}")
        return 0

    if a.cmd == "spread-baseline":
        import json
        from app.raman_saab.cited import spread as SP
        b = SP.build_baseline(a.n, a.seed)
        SP.BASELINE_PATH.write_text(json.dumps(b, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {SP.BASELINE_PATH}: {len(b['matters'])} matters, mean both-ways share "
              f"{b['mean_both_share']}")
        return 0

    if a.cmd == "serve":
        from app.raman_saab.cited.server import serve
        serve(a.port)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
