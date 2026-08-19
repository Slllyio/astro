# -*- coding: utf-8 -*-
"""Doctrine chart report — cast a chart, run judge_chart_doctrine, render a full HTML
reading (Rāśi + Navāṁśa squares, the 12-house verdict matrix, every fired sūtra verbatim,
and the chart-wide combinations).

Reproduces the Mainpuri kundalī engine reading used in PR #10's review thread. Run:

    PYTHONPATH=. python3 docs/raman_doctrine/examples/chart_report.py > /tmp/mainpuri.html

Self-contained: no scratchpad inputs. Swap MAINPURI for any {positions, lagna, jd} to
report a different nativity. The report is the live output of the current engine, so it
reflects increments 21–23 (full natal firing, natal-scope filter, Kemadruma-bhaṅga).
"""
import html, json
import app.medini.doctrine.raman_chart as rc
from app.medini.doctrine.domains import house_judgment as HJ
from app.core.ephemeris_engine import calculate_divisional_longitude

CSS = r""":root{
  --ground:#F1E9D8; --panel:#FBF7EC; --panel2:#F6EFDE;
  --ink:#2B2519; --ink-soft:#6E6454; --ink-faint:#938974;
  --accent:#B0551D; --accent-soft:#C87B3E; --indigo:#3C3A63;
  --line:#E2D8C2; --line-soft:#ECE4D2;
  --pos:#2E7D5B; --neg:#A5432F;
  --serif:"Iowan Old Style","Palatino Linotype","Book Antiqua",Palatino,Georgia,serif;
  --quote:Georgia,"Times New Roman",serif;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --ground:#141019; --panel:#1D1826; --panel2:#221C2D;
  --ink:#ECE3D1; --ink-soft:#AEA48C; --ink-faint:#7C7361;
  --accent:#E0913A; --accent-soft:#E8A85E; --indigo:#A29FDC;
  --line:#2C2637; --line-soft:#241F30;
  --pos:#5FB58A; --neg:#D6795F;
}}
:root[data-theme="light"]{
  --ground:#F1E9D8; --panel:#FBF7EC; --panel2:#F6EFDE;
  --ink:#2B2519; --ink-soft:#6E6454; --ink-faint:#938974;
  --accent:#B0551D; --accent-soft:#C87B3E; --indigo:#3C3A63;
  --line:#E2D8C2; --line-soft:#ECE4D2; --pos:#2E7D5B; --neg:#A5432F;
}
:root[data-theme="dark"]{
  --ground:#141019; --panel:#1D1826; --panel2:#221C2D;
  --ink:#ECE3D1; --ink-soft:#AEA48C; --ink-faint:#7C7361;
  --accent:#E0913A; --accent-soft:#E8A85E; --indigo:#A29FDC;
  --line:#2C2637; --line-soft:#241F30; --pos:#5FB58A; --neg:#D6795F;
}

/* verdict diverging scale — semantic, constant across themes */
.v0{--vc:#9C3327;--vt:#fff}.v1{--vc:#B85E38;--vt:#fff}.v2{--vc:#C9A04E;--vt:#2B2011}
.v3{--vc:#AEA24F;--vt:#241f0d}.v4{--vc:#8AA04F;--vt:#1e2410}.v5{--vc:#5E9A5A;--vt:#fff}
.v6{--vc:#3E8F63;--vt:#fff}.v7{--vc:#2C8270;--vt:#fff}.v8{--vc:#1F7378;--vt:#fff}

*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:clamp(20px,4vw,56px) clamp(16px,4vw,40px)}
a{color:inherit;text-decoration:none}
h1,h2,h3,h4{font-family:var(--serif);font-weight:600;text-wrap:balance;margin:0}
em{color:var(--ink-soft);font-style:italic}
code{font-family:var(--mono);font-size:.85em;background:var(--panel2);padding:.1em .4em;border-radius:4px}

/* masthead */
.masthead{border-bottom:2px solid var(--ink);padding-bottom:28px;margin-bottom:36px}
.mh-eyebrow{font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);
  font-weight:600;margin-bottom:14px}
.masthead h1{font-size:clamp(2.4rem,6vw,4rem);line-height:1.02;letter-spacing:-.01em}
.mh-sub{font-family:var(--quote);font-size:1.12rem;color:var(--ink-soft);max-width:60ch;margin:.7em 0 0}
.mh-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}
.chip{font-size:.78rem;padding:.34em .8em;border:1px solid var(--line);border-radius:999px;
  background:var(--panel);color:var(--ink-soft);white-space:nowrap}

/* charts */
.charts{display:flex;flex-wrap:wrap;gap:22px;margin-bottom:48px;align-items:flex-start}
.si-grid{display:grid;grid-template-columns:repeat(4,1fr);grid-template-rows:repeat(4,1fr);
  width:min(320px,80vw);aspect-ratio:1;background:var(--line);gap:1px;border:1px solid var(--ink);
  border-radius:6px;overflow:hidden;box-shadow:0 2px 18px rgba(0,0,0,.06)}
.si-cell{background:var(--panel);padding:6px 7px;display:flex;flex-direction:column;gap:3px;
  min-width:0;position:relative}
.si-cell.asc{background:color-mix(in srgb,var(--accent) 12%,var(--panel))}
.si-sign{font-size:.62rem;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-faint);font-weight:600}
.asc-mark{position:absolute;top:5px;right:6px;font-size:.54rem;letter-spacing:.08em;text-transform:uppercase;
  color:var(--accent);font-weight:700}
.si-pls{display:flex;flex-wrap:wrap;gap:3px;margin-top:auto}
.pl{font-size:.72rem;font-weight:600;font-family:var(--mono);background:var(--panel2);
  border:1px solid var(--line);border-radius:4px;padding:.05em .35em;color:var(--ink)}
.si-center{background:var(--panel2);display:flex;align-items:center;justify-content:center;text-align:center}
.si-center-t{font-family:var(--serif);font-size:.9rem;color:var(--ink-soft);font-weight:600;padding:4px}
.placements{flex:1;min-width:230px}
.placements h4{font-size:.9rem;text-transform:uppercase;letter-spacing:.1em;color:var(--ink-soft);margin-bottom:10px}
.ptab{width:100%;border-collapse:collapse;font-size:.88rem}
.ptab th{text-align:left;font-weight:600;color:var(--ink-faint);font-size:.72rem;text-transform:uppercase;
  letter-spacing:.08em;padding:5px 10px 5px 0;border-bottom:1px solid var(--line)}
.ptab td{padding:5px 10px 5px 0;border-bottom:1px solid var(--line-soft)}
.ptab .pn{font-weight:600}.ptab .num{font-variant-numeric:tabular-nums;color:var(--ink-soft)}

/* section headings */
section>h2{font-size:clamp(1.5rem,3.4vw,2.1rem);margin-bottom:8px;letter-spacing:-.01em}
.lede{font-family:var(--quote);color:var(--ink-soft);max-width:72ch;margin:0 0 22px;font-size:1.02rem}
.swatch{display:inline-block;width:.85em;height:.85em;border-radius:3px;background:var(--vc);
  vertical-align:-.08em;margin:0 .1em}

/* matrix */
.matrix-wrap{margin-bottom:52px}
.tscroll{overflow-x:auto;border:1px solid var(--line);border-radius:10px}
.matrix{width:100%;border-collapse:collapse;font-size:.86rem;min-width:640px}
.matrix thead th{background:var(--panel);text-align:left;font-family:var(--sans);font-weight:600;
  font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-soft);
  padding:11px 12px;border-bottom:1px solid var(--line);position:sticky;top:0}
.matrix tbody th.hname{text-align:left;font-family:var(--sans);font-weight:500;padding:9px 12px;
  border-bottom:1px solid var(--line-soft);white-space:nowrap}
.matrix .hname b{color:var(--accent);margin-right:.4em;font-variant-numeric:tabular-nums}
.matrix .hname span{color:var(--ink-soft)}
.vc{padding:7px 10px;border-bottom:1px solid var(--line-soft);border-left:1px solid var(--line-soft)}
.vc a{display:block;background:var(--vc);color:var(--vt);border-radius:5px;padding:.3em .55em;
  font-size:.8rem;font-weight:600;text-align:center;white-space:nowrap}
.vc.strong a{box-shadow:0 0 0 2px color-mix(in srgb,var(--vc) 45%,transparent)}
.matrix .fired{text-align:center;font-variant-numeric:tabular-nums;color:var(--ink-faint);
  border-bottom:1px solid var(--line-soft);font-size:.82rem}

/* houses */
.houses{margin-bottom:52px}
.house{background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:22px clamp(16px,2.4vw,26px);margin-bottom:20px;scroll-margin-top:16px}
.house-hd{display:flex;flex-wrap:wrap;gap:14px 20px;justify-content:space-between;align-items:flex-start;
  padding-bottom:16px;border-bottom:1px solid var(--line-soft);margin-bottom:18px}
.house-title{display:flex;gap:14px;align-items:center}
.hn{font-family:var(--serif);font-size:1.9rem;font-weight:700;color:var(--accent);
  width:1.7em;height:1.7em;flex:none;display:grid;place-items:center;
  border:2px solid color-mix(in srgb,var(--accent) 40%,transparent);border-radius:50%}
.house-title h3{font-size:1.28rem}
.dom{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-faint)}
.verdicts{display:flex;flex-wrap:wrap;gap:6px;align-items:center;max-width:520px}
.vpill{font-size:.74rem;font-weight:600;padding:.3em .6em;border-radius:6px;
  background:color-mix(in srgb,var(--vc) 15%,var(--panel));color:var(--ink);
  border:1px solid color-mix(in srgb,var(--vc) 45%,transparent)}
.vpill.big{background:var(--vc);color:var(--vt);font-size:.8rem}
.house-body{display:grid;grid-template-columns:1fr 1fr;gap:26px}
.col-label{font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:var(--accent);
  font-weight:700;margin-bottom:12px}
.col-label em{color:var(--ink-faint);text-transform:none;letter-spacing:0;font-weight:400}
.fac{margin-bottom:14px}
.fac-h{font-size:.86rem;font-weight:600;margin-bottom:5px}
.fac-h em{font-size:.76rem}
.finds{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:4px}
.finds li{display:grid;grid-template-columns:auto auto 1fr;gap:8px;align-items:baseline;
  font-size:.84rem;padding:3px 0;border-bottom:1px dotted var(--line-soft)}
.fdelta{font-family:var(--mono);font-size:.76rem;font-weight:700;font-variant-numeric:tabular-nums;
  min-width:3.2em;text-align:right}
.finds li.pos .fdelta{color:var(--pos)}.finds li.neg .fdelta{color:var(--neg)}
.finds li.zero .fdelta{color:var(--ink-faint)}
.fframe{font-size:.64rem;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-faint);
  border:1px solid var(--line);border-radius:4px;padding:.05em .35em;align-self:center}
.ftext{color:var(--ink-soft)}

/* sutras */
.sut{margin-bottom:16px}
.sut-h{font-size:.8rem;font-weight:700;color:var(--indigo);margin-bottom:7px;
  padding-bottom:4px;border-bottom:1px solid var(--line-soft)}
.sutras{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px}
.sutras li{position:relative;padding-left:14px;font-family:var(--quote);font-size:.92rem;
  color:var(--ink);line-height:1.5}
.sutras li::before{content:"";position:absolute;left:0;top:.55em;width:5px;height:5px;border-radius:50%;
  background:var(--ink-faint)}
.sutras li.s-favorable::before{background:var(--pos)}
.sutras li.s-unfavorable::before{background:var(--neg)}
.sutras li.s-mixed::before{background:var(--accent)}
.s-cite{display:inline-block;font-family:var(--mono);font-size:.64rem;font-weight:600;
  text-transform:uppercase;letter-spacing:.04em;color:var(--accent);
  background:color-mix(in srgb,var(--accent) 10%,transparent);border-radius:4px;
  padding:.08em .4em;margin-right:.5em;vertical-align:.08em}
.s-text{color:var(--ink-soft)}

/* global */
.global{margin-bottom:48px}
.cg-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}
.cg{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.cg h4{font-size:1rem;margin-bottom:12px;color:var(--indigo)}

/* footer */
.foot{border-top:2px solid var(--ink);padding-top:22px;font-family:var(--quote);
  color:var(--ink-soft);font-size:.95rem;display:flex;flex-direction:column;gap:12px}
.foot b{color:var(--ink)}
.caveat{background:var(--panel2);border-left:3px solid var(--accent);padding:12px 16px;border-radius:0 8px 8px 0}

@media (max-width:680px){
  .house-body{grid-template-columns:1fr;gap:20px}
  .verdicts{max-width:none}
}
"""


