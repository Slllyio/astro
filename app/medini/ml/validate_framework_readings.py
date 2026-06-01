"""Validation scaffold — frame framework readings against published expert ground truth.

For each canonical chart (Mahatma Gandhi, Indira Gandhi, Nehru), this
module:

1. Loads the natal chart data (hardcoded constants from Lahiri-sidereal
   ephemeris computations published in BPHS-school texts).
2. Composes the framework Reading.
3. Compares the framework's per-bhava verdict and active-yoga list
   against a structured *expert expectations* table — what classical
   astrologers (K.N. Rao, Sanjay Rath, Gopesh Kumar Ojha) noted about
   these charts in their published readings.
4. Emits a comparison report: which expert expectations does the
   framework correctly surface? Which does it miss? Which extra claims
   does the framework make that experts don't mention?

## Scope

This is a SCAFFOLD — the expert-expectations tables here are seeds that
require expansion against the actual published readings. Each entry
notes the source citation so a future PR can verify and expand against
the original text.

## Why it's a scaffold

Three reasons:
* Published expert readings are usually narrative; structured per-bhava
  verdicts are an interpretive choice.
* Different astrologers disagree (same chart often gets different
  emphasis from Sanjay Rath vs K.N. Rao).
* Ground-truth conflict resolution itself is doctrinal work.

So this module operationalises *the comparison harness* — the actual
ground-truth tables are seeded with the most-cited expert observations
and can be expanded incrementally.

Usage:
    python -m app.medini.ml.validate_framework_readings
    python -m app.medini.ml.validate_framework_readings --chart gandhi
"""
from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from typing import Final, Mapping

from app.core.chart_model import Chart
from app.core.dkp_modulation import Ashrama, DKPContext
from app.core.reading_composer import Reading, compose_reading

logger = logging.getLogger(__name__)


# ─── Canonical natal charts (Lahiri sidereal) ────────────────────────


@dataclass(frozen=True)
class CanonicalChart:
    """A famous chart + DKP context + expert-expected observations."""
    key: str
    name: str
    birth_iso: str
    chart: Chart
    context: DKPContext
    expected_observations: tuple["ExpectedObservation", ...]


@dataclass(frozen=True)
class ExpectedObservation:
    """One expert observation about a chart.

    Used to score the framework reading: does the framework surface this
    observation (PASS), does it surface the opposite (FAIL), or does it
    say nothing about this topic (MISS)?
    """
    topic: str                          # short label e.g. "5H promise"
    bhava: int | None                   # 1-12 if bhava-scoped
    expected_label: str | None          # strong/medium/weak/afflicted
    expected_yoga_active: tuple[str, ...]  # yogas expert mentions as active
    expected_yoga_absent: tuple[str, ...]  # yogas expert mentions as NOT active
    source: str                         # K.N. Rao, Sanjay Rath, etc.
    note: str


# Mahatma Gandhi — 1869-10-02, 07:11 LMT, Porbandar
# Source: K.N. Rao "Yogis, Destiny and the Wheel of Time" + Sanjay Rath
GANDHI = CanonicalChart(
    key="gandhi",
    name="Mahatma Gandhi",
    birth_iso="1869-10-02",
    chart=Chart(
        asc_sign=7, asc_lon=189.30,       # Libra Lagna
        planet_signs={
            "Sun": 6, "Moon": 8, "Mars": 8, "Mercury": 6,
            "Jupiter": 2, "Venus": 7, "Saturn": 8,
            "Rahu": 1, "Ketu": 7,
        },
        planet_houses={
            "Sun": 12, "Moon": 2, "Mars": 2, "Mercury": 12,
            "Jupiter": 8, "Venus": 1, "Saturn": 2,
            "Rahu": 7, "Ketu": 1,
        },
        planet_lons={
            "Sun": 165.60, "Moon": 217.40, "Mars": 220.20,
            "Mercury": 158.80, "Jupiter": 36.50, "Venus": 192.10,
            "Saturn": 225.40, "Rahu": 12.30, "Ketu": 192.30,
        },
        person_id="canonical-gandhi",
    ),
    context=DKPContext(
        birth_latitude=21.64, birth_longitude=69.62,
        current_residence_country="IN", climate_mahabhuta="pitta",
        birth_date_iso="1869-10-02", age_years=78.0,
        active_mundane_event="none", active_dasha_lord="Mars",
        ashrama=Ashrama.SANNYASA, marital_status="married",
        profession="political/spiritual leader", prashna="overall destiny",
    ),
    expected_observations=(
        ExpectedObservation(
            topic="Lagna lord (Venus) in own sign Libra in 1H",
            bhava=1, expected_label="strong",
            expected_yoga_active=("Malavya",),
            expected_yoga_absent=(),
            source="K.N. Rao",
            note="Venus in Libra in Lagna constitutes Malavya PMP yoga.",
        ),
        ExpectedObservation(
            topic="9H Jupiter (dharma karaka in own Taurus or Pisces)",
            bhava=9, expected_label="medium",
            expected_yoga_active=(),
            expected_yoga_absent=(),
            source="Sanjay Rath",
            note="Jupiter in 8H (deep occult) but its 9H aspect "
                 "preserves dharma signification.",
        ),
        ExpectedObservation(
            topic="10H career (karma) heavy malefic presence in 2H",
            bhava=10, expected_label="medium",
            expected_yoga_active=("Vipareeta Raja",),
            expected_yoga_absent=(),
            source="K.N. Rao",
            note="Saturn-Moon-Mars stellium in 2H gives intense karma; "
                 "Vipareeta Raja activates via dusthana lord placements.",
        ),
    ),
)

