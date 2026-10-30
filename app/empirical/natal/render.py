"""Natal decode → JSON dict and markdown, framing first, nothing omitted.

Mirrors ``app/empirical/engine/report.py``: a ``render()`` that returns the
full structured dict and a ``to_markdown()`` built from it that loses nothing.
The framing paragraph leads every surface — the repo's REPORT COMPLETENESS
rule works both ways here: every computed field is shown, and no shown field
escapes the disclosure that this is tradition, not measurement.

Usage:
    from app.empirical.natal.render import render, to_markdown
    payload = render(decode(assemble_chart(moment)))
    text = to_markdown(decode(assemble_chart(moment)))
"""

from __future__ import annotations

from typing import Any, Final

from app.empirical.natal.chart import ASCENDANT_WEIGHT, BALANCE_WEIGHTS, NatalChart
from app.empirical.natal.decoder import NatalDecode
from app.empirical.natal.lexicon import SIGNS, TRADITION_BANNER

__all__ = ["NATAL_FRAMING", "render", "to_markdown"]

NATAL_FRAMING: Final[str] = (
    "This decode reports what the mainstream Western tropical tradition "
    "associates with these placements. It describes a symbolic tradition; it "
    "is not a validated measurement. This project's own tournament tested "
    "natal-chart features against profession on 15,668 registry-timed births, "
    "and against event timing, and found no predictive advantage over "
    "birthplace and birth date alone. This is not a prediction about you."
)

_FACET_TITLES: Final[dict[str, str]] = {
    "personality": "Personality",
    "characteristics": "Characteristics",
    "attitude": "Attitude",
    "aptitude": "Aptitude",
    "intelligence": "Intelligence (cognitive style)",
    "work_style": "Work style",
    "work_area": "Work area",
}


