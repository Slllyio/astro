"""HTML presenter for the detailed report — the two-voice reading as a shareable page.

Renders a `DetailedReport` (app/raman_saab/detailed_report.py) as a self-contained, theme-aware
HTML document. The design encodes the report's own thesis in its type system: a **serif** doctrine
voice (Raman, authoritative), a **sans** instrument voice (the empirical population disclosure,
set behind a slate-teal rail), and a **mono** data voice (the raw divisional deep-reads). The
verdict path is never touched here — this is presentation over already-judged data.

`to_html(report)` returns body content + an inline <style> (ready to drop into an Artifact skeleton);
`standalone_html(report)` wraps it in a full document for local viewing / CLI `--format html`.
"""
from __future__ import annotations

import html
import re

from app.raman_saab.detailed_report import DetailedReport
from app.raman_saab.render import _jd_to_date

_HOUSE_NAME = {1: "Self / Body", 2: "Wealth / Family", 3: "Siblings / Courage", 4: "Mother / Home",
               5: "Children / Mind", 6: "Health / Enemies", 7: "Spouse / Partnership",
               8: "Longevity", 9: "Father / Fortune", 10: "Career", 11: "Gains",
               12: "Loss / Moksha / Spirituality"}

_CSS = """
:root {
  --bg:#f6f7fb; --surface:#ffffff; --ink:#1a1c28; --ink-soft:#565a6e; --rule:#e2e4ee;
  --doctrine:#3b3f8f; --instrument:#3f6b72; --instrument-soft:#3f6b7218;
  --afflicted:#a24b3b; --favourable:#3e7a5e; --mixed:#7a7e8c; --warn:#b0553e;
  --tag-bg:#eceef6; --tag-ink:#4a4e63;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --mono:ui-monospace,"Cascadia Code","SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#0f111a; --surface:#161824; --ink:#e7e8ef; --ink-soft:#a0a3b4; --rule:#262a3a;
  --doctrine:#9498e8; --instrument:#7fb0b8; --instrument-soft:#7fb0b81c;
  --afflicted:#d08872; --favourable:#74b593; --mixed:#9498a8; --warn:#e0987f;
  --tag-bg:#20233250; --tag-ink:#b7bacb;
}}
:root[data-theme="dark"]{
  --bg:#0f111a; --surface:#161824; --ink:#e7e8ef; --ink-soft:#a0a3b4; --rule:#262a3a;
  --doctrine:#9498e8; --instrument:#7fb0b8; --instrument-soft:#7fb0b81c;
  --afflicted:#d08872; --favourable:#74b593; --mixed:#9498a8; --warn:#e0987f;
  --tag-bg:#20233250; --tag-ink:#b7bacb;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  line-height:1.6;-webkit-font-smoothing:antialiased}
.doc{max-width:760px;margin:0 auto;padding:clamp(1.2rem,4vw,3.5rem) clamp(1rem,4vw,2rem)}
.eyebrow{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--instrument);
  font-weight:600}
.name{font-family:var(--serif);font-weight:600;font-size:clamp(2rem,5.5vw,3.1rem);line-height:1.08;
  margin:.35rem 0 .5rem;text-wrap:balance;color:var(--doctrine)}
.birth{font-family:var(--mono);font-size:.82rem;color:var(--ink-soft)}
.sig{display:flex;flex-wrap:wrap;gap:.5rem;margin:1.1rem 0 0}
.sig-chip{background:var(--surface);border:1px solid var(--rule);border-radius:999px;
  padding:.28rem .7rem;font-size:.78rem}
.sig-chip b{color:var(--doctrine);font-weight:600}
.legend{margin:1.8rem 0 0;padding:1rem 1.1rem;border:1px solid var(--rule);border-radius:12px;
  background:var(--surface);font-size:.86rem;color:var(--ink-soft)}
.legend .v-serif{font-family:var(--serif);color:var(--ink);font-weight:600}
.legend .v-sans{color:var(--instrument);font-weight:600}
h2.section{font-family:var(--serif);font-weight:600;font-size:1.5rem;margin:2.6rem 0 .3rem;
  padding-top:1.6rem;border-top:1px solid var(--rule);text-wrap:balance}
.section-sub{color:var(--ink-soft);font-size:.86rem;margin:.2rem 0 1.2rem}
.long{font-family:var(--serif);font-size:1.15rem}
.long b{color:var(--doctrine)}
.long-combos{list-style:none;padding:0;margin:.7rem 0 0}
.long-combos li{padding:.15rem 0;font-size:.9rem;color:var(--ink-soft)}
.house{padding:1.4rem 0;border-bottom:1px solid var(--rule)}
.house-head{display:flex;align-items:baseline;flex-wrap:wrap;gap:.6rem}
.house-head h3{font-family:var(--serif);font-weight:600;font-size:1.18rem;margin:0}
.house-num{color:var(--instrument);font-variant-numeric:tabular-nums}
.doctrine{font-family:var(--serif);font-size:1.05rem;margin:.6rem 0 0}
.doctrine strong{color:var(--doctrine);font-weight:600}
.chip{font-family:var(--sans);font-size:.7rem;font-weight:600;letter-spacing:.04em;
  text-transform:uppercase;padding:.16rem .5rem;border-radius:6px;white-space:nowrap}
.chip--afflicted{background:color-mix(in srgb,var(--afflicted) 16%,transparent);color:var(--afflicted)}
.chip--favourable{background:color-mix(in srgb,var(--favourable) 16%,transparent);color:var(--favourable)}
.chip--mixed{background:var(--tag-bg);color:var(--tag-ink)}
.active-badge{font-size:.68rem;font-weight:600;letter-spacing:.05em;text-transform:uppercase;
  color:var(--favourable)}
.instrument{margin:.9rem 0 0;padding:.75rem 0 .2rem 1rem;border-left:2px solid var(--instrument);
  background:var(--instrument-soft)}
.instrument-label{font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--instrument);font-weight:600;margin-bottom:.5rem}
.cal-row{display:grid;grid-template-columns:minmax(90px,1.3fr) minmax(70px,1fr) 2.4fr;
  gap:.7rem;align-items:center;padding:.22rem 0;font-size:.82rem}
.cal-row.muted{color:var(--ink-soft);grid-template-columns:1fr;font-style:italic}
.sig-name{font-weight:600}
.meter{position:relative;height:6px;border-radius:3px;
  background:linear-gradient(90deg,color-mix(in srgb,var(--afflicted) 35%,transparent),
  color-mix(in srgb,var(--mixed) 22%,transparent),
  color-mix(in srgb,var(--favourable) 35%,transparent))}
.meter-mark{position:absolute;top:-2px;left:var(--p);width:2px;height:10px;background:var(--ink);
  border-radius:1px}
.cal-note{color:var(--ink-soft);font-variant-numeric:tabular-nums}
.tag{display:inline-block;font-size:.68rem;font-weight:600;padding:.05rem .4rem;border-radius:5px;
  margin-left:.35rem;vertical-align:middle}
.tag--warn{background:color-mix(in srgb,var(--warn) 18%,transparent);color:var(--warn)}
.tag--univ{background:var(--tag-bg);color:var(--tag-ink)}
.timeline{list-style:none;padding:0;margin:0}
.period{padding:.8rem 0 .8rem 1.1rem;border-left:2px solid var(--rule);position:relative}
.period::before{content:"";position:absolute;left:-5px;top:1.15rem;width:8px;height:8px;
  border-radius:50%;background:var(--doctrine)}
.period-head{display:flex;flex-wrap:wrap;gap:.5rem;align-items:baseline}
.period-md{font-family:var(--serif);font-weight:600;font-size:1.02rem}
.period-dates{font-family:var(--mono);font-size:.75rem;color:var(--ink-soft)}
.lit{list-style:none;padding:0;margin:.4rem 0 0;display:flex;flex-direction:column;gap:.2rem}
.lit li{font-size:.85rem;display:flex;gap:.5rem;align-items:baseline}
.lit .hlabel{color:var(--ink-soft);min-width:9.5rem}
.limited{font-size:.78rem;color:var(--ink-soft);margin-top:.35rem}
details.varga{border:1px solid var(--rule);border-radius:10px;margin:.7rem 0;background:var(--surface)}
details.varga summary{cursor:pointer;padding:.7rem 1rem;font-family:var(--serif);font-weight:600;
  font-size:1rem;list-style-position:inside}
details.varga[open] summary{border-bottom:1px solid var(--rule)}
details.varga pre{margin:0;padding:1rem;overflow-x:auto;font-family:var(--mono);font-size:.76rem;
  line-height:1.5;color:var(--ink)}
.doclist{padding-left:1.1rem;margin:.4rem 0}
.doclist li{margin:.25rem 0;font-size:.92rem}
.provenance{margin-top:2.6rem;padding-top:1.4rem;border-top:1px solid var(--rule);
  font-size:.78rem;color:var(--ink-soft)}
a:focus-visible,summary:focus-visible{outline:2px solid var(--doctrine);outline-offset:2px}
@media (prefers-reduced-motion:no-preference){details.varga{transition:background .2s}}
"""


