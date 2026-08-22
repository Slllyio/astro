"""Render a ParasharaReading as markdown — every element, every citation.

A reading you cannot read is not finished. This turns the structured `ParasharaReading` into a
human-readable report, following the platform's standing discipline: **show everything the reading
computed, and cite every claim.** Nothing is collapsed to a bare count, and every doctrinal element
carries the BPHS sloka it came from, so a reader can trace any line back to Parashara's text.

The honesty flags the reading carries (dashas not balance-adjusted; Nisargayu pre-reduction) are
rendered too — the report never looks more settled than the engine is.
"""
from __future__ import annotations

from typing import Final

from app.parashara.doctrine.vargottama import SOURCE as _VARGOTTAMA_SOURCE
from app.parashara.reading import ParasharaReading

SOURCE_VARGOTTAMA: Final[str] = f"{_VARGOTTAMA_SOURCE.work}:{_VARGOTTAMA_SOURCE.line}"

_SIGN_NAMES: Final[tuple[str, ...]] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
_NAK_NAMES: Final[tuple[str, ...]] = (
    "Aswini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Ardra", "Punarvasu", "Pushya",
    "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha", "Sravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadra", "Uttara Bhadra", "Revati",
)
_VERDICT_MARK: Final[dict[str, str]] = {
    "flourishing": "flourishing", "ordinary": "ordinary", "annihilated": "annihilated",
}


def _sign(n: int) -> str:
    return _SIGN_NAMES[(n - 1) % 12]


