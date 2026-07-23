"""Family soul-group synthesis — how several souls interlock. REPORT-ONLY, nets nothing.

Cross-references the soul-signatures of a group (a family) to surface the ways their scripts are
woven together: shared soul-frames (same Ātmakāraka / Karakāṁśa / Ketu sign or nakshatra), karmic
role-swaps (one member's soul-planet is another's counsel- or spouse-significator), Ketu-axis
resonance (a shared past-life axis; one's mokṣa-vehicle seating another's soul), and the family's
recurring soul-motif.

Like ``two_spouse_children.py`` it **nets nothing** — the classical texts give no formula for
combining souls into one verdict, so this reports the interlocks and leaves the synthesis to the
reader. Imported by nothing in the D1 verdict path.

Usage:
    from app.raman_saab.judges.family_soul_group import build_family_soul_group
    g = build_family_soul_group([("father", chart_a), ("mother", chart_b), ...])
    g.role_swaps        # karmic role-interlocks across the group
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges.soul_reading import SoulTagged
from app.raman_saab.primitives import jaimini_reading, special_points
from app.raman_saab.primitives.chara_karakas import chara_karakas
from app.raman_saab.primitives.nakshatra_signature import signature_for

_SIGN: Final[tuple[str, ...]] = (
    "", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _sign(n: int) -> str:
    return _SIGN[n] if 0 < n < 13 else "?"


@dataclass(frozen=True)
class SoulSignature:
    """One member's soul distilled to its interlockable points."""
    role: str
    ak_planet: str
    ak_sign: int
    ak_nakshatra: int
    karakamsa_sign: int
    ketu_sign: int
    ketu_nakshatra: int
    karakas: tuple[tuple[str, str], ...]   # (role, planet) AK..DK
    arudha_sign: int

    def karaka(self, role: str) -> Optional[str]:
        return dict(self.karakas).get(role)


@dataclass(frozen=True)
class FamilySoulGroup:
    """The group's interlocks — REPORT-ONLY. DELIBERATELY no combined/group verdict."""
    signatures: tuple[SoulSignature, ...]
    shared_soul_frames: tuple[SoulTagged, ...]
    role_swaps: tuple[SoulTagged, ...]
    ketu_axis: tuple[SoulTagged, ...]
    recurring_motif: tuple[SoulTagged, ...]
    narrative: str
    notes: tuple[SoulTagged, ...]


def soul_signature(role: str, chart: RamanChart) -> SoulSignature:
    """Distil a chart into its interlockable soul-points (pure Jaimini primitives, fast)."""
    ak = special_points.atmakaraka(chart)
    akp = chart.planets[ak]
    ketu = chart.planets.get("Ketu")
    ck = chara_karakas(chart)
    return SoulSignature(
        role=role, ak_planet=ak, ak_sign=akp.sign, ak_nakshatra=akp.nakshatra,
        karakamsa_sign=jaimini_reading.karakamsa_sign(chart),
        ketu_sign=ketu.sign if ketu else 0,
        ketu_nakshatra=ketu.nakshatra if ketu else 0,
        karakas=tuple((r, ck[r]) for r in ("AK", "AmK", "BK", "MK", "PK", "GK", "DK") if r in ck),
        arudha_sign=special_points.arudha_lagna(chart).sign)


# ---------------------------------------------------------------------------
# interlock detectors — each fires only on genuine agreement, nets nothing
# ---------------------------------------------------------------------------

def _shared_frames(sigs: tuple[SoulSignature, ...]) -> tuple[SoulTagged, ...]:
    out: list[SoulTagged] = []
    for attr, label in (("ak_sign", "Ātmakāraka sign"), ("karakamsa_sign", "Karakāṁśa"),
                        ("ketu_sign", "Ketu sign")):
        groups: dict[int, list[str]] = {}
        for s in sigs:
            groups.setdefault(getattr(s, attr), []).append(s.role)
        for sign, roles in groups.items():
            if sign and len(roles) >= 2:
                out.append(SoulTagged(
                    f"{', '.join(roles)} share the same {label} ({_sign(sign)}) — souls seated in "
                    "one soul-frame", "JAIMINI_EXPLICIT", "JAIMINI-49"))
    for attr, label in (("ak_nakshatra", "Ātmakāraka nakshatra"), ("ketu_nakshatra", "Ketu nakshatra")):
        groups = {}
        for s in sigs:
            groups.setdefault(getattr(s, attr), []).append(s.role)
        for nak, roles in groups.items():
            if nak and len(roles) >= 2:
                out.append(SoulTagged(
                    f"{', '.join(roles)} share the same {label} ({signature_for(nak).name}) — a "
                    "strong past-life-together signal", "EDITORIAL_SYNTHESIS"))
    return tuple(out)