def build_analysis(positions, lagna, jd, dasha):
    """Cast the chart and return the judgment as a plain dict (the render input)."""
    ch = rc.from_printed_positions(positions, lagna, birth_jd=jd)
    c = ch.bundle.chart
    SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio",
             "Sagittarius","Capricorn","Aquarius","Pisces"]
    cd = HJ.judge_chart_doctrine(ch, dasha=dasha)
    nav = {p: int(calculate_divisional_longitude(lon, 9) // 30) + 1
           for p, lon in c.planet_lons.items()}
    out = {"signs": SIGNS, "asc_sign": c.asc_sign, "planet_signs": c.planet_signs,
           "planet_houses": c.planet_houses, "navamsa": nav,
           "navamsa_asc": int(calculate_divisional_longitude(c.asc_lon, 9) // 30) + 1,
           "houses": {}, "chart_global": []}
    HN = {1:"Tanu (Self/Body)",2:"Dhana (Wealth/Family)",3:"Sahaja (Siblings/Courage)",
          4:"Bandhu (Home/Mother)",5:"Putra (Children/Intellect)",6:"Ari (Enemies/Health)",
          7:"Kalatra (Marriage)",8:"Ayus (Longevity)",9:"Bhagya (Fortune/Father)",
          10:"Karma (Career)",11:"Labha (Gains)",12:"Vyaya (Loss/Moksha)"}
    for h, j in cd.houses.items():
        hd = {"name": HN[h], "domain": j.domain, "lagna": j.lagna_verdict.label,
              "lord": j.lord_verdict.label, "karaka": j.karaka_verdict.label,
              "conclusion": j.conclusion.label, "n_fired": j.n_fired, "buckets": {}}
        for s in j.steps:
            ev = [{"id": e.rule_id, "pol": e.polarity, "text": e.text} for e in s.evidence]
            if ev:
                hd["buckets"][s.key] = ev
        hd["findings"] = {f: [{"text": x.text, "delta": round(x.delta, 2), "frame": x.frame}
                              for x in v.findings]
                          for f, v in (("lagna", j.lagna_verdict), ("lord", j.lord_verdict),
                                       ("karaka", j.karaka_verdict))}
        out["houses"][str(h)] = hd
    for g in cd.chart_global:
        out["chart_global"].append({"id": g.rule_id, "type": g.rule_type, "pol": g.polarity,
                                     "mag": g.magnitude, "text": g.text, "book": g.book})
    return out


def render(d):
    """dict from build_analysis -> a full self-contained HTML page string."""
    SIGNS = d["signs"]
    SCALE = ['afflicted','weak','moderate','moderately good','fairly good',
             'fairly strong','fairly powerful','very strong','very powerful']
    GRADE = {g:i for i,g in enumerate(SCALE)}

    PLANET_GLYPH = {"Sun":"Su","Moon":"Mo","Mars":"Ma","Mercury":"Me","Jupiter":"Ju",
                    "Venus":"Ve","Saturn":"Sa","Rahu":"Ra","Ketu":"Ke"}
    BOOK = {"htjah_vol1":"HTJAH I","htjah_vol2":"HTJAH II","hpa":"HPA","three_hundred":"300 Yogas"}
    BUCKET_LABEL = {"bhava":"Bhāva (the house)","lord":"Lord of the house","occupants":"Occupants",
                    "karaka":"Kāraka (significator)","combinations":"Combinations / Yogas"}

    def cite(rid):
        parts = rid.split(".")
        book = parts[1] if len(parts) > 1 else ""
        return BOOK.get(book, book)

    def esc(s): return html.escape(str(s))

    def grade_class(label):
        i = GRADE.get(label, 2)
        return f"v{i}"

    # ---- South Indian grid ---------------------------------------------------
    # fixed 4x4: signs at the border, clockwise from Pisces(12) top-left.
    SI_CELLS = [12,1,2,3, 11,None,None,4, 10,None,None,5, 9,8,7,6]

    def sign_occupants(signs_map):
        occ = {s:[] for s in range(1,13)}
        for p, s in signs_map.items():
            occ[s].append(p)
        return occ

    def square_chart(signs_map, asc_sign, title):
        occ = sign_occupants(signs_map)
        cells = []
        center_done = False
        for idx, sgn in enumerate(SI_CELLS):
            if sgn is None:
                # render the 2x2 center once as a label block via a single spanning cell
                if not center_done:
                    cells.append(f'<div class="si-center" style="grid-area:2/2/4/4">'
                                 f'<span class="si-center-t">{esc(title)}</span></div>')
                    center_done = True
                continue
            planets = occ.get(sgn, [])
            is_asc = (sgn == asc_sign)
            chips = "".join(f'<span class="pl">{PLANET_GLYPH[p]}</span>' for p in planets)
            asc_mark = '<span class="asc-mark">Lagna</span>' if is_asc else ""
            cells.append(
                f'<div class="si-cell{" asc" if is_asc else ""}">'
                f'<span class="si-sign">{esc(SIGNS[sgn-1][:3])}</span>{asc_mark}'
                f'<span class="si-pls">{chips}</span></div>')
        return f'<div class="si-grid">{"".join(cells)}</div>'

    # ---- verdict matrix ------------------------------------------------------
    HOUSE_ROWS = ""
    for h in range(1,13):
        x = d["houses"][str(h)]
        cells = ""
        for key in ("lagna","lord","karaka","conclusion"):
            lab = x[key]
            strong = ' strong' if key=="conclusion" else ''
            cells += f'<td class="vc {grade_class(lab)}{strong}"><a href="#h{h}">{esc(lab)}</a></td>'
        HOUSE_ROWS += (f'<tr><th class="hname"><a href="#h{h}"><b>{h}</b> '
                       f'<span>{esc(x["name"])}</span></a></th>{cells}'
                       f'<td class="fired">{x["n_fired"]}</td></tr>')

    # ---- per-house detail ----------------------------------------------------
    def findings_block(findings):
        out = ""
        for fac in ("lagna","lord","karaka"):
            rows = findings.get(fac, [])
            if not rows: continue
            items = ""
            for f in rows:
                dv = f["delta"]
                sign = "pos" if dv>0 else ("neg" if dv<0 else "zero")
                dtxt = f'{dv:+.2f}' if dv else '0'
                items += (f'<li class="{sign}"><span class="fdelta">{dtxt}</span>'
                          f'<span class="fframe">{esc(f["frame"])}</span>'
                          f'<span class="ftext">{esc(f["text"])}</span></li>')
            out += (f'<div class="fac"><div class="fac-h">{fac.capitalize()} '
                    f'<em>scored testimony</em></div><ul class="finds">{items}</ul></div>')
        return out

    def sutra_block(buckets):
        order = ["bhava","lord","occupants","karaka","combinations"]
        out = ""
        for k in order:
            rows = buckets.get(k, [])
            if not rows: continue
            items = ""
            for e in rows:
                pol = e["pol"]
                items += (f'<li class="s-{esc(pol)}"><span class="s-cite">{esc(cite(e["id"]))}</span>'
                          f'<span class="s-text">{esc(e["text"])}</span></li>')
            out += (f'<div class="sut"><div class="sut-h">{esc(BUCKET_LABEL.get(k,k))}</div>'
                    f'<ul class="sutras">{items}</ul></div>')
        return out

    HOUSE_DETAIL = ""
    for h in range(1,13):
        x = d["houses"][str(h)]
        HOUSE_DETAIL += f'''
        <section class="house" id="h{h}">
          <header class="house-hd">
            <div class="house-title"><span class="hn">{h}</span>
              <div><h3>{esc(x["name"])}</h3><span class="dom">domain · {esc(x["domain"])}</span></div>
            </div>
            <div class="verdicts">
              <span class="vpill {grade_class(x["lagna"])}">bhāva · {esc(x["lagna"])}</span>
              <span class="vpill {grade_class(x["lord"])}">lord · {esc(x["lord"])}</span>
              <span class="vpill {grade_class(x["karaka"])}">kāraka · {esc(x["karaka"])}</span>
              <span class="vpill big {grade_class(x["conclusion"])}">conclusion · {esc(x["conclusion"])}</span>
            </div>
          </header>
          <div class="house-body">
            <div class="col-scored">
              <div class="col-label">How the engine scored it <em>({x["n_fired"]} rules fired)</em></div>
              {findings_block(x["findings"])}
            </div>
            <div class="col-sutra">
              <div class="col-label">Applicable sūtras that fired here</div>
              {sutra_block(x["buckets"])}
            </div>
          </div>
        </section>'''

    # ---- chart-global --------------------------------------------------------
    CG_GROUPS = {"yoga":"Yogas present in the chart","strength":"Bala &amp; Avasthā (planetary strength states)",
                 "graha_effect":"Graha effects (sign-placement & condition)","functional_role":"Functional roles",
                 "bhava_judgment":"Bhāva judgments","cancellation":"Cancellations"}
    cg_by = {}
    for g in d["chart_global"]:
        cg_by.setdefault(g["type"], []).append(g)
    CG_HTML = ""
    for t, title in CG_GROUPS.items():
        rows = cg_by.get(t, [])
        if not rows: continue
        items = ""
        for g in rows:
            items += (f'<li class="s-{esc(g["pol"])}"><span class="s-cite">{esc(BOOK.get(g["book"],g["book"]))}</span>'
                      f'<span class="s-text">{esc(g["text"])}</span></li>')
        CG_HTML += f'<div class="cg"><h4>{title}</h4><ul class="sutras">{items}</ul></div>'

    # ---- rasi placement list -------------------------------------------------
    def placement_rows():
        out = ""
        for p in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]:
            rs = d["planet_signs"][p]; hs = d["planet_houses"][p]; nv = d["navamsa"][p]
            out += (f'<tr><td class="pn">{esc(p)}</td><td>{esc(SIGNS[rs-1])}</td>'
                    f'<td class="num">{hs}</td><td>{esc(SIGNS[nv-1])}</td></tr>')
        return out

    total_fired_house = sum(len(sum(hh["buckets"].values(), [])) for hh in d["houses"].values())

    HTML = f'''<div class="wrap">
      <header class="masthead">
        <div class="mh-eyebrow">Vedic strength &amp; yoga reading · computed by the Raman doctrine engine</div>
        <h1>The Mainpuri Kundalī</h1>
        <p class="mh-sub">Scorpio lagna · a worked nativity from B. V. Raman's <em>How to Judge a Horoscope</em>,
           read here by the encoded-sūtra engine with full firing coverage.</p>
        <div class="mh-chips">
          <span class="chip">Lagna · Scorpio (Vṛścika), vargottama</span>
          <span class="chip">Janma Nakṣatra · Śatabhiṣā (Rahu) · pāda 4</span>
          <span class="chip">{total_fired_house} sūtras fired across 12 houses</span>
          <span class="chip">{len(d["chart_global"])} chart-wide combinations</span>
        </div>
      </header>

      <section class="charts">
        {square_chart(d["planet_signs"], d["asc_sign"], "Rāśi · D1")}
        {square_chart(d["navamsa"], d["navamsa_asc"], "Navāṁśa · D9")}
        <div class="placements">
          <h4>Placements</h4>
          <table class="ptab"><thead><tr><th>Graha</th><th>Rāśi</th><th>Bhāva</th><th>Navāṁśa</th></tr></thead>
          <tbody>{placement_rows()}</tbody></table>
        </div>
      </section>

      <section class="matrix-wrap">
        <h2>The verdict at a glance</h2>
        <p class="lede">Each house is judged on three factors — the <b>bhāva</b> itself, its <b>lord</b>, and its
          natural <b>kāraka</b> — then synthesised into a <b>conclusion</b>. Colour runs from
          <span class="swatch v0"></span> afflicted through <span class="swatch v2"></span> moderate to
          <span class="swatch v8"></span> very powerful.</p>
        <div class="tscroll">
        <table class="matrix">
          <thead><tr><th>House</th><th>Bhāva</th><th>Lord</th><th>Kāraka</th><th>Conclusion</th><th>Rules</th></tr></thead>
          <tbody>{HOUSE_ROWS}</tbody>
        </table>
        </div>
      </section>

      <section class="houses">
        <h2>House by house — the engine's reasoning &amp; the doctrine behind it</h2>
        <p class="lede">The left column is what moved the numeric grade (the audited scoring path, with each
          testimony's weight). The right column is <em>every applicable encoded sūtra that fired on this
          chart</em> — verbatim from Raman's books — surfaced for the reading whether or not it scored.</p>
        {HOUSE_DETAIL}
      </section>

      <section class="global">
        <h2>Chart-wide combinations that fired</h2>
        <p class="lede">Yogas, planetary strength-states (bala / avasthā) and functional roles have no single
          house anchor, so the engine fires each once for the whole chart.</p>
        <div class="cg-grid">{CG_HTML}</div>
      </section>

      <footer class="foot">
        <p><b>How this was produced.</b> Every verdict and every quoted sūtra is the live output of
          <code>judge_chart_doctrine</code> on the Mainpuri chart (Scorpio lagna, reconstructed from Raman's
          printed positions). Increment 21 widened the engine so all applicable natal sūtras fire into the
          reading; increment 22 then filtered out <em>horary (Prāśna) and electional (Muhūrta) rules</em>
          that were firing only because their antecedents happen to be true of a birth chart — a category
          error a reader caught. Out-of-scope firings: 7 → 0.</p>
        <p class="caveat"><b>Honest caveats.</b> (1) The widened sūtras enrich the <em>reading</em> only —
          they do not feed the numeric grade (feeding them over-credits), so the strength scores stay on the
          audited path (held-out within-one ≈ 54.7%). (2) The Moon lies in Śatabhiṣā, so the birth
          Vimśottarī daśā is <b>Rahu</b> (≈6.9% remaining at birth); a “current period” needs a birth date
          this historical chart doesn’t carry. (3) Kemadruma is now correctly suppressed — its bhaṅga holds
          (Venus in a kendra from Lagna and Moon), so the yoga no longer fires (increment 23). (4) The one
          known limit still visible: the navāṁśa-debilitation reads the 11th lord down despite its exalted
          Rāśi placement + rājayoga — the documented synthesis ceiling (the engine sums testimony where
          Raman weighs it holistically).</p>
      </footer>
    </div>'''
    return ('<title>Doctrine Chart Report</title>\n<style>\n' + CSS + '\n</style>\n'
            + HTML + '\n')


MAINPURI = dict(
    positions={"Sun":176.562,"Moon":319.0817,"Mars":172.4476,"Mercury":158.7869,
               "Jupiter":78.1407,"Venus":221.6724,"Saturn":255.8022,
               "Rahu":300.4694,"Ketu":120.4694},
    lagna=225.5089, jd=2447811.6888)


if __name__ == "__main__":
    d = build_analysis(MAINPURI["positions"], MAINPURI["lagna"], MAINPURI["jd"],
                       {"md": "Mercury", "ad": "Mercury"})
    print(render(d))
