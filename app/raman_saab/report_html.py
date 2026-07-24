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

from app.raman_saab.detailed_report import (
    GLOSSARY,
    ROLLUP_RULE,
    _HOUSE_NAME as _MD_HOUSE_NAME,
    _SIGN_NAME,
    _TIER_MEANING,
    DetailedReport,
    graded_buckets,
    plain_bhukti_summary,
    planet_rows,
    rollup_driver,
)
from app.raman_saab.primitives import nakshatra_signature
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
.md-group{margin:1.5rem 0 0}
.md-head{font-family:var(--serif);font-weight:600;font-size:1.12rem;color:var(--doctrine);
  margin:0 0 .1rem}
.theme-label{font-size:.64rem;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-soft);
  margin-right:.15rem;align-self:center}
.chip.focus{outline:2px solid var(--doctrine);outline-offset:1px}
.assoc-note{margin-top:.35rem;font-size:.8rem;color:var(--ink-soft);font-style:italic}
.assoc-note b{color:var(--doctrine);font-style:normal}
.lit-chips.lim{opacity:.6;margin-top:.25rem}
.grade-legend{margin:.2rem 0 1.2rem;padding:.8rem 1rem;border:1px solid var(--rule);
  border-radius:10px;background:var(--surface);font-size:.82rem;color:var(--ink-soft);
  display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.4rem .9rem}
.grade-legend b{color:var(--doctrine)}
.plain{margin-top:.45rem;font-size:.86rem;color:var(--ink);
  border-left:2px solid var(--instrument);padding-left:.7rem}
.plain b{color:var(--instrument);font-weight:600}
.timeline{list-style:none;padding:0;margin:0}
.period{padding:.7rem .6rem .7rem 1.1rem;border-left:2px solid var(--rule);position:relative}
.period::before{content:"";position:absolute;left:-5px;top:1.05rem;width:8px;height:8px;
  border-radius:50%;background:var(--doctrine)}
.period.now{background:var(--instrument-soft);border-radius:0 8px 8px 0}
.period.now::before{background:var(--instrument);box-shadow:0 0 0 3px var(--instrument-soft)}
.period-head{display:flex;flex-wrap:wrap;gap:.5rem;align-items:baseline}
.period-md{font-family:var(--serif);font-weight:600;font-size:.98rem}
.period-dates{font-family:var(--mono);font-size:.74rem;color:var(--ink-soft)}
.now-badge{font-size:.64rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  color:var(--instrument)}
.lit-chips{display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.4rem}
.lit-chips .chip{cursor:default}
.no-pe{font-size:.78rem;color:var(--ink-soft);margin-top:.4rem;font-style:italic}
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

/* ── table of contents ───────────────────────────────────────────── */
.toc{display:flex;flex-wrap:wrap;gap:.3rem .9rem;margin-top:1.1rem;font-size:.78rem}
.toc a{color:var(--instrument);text-decoration:none;border-bottom:1px solid transparent}
.toc a:hover{border-bottom-color:var(--instrument)}

/* ── the honesty headline ────────────────────────────────────────── */
.infobox{margin:2rem 0 0;padding:1.1rem 1.2rem;border:1px solid var(--instrument);
  border-radius:12px;background:var(--instrument-soft)}
.infobox-label{font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--instrument);font-weight:700;margin-bottom:.7rem}
.infostats{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:.7rem}
.infostats div{display:flex;flex-direction:column}
.infostats b{font-size:1.5rem;font-variant-numeric:tabular-nums;line-height:1.1}
.infostats span{font-size:.72rem;color:var(--ink-soft)}
.infostats .hi b{color:var(--doctrine)}
.infonote{font-size:.84rem;color:var(--ink-soft);margin:.8rem 0 0}

/* ── running-now box ─────────────────────────────────────────────── */
.nowbox{margin:1.8rem 0 0;padding:1.1rem 1.2rem;border:2px solid var(--doctrine);
  border-radius:12px;background:var(--surface)}
.now-head{font-family:var(--serif);font-size:1.1rem;display:flex;flex-wrap:wrap;gap:.5rem;
  align-items:baseline}
.now-head b{color:var(--doctrine)}
.now-row{display:flex;flex-wrap:wrap;gap:.3rem;align-items:center;margin-top:.6rem}

