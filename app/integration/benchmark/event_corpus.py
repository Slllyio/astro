"""Ground-truth event corpus for the famous-chart benchmark.

For each well-documented historical figure, lists known major life events
with date + domain + polarity. Sources are encyclopedic (Wikipedia,
Astro-Databank); events selected are unambiguous public-record facts.

Polarity mapping:
- "positive" — event is widely regarded as positive within the domain.
- "negative" — widely regarded as negative.
- "mixed" — significant but ambiguous (e.g. marriage that later dissolved).

The polarity attempts to capture WHAT the event represented at the time
it occurred, not its eventual outcome. Einstein's first marriage was
positive when contracted (1903); the divorce (1919) is a separate event.

DOCTRINE: This is a CALIBRATION CORPUS, not validation of doctrine.
Doctrine is axiomatic; we just check whether the engine's verdicts at
event dates align with documented outcomes.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Domain = Literal["career", "marriage", "children", "wealth", "health", "education"]
Polarity = Literal["positive", "negative", "mixed"]


class FamousChart(BaseModel):
    """Birth data for a famous historical figure."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    dob: str  # YYYY-MM-DD
    time: str  # HH:MM
    tz: str  # e.g. "+00:00"
    lat: float
    lon: float
    source: str


class FamousEvent(BaseModel):
    """One ground-truth life event for a chart."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chart_name: str
    event_date: str  # YYYY-MM-DD
    domain: str  # "career" / "marriage" / etc.
    polarity: str  # "positive" / "negative" / "mixed"
    description: str
    source: str = "Wikipedia"


# ---------------------------------------------------------------------------
# Charts (mirror tests/reading/famous_charts/*.json)
# ---------------------------------------------------------------------------

CHART_REGISTRY: dict[str, FamousChart] = {
    "einstein": FamousChart(
        name="Albert Einstein",
        dob="1879-03-14", time="11:30", tz="+00:00",
        lat=48.4011, lon=9.9876,
        source="Astro-Databank / Ulm Germany",
    ),
    "gandhi": FamousChart(
        name="Mahatma Gandhi",
        dob="1869-10-02", time="07:33", tz="+04:39",
        lat=21.6422, lon=69.6093,
        source="Astro-Databank / Porbandar India",
    ),
    "obama": FamousChart(
        name="Barack Obama",
        dob="1961-08-04", time="19:24", tz="-10:00",
        lat=21.3069, lon=-157.8583,
        source="Astro-Databank / Honolulu HI",
    ),
    "steve_jobs": FamousChart(
        name="Steve Jobs",
        dob="1955-02-24", time="19:15", tz="-08:00",
        lat=37.7749, lon=-122.4194,
        source="Astro-Databank / San Francisco CA",
    ),
    "apj_kalam": FamousChart(
        name="A.P.J. Abdul Kalam",
        dob="1931-10-15", time="01:00", tz="+05:30",
        lat=9.2876, lon=79.3129,
        source="Wikipedia / Rameswaram India",
    ),
    "ramana_maharshi": FamousChart(
        name="Ramana Maharshi",
        dob="1879-12-30", time="01:00", tz="+05:30",
        lat=10.1632, lon=78.7656,
        source="Wikipedia / Tiruchuli India",
    ),
}


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

FAMOUS_EVENTS: list[FamousEvent] = [
    # Einstein
    FamousEvent(
        chart_name="einstein",
        event_date="1903-01-06",
        domain="marriage",
        polarity="positive",
        description="Marries Mileva Maric in Bern",
    ),
    FamousEvent(
        chart_name="einstein",
        event_date="1905-03-17",
        domain="career",
        polarity="positive",
        description="Annus Mirabilis — 4 landmark papers including special relativity",
    ),
    FamousEvent(
        chart_name="einstein",
        event_date="1919-02-14",
        domain="marriage",
        polarity="negative",
        description="Divorce finalized from Mileva Maric",
    ),
    FamousEvent(
        chart_name="einstein",
        event_date="1921-11-10",
        domain="career",
        polarity="positive",
        description="Awarded Nobel Prize in Physics (for 1921)",
    ),

    # Gandhi
    FamousEvent(
        chart_name="gandhi",
        event_date="1883-05-14",
        domain="marriage",
        polarity="positive",
        description="Marries Kasturba Makanji",
    ),
    FamousEvent(
        chart_name="gandhi",
        event_date="1893-04-23",
        domain="career",
        polarity="positive",
        description="Sails to South Africa to take legal case — career launch",
    ),
    FamousEvent(
        chart_name="gandhi",
        event_date="1930-03-12",
        domain="career",
        polarity="positive",
        description="Salt March begins — Civil Disobedience Movement",
    ),
    FamousEvent(
        chart_name="gandhi",
        event_date="1948-01-30",
        domain="health",
        polarity="negative",
        description="Assassinated by Nathuram Godse, New Delhi",
    ),

    # Obama
    FamousEvent(
        chart_name="obama",
        event_date="1992-10-03",
        domain="marriage",
        polarity="positive",
        description="Marries Michelle Robinson in Chicago",
    ),
    FamousEvent(
        chart_name="obama",
        event_date="1998-07-04",
        domain="children",
        polarity="positive",
        description="Daughter Malia born",
    ),
    FamousEvent(
        chart_name="obama",
        event_date="2004-11-02",
        domain="career",
        polarity="positive",
        description="Elected to US Senate from Illinois",
    ),
    FamousEvent(
        chart_name="obama",
        event_date="2008-11-04",
        domain="career",
        polarity="positive",
        description="Elected 44th President of the United States",
    ),
    FamousEvent(
        chart_name="obama",
        event_date="2012-11-06",
        domain="career",
        polarity="positive",
        description="Re-elected to a second presidential term",
    ),

    # Steve Jobs
    FamousEvent(
        chart_name="steve_jobs",
        event_date="1976-04-01",
        domain="career",
        polarity="positive",
        description="Founds Apple Computer with Wozniak and Wayne",
    ),
    FamousEvent(
        chart_name="steve_jobs",
        event_date="1985-09-17",
        domain="career",
        polarity="negative",
        description="Resigns from Apple after losing power struggle",
    ),
    FamousEvent(
        chart_name="steve_jobs",
        event_date="1991-03-18",
        domain="marriage",
        polarity="positive",
        description="Marries Laurene Powell at Yosemite",
    ),
    FamousEvent(
        chart_name="steve_jobs",
        event_date="1997-09-16",
        domain="career",
        polarity="positive",
        description="Returns to Apple as interim CEO",
    ),
    FamousEvent(
        chart_name="steve_jobs",
        event_date="2003-10-21",
        domain="health",
        polarity="negative",
        description="Diagnosed with pancreatic cancer",
    ),
    FamousEvent(
        chart_name="steve_jobs",
        event_date="2011-10-05",
        domain="health",
        polarity="negative",
        description="Dies from complications of pancreatic cancer",
    ),

    # APJ Kalam
    FamousEvent(
        chart_name="apj_kalam",
        event_date="1998-05-11",
        domain="career",
        polarity="positive",
        description="Leads Pokhran-II nuclear tests as Chief Scientific Adviser",
    ),
    FamousEvent(
        chart_name="apj_kalam",
        event_date="2002-07-25",
        domain="career",
        polarity="positive",
        description="Sworn in as 11th President of India",
    ),
    FamousEvent(
        chart_name="apj_kalam",
        event_date="2015-07-27",
        domain="health",
        polarity="negative",
        description="Dies of cardiac arrest while delivering lecture",
    ),

    # Ramana Maharshi
    FamousEvent(
        chart_name="ramana_maharshi",
        event_date="1896-07-17",
        domain="education",
        polarity="positive",
        description="Death-experience awakening — self-realization",
    ),
    FamousEvent(
        chart_name="ramana_maharshi",
        event_date="1950-04-14",
        domain="health",
        polarity="negative",
        description="Mahasamadhi (death) at Sri Ramanasramam, Tiruvannamalai",
    ),
]