def _esc(s: str) -> str:
    return html.escape(str(s))


def _bold(s: str) -> str:
    """Escape, then promote **markdown bold** to <strong> (the synthesis prose uses it)."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _esc(s))


def _vclass(verdict: str) -> str:
    return verdict if verdict in ("afflicted", "favourable") else "mixed"


def _cal_row(e) -> str:
    if e.favourability_percentile is None:
        return f'<div class="cal-row muted"><span>{_esc(e.signification)}: {_esc(e.verdict)} '\
               '(uncalibrated)</span></div>'
    pct = round(e.favourability_percentile * 100)
    band = round((e.band_share or 0) * 100)
    tags = ""
    if e.band_share is not None and e.band_share >= 0.5:
        tags += '<span class="tag tag--univ">near-universal</span>'
    if e.inverted_warning:
        tags += '<span class="tag tag--warn">inverted channel</span>'
    return (
        f'<div class="cal-row"><span class="sig-name">{_esc(e.signification)}</span>'
        f'<div class="meter" style="--p:{pct}%"><span class="meter-mark"></span></div>'
        f'<span class="cal-note">more favourable than {pct}% &middot; {band}% share '
        f'({_esc(e.rarity)}){tags}</span></div>')


def _house_section(mr, cal) -> str:
    active = '<span class="active-badge">active now</span>' if "ACTIVE in the running" in mr.reading \
        else ""
    rows = "".join(_cal_row(e) for e in cal.entries)
    return (
        f'<section class="house"><div class="house-head">'
        f'<h3><span class="house-num">H{mr.house}</span> &middot; {_esc(_HOUSE_NAME[mr.house])}</h3>'
        f'<span class="chip chip--{_vclass(mr.verdict)}">{_esc(mr.verdict)}</span>{active}</div>'
        f'<p class="doctrine">{_bold(mr.reading)}</p>'
        f'<div class="instrument"><div class="instrument-label">Population context '
        f'&mdash; empirical, not Raman</div>{rows}</div></section>')


def _timeline(r: DetailedReport) -> str:
    items = []
    for tp in r.timeline.periods:
        lit = ""
        for a in tp.activated:
            if a.grade == "par_excellence":
                lit += (f'<li><span class="chip chip--{_vclass(a.natal_verdict)}">H{a.house}</span>'
                        f'<span class="hlabel">{_esc(_HOUSE_NAME[a.house])}</span>'
                        f'<span>{_esc(a.natal_verdict)} ({_esc(a.natal_degree)})</span></li>')
        if not lit:
            lit = '<li class="limited">(no par-excellence house this period)</li>'
        limited = [str(a.house) for a in tp.activated if a.grade == "limited"]
        lim = f'<div class="limited">limited: {", ".join(limited)}</div>' if limited else ""
        items.append(
            f'<li class="period"><div class="period-head">'
            f'<span class="period-md">{_esc(tp.period.maha)} Dasha</span>'
            f'<span class="period-dates">{_jd_to_date(tp.period.start_jd)} &ndash; '
            f'{_jd_to_date(tp.period.end_jd)}</span></div>'
            f'<ul class="lit">{lit}</ul>{lim}</li>')
    return '<ol class="timeline">' + "".join(items) + "</ol>"


def to_html(r: DetailedReport) -> str:
    """Body content + inline <style> — ready to drop into an Artifact skeleton."""
    s, b = r.synthesis, r.birth
    y, mo, d = r.longevity_ymd
    sig = [("Lagna", s.lagna), ("Navamsa Lagna", s.navamsa_lagna), ("Atmakaraka", s.atmakaraka),
           ("Arudha", s.arudha_lagna), ("Karakamsa", s.karakamsa),
           ("Running", f"{s.running_md} MD / {s.running_ad} AD")]
    sig_html = "".join(f'<span class="sig-chip"><b>{_esc(k)}</b> {_esc(v)}</span>' for k, v in sig)

    houses = "".join(_house_section(mr, r.calibration[mr.house]) for mr in s.matters)

    combos = "".join(f"<li>{_esc(c)}</li>" for c in s.longevity_combos)
    combos_html = f'<ul class="long-combos">{combos}</ul>' if combos else ""

    vargas = "".join(
        f'<details class="varga"{" open" if i == 0 else ""}><summary>{_esc(label)}</summary>'
        f'<pre>{_esc(body.strip())}</pre></details>'
        for i, (label, body) in enumerate(r.divisional))

    extras = ""
    if s.career:
        extras += (f'<h2 class="section">Career</h2><p class="section-sub">HTJAH-II &mdash; '
                   f'navamsa-dispositor of the 10th lord</p><p class="doctrine">{_esc(s.career)}</p>')
    if s.karakamsa_reading:
        km = "".join(f"<li>{_esc(x)}</li>" for x in s.karakamsa_reading)
        extras += (f'<h2 class="section">Jaimini Karakamsa</h2><p class="section-sub">the soul\'s '
                   f'inclination</p><ul class="doclist">{km}</ul>')

    return f"""<style>{_CSS}</style>