# Indira Gandhi — 1917-11-19, 23:11 IST, Allahabad
INDIRA = CanonicalChart(
    key="indira",
    name="Indira Gandhi",
    birth_iso="1917-11-19",
    chart=Chart(
        asc_sign=4, asc_lon=120.30,       # Cancer Lagna
        planet_signs={
            "Sun": 7, "Moon": 10, "Mars": 5, "Mercury": 8,
            "Jupiter": 3, "Venus": 8, "Saturn": 3,
            "Rahu": 5, "Ketu": 11,
        },
        planet_houses={
            "Sun": 4, "Moon": 7, "Mars": 2, "Mercury": 5,
            "Jupiter": 12, "Venus": 5, "Saturn": 12,
            "Rahu": 2, "Ketu": 8,
        },
        planet_lons={
            "Sun": 213.20, "Moon": 295.10, "Mars": 138.40,
            "Mercury": 218.40, "Jupiter": 67.80, "Venus": 240.20,
            "Saturn": 84.50, "Rahu": 134.30, "Ketu": 314.30,
        },
        person_id="canonical-indira",
    ),
    context=DKPContext(
        birth_latitude=25.45, birth_longitude=81.84,
        current_residence_country="IN", climate_mahabhuta="vata",
        birth_date_iso="1917-11-19", age_years=66.0,
        active_mundane_event="none", active_dasha_lord="Mars",
        ashrama=Ashrama.GRIHASTHA, marital_status="widowed",
        profession="Prime Minister", prashna="political destiny",
    ),
    expected_observations=(
        ExpectedObservation(
            topic="Cancer Lagna with Mars as Yogakaraka",
            bhava=10, expected_label="strong",
            expected_yoga_active=("Ruchaka",),
            expected_yoga_absent=(),
            source="Sanjay Rath",
            note="Cancer Lagna → Mars Yogakaraka (rules 5H Scorpio + 10H Aries); "
                 "if Mars exalted or in Kendra, Ruchaka activates.",
        ),
        ExpectedObservation(
            topic="7H Moon as karaka karmic husband-lord",
            bhava=7, expected_label="afflicted",
            expected_yoga_active=(),
            expected_yoga_absent=(),
            source="K.N. Rao",
            note="Widowhood doctrinally readable from afflicted 7H + "
                 "Sun-Mercury in 4H aspecting 10H.",
        ),
    ),
)

# Jawaharlal Nehru — 1889-11-14, 23:03 LMT, Allahabad
NEHRU = CanonicalChart(
    key="nehru",
    name="Jawaharlal Nehru",
    birth_iso="1889-11-14",
    chart=Chart(
        asc_sign=4, asc_lon=110.40,
        planet_signs={
            "Sun": 7, "Moon": 4, "Mars": 11, "Mercury": 7,
            "Jupiter": 5, "Venus": 6, "Saturn": 5,
            "Rahu": 5, "Ketu": 11,
        },
        planet_houses={
            "Sun": 4, "Moon": 1, "Mars": 8, "Mercury": 4,
            "Jupiter": 2, "Venus": 3, "Saturn": 2,
            "Rahu": 2, "Ketu": 8,
        },
        planet_lons={
            "Sun": 209.80, "Moon": 109.20, "Mars": 318.50,
            "Mercury": 198.30, "Jupiter": 138.20, "Venus": 174.60,
            "Saturn": 130.40, "Rahu": 122.10, "Ketu": 302.10,
        },
        person_id="canonical-nehru",
    ),
    context=DKPContext(
        birth_latitude=25.45, birth_longitude=81.84,
        current_residence_country="IN", climate_mahabhuta="vata",
        birth_date_iso="1889-11-14", age_years=74.0,
        active_mundane_event="none", active_dasha_lord="Saturn",
        ashrama=Ashrama.VANAPRASTHA, marital_status="widowed",
        profession="Prime Minister", prashna="political legacy",
    ),
    expected_observations=(
        ExpectedObservation(
            topic="Cancer Lagna intellectual leadership via Sun-Mercury 4H",
            bhava=4, expected_label="strong",
            expected_yoga_active=("Budha-Aditya",),
            expected_yoga_absent=(),
            source="Gopesh Kumar Ojha",
            note="Sun + Mercury conjunction in Libra (4H) → Budha-Aditya, "
                 "powerful intellect-with-status.",
        ),
        ExpectedObservation(
            topic="Moon in 1H (Cancer Lagna lord at home) — sensitivity",
            bhava=1, expected_label="strong",
            expected_yoga_active=(),
            expected_yoga_absent=(),
            source="K.N. Rao",
            note="Moon in own sign Cancer in Lagna gives emotional "
                 "sensitivity, characteristic of Nehru's writing voice.",
        ),
    ),
)

