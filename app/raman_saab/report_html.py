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
    _PLANET_THEME,
    _SIGN_NAME,
    _TIER_MEANING,
    _lagna_ledger,
    _outlook_strength_word,
    _outlook_window_label,
    _vedha_word,
    DetailedReport,
    adverse_transit_windows,
    ascendant_position,
    format_longitude,
    format_maraka_reasons,
    gochara_synthesis_sentence,
    graded_buckets,
    influence_basis,
    influence_basis_table,
    longevity_band_label,
    distinctive_gloss,
    driver_entry,
    nakshatra_lord,
    plain_bhukti_summary,
    planet_rows,
    rollup_driver,
    signification_tenor_split,
    tenor_note,
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

/* ── Your Reading: the plain-English section, read first ─────────────────── */
.plain-reading{margin:1.6rem 0 0;padding:1.5rem 1.7rem;border-radius:16px;
  background:color-mix(in srgb,var(--doctrine) 5%,var(--surface));
  border:1px solid color-mix(in srgb,var(--doctrine) 18%,var(--rule))}
.plain-reading p{font-family:var(--serif);font-size:1.08rem;line-height:1.6;color:var(--ink);
  margin:.75rem 0 0}
.plain-reading p:first-child{margin-top:0}
.plain-reading .pr-opening{font-size:1.18rem;color:var(--doctrine)}
.plain-reading p b{color:var(--doctrine)}
.plain-reading .pr-closing{font-family:var(--sans);font-size:.82rem;font-style:italic;
  color:var(--ink-soft);margin-top:1.1rem;padding-top:.9rem;
  border-top:1px solid color-mix(in srgb,var(--doctrine) 15%,var(--rule))}
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
/* Wave-3: yoga x dasha rows are grouped by yoga; this is the group's own band row. */
.yoga-group th{text-align:left;background:var(--tag-bg);color:var(--tag-ink);
  font-size:.72rem;letter-spacing:.04em}
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
.nichod-essence{margin:1rem 0 1.1rem;padding:1.2rem 1.4rem;border-left:4px solid var(--doctrine);
  border-radius:0 12px 12px 0;background:color-mix(in srgb,var(--doctrine) 6%,transparent);
  font-family:var(--serif);font-size:1.08rem;line-height:1.55;color:var(--ink)}
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
.infonote--warn{color:var(--warn)}
.infonote--warn .tag--warn{margin-right:.3rem}

/* ── running-now box ─────────────────────────────────────────────── */
.nowbox{margin:1.8rem 0 0;padding:1.1rem 1.2rem;border:2px solid var(--doctrine);
  border-radius:12px;background:var(--surface)}
.now-head{font-family:var(--serif);font-size:1.1rem;display:flex;flex-wrap:wrap;gap:.5rem;
  align-items:baseline}
.now-head b{color:var(--doctrine)}
.now-row{display:flex;flex-wrap:wrap;gap:.3rem;align-items:center;margin-top:.6rem}

/* ── gochara outlook (multi-year Gantt) ──────────────────────────── */
.gochara-outlook{margin-top:1.1rem}
.gochara-outlook svg{display:block;overflow:visible}
.gochara-bar{cursor:help;transition:fill-opacity .15s}
.gochara-bar:hover{fill-opacity:1 !important}

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
.badges{margin-top:.3rem;font-size:.72rem;color:var(--ink-soft)}
.badges code{background:var(--panel-2,rgba(127,127,127,.12));border-radius:4px;
  padding:.1rem .4rem;margin-right:.35rem;font-family:inherit}
.method-preamble{font-style:italic}
/* judgment-graph house cards — a vertical stack; the left rule carries the house's own
   natal verdict colour. Mobile-native: no horizontal scroll, no glyph legend to decode. */
.jg-house{margin:.5rem 0;padding:.1rem 0 .1rem .7rem}
.jg-house-head{margin:.2rem 0;font-size:.9rem}
.jg-house .doctrine{margin:.2rem 0}
.method-order{margin:.15rem 0 .6rem 1.4rem;font-size:.85rem;color:var(--ink-soft)}
/* progressive disclosure — Summary is the section head above; these are Why/Evidence/
   Calculation/Classical text, each openable independently, nothing ever removed */
details.disclosure{margin-top:.4rem;border-top:1px solid var(--rule,rgba(127,127,127,.2))}
details.disclosure>summary{cursor:pointer;font-size:.82rem;font-weight:600;padding:.3rem 0;
  color:var(--ink-soft)}
details.disclosure[open]>summary{color:var(--ink)}
blockquote.raman-quote{margin:.4rem 0;padding:.4rem .8rem;border-left:3px solid var(--doctrine);
  font-family:Georgia,serif;font-style:italic;font-size:.88rem}
blockquote.raman-quote cite{font-style:normal;color:var(--ink-soft);font-size:.78rem}
abbr.gloss{text-decoration:underline dotted;cursor:help}
.long-step{margin:.3rem 0;font-size:.9rem}

/* ── split status: the majority tenor vs the weakest-link headline ───────── */
.split-badge{opacity:.85;font-weight:500;cursor:help}
.split-note{margin:.5rem 0 0;padding:.5rem .75rem;border-radius:8px;font-size:.82rem;
  background:var(--tag-bg);color:var(--tag-ink);border-left:3px solid var(--instrument)}
.split-note--warn{background:color-mix(in srgb,var(--warn) 14%,transparent);color:var(--warn);
  border-left-color:var(--warn);font-weight:500}
.split-note--warn b{color:var(--warn)}

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

/* ── sticky progress bar ─────────────────────────────────────────── */
.stickybar{position:sticky;top:0;z-index:20;display:flex;justify-content:space-between;
  gap:1rem;align-items:center;padding:.5rem clamp(1rem,4vw,2rem);
  background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--rule);font-size:.76rem}
.sb-sec{font-weight:600;color:var(--doctrine);overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
.sb-now{color:var(--instrument);font-weight:600;white-space:nowrap}

/* ── chart diagrams ──────────────────────────────────────────────── */
.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1.2rem}
.chartfig{margin:0}
.chartfig figcaption{font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-soft);font-weight:600;margin-bottom:.4rem}
.chartgrid{position:relative;display:grid;gap:2px;aspect-ratio:1;
  grid-template-columns:repeat(4,1fr);grid-template-rows:repeat(4,1fr);
  grid-template-areas:"s12 s1 s2 s3" "s11 mid mid s4" "s10 mid mid s5" "s9 s8 s7 s6";
  background:var(--rule);border:2px solid var(--rule)}
.cbox{background:var(--surface);padding:.25rem .3rem;display:flex;flex-direction:column;gap:.15rem;
  min-height:0;overflow:hidden}
.cbox.asc{background:color-mix(in srgb,var(--doctrine) 10%,var(--surface));
  box-shadow:inset 0 0 0 2px var(--doctrine)}
.csign{font-size:.58rem;letter-spacing:.05em;text-transform:uppercase;color:var(--ink-soft)}
.cgrahas{display:flex;flex-wrap:wrap;gap:.15rem}
.cgrahas i{font-style:normal;font-size:.72rem;font-weight:600;color:var(--doctrine);
  font-family:var(--mono)}
.cmid{grid-area:mid;background:var(--surface);display:flex;flex-direction:column;
  align-items:center;justify-content:center;font-family:var(--serif);font-size:.9rem;
  color:var(--doctrine)}
.cmid span{font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-soft)}

/* ── varga cards ─────────────────────────────────────────────────── */
.vbody{padding:.9rem 1rem 1rem;display:flex;flex-direction:column;gap:.8rem}
.vsec{border-radius:10px;padding:.7rem .85rem}
.vcore{background:color-mix(in srgb,var(--doctrine) 7%,transparent);
  border-left:3px solid var(--doctrine)}
.voverlay{background:var(--instrument-soft);border-left:3px solid var(--instrument)}
.vsec-label{font-size:.63rem;letter-spacing:.1em;text-transform:uppercase;font-weight:700;
  color:var(--ink-soft);margin-bottom:.45rem}
.vcore .vsec-label{color:var(--doctrine)}
.voverlay .vsec-label{color:var(--instrument)}
.vrow{display:grid;grid-template-columns:minmax(120px,1fr) 2fr;gap:.6rem;padding:.16rem 0;
  font-size:.83rem;border-bottom:1px solid color-mix(in srgb,var(--rule) 60%,transparent)}
.vrow:last-child{border-bottom:0}
.vk{color:var(--ink-soft)}
.vv{font-weight:500}
.vtext{font-size:.83rem;color:var(--ink-soft);padding:.16rem 0}
.vbanner{margin:.5rem 0 .1rem;padding:.35rem .6rem;border-radius:7px;font-weight:700;
  font-size:.8rem;letter-spacing:.03em;background:var(--doctrine);color:var(--surface);
  display:inline-block}
details.vnotes{font-size:.78rem}
details.vnotes summary{cursor:pointer;color:var(--ink-soft);font-size:.7rem;
  letter-spacing:.08em;text-transform:uppercase}
details.vnotes ul{margin:.4rem 0 0;padding-left:1.1rem;color:var(--ink-soft)}
details.vnotes li{margin:.25rem 0}

/* ── house filters ───────────────────────────────────────────────── */
.filters{display:flex;flex-wrap:wrap;gap:.4rem;margin:0 0 1rem}
.filters button{font:inherit;font-size:.76rem;font-weight:600;cursor:pointer;
  padding:.3rem .7rem;border-radius:999px;border:1px solid var(--rule);
  background:var(--surface);color:var(--ink-soft)}
.filters button:hover{border-color:var(--instrument);color:var(--instrument)}
.filters button.on{background:var(--doctrine);border-color:var(--doctrine);color:var(--surface)}
.house[hidden]{display:none}

/* ── integrated insights ─────────────────────────────────────────── */
.insight{margin:.8rem 0;padding:.8rem 1rem;border:1px solid var(--rule);border-radius:10px;
  background:var(--surface)}
.insight-head b{font-family:var(--serif);font-size:1rem;color:var(--doctrine)}
.insight-head code{font-family:var(--mono);font-size:.72rem;color:var(--ink-soft);
  margin-left:.4rem}
.insight .doctrine{font-size:.92rem;margin:.35rem 0 0}
.insight .plain{margin-top:.4rem}
.source-quote{margin-top:.4rem;font-size:.82rem;font-style:italic;color:var(--ink-soft)}
.source-quote b{font-style:normal}
.insight-links{margin-top:.4rem;font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;
  color:var(--instrument)}

/* ── provenance banner (non-Raman sections) ──────────────────────── */
.provenance-banner{margin:2.2rem 0 .6rem;padding:.7rem .95rem;border:1px solid var(--warn);
  border-radius:10px;font-size:.8rem;color:var(--warn);
  background:color-mix(in srgb,var(--warn) 7%,transparent)}

/* ── glossary-linked header chips ────────────────────────────────── */
a.sig-chip{text-decoration:none;color:inherit}
a.sig-chip.has-gloss{border-bottom-style:dotted;cursor:help}
a.sig-chip.has-gloss:hover{border-color:var(--instrument);color:var(--instrument)}

/* ── caveat tags: bordered + iconised so disclaimers cannot be skimmed past ── */
.tag--warn{border:1px solid var(--warn)}
.tag--warn::before{content:"\\26A0  ";font-weight:700}
.tag--univ{border:1px dashed var(--tag-ink)}
.tag--univ::before{content:"\\2261  "}
.tag--rare::before{content:"\\2726  "}

@media (max-width:480px){
  .cal-row{grid-template-columns:1fr;gap:.15rem}
  .infostats b{font-size:1.25rem}
  .vrow{grid-template-columns:1fr;gap:0}
  .stickybar{font-size:.7rem}
}

