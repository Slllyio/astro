"""Stateful rectification session — the accumulate-evidence / evaluate / ask-next loop.

Mirrors how a human rectifier actually works (and how the worked rect_case_01 session
ran): evidence arrives piecemeal; each ``evaluate()`` re-scores the candidate classes
under BOTH ayanamsas, records a ``RoundRecord`` in the history, and the report says what
the evidence can and cannot yet resolve. The session is JSON-persistable — INPUTS +
HISTORY ONLY; scores are recomputed on load, so a session file can never smuggle stale
rankings across engine versions (an ``engine_fingerprint`` mismatch warns loudly).

Two modes:
  * ``rectify``  — a stated time ± window (default ±60 min), one pass.
  * ``discover`` — the whole day, two phases: coarse (20-min walk, classes grouped by
    lagna sign; groups within ``DISCOVER_DELTA`` of the best survive) then fine
    (default walk within the surviving lagna spans only).

Usage:
    from app.raman_saab.rectification.session import RectificationSession
    s = RectificationSession.new(mode="rectify", date=(1989, 10, 12), lat=27.23,
                                 lon=79.03, tz=5.5, time=(10, 2))
    s.add_event(LifeEvent("marriage", 2017, 12, 4))
    report = s.evaluate()
    s.save(Path("session.json"))
"""
from __future__ import annotations

import hashlib
import json
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from app.raman_saab.rectification import candidates as C
from app.raman_saab.rectification import scoring as S
from app.raman_saab.rectification.events import LifeEvent, NatalFact
from app.raman_saab.rectification.report import RectificationReport, build_report

Mode = Literal["rectify", "discover"]

#: discover phase-1: lagna-sign groups within this score of the best survive to phase 2.
DISCOVER_DELTA: float = 1.0
_COARSE_STEP_S: float = 1200.0


def _engine_fingerprint() -> str:
    """Heuristic engine-version marker: hash of the scoring-relevant module sources.
    A mismatch on load means prior history rankings may not reproduce."""
    root = Path(__file__).resolve().parent
    vim = root.parent / "primitives" / "vimshottari.py"
    h = hashlib.sha256()
    for p in (root / "events.py", root / "scoring.py", root / "candidates.py", vim):
        try:
            h.update(p.read_bytes())
        except OSError:
            h.update(b"?")
    return h.hexdigest()[:12]


@dataclass(frozen=True)
class RoundRecord:
    """One evaluate() snapshot — enough to see the candidate set shrink over rounds."""
    timestamp: str
    n_events: int
    n_facts: int
    n_candidates: int
    top: tuple[tuple[str, str, float], ...]      # (ayanamsa, time_str, total) top 5
    suggested_next: tuple[str, ...] = ()         # rendered next-question suggestions


