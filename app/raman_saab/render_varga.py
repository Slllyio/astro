"""Shodasavarga report rendering — deterministic, ASCII-safe text and markdown.

Usage:
    from app.raman_saab.render_varga import to_text, to_markdown
    print(to_text(build_shodasavarga_report(chart)))
"""
from __future__ import annotations

from app.raman_saab.judges.varga_judge import (
    PillarReading, ShodasavargaReport, VargaReading)

_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _pillar_line(p: PillarReading) -> str:
    house = f" house {p.varga_house}" if p.varga_house is not None else ""
    vt = " [vargottama]" if p.vargottama else ""
    return (f"{p.planet} in {_SIGNS[p.varga_sign - 1]}{house} "
            f"({p.dignity}){vt}")


def _reading_lines(r: VargaReading) -> list[str]:
    out = [f"D{r.n} {r.name} - {r.domain} [{r.source.work}:{r.source.line}]"]
    out.append(f"    lagna: {_SIGNS[r.chart.lagna_sign - 1]}"
               + ("  (vargottama lagna)" if r.chart.lagna_vargottama and r.n == 9 else ""))
    out.append(f"    lagna lord: {_pillar_line(r.lagna_lord)}")
    for k in r.karakas:
        out.append(f"    karaka:     {_pillar_line(k)}")
    if r.n != 2:
        occ = []
        if r.benefics_on_lagna:
            occ.append("benefics on lagna: " + ",".join(r.benefics_on_lagna))
        if r.malefics_on_lagna:
            occ.append("malefics on lagna: " + ",".join(r.malefics_on_lagna))
        if occ:
            out.append("    " + " | ".join(occ))
        out.append(f"    kendras: benefics [{','.join(r.benefics_in_kendra) or '-'}]"
                   f"  malefics [{','.join(r.malefics_in_kendra) or '-'}]")
    for key, value in r.notes:
        out.append(f"    {key}: {value}")
    out.append(f"    status: {r.status.upper()}")
    return out


def to_text(report: ShodasavargaReport) -> str:
    out: list[str] = ["=== SHODASAVARGA REPORT (16 divisional charts) ==="]
    for r in report.readings:
        out.append("")
        out.extend(_reading_lines(r))
    out.append("")
    out.append("--- Vargavisesha (own-varga counts over the saptavarga; GBB-3:356) ---")
    for v in report.vargavisesha:
        label = v.label or "-"
        vargas = ",".join(v.own_vargas) or "-"
        out.append(f"    {v.planet:8} {v.own_varga_count}x [{vargas}]  {label}")
    return "\n".join(out)


def to_markdown(report: ShodasavargaReport) -> str:
    out: list[str] = ["# Shodasavarga report", ""]
    out.append("| D | name | domain | lagna | lagna lord | status |")
    out.append("|---|------|--------|-------|------------|--------|")
    for r in report.readings:
        lord = _pillar_line(r.lagna_lord)
        out.append(f"| D{r.n} | {r.name} | {r.domain} | {_SIGNS[r.chart.lagna_sign - 1]} "
                   f"| {lord} | {r.status} |")
    out.append("")
    out.append("## Per-division detail")
    for r in report.readings:
        out.append("")
        out.append(f"### D{r.n} {r.name} [{r.source.work}:{r.source.line}]")
        for line in _reading_lines(r)[1:]:
            out.append("- " + line.strip())
    out.append("")
    out.append("## Vargavisesha (GBB-3:356)")
    out.append("")
    out.append("| planet | own vargas | count | amsa |")
    out.append("|--------|-----------|-------|------|")
    for v in report.vargavisesha:
        out.append(f"| {v.planet} | {','.join(v.own_vargas) or '-'} "
                   f"| {v.own_varga_count} | {v.label or '-'} |")
    return "\n".join(out)
