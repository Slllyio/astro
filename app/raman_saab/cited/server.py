"""A local browser front for the three tools, on the Python standard library only.

    python -m app.raman_saab.cited serve [--port 8765]

Binds to 127.0.0.1, so it is reachable from this machine only. Nothing is sent anywhere.

Pages:
    /                      search box, birth-data form, links
    /search?q=...          the library (passages, rules, Raman's worked charts)
    /passage?cite=...      any citation token read back with its surrounding lines
    /study/                Raman's worked charts beside the engine
    /study/<record>.html   one chart
    /read?golden=<record>  the cited reading of one of Raman's charts
    /read?name=&date=&time=&tz=&lat=&lon=   the cited reading of any chart
"""
from __future__ import annotations

import traceback
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

from app.raman_saab.cited import corpus, library, reading, study
from app.raman_saab.cited.html import e, page

NAV = ("<a href='/'>Home</a> · <a href='/search'>Library</a> · <a href='/study/'>Worked charts</a>")
_LABEL = {"passage": "Passages from the books", "rule": "Rules in the engine that encode them",
          "example": "Raman's worked charts"}


def _hl(snippet: str) -> str:
    return e(snippet).replace("[[", "<mark>").replace("]]", "</mark>")


def search_page(q: str, kind: str = "", scope: str = "") -> str:
    kinds = (kind,) if kind in library.KINDS else library.KINDS
    sel = lambda name, opts, cur: (f"<select name={name}>" + "".join(
        f"<option value='{e(k)}'{' selected' if k == cur else ''}>{e(lab)}</option>" for k, lab in opts)
        + "</select>")
    form = ("<form class=search action=/search><input type=text name=q autofocus "
            f"placeholder='e.g. seventh lord in the eighth' value='{e(q)}'>"
            + sel("kind", [("", "everything")] + [(k, _LABEL[k]) for k in library.KINDS], kind)
            + sel("scope", [("", "all books"), ("Raman, natal", "Raman, natal"), ("horary", "horary"),
                            ("KP", "KP Readers"), ("classical", "Classical, not Raman")], scope)
            + "<button>Search</button></form>")
    body = ["<h1>The classical library</h1>", form,
            "<p class=mute><small>Plain word search over the books' own text, the engine's rules "
            "and Raman's worked conclusions. It returns what the books say and where; it never "
            "paraphrases them.</small></p>"]
    if q:
        try:
            res = library.search(q, kinds=kinds, scope=scope, limit=12)
        except FileNotFoundError as ex:
            return page("Library", "\n".join(body + [f"<div class=notice>{e(ex)}</div>"]), nav=NAV)
        body.append("<p><small>Searched for: " + " and ".join(
            "(" + " or ".join(e(t) for t in g) + ")" for g in res.searched)
            + f" · matching {e(res.mode)}</small></p>")
        if not res.hits:
            body.append("<p>Nothing found. Try fewer or plainer words.</p>")
        for k in library.KINDS:
            hs = [h for h in res.hits if h.kind == k]
            if not hs:
                continue
            body.append(f"<h2>{e(_LABEL[k])}</h2>")
            for h in hs:
                link = f"/passage?cite={quote(h.cite)}"
                extra = ""
                if k == "example":
                    rid = h.detail.split(" ", 1)[0]
                    extra = (f" · <a href='/study/{e(study._slug(rid))}'>study this chart</a>"
                             f" · <a href='/read?golden={quote(rid)}'>cited reading</a>")
                body.append(f"<div class=card style='margin:8px 0'><div><a href='{link}'><b>{e(h.cite)}</b></a> "
                            f"<span class=pill>{e(h.scope)}</span> {e(h.title)}{extra}</div>"
                            f"<div>{_hl(h.snippet)}</div></div>")
    return page("Library" + (f": {q}" if q else ""), "\n".join(body), nav=NAV)