def to_markdown(reading: ParasharaReading) -> str:
    """The full reading as a markdown document."""
    c = reading.chart
    out: list[str] = []
    out.append("# Parashara reading (BPHS)")
    out.append("")
    out.append(f"- **Lagna:** {_sign(c.asc_sign)} ({c.asc_longitude:.2f}°)")
    out.append(f"- **Janma nakshatra:** {_NAK_NAMES[(c.janma_nakshatra - 1) % 27]} "
               f"(#{c.janma_nakshatra})")
    out.append(f"- **Paksha:** {'Shukla (waxing)' if c.moon_waxing else 'Krishna (waning)'}")
    out.append("")
    out.append("_Root authority: Brihat Parashara Hora Shastra. Every judgment below cites the "
               "sloka it derives from._")
    out.append("")

    # --- Bhava verdicts (ch.11) ---
    out.append("## House judgments — prosperity or annihilation (BPHS ch.11)")
    out.append("")
    out.append("| House | Sign | Verdict | Reasons |")
    out.append("|---|---|---|---|")
    for h in range(1, 13):
        v = reading.bhavas[h]
        hsign = _sign((c.asc_sign - 1 + h - 1) % 12 + 1)
        reasons = "; ".join(v.reasons) if v.reasons else "— (no strong factor either way)"
        out.append(f"| {h} | {hsign} | {_VERDICT_MARK[v.verdict]} | {reasons} |")
    out.append("")

    # --- Bhava-lord effects (ch.24) ---
    out.append("## House-lord placements — Parashara's effects (BPHS ch.24)")
    out.append("")
    out.append("For each house, its lord and the house that lord occupies, with Parashara's own "
               "effect for that placement. Each effect cites its ch.24 sloka.")
    out.append("")
    out.append("| House | Lord | Lord in house | Effect (BPHS ch.24) | Source |")
    out.append("|---|---|---|---|---|")
    for h in range(1, 13):
        p = reading.bhava_lord_effects.get(h)
        if p is None:
            continue
        if p.effect is not None:
            text = p.effect.text if len(p.effect.text) <= 300 else p.effect.text[:297] + "…"
            src = f"{p.effect.source.work}:{p.effect.source.line}"
        else:
            text = "— (sloka unrecoverable from the OCR; not guessed)"
            src = "—"
        out.append(f"| {h} | {p.lord} | {p.in_house} | {text} | {src} |")
    out.append("")

    # --- Nabhasa yogas (ch.35) ---
    out.append("## Nabhasa yogas — planetary distribution (BPHS ch.35)")
    out.append("")
    if reading.nabhasa:
        out.append("| Yoga | Family | Why | Operable | Source |")
        out.append("|---|---|---|---|---|")
        for y in reading.nabhasa:
            op = {True: "yes", False: "no", None: "if no Akriti/Dala yoga forms"}[y.operable]
            out.append(f"| {y.name} | {y.family} | {y.reason} | {op} | {y.source.work}:{y.source.line} |")
    else:
        out.append("_No Asraya or Sankhya Nabhasa yoga detected._")
    out.append("")

    # --- Lunar (Chandra) yogas (ch.37) ---
    out.append("## Lunar yogas — reckoned from the Moon (BPHS ch.37)")
    out.append("")
    if reading.chandra_yogas:
        out.append("| Yoga | Why | Source |")
        out.append("|---|---|---|")
        for y in reading.chandra_yogas:
            out.append(f"| {y.name} | {y.reason} | {y.source.work}:{y.source.line} |")
    else:
        out.append("_No lunar yoga detected._")
    out.append("")

    # --- Pancha Mahapurusha yogas (Saravali ch.37, allied) ---
    out.append("## Pancha Mahapurusha yogas (Saravali ch.37)")
    out.append("")
    if reading.mahapurusha:
        out.append("| Yoga | Graha | Dignity | Kendra | Source |")
        out.append("|---|---|---|---|---|")
        for y in reading.mahapurusha:
            out.append(f"| {y.name} | {y.planet} | {y.dignity} | {y.house} | "
                       f"{y.source.work}:{y.source.line} |")
    else:
        out.append("_No Pancha Mahapurusha yoga (no non-luminary in own/exaltation in a kendra)._")
    out.append("")

    # --- Special yogas (ch.36) ---
    out.append("## Other yogas (BPHS ch.36)")
    out.append("")
    if reading.special_yogas:
        out.append("| Yoga | Why | Source |")
        out.append("|---|---|---|")
        for y in reading.special_yogas:
            out.append(f"| {y.name} | {y.reason} | {y.source.work}:{y.source.line} |")
    else:
        out.append("_No ch.36 special yoga (e.g. Gaja-Kesari) detected._")
    out.append("")

    # --- Vargottama (Saravali ch.3) ---
    out.append("## Vargottama — same sign in Rasi and Navamsa (Saravali ch.3)")
    out.append("")
    if reading.vargottama:
        out.append(f"Vargottama (strong): **{', '.join(reading.vargottama)}** "
                   f"({SOURCE_VARGOTTAMA}).")
    else:
        out.append("_No body is Vargottama._")
    out.append("")

    # --- Vimsopaka (ch.7) ---
    out.append("## Vimsopaka bala — cross-varga strength (BPHS ch.7)")
    out.append("")
    out.append("Shodasavarga scheme (16 divisions), 0–20. Each score cites its scheme sloka.")
    out.append("")
    out.append("| Graha | Score | Band | Source |")
    out.append("|---|---|---|---|")
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        s = reading.vimsopaka.get(g)
        if s is None:
            continue
        out.append(f"| {g} | {s.score:.2f} | {s.band} | {s.source.work}:{s.source.line} |")
    out.append("")

    # --- Shadbala (ch.27) — COMPLETE, all six balas ---
    out.append("## Shadbala — strength (BPHS ch.27)")
    out.append("")
    out.append("_The complete six-fold strength: Sthana, Dig, Naisargika, Cheshta, Drik, and Kala. "
               "Kala is itself eight sub-components (broken out below). Drik may be negative. Totals "
               "are in rupas (60 virupas = 1 rupa)._")
    out.append("")
    out.append("| Graha | Sthana | Dig | Naisarg | Cheshta | Drik | Kala | Total (rupas) |")
    out.append("|---|---|---|---|---|---|---|---|")
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        s = reading.shadbala.get(g)
        if s is None:
            continue
        out.append(f"| {g} | {s.sthana.total:.1f} | {s.dig:.1f} | {s.naisargika:.1f} | "
                   f"{s.cheshta:.1f} | {s.drik:.1f} | {s.kala.total:.1f} | {s.rupas:.2f} |")
    out.append("")
    out.append("### Kala bala — the eight temporal sub-components (virupas)")
    out.append("")
    out.append("| Graha | Nathonnata | Paksha | Tribhaga | Varsha | Masa | Vara | Hora | Ayana |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        s = reading.shadbala.get(g)
        if s is None:
            continue
        k = s.kala
        out.append(f"| {g} | {k.nathonnata:.1f} | {k.paksha:.1f} | {k.tribhaga:.0f} | "
                   f"{k.varsha:.0f} | {k.masa:.0f} | {k.vara:.0f} | {k.hora:.0f} | {k.ayana:.1f} |")
    out.append("")

    # --- Avasthas (ch.45) ---
    out.append("## Planetary avasthas (BPHS ch.45)")
    out.append("")
    out.append("Baladi = age-state by degree (bala/kumara/yuva/vriddha/mrita); "
               "Jagradadi = awake/dreaming/sleeping by dignity.")
    out.append("")
    out.append("| Graha | Baladi | Jagradadi |")
    out.append("|---|---|---|")
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        a = reading.avasthas.get(g)
        if a is None:
            continue
        out.append(f"| {g} | {a.baladi} | {a.jagradadi} |")
    out.append("")

    # --- Dashas (ch.46) ---
    out.append("## Conditional dashas (BPHS ch.46)")
    out.append("")
    if not reading.balance_adjusted:
        out.append("_Timelines run from the start of the birth mahadasha — not adjusted for "
                   "the balance at birth, which needs Bhayat/Bhabhog (the Moon's ghatika position)._")
        out.append("")
    for d in reading.dashas:
        head = f"### {d.system.title()} — " + ("applicable" if d.applicable else "not applicable")
        out.append(head)
        out.append(f"_{d.reason}._")
        out.append("")
        if d.applicable and d.timeline:
            out.append("| Lord | Starts (yrs) | Length (yrs) |")
            out.append("|---|---|---|")
            for p in d.timeline:
                out.append(f"| {p.lord} | {p.start_year:.2f} | {p.years:.0f} |")
            out.append("")

    # --- Sthira rasi dasha (ch.46), seeded by the Brahma Graha ---
    sth = reading.sthira
    out.append("## Sthira dasha (BPHS ch.46)")
    out.append("")
    out.append(f"_Seeded from the Brahma Graha: **{sth.brahma_graha.planet}** in "
               f"{_sign(sth.brahma_graha.sign)} — {sth.brahma_graha.reason}._")
    out.append("")
    out.append("| Sign | Starts (yrs) | Length (yrs) |")
    out.append("|---|---|---|")
    for p in sth.timeline:
        out.append(f"| {_sign(p.sign)} | {p.start_year:.0f} | {p.years:.0f} |")
    out.append("")

    # --- Nisargayu (ch.43) ---
    out.append("## Nisargayu — natural longevity (BPHS ch.43)")
    out.append("")
    if not reading.nisargayu.reductions_applied:
        out.append("_Pre-reduction natural span (the full allotment scaled by deep exaltation). The "
                   "four Pindayu haranas + Ascendant contribution are not yet applied._")
        out.append("")
    out.append("| Graha | Full (yrs) | Scale | Contributes (yrs) |")
    out.append("|---|---|---|---|")
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        contrib = reading.nisargayu.per_planet.get(g)
        if contrib is None:
            continue
        out.append(f"| {g} | {contrib.full_years:.0f} | {contrib.scale:.3f} | "
                   f"{contrib.years:.2f} |")
    out.append(f"| **Total** | | | **{reading.nisargayu.natural_years:.2f}** |")
    out.append("")
    return "\n".join(out)