/* ── tables ──────────────────────────────────────────────────────── */
.tablewrap{overflow-x:auto}
table.grid{border-collapse:collapse;width:100%;font-size:.84rem}
table.grid th{text-align:left;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;
  color:var(--ink-soft);font-weight:600;padding:.4rem .5rem;border-bottom:1px solid var(--rule)}
table.grid td{padding:.4rem .5rem;border-bottom:1px solid var(--rule)}
table.grid .num{text-align:right;font-variant-numeric:tabular-nums}
table.grid .muted-cell{color:var(--ink-soft);font-size:.78rem}
table.sav td{text-align:center}
table.sav .strong{color:var(--favourable);font-weight:700}
table.sav .weakc{color:var(--afflicted);font-weight:700}

/* ── yogas ───────────────────────────────────────────────────────── */
.yogalist{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:.7rem}
.yogalist li{padding:.7rem .9rem;border:1px solid var(--rule);border-radius:10px;
  background:var(--surface);font-size:.88rem}
.yogalist b{font-family:var(--serif);font-size:1.02rem;color:var(--doctrine)}
.ykind{font-size:.64rem;letter-spacing:.08em;text-transform:uppercase;color:var(--instrument);
  border:1px solid var(--instrument);border-radius:5px;padding:.05rem .35rem;margin-left:.4rem}
.yeffect{color:var(--ink-soft)}
.yogalist code{font-family:var(--mono);font-size:.72rem;color:var(--ink-soft)}

/* ── house pillars + rollup driver ───────────────────────────────── */
.pillars{margin-top:.45rem;font-size:.83rem;color:var(--ink-soft)}
.pillars b{color:var(--doctrine);font-weight:600}
.driver{font-size:.72rem;color:var(--ink-soft)}
.driver b{color:var(--ink)}
.long-step{margin:.3rem 0;font-size:.9rem}

/* ── glossary ────────────────────────────────────────────────────── */
details.glossary{margin:2.4rem 0 0;border:1px solid var(--rule);border-radius:10px;
  background:var(--surface)}
details.glossary summary{cursor:pointer;padding:.8rem 1rem;font-family:var(--serif);
  font-weight:600}
details.glossary dl{margin:0;padding:0 1rem 1rem;font-size:.86rem}
details.glossary dt{font-weight:600;color:var(--doctrine);margin-top:.6rem}
details.glossary dd{margin:.1rem 0 0;color:var(--ink-soft)}

/* ── accessibility / contrast fixes ──────────────────────────────── */
.meter-mid{position:absolute;left:50%;top:-1px;width:1px;height:8px;
  background:var(--ink-soft);opacity:.45}
.meter-mark{transform:translateX(-50%)}
.tag--rare{background:color-mix(in srgb,var(--doctrine) 16%,transparent);color:var(--doctrine)}
.tag--univ{background:var(--tag-bg);color:var(--tag-ink);opacity:1}
.lit-chips.lim{opacity:1}
.lit-chips.lim .chip{background:transparent;border:1px dashed var(--rule);color:var(--ink-soft)}

@media (max-width:480px){
  .cal-row{grid-template-columns:1fr;gap:.15rem}
  .infostats b{font-size:1.25rem}
}