def passage_page(cite: str, context: int = 12) -> str:
    p = corpus.passage(cite, context=context)
    if p is None:
        return page("Passage", f"<h1>{e(cite)}</h1><p>This citation cannot be read on this machine "
                    "(unknown book, bad token, or the book text is not here).</p>", nav=NAV)
    lines = p["text"].splitlines()
    first = p["lo"]
    out = []
    for i, ln in enumerate(lines):
        no = first + i
        txt = e(ln)
        if p["start"] <= no <= p["end"]:
            txt = f"<mark>{txt}</mark>"
        out.append(f"<span class=mute>{no:>6}</span>  {txt}")
    prev_c = f"{p['work']}:{max(1, p['start'] - 2 * context - 1)}"
    next_c = f"{p['work']}:{p['end'] + 2 * context + 1}"
    body = (f"<h1>{e(p['title'])}</h1><p><span class=pill>{e(p['scope'])}</span> "
            f"<b>{e(cite)}</b> (highlighted), with {context} lines either side.</p>"
            f"<pre class=src>{chr(10).join(out)}</pre>"
            f"<p><a href='/passage?cite={quote(prev_c)}'>earlier</a> · "
            f"<a href='/passage?cite={quote(next_c)}'>later</a></p>")
    return page(cite, body, nav=NAV)


HOME_FORM = """<h2>A cited reading of any chart</h2>
<form class=search action=/read>
<input type=text name=name placeholder=Name required>
<input type=text name=date placeholder=YYYY-MM-DD required size=10>
<input type=text name=time placeholder=HH:MM required size=5>
<input type=text name=tz placeholder='UTC offset, e.g. 5.5' required size=8>
<input type=text name=lat placeholder=Latitude required size=8>
<input type=text name=lon placeholder=Longitude required size=8>
<button>Read</button></form>
<p class=mute><small>Takes a few seconds: every house is also re-judged at six shifted birth times.</small></p>"""


def home_page() -> str:
    body = ["<h1>Raman, cited</h1>",
            f"<div class=notice>{e(reading.HONESTY)}</div>",
            "<h2>Search the books</h2><form class=search action=/search><input type=text name=q "
            "placeholder='e.g. Saturn aspecting the seventh lord'><button>Search</button></form>",
            HOME_FORM,
            "<h2>Study Raman's own charts</h2><p><a href='/study/'>His worked charts beside the engine</a>, "
            "house by house, with his words and the rules.</p>"]
    return page("Raman, cited", "\n".join(body), nav=NAV)


@lru_cache(maxsize=1)
def _studies() -> dict[str, study.ChartStudy]:
    return {s.id: s for s in study.all_studies()}


@lru_cache(maxsize=64)
def _golden_reading(rid: str) -> str:
    return reading.to_html(reading.from_golden(rid))


class Handler(BaseHTTPRequestHandler):
    def _send(self, html: str, status: int = 200) -> None:
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):  # quieter console
        pass

    def do_GET(self) -> None:  # noqa: N802
        u = urlparse(self.path)
        qs = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/":
                return self._send(home_page())
            if u.path == "/search":
                return self._send(search_page(qs.get("q", ""), qs.get("kind", ""), qs.get("scope", "")))
            if u.path == "/passage":
                return self._send(passage_page(qs.get("cite", "")))
            if u.path in ("/study", "/study/"):
                return self._send(study.index_html(list(_studies().values()),
                                                   href=lambda rid: f"/study/{study._slug(rid)}"))
            if u.path.startswith("/study/"):
                rid = u.path[len("/study/"):].removesuffix(".html")
                s = _studies().get(rid)
                if s is None:
                    return self._send(page("Not found", "<p>No such chart.</p>", nav=NAV), 404)
                return self._send(study.chart_html(s, reading_href=f"/read?golden={quote(rid)}",
                                                   index_href="/study/"))
            if u.path == "/read":
                if qs.get("golden"):
                    return self._send(_golden_reading(qs["golden"]))
                r = reading.from_birth(qs["name"], qs["date"], qs["time"], float(qs["tz"]),
                                       float(qs["lat"]), float(qs["lon"]))
                return self._send(reading.to_html(r))
            return self._send(page("Not found", "<p>No such page.</p>", nav=NAV), 404)
        except (KeyError, ValueError) as ex:
            return self._send(page("Bad request", f"<p>Could not read the request: {e(ex)}</p>", nav=NAV), 400)
        except Exception:  # pragma: no cover - show the error locally rather than drop the page
            return self._send(page("Error", f"<pre>{e(traceback.format_exc())}</pre>", nav=NAV), 500)


def serve(port: int = 8765, host: str = "127.0.0.1") -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Serving on http://{host}:{port}/  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
