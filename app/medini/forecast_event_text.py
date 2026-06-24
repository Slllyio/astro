"""Per-event LLM text synthesis from doctrine citations.

For each forecast event, this module:

1. Pulls the event's RAG citations (passed in by the caller; we don't
   re-query the index here — that's ``forecast_citations``'s job).
2. Builds a prompt that gives the LLM both the structured event facts
   AND the verbatim citation snippets.
3. Asks for a 2-3 sentence synthesis: "what does THIS event mean,
   according to THESE classical passages?"

This is the deepest enrichment layer in the forecast stack. It only works
when:
* Citations are present (``include_citations=true`` was passed upstream),
* An LLM client is available (``OLLAMA_ENABLED=true``).

Without either, this annotator silently no-ops and returns the events
unchanged — by design, never breaks the forecast pipeline.

Cached via the same LRU as daily summaries so repeated /forecast loads
don't re-pay the LLM cost for identical events + citations.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Any

from app.llm.client import LLMClient, OllamaUnavailable
from app.medini.forecast_cache import LRUCache, cached_call

logger = logging.getLogger(__name__)


# Separate cache from daily summaries — keep their LRU sizes independent
# so a flood of distinct events doesn't evict daily-summary cache hits.
_event_text_cache = LRUCache(maxsize=2000)


def get_event_text_cache() -> LRUCache:
    return _event_text_cache


def reset_event_text_cache() -> None:
    _event_text_cache.clear()


# --------------------------------------------------------------------------- #
# Key derivation                                                               #
# --------------------------------------------------------------------------- #

def _event_text_key(event: dict[str, Any]) -> str:
    """Hash the event's discriminating fields + its citation set.

    Two events fetch the same cache entry if and only if they have the
    same type/planet/description AND the same top citations (by source +
    title). Re-pulling the RAG for a re-ordered citation list won't
    invalidate the cache; re-tagging the corpus and getting new top
    citations will.
    """
    cits = sorted(
        (
            (c.get("source") or "", c.get("title") or "", c.get("snippet") or "")
            for c in (event.get("citations") or [])
        ),
    )
    blob = json.dumps({
        "type": event.get("type"),
        "planet": event.get("planet") or "",
        "planet_a": event.get("planet_a") or "",
        "planet_b": event.get("planet_b") or "",
        "description": event.get("description") or "",
        "citations": cits,
    }, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Prompt construction                                                          #
# --------------------------------------------------------------------------- #

def _build_prompt(event: dict[str, Any]) -> str:
    """Compose the LLM prompt: structured event facts + numbered citations.

    Prompt design notes (why each element):

    * **Event facts** are listed atomically (type / planet / from-sign /
      to-sign / sign / date) — NOT just the descriptive string. This stops
      the LLM from re-interpreting the description and inventing
      "exaltation" or "dignity" claims that aren't in the citations.
    * **Numbered citations** ``[1]``, ``[2]``, ... give the LLM a stable
      anchor it can reference. The instructions demand that each
      interpretive claim be attributed: ``[1]`` after the sentence.
    * **Negative constraints** are now explicit and topic-specific:
      "DO NOT claim exaltation / debilitation / dignity / rulership /
      yoga unless [N] explicitly says it." This catches the v1 drift
      ("Moon exalted in Virgo" — wrong; Moon is exalted in Taurus).
    * **Conflict-naming** rule preserved from v1: forces the LLM to
      acknowledge disagreement between sources rather than averaging.
    * **Length cap** of 2-3 sentences keeps the page scannable.

    Without these constraints, even a capable LLM (qwen2.5) routinely
    hallucinates classical claims — verified empirically in the v1 smoke.
    """
    lines: list[str] = ["EVENT FACTS"]
    lines.append(f"  type: {event.get('type', '?')}")
    if event.get("planet"):
        lines.append(f"  planet: {event['planet']}")
    if event.get("planet_a") and event.get("planet_b"):
        lines.append(f"  planets: {event['planet_a']} + {event['planet_b']}")
    if event.get("from_sign"):
        lines.append(f"  from_sign: {event['from_sign']}")
    if event.get("to_sign"):
        lines.append(f"  to_sign: {event['to_sign']}")
    if event.get("from_state"):
        lines.append(f"  from_state: {event['from_state']}")
    if event.get("to_state"):
        lines.append(f"  to_state: {event['to_state']}")
    if event.get("sign"):
        lines.append(f"  sign: {event['sign']}")
    if event.get("date_utc"):
        lines.append(f"  date: {event['date_utc']}")
    if event.get("orb_degrees") is not None:
        lines.append(f"  orb: {event['orb_degrees']:.2f} degrees")
    if event.get("severity") is not None:
        lines.append(f"  severity: {event['severity']}/10")
    if event.get("domains"):
        lines.append(f"  domains: {', '.join(event['domains'][:5])}")
    lines.append(f"  description: {event.get('description', '')}")

    cits = event.get("citations") or []
    lines.append("")
    if cits:
        lines.append(f"CITED DOCTRINE ({len(cits)} passages — use ONLY these for interpretation)")
        for i, c in enumerate(cits, 1):
            src = c.get("source") or "?"
            title = c.get("title") or ""
            snippet = (c.get("snippet") or "").strip()
            lines.append(f"  [{i}] {src} - {title}")
            lines.append(f"      \"{snippet[:500]}\"")
    else:
        lines.append("CITED DOCTRINE: (none available)")

    lines.extend([
        "",
        "TASK — pick mode by reading the citations first",
        "  MODE A (grounded): if at least one citation directly addresses",
        "    this event's planet/sign/event-type, write a 2-3 sentence",
        "    synthesis. Attribute each claim with [N]. Start the response",
        "    with the literal prefix '[GROUNDED]:'.",
        "  MODE B (general principles): if NO citation directly addresses",
        "    this event, do NOT pretend otherwise. Write 2-3 sentences of",
        "    conservative general-principles interpretation drawing only",
        "    on universally-established attributions (e.g. Moon = public",
        "    sentiment, agriculture; Mars = military, conflict). Start",
        "    with the literal prefix '[GENERAL]:' so the reader knows",
        "    the synthesis is not directly cited.",
        "",
        "RULES (hard constraints — both modes)",
        "  * DO NOT claim exaltation, debilitation, dignity, ownership,",
        "    moolatrikona, rulership, yoga, or aspect UNLESS a [N] citation",
        "    explicitly states it for THIS placement.",
        "  * If two citations disagree, name the disagreement: 'while [1]",
        "    indicates X, [2] suggests Y.'",
        "  * Use only the planet, sign, and event facts in EVENT FACTS as",
        "    ground truth. Do NOT introduce new placements, nakshatra",
        "    readings, or dasha mentions unless cited.",
        "  * No phrases: 'energies', 'vibrations', 'cosmic', 'spiritual",
        "    journey'. No disclaimers about astrology.",
        "  * No preamble. Start immediately with [GROUNDED]: or [GENERAL]:",
        "",
        "OUTPUT:",
    ])
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Public                                                                       #
# --------------------------------------------------------------------------- #

def _parse_mode_marker(raw: str) -> tuple[str, bool | None]:
    """Strip the [GROUNDED]: or [GENERAL]: prefix and return (text, grounded).

    ``grounded`` is True when the LLM picked grounded mode, False for the
    general-principles fallback, and None when neither marker was found
    (older models or prompt drift — we still surface the text).
    """
    s = raw.strip()
    # Match either prefix anchored at start; tolerate a missing colon and
    # any reasonable amount of internal whitespace.
    grounded_match = re.match(r"^\[GROUNDED\]\s*:?\s*", s, flags=re.IGNORECASE)
    general_match = re.match(r"^\[GENERAL\]\s*:?\s*", s, flags=re.IGNORECASE)
    if grounded_match:
        return s[grounded_match.end():].strip(), True
    if general_match:
        return s[general_match.end():].strip(), False
    return s, None


def event_text(
    event: dict[str, Any], client: LLMClient,
) -> tuple[str, bool | None] | None:
    """Generate an LLM synthesis for one event.

    Returns:
      * ``(text, grounded_bool)`` on success — ``grounded`` is True when the
        LLM picked grounded mode, False for general-principles fallback,
        None when the model omitted the mode marker.
      * ``None`` when synthesis fails (no citations, LLM unavailable,
        any exception). Tells the route to omit ``event_text`` entirely.
    """
    if not event.get("citations"):
        return None
    try:
        raw = client.complete(_build_prompt(event)).strip()
    except OllamaUnavailable:
        logger.info("LLM unavailable for event_text on %s", event.get("type"))
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("event_text failed for %s: %s", event.get("type"), exc)
        return None
    text, grounded = _parse_mode_marker(raw)
    if not text:
        # Marker present but no content after it — treat as failure.
        return None
    return (text, grounded)


def annotate_events(
    events: list[dict[str, Any]],
    *,
    client: LLMClient | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """Attach ``event_text`` (and ``event_text_grounded``) to events with
    citations.

    Two fields per successful synthesis:
      * ``event_text``: the LLM prose (mode marker stripped).
      * ``event_text_grounded``: True when the LLM picked grounded mode
        (citations directly addressed the event), False for the general-
        principles fallback, None when the model omitted the marker.

    Events without citations are returned untouched (no fields added) so
    the UI can dispatch on ``"event_text" in event``. No client → no-op.
    """
    if client is None:
        return events
    cache = get_event_text_cache() if use_cache else None
    out: list[dict[str, Any]] = []
    for e in events:
        if not e.get("citations"):
            out.append(e)
            continue
        if cache is not None:
            key = _event_text_key(e)
            result = cached_call(cache, key, lambda: event_text(e, client))
        else:
            result = event_text(e, client)
        if result is None:
            out.append(e)
            continue
        text, grounded = result
        out.append({**e, "event_text": text, "event_text_grounded": grounded})
    return out
