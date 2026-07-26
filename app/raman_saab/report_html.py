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
    graded_buckets,
    driver_entry,
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


def _house_section(mr, cal, pf, chart, distinctive_houses: frozenset[int] = frozenset(),
                   conclusion: str = "") -> str:
    """One bhava: Raman's pillars + verdict (with the rollup driver named), then the overlay.
    `conclusion` is the pre-composed `detailed_report.house_conclusion` line (Raman's own
    closing device) — passed in, not computed here, so both renderers share one composer."""
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
        if split.favourable == split.afflicted and split.mixed == 0:
            badge_label = f"{split.favourable}-{split.afflicted} split"
        else:
            n = {"favourable": split.favourable, "afflicted": split.afflicted,
                 "mixed": split.mixed}[split.majority]
            badge_label = f"{n}/{split.total} {split.majority}"
        split_badge = (f'<span class="chip chip--{_vclass(split.majority)} split-badge" '
                       f'title="{_esc(note)}">{_esc(badge_label)}</span>')
        split_note_html = f'<div class="split-note">Split status: {_esc(note)}</div>'
    if drv_entry is not None and drv_entry.inverted_warning:
        inverted_note_html = (
            '<div class="split-note split-note--warn">&#9888; The driver, '
            f'<b>{_esc(driver)}</b>, is an atlas-proven <b>INVERTED channel</b> — real cases '
            'ran opposite to this reading; treat this house’s headline with maximal '
            'skepticism.</div>')

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

    return (
        f'<section class="house" data-flags="{" ".join(flags)}"><div class="house-head">'
        f'<h3><span class="house-num">H{mr.house}</span> &middot; {_esc(_HOUSE_NAME[mr.house])}</h3>'
        f'<span class="chip chip--{_vclass(mr.verdict)}">{_esc(mr.verdict)}</span>'
        f'{split_badge}{drv}{active}</div>'
        f'{split_note_html}{inverted_note_html}'
        f'{pillars}<p class="doctrine">{_bold(mr.reading)}</p>'
        + (f'<div class="split-note"><b>Conclusion</b> &mdash; {_esc(conclusion)}</div>'
           if conclusion else "")
        + f'<div class="instrument"><div class="instrument-label">Population context '
        f'&mdash; empirical, not Raman</div>{rows}</div></section>')


def _house_chip(a, *, ring: bool = False) -> str:
    """A house chip carrying its natal verdict (title = full verdict); ring = par-excellence."""
    return (f'<span class="chip chip--{_vclass(a.natal_verdict)}{" focus" if ring else ""}" '
            f'title="{_esc(_HOUSE_NAME[a.house])}: {_esc(a.natal_verdict)} '
            f'({_esc(a.natal_degree)})">H{a.house}</span>')


def _info_box(r: DetailedReport) -> str:
    """The honesty headline: how much of this document actually distinguishes this chart."""
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
        f'{inv_line}</div>')


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


def _house_strength_section(r: DetailedReport) -> str:
    """Cross-checks each house's verdict against Bhava Bala rank + SAV band — extends the
    House-by-house section above with whether each verdict stands on strong or shaky ground."""
    if not r.house_strength:
        return ""
    rows = "".join(
        f'<tr><td>H{row.house} {_esc(_HOUSE_NAME[row.house])}</td>'
        f'<td><span class="chip chip--{row.verdict}">{_esc(row.verdict)}</span></td>'
        f'<td class="num">{row.bhava_bala_rank or "n/a"} of 12</td>'
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
        '<th class="num">Bhava Bala rank</th><th class="num">SAV bindus</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>')