<main class="doc">
  <header>
    <div class="eyebrow">Vedic reading &middot; Sri B. V. Raman's system</div>
    <h1 class="name">{_esc(b.name)}</h1>
    <div class="birth">Born {b.year:04d}-{b.month:02d}-{b.day:02d} {b.hour:02d}:{b.minute:02d}
      (tz {b.tz_offset:+g}) &middot; {b.latitude:.4f}, {b.longitude:.4f} &middot; Lahiri sidereal</div>
    <div class="sig">{sig_html}</div>
    <div class="legend">This reading speaks in two voices. The
      <span class="v-serif">doctrine</span> (serif) is Raman's verdict, faithful to his texts and
      unchanged. Beneath it the <span class="v-sans">instrument</span> discloses how that verdict
      compares with {r.calibration[1].population_n:,} real charts &mdash; its information content,
      <em>not</em> a validated prediction about a life.</div>
  </header>

  <h2 class="section">Longevity &mdash; Ayurdaya</h2>
  <p class="long">Numeric span <b>{r.longevity_years:g} years</b> ({y}y {mo}m {d}d) &mdash;
    <b>{_esc(r.longevity_class)}</b>.</p>
  {combos_html}

  <h2 class="section">House by house</h2>
  <p class="section-sub">Each bhava: Raman's verdict, then its population context.</p>
  {houses}

  <h2 class="section">Life-narrative</h2>
  <p class="section-sub">Vimshottari Dasha &mdash; the same promises, read as they ripen.</p>
  {_timeline(r)}

  <h2 class="section">Divisional deep-reads</h2>
  <p class="section-sub">Shodasavarga &mdash; each divisional chart magnifies one matter (Raman core
    authoritative; varga overlay report-only).</p>
  {vargas}

  {extras}

  <div class="provenance">Doctrine faithful to B. V. Raman; italicised population context is
    EMPIRICAL_ASTRODATABANK provenance (n={r.calibration[1].population_n:,}), explicitly not Raman.
    Percentiles state how this chart's reading compares with real charts under Raman's method &mdash;
    a statement about the method's output, not a validated prediction about life outcomes.</div>
</main>"""


def standalone_html(r: DetailedReport, *, title: str | None = None) -> str:
    """Full standalone document for local viewing / CLI --format html."""
    t = _esc(title or f"Detailed reading - {r.birth.name}")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{t}</title></head><body>{to_html(r)}</body></html>')
