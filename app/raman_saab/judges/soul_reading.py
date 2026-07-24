"""Soul-destiny reading — a REPORT-ONLY, provenance-honest surface.

Reads a nativity as a SOUL with a scripted karmic path, in two provenance regimes:

  * ``core`` — Raman's OWN Parashari soul doctrine, fully citable and AUTHORITATIVE: past-birth
    merit (5th, poorvapunya, HTJAH-I:5019), dharma (9th, HTJAH-II:7285), mokṣa / the soul's
    after-death state (12th, HTJAH-II:16669), and the Ketu-kaivalya combination
    (Ketu in the 12th from Karakāṁśa → Final Emancipation, HTJAH-II:16527) — a report-only port of
    the standing stub ``house_12_vyaya/combinations.py`` H12.C.G2. Delegates verdicts to
    ``judge_house``. This is what stands.
  * ``jaimini_overlay`` — the Jaimini soul-script: the 7 chara karakas, the 12-bhavas-from-
    Karakāṁśa soul-purpose map, the Karakāṁśa occupant professions, the Chara Dasha "script", and
    the Arudha Lagna. The Jaimini corpus is FIREWALLED (non-citable) per the merge re-review
    (2026-07-24, book_registry.py): the ``JAIMINI_EXPLICIT`` tags remain as free-text textual
    provenance only — the corpus does not vouch for them (`sources.verify` declines them and the
    paired citation test skips).
  * ``nakshatra_signature`` — the AK / Moon / Lagna birth-star archetype. Deity/gana are
    ``CLASSICAL_NONCITABLE``; the archetype phrasing is ``EDITORIAL_SYNTHESIS``.

Node drishti in this engine is 7th-only (``doctrine/drishti.py:31``) — the soul layer inherits it.

VERDICT-AUTHORITY INVARIANT: imported by NOTHING in the D1 verdict path (``house_template.py``
never imports it) — the golden ratchet is untouched by construction. A standalone reading, exactly
like ``saptamsa_reading.py`` / ``two_spouse_children.py``. It NETS NO verdict where the texts give
no formula.

Usage:
    from app.raman_saab.judges.soul_reading import build_soul_reading
    r = build_soul_reading(chart)
    r.core.ketu_kaivalya               # Final-Emancipation combination present?
    r.jaimini_overlay.chara_karakas    # ((role, planet), ...) AK..DK
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, Optional

from app.raman_saab.chart import varga
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges.house_template import judge_house
from app.raman_saab.primitives import chara_dasha, jaimini_reading, special_points
from app.raman_saab.primitives.chara_karakas import chara_karakas, role_name
from app.raman_saab.primitives.nakshatra_signature import NakshatraSignature, signature_for

SoulProvenance = Literal[
    "RAMAN_EXPLICIT",           # Raman states it verbatim (Parashari-natal, citable)
    "RAMAN_GENERAL_PRINCIPLE",  # Raman's principle applied by analogy
    "JAIMINI_EXPLICIT",         # cited to the (experiment-unlocked) Jaimini corpus
    "CLASSICAL_NONCITABLE",     # classical-Vedic, outside any live corpus
    "EDITORIAL_SYNTHESIS",      # authored archetype phrasing, not a text
    "ABSENT_IN_RAMAN",          # a step no text nets; flagged, not silently supplied
]

_SIGN: Final[tuple[str, ...]] = (
    "", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces")

_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

# Iṣṭa-Devatā — the planet in the 12th from the Karakāṁśa (or, if empty, its lord) names the deity
# of the heart, worshipped for mokṣa (Jaimini; the classical planet→deity correspondence).
_ISHTA_DEVATA: Final[dict[str, str]] = {
    "Sun": "Śiva / Sūrya", "Moon": "Gaurī (Pārvatī) / Kṛṣṇa",
    "Mars": "Skanda (Subrahmaṇya) / Narasiṁha", "Mercury": "Viṣṇu (Buddha)",
    "Jupiter": "Viṣṇu / Śrī Rāma / Dattātreya", "Venus": "Lakṣmī / Paraśurāma",
    "Saturn": "Kūrma (Viṣṇu) / Śani / Brahmā", "Rahu": "Durgā / Varāha",
    "Ketu": "Gaṇeśa / Matsya",
}

# Ported verbatim from app/core/karakamsa_arudha.py:82-95 — the 12 bhavas read FROM the Karakāṁśa
# as the soul's scripted purpose (Jaimini soul-cartography). Cited to the unlocked Jaimini corpus.
_BHAVA_FROM_KARAKAMSA: Final[dict[int, str]] = {
    1: "the soul's natural disposition; the ishta of the body it took",
    2: "the soul's accumulated speech, voice, and family-of-origin karma",
    3: "the soul's courage-training; siblings-of-spirit; short passages",
    4: "the soul's emotional foundation; the mother of the soul; its inherited home of being",
    5: "the soul's purpose-mantra — what it came to teach; its bija affinity",
    6: "the soul's enemies-of-purpose; illnesses-as-teaching; obstacles to dharma",
    7: "the soul's dharma-partner; its ideal complement",
    8: "the soul's hidden karma; transformative initiation; the occult path",
    9: "the soul's guru-lineage; inherited dharma; the pilgrimage of being",
    10: "the soul's worldly mission; its karma-yoga channel — what the soul DOES",
    11: "the soul's network of kindred souls; spiritual gains",
    12: "the soul's mokṣa-vehicle; the ishta-devata indicator; the final liberation path",
}


@dataclass(frozen=True)
class SoulTagged:
    """One soul-reading line with its provenance + citation (the soul-layer analog of
    ``saptamsa_reading.Tagged``, with the extended ``SoulProvenance``)."""
    text: str
    provenance: SoulProvenance
    cite: str = ""


@dataclass(frozen=True)
class SoulCore:
    """The AUTHORITATIVE soul picture — Raman's own Parashari doctrine (all citable)."""
    poorvapunya_verdict: str
    dharma_verdict: str
    moksha_verdict: str
    ketu_kaivalya: bool
    lines: tuple[SoulTagged, ...]