def _role_swaps(sigs: tuple[SoulSignature, ...]) -> tuple[SoulTagged, ...]:
    out: list[SoulTagged] = []
    for x in sigs:
        for y in sigs:
            if x.role == y.role or not x.ak_planet:
                continue
            for ry, name in (("AmK", "counsel-significator"), ("DK", "spouse-significator")):
                if x.ak_planet == y.karaka(ry):
                    out.append(SoulTagged(
                        f"{x.role}'s soul-planet ({x.ak_planet}) is {y.role}'s {ry} "
                        f"({name}) — a karmic role-interlock", "JAIMINI_EXPLICIT", "JAIMINI-49"))
    seen: set[frozenset[str]] = set()
    for x in sigs:
        for y in sigs:
            if x.role == y.role:
                continue
            key = frozenset((x.role, y.role))
            if key in seen:
                continue
            if x.ak_planet and x.ak_planet == y.karaka("DK") and y.ak_planet == x.karaka("DK"):
                seen.add(key)
                out.append(SoulTagged(
                    f"{x.role} & {y.role}: each is the other's Darakāraka (spouse-significator) by "
                    "soul — a reciprocal bond", "EDITORIAL_SYNTHESIS"))
    return tuple(out)


def _ketu_axis(sigs: tuple[SoulSignature, ...]) -> tuple[SoulTagged, ...]:
    out: list[SoulTagged] = []
    for i, x in enumerate(sigs):
        for y in sigs[i + 1:]:
            if x.ketu_sign and x.ketu_sign == y.ketu_sign:
                out.append(SoulTagged(
                    f"{x.role} & {y.role} share the same Ketu sign ({_sign(x.ketu_sign)}) — a "
                    "shared past-life axis", "EDITORIAL_SYNTHESIS"))
            elif x.ketu_sign and y.ketu_sign and (x.ketu_sign - y.ketu_sign) % 12 == 6:
                out.append(SoulTagged(
                    f"{x.role} & {y.role} sit on the same Ketu axis (1/7: {_sign(x.ketu_sign)}/"
                    f"{_sign(y.ketu_sign)})", "EDITORIAL_SYNTHESIS"))
            if x.ketu_sign and x.ketu_sign == y.karakamsa_sign:
                out.append(SoulTagged(
                    f"{x.role}'s Ketu (mokṣa-vehicle) seats {y.role}'s Karakāṁśa (soul) — one's "
                    "liberation-path holds the other's soul", "EDITORIAL_SYNTHESIS"))
            if y.ketu_sign and y.ketu_sign == x.karakamsa_sign:
                out.append(SoulTagged(
                    f"{y.role}'s Ketu (mokṣa-vehicle) seats {x.role}'s Karakāṁśa (soul)",
                    "EDITORIAL_SYNTHESIS"))
    return tuple(out)


def _recurring_motif(sigs: tuple[SoulSignature, ...]) -> tuple[SoulTagged, ...]:
    n = len(sigs)
    counts = Counter(s.ak_sign for s in sigs if s.ak_sign)
    if not counts:
        return ()
    val, cnt = counts.most_common(1)[0]
    if cnt >= 2 and cnt * 2 >= n:
        return (SoulTagged(
            f"the family's dominant soul-motif: Ātmakāraka sign {_sign(val)} recurs in {cnt}/{n} "
            "members", "EDITORIAL_SYNTHESIS"),)
    return ()


# ---------------------------------------------------------------------------
# public builders
# ---------------------------------------------------------------------------

def _group_narrative(sigs: tuple[SoulSignature, ...], shared: tuple[SoulTagged, ...],
                     swaps: tuple[SoulTagged, ...], ketu: tuple[SoulTagged, ...],
                     motif: tuple[SoulTagged, ...]) -> str:
    """Weave the detected interlocks into one readable group-story."""
    n = len(sigs)
    s = [f"These {n} souls are woven into one script."]
    if shared:
        s.append(f"They share {len(shared)} soul-frame(s) — souls seated in common ground.")
    if swaps:
        s.append(f"Their soul-planets recur as one another's counsel- and spouse-significators "
                 f"({len(swaps)} karmic role-interlock(s)).")
    if ketu:
        s.append(f"Their Ketu axes — the shared past-life / mokṣa current — resonate in "
                 f"{len(ketu)} way(s).")
    if motif:
        s.append("A single soul-motif recurs across the group — the family's dominant note.")
    if not (shared or swaps or ketu or motif):
        s.append("No strong interlock surfaced — these souls walk largely independent scripts.")
    else:
        s.append("Read the interlocks below as resonance, not decree — the script binds, it does "
                 "not bind absolutely.")
    return " ".join(s)


def synthesize_from_signatures(signatures: tuple[SoulSignature, ...]) -> FamilySoulGroup:
    """Cross-reference already-distilled soul-signatures (the swisseph-free testable core)."""
    sigs = tuple(signatures)
    shared = _shared_frames(sigs)
    swaps = _role_swaps(sigs)
    ketu = _ketu_axis(sigs)
    motif = _recurring_motif(sigs)
    return FamilySoulGroup(
        signatures=sigs,
        shared_soul_frames=shared,
        role_swaps=swaps,
        ketu_axis=ketu,
        recurring_motif=motif,
        narrative=_group_narrative(sigs, shared, swaps, ketu, motif),
        notes=(SoulTagged(
            "Soul-group interlock is REPORT-ONLY and nets no verdict — no text gives a formula for "
            "combining souls; the synthesis is the reader's.", "ABSENT_IN_RAMAN"),))


def build_family_soul_group(
    charts_with_roles: list[tuple[str, RamanChart]]) -> FamilySoulGroup:
    """Distil each (role, chart) into a soul-signature and cross-reference them."""
    return synthesize_from_signatures(
        tuple(soul_signature(role, chart) for role, chart in charts_with_roles))
