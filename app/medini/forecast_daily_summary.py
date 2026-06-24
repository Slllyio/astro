"""Per-day prose summary generation for the multi-day forecast.

Combines all the events on a single date into one short paragraph that
synthesizes the day's "character": which planet dominates, which spheres
of life are touched, whether the day is heavy/light/transition.

Two paths:

* **LLM path** (when an `LLMClient` is provided): builds a structured
  prompt from the day's events + their severity + their domains, asks
  the LLM for a 2-3 sentence synthesis. Returns immediately on transport
  failure (treats it as fallback).

* **Deterministic path** (default): assembles a templated sentence from
  the same inputs — not as fluent but always available, always cheap,
  never 500s. Pinned to specific phrasings so the deterministic summary
  is testable.

The summary attaches per-day to the forecast `by_day` dict; the route
layer turns it on via `include_daily_summary=true`.
"""
from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from app.llm.client import LLMClient, OllamaUnavailable
from app.medini.forecast_cache import (
    cached_call,
    daily_summary_key,
    get_daily_summary_cache,
)
from app.medini.forecast_domains import DOMAINS

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Day-level feature extraction                                                 #
# --------------------------------------------------------------------------- #

def _dominant_domain(events: list[dict[str, Any]]) -> str | None:
    """The most-touched domain across the day's events, or None."""
    counter: Counter[str] = Counter()
    for e in events:
        for d in e.get("domains", []):
            counter[d] += 1
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def _peak_severity(events: list[dict[str, Any]]) -> int:
    """Max severity across the day; 0 if no events / no severity attached."""
    return max((e.get("severity", 0) for e in events), default=0)