def _preponderance_section(r: DetailedReport) -> str:
    """The full per-house testimony ledgers (v14) — Raman's 'judgment is the summing up of the
    influence of planets' (HTJAH-I:983-991) applied to every already-computed axis; the verdict
    column is the House-by-house rollup, displayed but never counted in its own tally."""
    if not r.preponderance.houses:
        return ""
    rows = "".join(
        f'<tr><td>H{ht_.house} {_esc(_HOUSE_NAME[ht_.house])}</td>'
        f'<td><span class="chip chip--{_vclass(ht_.verdict)}">{_esc(ht_.verdict)}</span></td>'
        f'<td class="num">{ht_.favourable}</td><td class="num">{ht_.adverse}</td>'
        f'<td class="num">{ht_.neutral}</td><td class="num">{ht_.absent}</td>'
        f'<td>{_esc(ht_.preponderance)}</td><td>{_esc(ht_.status)}</td></tr>'
        for ht_ in r.preponderance.houses)
    details = "".join(
        f'<div class="now-row"><span class="theme-label">H{ht_.house}</span>'
        + _esc("; ".join(f"{t.name} {t.value}" for t in ht_.testimonies
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
        '<div class="tablewrap"><table class="grid"><thead><tr><th>house</th><th>verdict</th>'
        '<th class="num">for</th><th class="num">against</th><th class="num">neutral</th>'
        '<th class="num">absent</th><th>preponderance</th><th>status</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>'
        f'<div class="instrument">{details}</div>'
        f'{picks_html}')


def _yoga_timing_section(r: DetailedReport) -> str:
    """When does each fired yoga's own lord run as MD or AD — extends the Yogas section above
    with WHEN, reusing the same lord_quality strength read Life-narrative already computes."""
    if not r.yoga_timing:
        return ""
    rows = "".join(
        f'<tr><td><b>{_esc(t.yoga_name)}</b></td><td>{_esc(t.role)}</td>'
        f'<td>{_esc(t.planet)}</td>'
        f'<td>{_outlook_window_label(t.period_start_jd, t.period_end_jd)}</td>'
        f'<td>{_esc(t.quality.tag)}</td></tr>'
        for t in r.yoga_timing)
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
        '<div class="tablewrap"><table class="grid"><thead><tr><th>yoga</th><th>period</th>'
        '<th>planet</th><th>window</th><th>delivery</th></tr></thead>'
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
    return ('<h2 class="section" id="sav">Ashtakavarga</h2>'
            '<p class="section-sub">Sarvashtakavarga bindus per sign; average 28 (total 337). '
            'Raman rates it corroborative, not decisive &mdash; <em>&ldquo;it does not seem to be '
            'quite reliable&rdquo;</em> (HTJAH-II:4453-4456).</p>'
            f'<div class="tablewrap"><table class="grid sav"><thead><tr>{head}</tr></thead>'
            f'<tbody><tr>{cells}</tr></tbody></table></div>')


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
        f'<div class="instrument">{"".join(rows)}</div>'
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
    from app.raman_saab.primitives.shadbala.total import is_powerful
    sb_rows = [(n, p) for n, p in planet_rows(r.chart) if p.shadbala_rupas is not None]
    if not sb_rows:
        return ""
    rows = ""
    for name, p in sb_rows:
        sb = p.shadbala_rupas
        strong = is_powerful(name, sb.total / 60.0)
        ik = (f"{p.ishta:.1f}/{p.kashta:.1f}"
              if p.ishta is not None and p.kashta is not None else "&ndash;")
        cells = "".join(f'<td class="num">{v / 60.0:.2f}</td>' for v in
                        (sb.sthana, sb.dig, sb.kala, sb.cheshta, sb.naisargika, sb.drik))
        rows += (f'<tr><td><b>{_esc(name)}</b></td>{cells}'
                 f'<td class="num"><b>{sb.total / 60.0:.2f}</b></td>'
                 f'<td>{"yes" if strong else "no"}</td><td class="num">{ik}</td></tr>')
    return ('<h2 class="section" id="shadbala">Shadbala &mdash; six-fold strength</h2>'
            '<p class="section-sub">The numbers behind every &ldquo;strong / weak&rdquo; in this '
            'report, in rupas (Raman: a yoga&rsquo;s effect depends on Shadbala; HTJAH-I:611).</p>'
            '<div class="tablewrap"><table class="grid"><thead><tr><th>graha</th>'
            '<th class="num">sthana</th><th class="num">dig</th><th class="num">kala</th>'
            '<th class="num">cheshta</th><th class="num">naisargika</th><th class="num">drik</th>'
            '<th class="num">total</th><th>powerful?</th><th class="num">ishta/kashta</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>')


def _maraka(r: DetailedReport) -> str:
    mp = getattr(r.chart, "maraka_points", None)
    if mp is None:
        return ""
    tiers = ""
    for tier in ("primary", "secondary", "tertiary"):
        names = [u.graha for u in mp.units if u.tier == tier]
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
        f'<td class="num">{c.score}</td></tr>'
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


def _gochara_table(r: DetailedReport) -> str:
    if not r.gochara:
        return ""
    rows = ""
    for g in r.gochara:
        av = str(g.bav_bindus) if g.bav_bindus is not None else "&ndash;"
        vedha = _esc(", ".join(g.vedha_by)) if g.vedha_by else "&ndash;"
        net = ("favourable" if g.net_good else "obstructed/adverse")
        rows += (f'<tr><td><b>{_esc(g.planet)}</b></td><td>{_esc(_SIGN_NAME[g.sign])}</td>'
                 f'<td class="num">{g.house_from_moon}</td>'
                 f'<td>{"favourable" if g.gochara_good else "adverse"}</td>'
                 f'<td class="num">{av}</td><td>{vedha}</td>'
                 f'<td><span class="chip chip--{"favourable" if g.net_good else "afflicted"}">'
                 f'{net}</span></td></tr>')
    return ('<h2 class="section" id="gochara">Current transits (Gochara) with Vedha</h2>'
            '<p class="section-sub">From the natal Moon at the reference date. Raman: transits are '
            'secondary, catalytic &mdash; conclusions rest on Dasa-vichara (HTJAH-II:4679-4687). '
            'The net column applies Vedha: an obstructed transit does not deliver.</p>'
            '<div class="tablewrap"><table class="grid"><thead><tr><th>planet</th><th>sign</th>'
            '<th class="num">from Moon</th><th>classical</th><th class="num">AV</th>'
            '<th>Vedha by</th><th>net</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
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
        f'</thead><tbody>{rows}</tbody></table></div>')


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
        f'<p class="pr-closing">{_esc(p.closing)}</p>'
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
        out.append("</ol></details>")
    return "".join(out)


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
    # header chips carry a plain-language tooltip pulled from the one glossary
    def _chip(k: str, v: str) -> str:
        gloss = next((g for term, g in GLOSSARY.items() if term.lower() in k.lower()), None)
        if gloss:
            return (f'<a class="sig-chip has-gloss" href="#glossary" title="{_esc(k)}: {_esc(gloss)}">'
                    f'<b>{_esc(k)}</b> {_esc(v)}</a>')
        return f'<span class="sig-chip"><b>{_esc(k)}</b> {_esc(v)}</span>'

    sig_html = "".join(_chip(k, str(v)) for k, v in sig)

    from app.raman_saab.detailed_report import house_conclusion
    dist_houses = frozenset(h for h, _e in r.distinctive)
    houses = "".join(
        _house_section(mr, r.calibration[mr.house],
                       r.proformas[mr.house - 1] if len(r.proformas) >= mr.house else None,
                       r.chart, dist_houses, conclusion=house_conclusion(r, mr.house))
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
        combos_html = (f'<p class="long-step"><b>1. Balarishta</b> (early-childhood danger): '
                       f'{bal}</p><p class="long-step"><b>2. Band by combination</b></p>'
                       + combos_html)

    vargas = "".join(_varga_card(label, body) for label, body in r.divisional)

    extras = ""
    if s.career:
        extras += (f'<h2 class="section" id="career">Career</h2><p class="section-sub">HTJAH-II '
                   f'&mdash; navamsa-dispositor of the 10th lord</p>'
                   f'<p class="doctrine">{_bold(s.career)}</p>')
    if s.deeptadi:                       # parity: previously dropped from the HTML entirely
        extras += ('<h2 class="section" id="deeptadi">Deeptadi avasthas</h2>'
                   '<p class="section-sub">each graha&rsquo;s result-state (HPA Ch.7)</p>'
                   f'<p class="doctrine">{_esc(", ".join(s.deeptadi))}</p>')
    if s.karakamsa_reading:
        km = "".join(f"<li>{_esc(x)}</li>" for x in s.karakamsa_reading)
        extras += (f'<h2 class="section" id="karakamsa">Jaimini Karakamsa</h2>'
                   f'<p class="section-sub">the soul\'s inclination</p>'
                   f'<ul class="doclist">{km}</ul>')
    extras += _soul_section(r)
    extras += _pitru_section(r)

    return f"""<style>{_CSS}</style>
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

  {_ruler_section(r)}

  {_now_box(r)}

  {_info_box(r)}

  {_distinctive(r)}

  {_dashboard(r)}

  <h2 class="section" id="charts">The charts</h2>
  <p class="section-sub">South-Indian layout &mdash; signs are fixed, the ascendant is marked.</p>
  <div class="charts">{_chart_grid(r, navamsa=False)}{_chart_grid(r, navamsa=True)}</div>

  {_positions(r)}

  {_shadbala(r)}

  {_yogas(r)}

  {_yoga_timing_section(r)}

  {_sav(r)}

  <h2 class="section" id="houses">House by house</h2>
  <p class="section-sub">Each bhava: Raman's pillars (lord, karaka, navamsa), his verdict, then the
    population context. {_esc(ROLLUP_RULE)} Where the majority of a house&rsquo;s significations
    disagree with that headline, a <b>split-status</b> badge says so &mdash; and where the
    headline is driven by an atlas-proven inverted channel, a warning is shown inline.</p>
  {filters}
  <div class="houses">{houses}</div>

  {_house_strength_section(r)}

  {_preponderance_section(r)}

  <h2 class="section" id="longevity">Longevity</h2>
  <p class="section-sub">Raman's order: establish the band by combination first, then fix the period
    by the marakas (HTJAH-II:4465-4472). The numeric span is a cross-check, never a date.</p>
  {combos_html}
  <p class="long"><b>3. Numeric cross-check (Ayurdaya)</b>: about
    <b>{round(r.longevity_years)} years</b> ({y}y {mo}m {d}d) &mdash;
    class <b>{_esc(r.longevity_class)}</b>. Treat as a band; the engine's own health layer defers
    lifespan.</p>

  {_maraka(r)}

  {_maraka_saturn_section(r)}

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

  {_ishta_kashta_section(r)}

  {_md_condition_section(r)}

  {_av_dasha_seat_section(r)}

  {_life_chapters_section(r)}

  {_gochara_table(r)}

  {_dasha_transit_section(r)}

  <h2 class="section" id="vargas">Divisional deep-reads</h2>
  <p class="section-sub">Shodasavarga &mdash; each divisional chart magnifies one matter (Raman core
    authoritative; varga overlay report-only).</p>
  {vargas}

  {extras}

  {_synthesis_section(r)}

  {_glossary()}

  {_nichod_section(r)}

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


def standalone_html(r: DetailedReport, *, title: str | None = None) -> str:
    """Full standalone document for local viewing / CLI --format html."""
    t = _esc(title or f"Detailed reading - {r.birth.name}")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{t}</title></head><body>{to_html(r)}</body></html>')