CANONICAL_CHARTS: Final[Mapping[str, CanonicalChart]] = {
    "gandhi": GANDHI,
    "indira": INDIRA,
    "nehru": NEHRU,
}


# ─── Comparison harness ──────────────────────────────────────────────


@dataclass(frozen=True)
class ObservationResult:
    """How the framework scored against one expert expectation."""
    topic: str
    status: str             # PASS / MISS / FAIL
    framework_label: str | None
    expected_label: str | None
    framework_yogas: tuple[str, ...]
    expected_yogas: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class ChartValidationReport:
    """Full validation report for one canonical chart."""
    chart_key: str
    chart_name: str
    n_observations: int
    n_pass: int
    n_miss: int
    n_fail: int
    results: tuple[ObservationResult, ...]
    framework_active_yogas: tuple[str, ...]


def _score_observation(
    obs: ExpectedObservation, reading: Reading,
) -> ObservationResult:
    """Score one expert observation against the framework reading."""
    framework_active_names = tuple(y.name for y in reading.active_yogas)
    fw_label: str | None = None
    if obs.bhava is not None:
        claim = reading.bhava_claims.get(obs.bhava)
        if claim is not None:
            fw_label = claim.verdict_label

    # Status logic
    status = "MISS"
    if obs.expected_label is not None and fw_label is not None:
        if fw_label == obs.expected_label:
            status = "PASS"
        elif {fw_label, obs.expected_label} <= {"weak", "afflicted"}:
            status = "PASS"  # treat weak/afflicted as equivalent doctrinally
        elif {fw_label, obs.expected_label} <= {"strong", "medium"}:
            status = "PASS" if obs.expected_label == "medium" else "MISS"
        else:
            status = "FAIL"  # directional disagreement

    # Yoga overlap check
    if obs.expected_yoga_active:
        expected_present = any(y in framework_active_names for y in obs.expected_yoga_active)
        if not expected_present:
            status = "MISS"
    if obs.expected_yoga_absent:
        wrong_present = any(y in framework_active_names for y in obs.expected_yoga_absent)
        if wrong_present:
            status = "FAIL"

    return ObservationResult(
        topic=obs.topic,
        status=status,
        framework_label=fw_label,
        expected_label=obs.expected_label,
        framework_yogas=framework_active_names,
        expected_yogas=obs.expected_yoga_active,
        note=obs.note,
    )


def validate_chart(canonical: CanonicalChart) -> ChartValidationReport:
    """Run framework on one canonical chart and score against expectations."""
    reading = compose_reading(canonical.chart, canonical.context)
    results = tuple(
        _score_observation(obs, reading)
        for obs in canonical.expected_observations
    )
    return ChartValidationReport(
        chart_key=canonical.key,
        chart_name=canonical.name,
        n_observations=len(results),
        n_pass=sum(1 for r in results if r.status == "PASS"),
        n_miss=sum(1 for r in results if r.status == "MISS"),
        n_fail=sum(1 for r in results if r.status == "FAIL"),
        results=results,
        framework_active_yogas=tuple(y.name for y in reading.active_yogas),
    )


def format_report(report: ChartValidationReport) -> str:
    """Plain-text rendering of one validation report."""
    lines = [
        "=" * 70,
        f"CHART: {report.chart_name} ({report.chart_key})",
        "=" * 70,
        f"Observations: {report.n_observations}  "
        f"PASS={report.n_pass}  MISS={report.n_miss}  FAIL={report.n_fail}",
        "",
        f"Framework active yogas: {', '.join(report.framework_active_yogas) or '(none)'}",
        "",
    ]
    for r in report.results:
        lines.append(f"[{r.status:>4s}] {r.topic}")
        lines.append(f"        expected={r.expected_label or '-'}, framework={r.framework_label or '-'}")
        if r.expected_yogas:
            present = [y for y in r.expected_yogas if y in r.framework_yogas]
            absent = [y for y in r.expected_yogas if y not in r.framework_yogas]
            lines.append(
                f"        expert yogas: present={present}, absent={absent}"
            )
        lines.append(f"        note: {r.note}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chart", choices=list(CANONICAL_CHARTS.keys()) + ["all"],
        default="all",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    keys = list(CANONICAL_CHARTS) if args.chart == "all" else [args.chart]
    overall_pass = overall_miss = overall_fail = 0
    for k in keys:
        report = validate_chart(CANONICAL_CHARTS[k])
        print(format_report(report))
        overall_pass += report.n_pass
        overall_miss += report.n_miss
        overall_fail += report.n_fail
    print("=" * 70)
    print(f"OVERALL: PASS={overall_pass} MISS={overall_miss} FAIL={overall_fail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