@dataclass(frozen=True)
class JaiminiOverlay:
    """The Jaimini soul-script — REPORT-ONLY (citations experiment-unlocked)."""
    atmakaraka: str
    karakamsa_sign: int
    chara_karakas: tuple[tuple[str, str], ...]     # (role, planet), AK..DK
    chara_dasha: tuple[tuple[int, int], ...]       # the (sign, years) script from birth
    arudha_lagna_sign: int
    ishta_devata: str                              # the mokṣa-deity (12th-from-Karakāṁśa)
    lines: tuple[SoulTagged, ...]


@dataclass(frozen=True)
class NakshatraSoulSignature:
    """AK / Moon / Lagna birth-star archetypes — split-provenance."""
    entries: tuple[SoulTagged, ...]


@dataclass(frozen=True)
class SoulReading:
    """The whole reading: Parashari core (decides) + Jaimini overlay + nakshatra signature."""
    core: SoulCore
    jaimini_overlay: JaiminiOverlay
    nakshatra_signature: NakshatraSoulSignature
    narrative: str
    notes: tuple[SoulTagged, ...]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


def _verdict(chart: RamanChart, house: int, sig: str) -> str:
    pf = judge_house(chart, house)
    sv = next((s for s in pf.significations if s.signification == sig), None)
    return sv.verdict if sv else "insufficient-evidence"


def _house_of_sign(from_sign: int, offset: int) -> int:
    return ((from_sign - 1) + (offset - 1)) % 12 + 1


def _navamsa_occupants(chart: RamanChart, sign: int) -> tuple[str, ...]:
    return tuple(n for n in _PLANET_ORDER
                if n in chart.planets and chart.planets[n].navamsa_sign == sign)


def _ketu_kaivalya(chart: RamanChart) -> bool:
    """H12.C.G2 ported: Ketu in the 12th sign FROM the Karakāṁśa (navamsa frame) → Kaivalya."""
    ketu = chart.planets.get("Ketu")
    if ketu is None:
        return False
    twelfth = _house_of_sign(jaimini_reading.karakamsa_sign(chart), 12)
    return ketu.navamsa_sign == twelfth


