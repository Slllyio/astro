"""Life Timeline + timing strength meter (Phase D).

The Vimśottarī mahādaśā sequence is fixed the moment the Moon's nakṣatra is
known, so the WHOLE life — childhood, the present, and the years ahead — can be
reconstructed deterministically from the birth balance alone (lord₀ + the years
that remained at birth), which `dasha_now` already computes. `md_judgments` only
looks forward from the present; this reducer fills in the past eras too.

For each mahādaśā it emits an **era** — age range, calendar span, the life
areas its lord governs (owned houses ∪ natural-kāraka bhāvas, mapped to plain
areas), a tone from the lord's real strength, and whether it is past / current /
future. The current era also carries a **cycle label** — Building / Peak /
Closing / Handover — from how far the running daśā has progressed (the timing
strength meter, replacing the flat "Active").

Pure, deterministic, fail-soft. No probability — the sequence and the dates are
exact Vimśottarī arithmetic; the tone is the engine's own strength grade.
"""
from __future__ import annotations

from typing import Any, Mapping

from app.integration.dasha_now import _DASHA_YEARS, _dasha_order_from
from app.reading._planet_lexicon import strength_index, well_placed
from app.reading.sequences.vimshottari_md import _NATURAL_KARAKA_BHAVAS

# life-area word per house (first clause of proforma._HOUSE_LIFE_AREA, kept
# local so this module doesn't import the orchestrator).
_HOUSE_AREA: dict[int, str] = {
    1: "self & vitality", 2: "wealth & family", 3: "courage & initiative",
    4: "home & contentment", 5: "children & creativity", 6: "work & health",
    7: "marriage & partnership", 8: "change & the unexpected",
    9: "fortune & higher learning", 10: "career & standing",
    11: "gains & fulfilment", 12: "expenditure & release",
}


def _era_theme(lord: str, functional: Mapping[str, dict[str, Any]]) -> list[str]:
    """The life areas a mahādaśā lord activates — its owned houses plus its
    natural-kāraka bhāvas, mapped to plain areas (deduped, ordered, capped)."""
    houses: list[int] = []
    houses += list((functional.get(lord) or {}).get("houses_ruled") or [])
    houses += list(_NATURAL_KARAKA_BHAVAS.get(lord, ()))
    seen: set[str] = set()
    areas: list[str] = []
    for h in houses:
        a = _HOUSE_AREA.get(h)
        if a and a not in seen:
            seen.add(a)
            areas.append(a)
    return areas[:4]


def _tone(lord: str, idx: Mapping[str, dict[str, Any]]) -> str:
    row = idx.get(lord)
    if not row:
        return "mixed"
    w = well_placed(row.get("dignity"), row.get("composite"), bool(row.get("combust")))
    return "favourable" if w is True else "challenging" if w is False else "mixed"


def _cycle_label(frac: float) -> str:
    """Where the running daśā stands in its own arc (the timing strength meter)."""
    if frac < 0.15:
        return "Building"
    if frac < 0.70:
        return "Peak"
    if frac < 0.90:
        return "Closing"
    return "Handover"


def build_life_timeline(reading: Mapping[str, Any],
                       extras: Mapping[str, Any]) -> dict[str, Any]:
    """Reconstruct the full-life mahādaśā sequence + the current cycle label.
    → {} on failure (needs dasha_now.birth_balance)."""
    try:
        dn = extras.get("dasha_now") or {}
        bb = dn.get("birth_balance") or {}
        md_now = dn.get("md") or {}
        lord0 = bb.get("md_lord")
        if not lord0 or lord0 not in _DASHA_YEARS:
            return {}
        # balance remaining at birth = the first (partial) MD's end age.
        end0 = bb.get("age_at_end_years")
        if end0 is None:
            return {}
        end0 = float(end0)
        age_now = float(md_now.get("age_now_years") or 0.0)

        # calendar anchor: derive the birth year from the running MD's real
        # start date + the age it began (best-effort; None if unavailable).
        birth_year: int | None = None
        sd = md_now.get("start_date") or ""
        if sd[:4].isdigit() and md_now.get("age_at_start_years") is not None:
            birth_year = round(int(sd[:4]) - float(md_now["age_at_start_years"]))

        idx = strength_index(extras.get("planet_strength"))
        functional = {f["planet"]: f for f in
                      ((extras.get("classical_factors") or {}).get("functional") or [])
                      if isinstance(f, dict) and f.get("planet")}

        order = _dasha_order_from(lord0)
        eras: list[dict[str, Any]] = []
        age = 0.0
        for i, lord in enumerate(order):
            span = end0 if i == 0 else float(_DASHA_YEARS[lord])
            a_start, a_end = age, age + span
            status = ("current" if a_start <= age_now < a_end
                      else "past" if a_end <= age_now else "future")
            era: dict[str, Any] = {
                "lord": lord,
                "age_start": round(a_start),
                "age_end": round(a_end),
                "year_start": (birth_year + round(a_start)) if birth_year else None,
                "year_end": (birth_year + round(a_end)) if birth_year else None,
                "areas": _era_theme(lord, functional),
                "tone": _tone(lord, idx),
                "status": status,
            }
            if status == "current":
                frac = float((dn.get("ad") or {}).get("md_progress_fraction") or 0.0)
                era["cycle"] = _cycle_label(frac)
                era["progress_pct"] = round(frac * 100)
            eras.append(era)
            age = a_end

        current = next((e for e in eras if e["status"] == "current"), None)
        return {
            "eras": eras,
            "current": current,
            "note": (
                "Your whole-life mahādaśā sequence, fixed by the Moon's "
                "nakṣatra at birth and reconstructed exactly (Vimśottarī). The "
                "areas are what each period's lord governs; the tone is that "
                "planet's strength — not a forecast of events."
            ),
        }
    except Exception:  # noqa: BLE001 — never block a reading
        return {}
