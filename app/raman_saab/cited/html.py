"""One self-contained HTML shell shared by the cited reading, the library and the study pages.
No external assets: every page opens from disk, offline, and prints cleanly."""
from __future__ import annotations

from html import escape

CSS = """
:root{--bg:#fbfaf7;--fg:#1d1b18;--mute:#6b665e;--line:#e3dfd6;--card:#fff;--fav:#1f6f43;
--mix:#8a6a12;--aff:#9b2c2c;--acc:#33507a;--quote:#f3f0e8}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#171614;--fg:#ece8e0;
--mute:#a39d92;--line:#34312c;--card:#1f1e1b;--fav:#6fc191;--mix:#e0bb57;--aff:#ef8a8a;
--acc:#9db8e3;--quote:#262420}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.55 Georgia,'Iowan Old Style',serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.8rem;margin:.2em 0}h2{font-size:1.35rem;margin:1.6em 0 .4em;border-bottom:1px solid var(--line);padding-bottom:.2em}
h3{font-size:1.08rem;margin:1.2em 0 .3em}
a{color:var(--acc)}small,.mute{color:var(--mute)}
.notice{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--acc);padding:12px 16px;margin:16px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:.92rem}
th,td{border-bottom:1px solid var(--line);padding:5px 6px;text-align:left;vertical-align:top}
th{font-weight:600;color:var(--mute)}
.wrap{overflow-x:auto}
.v-favourable{color:var(--fav);font-weight:600}.v-mixed{color:var(--mix);font-weight:600}
.v-afflicted{color:var(--aff);font-weight:600}.v-insufficient-evidence{color:var(--mute);font-weight:600}
.pill{display:inline-block;border:1px solid var(--line);border-radius:10px;padding:0 7px;font-size:.8rem;color:var(--mute)}
details{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:6px 10px;margin:6px 0}
summary{cursor:pointer}
blockquote,pre.src{background:var(--quote);margin:6px 0;padding:8px 12px;border-left:3px solid var(--line);
white-space:pre-wrap;font:14px/1.5 Georgia,serif;max-height:32em;overflow:auto}
.rule{margin:10px 0 14px}.rule .head{font-weight:600}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media (max-width:720px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:10px 14px}
mark{background:#f5e3a1;color:#1d1b18}
form.search{display:flex;gap:8px;flex-wrap:wrap}form.search input[type=text]{flex:1;min-width:200px;padding:8px;font-size:1rem}
form.search select,form.search button{padding:8px}
nav{font-size:.9rem;margin-bottom:8px}
@media print{details{border:none}details>summary{display:none}details:not([open])>*{display:block}}
"""


def page(title: str, body: str, *, nav: str = "") -> str:
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{escape(title)}</title><style>{CSS}</style></head><body><main>"
            f"{('<nav>' + nav + '</nav>') if nav else ''}{body}</main></body></html>")


def v(verdict: str) -> str:
    """A verdict word, coloured."""
    s = escape(str(verdict))
    return f"<span class='v-{s}'>{s}</span>"


def e(x: object) -> str:
    return escape(str(x))


def src_block(p: dict | None, cite: str, *, label: str = "the book's text") -> str:
    """A collapsible verbatim passage, or a plain note when the text is not on this machine."""
    if p is None:
        return f"<div class=mute><small>{e(cite)}: text not on this machine</small></div>"
    rng = f"lines {p['lo']}-{p['hi']}" if p["lo"] != p["hi"] else f"line {p['lo']}"
    return (f"<details><summary><small>{e(label)}, {e(p['work'])} {rng}</small></summary>"
            f"<pre class=src>{e(p['text'])}</pre></details>")
