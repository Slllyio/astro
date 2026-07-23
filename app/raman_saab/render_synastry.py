"""Text renderer for the two-chart synastry (`judges/two_chart_synastry.py`).

REPORT-ONLY, nets no verdict — the header says so. Emits UTF-8.

Usage:
    from app.raman_saab.render_synastry import to_text
    print(to_text(build_two_chart_synastry(chart_a, "husband", chart_b, "wife")))
"""
from __future__ import annotations

from app.raman_saab.judges.saptamsa_reading import Tagged
from app.raman_saab.judges.two_chart_synastry import KujaProfile, TwoChartSynastry


def _tag(t: Tagged) -> str:
    c = f" ({t.cite})" if t.cite else ""
    return f"[{t.provenance}]{c} {t.text}"


def _kuja_line(k: KujaProfile) -> str:
    if not k.strength:
        return f"  [{k.role}]  no Kuja doṣa"
    mit = " (mitigated)" if k.mitigated else ""
    where = (f"Mars in the {k.house_from_lagna}th from Lagna" if k.house_from_lagna
             else f"Mars in a Kuja house from {'/'.join(k.refs)}")
    return f"  [{k.role}]  Kuja doṣa on {', '.join(k.refs)} ({where}){mit}"


def _section(title: str, items: tuple[Tagged, ...], empty: str) -> list[str]:
    out = [f"-- {title} --"]
    out.extend(f"  - {_tag(t)}" for t in items) if items else out.append(f"  ({empty})")
    return out


def to_text(s: TwoChartSynastry) -> str:
    L: list[str] = []
    L.append("=" * 76)
    L.append(f"TWO-CHART SYNASTRY  —  {s.role_a} × {s.role_b}  (report-only, nets no verdict)")
    L.append("=" * 76)
    for n in s.notes:
        L.append(f"* {_tag(n)}")
    L.append("")
    L.append("-- KUJA (MANGAL) DOṢA --")
    L.append(_kuja_line(s.kuja_a))
    L.append(_kuja_line(s.kuja_b))
    for t in s.kuja_comparison:
        L.append(f"  - {_tag(t)}")
    L.append("")
    L.extend(_section("PLANET OVERLAY (one's benefics in the other's houses)", s.overlays,
                      "no notable benefic overlay"))
    L.append("")
    L.extend(_section("SUN-MOON", s.sun_moon, "no notable Moon-contact"))
    L.append("")
    L.extend(_section("CROSS-POINTS", s.cross_points, "no notable cross-point"))
    L.append("=" * 76)
    return "\n".join(L)