def _chart_dict(chart: NatalChart) -> dict[str, Any]:
    """Every computed chart field, structurally complete."""
    moment = chart.moment
    houses = None
    if chart.houses is not None:
        houses = {
            "system": chart.houses.system,
            "cusps": list(chart.houses.cusps),
            "ascendant": chart.houses.ascendant,
            "ascendant_sign": SIGNS[int(chart.houses.ascendant // 30.0)],
            "midheaven": chart.houses.midheaven,
            "midheaven_sign": SIGNS[int(chart.houses.midheaven // 30.0)],
            "armc": chart.houses.armc,
            "vertex": chart.houses.vertex,
        }
    return {
        "moment": {
            "year": moment.year,
            "month": moment.month,
            "day": moment.day,
            "hour": moment.hour,
            "minute": moment.minute,
            "latitude": moment.latitude,
            "longitude": moment.longitude,
            "tz_offset": moment.tz_offset,
            "time_known": moment.time_known,
        },
        "jd_ut": chart.jd_ut,
        "house_system_requested": chart.house_system,
        "positions": {
            body: {
                "longitude": pos.longitude,
                "sign": SIGNS[pos.sign_index],
                "degree_in_sign": pos.degree_in_sign,
                "is_retrograde": pos.is_retrograde,
                "latitude": pos.latitude,
                "distance_au": pos.distance_au,
                "speed_longitude": pos.speed_longitude,
                "speed_latitude": pos.speed_latitude,
            }
            for body, pos in chart.positions.items()
        },
        "south_node": chart.south_node,
        "south_node_sign": SIGNS[int(chart.south_node // 30.0)],
        "houses": houses,
        "houses_missing_reason": chart.houses_missing_reason,
        "house_of_body": dict(chart.house_of_body) if chart.house_of_body is not None else None,
        "aspects": [
            {
                "body_a": a.body_a,
                "body_b": a.body_b,
                "aspect": a.aspect,
                "angle": a.angle,
                "separation": a.separation,
                "orb": a.orb,
                "allowed_orb": a.allowed_orb,
                "applying": a.applying,
            }
            for a in chart.aspects
        ],
        "element_counts": dict(chart.element_counts),
        "modality_counts": dict(chart.modality_counts),
        "balance_weights": {**BALANCE_WEIGHTS, "Ascendant": ASCENDANT_WEIGHT},
        "chart_ruler": chart.chart_ruler,
        "dominant_planets": list(chart.dominant_planets),
        "moon_sign_ambiguous": chart.moon_sign_ambiguous,
    }


def render(decoded: NatalDecode) -> dict[str, Any]:
    """The complete structured payload. Framing and banner come first."""
    return {
        "framing": NATAL_FRAMING,
        "tradition_banner": TRADITION_BANNER,
        "chart": _chart_dict(decoded.chart),
        "facets": [
            {
                "facet": section.facet,
                "title": _FACET_TITLES[section.facet],
                "degraded": section.degraded,
                "notes": list(section.notes),
                "statements": [
                    {
                        "text": s.text,
                        "source": s.source,
                        "provenance": s.provenance,
                        "basis": list(s.basis),
                    }
                    for s in section.statements
                ],
            }
            for section in decoded.facets
        ],
        "disclosures": list(decoded.disclosures),
    }


def to_markdown(decoded: NatalDecode) -> str:
    """Markdown surface carrying everything the JSON carries."""
    data = render(decoded)
    chart = data["chart"]
    lines: list[str] = []

    lines.append("# Natal decode — Western tropical")
    lines.append("")
    lines.append(f"> {data['framing']}")
    lines.append("")
    lines.append(f"> {data['tradition_banner']}")
    lines.append("")

    m = chart["moment"]
    time_str = f"{m['hour']:02d}:{m['minute']:02d}" if m["time_known"] else "unknown (cast at local noon)"
    lines.append(
        f"Born {m['year']:04d}-{m['month']:02d}-{m['day']:02d} {time_str}, "
        f"lat {m['latitude']}, lon {m['longitude']}, UTC{m['tz_offset']:+g} "
        f"(JD UT {chart['jd_ut']:.5f})."
    )
    lines.append("")

    lines.append("## Planets at birth")
    lines.append("")
    lines.append("| Body | Longitude | Sign | In sign | Motion | Speed (deg/day) | Ecl. lat | Distance (AU) |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for body, pos in chart["positions"].items():
        motion = "retrograde" if pos["is_retrograde"] else "direct"
        lines.append(
            f"| {body} | {pos['longitude']:.4f} | {pos['sign']} | {pos['degree_in_sign']:.2f} | "
            f"{motion} | {pos['speed_longitude']:+.4f} | {pos['latitude']:+.4f} | {pos['distance_au']:.4f} |"
        )
    lines.append(f"| SouthNode | {chart['south_node']:.4f} | {chart['south_node_sign']} | — | derived | — | — | — |")
    lines.append("")

    lines.append(f"## Houses ({chart['house_system_requested']})")
    lines.append("")
    if chart["houses"] is None:
        lines.append(f"Not computed: {chart['houses_missing_reason']}.")
    else:
        h = chart["houses"]
        lines.append(
            f"Ascendant {h['ascendant']:.4f} ({h['ascendant_sign']}), "
            f"Midheaven {h['midheaven']:.4f} ({h['midheaven_sign']}), "
            f"ARMC {h['armc']:.4f}, Vertex {h['vertex']:.4f}."
        )
        lines.append("")
        lines.append("| House | Cusp | Occupants |")
        lines.append("|---|---|---|")
        occupants: dict[int, list[str]] = {}
        for body, house in chart["house_of_body"].items():
            occupants.setdefault(house, []).append(body)
        for i, cusp in enumerate(h["cusps"], start=1):
            names = ", ".join(occupants.get(i, [])) or "—"
            lines.append(f"| {i} | {cusp:.4f} | {names} |")
    lines.append("")

    lines.append("## Aspects")
    lines.append("")
    if not chart["aspects"]:
        lines.append("None within the configured orbs.")
    else:
        lines.append("| Bodies | Aspect | Separation | Orb | Allowed | Applying |")
        lines.append("|---|---|---|---|---|---|")
        for a in chart["aspects"]:
            applying = "—" if a["applying"] is None else ("yes" if a["applying"] else "no")
            lines.append(
                f"| {a['body_a']}–{a['body_b']} | {a['aspect']} ({a['angle']:.0f} deg) | "
                f"{a['separation']:.2f} | {a['orb']:.2f} | {a['allowed_orb']:.2f} | {applying} |"
            )
    lines.append("")

    lines.append("## Balance and emphasis")
    lines.append("")
    lines.append(f"Elements (weighted): {chart['element_counts']}")
    lines.append(f"Modalities (weighted): {chart['modality_counts']}")
    lines.append(f"Weights: {chart['balance_weights']}")
    lines.append(f"Chart ruler: {chart['chart_ruler'] or '— (no houses)'}")
    lines.append(f"Dominant planets: {', '.join(chart['dominant_planets'])}")
    lines.append(f"Moon sign ambiguous: {'yes' if chart['moon_sign_ambiguous'] else 'no'}")
    lines.append("")

    for section in data["facets"]:
        lines.append(f"## {section['title']}")
        lines.append("")
        if section["degraded"]:
            lines.append("*Degraded — see notes below.*")
            lines.append("")
        for stmt in section["statements"]:
            lines.append(f"- {stmt['text']} — *({stmt['source']})*")
        for note in section["notes"]:
            lines.append(f"- _Note: {note}_")
        lines.append("")

    lines.append("## Disclosures")
    lines.append("")
    for d in data["disclosures"]:
        lines.append(f"- {d}")
    lines.append("")

    return "\n".join(lines)