def _ishta_devata(chart: RamanChart) -> tuple[str, str]:
    """The Iṣṭa-Devatā: the deity of the 12th sign FROM the Karakāṁśa (navamsa frame). A planet
    occupying that sign names the deity; if empty, its lord does. Returns (deity, basis)."""
    twelfth = _house_of_sign(jaimini_reading.karakamsa_sign(chart), 12)
    occ = _navamsa_occupants(chart, twelfth)
    if occ:
        return (" / ".join(_ISHTA_DEVATA[p] for p in occ),
                f"{', '.join(occ)} in the 12th-from-Karakāṁśa ({_sign(twelfth)})")
    lord = SIGN_LORDS[twelfth]
    return (_ISHTA_DEVATA.get(lord, "—"),
            f"the empty 12th-from-Karakāṁśa ({_sign(twelfth)}); its lord {lord}")


def _nak_of(chart: RamanChart, point: str) -> Optional[int]:
    if point == "Lagna":
        return varga.nakshatra_pada(chart.asc_lon)[0]
    p = chart.planets.get(point)
    return p.nakshatra if p is not None else None


def _karakamsa_yogas(chart: RamanChart) -> list[tuple[str, str]]:
    """Classic Jaimini spiritual yogas from planets ON the Karakāṁśa (navamsa-conjunct the AK).
    Returns (text, cite). Jaimini Sūtras 1.2 (the experiment-unlocked JS corpus)."""
    occ = set(_navamsa_occupants(chart, jaimini_reading.karakamsa_sign(chart)))
    out: list[tuple[str, str]] = []
    if "Ketu" in occ:
        out.append(("Ketu on the Karakāṁśa → a mokṣa-inclined, renunciate soul", "JS-1"))
    if {"Ketu", "Jupiter"} <= occ:
        out.append(("Jupiter with Ketu on the Karakāṁśa → jñāna-yoga: knowledge of the Self / "
                    "Brahman", "JS-1"))
    if {"Ketu", "Sun"} <= occ:
        out.append(("Sun with Ketu on the Karakāṁśa → knowledge of the ātman / the divine", "JS-1"))
    if "Venus" in occ:
        out.append(("Venus on the Karakāṁśa → a bhakti (devotional) soul-current", "JS-1"))
    if "Jupiter" in occ:
        out.append(("Jupiter on the Karakāṁśa → a soul drawn to wisdom, dharma and teaching", "JS-1"))
    if "Saturn" in occ:
        out.append(("Saturn on the Karakāṁśa → a disciplined, tapas-oriented soul", "JS-1"))
    return out


def _karakamsa_argala(chart: RamanChart) -> list[tuple[str, str]]:
    """Jaimini argala on the Karakāṁśa (soul-seat), in the navamsa. Planets in the 2nd/4th/11th
    from the Karakāṁśa 'lock onto' (intervene on) the soul's expression; the 12th/10th/3rd
    respectively counter them (virodhārgala). Net argala when the intervening house outnumbers its
    counter (Jaimini Sūtras 1.1). Returns (text, cite)."""
    ks = jaimini_reading.karakamsa_sign(chart)
    pairs = ((2, 12, "resources & family (2nd)"), (4, 10, "foundation & heart (4th)"),
             (11, 3, "gains & kindred (11th)"))
    out: list[tuple[str, str]] = []
    for a, c, label in pairs:
        na = len(_navamsa_occupants(chart, _house_of_sign(ks, a)))
        nc = len(_navamsa_occupants(chart, _house_of_sign(ks, c)))
        if na == 0:
            continue
        if na > nc:
            out.append((f"argala on the soul-seat from {label}: {na} intervene, {nc} counter → an "
                        f"UNOPPOSED lock supporting the soul", "JS-1"))
        else:
            out.append((f"argala on the soul-seat from {label}: {na} intervene but {nc} counter → "
                        f"OBSTRUCTED (virodhārgala)", "JS-1"))
    return out