def _heaviest_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The event with the highest severity (ties broken by JD)."""
    if not events:
        return None
    return max(events, key=lambda e: (e.get("severity", 0), -e["jd"]))


def _event_type_counts(events: list[dict[str, Any]]) -> Counter[str]:
    return Counter(e["type"] for e in events)


# --------------------------------------------------------------------------- #
# Deterministic summary                                                        #
# --------------------------------------------------------------------------- #

# Tone-by-severity mapping. Bands match forecast_severity.severity_band.
_INTENSITY_OPENER: dict[str, str] = {
    "red":    "A heavy day:",
    "orange": "A notable day:",
    "yellow": "A moderate day:",
    "green":  "A light day:",
}


def deterministic_daily_summary(events: list[dict[str, Any]]) -> str:
    """Build a 1-2 sentence templated summary from the day's events.

    Always returns a non-empty string — even an empty event list gets a
    "nothing scheduled" sentence so the UI doesn't crash on missing data.
    """
    if not events:
        return "No mundane events scheduled."
    peak = _peak_severity(events)
    band = (
        "red" if peak >= 9 else "orange" if peak >= 7
        else "yellow" if peak >= 5 else "green"
    )
    opener = _INTENSITY_OPENER[band]
    heaviest = _heaviest_event(events)
    type_counts = _event_type_counts(events)

    # First sentence: opener + the headline event
    head_desc = (heaviest or {}).get("description", "an event")
    sentences = [f"{opener} {head_desc}."]

    # Second sentence: type count summary if more than one event
    if len(events) > 1:
        parts = [
            f"{n} {t.lower().replace('_', ' ')}{'s' if n != 1 else ''}"
            for t, n in type_counts.most_common()
        ]
        sentences.append(f"In total: {', '.join(parts)}.")

    # Third sentence (optional): dominant mundane domain
    dominant = _dominant_domain(events)
    if dominant:
        meta = DOMAINS.get(dominant)
        label = meta.label if meta else dominant
        sentences.append(f"Dominant sphere: {label}.")

    return " ".join(sentences)


# --------------------------------------------------------------------------- #
# LLM-backed summary                                                           #
# --------------------------------------------------------------------------- #

def _build_llm_prompt(date: str, events: list[dict[str, Any]]) -> str:
    """Compact, structured prompt — keeps LLM output focused on synthesis."""
    lines = [
        f"Date: {date}",
        f"Events ({len(events)}):",
    ]
    for e in events:
        sev = e.get("severity")
        bits = [e["type"]]
        if sev is not None:
            bits.append(f"sev={sev}/10")
        if e.get("planet"):
            bits.append(f"planet={e['planet']}")
        elif e.get("planet_a"):
            bits.append(f"pair={e['planet_a']}+{e['planet_b']}")
        if e.get("domains"):
            bits.append(f"domains={','.join(e['domains'][:3])}")
        lines.append(f"  - {' | '.join(bits)}: {e.get('description', '')}")
    lines.extend([
        "",
        "Write 2-3 sentences synthesizing the day's character for a "
        "Vedic mundane astrology newsletter. Be concrete (name the events) "
        "and grounded (no 'energies', no 'vibrations'). No disclaimers.",
    ])
    return "\n".join(lines)


def llm_daily_summary(
    date: str, events: list[dict[str, Any]], client: LLMClient,
) -> tuple[str, str]:
    """Ask the LLM for a per-day synthesis; fall back to deterministic on error.

    Returns ``(text, actual_source)`` where ``actual_source`` is ``"llm"``
    when the LLM call succeeded and ``"deterministic"`` when it fell back.
    The two-tuple shape exists so ``annotate_by_day`` can report the TRUE
    source to the client — earlier the source label was set blindly to
    "llm" whenever a client was passed, even when the LLM silently fell
    back to the template, which made the UI lie about what produced the
    text.
    """
    if not events:
        return deterministic_daily_summary(events), "deterministic"
    try:
        return client.complete(_build_llm_prompt(date, events)).strip(), "llm"
    except OllamaUnavailable:
        logger.info("LLM unavailable for daily summary; using deterministic")
        return deterministic_daily_summary(events), "deterministic"
    except Exception as exc:  # noqa: BLE001 - intentional safety net
        logger.warning("LLM daily-summary call raised %s; using deterministic", exc)
        return deterministic_daily_summary(events), "deterministic"


# --------------------------------------------------------------------------- #
# Top-level annotator                                                          #
# --------------------------------------------------------------------------- #

def annotate_by_day(
    by_day: dict[str, list[dict[str, Any]]],
    *,
    client: LLMClient | None = None,
    use_cache: bool = True,
) -> dict[str, dict[str, Any]]:
    """Return a parallel ``daily_summaries`` dict keyed by date.

    Each value is ``{"summary": str, "source": "llm"|"deterministic",
    "peak_severity": int, "dominant_domain": str | None}``.

    Returns a NEW dict — caller is free to merge it into the response
    envelope without worrying about in-place mutation of by_day.

    The reported ``source`` is the ACTUAL source: "llm" only when the LLM
    call succeeded, "deterministic" otherwise (no client, or LLM raised).
    Earlier this label was set blindly from "is client present?" which
    made the UI mis-tag silent fallbacks as LLM output.

    When ``use_cache`` is True (default), looks up + populates the
    process-wide LRU cache. The cache key bakes in the intended source
    ("llm" vs "deterministic") so flipping OLLAMA_ENABLED never serves
    cross-mode entries.
    """
    out: dict[str, dict[str, Any]] = {}
    cache = get_daily_summary_cache() if use_cache else None
    intended_source = "llm" if client is not None else "deterministic"

    def _compute(events: list[dict[str, Any]], date: str) -> tuple[str, str]:
        """Return (text, actual_source) for one day's events."""
        if client is not None:
            return llm_daily_summary(date, events, client)
        return deterministic_daily_summary(events), "deterministic"

    for date in sorted(by_day.keys()):
        events = by_day[date]
        if cache is not None:
            key = daily_summary_key(date, events, intended_source)
            text, actual_source = cached_call(
                cache, key, lambda: _compute(events, date),
            )
        else:
            text, actual_source = _compute(events, date)
        out[date] = {
            "summary": text,
            "source": actual_source,
            "peak_severity": _peak_severity(events),
            "dominant_domain": _dominant_domain(events),
        }
    return out
