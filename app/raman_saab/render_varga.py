"""Shodasavarga report rendering — deterministic, ASCII-safe text, markdown, and JSON.

Usage:
    from app.raman_saab.render_varga import to_text, to_markdown, to_dict
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
    # A `neutral` status is two different findings wearing one word (varga_judge.
    # _neutral_kind): "contested" = both poles fired and cancelled, "silent" = neither
    # fired. Printing the bare word told the reader the division had nothing to say even
    # when it had two things to say that disagreed.
    kind = f"  ({getattr(r, 'neutral_kind', '')})" if getattr(r, "neutral_kind", "") else ""
    out.append(f"    status: {r.status.upper()}{kind}")
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


def _sign_name(sign: int) -> str:
    return _SIGNS[sign - 1]


def _pillar_dict(p: PillarReading) -> dict:
    return {"planet": p.planet, "role": p.role, "sign": p.varga_sign,
            "sign_name": _sign_name(p.varga_sign), "house": p.varga_house,
            "dignity": p.dignity, "vargottama": p.vargottama}


def _reading_dict(r: VargaReading) -> dict:
    return {
        "n": r.n, "name": r.name, "domain": r.domain,
        "related_houses": list(r.related_houses),
        "citation": f"{r.source.work}:{r.source.line}",
        "lagna": {"sign": r.chart.lagna_sign, "sign_name": _sign_name(r.chart.lagna_sign),
                  "lord": r.chart.lagna_lord, "vargottama": r.chart.lagna_vargottama},
        "lagna_lord": _pillar_dict(r.lagna_lord),
        "karakas": [_pillar_dict(k) for k in r.karakas],
        "benefics_on_lagna": list(r.benefics_on_lagna),
        "malefics_on_lagna": list(r.malefics_on_lagna),
        "benefics_in_kendra": list(r.benefics_in_kendra),
        "malefics_in_kendra": list(r.malefics_in_kendra),
        "status": r.status,
        "neutral_kind": getattr(r, "neutral_kind", ""),
        "notes": {k: v for k, v in r.notes},
    }


def to_dict(report: ShodasavargaReport) -> dict:
    """JSON-serialisable form of the whole report (for the HTTP surface). The D1 lagna
    is surfaced once at the top; every division carries its own lagna + citation."""
    d1 = report.readings[0].chart
    return {
        "lagna": {"sign": d1.lagna_sign, "sign_name": _sign_name(d1.lagna_sign),
                  "lord": d1.lagna_lord},
        "readings": [_reading_dict(r) for r in report.readings],
        "vargavisesha": [
            {"planet": v.planet, "own_varga_count": v.own_varga_count,
             "own_vargas": list(v.own_vargas), "label": v.label,
             "citation": f"{v.source.work}:{v.source.line}"}
            for v in report.vargavisesha],
    }


def to_markdown(report: ShodasavargaReport) -> str:
    out: list[str] = ["# Shodasavarga report", ""]
    out.append("| D | name | domain | lagna | lagna lord | status |")
    out.append("|---|------|--------|-------|------------|--------|")
    for r in report.readings:
        lord = _pillar_line(r.lagna_lord)
        out.append(f"| D{r.n} | {r.name} | {r.domain} | {_SIGNS[r.chart.lagna_sign - 1]} "
                   f"| {lord} | {r.status}"
                   + (f" ({r.neutral_kind})" if getattr(r, "neutral_kind", "") else "")
                   + " |")
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
