"""Event-level profile generator — full transit context per dated event.

For each dated event of a person:

  - Event class, date, age, source
  - Active MD lord at event_jd + its natal house + houses it rules
  - Active AD lord at event_jd + its natal house + houses it rules
  - Full transit of 9 planets at the event moment:
      * sign, degree-in-sign, retrograde
      * transit-house in the person's natal chart
      * the transit nakshatra
      * which natal houses each planet is the lord of
      * classical doctrine flag: is the slow-mover transit landing in
        a house it is itself natal lord of (the "self-trigger" pattern)

Built on top of the existing `event_transits.parquet` Silver table plus
the chart computations from person_profile.

Usage:
    from app.medini.ml.event_profile import events_for_person, format_events
    events = events_for_person("ADB:2411626.0931")
    print(format_events(events))
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

import pandas as pd
import swisseph as swe

from app.core.ephemeris_engine import ZODIAC_SIGNS
from app.core.nakshatra import NAKSHATRAS, nakshatra_for_longitude
from app.medini.ml.person_profile import (
    _GRAHAS, _SIGN_RULERS, _houses_ruled_by_planet,
)

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")

# Trikona (auspicious) and Dusthana (difficult) houses.
_TRIKONA: Final[frozenset[int]] = frozenset({1, 5, 9})
_DUSTHANA: Final[frozenset[int]] = frozenset({6, 8, 12})


def events_for_person(
    person_id: str, data_dir: Path = DEFAULT_DATA_DIR,
    include_cross_corpus: bool = True,
) -> list[dict]:
    """Build the comprehensive list of events with full transit context.

    If ``include_cross_corpus`` is True (default), also pulls events from
    sibling person_ids in other corpora via resolved_persons.parquet.
    The natal chart used for "natal house" computation comes from the
    ``person_id`` parameter — that's the canonical anchor.
    """
    persons = pd.read_parquet(
        data_dir / "persons.parquet", columns=["person_id", "name"],
    )
    pname_row = persons[persons["person_id"] == person_id]
    if len(pname_row) == 0:
        raise KeyError(f"No person with id {person_id!r}")
    pname = str(pname_row.iloc[0]["name"])

    charts = pd.read_parquet(
        data_dir / "charts.parquet",
        columns=["person_id", "asc_sign"],
    )
    chart_row = charts[charts["person_id"] == person_id]
    if len(chart_row) == 0:
        raise KeyError(f"No chart for {person_id!r}")
    asc_sign = int(chart_row.iloc[0]["asc_sign"])

    # Resolve sibling person_ids via cross-corpus dedup.
    ids_to_pull: set[str] = {person_id}
    if include_cross_corpus:
        resolved = pd.read_parquet(
            data_dir / "resolved_persons.parquet",
            columns=["source_ids", "n_corpora"],
        )
        for _, r in resolved.iterrows():
            sids = list(r["source_ids"])
            if person_id in sids:
                ids_to_pull.update(sids)
                break

    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    events = events[events["person_id"].isin(ids_to_pull)].copy()

    transits = pd.read_parquet(data_dir / "event_transits.parquet")
    transits = transits[transits["person_id"].isin(ids_to_pull)]

    out: list[dict] = []
    for _, e in events.iterrows():
        e_id = int(e["event_id"])
        md_lord = e.get("md_lord_at_event")
        ad_lord = e.get("ad_lord_at_event")
        md_lord_str = str(md_lord) if pd.notna(md_lord) else None
        ad_lord_str = str(ad_lord) if pd.notna(ad_lord) else None

        # Per-planet transit rows for this event.
        ev_transits = transits[transits["event_id"] == e_id]
        planets_at_event: list[dict] = []
        for _, t in ev_transits.iterrows():
            graha = str(t["transit_planet"])
            t_lon = float(t["transit_lon"])
            t_sign = int(t["transit_sign"])
            # Re-derive transit_natal_house using the CANONICAL chart's
            # asc_sign so cross-corpus events report consistent values
            # (the source event_transits row's natal_house was computed
            # using whichever chart that event_id was tagged with).
            t_house = ((t_sign - asc_sign) % 12) + 1
            nak = nakshatra_for_longitude(t_lon)
            houses_ruled = _houses_ruled_by_planet(graha, asc_sign)
            in_own = t_house in houses_ruled
            planets_at_event.append({
                "planet": graha,
                "transit_lon": t_lon,
                "transit_sign": t_sign,
                "transit_sign_name": ZODIAC_SIGNS[t_sign - 1],
                "degree_in_sign": t_lon - (t_sign - 1) * 30.0,
                "transit_natal_house": t_house,
                "transit_nakshatra": NAKSHATRAS[nak["index"]],
                "transit_pada": nak["pada"],
                "transit_nakshatra_lord": nak["lord"],
                "natal_houses_ruled": list(houses_ruled),
                "is_slow_mover": bool(t["is_slow_mover"]),
                "is_retrograde": bool(t["is_retrograde"]),
                "in_own_lord_house": in_own,
                "in_trikona": t_house in _TRIKONA,
                "in_dusthana": t_house in _DUSTHANA,
            })

        out.append({
            "event_id": e_id,
            "person_name": pname,
            "event_class": str(e["event_class"]),
            "event_root": (
                str(e["event_class"])
                if "event_root" not in e else str(e.get("event_root"))
            ),
            "event_date": (
                str(e["event_date"]) if pd.notna(e["event_date"]) else None
            ),
            "event_jd": (
                float(e["event_jd"]) if pd.notna(e["event_jd"]) else None
            ),
            "age_at_event_years": (
                float(e["age_at_event_years"])
                if pd.notna(e["age_at_event_years"]) else None
            ),
            "source": str(e["source"]),
            "active_md_lord": md_lord_str,
            "active_md_lord_natal_houses_ruled": list(
                _houses_ruled_by_planet(md_lord_str, asc_sign)
            ) if md_lord_str else [],
            "md_elapsed_years": (
                float(e["md_elapsed_years"])
                if pd.notna(e["md_elapsed_years"]) else None
            ),
            "active_ad_lord": ad_lord_str,
            "active_ad_lord_natal_houses_ruled": list(
                _houses_ruled_by_planet(ad_lord_str, asc_sign)
            ) if ad_lord_str else [],
            "ad_elapsed_years": (
                float(e["ad_elapsed_years"])
                if pd.notna(e["ad_elapsed_years"]) else None
            ),
            "transit_planets": planets_at_event,
        })
    out.sort(key=lambda ev: ev["event_jd"] or float("inf"))
    return out


def format_events(events: list[dict]) -> str:
    """Render the event list as a structured human-readable report."""
    lines: list[str] = []
    add = lines.append
    if not events:
        return "(no events)"
    person = events[0]["person_name"]
    add("=" * 96)
    add(f"  EVENTS — {person.upper()}")
    add("=" * 96)
    add(f"  Total events: {len(events)}")
    for ev in events:
        add("")
        add("-" * 96)
        date_str = ev["event_date"] or "(undated)"
        age_str = (
            f"age {ev['age_at_event_years']:.1f}"
            if ev["age_at_event_years"] is not None else "age unknown"
        )
        add(f"  Event #{ev['event_id']} — {ev['event_class'].upper()}  "
            f"on {date_str}  ({age_str}, source: {ev['source']})")
        add("-" * 96)
        md = ev["active_md_lord"]
        ad = ev["active_ad_lord"]
        if md:
            md_houses = (
                ",".join(str(h) for h in ev["active_md_lord_natal_houses_ruled"])
                if ev["active_md_lord_natal_houses_ruled"] else "—"
            )
            md_elap = ev["md_elapsed_years"]
            add(f"    Active Dasha    : MD = {md} (natal lord of houses {md_houses}; "
                f"running {md_elap:.1f}y into MD)")
            if ad:
                ad_houses = (
                    ",".join(str(h) for h in ev["active_ad_lord_natal_houses_ruled"])
                    if ev["active_ad_lord_natal_houses_ruled"] else "—"
                )
                ad_elap = ev["ad_elapsed_years"]
                add(f"                      AD = {ad} (natal lord of houses {ad_houses}; "
                    f"running {ad_elap:.1f}y into AD)")
        else:
            add("    Active Dasha    : — (event_date not within natal Vimshottari cycle)")

        if not ev["transit_planets"]:
            add("    No transit data (event_date missing/out-of-cycle).")
            continue

        add("")
        add(f"    {'TRANSITS AT THIS EVENT (sidereal Lahiri):':<82}")
        add(f"    {'Planet':<8} {'Sign':<12} {'Deg':>7} {'House':>5} "
            f"{'Rules':<8} {'Nakshatra':<18} {'Pada':>4} {'NkLord':<8} "
            f"{'Slow':>4} {'Rx':>3} {'Self':>4}")
        add(f"    {'-'*8} {'-'*12} {'-'*7} {'-'*5} {'-'*8} {'-'*18} {'-'*4} "
            f"{'-'*8} {'-'*4} {'-'*3} {'-'*4}")
        # Sort: slow movers first, then by graha order.
        graha_order = {g: i for i, g in enumerate(_GRAHAS)}
        sorted_transits = sorted(
            ev["transit_planets"],
            key=lambda p: (not p["is_slow_mover"], graha_order.get(p["planet"], 99)),
        )
        for t in sorted_transits:
            rules = ",".join(str(h) for h in t["natal_houses_ruled"]) or "—"
            slow = "Y" if t["is_slow_mover"] else ""
            rx = "Rx" if t["is_retrograde"] else ""
            self_trig = "*" if t["in_own_lord_house"] else ""
            add(f"    {t['planet']:<8} {t['transit_sign_name']:<12} "
                f"{t['degree_in_sign']:6.2f}° {t['transit_natal_house']:>5} "
                f"{rules:<8} {t['transit_nakshatra']:<18} {t['transit_pada']:>4} "
                f"{t['transit_nakshatra_lord']:<8} {slow:>4} {rx:>3} {self_trig:>4}")
        # Highlight self-trigger if any.
        triggers = [
            t for t in ev["transit_planets"]
            if t["in_own_lord_house"] and t["is_slow_mover"]
        ]
        if triggers:
            add("")
            add("    >> Self-trigger pattern detected:")
            for t in triggers:
                rules = ",".join(str(h) for h in t["natal_houses_ruled"])
                add(f"      - {t['planet']} (natal lord of houses {rules}) "
                    f"transiting natal house {t['transit_natal_house']} "
                    f"— activating its own ruled domain")

    return "\n".join(lines)
