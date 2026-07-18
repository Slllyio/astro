"""Typed life events + natal facts for birth-time rectification — the evidence model.

Raman's own doctrine makes dated life events the PRIMARY rectification instrument:
"birth times can be rectified only by men of experience by a consideration of pronounced
life incidents" (HPA ch.12, On Birth Verification and Rectification), demonstrated on
his own rectified nativities ("by a careful consideration of his life incidents ... we
have been able to fix up the time", H.G. Wells, NH:6683; Goethe NH:4051-4080). Each
event type below maps to the house whose Time-of-Fructification significators must rule
the running Dasha/Bhukti/Pratyantar at the event date (HTJAH-I:1583-1596: "In timing
events pertaining to the first Bhava, note ... (a) Lord ... (b) planets aspecting ...
(c) planets posited ... The same consideration holds good with reference to the other
houses"), plus the explicit event karakas Raman names (e.g. marriage: "Marriage may
occur during the Dasa (period) of the planet (1) posited in the 7th house; (2) Venus and
the Moon; (3) planet aspecting the 7th house; or (4) owning the 7th house", AFB-9:98).

Every ``EventSpec`` row carries a verbatim ``Citation`` resolvable on disk (enforced by
``tests/raman_saab/rectification/test_events.py``); every ``signification_key`` must
exist in ``significations_of(house)`` (validated at import — no silent drift).

Usage:
    from app.raman_saab.rectification.events import LifeEvent, NatalFact, resolve_fact
    ev = LifeEvent(event_type="marriage", year=2017, month=12, day=4)
    ev.precision            # "day"
    fact = resolve_fact("mother", "afflicted")
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import Final, Literal, Optional

from app.raman_saab.doctrine.karakas import BHAVA_KARAKAS
from app.raman_saab.doctrine.significations import SIGNIFICATIONS, significations_of
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives.vimshottari import date_to_jd

DatePrecision = Literal["year", "month", "day"]
Observed = Literal["favourable", "mixed", "afflicted"]

_DAYS_IN_MONTH: Final[tuple[int, ...]] = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


@dataclass(frozen=True)
class EventSpec:
    """One event TYPE: the bhava whose fructification significators time it, the extra
    event karakas Raman names beyond the house's ``timer_set``, and the signification
    key bridging to the natal-fact channel. ``maraka_overlay`` marks relative-death
    events whose scoring additionally consults the maraka apparatus (HTJAH-I:770-795)."""
    key: str
    house: int
    aux_houses: tuple[int, ...]
    karakas: tuple[str, ...]
    signification_key: str
    question: str
    source: Citation
    maraka_overlay: bool = False
    notes: str = ""


EVENT_TAXONOMY: Final[dict[str, EventSpec]] = {
    spec.key: spec for spec in (
        EventSpec(
            "marriage", 7, (), ("Venus", "Moon"), "spouse",
            "When did the marriage take place?",
            Citation("AFB-9", 98),
            notes="'Marriage may occur during the Dasa of the planet (1) posited in the "
                  "7th; (2) Venus and the Moon; (3) aspecting the 7th; (4) owning the 7th' "
                  "— occupant/aspecter/lord arms are already timer_set(7); Venus+Moon are "
                  "the additive karakas."),
        EventSpec(
            "childbirth", 5, (), ("Jupiter",), "children",
            "When was a child born?",
            Citation("AFB-9", 142),
            notes="'Birth of children may occur during the Dasa or Bhukti of Jupiter, or "
                  "lord of the 5th (from the Ascendant or from the Moon)' — the from-Moon "
                  "lord and aspecters are already in timer_set(5)."),
        EventSpec(
            "career_start", 10, (), BHAVA_KARAKAS[10], "career",
            "When did the (first) major job or career begin?",
            Citation("AFB-10", 472),
            notes="'10th lord: Professional prosperity ... realisation of ambitions'. "
                  "GATE NOTE: the H10 fructification list (HTJAH-II:9916-9920) has NO "
                  "karaka clause; the karaka-as-timer warrant is AFB-10:482-486 ('whatever "
                  "natures ... belonging to the different planets, should be duly assigned "
                  "to the planets concerned in their respective periods') + the karaka "
                  "primary-consideration at HTJAH-II:9446-9452; multi-karaka set from "
                  "karakas.py BHAVA_KARAKAS[10]."),
        EventSpec(
            "career_change", 10, (8,), ("Saturn", "Mercury"), "career",
            "When did work/vocation change direction sharply?",
            Citation("HTJAH-II", 9910),
            notes="H10 fructification. Aux-8 anchor (gate-corrected): the TENTH-house "
                  "chapter's own 8th-house dispatch — 'In the Eighth House: The native has "
                  "many breaks in career ... If Jupiter influences the 10th lord ... in "
                  "the 8th house, he will become a mystic or spiritual teacher' "
                  "(HTJAH-II:9525-9535). Karaka-as-timer warrant AFB-10:482-486."),
        EventSpec(
            "honour_promotion", 10, (11,), ("Sun",), "status_honour",
            "When did a promotion / honour / public recognition come?",
            Citation("AFB-10", 472),
            notes="10th-lord Dasa 'professional prosperity ... reputation, respect'; 11th "
                  "aux 'influx of wealth ... gains' (AFB-10:474). Sun karaka anchored at "
                  "AFB-10:500-503 (Sun's period 'attains fame ... honours'); Jupiter was "
                  "DROPPED by the doctrine gate (no Raman honours-karaka line located)."),
        EventSpec(
            "income_gain", 11, (2,), ("Jupiter",), "gains",
            "When did a distinct influx of wealth/income occur?",
            Citation("HTJAH-II", 14494),
            notes="H11 fructification; 2nd as the paired wealth house ('11th lord: Influx "
                  "of wealth', AFB-10:474)."),
        EventSpec(
            "property_acquisition", 4, (), ("Mars", "Moon"), "property",
            "When was land / a house / a vehicle acquired?",
            Citation("HTJAH-I", 4303),
            notes="H4 fructification; Mars = property karaka, Moon = 4th karaka "
                  "(karakas.py BHAVA_KARAKAS[4])."),
        EventSpec(
            "foreign_travel", 9, (12,), (), "long_journeys",
            "When did a long/foreign journey or relocation happen?",
            Citation("HTJAH-I", 12731),
            notes="H9 long-journeys fructification; 12th as the paired "
                  "foreign-residence house."),
        EventSpec(
            "education_milestone", 4, (), ("Mercury", "Jupiter"), "education",
            "When did schooling/degree begin or complete?",
            Citation("AFB-6", 23),
            notes="Gate-corrected anchor: 'EDUCATION is generally ascertained from the "
                  "4th [house and the karaka of edu]cation, viz., Jupiter' (AFB-6:23-26); "
                  "Mercury: 'If Mercury is weak, he will fail in examinations or there "
                  "will be breaks in education' (HTJAH-I:6389). Aux-9 was DROPPED by the "
                  "doctrine gate: no Raman line makes the 9th the higher-learning event "
                  "house (AFB-6:28-29 puts even legal education at the 4th or 10th)."),
        EventSpec(
            "illness_accident", 6, (8,), ("Mars", "Saturn"), "accidents",
            "When did a serious illness or accident occur?",
            Citation("HTJAH-I", 6270),
            notes="H6 fructification; 8th aux for life-threat; Mars/Saturn the "
                  "affliction karakas."),
        EventSpec(
            "litigation", 6, (), ("Mars",), "enemies",
            "When did a court case / open enmity peak?",
            Citation("HTJAH-I", 6270)),
        EventSpec(
            "debt_discharge", 8, (6,), (), "sudden_gains",
            "When was a major debt cleared or a legacy received?",
            Citation("AFB-10", 469),
            notes="'8th lord: Discharge of debts' — timed by the 8th's timers; 6th aux "
                  "(the debt house itself)."),
        EventSpec(
            "spiritual_turn", 12, (9,), ("Saturn",), "moksha",
            "When did a marked spiritual/renunciate turn begin?",
            Citation("HTJAH-II", 16658)),
        EventSpec(
            "mother_death", 4, (), ("Moon",), "mother",
            "When did the native's mother die?",
            Citation("HTJAH-I", 770), maraka_overlay=True,
            notes="Maraka apparatus HTJAH-I:770-795, ROTATED to the relative's frame per "
                  "Raman's worked usage: 'Mars ... not only owns the second and seventh "
                  "Maraka but is actually situated in the second from Matru-Karaka' "
                  "(HTJAH-I:4479-4481); 'mother's death took place in Rahu Dasha, Venus "
                  "Bhukti, Venus Antara' (HTJAH-I:4482-4483). House/karaka anchors: 'The "
                  "fourth lord is also Matru-Karaka' (HTJAH-I:4475); Moon in MatruBhava "
                  "(HTJAH-I:4504)."),
        EventSpec(
            "father_death", 9, (), ("Sun",), "father",
            "When did the native's father die?",
            Citation("HTJAH-I", 770), maraka_overlay=True,
            notes="House/karaka anchor (gate-added): the 9th's own timing-factor list "
                  "includes '(g) the Sun who is the Karaka for father' "
                  "(HTJAH-I:12737-12738)."),
        EventSpec(
            "spouse_death", 7, (), ("Venus",), "coverture",
            "When did the native's spouse die?",
            Citation("HTJAH-I", 770), maraka_overlay=True,
            notes="House/karaka anchors (gate-added): 'the Karaka, who in this case would "
                  "be Venus' (HTJAH-II:225); '(g) the karaka of the 7th Bhava' among the "
                  "H7 timing factors (HTJAH-II:673-676); 'If the 7th lord is in the 12th "
                  "house and the karaka is also very weak ... one may lose one's wife "
                  "through death or separation' (HTJAH-II:832-836)."),
        EventSpec(
            "sibling_death", 3, (), ("Mars",), "siblings",
            "When did a sibling of the native die?",
            Citation("HTJAH-I", 770), maraka_overlay=True,
            notes="House/karaka anchors (gate-added): 'the Karaka for brothers (Kuja or "
                  "Mars)' (HTJAH-I:3428); the H3 timing factors include '(d) the Karaka' "
                  "(HTJAH-I:3523-3526)."),
    )
}


def _validate_taxonomy() -> None:
    """Import-time guard: every signification_key must exist for its house (no drift
    against doctrine/significations.py), houses/aux in 1..12, karakas are graha names."""
    grahas = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
              "Rahu", "Ketu"}
    for spec in EVENT_TAXONOMY.values():
        keys = {s.key for s in significations_of(spec.house)}
        if spec.signification_key not in keys:
            raise ValueError(
                f"EVENT_TAXONOMY[{spec.key!r}]: signification_key "
                f"{spec.signification_key!r} not among H{spec.house} keys {sorted(keys)}")
        for h in (spec.house, *spec.aux_houses):
            if not 1 <= h <= 12:
                raise ValueError(f"EVENT_TAXONOMY[{spec.key!r}]: bad house {h}")
        bad = set(spec.karakas) - grahas
        if bad:
            raise ValueError(f"EVENT_TAXONOMY[{spec.key!r}]: unknown karakas {sorted(bad)}")


_validate_taxonomy()


@dataclass(frozen=True)
class LifeEvent:
    """One dated life incident. Date precision is whatever the user actually knows —
    year, year+month, or full date — and the SCORER must honour it (a level of the
    dasha hierarchy is only scorable if one period covers the whole stated interval)."""
    event_type: str
    year: int
    month: Optional[int] = None
    day: Optional[int] = None
    description: str = ""
    weight: float = 1.0

    def __post_init__(self) -> None:
        if self.event_type not in EVENT_TAXONOMY:
            hint = difflib.get_close_matches(self.event_type, EVENT_TAXONOMY, n=3)
            raise ValueError(
                f"unknown event_type {self.event_type!r}; valid: "
                f"{sorted(EVENT_TAXONOMY)}" + (f"; did you mean {hint}?" if hint else ""))
        if not 1800 <= self.year <= 2200:
            raise ValueError(f"implausible event year {self.year}")
        if self.day is not None and self.month is None:
            raise ValueError("a day-precision event needs its month too")
        if self.month is not None and not 1 <= self.month <= 12:
            raise ValueError(f"bad month {self.month}")
        if self.day is not None and not 1 <= self.day <= _DAYS_IN_MONTH[self.month - 1]:
            raise ValueError(f"bad day {self.day} for month {self.month}")
        if self.weight <= 0:
            raise ValueError("weight must be positive")

    @property
    def spec(self) -> EventSpec:
        return EVENT_TAXONOMY[self.event_type]

    @property
    def precision(self) -> DatePrecision:
        if self.day is not None:
            return "day"
        return "month" if self.month is not None else "year"

    def jd_point(self) -> float:
        """Representative instant: stated day at noon, else month middle, else year middle."""
        if self.precision == "day":
            return date_to_jd(self.year, self.month, self.day)
        if self.precision == "month":
            return date_to_jd(self.year, self.month, 15)
        return date_to_jd(self.year, 7, 1)

    def jd_bounds(self) -> tuple[float, float]:
        """The full [start, end) interval the stated precision covers."""
        if self.precision == "day":
            start = date_to_jd(self.year, self.month, self.day, 0.0)
            return start, start + 1.0
        if self.precision == "month":
            start = date_to_jd(self.year, self.month, 1, 0.0)
            if self.month == 12:
                return start, date_to_jd(self.year + 1, 1, 1, 0.0)
            return start, date_to_jd(self.year, self.month + 1, 1, 0.0)
        return date_to_jd(self.year, 1, 1, 0.0), date_to_jd(self.year + 1, 1, 1, 0.0)


@dataclass(frozen=True)
class NatalFact:
    """A non-dated natal observation ('the mother has been chronically unwell') scored
    against the engine's judge_house verdict for its signification — the second
    evidence channel (it discriminated the ayanamsa in the worked rect_case_01)."""
    subject: str
    house: int
    observed: Observed
    description: str = ""
    weight: float = 1.0

    def __post_init__(self) -> None:
        keys = {s.key for s in significations_of(self.house)}
        if self.subject not in keys:
            raise ValueError(
                f"NatalFact subject {self.subject!r} not among H{self.house} "
                f"signification keys {sorted(keys)}")
        if self.weight <= 0:
            raise ValueError("weight must be positive")


def resolve_fact(subject: str, observed: Observed, *, description: str = "",
                 weight: float = 1.0) -> NatalFact:
    """Build a NatalFact from a signification key alone, locating its house by scanning
    the doctrine table. Unknown keys fail loudly with the valid-key list and a
    nearest-match hint — no silent guessing."""
    for sigs in SIGNIFICATIONS.values():
        for sig in sigs:
            if sig.key == subject:
                return NatalFact(subject=subject, house=sig.house, observed=observed,
                                 description=description, weight=weight)
    all_keys = sorted({s.key for sigs in SIGNIFICATIONS.values() for s in sigs})
    hint = difflib.get_close_matches(subject, all_keys, n=3)
    raise ValueError(
        f"unknown natal-fact subject {subject!r}; valid keys: {all_keys}"
        + (f"; did you mean {hint}?" if hint else ""))
