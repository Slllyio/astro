"""Birth-time rectification CLI — drive a stateful RectificationSession from the shell.

Never writes engine source; the only artifact is the --session JSON file (inputs +
history; scores recompute each run). Dual-ayanamsa (raman + lahiri) is the default and
the reports render both tracks side-by-side.

Usage:
    py -3.12 -m tools.raman_saab.rectify new --session S.json --mode rectify \\
        --date 1989-10-12 --time 10:02 --window-min 60 --tz 5.5 --lat 27.23 --lon 79.03
    py -3.12 -m tools.raman_saab.rectify new --session S.json --mode discover \\
        --date 1989-10-12 --tz 5.5 --lat 27.23 --lon 79.03
    py -3.12 -m tools.raman_saab.rectify add-event --session S.json --type marriage --date 2017-12-04
    py -3.12 -m tools.raman_saab.rectify add-fact  --session S.json --subject mother --observed afflicted
    py -3.12 -m tools.raman_saab.rectify run       --session S.json [--top 8] [--format text|markdown]
    py -3.12 -m tools.raman_saab.rectify status    --session S.json
    py -3.12 -m tools.raman_saab.rectify report    --session S.json [--top 8] [--format text|markdown]
"""
from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

from app.raman_saab.rectification.events import EVENT_TAXONOMY, LifeEvent, resolve_fact
from app.raman_saab.rectification.report import to_markdown, to_text
from app.raman_saab.rectification.session import RectificationSession


def _parse_date_parts(token: str) -> tuple[int, int | None, int | None]:
    """'YYYY' | 'YYYY-MM' | 'YYYY-MM-DD' -> (year, month|None, day|None); the token
    shape IS the stated precision (resolution honesty starts at the parser)."""
    parts = token.split("-")
    if not 1 <= len(parts) <= 3 or not all(p.isdigit() for p in parts):
        raise SystemExit(f"bad --date {token!r}: use YYYY, YYYY-MM or YYYY-MM-DD")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else None
    day = int(parts[2]) if len(parts) > 2 else None
    return year, month, day


def _cmd_new(args: argparse.Namespace) -> int:
    y, mo, d = _parse_date_parts(args.date)
    if mo is None or d is None:
        raise SystemExit("--date for `new` needs the full YYYY-MM-DD birth date")
    time = None
    if args.time:
        hh, _, mm = args.time.partition(":")
        time = (int(hh), int(mm or 0))
    session = RectificationSession.new(
        mode=args.mode, date=(y, mo, d), lat=args.lat, lon=args.lon, tz=args.tz,
        time=time, window_minutes=args.window_min)
    session.save(Path(args.session))
    print(f"session created: {args.session} (mode={args.mode}, "
          f"ayanamsas={'+'.join(session.ayanamsas)})")
    return 0


def _cmd_add_event(args: argparse.Namespace) -> int:
    if args.type not in EVENT_TAXONOMY:
        hint = difflib.get_close_matches(args.type, EVENT_TAXONOMY, n=3)
        raise SystemExit(
            f"unknown --type {args.type!r}\nvalid types: "
            + ", ".join(sorted(EVENT_TAXONOMY))
            + (f"\ndid you mean: {', '.join(hint)}?" if hint else ""))
    y, mo, d = _parse_date_parts(args.date)
    session = RectificationSession.load(Path(args.session))
    session.add_event(LifeEvent(args.type, y, mo, d, description=args.note or ""))
    session.save(Path(args.session))
    print(f"added {args.type} @ {args.date} "
          f"({session.events[-1].precision} precision); {len(session.events)} event(s)")
    return 0


def _cmd_add_fact(args: argparse.Namespace) -> int:
    session = RectificationSession.load(Path(args.session))
    try:
        fact = resolve_fact(args.subject, args.observed, description=args.note or "")
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    session.add_fact(fact)
    session.save(Path(args.session))
    print(f"added fact {fact.subject} (H{fact.house}) = {fact.observed}; "
          f"{len(session.facts)} fact(s)")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    session = RectificationSession.load(Path(args.session))
    if not session.events and not session.facts:
        raise SystemExit("no evidence yet — add-event / add-fact first")
    report = session.evaluate(top_k=args.top)
    session.save(Path(args.session))
    print(to_markdown(report) if args.format == "markdown" else to_text(report))
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    session = RectificationSession.load(Path(args.session))
    print(f"mode={session.mode}  birth={session.year}-{session.month:02d}-"
          f"{session.day:02d}  stated_time={session.stated_time}  "
          f"window=+/-{session.window_minutes}min  "
          f"ayanamsas={'+'.join(session.ayanamsas)}")
    print(f"evidence: {len(session.events)} event(s), {len(session.facts)} fact(s)")
    for ev in session.events:
        date = f"{ev.year}" + (f"-{ev.month:02d}" if ev.month else "") + (
            f"-{ev.day:02d}" if ev.day else "")
        print(f"  event {ev.event_type:20} {date}  ({ev.precision})")
    for f in session.facts:
        print(f"  fact  {f.subject:20} H{f.house} = {f.observed}")
    if not session.history:
        print("no evaluation rounds yet — use `run`")
    for i, r in enumerate(session.history, 1):
        tops = "; ".join(f"{ay}@{t}={total:+.2f}" for ay, t, total in r.top[:3])
        print(f"round {i} [{r.timestamp}] {r.n_events}ev/{r.n_facts}fa "
              f"{r.n_candidates} classes -> {tops}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rectify", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_new = sub.add_parser("new", help="create a session")
    p_new.add_argument("--session", required=True)
    p_new.add_argument("--mode", choices=("rectify", "discover"), required=True)
    p_new.add_argument("--date", required=True, help="birth date YYYY-MM-DD")
    p_new.add_argument("--time", help="stated birth time HH:MM (rectify mode)")
    p_new.add_argument("--window-min", type=int, default=60)
    p_new.add_argument("--tz", type=float, required=True)
    p_new.add_argument("--lat", type=float, required=True)
    p_new.add_argument("--lon", type=float, required=True)
    p_new.set_defaults(fn=_cmd_new)

    p_ev = sub.add_parser("add-event", help="add a dated life event")
    p_ev.add_argument("--session", required=True)
    p_ev.add_argument("--type", required=True)
    p_ev.add_argument("--date", required=True, help="YYYY | YYYY-MM | YYYY-MM-DD")
    p_ev.add_argument("--note", default="")
    p_ev.set_defaults(fn=_cmd_add_event)

    p_fa = sub.add_parser("add-fact", help="add a non-dated natal fact")
    p_fa.add_argument("--session", required=True)
    p_fa.add_argument("--subject", required=True,
                      help="signification key, e.g. mother / career / spouse")
    p_fa.add_argument("--observed", required=True,
                      choices=("favourable", "mixed", "afflicted"))
    p_fa.add_argument("--note", default="")
    p_fa.set_defaults(fn=_cmd_add_fact)

    for name, helptext in (("run", "evaluate and print the report"),
                           ("report", "alias of run")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--session", required=True)
        p.add_argument("--top", type=int, default=8)
        p.add_argument("--format", choices=("text", "markdown"), default="text")
        p.set_defaults(fn=_cmd_run)

    p_st = sub.add_parser("status", help="show session state from history (no recompute)")
    p_st.add_argument("--session", required=True)
    p_st.set_defaults(fn=_cmd_status)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