@media print{
  body{background:#fff;color:#000}
  .toc,.now-badge{display:none}
  details.varga,details.glossary{border:1px solid #ccc}
  details.varga>summary,details.glossary>summary{list-style:none}
  details[open]>*{display:revert}
  .house,.period,.yogalist li{break-inside:avoid}
  .infobox,.instrument{background:transparent;border:1px solid #999}
  a{color:#000;text-decoration:none}
}
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
    if e.rarity != "common":
        tags += '<span class="tag tag--rare">distinctive</span>'
    # 40-65 is the population midpoint; percentile language there is noise (and reads as a
    # contradiction next to an 'afflicted' verdict), so state plainly that it is typical.
    note = (f"typical &mdash; sits at the population midpoint &middot; {band}% share"
            if 40 <= pct <= 65 else
            f"more favourable than {pct}% of charts &middot; {band}% share")
    return (
        f'<div class="cal-row"><span class="sig-name">{_esc(e.signification)}</span>'
        f'<span class="chip chip--{_vclass(e.verdict)}">{_esc(e.verdict)}'
        f'{" " + _esc(e.degree) if e.degree else ""}</span>'
        f'<div class="meter" style="--p:{pct}%"><span class="meter-mid"></span>'
        f'<span class="meter-mark"></span></div>'
        f'<span class="cal-note">{note}{tags}</span></div>')


def _house_section(mr, cal, pf, chart) -> str:
    """One bhava: Raman's pillars + verdict (with the rollup driver named), then the overlay."""
    active = '<span class="active-badge">active now</span>' if "ACTIVE in the running" in mr.reading \
        else ""
    rows = "".join(_cal_row(e) for e in cal.entries)
    driver = rollup_driver(cal, mr.verdict)
    drv = (f'<span class="driver">driven by <b>{_esc(driver)}</b></span>' if driver else "")

    pillars = ""
    if pf is not None and pf.significations:
        led = pf.significations[0].ledger
        lp = chart.planets.get(pf.lord)
        bits = [f'<b>Lord</b> {_esc(pf.lord)}'
                + (f' in H{lp.rasi_house}' if lp is not None else "")
                + ("" if led.lord_strong is None else
                   f' ({"strong" if led.lord_strong else "weak"})'),
                f'<b>Karaka</b> {_esc(led.karaka)}'
                + ("" if led.karaka_strong is None else
                   f' ({"strong" if led.karaka_strong else "weak"})')
                + ("" if led.karaka_intact else " [afflicted]"),
                f'<b>Navamsa</b> {_esc(led.navamsa_status)}']
        if led.bhava_bala is not None:
            bits.append(f'<b>Bhava Bala</b> {led.bhava_bala:.0f}')
        pillars = f'<div class="pillars">{" &middot; ".join(bits)}</div>'

    return (
        f'<section class="house"><div class="house-head">'
        f'<h3><span class="house-num">H{mr.house}</span> &middot; {_esc(_HOUSE_NAME[mr.house])}</h3>'
        f'<span class="chip chip--{_vclass(mr.verdict)}">{_esc(mr.verdict)}</span>{drv}{active}</div>'
        f'{pillars}<p class="doctrine">{_bold(mr.reading)}</p>'
        f'<div class="instrument"><div class="instrument-label">Population context '
        f'&mdash; empirical, not Raman</div>{rows}</div></section>')


def _house_chip(a, *, ring: bool = False) -> str:
    """A house chip carrying its natal verdict (title = full verdict); ring = par-excellence."""
    return (f'<span class="chip chip--{_vclass(a.natal_verdict)}{" focus" if ring else ""}" '
            f'title="{_esc(_HOUSE_NAME[a.house])}: {_esc(a.natal_verdict)} '
            f'({_esc(a.natal_degree)})">H{a.house}</span>')


def _info_box(r: DetailedReport) -> str:
    """The honesty headline: how much of this document actually distinguishes this chart."""
    i = r.info
    return (
        f'<div class="infobox"><div class="infobox-label">Information content of this reading</div>'
        f'<div class="infostats">'
        f'<div><b>{i.total}</b><span>readings</span></div>'
        f'<div><b>{i.modal_count}</b><span>most common verdict</span></div>'
        f'<div><b>{i.near_universal}</b><span>near-universal</span></div>'
        f'<div><b>{i.inverted}</b><span>proven inverted</span></div>'
        f'<div class="hi"><b>{i.distinctive}</b><span>genuinely distinctive</span></div>'
        f'</div><p class="infonote">Most of this document is generic: {i.modal_count} of '
        f'{i.total} readings return the single most common verdict ({_esc(i.modal_verdict)}). '
        f'This is a disclosure about the method&rsquo;s output, not a statement about a life.</p>'
        f'</div>')


def _distinctive(r: DetailedReport) -> str:
    if not r.distinctive:
        return ""
    rows = "".join(
        f'<tr><td>H{h} {_esc(_MD_HOUSE_NAME[h])}</td><td>{_esc(e.signification)}</td>'
        f'<td><span class="chip chip--{_vclass(e.verdict)}">{_esc(e.verdict)}</span></td>'
        f'<td class="num">{e.favourability_percentile:.0%}</td>'
        f'<td class="num">{e.band_share:.0%}</td></tr>' for h, e in r.distinctive)
    return (
        '<h2 class="section" id="stands-out">What stands out</h2>'
        '<p class="section-sub">The readings furthest from the population midpoint &mdash; where '
        'this chart is least like everyone else&rsquo;s.</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>house</th><th>matter</th>'
        '<th>verdict</th><th class="num">percentile</th><th class="num">share</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>')


def _positions(r: DetailedReport) -> str:
    rows = []
    for name, p in planet_rows(r.chart):
        nk = nakshatra_signature.signature_for(p.nakshatra)
        notes = []
        if p.retrograde:
            notes.append("R")
        if p.vargottama:
            notes.append("vargottama")
        if getattr(p, "combust_fraction", 0) >= 0.5:
            notes.append("combust")
        rows.append(
            f'<tr><td><b>{_esc(name)}</b></td><td>{_esc(_SIGN_NAME[p.sign])}</td>'
            f'<td class="num">{p.rasi_house}</td>'
            f'<td>{_esc(nk.name if nk else "?")} ({p.pada})</td>'
            f'<td>{_esc(_SIGN_NAME[p.navamsa_sign])}</td>'
            f'<td class="muted-cell">{_esc(", ".join(notes)) or "&ndash;"}</td></tr>')
    return (
        '<h2 class="section" id="positions">Planetary positions</h2>'
        '<p class="section-sub">So the reading can be checked.</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>graha</th><th>sign</th>'
        '<th class="num">house</th><th>nakshatra (pada)</th><th>navamsa</th><th>notes</th></tr>'
        f'</thead><tbody>{"".join(rows)}</tbody></table></div>')


def _yogas(r: DetailedReport) -> str:
    if not r.yogas:
        return ('<h2 class="section" id="yogas">Yogas</h2>'
                '<p class="section-sub">No encoded yoga fires on this chart.</p>')
    items = "".join(
        f'<li><b>{_esc(y.name)}</b> <span class="ykind">{_esc(y.kind)}</span><br>'
        f'<span class="yeffect">{_esc(y.effect)}</span> '
        f'<code>{_esc(y.source.work)}:{y.source.line}</code></li>' for y in r.yogas)
    return ('<h2 class="section" id="yogas">Yogas present in this chart</h2>'
            '<p class="section-sub">Each with its citation. A yoga&rsquo;s effect depends on the '
            'strength of the planets causing it (HTJAH-I:611).</p>'
            f'<ul class="yogalist">{items}</ul>')


def _sav(r: DetailedReport) -> str:
    if not r.sav:
        return ""
    head = "".join(f"<th>{_SIGN_NAME[i][:3]}</th>" for i in range(1, 13))
    cells = "".join(
        f'<td class="num{" strong" if r.sav.get(i, 0) >= 30 else " weakc" if r.sav.get(i, 0) <= 25 else ""}">'
        f'{r.sav.get(i, 0)}</td>' for i in range(1, 13))
    return ('<h2 class="section" id="sav">Ashtakavarga</h2>'
            '<p class="section-sub">Sarvashtakavarga bindus per sign; average 28 (total 337). '
            'Raman rates it corroborative, not decisive &mdash; <em>&ldquo;it does not seem to be '
            'quite reliable&rdquo;</em> (HTJAH-II:4453-4456).</p>'
            f'<div class="tablewrap"><table class="grid sav"><thead><tr>{head}</tr></thead>'
            f'<tbody><tr>{cells}</tr></tbody></table></div>')


def _now_box(r: DetailedReport) -> str:
    """The client's first question — what is running right now — answered above the fold."""
    cur = next((tp for tp in r.timeline.periods
                if tp.period.start_jd <= r.ref_jd < tp.period.end_jd), None)
    if cur is None:
        return ""
    associated, buckets = graded_buckets(cur, r.chart)
    tier = "par excellence" if associated else "ordinary"
    focus = "".join(_house_chip(a) for a in buckets[tier])
    plain = plain_bhukti_summary(cur.activated, associated)
    sade = (f'<div class="now-row"><span class="theme-label">Sade-Sati</span>'
            f'{_esc(r.synthesis.sade_sati)}</div>' if r.synthesis.sade_sati else "")
    return (
        f'<div class="nowbox" id="now"><div class="infobox-label">Running now</div>'
        f'<div class="now-head"><b>{_esc(cur.period.maha)} Mahadasha</b> &rarr; '
        f'<b>{_esc(cur.period.antar or cur.period.maha)} Antardasha</b>'
        f'<span class="period-dates">{_jd_to_date(cur.period.start_jd)} &ndash; '
        f'{_jd_to_date(cur.period.end_jd)}</span></div>'
        f'<div class="now-row"><span class="theme-label">{tier}</span>{focus}</div>'
        f'{sade}<p class="plain">{_esc(plain)}</p></div>')


def _glossary() -> str:
    items = "".join(f'<dt>{_esc(k)}</dt><dd>{_esc(v)}</dd>' for k, v in GLOSSARY.items())
    return ('<details class="glossary" id="glossary"><summary>Glossary &mdash; the technical '
            'terms in plain language</summary>'
            f'<dl>{items}</dl></details>')


def _timeline(r: DetailedReport) -> str:
    """Windowed MD -> AD narrative graded per HTJAH-I:1592-1640: houses both lords influence are
    par-excellence when the AD lord is associated with the MD lord, else ordinary; a house only one
    lord influences is limited. Current AD marked."""
    out: list[str] = []
    cur: str | None = None
    for tp in r.timeline.periods:
        rows, maha, antar = tp.activated, tp.period.maha, tp.period.antar
        if maha != cur:
            if cur is not None:
                out.append("</ol></div>")
            cur = maha
            out.append(f'<div class="md-group"><h3 class="md-head">{_esc(cur)} Mahadasha</h3>'
                       f'<ol class="timeline">')
        associated, buckets = graded_buckets(tp, r.chart)   # ONE grading implementation
        assoc = ("its own bhukti" if antar == maha
                 else f'AD <b>{"is" if associated else "is not"}</b> associated with MD')
        blocks = f'<div class="assoc-note">{assoc}</div>'
        _TITLE = {"limited": "bhukti lord only", "feeble": "MD lord only",
                  "par excellence": "both lords, AD associated with MD",
                  "ordinary": "both lords, not associated"}
        for tier, items in buckets.items():
            if not items:
                continue
            dim = " lim" if tier in ("limited", "feeble") else ""
            chips = "".join(_house_chip(a, ring=(tier == "par excellence")) for a in items)
            blocks += (f'<div class="lit-chips{dim}"><span class="theme-label" '
                       f'title="{_TITLE[tier]}">{tier}</span>{chips}</div>')
        plain = plain_bhukti_summary(rows, associated)
        head, _, tail = plain.partition(":")
        blocks += f'<div class="plain"><b>{_esc(head)}:</b>{_esc(tail)}</div>'
        now = tp.period.start_jd <= r.ref_jd < tp.period.end_jd
        badge = '<span class="now-badge">now</span>' if now else ""
        ad = antar or maha
        out.append(
            f'<li class="period{" now" if now else ""}"><div class="period-head">'
            f'<span class="period-md">{_esc(ad)} AD</span>'
            f'<span class="period-dates">{_jd_to_date(tp.period.start_jd)} &ndash; '
            f'{_jd_to_date(tp.period.end_jd)}</span>{badge}</div>{blocks}</li>')
    if cur is not None:
        out.append("</ol></div>")
    return "".join(out)


def to_html(r: DetailedReport) -> str:
    """Body content + inline <style> — ready to drop into an Artifact skeleton."""
    s, b = r.synthesis, r.birth
    y, mo, d = r.longevity_ymd
    # full parity with the markdown signature block (previously HTML dropped half of these)
    sig = [("Lagna", s.lagna), ("Navamsa Lagna", s.navamsa_lagna), ("Atmakaraka", s.atmakaraka),
           ("Arudha", s.arudha_lagna), ("Karakamsa", s.karakamsa), ("Upapada", s.upapada),
           ("Spouse-lord", s.spouse_significator), ("Stronger frame", r.overview.stronger_frame),
           ("Running", f"{s.running_md} MD / {s.running_ad} AD"), ("Chara dasha", s.chara)]
    moon = r.chart.planets.get("Moon")
    if moon is not None:
        nk = nakshatra_signature.signature_for(moon.nakshatra)
        if nk is not None:
            sig.insert(1, ("Birth nakshatra", f"{nk.name} pada {moon.pada}"))
    if s.sade_sati:
        sig.append(("Sade-Sati", s.sade_sati.replace("Sade-Sati:", "").strip()))
    if s.panchanga:
        sig.append(("Panchanga", s.panchanga))
    sig_html = "".join(f'<span class="sig-chip"><b>{_esc(k)}</b> {_esc(v)}</span>' for k, v in sig)

    houses = "".join(
        _house_section(mr, r.calibration[mr.house],
                       r.proformas[mr.house - 1] if len(r.proformas) >= mr.house else None,
                       r.chart)
        for mr in s.matters)

    combos = "".join(f"<li>{_esc(c)}</li>" for c in s.longevity_combos)
    combos_html = f'<ul class="long-combos">{combos}</ul>' if combos else ""
    if r.balarishta is not None:
        bal = ("applies" if r.balarishta.applies and not r.balarishta.cancelled
               else "cancelled" if r.balarishta.cancelled else "does not apply")
        combos_html = (f'<p class="long-step"><b>1. Balarishta</b> (early-childhood danger): '
                       f'{bal}</p><p class="long-step"><b>2. Band by combination</b></p>'
                       + combos_html)

    vargas = "".join(
        f'<details class="varga"{" open" if i == 0 else ""}><summary>{_esc(label)}</summary>'
        f'<pre>{_esc(body.strip())}</pre></details>'
        for i, (label, body) in enumerate(r.divisional))

    extras = ""
    if s.career:
        extras += (f'<h2 class="section">Career</h2><p class="section-sub">HTJAH-II &mdash; '
                   f'navamsa-dispositor of the 10th lord</p><p class="doctrine">{_bold(s.career)}</p>')
    if s.deeptadi:                       # parity: previously dropped from the HTML entirely
        extras += ('<h2 class="section">Deeptadi avasthas</h2>'
                   '<p class="section-sub">each graha&rsquo;s result-state (HPA Ch.7)</p>'
                   f'<p class="doctrine">{_esc(", ".join(s.deeptadi))}</p>')
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
    <nav class="toc"><a href="#stands-out">What stands out</a><a href="#positions">Positions</a>
      <a href="#yogas">Yogas</a><a href="#sav">Ashtakavarga</a><a href="#houses">Houses</a>
      <a href="#longevity">Longevity</a><a href="#now">Now</a><a href="#timeline">Timeline</a>
      <a href="#vargas">Divisionals</a><a href="#glossary">Glossary</a></nav>
  </header>

  {_now_box(r)}

  {_info_box(r)}

  {_distinctive(r)}

  {_positions(r)}

  {_yogas(r)}

  {_sav(r)}

  <h2 class="section" id="houses">House by house</h2>
  <p class="section-sub">Each bhava: Raman's pillars (lord, karaka, navamsa), his verdict, then the
    population context. {_esc(ROLLUP_RULE)}</p>
  {houses}

  <h2 class="section" id="longevity">Longevity</h2>
  <p class="section-sub">Raman's order: establish the band by combination first, then fix the period
    by the marakas (HTJAH-II:4465-4472). The numeric span is a cross-check, never a date.</p>
  {combos_html}
  <p class="long"><b>3. Numeric cross-check (Ayurdaya)</b>: about
    <b>{round(r.longevity_years)} years</b> ({y}y {mo}m {d}d) &mdash;
    class <b>{_esc(r.longevity_class)}</b>. Treat as a band; the engine's own health layer defers
    lifespan.</p>

  <h2 class="section" id="timeline">Life-narrative</h2>
  <p class="section-sub">Vimshottari Mahadasha &rarr; Antardasha, {r.window_back} years back to
    {r.window_forward} ahead ({_jd_to_date(r.ref_jd - 365.2425 * r.window_back)} &ndash;
    {_jd_to_date(r.ref_jd + 365.2425 * r.window_forward)}). A planet influences a house by owning,
    occupying or aspecting the house or its lord (HTJAH-I:1586-1629). Grades (uniform for every
    house): both lords influence + AD associated with MD = <em>par excellence</em>, both but not
    associated = <em>ordinary</em>, bhukti lord only = <em>limited</em>, MD lord only =
    <em>feeble</em> (HTJAH-I:1592-1640, 2588-2599). Verdicts are the unchanged natal readings.</p>
  <div class="grade-legend">{"".join(f"<div><b>{k}</b> &mdash; {v}</div>"
      for k, v in _TIER_MEANING.items())}</div>
  {_timeline(r)}

  <h2 class="section" id="vargas">Divisional deep-reads</h2>
  <p class="section-sub">Shodasavarga &mdash; each divisional chart magnifies one matter (Raman core
    authoritative; varga overlay report-only).</p>
  {vargas}

  {extras}

  {_glossary()}

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