@media print{
  body{background:#fff;color:#000}
  .toc,.now-badge{display:none}
  details.varga,details.glossary{border:1px solid #ccc}
  details.varga>summary,details.glossary>summary{list-style:none}
  details[open]>*{display:revert}
  .house,.period,.yogalist li,.vsec,.chartfig,.md-group,.infobox,.nowbox,
  table.grid tr{break-inside:avoid}
  h2.section{break-after:avoid}
  .infobox,.instrument,.nowbox{background:transparent;border:1px solid #999}
  a{color:#000;text-decoration:none}
  .stickybar,.filters{display:none}
  details.varga,details.glossary,details.vnotes,details.md-group{display:block}
  details>summary{list-style:none}
  details:not([open])>*:not(summary){display:revert !important}
  .house[hidden]{display:block !important}
}
"""


def _esc(s: str) -> str:
    return html.escape(str(s))


def _bold(s: str) -> str:
    """Escape, then promote **markdown bold** to <strong> (the synthesis prose uses it)."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _esc(s))


def _vclass(verdict: str) -> str:
    return verdict if verdict in ("afflicted", "favourable") else "mixed"


def _method_preamble_html(section_id: str) -> str:
    """HTML sibling of detailed_report._method_preamble — the "why astrologers examine
    this" educational preamble, on the standalone surface too (REPORT COMPLETENESS)."""
    from app.raman_saab.plain_terms import SECTION_METHOD
    entry = SECTION_METHOD.get(section_id)
    if entry is None:
        return ""
    why, order = entry
    steps = "".join(f"<li>{_esc(step)}</li>" for step in order)
    return (f'<p class="section-sub method-preamble"><b>Why astrologers examine this.</b> '
            f'{_esc(why)}:</p><ol class="method-order">{steps}</ol>')


def _apply_glossary_abbrs(html_str: str) -> str:
    """Clickable glossary everywhere (review upgrade #8, standalone HTML): the FIRST plain-text
    occurrence of each known term is wrapped in `<abbr title="plain — analogy">` — a hover
    reveals the plain-terms gloss without leaving the page. Operates only on TEXT segments
    (tag markup, and <script>/<style> bodies, are walked past untouched) so it can never
    corrupt an attribute, an id, or embedded JS/CSS."""
    from app.raman_saab.plain_terms import TERM_GLOSS
    terms = sorted(TERM_GLOSS.keys(), key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b")
    parts = re.split(r"(<[^>]*>)", html_str)
    seen: set[str] = set()
    skip_tag: str | None = None
    for i, part in enumerate(parts):
        if part.startswith("<"):
            m = re.match(r"</?\s*([a-zA-Z0-9]+)", part)
            name = m.group(1).lower() if m else ""
            if part.startswith("</") and name in ("script", "style"):
                skip_tag = None
            elif name in ("script", "style"):
                skip_tag = name
            continue
        if skip_tag:
            continue

        def _sub(m: re.Match) -> str:
            term = m.group(1)
            if term in seen:
                return term
            seen.add(term)
            g = TERM_GLOSS[term]
            title = html.escape(f"{g.plain} — {g.analogy}")
            return f'<abbr class="gloss" title="{title}">{term}</abbr>'

        parts[i] = pattern.sub(_sub, part)
    return "".join(parts)


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


def _raman_quote_html(mr, pf) -> str:
    """HTML sibling of detailed_report's item-14 "Raman writes" block — the driver
    signification's own cited source, verbatim, for the house's Classical-text level."""
    if pf is None or not pf.significations:
        return ""
    from app.raman_saab.detailed_report import passage_quote
    from app.raman_saab.doctrine.significations import SIGNIFICATIONS
    dr = next((sv for sv in pf.significations if sv.verdict == pf.rollup), pf.significations[0])
    sig = next((s for s in SIGNIFICATIONS.get(mr.house, ()) if s.key == dr.signification), None)
    if sig is None or sig.source is None:
        return ""
    q = passage_quote(f"{sig.source.work}:{sig.source.line}")
    if not q:
        return ""
    return (f'<blockquote class="raman-quote">&ldquo;{_esc(q)}&rdquo; '
            f'<cite>({sig.source.work}:{sig.source.line})</cite> &mdash; and this chart '
            f'computes: <b>{_esc(mr.verdict)}</b> for <i>{_esc(dr.signification)}</i>.'
            f'</blockquote>')


def _house_strip(rows: tuple) -> str:
    """Wave-3 (2026-08-18): the verdict-first 12-row strip that opens the house chapter —
    the markdown strip's HTML twin, built from the SAME `detailed_report.house_strip_rows`
    composer so the two surfaces cannot drift. A scanning index only: the twelve deep
    blocks follow it unchanged and in full."""
    if not rows:
        return ""
    body = ""
    for row in rows:
        inv = (' <span class="tag tag--warn">INVERTED</span>' if row.inverted else "")
        split = (f'<span class="chip chip--{_vclass(row.verdict)} split-badge" '
                 f'title="{_esc(row.split_note)}">{_esc(row.split)}</span>'
                 if row.split else 'consistent')
        body += (f'<tr><td><a href="#house-{row.house}">H{row.house}</a></td>'
                 f'<td>{_esc(row.name)}</td>'
                 f'<td><span class="chip chip--{_vclass(row.verdict)}">'
                 f'{_esc(row.verdict)}</span>{inv}</td>'
                 f'<td>{_esc(row.driver) if row.driver else "&mdash;"}</td>'
                 f'<td>{split}</td>'
                 f'<td>{_esc(row.tier) if row.tier else "not lit"}</td></tr>')
    return ('<p class="section-sub"><b>The twelve houses at a glance</b> &mdash; a '
            'scanning index; each row&rsquo;s full judgment, evidence and population '
            'context follows below, unabridged.</p>'
            '<div class="tablewrap"><table class="grid"><thead><tr><th>#</th>'
            '<th>house</th><th>verdict</th><th>driver</th><th>split status</th>'
            '<th>running period</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div>'
            '<p class="section-sub"><i>&ldquo;Running period&rdquo; is this house&rsquo;s '
            'four-tier fructification grade in the bhukti running at the reference date '
            '(par excellence / ordinary / limited / feeble, HTJAH-I:1592-1596); &ldquo;not '
            'lit&rdquo; means neither period-lord influences the house. &ldquo;Split '
            'status&rdquo; repeats the block&rsquo;s own split note; &ldquo;consistent&rdquo; '
            'means the majority tenor agrees with the headline.</i></p>')


def _house_section(mr, cal, pf, chart, distinctive_houses: frozenset[int] = frozenset(),
                   conclusion: str = "", ht=None, frame_line: str = "",
                   tier_line: str = "", chief: tuple = (), cross_refs: tuple = (),
                   maintainer_notes: str = "", cal_rollup: str = "") -> str:
    """One bhava: Raman's pillars + verdict (with the rollup driver named), then the overlay.
    `conclusion` is the pre-composed `detailed_report.house_conclusion` line (Raman's own
    closing device) — passed in, not computed here, so both renderers share one composer.
    Wave-2 (2026-08-18, add-only): `frame_line` / `tier_line` (the pre-composed
    `house_frame_line` / `house_current_tier_line` disclosures) and `chief` (the
    `house_chief_combinations` rows — signification, rule id, Raman's effect prose,
    citation) are likewise passed in from the shared composers.
    Wave-3 (2026-08-18, add-only): `cross_refs` (the conditional in-block pointers —
    PREC-1 dashboard disagreement, the Longevity deferral), `maintainer_notes` (the
    encoding-scope fine print routed out of the chief-combination prose) and `cal_rollup`
    (the repeat-band summary above the retained population rows) — all pre-composed in
    `detailed_report`, all conditional on state the judgment path computed. The
    Conclusion is now rendered at the HEAD of the block; the machine-composed evidence
    chain it used to sit under is unchanged and labelled "Working"."""
    is_active = "ACTIVE in the running" in mr.reading
    active = '<span class="active-badge">active now</span>' if is_active else ""
    flags = [_vclass(mr.verdict)]
    if is_active:
        flags.append("active")
    if mr.house in distinctive_houses:
        flags.append("distinctive")
    rows = "".join(_cal_row(e) for e in cal.entries)
    drv_entry = driver_entry(cal, mr.verdict)
    driver = drv_entry.signification if drv_entry else None
    drv = (f'<span class="driver">driven by <b>{_esc(driver)}</b></span>' if driver else "")

    split = signification_tenor_split(cal)
    note = tenor_note(split, mr.verdict)
    split_badge = split_note_html = inverted_note_html = ""
    if note:
        # one composer for both surfaces (the markdown strip calls the same function)
        from app.raman_saab.detailed_report import house_strip_badge
        badge_label = house_strip_badge(split, note)
        split_badge = (f'<span class="chip chip--{_vclass(split.majority)} split-badge" '
                       f'title="{_esc(note)}">{_esc(badge_label)}</span>')
        from app.raman_saab.detailed_report import SPLIT_POINTER
        split_note_html = (f'<div class="split-note">Split status: {_esc(note)}</div>'
                           f'<div class="split-note"><i>{_esc(SPLIT_POINTER)}</i></div>')
    if drv_entry is not None and drv_entry.inverted_warning:
        from app.raman_saab.detailed_report import INVERTED_POINTER
        inverted_note_html = (
            '<div class="split-note split-note--warn">&#9888; The driver, '
            f'<b>{_esc(driver)}</b>, is an atlas-proven <b>INVERTED channel</b> — real cases '
            'ran opposite to this reading; treat this house’s headline with maximal '
            'skepticism.</div>'
            f'<div class="split-note split-note--warn"><i>{_esc(INVERTED_POINTER)}</i></div>')
    xref_html = "".join(f'<div class="split-note"><i>{_esc(x)}</i></div>'
                        for x in cross_refs)
    conclusion_html = (f'<div class="split-note"><b>Conclusion</b> &mdash; '
                       f'{_esc(conclusion)}</div>' if conclusion else "")

    pillars = ""
    if pf is not None and pf.significations:
        led = pf.significations[0].ledger
        lagna_led = _lagna_ledger(pf.significations[0])
        lp = chart.planets.get(pf.lord)
        bits = [f'<b>Lord</b> {_esc(pf.lord)}'
                + (f' in H{lp.rasi_house}' if lp is not None else "")
                + ("" if lagna_led.lord_strong is None else
                   f' ({"strong" if lagna_led.lord_strong else "weak"})'),
                f'<b>Karaka</b> {_esc(led.karaka)}'
                + ("" if led.karaka_strong is None else
                   f' ({"strong" if led.karaka_strong else "weak"})')
                + ("" if led.karaka_intact else " [afflicted]"),
                f'<b>Navamsa</b> {_esc(lagna_led.navamsa_status)}']
        if led.bhava_bala is not None:
            bits.append(f'<b>Bhava Bala</b> {led.bhava_bala:.0f}')
        pillars = f'<div class="pillars">{" &middot; ".join(bits)}</div>'

    badges = ""
    if pf is not None and ht is not None:
        fired_ct = 0
        cites: set[str] = set()
        for sv in pf.significations:
            for led2 in (sv.ledger, *sv.alt_ledgers):
                for fr in (*led2.fired_benefic, *led2.fired_malefic, *led2.fired_neutral):
                    fired_ct += 1
                    cites.add(f"{fr.rule.source.work}:{fr.rule.source.line}")
        band = ("High" if "corrobor" in ht.status else "Low" if "contest" in ht.status
                else "Medium")
        badges = (f'<div class="badges"><code>Evidence {len(ht.testimonies)}</code> '
                  f'<code>Rules {fired_ct}</code> <code>Sources {len(cites)}</code> '
                  f'<code>Support {_esc(band)} ({ht.favourable}F/{ht.adverse}A)</code></div>')

    # progressive disclosure (review upgrade #3): Summary is always visible (the head above);
    # Why stays open by default (no regression from the prior always-visible reading); Evidence /
    # Calculation / Classical text are closed by default with a substantive <summary> label —
    # every level's content remains fully present in the document, never dropped.
    quote_html = _raman_quote_html(mr, pf)
    testimony_n = len(ht.testimonies) if ht is not None else len(cal.entries)
    support_word = (("High" if "corrobor" in ht.status else "Low" if "contest" in ht.status
                     else "Medium") if ht is not None else "")
    # Wave-2 D2/D4 (2026-08-18): the deciding-frame and current-period-tier disclosure
    # lines, rendered inside the always-open Why pane where the reading they reconcile
    # sits; D1: the chief fired combinations as their own open disclosure level.
    frame_html = (f'<div class="split-note"><b>Frame</b> &mdash; {_esc(frame_line)}</div>'
                  if frame_line else "")
    tier_html = (f'<div class="split-note"><b>Current period</b> &mdash; '
                 f'{_esc(tier_line)}</div>' if tier_line else "")
    level_why = (
        '<details class="disclosure" open><summary>Why</summary>'
        f'<p class="doctrine"><b>Working</b> &mdash; {_bold(mr.reading)}</p>'
        f'{frame_html}{tier_html}</details>')
    level_chief = ""
    if chief:
        chief_items = "".join(
            f'<li><i>{_esc(csig)}</i>: <code>{_esc(cid)}</code> &mdash; '
            f'&ldquo;{_esc(ctext)}&rdquo; ({_esc(ccite)})</li>'
            for csig, cid, ctext, ccite in chief)
        notes_html = (f'<p class="section-sub"><i>Encoding-scope notes (maintainer fine '
                      f'print, not readings): {_esc(maintainer_notes)}</i></p>'
                      if maintainer_notes else "")
        level_chief = (
            f'<details class="disclosure" open><summary>Chief combinations &mdash; '
            f'the fired rules that decided, in Raman&rsquo;s own words</summary>'
            f'<ul>{chief_items}</ul>{notes_html}</details>')
    rollup_html = (f'<div class="split-note"><i>{_esc(cal_rollup)}</i></div>'
                   if cal_rollup else "")
    level_evidence = (
        f'<details class="disclosure"><summary>Evidence &mdash; {testimony_n} testimonies'
        f'{f", {support_word} support" if support_word else ""}</summary>'
        f'{badges}<div class="instrument"><div class="instrument-label">Population context '
        f'&mdash; empirical, not Raman</div>{rollup_html}{rows}</div></details>')
    level_calc = (f'<details class="disclosure"><summary>Calculation</summary>{pillars}</details>'
                  if pillars else "")
    level_classical = (f'<details class="disclosure"><summary>Classical text (Raman '
                       f'verbatim)</summary>{quote_html}</details>' if quote_html else "")

    return (
        f'<section class="house" data-flags="{" ".join(flags)}" '
        f'id="house-{mr.house}"><div class="house-head">'
        f'<h3><span class="house-num">H{mr.house}</span> &middot; {_esc(_HOUSE_NAME[mr.house])}</h3>'
        f'<span class="chip chip--{_vclass(mr.verdict)}">{_esc(mr.verdict)}</span>'
        f'{split_badge}{drv}{active}</div>'
        f'{split_note_html}{inverted_note_html}{xref_html}{conclusion_html}'
        f'{level_why}{level_chief}{level_evidence}{level_calc}{level_classical}</section>')


def _house_chip(a, *, ring: bool = False, basis: str = "") -> str:
    """A house chip carrying its natal verdict (title = full verdict); ring = par-excellence.
    Wave-2 (2026-08-18): `basis` (optional) appends the influence-basis derivation — BY WHICH
    of Raman's factors the period lords influence this house (HTJAH-I:1586-1596) — into the
    native tooltip; callers that pass nothing render exactly as before."""
    tail = f" &mdash; {_esc(basis)}" if basis else ""
    return (f'<span class="chip chip--{_vclass(a.natal_verdict)}{" focus" if ring else ""}" '
            f'title="{_esc(_HOUSE_NAME[a.house])}: {_esc(a.natal_verdict)} '
            f'({_esc(a.natal_degree)}){tail}">H{a.house}</span>')


def _info_box(r: DetailedReport) -> str:
    """The honesty headline: how much of this document actually distinguishes this chart."""
    from app.raman_saab.detailed_report import POPULATION_NOTE as _POPULATION_NOTE
    i = r.info
    inv_line = ""
    if i.inverted_locations:
        chips = "".join(f'<span class="tag tag--warn">{_esc(loc)}</span>'
                        for loc in i.inverted_locations)
        inv_line = (f'<p class="infonote infonote--warn"><b>Inverted channels in this chart:</b> '
                   f'{chips} &mdash; any house headline driven by one of these ran opposite to '
                   f'real cases in the validation program; treat with maximal skepticism.</p>')
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
        f'<p class="infonote">{_esc(_POPULATION_NOTE)}</p>'
        f'{inv_line}</div>')


_AXIS_LABEL_HTML = {"verdict": "verdict", "magnitude": "strength", "state": "state",
                    "dasha": "timing", "varga": "divisional", "transit": "transit",
                    "yoga": "yoga", "citation": "cross-feature"}


def _themes_section(r: DetailedReport) -> str:
    """The v34 integrated-interpretation section (theme synthesis) — a re-read ACROSS the
    sections, above the technical ones. Judges nothing anew; every claim traces to an
    authoritative verdict via its accessor."""
    ts = getattr(r, "themes", None)
    head = '<h2 class="section" id="integrated-reading">The integrated reading</h2>'
    if ts is None or not getattr(ts, "themes", None):
        return (head + '<p class="muted">Not available for this chart in the current engine '
                '(too few decided sections to synthesize).</p>')
    out = [head,
           '<p class="section-sub">One reading across every section above &mdash; not a new '
           'judgment. Each theme gathers the findings the report already made (house verdict, '
           'strength, planetary state, divisional confirmation, yoga, timing) into one '
           'mechanism, states how strongly they converge, and names any tension with the '
           'precedence rule that resolves it. The direction of every theme is the engine&rsquo;s '
           'own house verdict, unchanged.</p>']
    p = ts.portrait
    out.append('<h3>Executive portrait</h3><ul class="portrait">')
    if p.frame:
        out.append(f'<li><b>Reading frame</b> &mdash; judged chiefly from the {_esc(p.frame)} '
                   'frame (the stronger of the two lagnas here).</li>')
    if p.dominant_actors:
        acts = "; ".join(f"<b>{_esc(n)}</b> ({_esc(w)})" for n, w in p.dominant_actors)
        out.append(f'<li><b>Dominant actors</b> &mdash; {acts}.</li>')
    if p.strongest_domains:
        out.append(f'<li><b>Strongest domains</b> &mdash; {_esc(", ".join(p.strongest_domains))}.</li>')
    if p.weakest_domains:
        out.append(f'<li><b>Areas under strain</b> &mdash; {_esc(", ".join(p.weakest_domains))}.</li>')
    if p.protective_factors:
        out.append(f'<li><b>Protective factors</b> &mdash; {_esc("; ".join(p.protective_factors))}.</li>')
    if p.principal_tension:
        out.append(f'<li><b>Principal tension</b> &mdash; {_esc(p.principal_tension)}</li>')
    if p.current_chapter:
        nxt = f"; {_esc(p.next_chapter)}" if p.next_chapter else ""
        out.append(f'<li><b>Current chapter</b> &mdash; {_esc(p.current_chapter)}{nxt}.</li>')
    if p.honesty_note:
        out.append(f'<li class="muted"><i>{_esc(p.honesty_note)}</i></li>')
    out.append("</ul>")

    by_id = {t.theme_id: t for t in ts.themes}
    spine = [by_id[i] for i in ts.spine if i in by_id]
    if spine:
        out.append('<h3>The interpretive spine</h3><ul>')
        for t in spine:
            out.append(f'<li><b>{_esc(t.name)}</b> &mdash; {_esc(t.headline_verdict)} '
                       f'({t.convergence.replace("_", " ").lower()} convergence)</li>')
        out.append("</ul>")

    out.append("<h3>Major life-themes</h3>")
    for t in ts.themes:
        houses = ", ".join(f"H{h}" for h in t.houses)
        dom = ", ".join(t.dominant_planets) if t.dominant_planets else "the chart"
        out.append(f'<div class="theme"><h4>{_esc(t.name)} &mdash; <b>{_esc(t.headline_verdict)}</b> '
                   f'({t.convergence.replace("_", " ").lower()} convergence)</h4>')
        out.append(f'<p><i>{_esc(t.final_interpretation)}</i></p><ul>')
        out.append(f'<li><b>Network</b> &mdash; {houses}'
                   + (f'; karakas {_esc(", ".join(t.karakas))}' if t.karakas else '')
                   + f'; driven by {_esc(dom)}.</li>')
        out.append(f'<li><b>Convergence</b> &mdash; {_esc(t.convergence_why)}</li>')
        out.append(f'<li><b>Divisional (D9)</b> &mdash; {_esc(t.varga_relation)}.</li>')
        if t.activation_span:
            out.append(f'<li><b>Timing</b> &mdash; {_esc(t.activation_span)}</li>')
        out.append("</ul>")
        out.append('<table class="evidence"><thead><tr><th>axis</th><th>finding</th>'
                   '<th>source</th></tr></thead><tbody>')
        for lk in t.links:
            src = lk.accessor.split("@")[-1].strip()
            out.append(f'<tr><td>{_esc(_AXIS_LABEL_HTML.get(lk.axis, lk.axis))}</td>'
                       f'<td>{_esc(lk.label)}: {_esc(lk.value)}</td>'
                       f'<td><code>{_esc(src)}</code></td></tr>')
        out.append("</tbody></table>")
        for c in t.contradictions:
            out.append(f'<p class="tension"><b>Tension ({_esc(c.kind)})</b> &mdash; '
                       f'{_esc(c.poles[0])} vs {_esc(c.poles[1])}. Resolved by '
                       f'<b>{_esc(c.governing)}</b>: {_esc(c.resolution)}</p>')
        out.append("</div>")

    if getattr(ts, "connections", None):
        out.append('<h3>How the themes connect</h3><p class="section-sub">Where one computed '
                   'factor drives more than one life-area, so the chart reads as a single '
                   'fabric.</p><ul>')
        for c in ts.connections:
            out.append(f'<li>{_esc(c.note)}</li>')
        out.append("</ul>")

    if getattr(ts, "dasha_evolution", None):
        out.append('<h3>Dasha evolution &mdash; the horoscope through time</h3>'
                   '<p class="section-sub">Each Mahadasha chapter and the themes it brings to '
                   'the top tier, split into what newly emerges and what continues.</p>'
                   '<table class="evidence"><thead><tr><th>chapter</th><th>span</th>'
                   '<th>lean</th><th>newly emphasized</th><th>continuing</th></tr></thead><tbody>')
        for ch in ts.dasha_evolution:
            now = " (now)" if ch.is_current else ""
            out.append(f'<tr><td>{_esc(ch.maha)} MD{now}</td><td>{_esc(ch.span)}</td>'
                       f'<td>{_esc(ch.lean)}</td><td>{_esc(", ".join(ch.emerging) or "-")}</td>'
                       f'<td>{_esc(", ".join(ch.continuing) or "-")}</td></tr>')
        out.append("</tbody></table>")

    out.append('<h3>Varga confirmation matrix</h3><p class="section-sub">Does the relevant '
               'division confirm, qualify or stay neutral on each theme&rsquo;s natal '
               'indication? (D9 is the only division that modulates a D1 verdict here.)</p>'
               '<table class="evidence"><thead><tr><th>theme</th><th>natal verdict</th>'
               '<th>D9 relation</th></tr></thead><tbody>')
    for t in ts.themes:
        out.append(f'<tr><td>{_esc(t.name)}</td><td>{_esc(t.headline_verdict)}</td>'
                   f'<td>{_esc(t.varga_relation)}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


def _interpretation_guide_section(r: DetailedReport) -> str:  # noqa: ARG001 — chart-independent
    """v18 — how to read this report: the collected precedence rules, reading order,
    parallel lenses and axes. Pure doctrine metadata (interpretation_guide module)."""
    from app.raman_saab.interpretation_guide import INTERPRETATION_GUIDE as ig
    steps = "".join(
        f'<li><b>{_esc(s["title"])}</b> &mdash; {_esc(s["answers"])} {_esc(s["adds"])}</li>'
        for s in ig["reading_order"])
    prec_rows = "".join(
        f'<tr><td>{_esc(p["id"])}</td><td>{_esc(", ".join(p["sections"]))}</td>'
        f'<td>{_esc(p["relation"])}</td><td>{_esc(p["rule_text"])}</td></tr>'
        for p in ig["precedence"])
    par_items = "".join(
        f'<li><b>{_esc(p["id"])}</b> ({_esc(", ".join(p["sections"]))}): {_esc(p["why"])}</li>'
        for p in ig["parallel_lenses"])
    axis_rows = "".join(
        f'<tr><td>{_esc(a["axis"])}</td>'
        f'<td>{_esc(a["means"] + (" — " + a["qualification"] if a.get("qualification") else ""))}</td>'
        f'<td>{_esc(", ".join(a["sections"]))}</td><td>{_esc(a["citation"])}</td></tr>'
        for a in ig["axes"])
    return (
        '<h2 class="section" id="interpretation-guide">How to read this report</h2>'
        f'<p class="section-sub"><i>{_esc(ig["preamble"])}</i></p>'
        '<p class="section-sub"><b>Start here &mdash; five sections answer most '
        f'questions:</b></p><ol>{steps}</ol>'
        '<p class="section-sub"><b>When two sections seem to disagree, these rules '
        'govern</b> (each is a rule this report already states in the section that '
        'yields):</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>#</th><th>sections</th>'
        f'<th>relation</th><th>the rule</th></tr></thead><tbody>{prec_rows}</tbody>'
        '</table></div>'
        '<p class="section-sub"><b>Parallel lenses</b> &mdash; no ranking exists; read '
        f'side by side, never averaged:</p><ul>{par_items}</ul>'
        '<p class="section-sub"><b>The independent axes</b> (disagreement between axes is '
        'not a contradiction):</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>axis</th>'
        '<th>measures</th><th>shown in</th><th>citation</th></tr></thead>'
        f'<tbody>{axis_rows}</tbody></table></div>')


def _distinctive(r: DetailedReport) -> str:
    if not r.distinctive:
        return ""
    # Wave-2 parity repair (2026-08-18): the markdown, the JSON (`gloss`) and the
    # interactive page all carry the degree word, the rarity band and the plain-language
    # midpoint-side sentence; this renderer had kept the pre-Wave-1 five columns. Same
    # composers (`distinctive_gloss`), no new judgment — REPORT COMPLETENESS: a field the
    # report computes appears on EVERY surface.
    rows = "".join(
        f'<tr><td>H{h} {_esc(_MD_HOUSE_NAME[h])}</td><td>{_esc(e.signification)}</td>'
        f'<td><span class="chip chip--{_vclass(e.verdict)}">{_esc(e.verdict)}</span>'
        f' {_esc(str(e.degree))}</td>'
        f'<td class="num">{e.favourability_percentile:.0%}</td>'
        f'<td class="num">{e.band_share:.0%} ({_esc(str(e.rarity))})</td>'
        f'<td>{_esc(distinctive_gloss(e))}</td></tr>' for h, e in r.distinctive)
    return (
        '<h2 class="section" id="stands-out">What stands out</h2>'
        '<p class="section-sub">The readings furthest from the population midpoint &mdash; where '
        'this chart is least like everyone else&rsquo;s. Rare readings first, then notable, '
        'then common; within each band, furthest from the midpoint first.</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>house</th><th>matter</th>'
        '<th>verdict</th><th class="num">percentile</th><th class="num">share</th>'
        '<th>in plain terms</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>')


def _yoga_deep_section(r: DetailedReport) -> str:
    """v21 — every fired yoga as a full study; strength is measured rupas, never a %."""
    if not r.yoga_deep:
        return ""
    blocks = []
    for y in r.yoga_deep:
        # Wave-2 B (2026-08-18): placement class + functional nature per participant,
        # and the per-yoga SYN_R1 stronger-participant line (3HC:1359) — same content
        # as the markdown surface.
        parts = "; ".join(
            f"{_esc(f.planet)}: house {f.house}"
            + (f" ({_esc(f.placement)})" if getattr(f, "placement", "") else "")
            + f", {_esc(_SIGN_NAME[f.sign])}, "
            f"{_esc(f.dignity)}"
            + (f" (effective: {_esc(f.effective_dignity)})"
               if f.effective_dignity != f.dignity else "")
            + (f", {f.rupas} rupas" if f.rupas is not None else "")
            + (f", functional {_esc(f.functional)} for this Lagna"
               if getattr(f, "functional", "") else "")
            for f in y.participants)
        rows = [
            ("Definition (verbatim)", f"&ldquo;{_esc(y.definition_quote)}&rdquo; "
                                      f"({_esc(y.cite)})"),
            ("Computation", f"<code>{_esc(y.computation)}</code>"),
            ("Why it qualifies", parts or "&ndash;"),
            ("Strength (measured)", _esc(y.strength_note)),
        ]
        if getattr(y, "syn_r1_line", ""):
            rows.append(("Stronger-participant delivery", _esc(y.syn_r1_line)))
        rows.append(("Cancellation", _esc(y.cancellation_note)))
        if y.modifiers:
            rows.append(("Modifying planets", _esc(", ".join(y.modifiers))))
        if y.periods:
            rows.append(("Operating periods", _esc("; ".join(y.periods))))
        if y.nh_examples:
            rows.append(("In Notable Horoscopes", _esc(", ".join(y.nh_examples))))
        rows.append(("Effect (Raman)", _esc(y.effect)))
        body = "".join(f'<div class="vrow"><span class="vk">{k}</span>'
                       f'<span class="vv">{v}</span></div>' for k, v in rows)
        blocks.append(f'<h3>{y.comparison_rank}. {_esc(y.name)} ({_esc(y.kind)})</h3>'
                      f'<div class="vsec">{body}</div>')
    return (
        '<h2 class="section" id="yoga-deep">Yoga deep-read</h2>'
        '<p class="section-sub"><b>In simple terms:</b> every yoga this chart fires, '
        'studied in full &mdash; the quoted definition, the exact computed rule, the '
        'participants and their state, measured strength (rupas &mdash; Raman assigns no '
        'percentage and none is invented), stated cancellations, operating periods, and '
        'Notable Horoscopes appearances.</p>' + "".join(blocks))


def _planet_bios_section(r: DetailedReport) -> str:
    """v20 — dominant-graha biographies from the judgment-graph census (pure re-read)."""
    if not r.planet_bios:
        return ""
    from app.raman_saab.planet_biographies import MODERN_BANNER
    blocks = []
    for b in r.planet_bios:
        census = ", ".join(f"{k} {v}" for k, v in b.census_by_relation)
        modern = ("" if not b.themes_modern else
                  f'<p class="section-sub"><b>Modern keywords</b> '
                  f'<span class="tag tag--warn">{_esc(MODERN_BANNER)}</span> '
                  f'{_esc(", ".join(b.themes_modern))}</p>')

        def _quote(label: str, pair) -> str:
            if not pair:
                return ""
            return (f'<p class="section-sub"><b>{label}</b> &mdash; '
                    f'&ldquo;{_esc(pair[0])}&rdquo; <i>({_esc(pair[1])})</i></p>')

        node_sign_note = ("" if b.sign_text or b.planet not in ("Rahu", "Ketu") else
                          '<p class="section-sub"><b>In its sign</b> &mdash; the nodes '
                          'are aprakasha grahas; HPA-22 states no per-sign results '
                          '(HPA-22:522) &mdash; an honest absence.</p>')
        vocation = ("" if not b.themes_raman else
                    f'<p class="section-sub"><b>Raman&rsquo;s vocation words</b> '
                    f'(HTJAH-II:10249-10274) &mdash; {_esc(b.themes_raman)}</p>')
        disease = ("" if not b.disease_text else
                   f'<p class="section-sub"><b>Disease indications</b> &mdash; '
                   f'{_esc(b.disease_text[0])} <i>({_esc(b.disease_text[1])})</i></p>')
        # portrait additions (2026-08-18 report-critique): role-first header, condition
        # header line, itemized drishti, avastha consequence, named karakatvas; the
        # census is demoted to a trailing receipts line (same data, kept in full).
        hdr_bits: list[str] = []
        if b.rupas is not None:
            hdr_bits.append(f"{b.rupas:.2f} rupas &mdash; "
                            + ("meets" if b.powerful else "below")
                            + " Raman&rsquo;s minimum (GBB-8:303)")
        elif b.planet in ("Rahu", "Ketu"):
            hdr_bits.append("no Shadbala (chayagraha &mdash; the measure is defined "
                            "for the seven visible planets)")
        if b.functional_nature:
            from app.raman_saab.detailed_report import _SIGN_NAME as _SN
            hdr_bits.append(f"functional {_esc(b.functional_nature)} for "
                            f"{_esc(_SN[r.chart.asc_sign])} (HTJAH-I:523-604)")
        hdr = (f'<p class="section-sub"><i>{"; ".join(hdr_bits)}</i></p>'
               if hdr_bits else "")
        casts = ("" if not b.casts_drishti else
                 f'<p class="section-sub"><b>Casts drishti on</b> &mdash; '
                 f'{_esc(", ".join(b.casts_drishti))} (whole-sign)</p>')
        recv = (f'<p class="section-sub"><b>Receives drishti from</b> &mdash; '
                f'{_esc(", ".join(b.receives_drishti))}</p>'
                if b.receives_drishti else
                ('<p class="section-sub"><b>Receives drishti from</b> &mdash; '
                 'no planet aspects it</p>'
                 if (b.rupas is not None or b.planet in ("Rahu", "Ketu")) else ""))
        av_line = ("" if not (b.avastha and b.avastha_result) else
                   f'<p class="section-sub"><b>Avastha consequence (HPA Ch.7)</b> '
                   f'&mdash; {_esc(b.avastha)}: {_esc(b.avastha_result)}</p>')
        family = ("" if not (b.family_role_named or b.family_role) else
                  f'<p class="section-sub"><b>Family/karaka duties</b> &mdash; '
                  f'{_esc(b.family_role_named or b.family_role)}</p>')
        receipts = (f'<p class="section-sub"><b>Receipts</b> &mdash; {b.census_count} '
                    f'graph appearances ({_esc(census)})</p>')
        blocks.append(
            f'<h3>{_esc(b.planet)}'
            + (f' &mdash; {_esc(b.role_line)}' if b.role_line else '') + '</h3>'
            + hdr
            + f'<p>{_esc(b.prose)}</p>'
            + _quote("In its sign (HPA-22)", b.sign_text) + node_sign_note
            + _quote("In its house (HPA-21)", b.house_text)
            + casts + recv + av_line
            + family + disease
            + _quote("Its Mahadasha runs NOW (HPA-24)", b.md_result_now)
            + _quote("Its Bhukti runs NOW (HPA-24)", b.ad_result_now)
            + _quote("Transit results (HPA-34, house-by-house from the Moon)",
                     b.transit_text)
            + vocation + modern + receipts)
    return (
        '<h2 class="section" id="planet-bios">Planet biographies (dominant grahas)</h2>'
        '<p class="section-sub"><b>In simple terms:</b> the grahas that drive the most of '
        'this chart&rsquo;s computed readings, counted over the judgment graph, each told '
        'as one story. Every line re-reads a value shown elsewhere; nothing here is a new '
        'judgment.</p>' + "".join(blocks))


def _digest_section(r: DetailedReport) -> str:
    """v19 — the engine's own ranked digest, previously JSON/interactive-only (the
    coherence audit's completeness repair)."""
    if not r.digest.items:
        return ""
    rows = "".join(
        # 1-based rank for humans (Wave-2, 2026-08-17); `priority` stays 0-based in JSON.
        f'<tr><td class="num">{it.priority + 1}</td><td>{_esc(it.kind)}</td>'
        f'<td><b>{_esc(it.title)}</b> &mdash; {_esc(it.detail)}</td><td>{_esc(it.lean)}</td>'
        f'<td>{_esc(", ".join(it.sections)) if it.sections else "&ndash;"}</td>'
        f'<td>{_esc(", ".join(it.cites)) if it.cites else "&ndash;"}</td></tr>'
        for it in r.digest.items)
    return (
        '<h2 class="section" id="digest">What matters most (ranked digest)</h2>'
        f'<p class="section-sub"><i>{_esc(r.digest.headline)}</i></p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th class="num">#</th>'
        '<th>kind</th><th>finding</th><th>lean</th><th>bridges</th><th>cites</th></tr>'
        f'</thead><tbody>{rows}</tbody></table></div>')


def _positions(r: DetailedReport) -> str:
    rows = []
    # Ascendant row first (2026-08-17 report-critique fix: exact degrees + Ascendant +
    # nakshatra lord, so the cast is checkable against Jagannatha Hora and the birth
    # Mahadasha is auditable from the Moon's star-lord).
    asc_lon_s, asc_nak, asc_pada, asc_nav, asc_sign = ascendant_position(r.chart)
    asc_nk = nakshatra_signature.signature_for(asc_nak)
    rows.append(
        f'<tr><td><b>Ascendant</b></td><td class="num">{_esc(asc_lon_s)}</td>'
        f'<td>{_esc(_SIGN_NAME[asc_sign])}</td>'
        f'<td class="num">1</td>'
        f'<td>{_esc(asc_nk.name if asc_nk else "?")} ({asc_pada})</td>'
        f'<td>{_esc(nakshatra_lord(asc_nak))}</td>'
        f'<td>{_esc(_SIGN_NAME[asc_nav])}</td>'
        f'<td class="muted-cell">&ndash;</td></tr>')
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
            f'<tr><td><b>{_esc(name)}</b></td><td class="num">{_esc(format_longitude(p.lon))}</td>'
            f'<td>{_esc(_SIGN_NAME[p.sign])}</td>'
            f'<td class="num">{p.rasi_house}</td>'
            f'<td>{_esc(nk.name if nk else "?")} ({p.pada})</td>'
            f'<td>{_esc(nakshatra_lord(p.nakshatra))}</td>'
            f'<td>{_esc(_SIGN_NAME[p.navamsa_sign])}</td>'
            f'<td class="muted-cell">{_esc(", ".join(notes)) or "&ndash;"}</td></tr>')
    return (
        '<h2 class="section" id="positions">Planetary positions</h2>'
        '<p class="section-sub">So the reading can be checked &mdash; exact sidereal (Lahiri) '
        'longitudes in sign-degree form, Ascendant included; the nakshatra lord is each '
        'star&rsquo;s Vimshottari lord (the Moon&rsquo;s row explains the birth Mahadasha).</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>graha</th>'
        '<th class="num">longitude</th><th>sign</th>'
        '<th class="num">house</th><th>nakshatra (pada)</th><th>nak lord</th><th>navamsa</th>'
        '<th>notes</th></tr>'
        f'</thead><tbody>{"".join(rows)}</tbody></table></div>')


def _yogas(r: DetailedReport) -> str:
    # Wave-2 A (2026-08-18, add-only): coverage disclosure + cancelled-Kemadruma +
    # notable absences + family names + deep-read-rank ordering — same content as the
    # markdown surface (template contract: every renderer shows every addition).
    from app.raman_saab.doctrine.yogas import YOGAS as _RECORDS
    from app.raman_saab.doctrine.yogas import (MAHAPURUSHA_IDS, family_breakdown,
                                               yoga_family)
    from app.raman_saab.primitives.bhangas import kemadruma as _kem_geometry
    from app.raman_saab.yoga_deep_read import kemadruma_cancellation_branch

    kem_html = ""
    if _kem_geometry(r.chart):
        _kb = kemadruma_cancellation_branch(r.chart)
        if _kb is not None:
            kem_html = (f'<p class="section-sub"><i>Kemadruma geometry is present but '
                        f'cancelled by {_esc(_kb)} &mdash; the yoga does not fire '
                        f'(bhanga per 3HC:2182-2185; the Arishta chapter reports the '
                        f'same three-state read).</i></p>')
    absent_bits = []
    if not any(y.id in MAHAPURUSHA_IDS for y in r.yogas):
        absent_bits.append("no Pancha Mahapurusha yoga fires")
    if not any(y.kind == "arishta" for y in r.yogas):
        absent_bits.append("no encoded arishta yoga fires")
    absent_html = (f'<p class="section-sub"><i>Notable absences (computed from the same '
                   f'detection pass): {_esc("; ".join(absent_bits))}.</i></p>'
                   if absent_bits else "")
    fams = "; ".join(f"{fam} {n}" for fam, n in family_breakdown())
    coverage_html = (
        f'<p class="section-sub"><i>Coverage disclosure: {len(_RECORDS)} named '
        f'combinations are encoded and checked against every chart, of the ~300 in '
        f'Raman&rsquo;s <b>Three Hundred Important Combinations</b> and allied chapters '
        f'&mdash; by family: {_esc(fams)}. A yoga absent from this list is '
        f'<b>unchecked, not absent</b>.</i></p>')
    if not r.yogas:
        return ('<h2 class="section" id="yogas">Yogas</h2>'
                '<p class="section-sub">No encoded yoga fires on this chart.</p>'
                + kem_html + absent_html + coverage_html)
    rank_of = {yd.id: yd.comparison_rank for yd in r.yoga_deep}
    ordered = sorted(enumerate(r.yogas),
                     key=lambda iy: (rank_of.get(iy[1].id, 10_000), iy[0]))
    items = "".join(
        f'<li><b>{_esc(y.name)}</b> <span class="ykind">'
        f'{_esc(yoga_family(y.id) if (y.kind == "other" and yoga_family(y.id)) else y.kind)}'
        f'</span><br>'
        f'<span class="yeffect">{_esc(y.effect)}</span> '
        f'<code>{_esc(y.source.work)}:{y.source.line}</code></li>'
        for _i, y in ordered)
    order_html = ('<p class="section-sub"><i>Ordered by the deep-read&rsquo;s measured '
                  'comparison rank (strongest participants first).</i></p>'
                  if r.yoga_deep else "")
    return ('<h2 class="section" id="yogas">Yogas present in this chart</h2>'
            '<p class="section-sub">Each with its citation. A yoga&rsquo;s effect depends on the '
            'strength of the planets causing it (HTJAH-I:611).</p>'
            f'<ul class="yogalist">{items}</ul>'
            f'{order_html}{kem_html}{absent_html}{coverage_html}')


def _house_strength_section(r: DetailedReport) -> str:
    """Cross-checks each house's verdict against Bhava Bala rank + SAV band — extends the
    House-by-house section above with whether each verdict stands on strong or shaky ground."""
    if not r.house_strength:
        return ""
    rows = "".join(
        f'<tr><td>H{row.house} {_esc(_HOUSE_NAME[row.house])}</td>'
        f'<td><span class="chip chip--{row.verdict}">{_esc(row.verdict)}</span></td>'
        f'<td class="num">{row.bhava_bala_rank or "n/a"} of 12</td>'
        f'<td class="num">'
        f'{f"{row.bhava_bala / 60.0:.2f}" if row.bhava_bala is not None else "n/a"}</td>'
        f'<td class="num">{row.sav_bindus if row.sav_bindus is not None else "n/a"} '
        f'({_esc(row.sav_band)})</td></tr>'
        for row in r.house_strength)
    return (
        '<h2 class="section" id="house-strength">House strength cross-check</h2>'
        '<p class="section-sub"><b>In simple terms:</b> every house above got a verdict '
        '&mdash; favourable, afflicted or mixed &mdash; but not every house stands on equally '
        'strong ground. This table cross-checks each verdict against two independent strength '
        'measures Raman also uses: Bhava Bala (the house&rsquo;s own strength, RANKED '
        '1st-strongest to 12th-weakest across your chart; Raman gives no numeric cutoff, only a '
        'ranking, GBB-9:332) and its Sarvashtakavarga bindus (that sign&rsquo;s share of the 337 '
        'total, average 28). Neither measure changes the verdict shown above &mdash; they say '
        'whether it is well-supported or sits on thinner ground.</p>'
        '<p class="section-sub"><i>What a strong-yet-afflicted or weak-yet-favourable house '
        'means:</i> Raman lists a house&rsquo;s own strength and its aspects/qualities as '
        'SEPARATE considerations when judging a house &mdash; &ldquo;the strength of the '
        'house itself&rdquo; and &ldquo;the natural qualities of the house&hellip; or the '
        'planets&hellip; having aspects&rdquo; are numbered separately (HTJAH-I:468-478). '
        'Bhava Bala is mostly a magnitude &mdash; HOW FULLY a house&rsquo;s indications are '
        'enjoyed (&ldquo;otherwise he will not sufficiently enjoy them,&rdquo; GBB-9:32-34) '
        '&mdash; though not perfectly independent of direction: one of its three components, '
        'Bhava Drig Bala, is itself signed positive or negative by benefic or malefic aspect '
        '(GBB-9:180-219). In practice the lord&rsquo;s Shadbala (always a magnitude, never '
        'signed) dominates the total, so a strong-but-afflicted house tends to deliver its '
        'difficulty with unusual force and certainty, and a weak-but-favourable house tends to '
        'deliver real good results only mildly or partly enjoyed &mdash; a tendency, not an '
        'absolute rule.</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>house</th><th>verdict</th>'
        '<th class="num">Bhava Bala rank</th><th class="num">Bhava Bala (rupas)</th>'
        '<th class="num">SAV bindus</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>')


def _preponderance_section(r: DetailedReport) -> str:
    """The full per-house testimony ledgers (v14) — Raman's 'judgment is the summing up of the
    influence of planets' (HTJAH-I:983-991) applied to every already-computed axis; the verdict
    column is the House-by-house rollup, displayed but never counted in its own tally."""
    if not r.preponderance.houses:
        return ""
    # Wave-2 E (2026-08-18, add-only): the core/overlay witness-class column and tags —
    # same content as the markdown surface; flat counts and status words untouched.
    rows = "".join(
        f'<tr><td>H{ht_.house} {_esc(_HOUSE_NAME[ht_.house])}</td>'
        f'<td><span class="chip chip--{_vclass(ht_.verdict)}">{_esc(ht_.verdict)}</span></td>'
        f'<td class="num">{ht_.favourable}</td><td class="num">{ht_.adverse}</td>'
        f'<td class="num">{ht_.neutral}</td><td class="num">{ht_.absent}</td>'
        f'<td>core: {ht_.core_favourable} for / {ht_.core_adverse} against</td>'
        f'<td>{_esc(ht_.preponderance)}</td><td>{_esc(ht_.status)}</td></tr>'
        for ht_ in r.preponderance.houses)
    details = "".join(
        f'<div class="now-row"><span class="theme-label">H{ht_.house}</span>'
        + _esc("; ".join(f"{t.name} [{t.klass}] {t.value}" for t in ht_.testimonies
                         if t.lean != "absent") or "no decided testimony") + '</div>'
        for ht_ in r.preponderance.houses)
    pr = r.preponderance
    picks = []
    if pr.most_corroborated_favourable is not None:
        picks.append(f'most-corroborated favourable: H{pr.most_corroborated_favourable}')
    if pr.most_corroborated_afflicted is not None:
        picks.append(f'most-corroborated afflicted: H{pr.most_corroborated_afflicted}')
    if pr.most_contested is not None:
        picks.append(f'most-contested: H{pr.most_contested}')
    picks_html = (f'<p class="plain">{_esc(" | ".join(picks))}</p>' if picks else "")
    return (
        '<h2 class="section" id="preponderance">Preponderance of testimonies</h2>'
        '<p class="section-sub"><b>In simple terms:</b> Raman defines judgment itself as '
        '&ldquo;the summing up of the influence of planets&rdquo; &mdash; the house, its lord, '
        'its occupants and its karaka weighed together (HTJAH-I:983-991), with everything '
        '&ldquo;properly weighed before any result can be deduced&rdquo; (HTJAH-I:495; '
        'HTJAH-II:654-661 repeats the injunction for marriage, and &ldquo;never&hellip; on '
        'the basis of one or two combinations&rdquo; is his own wording, said of mental '
        'diagnosis, HTJAH-I:6245-6246). This table lines up, per house, every already-computed '
        'testimony the report holds elsewhere and counts where the balance lies &mdash; '
        'Raman&rsquo;s own conclusion word: &ldquo;there is a preponderance of benefic '
        'influences&hellip;&rdquo; (HTJAH-I:8870).</p>'
        '<p class="section-sub"><i>Three honesty rules govern this table.</i> (1) The Verdict '
        'column is the authoritative House-by-house verdict, unchanged &mdash; and it is '
        'deliberately NOT counted among its own witnesses (a headline cannot corroborate '
        'itself). (2) Raman states NO numeric rule for how many testimonies decide a matter '
        '(HTJAH-I:495 says only that all must be properly weighed &mdash; and his own worked '
        'conclusion weighs witnesses unequally, HTJAH-I:8870-8876); the Preponderance column '
        'here is a simple equal-weight majority of leaning witnesses &mdash; a presentation '
        'convention borrowing his vocabulary, not his weighing &mdash; it never alters a '
        'verdict, and a &ldquo;contested&rdquo; row means the witnesses split, not that the '
        'verdict is wrong. (3) The witnesses are NOT independent votes: lord, karaka and '
        'navamsa are the verdict&rsquo;s own inputs restated by name, and the majority tenor '
        'derives from the same significations as the headline. Yogas bearing on a house '
        '(Raman&rsquo;s Primary Considerations, e.g. HTJAH-I:4135-4139) ARE now tallied, '
        'mapped on his worked-chart principle &mdash; the houses each yoga&rsquo;s '
        'constituent planets own, occupy or aspect (&ldquo;the nature of ownership of the '
        'planets causing the yoga,&rdquo; HTJAH-I:2879-2890 &mdash; the principle, not an '
        'exact derivation; his own example there names one house this mapping cannot '
        'produce) &mdash; with disclosed limits: whole-chart pattern yogas carry no '
        'constituent identity and are unmapped, and formation-strength modifiers are not '
        'graded &mdash; dusthana formation can nullify Gajakesari (HTJAH-I:2948-2956) and '
        'can bring Raja-Yoga Bhanga (HTJAH-I:15903, 16139; not absolutely, 15531), so a '
        'dusthana-formed raja yoga may lean favourable here despite a possible bhanga. A '
        'yoga row leans by its encoded kind (raja/dhana favourable, arishta adverse) and, for '
        'the specific yogas whose classical printed effect is unambiguous, by that effect '
        '&mdash; the Pancha Mahapurusha, Budha-Aditya, Vasumathi and Jaya favourable; Daridra '
        'and Asatyavadi adverse (each with its own citation in the Yogas section). Lunar and '
        'the remaining other-kind yogas stay neutral (a conditionally-benefic lunar yoga can '
        'be nullified in dusthana formation). Bhava-Bala rank is shown as a magnitude and '
        'carries no direction.</p>'
        '<p class="section-sub"><i>(4) A witness-class tag separates core testimony '
        '&mdash; the house&rsquo;s own lord, karaka and navamsa, the axes Raman&rsquo;s '
        'summing-up itself names (HTJAH-I:983-991) &mdash; from overlay cross-checks '
        '(SAV band, Bhava-Bala rank, matter-vargas, majority tenor, yoga bearings). The '
        'Core column restates the same rows as a second count pair; it is Raman&rsquo;s '
        'unequal weighing made visible, not a new weighting, and it alters nothing. '
        'Yoga-bearing rows additionally disclose their link: [direct - own/occupy], the '
        'factor his worked charts demonstrate, vs [aspect-derived - admitted '
        'extension].</i></p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>house</th><th>verdict</th>'
        '<th class="num">for</th><th class="num">against</th><th class="num">neutral</th>'
        '<th class="num">absent</th><th>core (for/against)</th>'
        '<th>preponderance</th><th>status</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>'
        f'<div class="instrument">{details}</div>'
        f'{picks_html}')


def _yoga_timing_section(r: DetailedReport) -> str:
    """When does each fired yoga's own lord run as MD or AD — extends the Yogas section above
    with WHEN, reusing the same lord_quality strength read Life-narrative already computes."""
    if not r.yoga_timing:
        return ""
    # Wave-2 C (2026-08-18, add-only): MD-context on AD rows, a NOW marker on the
    # row(s) containing the reference date, and the shared per-yoga next-ripening
    # summary above the retained full table.
    from app.raman_saab.detailed_report import yoga_next_ripening
    ripening = yoga_next_ripening(r)
    ripening_html = ""
    if ripening:
        ripening_html = (
            '<p class="section-sub"><i>Next ripening, per yoga (the full table below '
            'is retained):</i></p><ul>'
            + "".join(f'<li><b>{_esc(n)}</b> &mdash; {_esc(s)}</li>'
                      for n, s in ripening)
            + '</ul>')
    # Wave-3 (2026-08-18): the rows are GROUPED BY YOGA (shared
    # `detailed_report.yoga_timing_grouped`) instead of interleaved by date — each group
    # opens with a labelled band row, every window is retained, no column is dropped.
    from app.raman_saab.detailed_report import yoga_timing_grouped
    rows = ""
    for yname, group in yoga_timing_grouped(r):
        rows += (f'<tr class="yoga-group"><th colspan="6">{_esc(yname)} &mdash; '
                 f'{len(group)} constituent-lord window'
                 f'{"s" if len(group) != 1 else ""}</th></tr>')
        rows += "".join(
            f'<tr><td><b>{_esc(t.yoga_name)}</b></td>'
            f'<td>{_esc(f"AD (under {t.maha} MD)" if t.role == "AD" and t.maha else t.role)}'
            f'</td>'
            f'<td>{_esc(t.planet)}</td>'
            f'<td>{_outlook_window_label(t.period_start_jd, t.period_end_jd)}</td>'
            f'<td>{_esc(t.quality.tag)}</td>'
            f'<td>{"NOW" if t.period_start_jd <= r.ref_jd < t.period_end_jd else ""}</td></tr>'
            for t in group)
    return (
        '<h2 class="section" id="yoga-timing">Yoga &times; Dasha timing</h2>'
        '<p class="section-sub"><b>In simple terms:</b> a yoga is not always "on" &mdash; Raman '
        'says it ripens most clearly during the periods of its own ruling planet(s) '
        '(HTJAH-I:4324). "Delivery" is how well-placed that planet is in your natal chart (well '
        '/ mixed / poorly / unknown) &mdash; the same strength read the rest of this report '
        'already uses; magnitude scales with it, and doubles at Vargottama (HTJAH-I:5372). Most '
        'named yogas above can be pinned to specific ruling planets &mdash; a fixed planet, a '
        'house-lordship, or a small checkable set of candidates. The whole-chart-pattern yogas '
        '(where all seven visible planets together form a shape or count, not any one or two of '
        'them specifically) have no single "lord" in Raman&rsquo;s own definition and simply '
        'have no row here &mdash; a genuine coverage gap in what this cross-check computes, not '
        'a judgment that they lack timing.</p>'
        f'{ripening_html}'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>yoga</th><th>period</th>'
        '<th>planet</th><th>window</th><th>delivery</th><th>now</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>')


def _sav(r: DetailedReport) -> str:
    if not r.sav:
        return ""
    head = "".join(f"<th>{_SIGN_NAME[i][:3]}</th>" for i in range(1, 13))
    vals = [r.sav.get(i, 0) for i in range(1, 13)]
    lo, hi = min(vals), max(vals)
    span = max(hi - 28, 28 - lo, 1)
    cells = ""
    for i, v in enumerate(vals, start=1):
        # heat: deviation from the 28-bindu average, green above / terracotta below
        t = min(abs(v - 28) / span, 1.0)
        hue = "--favourable" if v >= 28 else "--afflicted"
        cells += (f'<td class="num heat" style="background:color-mix(in srgb,var({hue}) '
                  f'{t * 32:.0f}%,transparent)" title="{_esc(_SIGN_NAME[i])}: {v} bindus '
                  f'({v - 28:+d} vs average)">{v}</td>')
    # AV completeness (2026-08-17, append-only): deviation row vs the 337/12 average and the
    # Lagna / Moon-sign columns marked (Gochara is graded FROM the Moon), then the full BAV
    # 7x12 matrix, the HPA-26 reductions and the Sodya Pinda — the layer the engine always
    # computed, now shown. Same fields as the markdown renderer.
    dev_cells = "".join(f'<td class="num">{v - 28:+d}</td>' for v in vals)
    moon_p = r.chart.planets.get("Moon")
    moon_sign = moon_p.sign if moon_p is not None else None
    mark_cells = ""
    for i in range(1, 13):
        m = [lbl for lbl, hit in (("Lagna", i == r.chart.asc_sign),
                                  ("Moon", i == moon_sign)) if hit]
        mark_cells += f'<td class="strong">{"+".join(m)}</td>' if m else "<td></td>"
    extra = (
        '<p class="section-sub">Second row: deviation vs the 28-bindu average. Third row: '
        'the Lagna column (house 1; count houses from it) and the Moon-sign column (transits '
        'in the Gochara section are judged from the Moon).</p>')
    if r.bav_matrix:
        bav_head = ("<th>Planet</th>"
                    + "".join(f"<th>{_SIGN_NAME[i][:3]}</th>" for i in range(1, 13))
                    + "<th>Total</th><th>Natal seat</th>")
        bav_rows = ""
        for bm in r.bav_matrix:
            row_cells = ""
            for i, v in enumerate(bm.bindus, start=1):
                cls = ' class="num strong"' if bm.seat_sign == i else ' class="num"'
                row_cells += f"<td{cls}>{v}</td>"
            seat = (f"{_esc(_SIGN_NAME[bm.seat_sign][:3])} ({bm.seat_bindus})"
                    if bm.seat_sign is not None else "n/a")
            bav_rows += (f"<tr><td>{_esc(bm.planet)}</td>{row_cells}"
                         f'<td class="num">{bm.total}</td><td>{seat}</td></tr>')
        extra += (
            '<h3>Bhinnashtakavarga (BAV) &mdash; each planet&rsquo;s own bindu row</h3>'
            '<p class="section-sub">The per-planet tables the SAV row above sums (canonical '
            'Parashari benefic-places tables; each planet&rsquo;s total is a fixed checksum '
            'and the seven rows always sum to 337). The Gochara table&rsquo;s &ldquo;AV '
            'bindus&rdquo; and Kakshya columns, and the AV dasha-seat outlook, all read from '
            'these rows. The highlighted cell is that planet&rsquo;s own natal sign &mdash; '
            'its seat, shown again in the last column.</p>'
            f'<div class="tablewrap"><table class="grid sav"><thead><tr>{bav_head}</tr>'
            f'</thead><tbody>{bav_rows}</tbody></table></div>')
    if r.bav_reduced:
        red_head = ("<th>Planet</th>"
                    + "".join(f"<th>{_SIGN_NAME[i][:3]}</th>" for i in range(1, 13)))
        tri_rows = "".join(
            f"<tr><td>{_esc(br.planet)}</td>"
            + "".join(f'<td class="num">{v}</td>' for v in br.trikona) + "</tr>"
            for br in r.bav_reduced)
        fin_rows = "".join(
            f"<tr><td>{_esc(br.planet)}</td>"
            + "".join(f'<td class="num">{v}</td>' for v in br.reduced) + "</tr>"
            for br in r.bav_reduced)
        extra += (
            '<h3>HPA-26 reductions (Trikona + Ekadhipathya Sodhana)</h3>'
            '<p class="section-sub">HPA-26 reductions &mdash; used classically for special '
            'calculations; shown for completeness; ASP transit application deferred pending '
            'corpus. Raman: the bindu tables &ldquo;must be subjected to two reductions, '
            'viz., Thrikona reduction and Ekadhipathya reduction&rdquo; (HPA-26:390-393), in '
            'that order &mdash; &ldquo;After the Thrikona reduction, the Ekadhipathya '
            'reduction must be applied&rdquo; (HPA-26:466-467). Trikona follows Raman&rsquo;s '
            'own stated SUBTRACT reading (HPA-26:423-431), regression-pinned to his worked '
            'Sun table (HPA-26:432-462).</p>'
            '<p class="section-sub"><strong>After Trikona Sodhana</strong> '
            '(HPA-26:403-421):</p>'
            f'<div class="tablewrap"><table class="grid sav"><thead><tr>{red_head}</tr>'
            f'</thead><tbody>{tri_rows}</tbody></table></div>'
            '<p class="section-sub"><strong>After both reductions</strong> (Ekadhipathya '
            'applied, HPA-26:464-497):</p>'
            f'<div class="tablewrap"><table class="grid sav"><thead><tr>{red_head}</tr>'
            f'</thead><tbody>{fin_rows}</tbody></table></div>')
    if r.sodya_pinda:
        sp_rows = "".join(
            f"<tr><td>{_esc(sp.planet)}</td>"
            f'<td class="num">{sp.rasi}</td><td class="num">{sp.graha}</td>'
            f'<td class="num">{sp.total}</td></tr>'
            for sp in r.sodya_pinda)
        extra += (
            '<h3>Sodya Pinda (Rasi + Graha Gunakara)</h3>'
            '<div class="tablewrap"><table class="grid sav"><thead><tr><th>Planet</th>'
            '<th class="num">Rasi Gunakara</th><th class="num">Graha Gunakara</th>'
            '<th class="num">Sodya Pinda</th></tr></thead>'
            f'<tbody>{sp_rows}</tbody></table></div>'
            '<p class="section-sub">Computed from the reduced tables above: each sign&rsquo;s '
            'reduced bindus &times; its fixed zodiacal factor (Rasi Gunakara, '
            'HPA-26:1149-1153), plus the reduced bindus in each graha&rsquo;s occupied sign '
            '&times; its fixed planetary factor (Graha Gunakara, HPA-26:1311-1315). The sum '
            'is Raman&rsquo;s Sodya Pinda by his own naming (ASP-14:196-198); HPA-26 applies '
            'it to LONGEVITY (the &times;7/27 Ayurdaya use, HPA-26:1400-1404 / '
            'ASP-14:199-201). Honesty note, recorded not fudged: on ASP-14&rsquo;s worked '
            'Standard Horoscope Raman prints Sun 96/86/182 where this pipeline gives '
            '103/88/191 on his own stated longitudes &mdash; the divergence is in HIS printed '
            'reduced tables (the 1962 book carries known misprints), so the engine pins the '
            'RULES, anchored on HPA-26&rsquo;s own worked reduction, and records this '
            'delta.</p>')
    return ('<h2 class="section" id="sav">Ashtakavarga</h2>'
            '<p class="section-sub">Sarvashtakavarga bindus per sign; average 28 (total 337). '
            'Raman rates it corroborative, not decisive &mdash; <em>&ldquo;it does not seem to be '
            'quite reliable&rdquo;</em> (HTJAH-II:4453-4456).</p>'
            f'<div class="tablewrap"><table class="grid sav"><thead><tr>{head}</tr></thead>'
            f'<tbody><tr>{cells}</tr><tr>{dev_cells}</tr><tr>{mark_cells}</tr></tbody>'
            f'</table></div>'
            f'{extra}')


#: South-Indian fixed-sign layout: 4x4 grid, signs clockwise from Pisces top-left.
_SI_LAYOUT: tuple[tuple[int, ...], ...] = ((12, 1, 2, 3), (11, 0, 0, 4), (10, 0, 0, 5),
                                           (9, 8, 7, 6))
_GRAHA_ABBR = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju",
               "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"}


def _chart_grid(r: DetailedReport, *, navamsa: bool) -> str:
    """A traditional South-Indian 12-box chart (signs fixed, Asc marked) as a CSS grid."""
    asc = r.chart.asc_sign
    if navamsa:
        from app.raman_saab.primitives import special_points as sp
        try:
            asc = sp.navamsa_lagna(r.chart).sign
        except Exception:  # noqa: BLE001
            pass
    occupants: dict[int, list[str]] = {s: [] for s in range(1, 13)}
    for name, p in planet_rows(r.chart):
        sign = p.navamsa_sign if navamsa else p.sign
        occupants[sign].append(_GRAHA_ABBR.get(name, name[:2]))

    cells = []
    for row in _SI_LAYOUT:
        for sign in row:
            if sign == 0:
                continue
            is_asc = sign == asc
            body = "".join(f'<i>{g}</i>' for g in occupants[sign])
            cells.append(
                f'<div class="cbox{" asc" if is_asc else ""}" '
                f'style="grid-area:s{sign}">'
                f'<span class="csign">{_esc(_SIGN_NAME[sign][:3])}'
                f'{" &middot; Asc" if is_asc else ""}</span>'
                f'<div class="cgrahas">{body}</div></div>')
    label = "Navamsa (D-9)" if navamsa else "Rasi (D-1)"
    return (f'<figure class="chartfig"><figcaption>{label}</figcaption>'
            f'<div class="chartgrid">{"".join(cells)}'
            f'<div class="cmid">{_esc(_SIGN_NAME[asc])}<span>lagna</span></div>'
            f'</div></figure>')


def _varga_card(label: str, body: str) -> str:
    """Turn a varga renderer's monospace block into a structured card.

    The renderers share one shape: provenance notes (`* [TAG] (cite) text`), a
    `-- RAMAN CORE --` section, then a `-- D-x OVERLAY --` section, with `key : value`
    rows and `>>> VERDICT <<<` banners. Parsed rather than re-implemented so the doctrine
    text stays the single source.
    """
    notes: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    cur: list[str] = []
    cur_title = ""
    for raw in body.splitlines():
        line = raw.rstrip()
        if not line.strip() or set(line.strip()) <= {"="}:
            continue
        if line.startswith("* "):
            notes.append(line[2:].strip())
            continue
        if line.strip().startswith("--") and line.strip().endswith("--"):
            if cur_title or cur:
                sections.append((cur_title, cur))
            cur_title, cur = line.strip().strip("- ").strip(), []
            continue
        if not cur_title and line.isupper():          # the renderer's own title line
            continue
        cur.append(line)
    if cur_title or cur:
        sections.append((cur_title, cur))

    def _rows(lines: list[str]) -> str:
        out = []
        for ln in lines:
            t = ln.strip()
            if t.startswith(">>>"):
                out.append(f'<div class="vbanner">{_esc(t.strip("&gt;&lt;> ").strip())}</div>')
                continue
            if t.startswith("- "):
                t = t[2:]
            key, sep, val = t.partition(":")
            if sep and len(key) < 42:
                out.append(f'<div class="vrow"><span class="vk">{_esc(key.strip())}</span>'
                           f'<span class="vv">{_esc(val.strip())}</span></div>')
            else:
                out.append(f'<div class="vtext">{_esc(t)}</div>')
        return "".join(out)

    note_html = "".join(
        f'<li>{_esc(n)}</li>' for n in notes)
    sec_html = ""
    for title, lines in sections:
        core = "RAMAN CORE" in title.upper()
        sec_html += (
            f'<div class="vsec {"vcore" if core else "voverlay"}">'
            f'<div class="vsec-label">{_esc(title)}</div>{_rows(lines)}</div>')
    return (
        f'<details class="varga"><summary>{_esc(label)}</summary>'
        f'<div class="vbody">{sec_html}'
        + (f'<details class="vnotes"><summary>provenance &amp; citations</summary>'
           f'<ul>{note_html}</ul></details>' if note_html else "")
        + "</div></details>")


#: planet -> house relations drawn in the influence matrix: (key, label, colour, glyph).
#: Order is the column order INSIDE each cell, so the same relation always sits in the same
#: sub-position and a column can be scanned down at a glance.
_MATRIX_RELATIONS: tuple[tuple[str, str, str, str], ...] = (
    ("lord_of", "lord of", "var(--afflicted)", "circle"),
    ("occupies", "occupies", "var(--doctrine)", "square"),
    ("aspects", "aspects", "var(--mixed)", "triangle"),
    ("karaka_of", "karaka of", "var(--favourable)", "diamond"),
)


def _judgment_graph_svg(jg, planets: list[str]) -> str:
    """The planet -> house influence MATRIX (mirrors the interactive page's
    `planetInfluenceMatrix`), as static server-side SVG — `<title>` elements give native hover
    tooltips with no JS. A grid, not a node-link diagram: ~90 planet->house edges drawn as
    curved lines cross into unreadable spaghetti, whereas one cell per (planet, house) pair
    never overlaps. Empty string when there is nothing to draw."""
    rel_keys = [r[0] for r in _MATRIX_RELATIONS]
    pairs: dict[tuple[str, int], dict[str, str]] = {}
    for e in jg.edges:
        if not (e.src.startswith("planet:") and e.dst.startswith("house:")):
            continue
        if e.relation not in rel_keys:
            continue
        p = e.src.split(":")[1]
        if p not in planets:
            continue
        # dedupe: a planet is (say) karaka of a house ONCE, even when several significations
        # assert it — the mark reflects the relation, not how many edges carry it.
        pairs.setdefault((p, int(e.dst.split(":")[1])), {})[e.relation] = e.cite or ""
    if not pairs:
        return ""

    order = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
    present = {p for p, _h in pairs}
    rows = [p for p in order if p in present]
    houses = list(range(1, 13))
    verdict = {int(n.id.split(":")[1]): dict(n.data).get("verdict", "")
               for n in jg.nodes if n.kind == "house"}

    pad_l, pad_t, cw, rh = 78, 44, 48, 34
    w = pad_l + len(houses) * cw + 8
    h_total = pad_t + len(rows) * rh + 10
    parts: list[str] = []

    for ci, hn in enumerate(houses):
        x = pad_l + ci * cw
        vc = _vclass(verdict.get(hn, ""))
        col = {"favourable": "var(--favourable)", "afflicted": "var(--afflicted)"}.get(
            vc, "var(--mixed)")
        title = f"H{hn} · {_HOUSE_NAME.get(hn, '')}" + (
            f" — {verdict[hn]}" if verdict.get(hn) else "")
        parts.append(f'<rect x="{x}" y="6" width="{cw - 3}" height="{pad_t - 12}" rx="3" '
                     f'fill="{col}" opacity="0.12"><title>{_esc(title)}</title></rect>')
        parts.append(f'<text x="{x + (cw - 3) / 2:.1f}" y="{pad_t - 20}" font-size="11" '
                     f'text-anchor="middle" font-weight="600" fill="{col}">H{hn}</text>')
        parts.append(f'<rect x="{x}" y="{pad_t - 12}" width="{cw - 3}" height="3" fill="{col}"/>')

    for ri, p in enumerate(rows):
        y = pad_t + ri * rh
        if ri % 2 == 0:
            parts.append(f'<rect x="{pad_l}" y="{y}" width="{len(houses) * cw}" height="{rh}" '
                         f'fill="var(--ink-soft)" opacity="0.06"/>')
        parts.append(f'<text x="{pad_l - 8}" y="{y + rh * 0.62:.1f}" font-size="11" '
                     f'text-anchor="end" font-weight="600" fill="var(--ink)">{_esc(p)}</text>')
        for ci, hn in enumerate(houses):
            rels = pairs.get((p, hn))
            if not rels:
                continue
            for idx, (key, label, colour, glyph) in enumerate(_MATRIX_RELATIONS):
                if key not in rels:
                    continue
                gx = pad_l + ci * cw + 10 + idx * 10
                gy = y + rh / 2
                cite = rels[key]
                title = (f"{p} {label} H{hn} ({_HOUSE_NAME.get(hn, '')})"
                        + (f" — {cite}" if cite else ""))
                tt = f"<title>{_esc(title)}</title>"
                if glyph == "circle":
                    parts.append(f'<circle cx="{gx}" cy="{gy:.1f}" r="4.2" fill="{colour}" '
                                 f'opacity="0.95">{tt}</circle>')
                elif glyph == "square":
                    parts.append(f'<rect x="{gx - 3.6}" y="{gy - 3.6:.1f}" width="7.2" '
                                 f'height="7.2" rx="1" fill="{colour}" opacity="0.95">{tt}</rect>')
                elif glyph == "triangle":
                    parts.append(
                        f'<polygon points="{gx},{gy - 4.4:.1f} {gx + 4},{gy + 3.4:.1f} '
                        f'{gx - 4},{gy + 3.4:.1f}" fill="{colour}" opacity="0.95">{tt}</polygon>')
                else:
                    parts.append(
                        f'<polygon points="{gx},{gy - 4.4:.1f} {gx + 4.4},{gy:.1f} '
                        f'{gx},{gy + 4.4:.1f} {gx - 4.4},{gy:.1f}" fill="{colour}" '
                        f'opacity="0.95">{tt}</polygon>')

    legend = " &middot; ".join(
        f'<span style="color:{c}">{"●" if g == "circle" else "■" if g == "square" else "▲" if g == "triangle" else "◆"}</span> {lb}'
        for _k, lb, c, g in _MATRIX_RELATIONS)
    body = "".join(parts)
    return (f'<p class="section-sub">{legend} &mdash; one cell per planet/house pair; column '
            f'headers are tinted by that house&rsquo;s own natal verdict. Hover any mark for '
            f'the exact relation and citation.</p>'
            f'<div class="tablewrap"><svg viewBox="0 0 {w} {h_total}" '
            f'style="max-width:100%;height:auto;min-width:{w}px" role="img" '
            f'aria-label="Judgment graph — planet to house influence matrix">{body}</svg></div>')


def _judgment_graph_section(r: DetailedReport) -> str:
    """v32 — the judgment graph, already USED in Your Reading (the dominant-planet census
    sentence quotes its count) and now shown right beside it: node/edge counts, the relation
    breakdown, and the full planet -> house network as a static inline SVG."""
    from app.raman_saab.judgment_graph import build_judgment_graph
    try:
        jg = build_judgment_graph(r)
    except Exception:  # noqa: BLE001 — sparse/Track-B chart; a re-read, not a verdict
        return ('<h2 class="section" id="judgment-graph">Judgment graph</h2>'
                '<p class="section-sub caveat">Graph unavailable for this chart (sparse '
                'data) &mdash; the readings above stand on their own evidence regardless.</p>')
    from app.raman_saab.judgment_graph import (DOCTRINE_CONSTANT_RELATIONS,
                                               house_facts, house_sentence)
    by_rel: dict[str, int] = {}
    for e in jg.edges:
        by_rel[e.relation] = by_rel.get(e.relation, 0) + 1
    rel_txt = ", ".join(f"{_esc(k)} {v}" for k, v in sorted(by_rel.items()))
    planets = sorted({e.src.split(":")[1] for e in jg.edges
                      if e.src.startswith("planet:") and e.dst.startswith("house:")})

    # PRIMARY — what shapes each area of THIS life, as a vertical stack of plain sentences.
    cards: list[str] = []
    for h, f in sorted(house_facts(jg).items()):
        col = {"favourable": "var(--favourable)", "afflicted": "var(--afflicted)"}.get(
            _vclass(f.verdict), "var(--mixed)")
        # karaka is NOT chipped — it gets its own line below (chipping it too said the same
        # thing twice); the chips carry only the chart-specific roles.
        chips = "".join(
            f'<span class="tag">{_esc(p)} &mdash; {_esc(phrase)}</span>'
            for rel, phrase in (("lord_of", "rules it"), ("occupies", "sits in it"),
                                ("aspects", "aspects it"))
            for p in f.roles.get(rel, ()))
        karaka_line = ("" if not f.karakas else
                       '<p class="section-sub">Natural significators (karaka): '
                       + _esc(", ".join(f.karakas)) + '</p>')
        timers = ""
        if f.timers:
            timers = ('<p class="section-sub">Periods that light this house (at best): '
                      + _esc(", ".join(f"{lord}{f' ({g})' if g else ''}"
                                       for lord, g in f.timers)) + '</p>')
        cards.append(
            f'<div class="jg-house" style="border-left:3px solid {col}">'
            f'<p class="jg-house-head"><b>H{h} &middot; {_esc(_HOUSE_NAME.get(h, ""))}</b>'
            + (f' <span class="tag" style="color:{col}">{_esc(f.verdict)}</span>'
               if f.verdict else "")
            + f'</p><p class="doctrine">{_esc(house_sentence(f))}</p>'
            + (f'<p class="section-sub">{chips}</p>' if chips else "")
            + karaka_line + timers + '</div>')

    const_n = sum(by_rel.get(k, 0) for k in DOCTRINE_CONSTANT_RELATIONS)
    const_line = ("" if not const_n else
                  f'<p class="section-sub">A further <b>{const_n}</b> edges record how the '
                  f'report&rsquo;s own sections relate (which section governs another, which '
                  f're-reads another). Those are the same for every chart &mdash; they '
                  f'describe the method, not this nativity &mdash; and are set out in '
                  f'&ldquo;How to read this report&rdquo;.</p>')

    return (
        '<h2 class="section" id="judgment-graph">Judgment graph</h2>'
        '<p class="section-sub">The reasoning behind this reading: every planet linked to '
        'the houses it rules, sits in, aspects or signifies, and to the periods that light '
        'them.</p>'
        '<h3 class="sub">What shapes each area of your life</h3>'
        + "".join(cards)
        + '<h3 class="sub">All planets &times; all houses at once</h3>'
        + _judgment_graph_svg(jg, planets)
        + const_line
        + f'<p class="section-sub"><b>{len(jg.nodes)} nodes, {len(jg.edges)} edges</b> '
          f'&mdash; {rel_txt}.</p>')


def _ruler_section(r: DetailedReport) -> str:
    """Raman's first-impression card (v13): the ruler of the nativity (Lagna lord) and the
    strongest planet by Shadbala, with the HTJAH-I:3892-3897 nature/appearance comparison —
    pure re-reads of already-computed values (see `detailed_report.build_ruler`)."""
    from app.raman_saab.detailed_report import _SIGN_NAME, _jd_month_year
    ru = r.ruler
    rows: list[str] = []
    ll_bit = f"{_esc(ru.lagna_lord)}, lord of the {_esc(_SIGN_NAME[r.chart.asc_sign])} Lagna"
    if ru.lagna_lord_house is not None:
        ll_bit += f", in house {ru.lagna_lord_house}"
    rows.append(f'<div class="now-row"><span class="theme-label">Ruler (Lagna lord)</span>'
                f'{ll_bit}</div>')
    # the ruler's OWN condition block (2026-08-18 report-critique — the chapter's
    # namesake gets the same full read the strongest planet already had)
    ll_cond: list[str] = []
    if ru.lagna_lord_sign is not None:
        ll_cond.append(f"in {_esc(_SIGN_NAME[ru.lagna_lord_sign])}"
                       + (f" ({_esc(ru.ll_dignity)} sign)" if ru.ll_dignity else ""))
    if ru.ll_avastha is not None:
        ll_cond.append(f"{_esc(ru.ll_avastha)} avastha (HPA Ch.7)")
    if ru.ll_rupas is not None and ru.ll_required is not None:
        ll_cond.append(
            f"{ru.ll_rupas:.2f} rupas against its required {ru.ll_required:.1f} "
            f"(GBB-8:303) &mdash; {'meets' if ru.ll_powerful else 'below'} the minimum"
            + (", the only planet in this chart below its own"
               if ru.ll_only_failing else ""))
    if ru.ll_functional_nature is not None:
        ll_cond.append(f"functional {_esc(ru.ll_functional_nature)} for this Lagna")
    if ru.lagna_lord_house is not None:
        ll_cond.append("aspected by "
                       + (", ".join(_esc(a) for a in ru.ll_aspects_received)
                          if ru.ll_aspects_received else "no planet"))
    if ru.ll_dispositor is not None:
        ll_cond.append(f"dispositor {_esc(ru.ll_dispositor)}"
                       + (f" in house {ru.ll_dispositor_house}"
                          if ru.ll_dispositor_house is not None else ""))
    if ll_cond:
        rows.append(f'<div class="now-row"><span class="theme-label">Ruler&rsquo;s own '
                    f'condition</span>{"; ".join(ll_cond)}</div>')
    if ru.foundation_line:
        rows.append(f'<div class="now-row"><span class="theme-label">Foundation</span>'
                    f'{_esc(ru.foundation_line)}</div>')
    if ru.chandra_lagna_lord is not None:
        ch_bit = (f'the signature reads the MOON as the stronger frame (HTJAH-I:645-646), '
                  f'so the Chandra-lagna lord ({_esc(ru.chandra_lagna_lord)}) is the third '
                  f'classical candidate')
        if ru.chandra_ll_condition:
            ch_bit += f' &mdash; it stands {_esc(ru.chandra_ll_condition)}'
        rows.append(f'<div class="now-row"><span class="theme-label">Third candidate '
                    f'(Chandra Lagna)</span>{ch_bit}</div>')
    if ru.strongest is not None and ru.strongest_rupas is not None:
        s_bit = f"{_esc(ru.strongest)} ({ru.strongest_rupas:.1f} rupas)"
        if ru.coincide:
            s_bit += (' &mdash; the ruler itself: &ldquo;the foundation is quite sound&rdquo; '
                      '(HTJAH-I:3880-3882)')
        rows.append(f'<div class="now-row"><span class="theme-label">Strongest (Shadbala)'
                    f'</span>{s_bit}</div>')
        if ru.navamsa_lagna_lord is not None:
            if ru.navamsa_lagna_lord == ru.strongest:
                cmp_bit = (f'the lord of the Navamsa Lagna is the strongest planet itself '
                           f'({_esc(ru.strongest)}); it stamps the nature and appearance '
                           f'either way (HTJAH-I:3892-3897)')
            elif ru.stamps_nature is not None:
                cmp_bit = (f'as between the strongest planet and the lord of the Navamsa Lagna '
                           f'({_esc(ru.navamsa_lagna_lord)}), <b>{_esc(ru.stamps_nature)}</b> '
                           f'is the more powerful and stamps the nature and appearance '
                           f'(HTJAH-I:3892-3897)')
            else:
                cmp_bit = (f'the strongest planet and the lord of the Navamsa Lagna '
                           f'({_esc(ru.navamsa_lagna_lord)}) cannot be ranked here &mdash; '
                           f'no winner is guessed (HTJAH-I:3892-3897)')
            rows.append(f'<div class="now-row"><span class="theme-label">Nature &amp; '
                        f'appearance</span>{cmp_bit}</div>')
        temper = (_esc(ru.temperament) + " (HTJAH-I:6248-6268)" if ru.temperament is not None
                  else "Raman&rsquo;s strongest-planet passage (HTJAH-I:6248-6268) gives no "
                       "line for the Moon &mdash; an honest absence, nothing invented")
        rows.append(f'<div class="now-row"><span class="theme-label">Temperament</span>'
                    f'{temper}</div>')
        cond = []
        if ru.functional_nature is not None:
            cond.append(f"{_esc(ru.functional_nature)} for this Lagna")
        if ru.avastha is not None:
            cond.append(f"{_esc(ru.avastha)} avastha (HPA Ch.7)")
        if ru.ik_lean is not None:
            cond.append(f"{_esc(ru.ik_lean)} Ishta/Kashta lean (GBB-10:134)")
        if ru.vargottama:
            cond.append("vargottama")
        if ru.retrograde:
            cond.append("retrograde")
        if cond:
            rows.append(f'<div class="now-row"><span class="theme-label">Condition</span>'
                        f'{"; ".join(cond)}</div>')
        yb = (", ".join(_esc(n) for n in ru.yogas_involving) if ru.yogas_involving
              else "none of the fired yogas resolves to it")
        rows.append(f'<div class="now-row"><span class="theme-label">Yogas</span>{yb}</div>')
        if ru.md_windows:
            spans = ", ".join(f"{_jd_month_year(s0)} to {_jd_month_year(e0)}"
                              for s0, e0 in ru.md_windows)
            rows.append(f'<div class="now-row"><span class="theme-label">Own Mahadasha</span>'
                        f'{spans}</div>')
        else:
            rows.append('<div class="now-row"><span class="theme-label">Own Mahadasha</span>'
                        'does not fall inside the displayed window</div>')
    else:
        rows.append('<div class="now-row"><span class="theme-label">Strongest (Shadbala)'
                    '</span>no Shadbala on this chart &mdash; nothing is guessed in its '
                    'place</div>')
    return (
        '<h2 class="section" id="ruler">Ruler of the nativity</h2>'
        '<p class="section-sub">Raman&rsquo;s own opening move: &ldquo;in order to obtain a '
        'first impression we must first of all consider the ruler of the nativity&rdquo; '
        '(HTJAH-I:16001-16002) &mdash; and separately, &ldquo;the strongest planet in the '
        'horoscope determines the predominance of the physical, mental and spiritual '
        'peculiarities of the person&rdquo; (HTJAH-I:6248-6250). The classical temperament '
        'lines are shorthand for tendencies, never medical statements &mdash; how the method '
        'reads this chart, not a prediction.</p>'
        + (f'<p class="plain"><b>{_esc(ru.takeaway)}</b></p>' if ru.takeaway else '')
        + f'<div class="instrument">{"".join(rows)}</div>'
        f'<p class="plain">{_esc(ru.signature)}</p>')


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


def _dashboard(r: DetailedReport) -> str:
    rows = "".join(
        f'<tr><td>{_esc(en.matter)}</td><td>D-{en.varga} {_esc(en.varga_name)}</td>'
        f'<td><span class="chip chip--{_vclass(en.verdict)}">{_esc(en.verdict)}</span></td></tr>'
        for en in r.dashboard.entries)
    return ('<h2 class="section" id="dashboard">The twelve matters at a glance</h2>'
            '<p class="section-sub">Each matter&rsquo;s authoritative verdict from its dedicated '
            'deep reader (Raman&rsquo;s method decides; the divisional corroborates).</p>'
            '<div class="tablewrap"><table class="grid"><thead><tr><th>matter</th>'
            '<th>divisional</th><th>verdict</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


def _shadbala(r: DetailedReport) -> str:
    from app.raman_saab.detailed_report import _ishta_kashta_lean as _ik_lean
    from app.raman_saab.primitives.shadbala.total import is_powerful
    sb_rows = [(n, p) for n, p in planet_rows(r.chart) if p.shadbala_rupas is not None]
    if not sb_rows:
        return ""
    rows = ""
    from app.raman_saab.plain_terms import band_rupas
    from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED
    rows = ""
    bars = ""
    notes: list[str] = []
    _comp_names = ("sthana", "dig", "kala", "cheshta", "naisargika", "drik")
    max_r = max(p.shadbala_rupas.total / 60.0 for _n, p in sb_rows) or 1.0
    for i, (name, p) in enumerate(sb_rows):
        sb = p.shadbala_rupas
        tot = sb.total / 60.0
        strong = is_powerful(name, tot)
        band = band_rupas(name, tot)
        ik = (f"{p.ishta:.1f}/{p.kashta:.1f}"
              if p.ishta is not None and p.kashta is not None else "&ndash;")
        comps = (sb.sthana, sb.dig, sb.kala, sb.cheshta, sb.naisargika, sb.drik)
        cells = "".join(f'<td class="num">{v / 60.0:.2f}</td>' for v in comps)
        _req = MIN_REQUIRED.get(name)
        ratio = f"{tot / _req:.2f}" if _req else "&ndash;"
        rows += (f'<tr><td><b>{_esc(name)}</b></td>{cells}'
                 f'<td class="num"><b>{tot:.2f}</b></td>'
                 f'<td class="num">{ratio}</td>'
                 f'<td>{"yes" if strong else "no"}</td><td class="num">{ik}</td>'
                 f'<td>{_esc(band)}</td></tr>')
        if not strong:
            # weakest-component pointer: arithmetic on the six shown values only —
            # NO per-component minimum is asserted (none are encoded)
            _wk_name, _wk_val = min(zip(_comp_names, comps), key=lambda kv: kv[1])
            notes.append(
                f'{_esc(name)} falls below its minimum; of the six components shown, '
                f'its smallest is {_wk_name} ({_wk_val / 60.0:.2f} rupas) &mdash; an '
                f'arithmetic pointer to where the deficit sits, not a per-component '
                f'judgment (no per-component minima are encoded)')
        # the horsepower bar (inline SVG row): bar to max, tick at Raman's requirement
        y = 10 + i * 26
        w = 340.0 * tot / (max_r * 1.15)
        req = MIN_REQUIRED.get(name)
        tick = (f'<line x1="{120 + 340.0 * req / (max_r * 1.15):.1f}" y1="{y - 8}" '
                f'x2="{120 + 340.0 * req / (max_r * 1.15):.1f}" y2="{y + 10}" '
                f'stroke="var(--ink)" stroke-width="1.5" opacity="0.7"/>'
                if req else "")
        color = "var(--fav)" if strong else "var(--aff)"
        bars += (f'<text x="4" y="{y + 4}" style="font-size:11px;fill:var(--ink)">'
                 f'{_esc(name)}</text>'
                 f'<rect x="120" y="{y - 8}" width="{w:.1f}" height="16" rx="3" '
                 f'fill="{color}" opacity="0.8"/>{tick}'
                 f'<text x="{124 + w:.1f}" y="{y + 4}" '
                 f'style="font-size:10px;fill:var(--ink)">{tot:.1f} &mdash; '
                 f'{_esc(band.split(" — ")[0])}</text>')
    svg = (f'<svg viewBox="0 0 560 {14 + len(sb_rows) * 26}" '
           f'style="max-width:100%;height:auto" role="img" '
           f'aria-label="Shadbala strength bars">{bars}</svg>')
    return ('<h2 class="section" id="shadbala">Shadbala &mdash; six-fold strength</h2>'
            '<p class="section-sub"><b>Planetary strength &mdash; think of it as '
            'horsepower:</b> a powerful engine can pull a heavier load, and a strong '
            'planet tends to deliver its indications more effectively. Bars below the '
            'tick fall short of RAMAN&rsquo;S OWN required minimum (GBB-8:303) &mdash; '
            'the bands are his thresholds, never invented cutoffs. The numbers behind '
            'every &ldquo;strong / weak&rdquo; in this report (HTJAH-I:611). '
            'Ishta/Kashta = good-yield / hard-yield potential.</p>'
            f'{svg}'
            '<div class="tablewrap"><table class="grid"><thead><tr><th>graha</th>'
            '<th class="num">sthana</th><th class="num">dig</th><th class="num">kala</th>'
            '<th class="num">cheshta</th><th class="num">naisargika</th><th class="num">drik</th>'
            '<th class="num">total</th><th class="num">ratio</th>'
            '<th>powerful?</th><th class="num">ishta/kashta</th>'
            '<th>in plain terms</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>'
            # scale + definitional notes (2026-08-18 report-critique, append-only)
            '<p class="section-sub">Scale notes: <b>ratio</b> = total / Raman&rsquo;s '
            'required minimum (GBB-8:303) &mdash; 1.00 is exactly the bar. The Sun and '
            'Moon show <b>cheshta 0.00 by definition</b> &mdash; they receive no Cheshta '
            'Bala in the Shadbala total (GBB-6:23-28); that cell is not missing data. '
            '<b>Ishta/Kashta</b> are each on a 0-60 scale (GBB-10:134); this chart&rsquo;s '
            'leans, in the same good/hard vocabulary the period readings use: '
            + _esc("; ".join(f"{n} {_ik_lean(r.chart, n)}" for n, _p in sb_rows
                             if _ik_lean(r.chart, n) is not None)) + '.</p>'
            + "".join(f'<p class="section-sub">{n}.</p>' for n in notes))


def _maraka(r: DetailedReport) -> str:
    mp = getattr(r.chart, "maraka_points", None)
    if mp is None:
        return ""
    tiers = ""
    for tier in ("primary", "secondary", "tertiary"):
        # each graha names WHY it qualified (2026-08-17 report-critique fix: the clause was
        # computed by primitives/maraka.py and discarded before display).
        names = []
        for u in mp.units:
            if u.tier != tier:
                continue
            why = format_maraka_reasons(u.reasons)
            names.append(f"{u.graha} ({why})" if why else u.graha)
        if names:
            tiers += (f'<div class="vrow"><span class="vk">{tier}</span>'
                      f'<span class="vv">{_esc(", ".join(names))}</span></div>')
    s = r.synthesis
    running = ("carries a maraka-tier lord" if r.maraka_period_now
               else "carries no maraka-tier lord")
    return ('<h2 class="section" id="maraka">The maraka scheme</h2>'
            '<p class="section-sub">Raman&rsquo;s second step after the longevity band '
            '(HTJAH-I:761-814): the 2nd and 7th are the houses of death; their lords, occupants '
            'and associates carry maraka power in their periods. A disclosure of the method, not '
            'a prediction &mdash; the validation program measured no chart-specific death-timing '
            'signal.</p>'
            f'<div class="vsec vcore">{tiers}'
            f'<div class="vrow"><span class="vk">22nd drekkana lord</span>'
            f'<span class="vv">{_esc(mp.drekkana22_lord)}</span></div>'
            f'<div class="vrow"><span class="vk">64th navamsa lord</span>'
            f'<span class="vv">{_esc(mp.navamsa64_lord)}</span></div>'
            f'<div class="vrow"><span class="vk">running period</span>'
            f'<span class="vv">{_esc(s.running_md)} MD / {_esc(s.running_ad)} AD &mdash; '
            f'{running} (broad flag by design)</span></div></div>')


def _maraka_saturn_section(r: DetailedReport) -> str:
    """The classical 'last signal' of a maraka period — RASI half only, strictly the method,
    never a strengthened death signal (this project's own real-outcome research measured none)."""
    if not r.maraka_saturn:
        return ""
    rows = "".join(
        f'<tr><td>{_esc(c.maha)}/{_esc(c.antar)}</td>'
        f'<td>{_outlook_window_label(c.window_start_jd, c.window_end_jd)}</td>'
        f'<td>{_outlook_window_label(c.overlap_start_jd, c.overlap_end_jd)}</td>'
        f'<td>{_esc(_SIGN_NAME[c.sign])}</td>'
        f'<td class="num">'
        f'{_esc(f"{c.score} = {c.score_parts}" if c.score_parts else str(c.score))}</td></tr>'
        for c in r.maraka_saturn)
    return (
        '<h2 class="section" id="maraka-saturn">Maraka &times; Saturn-transit confluence</h2>'
        '<p class="section-sub"><b>In simple terms:</b> Raman names one specific classical '
        'signal for a maraka period &mdash; Ayushkaraka Saturn transiting back over the sign it '
        'occupied at your birth, or its trines, during a maraka-tier Dasha/Bhukti '
        '(HTJAH-II:4846-4849). The windows below are where BOTH conditions line up. This shows '
        'only the RASI half of that signature &mdash; the Navamsa half is not computed here. '
        '&ldquo;Maraka tier&rdquo; is how strong a death-signal the Bhukti&rsquo;s own lords '
        'carry (primary=3, secondary=2, tertiary=1 per lord, summed) &mdash; a higher number '
        'means both the MD and AD lord are more central to the classical maraka set, not a '
        'stronger prediction.</p>'
        '<p class="section-sub"><i>A statement of the method, not a prediction:</i> this '
        'project&rsquo;s own real-outcome validation measured NO death-timing signal from '
        'maraka checks generally. This section exists to show what Raman&rsquo;s textbook '
        'method says, faithfully &mdash; never as a strengthened death signal.</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>maraka bhukti</th>'
        '<th>bhukti window</th><th>confluence window</th><th>sign</th>'
        '<th class="num">maraka tier</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>')


def _health_readout_section(r: DetailedReport) -> str:
    """v17 — the health/vulnerability READ-OUT: a pure re-read of already-computed verdicts,
    caveat always rendered, descriptive idiom only (never a medical statement or prediction)."""
    h = r.health_readout
    if not h.rows:
        return ""
    rows = "".join(
        f'<tr><td><b>{_esc(row.area)}</b></td><td>{_esc(row.verdict)}</td>'
        f'<td>{_esc(row.note)}</td><td>{_esc(row.provenance)}</td></tr>'
        for row in h.rows)
    tier_line = ""
    if h.maraka_tiers:
        tier_txt = ", ".join(f"{_esc(g)} ({_esc(t)})" for g, t in h.maraka_tiers)
        tier_line = (
            f'<p class="section-sub"><b>Maraka tiers</b> (re-read from The maraka scheme): '
            f'{tier_txt} &mdash; <b>22nd drekkana lord</b>: {_esc(h.drekkana22_lord)}, '
            f'<b>64th navamsa lord</b>: {_esc(h.navamsa64_lord)}.</p>')
    period = ("carries a maraka-tier lord" if h.maraka_period_now
              else "carries no maraka-tier lord")
    return (
        '<h2 class="section" id="health-readout">Health &amp; vulnerability read-out</h2>'
        f'{_method_preamble_html("health_readout")}'
        '<p class="section-sub"><b>In simple terms:</b> the health-adjacent verdicts this '
        'report already computed &mdash; the 1st/6th/8th/12th house readings, the Moon and '
        'Mercury karakas, the balarishta screen, the maraka tiers and the longevity band '
        '&mdash; gathered on one page. Every row names the section it re-reads; nothing '
        'here is new.</p>'
        f'<p class="section-sub caveat"><i>{_esc(h.caveat)}</i></p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>indicator</th>'
        '<th>verdict</th><th>detail</th><th>re-read from</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>'
        f'{tier_line}'
        f'<p class="section-sub"><b>Running period</b>: {period} (broad, low-discrimination '
        f'flag by design). <b>Longevity band</b> (re-read from Longevity): '
        f'{_esc(h.longevity_band)}.</p>')


def _rect_confidence_section(r: DetailedReport) -> str:
    """v31 — birth-time sensitivity, measured as a bidirectional minute RANGE per pillar
    (never a fixed pass/fail at one offset, never an invented percentage)."""
    rc = r.rect_confidence
    if rc is None:
        return ""
    def _flips(pl) -> str:
        parts = [f"{off:+d} min &rarr; {_esc(v)}"
                for off, v in filter(None, (pl.flip_minus, pl.flip_plus))]
        return ("; ".join(parts) if parts else
                f"stable beyond &plusmn;{rc.scan_window} min (not tested further)")
    rows = "".join(
        f'<tr><td>{_esc(pl.pillar)}</td><td>{_esc(pl.base_value)}</td>'
        f'<td>-{pl.stable_minus} to +{pl.stable_plus}</td>'
        f'<td>{_flips(pl)}</td></tr>'
        for pl in rc.pillars)
    return (
        '<h2 class="section" id="rect-confidence">Rectification confidence</h2>'
        f'<p class="section-sub"><i>{_esc(rc.frame)}</i></p>'
        f'<p class="section-sub"><b>Verdict</b> &mdash; {_esc(rc.label)}</p>'
        f'<p class="section-sub"><b>Every pillar holds together</b> from '
        f'-{rc.overall_stable_minus} to +{rc.overall_stable_plus} minutes '
        f'({rc.stable_count} of {rc.total_count} pillars never flip inside the full '
        f'&plusmn;{rc.scan_window}-minute scan)</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>pillar</th>'
        '<th>at the stated time</th><th>stable range (minutes)</th><th>flips to</th></tr>'
        f'</thead><tbody>{rows}</tbody></table></div>')


def _decades_section(r: DetailedReport) -> str:
    """v28 — indications per decade; never probabilities."""
    dt = r.decades
    if dt is None:
        return ""
    blocks = []
    for d in dt.decades:
        if not d.inside_window:
            blocks.append(f'<h3>{_esc(d.label)}</h3>'
                          f'<p class="section-sub"><i>{_esc(d.note)}</i></p>')
            continue
        rows = [("Running Mahadashas", _esc(", ".join(d.md_lords) or "-")
                 + (f" (leans: {_esc(', '.join(d.leans))})" if d.leans else ""))]
        if d.areas_favourable:
            rows.append(("Read favourably here", _esc("; ".join(d.areas_favourable))))
        if d.areas_challenged:
            rows.append(("Read as challenged here", _esc("; ".join(d.areas_challenged))))
        if d.yogas_ripening:
            rows.append(("Yogas ripening", _esc("; ".join(d.yogas_ripening))))
        body = "".join(f'<div class="vrow"><span class="vk">{k}</span>'
                       f'<span class="vv">{v}</span></div>' for k, v in rows)
        blocks.append(f'<h3>{_esc(d.label)}</h3><div class="vsec">{body}</div>')
    return ('<h2 class="section" id="decades">Decade indication timeline</h2>'
            f'<p class="section-sub"><i>{_esc(dt.frame)}</i></p>' + "".join(blocks))


def _life_synthesis_section(r: DetailedReport) -> str:
    """v29 — the biography-closing chapter; strict re-read."""
    ls = r.life_synthesis
    if ls is None:
        return ""
    paras = "".join(f'<p><b>{_esc(theme)}.</b> {_esc(para)}</p>'
                    for theme, para in ls.paragraphs)
    return ('<h2 class="section" id="life-synthesis">Full life synthesis</h2>'
            '<p class="section-sub"><b>In simple terms:</b> the report&rsquo;s chapters '
            'read as one biography &mdash; every line a re-read of a section above, '
            'nothing judged anew.</p>'
            f'{paras}<p class="section-sub"><i>{_esc(ls.closing)}</i></p>')


def _psych_section(r: DetailedReport) -> str:
    """v27 — the psychological profile: the mind stack woven, lagna portrait verbatim."""
    ps = r.psych
    if ps is None:
        return ""
    rows = [("The rising sign's portrait (Raman verbatim)",
             f"&ldquo;{_esc(ps.lagna_quote[0])}&rdquo; <i>({_esc(ps.lagna_quote[1])})</i>")]
    if ps.moon_state:
        rows.append(("The mind's significator", _esc(ps.moon_state)))
    for _mm_id, _mm_text, _mm_cite in ps.moon_mind:
        rows.append((f"The Moon's sign (mental disposition) [{_esc(_mm_id)}]",
                     f"{_esc(_mm_text)} <i>({_esc(_mm_cite)})</i>"))
    if ps.mercury_line:
        rows.append(("Mercury (buddhi)", _esc(ps.mercury_line)))
    if ps.deeptadi_moon:
        rows.append(("The Moon's avastha (cross-reference)", _esc(ps.deeptadi_moon)))
    if ps.temperament:
        rows.append(("Temperament of the strongest planet",
                     _esc(ps.temperament) + " (HTJAH-I:6248-6268)"))
    if ps.nature_stamp:
        rows.append(("Nature &amp; appearance stamped by",
                     _esc(ps.nature_stamp) + " (HTJAH-I:3892-3897)"))
    if ps.atmakaraka:
        rows.append(("Atmakaraka", _esc(ps.atmakaraka) + " (the 7-karaka scheme)"))
    body = "".join(f'<div class="vrow"><span class="vk">{k}</span>'
                   f'<span class="vv">{v}</span></div>' for k, v in rows)
    return ('<h2 class="section" id="psych">Psychological profile</h2>'
            f'{_method_preamble_html("psych")}'
            f'<p class="section-sub"><i>{_esc(ps.woven)}</i></p>'
            f'<div class="vsec">{body}</div>')


def _aptitude_section(r: DetailedReport) -> str:
    """v33 — aptitude, intelligence & work style: the three trait axes re-read."""
    ap = r.aptitude
    if ap is None:
        return ""
    rows: list[tuple[str, str]] = []
    if ap.intellect_verdict:
        rows.append(("Intellect (H5, Jupiter karaka)",
                     _esc(ap.intellect_verdict) + " (HTJAH-I:5012)"))
    for rid, text, cite in ap.intellect_fired:
        rows.append((f"Fired intellect combo [{_esc(rid)}]",
                     f"{_esc(text)} <i>({_esc(cite)})</i>"))
    rows.append(("Mercury (buddhi)", _esc(ap.mercury_state)))
    if ap.mercury_house_text:
        rows.append(("Mercury in its house (Raman verbatim)",
                     f"&ldquo;{_esc(ap.mercury_house_text[0])}&rdquo; "
                     f"<i>({_esc(ap.mercury_house_text[1])})</i>"))
    if ap.mercury_sign_text:
        rows.append(("Mercury in its sign (Raman verbatim)",
                     f"&ldquo;{_esc(ap.mercury_sign_text[0])}&rdquo; "
                     f"<i>({_esc(ap.mercury_sign_text[1])})</i>"))
    for rid, text, cite in ap.moon_mind_fired:
        rows.append((f"The Moon's mental disposition [{_esc(rid)}]",
                     f"{_esc(text)} <i>({_esc(cite)})</i>"))
    if ap.jupiter_state:
        rows.append(("Jupiter (intellect karaka)", _esc(ap.jupiter_state)))
    if ap.courage_verdict:
        rows.append(("Courage / initiative (H3)",
                     _esc(ap.courage_verdict) + " (HTJAH-I:3324)"))
    if ap.trade_indication:
        lord, disp, trade = ap.trade_indication
        rows.append(("Navamsa-dispositor trade",
                     f"10th lord {_esc(lord)}, dispositor {_esc(disp)}: {_esc(trade)} "
                     "(HTJAH-II:10249)"))
    if ap.tenth_sign_profile:
        rows.append(("10th-sign profile",
                     f"sign {ap.tenth_sign_profile[0]}: {_esc(ap.tenth_sign_profile[1])} "
                     "(HTJAH-II:10340)"))
    if ap.strongest_affinity:
        rows.append(("Strongest planet's field",
                     f"{_esc(ap.strongest_affinity[0])}: {_esc(ap.strongest_affinity[1])} "
                     "(HTJAH-II:10249)"))
    for key, verdict in ap.mode_split:
        rows.append((f"H10 mode: {_esc(key)}", _esc(verdict)))
    if ap.tenth_lord_state:
        rows.append(("10th lord's condition", _esc(ap.tenth_lord_state)))
    if ap.saturn_state:
        rows.append(("Saturn's condition", _esc(ap.saturn_state)))
    if ap.mars_state:
        rows.append(("Mars's condition", _esc(ap.mars_state)))
    if ap.style_modern:
        from app.raman_saab.planet_biographies import MODERN_BANNER
        rows.append((f"Modern keywords [{_esc(MODERN_BANNER)}]",
                     _esc("; ".join(ap.style_modern))))
    body = "".join(f'<div class="vrow"><span class="vk">{k}</span>'
                   f'<span class="vv">{v}</span></div>' for k, v in rows)
    return ('<h2 class="section" id="aptitude">Aptitude, intelligence &amp; work style</h2>'
            f'{_method_preamble_html("aptitude")}'
            f'<p class="section-sub"><i>{_esc(ap.woven)}</i></p>'
            f'<div class="vsec">{body}</div>')


def _arishta_section(r: DetailedReport) -> str:
    """v22 — Arishta & Bhanga: afflictions AND their doctrinal cancellations."""
    a = r.arishta
    if a is None:
        return ""
    bal = ("applies" if a.balarishta_applies and not a.balarishta_cancelled
           else "CANCELLED" if a.balarishta_cancelled else "does not apply")
    rows = [("Balarishta (HPA-14)",
             bal + (" — " + "; ".join(a.balarishta_reasons)
                    if a.balarishta_reasons else ""))]
    # Wave-2 (2026-08-18, item 5a): the clear case discloses WHAT was screened.
    if not a.balarishta_applies:
        from app.raman_saab.primitives.balarishta import screened_conditions
        rows.append(("Balarishta screen",
                     "screened: " + "; ".join(
                         f"{_esc(label)} ({_esc(cite)})"
                         for label, cite in screened_conditions())
                     + " — none present"))
    rows.append(("Raman's antidotes (verbatim)",
                 f"&ldquo;{_esc(a.antidote_quote)}&rdquo; ({_esc(a.antidote_cite)})"))
    if a.bhangas:
        for p, dig, eff in a.bhangas:
            rows.append(("Bhanga", f"{_esc(p)}: {_esc(dig)} cancelled to effective "
                                   f"{_esc(eff)} (neecha bhanga)"))
    # Wave-2 (item 5d): distinguish the two no-bhanga cases — a debility standing
    # UNCANCELLED vs no debilitated planet at all.
    _uncx = getattr(a, "uncancelled_debilities", ())
    for p in _uncx:
        rows.append(("Bhanga", f"{_esc(p)} is debilitated and NO cancellation "
                               f"operates: the debility stands (no neecha bhanga)"))
    if not a.bhangas and not _uncx:
        rows.append(("Bhanga", "no planet is debilitated in this chart, so no "
                               "cancellation question arises"))
    rows.append(("Kemadruma", _esc(a.kemadruma_note)))
    for pr_line in a.protections:
        rows.append(("Longevity protection", _esc(pr_line)))
    rows.append(("Band", _esc(a.band)))
    rows.append(("Maraka context", _esc(a.maraka_note)))
    body = "".join(f'<div class="vrow"><span class="vk">{k}</span>'
                   f'<span class="vv">{v}</span></div>' for k, v in rows)
    return ('<h2 class="section" id="arishta">Arishta &amp; Bhanga</h2>'
            '<p class="section-sub"><b>In simple terms:</b> the afflictions Raman '
            'screens for and &mdash; equally doctrinal &mdash; the cancellations that '
            'neutralise them. Every row re-reads a computed state.</p>'
            f'<div class="vsec">{body}</div>')


def _gochara_table(r: DetailedReport) -> str:
    if not r.gochara:
        return ""
    rows = ""
    for g in r.gochara:
        av = str(g.bav_bindus) if g.bav_bindus is not None else "&ndash;"
        vedha = _esc(", ".join(g.vedha_by)) if g.vedha_by else "&ndash;"
        net = ("favourable" if g.net_good else "obstructed/adverse")
        # Kakshya micro-transit + bindus/8 proportion (ASP-13) — same fields as the markdown.
        prop = f"{g.bav_proportion:.0%}" if g.bav_proportion is not None else "&ndash;"
        kak = ("&ndash;" if g.kakshya_lord is None else
               f'{_esc(g.kakshya_lord)} '
               f'({"donated" if g.kakshya_favourable else "no bindu"})')
        rows += (f'<tr><td><b>{_esc(g.planet)}</b></td><td>{_esc(_SIGN_NAME[g.sign])}</td>'
                 f'<td class="num">{g.house_from_moon}</td>'
                 f'<td>{"favourable" if g.gochara_good else "adverse"}</td>'
                 f'<td class="num">{av}</td><td class="num">{prop}</td><td>{kak}</td>'
                 f'<td>{vedha}</td>'
                 f'<td><span class="chip chip--{"favourable" if g.net_good else "afflicted"}">'
                 f'{net}</span></td></tr>')
    # Wave-2 (2026-08-18): the synthesis sentences — one deterministic join of each row's
    # own columns, the way Raman narrates a transit; the table above stays in full.
    sentences = "".join(f'<li>{_esc(gochara_synthesis_sentence(g))}</li>' for g in r.gochara)
    return ('<h2 class="section" id="gochara">Current transits (Gochara) with Vedha</h2>'
            '<p class="section-sub">From the natal Moon at the reference date. Raman: transits are '
            'secondary, catalytic &mdash; conclusions rest on Dasa-vichara (HTJAH-II:4679-4687). '
            'The net column applies Vedha: an obstructed transit does not deliver.</p>'
            '<div class="tablewrap"><table class="grid"><thead><tr><th>planet</th><th>sign</th>'
            '<th class="num">from Moon</th><th>classical</th><th class="num">AV</th>'
            '<th class="num">proportion</th><th>Kakshya</th>'
            '<th>Vedha by</th><th>net</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
            '<p class="section-sub"><b>Read as sentences</b> &mdash; the same rows joined the '
            'way Raman narrates a transit (station + support + vedha in one breath); every '
            'clause restates a column above, no new judgment:</p>'
            f'<ul class="tightlist">{sentences}</ul>'
            f'{_gochara_outlook_svg(r)}')


# Duplicated from detailed_report._MONTH_ABBR on purpose to keep this a display-only helper.
_MONTH_ABBR = ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _compact_month(jd: float) -> str:
    """'Mar'24' — a narrow month+year label that fits inside a Gantt bar."""
    import swisseph as swe
    y, m, _d, _h = swe.revjul(jd, swe.GREG_CAL)
    return f"{_MONTH_ABBR[int(m)]}'{int(y) % 100:02d}"


def _gochara_outlook_svg(r: DetailedReport) -> str:
    """A multi-year Gantt-style outlook for Jupiter/Saturn/Rahu/Ketu — the same Gochara scheme
    as the snapshot table above, spread across [ref - window_back, ref + window_forward]. Solid
    bars are classically-benefic windows; fainter bars were more often Vedha-obstructed across
    their span (see `_vedha_word` / GocharaSegment.vedha_sample_fraction for the honesty caveat
    on that estimate's resolution). A data table below the graph repeats every window in plain
    words (not only on hover), since a printed page cannot hover."""
    if not r.gochara_outlook:
        return ""
    import swisseph as swe

    start_jd = r.ref_jd - r.window_back * 365.2425
    end_jd = r.ref_jd + r.window_forward * 365.2425
    span = end_jd - start_jd
    if span <= 0:
        return ""
    planets = [p for p in ("Jupiter", "Saturn", "Rahu", "Ketu") if r.gochara_outlook.get(p)]
    if not planets:
        return ""
    width, ml, mr, mt, mb = 860, 78, 16, 26, 22
    row_h = 52
    height = mt + mb + row_h * len(planets)
    cw = width - ml - mr

    def x_of(jd: float) -> float:
        return ml + (jd - start_jd) / span * cw

    y0 = int(swe.revjul(start_jd, swe.GREG_CAL)[0])
    y1 = int(swe.revjul(end_jd, swe.GREG_CAL)[0]) + 1
    parts: list[str] = []
    for yr in range(y0, y1 + 1):
        for month in (1, 4, 7, 10):                     # quarter ticks — finer than year alone
            gx = x_of(swe.julday(yr, month, 1, 0.0, swe.GREG_CAL))
            if gx < ml or gx > width - mr:
                continue
            if month == 1:
                parts.append(f'<line x1="{gx:.1f}" y1="{mt}" x2="{gx:.1f}" y2="{height - mb}" '
                             f'style="stroke:var(--rule)" stroke-width="1"/>')
                parts.append(f'<text x="{gx:.1f}" y="{height - mb + 13}" font-size="9" '
                             f'text-anchor="middle" style="fill:var(--ink-soft)">{yr}</text>')
            else:
                parts.append(f'<line x1="{gx:.1f}" y1="{height - mb - 5}" x2="{gx:.1f}" '
                             f'y2="{height - mb}" style="stroke:var(--rule)" stroke-width="1" '
                             f'opacity="0.55"/>')

    good_rows: list[tuple[str, "object"]] = []           # (planet, seg) for the table below
    for i, planet in enumerate(planets):
        ry = mt + i * row_h
        cy = ry + 17
        parts.append(f'<text x="{ml - 8}" y="{cy + 3:.1f}" font-size="11" text-anchor="end" '
                     f'style="fill:var(--ink)">{_esc(planet)}</text>')
        parts.append(f'<line x1="{ml}" y1="{cy:.1f}" x2="{width - mr}" y2="{cy:.1f}" '
                     f'style="stroke:var(--rule)" stroke-width="1"/>')
        for seg in r.gochara_outlook[planet]:
            if not seg.gochara_good or (seg.end_jd - seg.start_jd) < 25:
                continue
            good_rows.append((planet, seg))
            x0, x1 = max(x_of(seg.start_jd), ml), min(x_of(seg.end_jd), width - mr)
            if x1 <= x0:
                continue
            bar_w = x1 - x0
            opacity = max(0.32, 0.92 - 0.6 * seg.vedha_sample_fraction)
            bav = f"{seg.bav_bindus} bindus" if seg.bav_bindus is not None else "n/a"
            title = (f"{planet} ({_PLANET_THEME[planet]}) in {_SIGN_NAME[seg.sign]}: "
                    f"{_outlook_window_label(seg.start_jd, seg.end_jd)} — AV "
                    f"support {bav}; Vedha {_vedha_word(seg.vedha_sample_fraction)}")
            parts.append(
                f'<rect class="gochara-bar" x="{x0:.1f}" y="{ry + 6:.1f}" '
                f'width="{bar_w:.1f}" height="26" rx="4" '
                f'style="fill:var(--favourable);fill-opacity:{opacity:.2f}">'
                f'<title>{_esc(title)}</title></rect>')
            if bar_w >= 56:                              # room for a compact month label
                cm0, cm1 = _compact_month(seg.start_jd), _compact_month(seg.end_jd)
                label = cm0 if cm0 == cm1 else f"{cm0}–{cm1}"
                parts.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{ry + 44:.1f}" font-size="8.5" '
                             f'text-anchor="middle" style="fill:var(--ink-soft)">{label}</text>')

    today_x = x_of(r.ref_jd)
    parts.append(
        f'<line x1="{today_x:.1f}" y1="{mt - 8}" x2="{today_x:.1f}" y2="{height - mb}" '
        f'style="stroke:var(--warn)" stroke-width="1.5" stroke-dasharray="3,2"/>'
        f'<text x="{today_x:.1f}" y="{mt - 11}" font-size="9" text-anchor="middle" '
        f'style="fill:var(--warn)">today</text>')

    good_rows.sort(key=lambda pw: pw[1].start_jd)
    table_rows = "".join(
        f'<tr><td><b>{_esc(planet)}</b></td>'
        f'<td>{_outlook_window_label(seg.start_jd, seg.end_jd)}</td>'
        f'<td>{_esc(_PLANET_THEME[planet])}</td>'
        f'<td>{_esc(_outlook_strength_word(seg.bav_bindus))}</td>'
        f'<td>{_esc(_vedha_word(seg.vedha_sample_fraction).split(" ")[0])}</td></tr>'
        for planet, seg in good_rows)

    return (
        '<div id="gochara-outlook" class="gochara-outlook">'
        '<h3>Favourable transit windows, mapped over time</h3>'
        '<p class="section-sub"><b>In simple terms:</b> these are the months ahead (and behind) '
        'when Jupiter, Saturn, Rahu or Ketu sits in a position that classically supports the side '
        'of life that planet governs (see "what it supports" below). A solid bar is well backed '
        'and rarely blocked; a faded bar looks supportive on paper but was often blunted by '
        'another planet&rsquo;s position across that stretch (hover a bar, or see the table, for '
        'exact months). Only Jupiter, Saturn, Rahu and Ketu are graphed &mdash; they change sign '
        'slowly enough to read at this scale; Mars and the faster grahas stay in the snapshot '
        'table above. Per Raman, a transit is always secondary to the Dasha (HTJAH-II:4679) '
        '&mdash; read a window here as <i>added</i> support during whatever your running period '
        '(Life-narrative, below) already indicates, not on its own.</p>'
        f'<svg viewBox="0 0 {width} {height}" width="100%" style="max-width:{width}px" '
        f'role="img" aria-label="Gochara favourability over time">'
        f'{"".join(parts)}</svg>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>planet</th><th>window</th>'
        '<th>what it supports</th><th>strength</th><th>interference</th></tr></thead>'
        f'<tbody>{table_rows}</tbody></table></div></div>')


def _dasha_transit_section(r: DetailedReport) -> str:
    """The Dasha x Transit confluence: stretches where the running MD/AD lord is also, at the
    same time, in one of its own favourable Gochara windows — a genuine cross-reference of the
    Life-narrative and Gochara sections above, not a new judgment (see ConfluenceWindow's
    docstring)."""
    if not r.dasha_transit:
        return ""
    rows = "".join(
        f'<tr><td><b>{_esc(c.role)}</b></td><td>{_esc(c.planet)}</td>'
        f'<td>{_outlook_window_label(c.overlap_start_jd, c.overlap_end_jd)}</td>'
        f'<td>{_esc(_PLANET_THEME[c.planet])}</td>'
        f'<td>{_esc(_outlook_strength_word(c.bav_bindus))}</td>'
        f'<td>{_esc(_vedha_word(c.vedha_sample_fraction).split(" ")[0])}</td></tr>'
        for c in r.dasha_transit)
    return (
        '<h2 class="section" id="dasha-transit">Dasha &times; Transit confluence</h2>'
        '<p class="section-sub"><b>In simple terms:</b> these are the specific stretches where '
        'your running Mahadasha (MD) or Antardasha (AD) lord is <i>also</i>, at the same time, '
        'transiting favourably in the sky. Raman treats a transit as secondary to the Dasha '
        '(HTJAH-II:4679) &mdash; "a good transit only delivers what the running period already '
        'permits" &mdash; so a confluence below is the clearest confirmation this report can '
        'offer: the very planet already ruling this stretch of your life is also well placed by '
        'transit. Only Jupiter, Saturn, Rahu and Ketu are tracked long-range (the same four the '
        'outlook above covers); a period led by the Sun, Moon, Mars, Mercury or Venus simply has '
        'no row here &mdash; a gap in what this cross-check computes, not a judgment that the '
        'period lacks support.</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>period</th><th>planet</th>'
        '<th>overlap</th><th>what it supports</th><th>strength</th><th>interference</th></tr>'
        f'</thead><tbody>{rows}</tbody></table></div>'
        f'{_dasha_transit_adverse_section(r)}')


def _dasha_transit_adverse_section(r: DetailedReport) -> str:
    """Wave-2 (2026-08-18): the ADVERSE mirror of the confluence table — the favourable
    builder was one-sided by construction (`if not seg.gochara_good: continue`); Raman's
    blending doctrine reads obstruction too (HPA-34:369-381). The favourable table above is
    untouched; this renders below it, method-only, same coarse-sampling honesty."""
    if not r.dasha_transit_adverse:
        return ""
    rows = ""
    for c in r.dasha_transit_adverse:
        mit = (f"{c.bav_bindus}/8 of the evil neutralised" if c.bav_bindus is not None
               else "&ndash; (node: no classical Ashtakavarga)"
               if c.planet in ("Rahu", "Ketu") else "&ndash; (not computed)")
        rows += (f'<tr><td><b>{_esc(c.role)}</b></td><td>{_esc(c.planet)}</td>'
                 f'<td>{_outlook_window_label(c.overlap_start_jd, c.overlap_end_jd)}</td>'
                 f'<td>{_esc(_PLANET_THEME[c.planet])}</td><td>{mit}</td>'
                 f'<td>&ndash;</td></tr>')
    return (
        '<h3>Adverse dasha &times; transit confluence</h3>'
        '<p class="section-sub"><b>In simple terms:</b> the mirror of the table above &mdash; '
        'the stretches where a running MD or AD lord is, at the same time, transiting a '
        'station from your Moon that the classical Gochara scheme counts AGAINST that planet. '
        'Raman&rsquo;s blending doctrine weighs obstruction as well as reinforcement '
        '(&ldquo;blended with those of Gochara and Ashtakavarga, together with Vedha or '
        'obstructing forces&rdquo;, HPA-34:369-381) &mdash; the two tables are the two halves '
        'of one method statement: reduced transit support during what the period already '
        'indicates, never a stand-alone prediction. Mitigation applies Raman&rsquo;s own '
        'proportion law (bindus neutralise the evil to that extent, ASP-13:416); Vedha is '
        'defined for favourable transits only, so that column reads &ndash; here (not '
        'computed, not zero). Same coverage and sampling honesty as above: only the four '
        'long-range movers contribute rows, at the outlook&rsquo;s coarse ~week sampling '
        '&mdash; method windows, not exact dates.</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>period</th><th>planet</th>'
        '<th>overlap</th><th>what it concerns</th><th>mitigation (own AV bindus)</th>'
        f'<th>interference</th></tr></thead><tbody>{rows}</tbody></table></div>')


def _soul_section(r: DetailedReport) -> str:
    from app.raman_saab.detailed_report import _clean_box
    body = _varga_card("Soul & destiny (extended Jaimini reading)",
                       _clean_box(render_soul_text(r)))
    return f'<div id="soul">{body}</div>'


def render_soul_text(r: DetailedReport) -> str:
    from app.raman_saab import render_soul
    return render_soul.to_text(r.soul)


def _pitru_section(r: DetailedReport) -> str:
    from app.raman_saab import render_pitru
    from app.raman_saab.detailed_report import _clean_box
    banner = ('<div class="provenance-banner">Provenance notice: only the children verdict is '
              'Raman (HTJAH-I:5018). The curse-yoga screens are CLASSICAL_NONCITABLE '
              '(BPHS / Prasna Marga) &mdash; reported for completeness, outside Raman&rsquo;s '
              'canon, and carrying no demonstrated predictive weight.</div>')
    body = _varga_card("Pitru dosha screen", _clean_box(render_pitru.to_text(r.pitru)))
    return f'<div id="pitru">{banner}{body}</div>'


_SYN_BAND = {
    "raman": ("Raman's own combination doctrine", None, "vcore"),
    "classical": ("Classical corroboration",
                  "Provenance notice: CLASSICAL_NONCITABLE (Laghu Parashari, BPHS, Uttara "
                  "Kalamrita, Saravali) — outside Raman's citable canon; where they conflict "
                  "with Raman, Raman wins.", "voverlay"),
    "av": ("Ashtakavarga combinations",
           "Raman's own caveat governs this band: “Ashtakavarga method is equally "
           "important. But, it does not seem to be quite reliable” (HTJAH-II:4453-4456). "
           "These never override an insight from the bands above.", "voverlay"),
}


def _synthesis_section(r: DetailedReport) -> str:
    """The integrated-insights section: fired cross-feature rules, banded by provenance."""
    from app.raman_saab.detailed_report import descriptive_rules
    parts = ['<h2 class="section" id="synthesis">Integrated insights</h2>'
             '<p class="section-sub">Where the report&rsquo;s sections meet: encoded '
             'combination doctrine connecting Shadbala, yogas, dashas, transits, Ashtakavarga '
             'and the houses. Each insight leads with a plain-language reading, backed by the '
             'exact text it draws from &mdash; not a prediction.</p>'
             '<p class="section-sub">How to read several strength measures at once (the '
             'general form of the House strength cross-check&rsquo;s own finding above): '
             'Raman&rsquo;s system tracks a house/planet/period along SEVERAL INDEPENDENT '
             'axes, not one score. The VERDICT (favourable/afflicted) comes from aspect, '
             'lordship and association &mdash; a direction (HTJAH-I:468-478 lists a '
             'house&rsquo;s strength and its aspects/qualities as separate considerations). '
             'Bhava Bala/Shadbala is mostly a MAGNITUDE &mdash; how fully results are enjoyed, '
             'not whether they are good (GBB-9:32-34). Avastha is a STATE the planet acts '
             'from (Deeptadi avasthas, HPA Ch.7). Ishta/Kashta is a period&rsquo;s own '
             'good-vs-hard TENDENCY (GBB-10:134). Ashtakavarga bindus are a separate, '
             'lower-reliability CORROBORATING tier by Raman&rsquo;s own admission '
             '(&ldquo;it does not seem to be quite reliable,&rdquo; HTJAH-II:4453-4456). '
             'These axes are not meant to always agree &mdash; a planet can be strong yet in '
             'a hard state, or favourable yet thin &mdash; and reading two of them apart is '
             'not a contradiction to resolve.</p>']
    cur = None
    for ins in r.insights:
        if ins.rule.band != cur:
            cur = ins.rule.band
            head, banner, _tint = _SYN_BAND[cur]
            parts.append(f'<h3 class="md-head">{_esc(head)}</h3>')
            if banner:
                parts.append(f'<div class="provenance-banner">{_esc(banner)}</div>')
        cite = (f'<code>{_esc(ins.rule.source.work)}:{ins.rule.source.line}</code>'
                if ins.rule.source else
                f'<span class="tag tag--univ">{_esc(ins.rule.provenance)}</span>')
        parts.append(
            f'<div class="insight"><div class="insight-head"><b>{_esc(ins.rule.name)}</b> '
            f'{cite}</div>'
            f'<p class="doctrine">{_esc(ins.rule.simple_meaning)}</p>'
            f'<div class="plain"><b>This chart:</b> {_esc(ins.detail)}</div>'
            f'<div class="source-quote"><b>The text says:</b> '
            f'&ldquo;{_esc(ins.rule.doctrine)}&rdquo;</div>'
            f'<div class="insight-links">links: {_esc(" x ".join(ins.rule.links))}</div></div>')
    on_record = descriptive_rules()
    if on_record:
        items = "".join(
            f'<li><b>{_esc(d.name)}</b>'
            + (f' <code>{_esc(d.source.work)}:{d.source.line}</code>' if d.source else "")
            + f' &mdash; {_esc(d.doctrine)}</li>' for d in on_record)
        parts.append('<details class="vnotes"><summary>further combination doctrine on record '
                     f'(not yet computed)</summary><ul>{items}</ul></details>')
    parts.append('<p class="section-sub">Excluded by project locks (recorded, not encoded): '
                 'Argala rasi-dasha grading; the KP sub-lord chain; nodal Vedha. No combination '
                 'was invented beyond what the texts state.</p>')
    return "".join(parts)


def _glossary() -> str:
    items = "".join(f'<dt>{_esc(k)}</dt><dd>{_esc(v)}</dd>' for k, v in GLOSSARY.items())
    return ('<details class="glossary" id="glossary"><summary>Glossary &mdash; the technical '
            'terms in plain language</summary>'
            f'<dl>{items}</dl></details>')


def _plain_reading_section(r: DetailedReport) -> str:
    """'Your Reading' — the report's one genuinely plain-English section, rendered first."""
    p = r.plain_reading
    paras = "".join(f'<p><b>{_esc(theme)}.</b> {_esc(para)}</p>'
                    for theme, para in p.life_paragraphs)
    return (
        '<section class="plain-reading" id="plain-reading">'
        f'<p class="pr-opening">{_esc(p.opening)}</p>'
        f'{paras}'
        f'<p>{_esc(p.now)}</p>'
        f'<p>{_esc(p.notable)}</p>'
        + ("" if not p.reconciliations else
           '<p><b>Where readings pull in different directions</b> (both poles shown; the '
           'reconciling rule is in How to read this report):</p><ul>'
           + "".join(f'<li>{_esc(rec)}</li>' for rec in p.reconciliations) + '</ul>')
        + f'<p class="pr-closing">{_esc(p.closing)}</p>'
        '</section>')


def _nichod_section(r: DetailedReport) -> str:
    """The capstone: the report's whole distilled into one deep-level read. Nothing here is a
    new judgment — see Nichod's docstring in detailed_report.py."""
    n = r.nichod
    rows = [("Identity", n.identity), ("Strength profile", n.strength_profile),
            ("Longevity", n.longevity), ("Yogas", n.yogas), ("What stands out", n.stands_out),
            ("The twelve matters", n.matters_tally), ("Running now", n.current_period),
            ("Live transits", n.live_transits)]
    if n.spotlight:
        rows.append(("Cross-feature spotlight", n.spotlight))
    if n.turning_points:
        rows.append(("Turning points (a timing lens, not an event)",
                     "; ".join(f"{when}: {what}" for when, what in n.turning_points)))
    if n.forward_horizon:
        rows.append(("Forward horizon (a period indication, not an event)",
                     n.forward_horizon))
    ingredients = "".join(
        f'<div class="vrow"><span class="vk">{_esc(k)}</span><span class="vv">{_esc(v)}</span>'
        f'</div>' for k, v in rows)
    caution_html = (f'<div class="split-note split-note--warn">{_esc(n.caution)}</div>'
                   if n.caution else "")
    return (
        '<h2 class="section" id="nichod">Nichod</h2>'
        '<p class="section-sub">The distilled essence: every section above, squeezed into one. '
        'Nothing here is a new judgment &mdash; each clause selects, counts, or quotes what the '
        'report already showed. Not a prediction.</p>'
        f'<blockquote class="nichod-essence">{_esc(n.essence)}</blockquote>'
        f'{caution_html}'
        '<div class="vsec vcore"><div class="vsec-label">Ingredients</div>'
        f'{ingredients}</div>')


def _timeline(r: DetailedReport) -> str:
    """Windowed MD -> AD narrative graded per HTJAH-I:1592-1640: houses both lords influence are
    par-excellence when the AD lord is associated with the MD lord, else ordinary; a house only one
    lord influences is limited. Current AD marked."""
    running_md = next((tp.period.maha for tp in r.timeline.periods
                       if tp.period.start_jd <= r.ref_jd < tp.period.end_jd), None)
    # Wave-2 (2026-08-18): the influence-basis table (role-preserving timer_roles, pinned
    # equal to timer_set) — each chip's tooltip now DERIVES the tier instead of asserting
    # it: "MD owns+karaka; AD aspects lord" (HTJAH-I:1586-1596).
    _basis_table = influence_basis_table(r.chart)

    def _chip_basis(a) -> str:
        bits: list[str] = []
        if a.md_activates:
            bits.append(f"MD {influence_basis(_basis_table, a.house, a.md_lord)}".rstrip())
        if a.antar_activates and a.antar_lord is not None:
            bits.append(
                f"AD {influence_basis(_basis_table, a.house, a.antar_lord)}".rstrip())
        return "; ".join(bits)
    # count the bhuktis per MD so the accordion summary is informative while collapsed
    spans: dict[str, list[float]] = {}
    for tp in r.timeline.periods:
        spans.setdefault(tp.period.maha, [tp.period.start_jd, tp.period.end_jd])
        spans[tp.period.maha][1] = tp.period.end_jd
    out: list[str] = []
    cur: str | None = None
    for tp in r.timeline.periods:
        rows, maha, antar = tp.activated, tp.period.maha, tp.period.antar
        if maha != cur:
            if cur is not None:
                out.append("</ol></details>")
            cur = maha
            lo, hi = spans[cur]
            is_now = cur == running_md
            out.append(
                f'<details class="md-group"{" open" if is_now else ""}>'
                f'<summary class="md-head">{_esc(cur)} Mahadasha'
                f'<span class="period-dates">{_jd_to_date(lo)} &ndash; {_jd_to_date(hi)}</span>'
                + ('<span class="now-badge">running</span>' if is_now else "")
                + f'</summary><ol class="timeline">')
        associated, buckets = graded_buckets(tp, r.chart)   # ONE grading implementation
        assoc = ("its own bhukti" if antar == maha
                 else f'AD <b>{"is" if associated else "is not"}</b> associated with MD')
        blocks = f'<div class="assoc-note">{assoc}</div>'
        # Wave-1 (2026-08-17): the lord_quality delivery tags — computed on every activation
        # row (HTJAH-II:10004-10008) but previously dropped by this renderer.
        if rows:
            q0 = rows[0]
            dlv = f"MD {maha} delivers {q0.md_quality.tag}"
            if antar is not None and antar != maha and q0.antar_quality is not None:
                dlv += f"; AD {antar} delivers {q0.antar_quality.tag}"
            blocks += f'<div class="assoc-note">{_esc(dlv)}</div>'
        _TITLE = {"limited": "bhukti lord only", "feeble": "MD lord only",
                  "par excellence": "both lords, AD associated with MD",
                  "ordinary": "both lords, not associated"}
        for tier, items in buckets.items():
            if not items:
                continue
            dim = " lim" if tier in ("limited", "feeble") else ""
            chips = "".join(_house_chip(a, ring=(tier == "par excellence"),
                                        basis=_chip_basis(a)) for a in items)
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
        out.append("</ol></details>")
    return "".join(out)


def _pratyantar_block(r: DetailedReport) -> str:
    """Wave-1 (2026-08-17): the CURRENT bhukti's nine Pratyantardashas, dated — the third
    Vimshottari level Raman names as result-carrying (HTJAH-II:668-702). Same data as the
    markdown block; running pratyantar marked."""
    if not r.pratyantar_now:
        return ""
    items = ""
    for pr_ in r.pratyantar_now:
        now = (' <span class="now-badge">now</span>'
               if pr_.start_jd <= r.ref_jd < pr_.end_jd else "")
        items += (f'<li>{_esc(pr_.maha)} MD / {_esc(pr_.antar)} AD / '
                  f'<b>{_esc(pr_.pratyantar)} PD</b> '
                  f'({_jd_to_date(pr_.start_jd)} &ndash; {_jd_to_date(pr_.end_jd)}){now}</li>')
    return ('<h3>Pratyantardasha drill-down (current bhukti)</h3>'
            '<p class="section-sub">The third level of the Vimshottari hierarchy, for the '
            'bhukti running now only &mdash; the same proportional lord-years/120 split one '
            'level down. Raman names all three levels as carriers of a house&rsquo;s results: '
            '&ldquo;as lords of the Dasas (main-periods), as lords of Bhuktis (Sub-periods) or '
            'as lords of the Antaras&rdquo; (HTJAH-II:668-702).</p>'
            f'<ul class="tightlist">{items}</ul>')


def _chara_sequence_block(r: DetailedReport) -> str:
    """Wave-1 (2026-08-17): the Chara dasha sequence, dated by plain JD arithmetic from birth
    (KN Rao convention as encoded), running sign marked — the Chart signature chip names the
    sign; this dates the whole script."""
    if not r.chara_sequence:
        return ""
    items = ""
    for cs in r.chara_sequence:
        now = ' <span class="now-badge">now</span>' if cs.current else ""
        items += (f'<li>{_esc(_SIGN_NAME[cs.sign])} &mdash; {cs.years}y '
                  f'({_jd_to_date(cs.start_jd)} &ndash; {_jd_to_date(cs.end_jd)}){now}</li>')
    return ('<h3>Chara dasha (Jaimini) &mdash; dated sequence</h3>'
            '<p class="section-sub">The parallel sign-based dasha (see glossary). Dates are '
            'plain JD arithmetic from birth (period years &times; 365.2425 days) over the '
            'KN Rao sequence already encoded; the 12-sign cycle repeats. No result judgment '
            'attaches here &mdash; matters are read from Vimshottari above.</p>'
            f'<ul class="tightlist">{items}</ul>')


def _adverse_windows_table(r: DetailedReport) -> str:
    """Wave-1 (2026-08-17): the classically-adverse Gochara windows the outlook always
    computed — the mirror of the favourable table, honestly labeled (mitigation by Raman's
    bindus/8 proportion law, ASP-13:416; Vedha undefined for adverse spans)."""
    bad = adverse_transit_windows(r)
    if not bad:
        return ""
    rows = ""
    for planet, seg, bav in bad:
        mit = (f"{bav}/8 of the evil neutralised" if bav is not None
               else "&ndash; (node: no classical Ashtakavarga)")
        rows += (f'<tr><td><b>{_esc(planet)}</b></td>'
                 f'<td>{_outlook_window_label(seg.start_jd, seg.end_jd)}</td>'
                 f'<td>{_esc(_PLANET_THEME[planet])}</td><td>{mit}</td>'
                 f'<td>&ndash;</td></tr>')
    return ('<div class="gochara-outlook"><h3>Adverse transit windows</h3>'
            '<p class="section-sub">The mirror of the favourable table above &mdash; the same '
            'computation always produced these windows; only the favourable half was shown '
            'before. &ldquo;What it concerns&rdquo; is the life-area that planet governs, here '
            'classically unsupported; &ldquo;mitigation&rdquo; applies Raman&rsquo;s own '
            'proportion law (bindus in the transited sign neutralise the evil to that extent, '
            'ASP-13:416); Vedha (interference) is defined for favourable transits only, so it '
            'reads &ndash; here (not computed, not zero). Per Raman a transit stays secondary '
            'to the Dasha (HTJAH-II:4679).</p>'
            '<div class="tablewrap"><table class="grid"><thead><tr><th>planet</th>'
            '<th>window</th><th>what it concerns</th><th>mitigation (own AV bindus)</th>'
            '<th>interference</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div></div>')


def _sade_sati_strip(r: DetailedReport) -> str:
    """Wave-1 (2026-08-17): the dated Sade-Sati phase spans (Saturn in the 12th/1st/2nd from
    the natal Moon), method-only — no Sade-Sati x Moon result doctrine is on record, so the
    strip carries dates (plain gochara arithmetic), never an intensity reading."""
    if not r.sade_sati_phases:
        return ""
    items = ""
    for ph in r.sade_sati_phases:
        now = ' <span class="now-badge">now</span>' if ph.current else ""
        items += (f'<li><b>{_esc(ph.phase)}</b> &mdash; Saturn in '
                  f'{_esc(_SIGN_NAME[ph.sign])}: '
                  f'{_outlook_window_label(ph.start_jd, ph.end_jd)}{now}</li>')
    return ('<div class="gochara-outlook">'
            '<h3>Sade-Sati phase windows (Saturn from the natal Moon)</h3>'
            '<p class="section-sub">Saturn&rsquo;s ~7.5-year passage across the 12th, 1st and '
            '2nd signs from the natal Moon &mdash; the episode nearest the reference date, '
            'current position marked. <b>Method note (dates only):</b> no Sade-Sati &times; '
            'Moon result doctrine is on record in the encoded corpus, so no intensity or '
            'result reading is offered &mdash; the dates are plain gochara arithmetic '
            '(transiting Saturn&rsquo;s sign against the natal Moon sign), at the '
            'outlook&rsquo;s ~week sampling resolution.</p>'
            f'<ul class="tightlist">{items}</ul></div>')


def _ishta_kashta_section(r: DetailedReport) -> str:
    """The SAME windowed MD/AD timeline as _timeline() above, painted with each lord's Ishta/
    Kashta lean (GBB-10:134) — a colour-strip companion, not a new timeline."""
    if not r.ishta_kashta:
        return ""
    _LEAN_CHIP = {"good": "favourable", "hard": "afflicted", "balanced": "mixed"}
    rows = "".join(
        f'<tr><td>{_esc(ik.maha)}</td>'
        f'<td><span class="chip chip--{_LEAN_CHIP.get(ik.maha_lean, "mixed")}">'
        f'{_esc(ik.maha_lean or "no data")}</span></td>'
        f'<td>{_esc(ik.antar or ik.maha)}</td>'
        f'<td><span class="chip chip--{_LEAN_CHIP.get(ik.antar_lean, "mixed")}">'
        f'{_esc(ik.antar_lean or "no data")}</span></td>'
        f'<td>{_outlook_window_label(ik.start_jd, ik.end_jd)}</td>'
        f'<td>{_esc(ik.prevails or "")}</td></tr>'
        for ik in r.ishta_kashta)
    return (
        '<h2 class="section" id="ishta-kashta">Ishta &amp; Kashta outlook</h2>'
        '<p class="section-sub"><b>In simple terms:</b> a planet with more Ishta Phala (its own '
        '&ldquo;good tendency&rdquo;) inclines to give good results in its Dasha or Bhukti; '
        'more Kashta Phala (&ldquo;hard tendency&rdquo;) inclines to harder ones (GBB-10:134). '
        'This paints that SAME lean across every period in the Life-narrative timeline above, '
        'not just the one running now. Where a bhukti&rsquo;s own lord is stronger (by '
        'Shadbala) than the Mahadasha lord, no general rule is stated for whose character wins '
        '&mdash; so only the MD-predominates direction is shown (GBB-10:145-152).</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>MD</th><th>MD lean</th>'
        '<th>AD</th><th>AD lean</th><th>window</th><th>notes</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>')


def _dasa_kakshya_section(r: DetailedReport) -> str:
    if not r.dasa_kakshya:
        return ""
    rows = "".join(
        f'<tr><td><b>{_esc(k.maha)}</b></td><td>{_esc(k.ruler)}</td>'
        f'<td>{_esc(_outlook_window_label(k.start_jd, k.end_jd))}</td>'
        f'<td>{"yes" if k.donated else "no"}</td><td>{_esc(k.reading)}</td></tr>'
        for k in r.dasa_kakshya)
    return ('<h2 class="section" id="dasa-kakshya">Dasha Kakshya intervals</h2>'
            '<p class="section-sub">Each Mahadasha split into 8 equal parts ruled in Kakshya order '
            '(ASP-12:174-182); a part whose ruler donated a bindu to the Dasha lord&rsquo;s natal sign '
            'inclines favourable, an undonated part runs adverse (ASP-12:211-214) unless relieved '
            'by the ruler&rsquo;s own signs (ASP-12:215-219). A timing lens, never a verdict.</p>'
            '<div class="tablewrap"><table class="grid"><thead><tr><th>Mahadasha</th>'
            '<th>interval ruler</th><th>window</th><th>donated</th><th>reading</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


def _md_condition_section(r: DetailedReport) -> str:
    """The full-timeline version of SYN_R4's current-MD-only strength/vargottama check —
    painted across every Mahadasha run in the window, one row each."""
    if not r.md_condition:
        return ""
    rows = "".join(
        f'<tr><td>{_esc(c.maha)}</td>'
        f'<td>{_outlook_window_label(c.start_jd, c.end_jd)}</td>'
        f'<td>{"strong" if c.strong else "weak" if c.strong is False else "unknown"}</td>'
        f'<td>{"yes" if c.vargottama else "no"}</td>'
        f'<td>{_esc(_SIGN_NAME[c.navamsa_sign]) if c.navamsa_sign else "n/a"}</td>'
        f'<td>{"yes" if c.at_maximum else "no"}</td></tr>'
        for c in r.md_condition)
    return (
        '<h2 class="section" id="md-condition">MD-lord condition outlook</h2>'
        '<p class="section-sub"><b>In simple terms:</b> a Dasha delivers in proportion to how '
        'well-placed its own ruling planet actually is &mdash; its strength, and its Navamsa '
        'disposition &mdash; reaching its stated maximum only when strong in BOTH the main '
        'chart and the Navamsa (HPA-24:51-86). This is the SAME check the Life-narrative '
        'timeline above already runs for whichever Mahadasha is current, painted onto every '
        'Mahadasha in the window &mdash; Shadbala strength, Vargottama and Navamsa are all '
        'fixed at birth, so this is a lookup, not a new judgment.</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>Mahadasha</th><th>window</th>'
        '<th>Shadbala</th><th>vargottama</th><th>navamsa</th><th>at maximum</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>')


def _av_dasha_seat_section(r: DetailedReport) -> str:
    """The MD lord graded by his own Ashtakavarga bindus, painted across the whole timeline —
    AV-tier, shown last among the Life-narrative companions under Raman's own caveat."""
    if not r.av_dasha_seats:
        return ""
    rows = "".join(
        f'<tr><td>{_esc(a.maha)}</td>'
        f'<td>{_outlook_window_label(a.start_jd, a.end_jd)}</td>'
        f'<td>{_esc(_SIGN_NAME[a.sign])}</td>'
        f'<td class="num">{a.bindus if a.bindus is not None else "n/a"}</td>'
        f'<td>{_esc(a.read)}</td></tr>'
        for a in r.av_dasha_seats)
    return (
        '<h2 class="section" id="av-dasha-seat">AV dasha-seat outlook</h2>'
        '<p class="section-sub"><i>Raman&rsquo;s own caveat governs this section:</i> '
        '&ldquo;Ashtakavarga method is equally important. But, it does not seem to be quite '
        'reliable&rdquo; (HTJAH-II:4453-4456). This classical method never overrides the '
        'Raman-band readings elsewhere in this report &mdash; it is shown last among the '
        'Life-narrative companions for that reason.</p>'
        '<p class="section-sub"><b>In simple terms:</b> a Dasha&rsquo;s lord can also be '
        'graded by how many Ashtakavarga bindus he holds in his OWN natal sign &mdash; 5 or '
        'more reads auspicious, 3 or fewer adverse, exactly 4 mixed (Patel ch015:996-1034). '
        'Painted across every Mahadasha in the window; bindus are fixed at birth, so this is a '
        'lookup, not a new judgment.</p>'
        '<div class="tablewrap"><table class="grid"><thead><tr><th>Mahadasha</th><th>window</th>'
        '<th>sign</th><th class="num">bindus</th><th>reading</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>')


def _life_chapters_section(r: DetailedReport) -> str:
    """One woven prose chapter per Mahadasha run (v15) — the Napoleon-narration shape
    (HTJAH-I:15950-15999) merging the Life-narrative companions; natal factors first,
    transits last (HTJAH-I:8410-8411)."""
    if not r.life_chapters.chapters:
        return ""
    blocks = []
    for ch in r.life_chapters.chapters:
        now_tag = " &mdash; now" if ch.is_current else ""
        blocks.append(
            f'<h3 class="md-head">{_esc(ch.maha)} Mahadasha '
            f'({_outlook_window_label(ch.start_jd, ch.end_jd)}){now_tag}</h3>'
            f'<p class="doctrine">{_esc(ch.narrative)}</p>')
    return (
        '<h2 class="section" id="life-chapters">Life-chapters</h2>'
        '<p class="section-sub"><b>In simple terms:</b> the Life-narrative above and its three '
        'companion tables (Ishta/Kashta, MD-lord condition, AV dasha-seat) each paint ONE lens '
        'across the same years. This section reads them TOGETHER, one chapter per Mahadasha '
        '&mdash; the way Raman himself narrates a nativity (his Chart No. 203 reads each dasha '
        'from yoga + lord condition + house placement + directional influence in one '
        'paragraph, HTJAH-I:15950-15999), and the way his blending doctrine demands: '
        '&ldquo;astrological predictions can be accurate when the influences of birth chart '
        'are blended with those of Gochara and Ashtakavarga, together with Vedha or '
        'obstructing forces&rdquo; (HPA-34:369-381; Vedha is not re-narrated per chapter '
        '&mdash; it is applied in the Gochara table and sampled as interference in the Dasha '
        'x Transit confluence table). Nothing here is a new judgment &mdash; every clause '
        're-reads a row already shown in the sections above, and chapter spans are clipped to '
        'the report&rsquo;s display window (a Mahadasha may begin before or continue past its '
        'shown dates). Within each chapter the natal factors come FIRST and transits LAST: '
        '&ldquo;primary importance must be given to the natal positions and Dasha and only '
        'secondary consideration to transiting planets&rdquo; (HTJAH-I:8410-8411; '
        'HTJAH-II:4679-4687 repeats it &mdash; transits are secondary, catalytic, conclusions '
        'rest on Dasa-vichara). As everywhere in this report: how the method reads this '
        'chart, not a prediction.</p>'
        + "".join(blocks))


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
    # Raman's first glance (2026-08-18 report-critique, append-only): balance of dasha
    # at birth, exact Lagna/Moon degrees, paksha-vs-Shadbala, luminary strength flags,
    # the Lagna lord's disposition, day-lord observation — same computed rows as the
    # markdown signature (detailed_report.signature_first_glance).
    from app.raman_saab.detailed_report import signature_first_glance as _sig_fg
    sig.extend(_sig_fg(r))
    # header chips carry a plain-language tooltip pulled from the one glossary
    def _chip(k: str, v: str) -> str:
        gloss = next((g for term, g in GLOSSARY.items() if term.lower() in k.lower()), None)
        if gloss:
            return (f'<a class="sig-chip has-gloss" href="#glossary" title="{_esc(k)}: {_esc(gloss)}">'
                    f'<b>{_esc(k)}</b> {_esc(v)}</a>')
        return f'<span class="sig-chip"><b>{_esc(k)}</b> {_esc(v)}</span>'

    sig_html = "".join(_chip(k, str(v)) for k, v in sig)

    from app.raman_saab.detailed_report import (calibration_rollup_line,
                                                house_chief_combinations,
                                                house_conclusion,
                                                house_current_tier_line,
                                                house_dashboard_conflicts,
                                                house_frame_line,
                                                house_longevity_pointer,
                                                house_maintainer_notes,
                                                house_strip_rows)
    dist_houses = frozenset(h for h, _e in r.distinctive)
    ht_by_house = {h.house: h for h in r.preponderance.houses}

    def _xrefs(house: int) -> tuple:
        # conditional pointers only: each fires from computed state (a dashboard/bhava
        # verdict disagreement; deferred longevity metadata), never unconditionally.
        out = list(house_dashboard_conflicts(r, house))
        lp = house_longevity_pointer(r, house)
        if lp:
            out.append(lp)
        return tuple(out)

    house_strip = _house_strip(house_strip_rows(r))
    houses = "".join(
        _house_section(mr, r.calibration[mr.house],
                       r.proformas[mr.house - 1] if len(r.proformas) >= mr.house else None,
                       r.chart, dist_houses, conclusion=house_conclusion(r, mr.house),
                       ht=ht_by_house.get(mr.house),
                       frame_line=house_frame_line(r, mr.house),
                       tier_line=house_current_tier_line(r, mr.house),
                       chief=house_chief_combinations(r, mr.house),
                       cross_refs=_xrefs(mr.house),
                       maintainer_notes=house_maintainer_notes(r, mr.house),
                       cal_rollup=calibration_rollup_line(r.calibration[mr.house]))
        for mr in s.matters)
    filters = ('<div class="filters" role="group" aria-label="filter houses">'
               + "".join(f'<button type="button" data-filter="{f}"'
                         f'{" class=\'on\'" if f == "all" else ""}>{lbl}</button>'
                         for f, lbl in (("all", "All 12"), ("active", "Active now"),
                                        ("favourable", "Favourable"), ("afflicted", "Afflicted"),
                                        ("distinctive", "Distinctive")))
               + "</div>")

    combos = "".join(f"<li>{_esc(c)}</li>" for c in s.longevity_combos)
    combos_html = f'<ul class="long-combos">{combos}</ul>' if combos else ""
    if r.balarishta is not None:
        bal = ("applies" if r.balarishta.applies and not r.balarishta.cancelled
               else "cancelled" if r.balarishta.cancelled else "does not apply")
        # Wave-2 (2026-08-18, item 5a): the clear case discloses what was screened —
        # the primitive's own checked conditions, so "does not apply" is checkable.
        screen_html = ""
        if not r.balarishta.applies:
            from app.raman_saab.primitives.balarishta import screened_conditions
            screen_html = ('<p class="long-step">screened: '
                           + "; ".join(f'{_esc(label)} ({_esc(cite)})'
                                       for label, cite in screened_conditions())
                           + ' &mdash; none present</p>')
        combos_html = (f'<p class="long-step"><b>1. Balarishta</b> (early-childhood danger): '
                       f'{bal}</p>{screen_html}'
                       f'<p class="long-step"><b>2. Band by combination</b></p>'
                       + combos_html)

    vargas = "".join(_varga_card(label, body) for label, body in r.divisional)

    extras = ""
    if s.career:
        extras += (f'<h2 class="section" id="career">Career</h2><p class="section-sub">HTJAH-II '
                   f'&mdash; navamsa-dispositor of the 10th lord</p>'
                   f'<p class="doctrine">{_bold(s.career)}</p>')
    if r.profession is not None:
        pf = r.profession
        prow = "".join(
            f'<tr><td>{_esc(src.source)}</td><td>{_esc(src.key)}</td>'
            f'<td>{_esc(src.trades)}'
            + (f' <i>({_esc(src.note)})</i>' if src.note else "")
            + f'</td><td>{_esc(src.cite)}</td></tr>' for src in pf.sources)
        # Wave-2 (item 3a): the D-10 row the preamble promises — corroboration,
        # deliberately not a convergence vote.
        _d10 = getattr(pf, "dasamsa_row", ())
        if _d10:
            prow += (f'<tr><td>{_esc(_d10[0])}</td><td>{_esc(_d10[1])}</td>'
                     f'<td>{_esc(_d10[2])}</td><td>{_esc(_d10[3])}</td></tr>')
        conv = ("" if not pf.convergent else
                '<p class="section-sub"><b>Convergent trades</b> (named by 2+ '
                'derivations) &mdash; '
                + _esc(", ".join(f"{w} ({n})" for w, n in pf.convergent)) + '</p>')
        # Wave-2 (item 3c): same-graha disclosure on the convergence count.
        if getattr(pf, "convergence_note", ""):
            conv += ('<p class="section-sub"><b>One planet, several hats</b> &mdash; '
                     + _esc(pf.convergence_note) + '</p>')
        # Wave-2 (item 3b): H10 activations — the marriage monograph's H7 lens, for work.
        if getattr(pf, "h10_windows", ()):
            conv += ('<p class="section-sub"><b>H10 activations in the window</b> '
                     '(a timing lens, never a promise) &mdash; '
                     + _esc("; ".join(pf.h10_windows)) + '</p>')
        modes = ("" if not pf.mode_split else
                 '<p class="section-sub"><b>H10 mode split</b> &mdash; '
                 + _esc("; ".join(f"{k}: {v}" for k, v in pf.mode_split)) + '</p>')
        extras += (
            '<h2 class="section" id="profession">Profession synthesis</h2>'
            f'{_method_preamble_html("profession")}'
            '<p class="section-sub"><b>In simple terms:</b> every encoded derivation '
            'angle, then the deterministic convergence count &mdash; never a new '
            'judgment.</p>'
            '<div class="tablewrap"><table class="grid"><thead><tr><th>derivation</th>'
            '<th>resolves to</th><th>vocation words</th><th>cite</th></tr></thead>'
            f'<tbody>{prow}</tbody></table></div>{modes}{conv}')
    if r.wealth is not None:
        wch = r.wealth
        # Wave-2 (item 4d): the population-context column the signification rows
        # already carry in the House-by-house section, re-read per row.
        wrow = "".join(f'<tr><td>{_esc(x.channel)}</td><td>{_esc(x.reading)}</td>'
                       f'<td>{_esc(x.cite)}</td>'
                       f'<td>{_esc(getattr(x, "context", "") or "-")}</td></tr>'
                       for x in wch.rows)
        exp = ("" if not wch.expansion_periods else
               '<p class="section-sub"><b>Periods of expansion</b> (H2/H11 activated at '
               'ordinary tier or better &mdash; a timing lens, never a promise): '
               + _esc("; ".join(wch.expansion_periods)) + '</p>')
        # Wave-2 (item 4c): the non-differential-lens self-disclosure.
        if getattr(wch, "expansion_note", ""):
            exp += ('<p class="section-sub caveat"><i>Self-disclosure: '
                    + _esc(wch.expansion_note) + '.</i></p>')
        # Wave-2 (items 4a/4b): dhana/daridra fired-or-absent + the wealth lords'
        # computed conditions.
        dhana = ("" if not getattr(wch, "dhana_row", "") else
                 '<p class="section-sub"><b>Dhana / Daridra yogas</b> &mdash; '
                 + _esc(wch.dhana_row) + '</p>')
        lords = "".join('<p class="section-sub"><b>Lord condition</b> &mdash; '
                        + _esc(lc) + '</p>'
                        for lc in getattr(wch, "lord_conditions", ()))
        extras += (
            '<h2 class="section" id="wealth">Wealth chapter</h2>'
            f'{_method_preamble_html("wealth")}'
            '<p class="section-sub"><b>In simple terms:</b> the CHANNELS, not one '
            'verdict &mdash; every row re-reads a judged signification or a cited '
            'source-of-gains table.</p>'
            '<div class="tablewrap"><table class="grid"><thead><tr><th>channel</th>'
            '<th>reading</th><th>cite</th><th>population context</th></tr></thead>'
            f'<tbody>{wrow}</tbody></table></div>{dhana}{lords}{exp}')
    if r.marriage is not None:
        m = r.marriage
        # Wave-2 (items 1d/1e): fortified-first grouping with a tally; maintainer
        # notes routed to trailing fine print (still rendered — ADD-ONLY routing).
        from app.raman_saab.monographs import split_maintainer_notes as _smn
        _fort = [x for x in m.fired_kalatra if x[0] == "fortified"]
        _affl = [x for x in m.fired_kalatra if x[0] == "afflicted"]
        _rest = [x for x in m.fired_kalatra if x[0] not in ("fortified", "afflicted")]
        _fine: list[str] = []
        _lis: list[str] = []
        # NB: fresh loop names — `b` is r.birth in this scope (shadowing it was the
        # critique's bug-1 class; do not reuse outer names in to_html loops).
        for _kbr, _ktx, _kci in (*_fort, *_affl, *_rest):
            _clean, _mnote = _smn(_ktx)
            _lis.append(f'<li>({_esc(_kbr)}) {_esc(_clean)} <i>({_esc(_kci)})</i></li>')
            if _mnote:
                _fine.append(f"{_kci}: {_mnote}")
        kal = "".join(_lis)
        tally = (f'{len(_fort)} fortified, {len(_affl)} afflicted'
                 + (f', {len(_rest)} other' if _rest else ''))
        fine_html = ("" if not _fine else
                     '<p class="section-sub caveat"><i>Encoding-scope notes '
                     '(maintainer fine print, not readings): '
                     + _esc(" | ".join(_fine)) + '</i></p>')
        # Wave-2 (item 1a): the happiness-vs-coverture split, judged separately.
        split_html = ""
        if getattr(m, "marital_happiness", None) or getattr(m, "coverture", None):
            split_html = (
                '<p class="section-sub"><b>Marital happiness: '
                + _esc(m.marital_happiness or "not judged")
                + '; the partner&rsquo;s own longevity (coverture): '
                + _esc(m.coverture or "not judged")
                + '</b> &mdash; two separate 7th-house significations, judged '
                  'separately (re-read from House 7)</p>')
        # Wave-2 (item 1b): the Kuja-dosha per-frame narration.
        kuja_html = ""
        if getattr(m, "kuja_narration", ()):
            kuja_html = (
                '<p class="section-sub"><b>Kuja (Mangal) dosha, checked frame by '
                'frame (HTJAH-II:2579-2622)</b> &mdash; the rule&rsquo;s own '
                'evaluation, disclosed:</p><ul class="doclist">'
                + "".join(f'<li>{_esc(kn)}</li>' for kn in m.kuja_narration)
                + '</ul>')
        # Wave-2 (item 1c): the method's own favourable Jupiter windows on the 7th
        # from the Moon — a filter of the Gochara outlook, no new doctrine claim.
        jup_html = ""
        if getattr(m, "jupiter_h7_windows", ()):
            jup_html = (
                '<p class="section-sub"><b>Jupiter transits touching the 7th (from '
                'the Moon)</b> &mdash; the method&rsquo;s own favourable-transit '
                'windows (the Gochara outlook above) in which Jupiter occupies the '
                '7th from the Moon: '
                + _esc("; ".join(m.jupiter_h7_windows)) + '</p>')
        extras += (
            '<h2 class="section" id="marriage">Marriage monograph</h2>'
            f'{_method_preamble_html("marriage")}'
            f'<p class="section-sub"><b>The 7th house&rsquo;s scope (Raman verbatim):</b> '
            f'&ldquo;{_esc(m.seventh_covers)}&rdquo;</p>'
            f'<p class="section-sub"><b>Headline (unchanged H7 verdict)</b> &mdash; '
            f'{_esc(m.verdict)}'
            + (f' &middot; <b>Upapada</b> {_esc(m.upapada)}' if m.upapada else "")
            + (f' &middot; <b>Children (H5)</b> {_esc(m.children_after)}'
               if m.children_after else "") + '</p>'
            + split_html
            + (f'<p class="section-sub"><b>The 7th lord in house '
               f'{m.lord_placement_house} (verbatim, his periods)</b> &mdash; '
               f'&ldquo;{_esc(m.lord_period_text)}&rdquo; (HTJAH-II:710)</p>'
               if m.lord_period_text else "")
            + (f'<p class="section-sub"><b>The partner&rsquo;s significator in its '
               f'sign</b> &mdash; &ldquo;{_esc(m.spouse_sign_text[0])}&rdquo; '
               f'<i>({_esc(m.spouse_sign_text[1])})</i></p>' if m.spouse_sign_text
               else "")
            + kuja_html
            + (f'<p class="section-sub"><b>Kalatra rules firing in this chart</b> '
               f'({_esc(tally)}):</p><ul class="doclist">{kal}</ul>{fine_html}'
               if kal else "")
            + f'<p class="section-sub"><b>Timing doctrine (verbatim)</b> &mdash; '
              f'&ldquo;{_esc(m.timing_navamsa)}&rdquo; (HTJAH-II:853)</p>'
            + (f'<p class="section-sub"><b>H7 activations</b> &mdash; '
               f'{_esc("; ".join(m.timing_windows))}</p>' if m.timing_windows else "")
            + jup_html
            + f'<p class="section-sub caveat"><i>On separation and loss of the partner, '
              f'the method&rsquo;s own statements &mdash; quoted, not composed; a '
              f'statement of the method, not a prediction:</i> '
              f'&ldquo;{_esc(m.separation_quote)}&rdquo; (HTJAH-II:887)</p>')
    if r.children is not None:
        c = r.children
        pr_ = "".join(f'<li>({_esc(b)}) {_esc(t)} <i>({_esc(ci)})</i></li>'
                      for b, t, ci in c.fired_rules)
        sig = "; ".join(f"{k}: {v}" for k, v in c.significations)
        # Wave-2 (items 2a/2b): the Jupiter (putrakaraka) condition and the D-7
        # corroboration row the preamble promises.
        jup_html = ("" if not getattr(c, "putrakaraka_line", "") else
                    '<p class="section-sub"><b>' + _esc(c.putrakaraka_line) + '</b></p>')
        d7_html = ("" if not getattr(c, "d7_corroboration", "") else
                   '<p class="section-sub"><b>Saptamsa (D-7) corroboration</b> '
                   '&mdash; ' + _esc(c.d7_corroboration) + '</p>')
        # Wave-2 (item 2c): the doctrine-reviewed reframe note, VERBATIM from the
        # D-7 section, placed BEFORE the fired rules.
        reframe_html = ("" if not getattr(c, "reframe_note", "") else
                        '<p class="section-sub caveat"><i>'
                        + _esc(c.reframe_note) + '</i></p>')
        extras += (
            '<h2 class="section" id="children">Children chapter</h2>'
            f'{_method_preamble_html("children")}'
            f'<p class="section-sub"><b>Headline (unchanged H5 verdict)</b> &mdash; '
            f'{_esc(c.verdict)} &middot; {_esc(sig)}</p>'
            + jup_html + d7_html + reframe_html
            + (f'<ul class="doclist">{pr_}</ul>' if pr_ else "")
            + (f'<p class="section-sub"><b>H5 activations</b> &mdash; '
               f'{_esc("; ".join(c.timing_windows))}</p>' if c.timing_windows else "")
            + f'<p class="section-sub"><i>Raman&rsquo;s fifth-house combinations, '
              f'verbatim (quoted whole so nothing is cherry-picked):</i> '
              f'&ldquo;{_esc(c.combos_quote)}&rdquo; (HTJAH-I:5179)</p>')
    if s.deeptadi:                       # parity: previously dropped from the HTML entirely
        extras += ('<h2 class="section" id="deeptadi">Deeptadi avasthas</h2>'
                   '<p class="section-sub">each graha&rsquo;s result-state (HPA Ch.7)</p>'
                   f'<p class="doctrine">{_esc(", ".join(s.deeptadi))}</p>')
        # per-planet testimony table (2026-08-18 report-critique: from trivia to
        # testimony) — same rows the markdown renders via deeptadi_table.
        from app.raman_saab.detailed_report import deeptadi_table as _dt
        _dt_rows = _dt(r)
        if _dt_rows:
            dt_html = "".join(
                f'<tr><td><b>{_esc(n_)}</b></td><td>{_esc(st_)}</td>'
                f'<td>{_esc(res_)}</td><td>{_esc(role_)}</td></tr>'
                for n_, st_, res_, role_ in _dt_rows)
            extras += (
                '<p class="section-sub">Each state read as testimony &mdash; '
                'Raman&rsquo;s stated result beside the houses the planet answers for. '
                'Secondary states are disclosed in parentheses (the dignity-first '
                'priority order names the dominant one). Rahu/Ketu are always '
                'retrograde, hence perpetually Sakta &mdash; definitional, not a '
                'strength claim.</p>'
                '<div class="tablewrap"><table class="grid"><thead><tr><th>graha</th>'
                '<th>state</th><th>Raman&rsquo;s stated result (HPA Ch.7:46-83)</th>'
                '<th>rules / occupies</th></tr></thead>'
                f'<tbody>{dt_html}</tbody></table></div>')
        # Baladi/Jagradadi (2026-08-17 report-critique fix): computed and consumed by the
        # house judge (intensity demotion), previously never shown on any static surface.
        from app.raman_saab.judges.house_template import baladi_jagradadi_states
        _bj = baladi_jagradadi_states(r.chart)
        if _bj:
            bj_rows = "".join(
                f'<tr><td><b>{_esc(n)}</b></td><td>{_esc(_bj[n]["baladi"])}</td>'
                f'<td>{_esc(_bj[n]["jagradadi"])}</td></tr>'
                for n, _p in planet_rows(r.chart) if n in _bj)
            extras += (
                '<p class="section-sub">Baladi (ageing, by degree-in-sign) and Jagradadi '
                '(consciousness, by incoming drishti) states &mdash; the judge&rsquo;s '
                'intensity dial: a house whose deliverers sit in Mrita/Sushupti has its '
                'verdict DEGREE demoted one step, never the verdict itself. Provenance: '
                'CLASSICAL_NONCITABLE (Phaladeepika Ch.3 Sl.3/Sl.10/Sl.20; BPHS Ch.1 '
                'Sl.14-16) &mdash; outside Raman&rsquo;s own canon, shown because the '
                'judge consumes it.</p>'
                '<div class="tablewrap"><table class="grid"><thead><tr><th>graha</th>'
                '<th>Baladi (ageing)</th><th>Jagradadi (consciousness)</th></tr></thead>'
                f'<tbody>{bj_rows}</tbody></table></div>')
    if s.karakamsa_reading:
        km = "".join(f"<li>{_esc(x)}</li>" for x in s.karakamsa_reading)
        # Wave-2 (2026-08-18): header context before the sutra fragments (computed AK +
        # Karakamsa sign, re-read from the chart signature) + a purely navigational
        # cross-reference — the classical passage pairing the karakamsa reading with the
        # running chara period is corpus-gated and NOT composed here.
        extras += (f'<h2 class="section" id="karakamsa">Jaimini Karakamsa</h2>'
                   f'<p class="section-sub">the soul\'s inclination &mdash; context: the '
                   f'Atmakaraka (soul-planet) of this chart is <b>{_esc(s.atmakaraka)}</b>; '
                   f'its navamsa seat, the Karakamsa, is <b>{_esc(s.karakamsa)}</b> '
                   f'(JS 1.2 Su.14-22)</p>'
                   f'<ul class="doclist">{km}</ul>'
                   f'<p class="section-sub">See also: the dated Chara dasha (Jaimini) '
                   f'sequence in the timeline section above, and the full Karakamsa reading '
                   f'in Soul &amp; destiny below &mdash; cross-references only; the '
                   f'classical passage pairing the two is corpus-gated and not composed '
                   f'here.</p>')
    extras += _soul_section(r)
    if r.karmic is not None:
        kv = r.karmic
        krows = [("Atmakaraka", _esc(kv.atmakaraka) + " (the 7-karaka scheme, locked)")]
        if kv.karakamsa:
            krows.append(("Karakamsa", _esc(kv.karakamsa)))
        if kv.upapada:
            krows.append(("Upapada", _esc(kv.upapada)))
        krows.append(("Raman's Jaimini doctrine (verbatim)",
                      f"&ldquo;{_esc(kv.doctrine_quote)}&rdquo; "
                      f"<i>({_esc(kv.doctrine_cite)})</i>"))
        # Wave-2 (2026-08-18): one-sentence domain re-reads, not embedded full blocks —
        # REPORT COMPLETENESS holds: the full D-20/D-60 blocks still render, untrimmed,
        # at their home in the Divisional deep-reads section.
        if kv.d20_core:
            krows.append(("D-20 Vimsamsa (spiritual) &mdash; domain re-read",
                          _esc(kv.d20_core)))
        if kv.d60_core:
            krows.append(("D-60 Shashtiamsa (totality) &mdash; domain re-read",
                          _esc(kv.d60_core)))
        kbody = "".join(f'<div class="vrow"><span class="vk">{k}</span>'
                        f'<span class="vv">{v}</span></div>' for k, v in krows)
        extras += ('<h2 class="section" id="karmic">Karmic evolution (Jaimini)</h2>'
                   f'<p class="section-sub"><i>{_esc(kv.frame)}</i></p>'
                   f'<div class="vsec">{kbody}</div>')
    extras += _pitru_section(r)

    body = f"""<style>{_CSS}</style>
<div class="stickybar" id="stickybar">
  <span class="sb-sec" id="sb-sec">{_esc(b.name)}</span>
  <span class="sb-now">{_esc(s.running_md)} MD / {_esc(s.running_ad)} AD</span>
</div>
<main class="doc">
  <header>
    <div class="eyebrow">Vedic reading &middot; Sri B. V. Raman's system</div>
    <h1 class="name">{_esc(b.name)}</h1>
    <div class="birth">Born {b.year:04d}-{b.month:02d}-{b.day:02d} {b.hour:02d}:{b.minute:02d}
      (tz {b.tz_offset:+g}) &middot; {b.latitude:.4f}, {b.longitude:.4f} &middot; Lahiri sidereal</div>
    {_plain_reading_section(r)}
    <div class="sig">{sig_html}</div>
    <div class="legend">This reading speaks in two voices. The
      <span class="v-serif">doctrine</span> (serif) is Raman's verdict, faithful to his texts and
      unchanged. Beneath it the <span class="v-sans">instrument</span> discloses how that verdict
      compares with {r.calibration[1].population_n:,} real charts &mdash; its information content,
      <em>not</em> a validated prediction about a life.</div>
    <nav class="toc"><a href="#stands-out">What stands out</a><a href="#dashboard">12 matters</a>
      <a href="#charts">Charts</a><a href="#positions">Positions</a>
      <a href="#shadbala">Shadbala</a>
      <a href="#yogas">Yogas</a><a href="#sav">Ashtakavarga</a><a href="#houses">Houses</a>
      <a href="#longevity">Longevity</a><a href="#maraka">Marakas</a><a href="#now">Now</a>
      <a href="#timeline">Timeline</a><a href="#gochara">Transits</a>
      <a href="#vargas">Divisionals</a><a href="#soul">Soul</a>
      <a href="#synthesis">Insights</a><a href="#glossary">Glossary</a>
      <a href="#nichod">Nichod</a></nav>
  </header>

  {_judgment_graph_section(r)}

  {_ruler_section(r)}

  {_planet_bios_section(r)}

  {_psych_section(r)}

  {_now_box(r)}

  {_info_box(r)}

  {_interpretation_guide_section(r)}

  {_themes_section(r)}

  {_distinctive(r)}

  {_digest_section(r)}

  {_dashboard(r)}

  <h2 class="section" id="charts">The charts</h2>
  <p class="section-sub">South-Indian layout &mdash; signs are fixed, the ascendant is marked.</p>
  <div class="charts">{_chart_grid(r, navamsa=False)}{_chart_grid(r, navamsa=True)}</div>

  {_positions(r)}

  {_rect_confidence_section(r)}

  {_shadbala(r)}

  {_yogas(r)}

  {_yoga_timing_section(r)}

  {_yoga_deep_section(r)}

  {_sav(r)}

  <h2 class="section" id="houses">House by house</h2>
  <p class="section-sub">Each bhava: Raman's pillars (lord, karaka, navamsa), his verdict, then the
    population context. {_esc(ROLLUP_RULE)} Where the majority of a house&rsquo;s significations
    disagree with that headline, a <b>split-status</b> badge says so &mdash; and where the
    headline is driven by an atlas-proven inverted channel, a warning is shown inline.</p>
  {house_strip}
  {filters}
  <div class="houses">{houses}</div>

  {_house_strength_section(r)}

  {_preponderance_section(r)}

  <h2 class="section" id="longevity">Longevity</h2>
  {_method_preamble_html("longevity")}
  <p class="section-sub">Raman's order: establish the band by combination first, then fix the period
    by the marakas (HTJAH-II:4465-4472). The numeric span is a cross-check, never a date.</p>
  {combos_html}
  <p class="long"><b>3. Numeric cross-check (Ayurdaya)</b>: about
    <b>{round(r.longevity_years)} years</b> ({y}y {mo}m {d}d) &mdash;
    class <b>{_esc(longevity_band_label(r.longevity_class))}</b>. Treat as a band, not a date:
    this report never converts the band into a date.</p>

  {_maraka(r)}

  {_maraka_saturn_section(r)}

  {_health_readout_section(r)}

  {_arishta_section(r)}

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

  {_pratyantar_block(r)}

  {_chara_sequence_block(r)}

  {_ishta_kashta_section(r)}

  {_md_condition_section(r)}

  {_av_dasha_seat_section(r)}
  {_dasa_kakshya_section(r)}

  {_life_chapters_section(r)}

  {_decades_section(r)}

  {_gochara_table(r)}

  {_adverse_windows_table(r)}

  {_sade_sati_strip(r)}

  {_dasha_transit_section(r)}

  <p class="section-sub"><i>Live companion not reproducible here:</i> the interactive report
    page carries an on-demand &ldquo;Today for you (Muhurtha)&rdquo; panel &mdash;
    Raman&rsquo;s Muhurtha rules judging the CURRENT day (tarabala/chandrabala, Rahu Kalam,
    Durmuhurtha) against this native&rsquo;s own janma nakshatra and rasi, computed live at
    view time. A static report is cast once; that panel is recast
    every day &mdash; open the interactive page for it.</p>

  <h2 class="section" id="vargas">Divisional deep-reads</h2>
  <p class="section-sub">Shodasavarga &mdash; each divisional chart magnifies one matter (Raman core
    authoritative; varga overlay report-only).</p>
  {vargas}

  {extras}

  {_synthesis_section(r)}

  {_life_synthesis_section(r)}

  {_glossary()}

  {_nichod_section(r)}

  {_aptitude_section(r)}

  <div class="provenance">Doctrine faithful to B. V. Raman; italicised population context is
    EMPIRICAL_ASTRODATABANK provenance (n={r.calibration[1].population_n:,}), explicitly not Raman.
    Percentiles state how this chart's reading compares with real charts under Raman's method &mdash;
    a statement about the method's output, not a validated prediction about life outcomes.</div>
</main>
<script>
(function () {{
  var houses = document.querySelector('.houses');
  var bar = document.querySelector('.filters');
  if (houses && bar) {{
    bar.addEventListener('click', function (ev) {{
      var btn = ev.target.closest('button[data-filter]');
      if (!btn) return;
      var want = btn.dataset.filter;
      bar.querySelectorAll('button').forEach(function (b) {{ b.classList.toggle('on', b === btn); }});
      houses.querySelectorAll('.house').forEach(function (h) {{
        var flags = (h.dataset.flags || '').split(' ');
        h.hidden = !(want === 'all' || flags.indexOf(want) !== -1);
      }});
    }});
  }}
  var label = document.getElementById('sb-sec');
  var secs = Array.prototype.slice.call(document.querySelectorAll('h2.section[id]'));
  if (label && secs.length && 'IntersectionObserver' in window) {{
    var io = new IntersectionObserver(function (entries) {{
      entries.forEach(function (e) {{ if (e.isIntersecting) label.textContent = e.target.textContent; }});
    }}, {{ rootMargin: '-45% 0px -50% 0px' }});
    secs.forEach(function (sec) {{ io.observe(sec); }});
  }}
}})();
</script>"""
    return _apply_glossary_abbrs(_apply_section_subtitles(body))


#: mirrors detailed_report._INJECTED_PREAMBLE_IDS — the ten post-wiring chapters.
_INJECTED_PREAMBLE_IDS = frozenset(
    {"yogas", "timeline", "shadbala", "ashtakavarga", "gochara",
     "divisional", "soul", "ruler", "maraka", "karmic"})


def _apply_section_subtitles(html_str: str) -> str:
    """Reframe part 2 (2026-08-17): inject the section_meta plain-language subtitle
    (+ the ten late-wired method preambles) right after each section's first
    ``<h2 class="section" id="...">`` — the same document-wide-transform shape as
    ``_apply_glossary_abbrs``. Add-only: markers, ids and order are untouched."""
    import re as _re

    from app.raman_saab.detailed_report import SECTION_CONTRACT
    from app.raman_saab.section_meta import SECTION_META
    for spec in SECTION_CONTRACT:
        hm = spec.html_marker
        if not hm or not hm.startswith('id="'):
            continue
        m = SECTION_META.get(spec.section_id)
        if m is None:
            continue
        sub = (f'<p class="section-sub"><i>{_esc(m.subtitle_en)}</i> &mdash; '
               f'<b>Answers:</b> {_esc(m.answers_en)}</p>')
        if spec.section_id in _INJECTED_PREAMBLE_IDS:
            sub += _method_preamble_html(spec.section_id)
        pat = _re.compile(r'(<h2 class="section" ' + _re.escape(hm) + r'>.*?</h2>)',
                          _re.S)
        html_str, _n = pat.subn(lambda mo: mo.group(1) + sub, html_str, count=1)
    return html_str


def standalone_html(r: DetailedReport, *, title: str | None = None) -> str:
    """Full standalone document for local viewing / CLI --format html."""
    t = _esc(title or f"Detailed reading - {r.birth.name}")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{t}</title></head><body>{to_html(r)}</body></html>')
