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
from app.parashara.doctrine.saravali_grids import normalize_house_phrase
from app.parashara.doctrine.chara_karaka import ROLE_NAMES
from app.parashara.doctrine.karakamsa_effects import karakamsa_in_signs
from app.parashara.primitives.ashtakavarga import sav_band as _sav_band
from app.parashara.primitives.yogini_dasha import YOGINI_BY_LORD as _YOGINI_BY_LORD
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

    # --- Functional nature by lagna (ch.34) ---
    out.append("## Functional nature of the grahas for this lagna (BPHS ch.34)")
    out.append("")
    yk = ", ".join(reading.yogakarakas) if reading.yogakarakas else "none"
    mk = ", ".join(reading.marakas) if reading.marakas else "none"
    out.append(f"Yogakaraka(s): **{yk}**. Maraka (killer) lords: {mk}.")
    out.append("")
    out.append("| Graha | Functional nature | Maraka? |")
    out.append("|---|---|---|")
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        cls = reading.functional_class.get(g, "—")
        out.append(f"| {g} | {cls} | {'yes' if g in reading.marakas else '—'} |")
    out.append("")
    if reading.maraka_planets:
        out.append("Maraka (death-dealing) planets — their dasha/bhukti periods are classically "
                   "life-sensitive (BPHS ch.44):")
        out.append("")
        out.append("| Graha | Why | Source |")
        out.append("|---|---|---|")
        for m in reading.maraka_planets:
            out.append(f"| {m.planet} | {m.reason} | {m.source.work}:{m.source.line} |")
        out.append("")

    # --- Shodasavarga (BPHS ch.6-7) ---
    _SIGN_ABBR = ("Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi")
    from app.parashara.chart.shodasavarga import VARGAS as _VARGAS, DIVISIONS_SOURCE as _VSRC
    out.append("## Shodasavarga — the sixteen divisional charts (BPHS ch.6–7)")
    out.append("")
    out.append(f"Each body's sign in all sixteen vargas (BPHS-6:{_VSRC.line}). D1=Rasi, D9=Navamsa "
               "(dharma/marriage), D10=Dasamsa (career), D60=Shashtiamsa.")
    out.append("")
    header = "| Body | " + " | ".join(f"{t}·{name[:4]}" for t, _, name in _VARGAS) + " |"
    out.append(header)
    out.append("|" + "---|" * (len(_VARGAS) + 1))
    for body in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
        row = reading.shodasavarga.get(body)
        if row is None:
            continue
        cells = " | ".join(_SIGN_ABBR[row[t] - 1] for t, _, _ in _VARGAS)
        out.append(f"| {body} | {cells} |")
    out.append("")

    # --- Upagrahas (BPHS ch.3 sl.61-64) ---
    out.append("## Upagrahas — Sun-derived sub-planets (BPHS ch.3)")
    out.append("")
    out.append("The five Aprakasa grahas computed from the Sun's longitude (BPHS-3:1173); malefic by "
               "nature. Gulika/Mandi (the Saturn-based upagraha) is shown separately below.")
    out.append("")
    out.append("| Upagraha | Longitude | Sign |")
    out.append("|---|---|---|")
    for name in ("Dhuma", "Vyatipata", "Parivesha", "Indrachapa", "Upaketu"):
        lon = reading.upagrahas.get(name)
        if lon is None:
            continue
        out.append(f"| {name} | {lon:.2f}° | {_SIGN_NAMES[int(lon // 30)]} |")
    out.append("")
    if reading.upagraha_house_effects:
        out.append("Effect of each upagraha in the house it occupies (BPHS ch.25):")
        out.append("")
        out.append("| Upagraha | House | Effect | Source |")
        out.append("|---|---|---|---|")
        for name in ("Dhuma", "Vyatipata", "Parivesha", "Indrachapa", "Upaketu"):
            ue = reading.upagraha_house_effects.get(name)
            if ue is None:
                continue
            house, s = ue
            text = s.text if len(s.text) <= 300 else s.text[:297] + "…"
            out.append(f"| {name} | {house} | {text} | {s.source.work}:{s.source.line} |")
        out.append("")

    # --- Planet-in-house effects (Saravali ch.30) ---
    out.append("## Planet-in-house effects (Saravali ch.30)")
    out.append("")
    out.append("Each graha's effect in the house it occupies — the allied planet grid BPHS lacks "
               "(BPHS gives only lords-in-houses, ch.24). Each cell cites its Saravali sloka.")
    out.append("")
    out.append("| Graha | House | Effect | Source |")
    out.append("|---|---|---|---|")
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        pe = reading.planet_house_effects.get(g)
        if pe is None:
            continue
        house, s = pe
        text = normalize_house_phrase(s.text, house)
        text = text if len(text) <= 300 else text[:297] + "…"
        out.append(f"| {g} | {house} | {text} | {s.source.work}:{s.source.line} |")
    out.append("")

    # --- Chara karakas + Karakamsa (BPHS ch.32-33) ---
    out.append("## Chara karakas & Karakamsa (BPHS ch.32–33)")
    out.append("")
    out.append("Parashara's 7 movable karakas — the visible planets ranked by degree within their "
               "sign (BPHS-32:60). The 7-planet scheme is Parashara's own primary; the 8th (Rahu, "
               "degree-inverted) is the \"some say\" minority BPHS-32:152 names, not used — the "
               "Atmakaraka is never a node.")
    out.append("")
    out.append("| Role | Karaka | Planet |")
    out.append("|---|---|---|")
    for role in ("AK", "AmK", "BK", "MK", "PiK", "GK", "DK"):
        planet = reading.chara_karakas.get(role)
        if planet:
            out.append(f"| {role} | {ROLE_NAMES[role]} | {planet} |")
    out.append("")
    ks = reading.karakamsa_sign
    out.append(f"**Karakamsa** (navamsa sign of the Atmakaraka, the ch.33 reading-lagna): "
               f"{_SIGN_NAMES[ks - 1]}.")
    out.append("")
    _ksign = karakamsa_in_signs()
    if _ksign is not None:
        out.append(f"Parashara's effects by the Karakamsa's sign ({_ksign.source.work}:"
                   f"{_ksign.source.line}) — locate {_SIGN_NAMES[ks - 1]} in the passage:")
        out.append("")
        out.append("> " + _ksign.text)
        out.append("")

    # --- Two-planet conjunctions (Saravali ch.15) ---
    if reading.conjunctions:
        out.append("## Two-planet conjunctions (Saravali ch.15)")
        out.append("")
        out.append("Grahas sharing a sign, with Saravali's effect for that pair (the 21-pair grid "
                   "BPHS lacks).")
        out.append("")
        out.append("| Pair | Effect | Source |")
        out.append("|---|---|---|")
        for pair, s in reading.conjunctions:
            name = " + ".join(sorted(pair))
            text = s.text if len(s.text) <= 300 else s.text[:297] + "…"
            out.append(f"| {name} | {text} | {s.source.work}:{s.source.line} |")
        out.append("")
        if reading.triple_conjunctions:
            out.append("Three grahas sharing a sign (Saravali ch.16):")
            out.append("")
            out.append("| Triple | Effect | Source |")
            out.append("|---|---|---|")
            for trio, s in reading.triple_conjunctions:
                name = " + ".join(sorted(trio))
                text = s.text if len(s.text) <= 300 else s.text[:297] + "…"
                out.append(f"| {name} | {text} | {s.source.work}:{s.source.line} |")
            out.append("")

    # --- Dignity concentrations (Saravali ch.45) ---
    if reading.dignity_concentrations:
        out.append("## Dignity concentrations (Saravali ch.45)")
        out.append("")
        out.append("When two or more grahas simultaneously hold the same dignity, Saravali gives a "
                   "distinct verdict (two exalted → rich and famous; all seven → \"an emperor\"). "
                   "BPHS has the dignity tables but no such concentration rule.")
        out.append("")
        out.append("| Dignity | Grahas | Verdict | Source |")
        out.append("|---|---|---|---|")
        for dignity in ("exalted", "moolatrikona", "own", "friendly", "debilitated"):
            hit = reading.dignity_concentrations.get(dignity)
            if hit is None:
                continue
            n, s = hit
            text = s.text if len(s.text) <= 300 else s.text[:297] + "…"
            out.append(f"| {dignity} | {n} | {text} | {s.source.work}:{s.source.line} |")
        out.append("")

    # --- Gulika (ch.3 / ch.25) ---
    out.append("## Gulika (Mandi) — the chief non-luminous point (BPHS ch.3, ch.25)")
    out.append("")
    ge = reading.gulika_effect
    out.append(f"Gulika is in **{_sign(reading.gulika_sign)}**, the **{reading.gulika_house}th** "
               f"house from the lagna.")
    out.append("")
    if ge is not None and ge.text:
        out.append(f"_Effect ({ge.source.work}:{ge.source.line}):_ {ge.text}")
    else:
        out.append("_Effect for this house not recoverable from the OCR (not guessed)._")
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

    # --- Richer bhava verdict (ch.11 + strength + yoga) ---
    out.append("## House judgments — richer verdict: ch.11 + strength + yoga")
    out.append("")
    out.append("The ch.11 method extended by Parashara's own strength and yoga signals — the lord's "
               "Vimsopaka band (ch.7), the karaka's dignity (ch.32), the house's Sarvashtakavarga "
               "bindus (ch.66), and any Pancha Mahapurusha yoga on the lord/karaka. Same net-vote "
               "rule as ch.11; every added vote cites its own sloka.")
    out.append("")
    out.append("| House | Sign | Richer verdict | ch.11 | Votes (p/a) | Factors |")
    out.append("|---|---|---|---|---|---|")
    for h in range(1, 13):
        rv = reading.richer_bhavas[h]
        hsign = _sign((c.asc_sign - 1 + h - 1) % 12 + 1)
        factors = "; ".join(rv.factors) if rv.factors else "— (no factor either way)"
        out.append(f"| {h} | {hsign} | {rv.graded} | {_VERDICT_MARK[rv.base.verdict]} "
                   f"| {rv.prosperity_votes}/{rv.annihilation_votes} | {factors} |")
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

    # --- Argala (ch.31) ---
    out.append("## Argala — planetary intervention on each house (BPHS ch.31)")
    out.append("")
    out.append("Planets in the 2nd/4th/11th/5th from a house cause argala; those in the 12th/10th/"
               "3rd/9th obstruct it. A prevailing argala (unobstructed or out-numbering) is shown.")
    out.append("")
    out.append("| House | Sign | Prevailing argalas |")
    out.append("|---|---|---|")
    for h in range(1, 13):
        hsign = (c.asc_sign - 1 + h - 1) % 12 + 1
        prevailing = [a for a in reading.argala.get(h, ()) if a.prevails]
        if prevailing:
            desc = "; ".join(
                f"{'Vipareeta ' if a.vipareeta else ''}{a.argala_house}th "
                f"({', '.join(a.argala_planets)})" for a in prevailing)
        else:
            desc = "— (none prevail)"
        out.append(f"| {h} | {_sign(hsign)} | {desc} |")
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

    # --- Solar yogas (ch.38) ---
    out.append("## Solar yogas — reckoned from the Sun (BPHS ch.38)")
    out.append("")
    if reading.solar_yogas:
        out.append("| Yoga | Why | Source |")
        out.append("|---|---|---|")
        for y in reading.solar_yogas:
            out.append(f"| {y.name} | {y.reason} | {y.source.work}:{y.source.line} |")
    else:
        out.append("_No solar yoga detected._")
    out.append("")

    # --- Pancha Mahapurusha yogas (Saravali ch.37, allied) ---
    out.append("## Pancha Mahapurusha yogas (Saravali ch.37)")
    out.append("")
    if reading.mahapurusha:
        out.append("| Yoga | Graha | Dignity | Kendra | Definition | Effect |")
        out.append("|---|---|---|---|---|---|")
        for y in reading.mahapurusha:
            out.append(f"| {y.name} | {y.planet} | {y.dignity} | {y.house} | "
                       f"{y.source.work}:{y.source.line} | {y.effect.work}:{y.effect.line} |")
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
    out.append("| Graha | Score | Band | Parashara's phrasing | Source |")
    out.append("|---|---|---|---|---|")
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        s = reading.vimsopaka.get(g)
        if s is None:
            continue
        out.append(f"| {g} | {s.score:.2f} | {s.band} | {s.verdict} | {s.source.work}:{s.source.line} |")
    out.append("")
    out.append("Per-division Varga Viswa (which of the 16 divisions hold each graha's dignity):")
    out.append("")
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        s = reading.vimsopaka.get(g)
        if s is None or not s.per_varga:
            continue
        parts = ", ".join(f"{tag} {val:.2f}" for tag, val in s.per_varga.items())
        out.append(f"- **{g}**: {parts}")
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
    out.append("### Sthana bala — the five positional sub-components (virupas)")
    out.append("")
    out.append("| Graha | Uchcha | Saptavargaja | Ojhayugma | Kendradi | Drekkana |")
    out.append("|---|---|---|---|---|---|")
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        s = reading.shadbala.get(g)
        if s is None:
            continue
        st = s.sthana
        out.append(f"| {g} | {st.uchcha:.1f} | {st.saptavargaja:.1f} | {st.ojhayugmarasiamsa:.1f} | "
                   f"{st.kendradi:.1f} | {st.drekkana:.1f} |")
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

    # --- Ashtakavarga (ch.66) ---
    out.append("## Ashtakavarga (BPHS ch.66)")
    out.append("")
    out.append("Sarvashtakavarga (SAV) bindus per house from the lagna (the total across all signs is "
               "always 337), then each graha's Bhinnashtakavarga.")
    out.append("")
    out.append("SAV bands (BPHS-72): >30 favourable, 25-30 medium, <25 adverse.")
    out.append("")
    out.append("| House | Sign | SAV bindus | Band |")
    out.append("|---|---|---|---|")
    for h in range(1, 13):
        hsign = (c.asc_sign - 1 + h - 1) % 12 + 1
        b = reading.sav.get(hsign, 0)
        out.append(f"| {h} | {_sign(hsign)} | {b} | {_sav_band(b)} |")
    out.append(f"| **Total** | | **{sum(reading.sav.values())}** | |")
    out.append("")
    out.append("| Graha | " + " | ".join(_sign(s) for s in range(1, 13)) + " | Total |")
    out.append("|---|" + "---|" * 13)
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        row = reading.bav.get(g, {})
        cells = " | ".join(str(row.get(s, 0)) for s in range(1, 13))
        out.append(f"| {g} | {cells} | {sum(row.values())} |")
    out.append("")

    # --- Avasthas (ch.45) ---
    out.append("## Planetary avasthas (BPHS ch.45)")
    out.append("")
    out.append("Baladi = age-state by degree (bala/kumara/yuva/vriddha/mrita); "
               "Jagradadi = awake/dreaming/sleeping by dignity; "
               "Deeptadi = dignity/placement state (+Vikala if with a malefic, +Kopa if combust). "
               "Grades are Parashara's result-strength (1.0 full / 0.5 half / 0.0 nil).")
    out.append("")
    out.append("| Graha | Baladi (grade) | Jagradadi (grade) | Deeptadi |")
    out.append("|---|---|---|---|")
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        a = reading.avasthas.get(g)
        if a is None:
            continue
        deept = a.deeptadi + (" +Vikala" if a.deeptadi_vikala else "") + (" +Kopa" if a.deeptadi_kopa else "")
        out.append(f"| {g} | {a.baladi} ({a.baladi_grade:.2f}) | "
                   f"{a.jagradadi} ({a.jagradadi_grade:.2f}) | {deept} |")
    out.append("")

    # --- Dashas (ch.46) ---
    out.append("## Conditional dashas (BPHS ch.46)")
    out.append("")
    if reading.balance_adjusted:
        out.append("_Dates are birth-balance-adjusted: the birth mahadasha shows its remaining span "
                   "from the Moon's arc through its nakshatra (BPHS-46:21-22, arc-proportional "
                   "Bhayat/Bhabhog). Years-after-birth; negative bhukti dates began before birth._")
        out.append("")
    for d in reading.dashas:
        head = f"### {d.system.title()} — " + ("applicable" if d.applicable else "not applicable")
        out.append(head)
        out.append(f"_{d.reason}._")
        out.append("")
        if d.applicable and d.timeline:
            is_yogini = d.system == "yogini"
            maraka_lords = {m.planet for m in reading.maraka_planets}
            out.append(("| Yogini | Lord | Starts (yrs) | Length (yrs) | Maraka? |" if is_yogini
                        else "| Lord | Starts (yrs) | Length (yrs) | Maraka? |"))
            out.append("|---|---|---|---|---|" if is_yogini else "|---|---|---|---|")
            for p in d.timeline:
                mk = "maraka" if p.lord in maraka_lords else "—"
                if is_yogini:
                    out.append(f"| {_YOGINI_BY_LORD.get(p.lord, '?')} | {p.lord} | "
                               f"{p.start_year:.2f} | {p.years:.0f} | {mk} |")
                else:
                    out.append(f"| {p.lord} | {p.start_year:.2f} | {p.years:.0f} | {mk} |")
            out.append("")
        if d.applicable and d.bhuktis:
            out.append("Antardashas (bhuktis) within each mahadasha (BPHS-46:110):")
            out.append("")
            for md_lord, bh in d.bhuktis:
                parts = ", ".join(f"{p.lord} {p.years:.2f}y" for p in bh)
                out.append(f"- **{md_lord}** MD: {parts}")
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

    # --- Nisargayu after the four haranas (ch.43 sl.567) ---
    hs = reading.nisargayu_haranas
    out.append("### After the four haranas (BPHS-43:567)")
    out.append("")
    out.append("_The four Pindayu reductions applied to Nisargayu — Astangata (combust), Satru "
               "Kshetra (enemy sign), Vyayadi (12th–7th), Kroorodaya (malefic in lagna); only the "
               "highest per graha (BPHS-43:392). The Ascendant's own contribution is not yet added._")
    out.append("")
    out.append("| Graha | Pre (yrs) | Reduction | Via | After (yrs) |")
    out.append("|---|---|---|---|---|")
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        r = hs.per_planet.get(g)
        c = hs.contributions.get(g)
        if r is None or c is None:
            continue
        out.append(f"| {g} | {c.years:.2f} | {r.net * 100:.0f}% | {r.reason} | "
                   f"{c.years * (1 - r.net):.2f} |")
    out.append(f"| **Total** | **{reading.nisargayu.natural_years:.2f}** | | | "
               f"**{hs.planetary_years:.2f}** |")
    out.append("")
    return "\n".join(out)
