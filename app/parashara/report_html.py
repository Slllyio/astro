"""Standalone HTML surface for the Parashara reading.

`to_html(reading)` renders the complete cited markdown report (`to_markdown`) into a self-contained,
theme-aware HTML document — every section the engine computes, no external assets. It reuses the
already-complete markdown (guarded by `test_report_completeness.py`) via the installed `markdown`
library's table support, so the HTML never drifts from the markdown's coverage.

Usage:
    from app.parashara.report_html import to_html
    html = to_html(read(chart))     # a full <!doctype html> document string
"""
from __future__ import annotations

import markdown as _markdown

from app.parashara.reading import ParasharaReading
from app.parashara.render import to_markdown

_CSS = """
:root { --bg:#fdfdfc; --fg:#1a1a1a; --muted:#666; --line:#e2e2df; --accent:#7a4a12;
        --thead:#f4f1ec; --code:#f0efec; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#16150f; --fg:#e8e6df; --muted:#a0998a; --line:#333026; --accent:#d9a441;
          --thead:#211f17; --code:#211f17; } }
* { box-sizing: border-box; }
body { background:var(--bg); color:var(--fg); margin:0;
       font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,serif;
       -webkit-text-size-adjust:100%; }
main { max-width: 900px; margin: 0 auto; padding: 2.2rem 1.3rem 4rem; }
h1,h2,h3 { line-height:1.25; font-weight:650; }
h1 { font-size:1.7rem; border-bottom:2px solid var(--accent); padding-bottom:.4rem; }
h2 { font-size:1.28rem; margin-top:2.2rem; border-bottom:1px solid var(--line); padding-bottom:.25rem; }
h3 { font-size:1.08rem; margin-top:1.5rem; color:var(--accent); }
p, li { color:var(--fg); }
blockquote { margin:.6rem 0; padding:.4rem .9rem; border-left:3px solid var(--accent);
             background:var(--code); color:var(--muted); border-radius:0 4px 4px 0; }
code { background:var(--code); padding:.1rem .35rem; border-radius:3px; font-size:.9em; }
table { border-collapse:collapse; width:100%; margin:.8rem 0; font-size:.92rem; display:block;
        overflow-x:auto; }
th,td { border:1px solid var(--line); padding:.38rem .6rem; text-align:left; vertical-align:top; }
thead th { background:var(--thead); position:sticky; top:0; }
tr:nth-child(even) td { background:color-mix(in srgb, var(--thead) 45%, transparent); }
a { color:var(--accent); }
.footer { margin-top:3rem; padding-top:1rem; border-top:1px solid var(--line);
          color:var(--muted); font-size:.85rem; }
"""


def to_html(reading: ParasharaReading) -> str:
    """The full reading as a standalone, theme-aware HTML document string."""
    body = _markdown.markdown(
        to_markdown(reading),
        extensions=["tables", "sane_lists", "attr_list"],
        output_format="html5",
    )
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>Parashara reading (BPHS engine)</title>"
        f"<style>{_CSS}</style></head><body><main>\n{body}\n"
        "<div class=\"footer\">Parashara (BPHS) engine · every statement cites its own sloka line "
        "(WORK:line) · a scholarly instrument answering “what would Parashara say”.</div>"
        "</main></body></html>"
    )