@dataclass
class RectificationSession:
    """Mutable by design (an evidence accumulator); persisted explicitly via save()."""
    mode: Mode
    year: int
    month: int
    day: int
    latitude: float
    longitude: float
    tz_offset: float
    stated_time: Optional[tuple[int, int]] = None
    window_minutes: int = 60
    ayanamsas: tuple[str, ...] = ("raman", "lahiri")
    events: list[LifeEvent] = field(default_factory=list)
    facts: list[NatalFact] = field(default_factory=list)
    history: list[RoundRecord] = field(default_factory=list)
    engine_fingerprint: str = ""

    # ── construction ──────────────────────────────────────────────────────────
    @classmethod
    def new(cls, *, mode: Mode, date: tuple[int, int, int], lat: float, lon: float,
            tz: float, time: Optional[tuple[int, int]] = None,
            window_minutes: int = 60,
            ayanamsas: tuple[str, ...] = ("raman", "lahiri")) -> "RectificationSession":
        if mode == "rectify" and time is None:
            raise ValueError("rectify mode needs a stated time; use discover otherwise")
        return cls(mode=mode, year=date[0], month=date[1], day=date[2],
                   latitude=lat, longitude=lon, tz_offset=tz, stated_time=time,
                   window_minutes=window_minutes, ayanamsas=tuple(ayanamsas),
                   engine_fingerprint=_engine_fingerprint())

    # ── evidence ──────────────────────────────────────────────────────────────
    def add_event(self, ev: LifeEvent) -> None:
        self.events.append(ev)

    def add_fact(self, fact: NatalFact) -> None:
        self.facts.append(fact)

    # ── evaluation ────────────────────────────────────────────────────────────
    def _window_hours(self) -> tuple[float, float]:
        hh, mm = self.stated_time                      # type: ignore[misc]
        centre = hh + mm / 60.0
        half = self.window_minutes / 60.0
        return max(0.0, centre - half), min(24.0, centre + half)

    def _generate(self, window: tuple[float, float],
                  walk_step_s: float = C._WALK_STEP_S) -> tuple[C.CandidateChart, ...]:
        return C.generate_candidates(
            year=self.year, month=self.month, day=self.day,
            latitude=self.latitude, longitude=self.longitude, tz_offset=self.tz_offset,
            window_local_hours=window, ayanamsas=self.ayanamsas,
            event_jds=tuple(ev.jd_point() for ev in self.events),
            walk_step_s=walk_step_s)

    def _score_all(self, cands: tuple[C.CandidateChart, ...], cache: C.ChartCache,
                   *, top_k: int) -> tuple[S.CandidateScore, ...]:
        """Tier-L scoring for every class; the fact channel (Tier-F, expensive) only on
        the event-score top-K survivors — the documented cast budget."""
        events = tuple(self.events)
        light = tuple(S.score_candidate(c, cache, events) for c in cands)
        if not self.facts:
            return light
        ranked = sorted(light, key=lambda cs: cs.channels.total, reverse=True)
        survivors = {cs.candidate.class_id for cs in ranked[:top_k]}
        out: list[S.CandidateScore] = []
        for cs in light:
            if cs.candidate.class_id in survivors:
                out.append(S.score_candidate(cs.candidate, cache, events,
                                             tuple(self.facts), include_facts=True))
            else:
                out.append(cs)
        return tuple(out)

    def evaluate(self, *, top_k: int = 8,
                 with_suggestions: bool = True) -> RectificationReport:
        """Run the mode's search, score every candidate class, compute the next-question
        suggestions, and record the round."""
        from app.raman_saab.rectification import suggest as SG
        cache = C.ChartCache()
        if self.mode == "rectify":
            cands = self._generate(self._window_hours())
        else:
            cands = self._discover_candidates(cache)
        scored = self._score_all(cands, cache, top_k=top_k)
        suggestions: tuple[str, ...] = ()
        if with_suggestions and len(scored) >= 2:
            ranked = tuple(sorted(scored, key=lambda cs: cs.channels.total,
                                  reverse=True))
            birth_jd = min(c.birth_jd for c in cands)
            horizon = datetime.now(timezone.utc)
            horizon_jd = birth_jd + max(
                0.0, (horizon - datetime(self.year, self.month, self.day,
                                         tzinfo=timezone.utc)).days)
            sugg = SG.suggest_events(
                ranked, cache, frozenset(ev.event_type for ev in self.events),
                birth_jd=birth_jd, horizon_jd=horizon_jd)
            sugg += SG.suggest_facts(
                ranked, cache, frozenset(f.subject for f in self.facts))
            suggestions = tuple(s.render() for s in sugg)
        report = build_report(mode=self.mode, scored=scored,
                              events=tuple(self.events), facts=tuple(self.facts),
                              top_k=top_k, suggestions=suggestions)
        top5 = tuple((cs.candidate.ayanamsa, cs.candidate.time_str,
                      round(cs.channels.total, 3)) for cs in report.ranked[:5])
        self.history.append(RoundRecord(
            timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            n_events=len(self.events), n_facts=len(self.facts),
            n_candidates=len(cands), top=top5, suggested_next=suggestions[:3]))
        return report

    def _discover_candidates(self, cache: C.ChartCache) -> tuple[C.CandidateChart, ...]:
        """Discover mode, two phases: coarse lagna-sign groups -> survivors -> fine
        classes within the surviving lagna spans only."""
        coarse = self._generate((0.0, 24.0), walk_step_s=_COARSE_STEP_S)
        events = tuple(self.events)
        by_group: dict[tuple[str, int], list[tuple[C.CandidateChart, float]]] = {}
        for cand in coarse:
            cs = S.score_candidate(cand, cache, events)
            by_group.setdefault((cand.ayanamsa, cand.features.asc_sign), []).append(
                (cand, cs.channels.total))
        best_total = max((t for rows in by_group.values() for _, t in rows),
                         default=0.0)
        fine: list[C.CandidateChart] = []
        for (_ay, _sign), rows in by_group.items():
            group_best = max(t for _, t in rows)
            if group_best < best_total - DISCOVER_DELTA:
                continue
            lo = min(c.birth_jd for c, _ in rows)
            hi = max(c.birth_jd for c, _ in rows)
            # class-representative jds -> a local-hour span, padded by the coarse step
            pad = _COARSE_STEP_S / 86400.0
            lo_h = ((lo - pad) + self.tz_offset / 24.0) % 1.0 * 24.0
            hi_h = ((hi + pad) + self.tz_offset / 24.0) % 1.0 * 24.0
            if hi_h <= lo_h:
                lo_h, hi_h = max(0.0, lo_h - 0.5), min(24.0, lo_h + 2.5)
            fine.extend(self._generate((max(0.0, lo_h), min(24.0, hi_h))))
        # de-duplicate by class_id (spans may overlap across groups)
        seen: set[str] = set()
        out: list[C.CandidateChart] = []
        for cand in fine:
            if cand.class_id not in seen:
                seen.add(cand.class_id)
                out.append(cand)
        return tuple(out)

    # ── persistence (inputs + history ONLY; scores recompute on load) ─────────
    def to_json(self) -> str:
        payload = {
            "mode": self.mode,
            "date": [self.year, self.month, self.day],
            "latitude": self.latitude, "longitude": self.longitude,
            "tz_offset": self.tz_offset,
            "stated_time": list(self.stated_time) if self.stated_time else None,
            "window_minutes": self.window_minutes,
            "ayanamsas": list(self.ayanamsas),
            "events": [asdict(ev) for ev in self.events],
            "facts": [asdict(f) for f in self.facts],
            "history": [asdict(r) for r in self.history],
            "engine_fingerprint": self.engine_fingerprint,
        }
        return json.dumps(payload, indent=2)

    def save(self, path: Path) -> None:
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "RectificationSession":
        d = json.loads(path.read_text(encoding="utf-8"))
        session = cls(
            mode=d["mode"], year=d["date"][0], month=d["date"][1], day=d["date"][2],
            latitude=float(d["latitude"]), longitude=float(d["longitude"]),
            tz_offset=float(d["tz_offset"]),
            stated_time=tuple(d["stated_time"]) if d.get("stated_time") else None,
            window_minutes=int(d.get("window_minutes", 60)),
            ayanamsas=tuple(d.get("ayanamsas", ("raman", "lahiri"))),
            events=[LifeEvent(**ev) for ev in d.get("events", [])],
            facts=[NatalFact(**f) for f in d.get("facts", [])],
            history=[RoundRecord(timestamp=r["timestamp"], n_events=r["n_events"],
                                 n_facts=r["n_facts"], n_candidates=r["n_candidates"],
                                 top=tuple(tuple(t) for t in r["top"]),
                                 suggested_next=tuple(r.get("suggested_next", ())))
                     for r in d.get("history", [])],
            engine_fingerprint=d.get("engine_fingerprint", ""))
        current = _engine_fingerprint()
        if session.engine_fingerprint and session.engine_fingerprint != current:
            warnings.warn(
                f"session was saved under engine {session.engine_fingerprint}, now "
                f"{current}: prior history rankings may not reproduce; re-run evaluate()",
                UserWarning, stacklevel=2)
        return session