def _soul_narrative(chart: RamanChart, core: SoulCore, overlay: JaiminiOverlay) -> str:
    """Weave the scattered soul-data into one readable 'what this soul came to do' paragraph."""
    ks = overlay.karakamsa_sign
    ak_nak = _nak_of(chart, overlay.atmakaraka)
    arche = signature_for(ak_nak).soul_archetype if ak_nak else "a soul"

    def held(offset: int) -> str:
        occ = _navamsa_occupants(chart, _house_of_sign(ks, offset))
        return ", ".join(occ) if occ else f"the lord {SIGN_LORDS[_house_of_sign(ks, offset)]}"

    art = "an" if core.dharma_verdict[:1].lower() in "aeiou" else "a"
    parts = [
        f"The soul-significator is {overlay.atmakaraka} — {arche}.",
        f"It carries {core.poorvapunya_verdict} merit from past births and walks {art} "
        f"{core.dharma_verdict} dharma.",
        f"Its purpose-mantra (5th from Karakāṁśa) works through {held(5)}, its worldly mission "
        f"(10th) through {held(10)}, and its guru-lineage (9th) through {held(9)}.",
        f"Its mokṣa-vehicle (12th) is held by {held(12)}, its iṣṭa-devatā is {overlay.ishta_devata}, "
        f"and the after-death state reads {core.moksha_verdict}.",
    ]
    if core.ketu_kaivalya:
        parts.append("Ketu in the 12th from the Karakāṁśa marks a Kaivalya (final-emancipation) "
                     "current.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# builder
# ---------------------------------------------------------------------------

def _build_core(chart: RamanChart) -> SoulCore:
    poorva = _verdict(chart, 5, "poorvapunya")
    dharma = _verdict(chart, 9, "dharma")
    moksha = _verdict(chart, 12, "moksha")
    kaivalya = _ketu_kaivalya(chart)
    lines = [
        SoulTagged(f"Poorvapunya (merit carried from past births, the 5th): {poorva}",
                   "RAMAN_EXPLICIT", "HTJAH-I:5019"),
        SoulTagged(f"Dharma (the soul's law/path, the 9th): {dharma}",
                   "RAMAN_EXPLICIT", "HTJAH-II:7285"),
        SoulTagged(f"Mokṣa / the after-death state of the soul (the 12th): {moksha}",
                   "RAMAN_EXPLICIT", "HTJAH-II:16669"),
    ]
    if kaivalya:
        lines.append(SoulTagged(
            "Ketu occupies the 12th from the Karakāṁśa → the Kaivalya (Final Emancipation) "
            "combination is PRESENT", "RAMAN_EXPLICIT", "HTJAH-II:16527"))
    else:
        lines.append(SoulTagged(
            "the Ketu-in-12th-from-Karakāṁśa Kaivalya combination is not present",
            "RAMAN_EXPLICIT", "HTJAH-II:16527"))
    return SoulCore(poorvapunya_verdict=poorva, dharma_verdict=dharma, moksha_verdict=moksha,
                    ketu_kaivalya=kaivalya, lines=tuple(lines))


def _build_jaimini_overlay(chart: RamanChart) -> JaiminiOverlay:
    ak = special_points.atmakaraka(chart)
    ks = jaimini_reading.karakamsa_sign(chart)
    ck = chara_karakas(chart)
    ck_tuple = tuple((role, ck[role]) for role in ("AK", "AmK", "BK", "MK", "PK", "GK", "DK")
                     if role in ck)
    lines: list[SoulTagged] = [
        SoulTagged(f"Ātmakāraka (the soul significator): {ak}; Karakāṁśa (its navamsa seat): "
                   f"{_sign(ks)}", "JAIMINI_EXPLICIT", "JAIMINI-49"),
    ]
    for role, planet in ck_tuple:
        lines.append(SoulTagged(f"{role_name(role)}: {planet}", "JAIMINI_EXPLICIT", "JAIMINI-49"))
    # the 12-bhavas-from-Karakāṁśa soul-purpose map (occupants by navamsa)
    for bhava in range(1, 13):
        sign = _house_of_sign(ks, bhava)
        occ = _navamsa_occupants(chart, sign)
        occ_txt = f" [held by {', '.join(occ)}]" if occ else ""
        lines.append(SoulTagged(
            f"{bhava}th from Karakāṁśa ({_sign(sign)}) — {_BHAVA_FROM_KARAKAMSA[bhava]}{occ_txt}",
            "JAIMINI_EXPLICIT", "JAIMINI-49"))
    # Karakāṁśa occupant professions (Jaimini Sutras 1.2)
    for planet, indication in jaimini_reading.karakamsa_indications(chart):
        lines.append(SoulTagged(
            f"{planet} on the Karakāṁśa → {indication}", "JAIMINI_EXPLICIT", "JS-1"))
    # the Chara Dasha script
    seq = tuple(chara_dasha.chara_dasha(chart))
    al = special_points.arudha_lagna(chart).sign
    lines.append(SoulTagged(
        "Chara Dasha (the soul-script unfolding): "
        + " → ".join(f"{_sign(s)}({y}y)" for s, y in seq), "JAIMINI_EXPLICIT", "JAIMINI-49"))
    lines.append(SoulTagged(
        f"Arudha Lagna (the soul's worldly mask): {_sign(al)}", "JAIMINI_EXPLICIT", "JAIMINI-49"))
    deity, basis = _ishta_devata(chart)
    lines.append(SoulTagged(
        f"Iṣṭa-Devatā (the deity of the heart, worshipped for mokṣa): {deity} — from {basis}",
        "JAIMINI_EXPLICIT", "JAIMINI-49"))
    for text, cite in _karakamsa_yogas(chart):
        lines.append(SoulTagged(text, "JAIMINI_EXPLICIT", cite))
    for text, cite in _karakamsa_argala(chart):
        lines.append(SoulTagged(text, "JAIMINI_EXPLICIT", cite))
    return JaiminiOverlay(atmakaraka=ak, karakamsa_sign=ks, chara_karakas=ck_tuple,
                          chara_dasha=seq, arudha_lagna_sign=al, ishta_devata=deity,
                          lines=tuple(lines))


def _build_nakshatra_signature(chart: RamanChart) -> NakshatraSoulSignature:
    entries: list[SoulTagged] = []
    for label, point in (("Ātmakāraka", special_points.atmakaraka(chart)),
                         ("Moon (manas)", "Moon"), ("Lagna", "Lagna")):
        nak = _nak_of(chart, point)
        if nak is None:
            continue
        s: NakshatraSignature = signature_for(nak)
        entries.append(SoulTagged(
            f"{label} in {s.name} — deity {s.devata}, {s.gana}-gana, symbol '{s.symbol}'",
            "CLASSICAL_NONCITABLE"))
        entries.append(SoulTagged(
            f"{label} soul-archetype: {s.soul_archetype} — {s.soul_keyword}",
            "EDITORIAL_SYNTHESIS"))
    return NakshatraSoulSignature(entries=tuple(entries))


def build_soul_reading(chart: RamanChart) -> SoulReading:
    """Assemble the provenance-honest soul-destiny reading for ``chart``.

    ``core`` decides (Raman's Parashari soul doctrine); ``jaimini_overlay`` + ``nakshatra_signature``
    corroborate (report-only). Nets no combined verdict."""
    notes = (
        SoulTagged("REPORT-ONLY: imported by nothing in the D1 verdict path; the golden ratchet is "
                   "untouched by construction.", "RAMAN_GENERAL_PRINCIPLE"),
        SoulTagged("The Jaimini citation firewall is LOCKED (merge re-review 2026-07-24): the "
                   "Jaimini references in this overlay are free-text textual provenance only; the "
                   "corpus does not vouch for them.", "JAIMINI_EXPLICIT", "JAIMINI-49"),
        SoulTagged("Nodes cast the 7th aspect only in this engine (not 5/9); Ketu is the mokṣa/"
                   "past-life significator.", "RAMAN_GENERAL_PRINCIPLE"),
        SoulTagged("A scripted destiny is a promise and a tendency, not a fixed fate; the Parashari "
                   "core decides, the Jaimini/nakshatra layers corroborate. No formula nets these "
                   "into one verdict.", "ABSENT_IN_RAMAN"),
    )
    core = _build_core(chart)
    overlay = _build_jaimini_overlay(chart)
    return SoulReading(
        core=core,
        jaimini_overlay=overlay,
        nakshatra_signature=_build_nakshatra_signature(chart),
        narrative=_soul_narrative(chart, core, overlay),
        notes=notes)
