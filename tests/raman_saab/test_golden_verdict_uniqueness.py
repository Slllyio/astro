"""One nativity, one verdict per matter — the guard for a bug that silently double-counted.

The corpus stores ONE RECORD PER CHAPTER-PRESENTATION, so a single person legitimately appears
under several ids: Raman re-presents the same chart in the 7th-house chapter, the 9th, the 11th,
and judges a different matter each time. That is correct and must keep working.

What is NOT correct is the same (nativity, house, signification) verdict existing on more than one
of those records. It happened on 2026-08-23: an extraction batch deduplicated by CHART NUMBER
instead of by BIRTH MOMENT (the printings number charts differently), leaking 19 duplicate
records, and a follow-up "merge verdicts across presentations" pass then wrote the same DRAFT
verdict onto every copy — 14 duplicated matters, nine of which CONTRADICTED an already-CONFIRMED
verdict for that same matter with a different ordinal.

Nothing scored at the time, because DRAFT rows are skipped by the ratchet. But the damage was
latent and severe: confirming those rows later would have counted one of Raman's judgments two,
three or four times in a single accuracy figure, and in nine cases would have asserted two
different ordinals for one matter. This file makes that unrepresentable.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest

_GOLDENS = Path(__file__).resolve().parents[1] / "fixtures" / "raman_goldens.jsonl"


def _records() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not _GOLDENS.is_file():
        return out
    for raw in _GOLDENS.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if s and not s.startswith("#"):
            out.append(json.loads(s))
    return out


def _by_nativity() -> dict[str, list[dict[str, Any]]]:
    """Records grouped by birth moment to the minute — the edition-independent identity of a
    nativity, and the only sound dedupe key (chart numbers differ between printings)."""
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in _records():
        b = r.get("birth") or {}
        if b.get("dt"):
            out[str(b["dt"])[:16]].append(r)
    return out


def _matters(rec: dict[str, Any]) -> list[tuple[str, str]]:
    return [(h, e.get("signification", "")) for h, e in (rec.get("expected_verdicts") or {}).items()]


@pytest.mark.skipif(not _GOLDENS.is_file(), reason="golden corpus absent")
class TestOneVerdictPerMatterPerNativity:
    def test_no_matter_is_scored_twice_for_one_nativity(self):
        """The load-bearing assertion: no (nativity, house, signification) may carry more than
        one CONFIRMED verdict. A duplicate would count one of Raman's judgments twice in the
        accuracy figure, inflating or deflating it by pure bookkeeping."""
        offences = []
        for key, recs in _by_nativity().items():
            if len(recs) < 2:
                continue
            owners: dict[tuple[str, str], list[str]] = defaultdict(list)
            for r in recs:
                for h, e in (r.get("expected_verdicts") or {}).items():
                    if e.get("verdict_review") == "CONFIRMED":
                        owners[(h, e.get("signification", ""))].append(r["id"])
            for matter, ids in owners.items():
                if len(ids) > 1:
                    offences.append(f"{key} {matter} confirmed on {sorted(ids)}")
        assert not offences, (
            "the same matter is CONFIRMED on several records of one nativity — the accuracy "
            "denominator would double-count it:\n  " + "\n  ".join(offences))

    def test_no_draft_duplicates_a_confirmed_matter(self):
        """A DRAFT sitting on the same matter as a CONFIRMED verdict is at best noise and at
        worst a contradiction waiting to be promoted — nine such rows carried a DIFFERENT
        ordinal from the confirmed one when this was first measured."""
        offences = []
        for key, recs in _by_nativity().items():
            if len(recs) < 2:
                continue
            status: dict[tuple[str, str], dict[str, list[str]]] = defaultdict(
                lambda: {"CONFIRMED": [], "DRAFT": []})
            for r in recs:
                for h, e in (r.get("expected_verdicts") or {}).items():
                    bucket = status[(h, e.get("signification", ""))]
                    bucket.setdefault(e.get("verdict_review", "DRAFT"), []).append(r["id"])
            for matter, b in status.items():
                if b["CONFIRMED"] and b["DRAFT"]:
                    offences.append(f"{key} {matter}: confirmed {b['CONFIRMED']} vs draft {b['DRAFT']}")
        assert not offences, (
            "a DRAFT verdict shadows an already-CONFIRMED matter on the same nativity:\n  "
            + "\n  ".join(offences))

    def test_no_confirmed_verdict_names_a_signification_that_does_not_exist(self):
        """A CONFIRMED verdict is looked up by exact signification key. An invalid key resolves
        to nothing, so the row would sit in the denominator scoring against a matter the engine
        never judges — a silent, permanent distortion. Unrepresentable, hard fail.

        Chapter-derived attribution is one way to get here (HTJAH-I's fourth-house chapter judges
        the mother AND education, and four extracted rows were blanket-labelled `mother` while
        their prose discussed learning); the NH extractor's compound labels are another."""
        from app.raman_saab.doctrine.significations import significations_of
        bad = []
        for r in _records():
            for h, e in (r.get("expected_verdicts") or {}).items():
                if e.get("verdict_review") != "CONFIRMED":
                    continue
                keys = {s.key for s in significations_of(int(h[1:]))}
                if e.get("signification") not in keys:
                    bad.append(f"{r['id']} {h}: {e.get('signification')!r} not in {sorted(keys)}")
        assert not bad, ("a CONFIRMED verdict names a signification that does not exist — it "
                         "would score against nothing:\n  " + "\n  ".join(bad))

    def test_draft_rows_with_an_invalid_signification_only_shrink(self):
        """The NH extractor emitted compound labels ('wealth/speech', 'death/maraka',
        'self/body') that are not signification keys. None are CONFIRMED, so none are scored —
        but each is a landmine for the adjudication programme, because confirming one silently
        scores against nothing. Which of the two matters Raman actually judged is a decision for
        the reviewer reading his prose, not something to guess here, so they are ratcheted: the
        count may fall as review resolves them, never rise."""
        from app.raman_saab.doctrine.significations import significations_of
        bad = []
        for r in _records():
            for h, e in (r.get("expected_verdicts") or {}).items():
                if e.get("verdict_review") == "CONFIRMED":
                    continue
                keys = {s.key for s in significations_of(int(h[1:]))}
                if e.get("signification") not in keys:
                    bad.append(f"{r['id']} {h}:{e.get('signification')}")
        assert len(bad) <= 11, (
            f"{len(bad)} DRAFT rows name a non-existent signification (known backlog: 11). "
            f"New ones must not be introduced:\n  " + "\n  ".join(sorted(bad)))

    def test_every_confirmed_verdict_states_an_ordinal(self):
        """`verdict_review: CONFIRMED` with a literal 'DRAFT' ordinal is the corpus's other
        way of saying un-reviewed; the two must never disagree."""
        bad = [f"{r['id']} {h}" for r in _records()
               for h, e in (r.get("expected_verdicts") or {}).items()
               if e.get("verdict_review") == "CONFIRMED" and e.get("verdict") == "DRAFT"]
        assert not bad, f"CONFIRMED rows carrying the DRAFT literal: {bad}"
