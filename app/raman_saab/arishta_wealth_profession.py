"""Three user-requested chapters (v22-v24): Arishta & Bhanga, Profession synthesis,
the Wealth chapter — all PURE RE-READS (PREC-10) of computed judgments + cited tables.

v22 Arishta & Bhanga — Balarishta (HPA-14 yogas + antidotes, already computed), the
per-planet bhanga states (dignity vs bhanga-aware effective dignity), Kemadruma and its
cancellation, the fired longevity-protection combinations (HTJAH-II), the Ayurdaya band,
and Raman's antidote passage quoted verbatim (HPA-14:232-266).

v23 Profession synthesis — Raman devoted whole chapters to profession; this derives it
from EVERY encoded angle and then shows the convergence: the 10th sign's profile
(HTJAH-II CAREER_BY_SIGN), the navamsa-dispositor of the 10th lord (his primary method,
HTJAH-II:10249), the strongest planet, the Atmakaraka (the 7-karaka lock; the
karakamsa-profession DOCTRINE proper is Jaimini and stays outside the canon — the row
shown applies Raman's own vocation table to the AK, and says so), the running MD lord,
the H10 mode split (authority/trade/learned/labour signification verdicts), and the
career-kind fired yogas. Convergence = deterministic token overlap across the cited
vocation texts — a count, not a new judgment.

v24 Wealth chapter — not "wealth favourable" but the channels: earning style (the 2nd
lord's house -> SECOND_LORD_HOUSE_GAINS, HTJAH-I:2504+), accumulation (H2 wealth
verdict), gains channels (planets in the 11th -> PLANET_IN_11TH_GAINS,
HTJAH-II:14373-14386), inheritance (H8 legacies), sudden gains (H8), speculation (H5 +
the 2nd-lord-in-5th channel), authority/government (H10 profession_authority), service
vs trade vs learned vs labour (the H10 mode verdicts), land & property (H4 property),
foreign (H12 foreign_residence), and the periods of expansion (MD runs whose activated
houses include H2 or H11 at ordinary tier or better — the timeline's own rows).

Usage:
    from app.raman_saab.arishta_wealth_profession import (
        build_arishta_chapter, build_profession_synthesis, build_wealth_chapter)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Optional

from app.raman_saab.doctrine.sources import passage

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


# ── v22 Arishta & Bhanga ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ArishtaChapter:
    balarishta_applies: bool
    balarishta_cancelled: bool
    balarishta_reasons: tuple[str, ...]
    antidote_quote: str                     # HPA-14:232-266, verbatim
    antidote_cite: str
    bhangas: tuple[tuple[str, str, str], ...]   # (planet, dignity, effective_dignity)
    kemadruma_note: str
    protections: tuple[str, ...]            # fired longevity combos, cited class/span/desc
    band: str
    maraka_note: str
    # ── Wave-2 (2026-08-18 report-critique item 5d, append-only): the two no-bhanga
    # cases were collapsed into one ambiguous sentence — "no cancellation operates"
    # could mean "nothing is debilitated" (no question arises) OR "a debility stands
    # uncancelled" (a real affliction). This field carries the planets whose debility
    # stands UNCANCELLED so renderers can distinguish them; empty + empty `bhangas`
    # means no planet is debilitated at all. Default keeps existing constructions. ──
    uncancelled_debilities: tuple[str, ...] = ()


def build_arishta_chapter(r: "DetailedReport") -> Optional[ArishtaChapter]:
    from app.raman_saab.primitives.bhangas import (effective_dignity, kemadruma,
                                                   kemadruma_bhanga)
    from app.raman_saab.primitives.dignity import dignity as _dignity

    bal = r.balarishta
    if bal is None and not r.synthesis.longevity_combos:
        return None
    quote = passage("HPA-14:232-266")
    qtext = re.sub(r"\s*\n\s*", " ", (quote or {}).get("text", "")).strip()
    changed: list[tuple[str, str, str]] = []
    uncancelled: list[str] = []
    for p in _GRAHAS:
        if p not in r.chart.planets:
            continue
        try:
            dig = _dignity(p, r.chart)
            eff = effective_dignity(p, r.chart)
        except Exception:  # noqa: BLE001 — Track-B sparse
            continue
        if dig != eff:
            changed.append((p, dig, eff))
        elif dig == "debil":
            # Wave-2 item 5d: a debility that STANDS (no cancellation) is the
            # doctrinal opposite of "nothing is debilitated" — record it apart.
            uncancelled.append(p)
    try:
        kd = kemadruma(r.chart)
        kdb = kemadruma_bhanga(r.chart) if kd else False
    except Exception:  # noqa: BLE001
        kd, kdb = False, False
    kem = ("Kemadruma geometry present but CANCELLED (3HC's own bhanga) — the yoga does "
           "not fire" if kd and kdb else
           "Kemadruma fires (Moon flanked by empty houses, 3HC:2172)" if kd else
           "no Kemadruma (the Moon is not flanked by empty houses)")
    prot = tuple(str(x) for x in r.synthesis.longevity_combos)
    # harmonised band label (Wave-2 item 5b): "Purnayu (purna band)", never bare
    # "purna" beside the combos' "Purnayu" — one reading, one vocabulary.
    from app.raman_saab.detailed_report import longevity_band_label
    return ArishtaChapter(
        balarishta_applies=bool(bal and bal.applies),
        balarishta_cancelled=bool(bal and bal.cancelled),
        balarishta_reasons=tuple(bal.reasons) if bal else (),
        antidote_quote=qtext, antidote_cite="HPA-14:232",
        bhangas=tuple(changed), kemadruma_note=kem, protections=prot,
        band=f"{longevity_band_label(r.longevity_class)} (Ayurdaya cross-check "
             f"~{round(r.longevity_years)}y — a band, not a date)",
        maraka_note=("the running period carries a maraka-tier lord (broad flag)"
                     if r.maraka_period_now else
                     "the running period carries no maraka-tier lord"),
        uncancelled_debilities=tuple(uncancelled))


# ── v23 Profession synthesis ────────────────────────────────────────────────────


@dataclass(frozen=True)
class ProfessionSource:
    source: str                 # which derivation angle
    key: str                    # the planet or sign it resolved to
    trades: str                 # the cited vocation text
    cite: str
    note: str                   # provenance/scope note where one is owed


@dataclass(frozen=True)
class ProfessionSynthesis:
    sources: tuple[ProfessionSource, ...]
    mode_split: tuple[tuple[str, str], ...]    # H10 signification key -> verdict
    convergent: tuple[tuple[str, int], ...]    # trade word -> how many sources name it
    # ── Wave-2 (2026-08-18 report-critique item 3, append-only): the D-10 row the
    # preamble already promises (a re-read of the computed Dasamsa reading — shown
    # as corroboration, deliberately NOT appended to `sources` so the convergence
    # tally is unchanged), the H10 activation windows (same infrastructure as the
    # marriage monograph's H7 windows), and the same-graha convergence disclosure
    # (e.g. three "votes" that are one planet under three hats). Defaults keep
    # every existing construction unchanged. ────────────────────────────────────
    dasamsa_row: tuple[str, ...] = ()          # (derivation, resolves to, reading, cite)
    h10_windows: tuple[str, ...] = ()          # H10 activations from the timeline
    convergence_note: str = ""                 # same-graha multiple-hats disclosure


def build_profession_synthesis(r: "DetailedReport") -> Optional[ProfessionSynthesis]:
    from app.raman_saab.primitives.career import (CAREER_BY_SIGN,
                                                  TRADE_BY_NAVAMSA_DISPOSITOR,
                                                  career_indication, tenth_sign)
    from app.raman_saab.primitives.chara_karakas import chara_karakas

    srcs: list[ProfessionSource] = []
    try:
        ts = tenth_sign(r.chart)
        srcs.append(ProfessionSource(
            "The 10th sign's profile", f"sign {ts}", CAREER_BY_SIGN[ts],
            "HTJAH-II:10340", ""))
    except Exception:  # noqa: BLE001
        pass
    try:
        ci = career_indication(r.chart)
    except Exception:  # noqa: BLE001
        ci = None
    if ci is not None:
        lord, disp, trade = ci
        srcs.append(ProfessionSource(
            "Navamsa-dispositor of the 10th lord (Raman's primary method)",
            f"{lord} -> {disp}", trade, "HTJAH-II:10249", ""))
    if r.ruler.strongest is not None:
        t = TRADE_BY_NAVAMSA_DISPOSITOR.get(r.ruler.strongest)
        if t:
            srcs.append(ProfessionSource(
                "The strongest planet (Shadbala)", r.ruler.strongest, t,
                "HTJAH-II:10249", ""))
    try:
        ak = chara_karakas(r.chart).get("AK")
    except Exception:  # noqa: BLE001
        ak = None
    if ak:
        t = TRADE_BY_NAVAMSA_DISPOSITOR.get(ak)
        if t:
            srcs.append(ProfessionSource(
                "The Atmakaraka", ak, t, "HTJAH-II:10249",
                "karakamsa-profession doctrine proper is Jaimini (outside the citable "
                "canon); this row applies Raman's own vocation table to the AK"))
    md = r.synthesis.running_md
    if md:
        t = TRADE_BY_NAVAMSA_DISPOSITOR.get(md)
        if t:
            srcs.append(ProfessionSource(
                "The running Mahadasha lord", md, t, "HTJAH-II:10249",
                "a timing colour on the vocation, not a separate destiny"))
    if not srcs:
        return None
    # H10 mode split — the four profession significations' judged verdicts.
    modes: list[tuple[str, str]] = []
    if len(r.proformas) >= 10:
        for sv in r.proformas[9].significations:
            if sv.signification.startswith("profession") or sv.signification == "career":
                modes.append((sv.signification, sv.verdict))
    # deterministic convergence: trade tokens named by 2+ sources
    counts: dict[str, int] = {}
    for s in srcs:
        for tok in {w.strip().lower() for part in s.trades.split(",")
                    for w in [part.split("&")[0]] if len(w.strip()) > 3}:
            counts[tok] = counts.get(tok, 0) + 1
    convergent = tuple(sorted(((w, n) for w, n in counts.items() if n >= 2),
                              key=lambda x: (-x[1], x[0])))
    # ── Wave-2 additions (2026-08-18, pure re-reads) ──────────────────────────
    # (a) the D-10 row the preamble promises: the computed Dasamsa career reading
    # (corroboration only — NOT a convergence vote, so `convergent` is unchanged).
    d10_row: tuple[str, ...] = ()
    try:
        from app.raman_saab.judges.dasamsa_career_reading import (
            build_dasamsa_career_reading)
        dr = build_dasamsa_career_reading(r.chart)
        # Provenance corrected 2026-08-19. Two things were misattributed here:
        #   (1) `dr.core.career_verdict` is `judge_house(chart, 10)` on the RASI — Raman's own
        #       core method. Printing it bare under a "Dasamsa D-10" derivation label read as
        #       though the D-10 had cast it; the D-10 overlay casts no verdict at all.
        #   (2) HTJAH-II:9729 is Raman's NAVAMSA-of-the-10th-lord passage, not a dasamsa
        #       passage — he teaches no dasamsa chart. The D-10 reaches this engine only
        #       through his Parashara pointer (HPA-11:195; see doctrine/varga_domains.py).
        # Each clause now sits under the anchor that actually licenses it.
        d10_row = (
            "The Dasamsa D-10 (re-read; corroboration, not a convergence vote)",
            f"career {dr.core.career_verdict} (Raman's own rasi method decides this; "
            f"the D-10 overlay casts no verdict of its own)",
            f"the 10th lord {dr.core.tenth_lord} sits in the D-10 in "
            f"{dr.overlay.tenth_lord_d10_dignity} dignity; his rasi navamsa "
            f"dignity reads {dr.core.tenth_lord_navamsa_dignity}",
            "D-10 Career section: domain via HPA-11:195, the navamsa technique "
            "at HTJAH-II:9729")
    except Exception:  # noqa: BLE001 — Track-B sparse
        d10_row = ()
    # (b) H10 activation windows — same timeline re-read the marriage monograph
    # uses for H7 (a timing lens, never a promise).
    from app.raman_saab.render import _jd_to_date
    h10 = tuple(
        f"{ch.maha} MD ({_jd_to_date(ch.start_jd)} to {_jd_to_date(ch.end_jd)}): "
        f"H10 {tier}"
        for ch in r.life_chapters.chapters
        for h, tier, _v in ch.houses_lit if h == 10)
    # (c) same-graha convergence disclosure: derivations that resolved to ONE
    # planet are one planet counted several times, not independent confirmations.
    hat_names = {
        "The strongest planet (Shadbala)": "the strongest planet",
        "The Atmakaraka": "the Atmakaraka",
        "The running Mahadasha lord": "the running Mahadasha lord",
    }
    by_planet: dict[str, list[str]] = {}
    for s in srcs:
        if s.source in hat_names and s.key in _GRAHAS:
            by_planet.setdefault(s.key, []).append(hat_names[s.source])
        elif s.source.startswith("Navamsa-dispositor"):
            disp = s.key.split(" -> ")[-1]
            if disp in _GRAHAS:
                by_planet.setdefault(disp, []).append(
                    "the navamsa-dispositor of the 10th lord")
    conv_note = "; ".join(
        f"{', '.join(hats)} all resolve to {planet} - one planet counted "
        f"{len(hats)} times in the convergence tally, not {len(hats)} "
        f"independent confirmations"
        for planet, hats in by_planet.items() if len(hats) >= 2)
    return ProfessionSynthesis(sources=tuple(srcs), mode_split=tuple(modes),
                               convergent=convergent,
                               dasamsa_row=d10_row, h10_windows=h10,
                               convergence_note=conv_note)


# ── v24 Wealth chapter ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class WealthRow:
    channel: str
    reading: str
    cite: str
    # Wave-2 (2026-08-18 report-critique item 4d, append-only): the population-
    # calibration context the signification rows already carry elsewhere in the
    # report — re-read here so the table is not a wall of bare "favourable".
    # "" where the row is not a calibrated signification.
    context: str = ""


@dataclass(frozen=True)
class WealthChapter:
    rows: tuple[WealthRow, ...]
    expansion_periods: tuple[str, ...]     # MD runs with H2/H11 lit at ordinary+
    # ── Wave-2 (2026-08-18 report-critique item 4, append-only): the classical
    # first question about wealth — which Dhana yogas fire, and Daridra — stated
    # explicitly (presence AND absence); the 2nd- and 11th-lord condition lines
    # (same computed facts the aptitude chapter shows); and the self-disclosure
    # owed when the expansion lens is non-differential in this chart. Defaults
    # keep every existing construction unchanged. ───────────────────────────────
    dhana_row: str = ""                    # fired-or-absent, with cites when fired
    lord_conditions: tuple[str, ...] = ()  # 2nd lord / 11th lord computed conditions
    expansion_note: str = ""               # non-differential-lens disclosure ("" = n/a)


def _sig_verdict(r: "DetailedReport", house: int, key: str) -> Optional[str]:
    if len(r.proformas) < house:
        return None
    sv = next((s for s in r.proformas[house - 1].significations
               if s.signification == key), None)
    return f"{sv.verdict} ({sv.degree})" if sv is not None else None


def _sig_context(r: "DetailedReport", house: int, key: str) -> str:
    """The population-calibration context of one signification — a re-read of the
    same CalibratedEntry the House-by-house section already renders; "" when the
    row carries no percentile (uncalibrated / abstained)."""
    cr = r.calibration.get(house)
    if cr is None:
        return ""
    e = next((e for e in cr.entries if e.signification == key), None)
    if e is None or e.favourability_percentile is None or e.band_share is None:
        return ""
    return (f"more favourable than {e.favourability_percentile:.0%} of the "
            f"population; {e.band_share:.0%} share this exact reading ({e.rarity})")


def build_wealth_chapter(r: "DetailedReport") -> Optional[WealthChapter]:
    from app.raman_saab.doctrine.lookups.source_of_gains import (
        PLANET_IN_11TH_GAINS, SECOND_LORD_HOUSE_GAINS)

    rows: list[WealthRow] = []

    def _add(channel: str, reading: Optional[str], cite: str,
             context: str = "") -> None:
        if reading:
            rows.append(WealthRow(channel, reading, cite, context))

    # earning style: where the 2nd lord sits
    if len(r.proformas) >= 2:
        lord2 = r.proformas[1].lord
        p2 = r.chart.planets.get(lord2)
        if p2 is not None:
            slg = SECOND_LORD_HOUSE_GAINS.get(p2.rasi_house)
            if slg is not None:
                c = slg.sources[0]
                _add("Earning style (2nd lord in house "
                     f"{p2.rasi_house})", f"gains through {slg.channel}",
                     f"{c.work}:{c.line}")
    _add("Accumulation (H2 wealth)", _sig_verdict(r, 2, "wealth"),
         "H2 proforma", _sig_context(r, 2, "wealth"))
    # gains channels: planets occupying the 11th
    for p in _GRAHAS:
        pl = r.chart.planets.get(p)
        if pl is not None and pl.rasi_house == 11:
            gc_row = PLANET_IN_11TH_GAINS.get(p)
            if gc_row is not None:
                c = gc_row.sources[0]
                _add(f"Gains channel ({p} in the 11th)", gc_row.channel,
                     f"{c.work}:{c.line}")
    _add("Gains (H11)", _sig_verdict(r, 11, "gains"), "H11 proforma",
         _sig_context(r, 11, "gains"))
    _add("Acquisitions (H11)", _sig_verdict(r, 11, "acquisitions"), "H11 proforma",
         _sig_context(r, 11, "acquisitions"))
    _add("Inheritance / legacies (H8)", _sig_verdict(r, 8, "legacies"), "H8 proforma",
         _sig_context(r, 8, "legacies"))
    _add("Sudden gains (H8)", _sig_verdict(r, 8, "sudden_gains"), "H8 proforma",
         _sig_context(r, 8, "sudden_gains"))
    _add("Speculation (H5 poorvapunya frame)", _sig_verdict(r, 5, "poorvapunya"),
         "H5 proforma", _sig_context(r, 5, "poorvapunya"))
    _add("Authority / government (H10)", _sig_verdict(r, 10, "profession_authority"),
         "H10 proforma", _sig_context(r, 10, "profession_authority"))
    _add("Trade / business (H10)", _sig_verdict(r, 10, "profession_trade"),
         "H10 proforma", _sig_context(r, 10, "profession_trade"))
    _add("Learned professions (H10)", _sig_verdict(r, 10, "profession_learned"),
         "H10 proforma", _sig_context(r, 10, "profession_learned"))
    _add("Service / labour (H10)", _sig_verdict(r, 10, "profession_labour"),
         "H10 proforma", _sig_context(r, 10, "profession_labour"))
    _add("Land & property (H4)", _sig_verdict(r, 4, "property"), "H4 proforma",
         _sig_context(r, 4, "property"))
    _add("Foreign residence / income abroad (H12)",
         _sig_verdict(r, 12, "foreign_residence"), "H12 proforma",
         _sig_context(r, 12, "foreign_residence"))
    if not rows:
        return None
    # periods of expansion: MD chapters whose lit houses include 2 or 11 at ordinary+
    good_tiers = {"par excellence", "ordinary"}
    exp: list[str] = []
    from app.raman_saab.render import _jd_to_date
    for ch in r.life_chapters.chapters:
        hit = [f"H{h} ({tier})" for h, tier, _v in ch.houses_lit
               if h in (2, 11) and tier in good_tiers]
        if hit:
            exp.append(f"{ch.maha} MD ({_jd_to_date(ch.start_jd)} to "
                       f"{_jd_to_date(ch.end_jd)}): {', '.join(hit)}")
    # ── Wave-2 additions (2026-08-18, pure re-reads) ──────────────────────────
    # (a) Dhana / Daridra fired-or-absent: the encoded Y.DHANA.* + Y.DARIDRA set
    # checked against the chart's OWN fired yogas — presence AND absence stated.
    dhana_row = ""
    try:
        from app.raman_saab.doctrine.yogas import YOGAS
        dhana_recs = [rec for rec in YOGAS if rec.id.startswith("Y.DHANA")]
        daridra_recs = [rec for rec in YOGAS if rec.id.startswith("Y.DARIDRA")]
        fired_ids = {y.id for y in r.yogas}
        dhana_fired = [rec for rec in dhana_recs if rec.id in fired_ids]
        daridra_fired = [rec for rec in daridra_recs if rec.id in fired_ids]
        dhana_bit = (
            "Dhana yogas: " + "; ".join(
                f"{rec.name} fires ({rec.source.work}:{rec.source.line})"
                for rec in dhana_fired)
            if dhana_fired else
            f"Dhana yogas: none of the encoded set ({len(dhana_recs)} "
            f"combinations) fires")
        daridra_bit = (
            "; ".join(f"{rec.name} fires ({rec.source.work}:{rec.source.line})"
                      for rec in daridra_fired)
            if daridra_fired else "Daridra: absent")
        dhana_row = f"{dhana_bit}; {daridra_bit}"
    except Exception:  # noqa: BLE001
        dhana_row = ""
    # (b) the 2nd and 11th lords' computed conditions (the aptitude chapter's
    # own _condition read, applied to the wealth lords).
    lord_lines: list[str] = []
    try:
        from app.raman_saab.monographs import _condition
        for house_no, label in ((2, "The 2nd lord"), (11, "The 11th lord")):
            if len(r.proformas) >= house_no:
                lord = r.proformas[house_no - 1].lord
                cond = _condition(lord, r)
                if cond:
                    lord_lines.append(f"{label} {lord} - {cond}")
    except Exception:  # noqa: BLE001
        lord_lines = []
    # (c) self-disclosure when the expansion lens is non-differential: every MD
    # in the window qualifying at the top grade discriminates nothing — the same
    # standard the population-context rows apply to near-universal readings.
    expansion_note = ""
    n_chapters = len(r.life_chapters.chapters)
    if exp and n_chapters and len(exp) == n_chapters and all(
            "(par excellence)" in e and "(ordinary)" not in e for e in exp):
        expansion_note = (
            "in this chart every period in the window activates H2/H11 at the "
            "top grade - the lens is non-differential here and separates no "
            "period from another")
    return WealthChapter(rows=tuple(rows), expansion_periods=tuple(exp),
                         dhana_row=dhana_row,
                         lord_conditions=tuple(lord_lines),
                         expansion_note=expansion_note)
