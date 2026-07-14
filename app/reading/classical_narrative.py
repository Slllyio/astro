"""Classical judicial narrative — a reading in the manner of B. V. Raman.

This turns the engine's *real* computed judgments (house verdicts, planetary
strength, functional roles, yogas, daśā) into a continuous, measured, judicial
assessment that follows Raman's own hierarchy of reasoning, exactly as in
*How to Judge a Horoscope*:

    1. General estimate of the horoscope
    2. The Ascendant (sign, occupants, aspects)
    3. The Ascendant lord
    4. The Moon (mind)
    5. The Sun (authority, father)
    6. The remaining planets
    7. The house lords
    8. The important yogas (explained, not listed)
    9. Synthesis of the several bhāvas
   10. Timing — daśā and the present period

It is deterministic (no LLM), fail-soft, and **additive**: it reasons from the
same real engine output the numerical dashboard shows, translated into Raman's
measured register — promise separated from timing, contradictions reconciled,
no scores in the prose, and Saturn-like restraint (never "excellent/great").

Every figure it rests on is real; nothing is invented. Cautions and outcome
predictions are kept measured, consistent with the honest validation ceiling.
"""
from __future__ import annotations

from typing import Any, Mapping

from app.core.dignity import SIGN_RULERS

from app.reading._planet_lexicon import (
    PLANET_QUALITY,
    PLANET_SIG,
    SIGN_TEMPERAMENT,
    well_placed as _lex_well_placed,
)

_SIGN_NAMES = (
    "", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
    "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
_SIGN_TEMPERAMENT = SIGN_TEMPERAMENT
_PLANET_SIG = PLANET_SIG
_HOUSE_SIG = {
    1: "the body, health and temperament",
    2: "wealth, family and speech",
    3: "courage, brothers and self-effort",
    4: "the mother, home and inner contentment",
    5: "children, intelligence and past merit",
    6: "health, adversaries and debts",
    7: "marriage and partnerships",
    8: "longevity and the vicissitudes of life",
    9: "fortune, the father and religious merit",
    10: "profession, honour and standing",
    11: "gains and the fulfilment of desires",
    12: "expenditure, losses and final emancipation",
}
_HOUSE_ORD = {
    1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth",
    7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth", 11: "eleventh",
    12: "twelfth",
}
_KENDRAS = {1, 4, 7, 10}
_TRIKONAS = {1, 5, 9}
_DUSTHANAS = {6, 8, 12}

# Each planet's higher expression (when well placed) and its shadow (when
# afflicted) — for the character portrait and the per-planet paragraphs.
# Sourced from the shared lexicon so the native profile reads identically.
_PLANET_QUALITY = PLANET_QUALITY


def _grade_word(idx: int | None) -> str:
    return {
        8: "exceptionally strong", 7: "very strong", 6: "powerful",
        5: "well fortified", 4: "reasonably strong", 3: "moderately disposed",
        2: "of ordinary strength", 1: "weak", 0: "much afflicted",
    }.get(idx if idx is not None else -1, "of undetermined strength")


def _fav_phrase(idx: int | None) -> str:
    return {
        8: "distinctly favourable", 7: "distinctly favourable",
        6: "very favourable", 5: "favourable", 4: "reasonably good",
        3: "moderately favourable", 2: "of an ordinary nature",
        1: "somewhat adverse", 0: "considerably afflicted",
    }.get(idx if idx is not None else -1, "of a mixed nature")


def _dignity_clause(dig: str | None) -> str:
    return {
        "exalted": "exalted and hence very powerful",
        "moolatrikona": "in its moolatrikona and strong",
        "own": "in its own sign, well established",
        "friendly": "in a friendly sign",
        "neutral": "in a neutral sign",
        "inimical": "in an inimical sign and somewhat weakened",
        "enemy": "in an inimical sign and somewhat weakened",
        "debilitated": "in its sign of debilitation",
    }.get(str(dig or "").lower(), "moderately placed")


def _house_class(h: int) -> str:
    if h in _TRIKONAS and h != 1:
        return "a trine"
    if h in _KENDRAS:
        return "a quadrant"
    if h in _DUSTHANAS:
        return "a difficult house"
    return "a neutral house"


def _andlist(items: list[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def build_classical_narrative(
    reading: Mapping[str, Any], bundle: Any,
) -> list[dict[str, Any]]:
    """Assemble the ten-chapter judicial narrative. Fail-soft → []."""
    try:
        extras = (reading.get("chart") or {}).get("extras") or {}
        signs = dict(bundle.chart.planet_signs)
        houses = dict(bundle.kundali.planet_house)
        retro = dict(getattr(bundle.chart, "planet_retrograde", {}) or {})
        combust = dict(getattr(bundle, "combust", {}) or {})
        nav = dict(getattr(bundle, "navamsa_sign", {}) or {})
        lagna_sign = int(bundle.kundali.lagna_sign)
        lagna_lord = str(bundle.lagna_lord)
        moon_waxing = bool(getattr(bundle, "moon_waxing", True))

        hd = (extras.get("house_doctrine") or {}).get("houses") or {}
        pstr = {r["planet"]: r for r in
                ((extras.get("planet_strength") or {}).get("planets") or [])}
        cf = extras.get("classical_factors") or {}
        yogas = [y for y in (reading.get("classical_yogas") or [])
                 if isinstance(y, dict)]
        decisions = extras.get("domain_decisions") or []
        dn = extras.get("dasha_now") or {}

        # Raman's own verbatim statements for this chart, mapped to the house
        # each pertains to, so they can be woven into the relevant chapter.
        cites_by_house: dict[int, list[str]] = {}
        cites_global: list[str] = []
        for c in ((extras.get("raman_doctrine") or {}).get("favorable") or []):
            q = f'"{str(c.get("text", "")).rstrip(".")}." ({c.get("book_label", "")})'
            h = c.get("house")
            if h:
                cites_by_house.setdefault(int(h), []).append(q)
            else:
                cites_global.append(q)

        def hidx(h: int) -> int | None:
            return (hd.get(str(h)) or {}).get("verdict_index")

        def occupants(h: int) -> list[str]:
            return [p for p in _PLANET_SIG if houses.get(p) == h]

        def vargottama(p: str) -> bool:
            return p in signs and nav.get(p) == signs.get(p)

        def planet_state_clause(p: str) -> str:
            dig = (pstr.get(p) or {}).get("dignity")
            bits = [_dignity_clause(dig)]
            if combust.get(p):
                bits.append("combust")
            if retro.get(p) and p not in ("Sun", "Moon"):
                bits.append("retrograde")
            if vargottama(p):
                bits.append("vargottama, which lends it stability")
            return _andlist(bits)

        def well_placed(p: str) -> bool | None:
            """True = its higher qualities show, False = its shadow, None = mixed.
            Delegates to the shared lexicon predicate so both readings agree."""
            row = pstr.get(p) or {}
            return _lex_well_placed(
                row.get("dignity"), row.get("composite"), bool(combust.get(p)),
            )

        # Varied phrasings (indexed per planet) so the prose never reads from a
        # template — no repeated "Being well placed…" / "It confers…".
        _POS_T = (
            "Well placed, it lends {g}.",
            "From so strong a position it gives {g}.",
            "Its condition here favours {g}.",
            "So situated, it bestows {g}.",
            "Standing thus, it yields {g}.",
        )
        _NEG_T = (
            "Afflicted here, it turns rather to {s}, which the native does well to temper.",
            "In this weakened state it inclines to {s}.",
            "Its affliction here shows as {s}.",
            "Compromised in this place, it leans toward {s}.",
            "Under strain here, its expression tends to {s}.",
        )
        _MIX_T = (
            "It affords a fair measure of {g}.",
            "It gives a moderate share of {g}.",
            "Its expression of {g} is of a middling order.",
        )
        _P_IDX = {p: i for i, p in enumerate(
            ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"))}

        def quality_clause(p: str) -> str:
            good, shadow = _PLANET_QUALITY.get(p, ("", ""))
            if not good:
                return ""
            i = _P_IDX.get(p, 0)
            w = well_placed(p)
            if w is True:
                return _POS_T[i % len(_POS_T)].format(g=good)
            if w is False:
                return _NEG_T[i % len(_NEG_T)].format(s=shadow)
            return _MIX_T[i % len(_MIX_T)].format(g=good)

        chapters: list[dict[str, Any]] = []

        # ---- 1. General estimate --------------------------------------------
        strong = [h for h in range(1, 13) if (hidx(h) or 0) >= 5]
        afflicted = [h for h in range(1, 13) if (hidx(h) is not None and hidx(h) <= 1)]
        if len(strong) >= len(afflicted) + 3:
            tone = "This is, on the whole, a favourable horoscope"
        elif len(afflicted) >= len(strong) + 3:
            tone = "This horoscope is beset by certain afflictions"
        else:
            tone = "This is a horoscope of mixed strength"
        l1 = hidx(1)
        lord_h1 = hd.get("1") or {}
        p1 = [
            f"{tone}, its promise resting chiefly on the ascendant, its lord and "
            f"the Moon. The ascendant is {_grade_word(l1)}, "
            f"and the native is endowed with "
            f"{'considerable' if (l1 or 0) >= 5 else 'a fair measure of' if (l1 or 0) >= 3 else 'limited'} "
            f"natural fortune."
        ]
        if strong:
            areas = _andlist([_HOUSE_SIG[h].split(",")[0] for h in strong[:3]])
            p1.append(f"Its stronger promise lies in the matters of {areas}.")
        if afflicted:
            areas = _andlist([_HOUSE_SIG[h].split(",")[0] for h in afflicted[:3]])
            p1.append(
                f"On the other hand, {areas} are less favoured, and these temper "
                f"the fuller fruition of the horoscope's promise."
            )
        if cites_global:
            p1.append("The texts are explicit on the point: " + cites_global[0])
        chapters.append({"n": 1, "title": "General estimate of the horoscope",
                         "paras": [" ".join(p1)]})

        # ---- 2. The Ascendant ------------------------------------------------
        asc_name = _SIGN_NAMES[lagna_sign]
        temper = _SIGN_TEMPERAMENT.get(lagna_sign, "")
        occ1 = occupants(1)
        s = [f"The ascendant is {asc_name}, giving a nature that is {temper}."]
        if occ1:
            ben = [p for p in occ1 if (pstr.get(p) or {}).get("dignity")
                   in ("exalted", "own", "moolatrikona", "friendly")]
            s.append(
                f"It is occupied by {_andlist(occ1)}, which "
                f"{'strengthens the constitution and stamps the personality' if ben else 'colours the temperament'} "
                f"accordingly."
            )
        infl = [i["planet"] for i in (lord_h1.get("influencers") or [])
                if i.get("planet") not in occ1]
        if infl:
            s.append(
                f"The ascendant further receives the influence of {_andlist(infl[:3])}, "
                f"which must be weighed in judging the native's disposition and health."
            )
        s.append(
            f"The constitution may be taken as {_fav_phrase(l1)}"
            f"{'; the native should nonetheless guard against nervous strain' if (l1 or 0) <= 2 else ''}."
        )
        # A fuller portrait of character — temperament, mind, will, courage —
        # drawn before any prediction of events, as Raman was wont to do.
        moon_w = well_placed("Moon")
        sun_w = well_placed("Sun")
        mars_w = well_placed("Mars")
        portrait = [
            "As to character, the disposition given by the rising sign is "
            f"deepened by the several planets. The emotional nature, read from the "
            f"Moon, is "
            + ("warm, steady and sympathetic"
               if moon_w is True else "sensitive and somewhat changeful"
               if moon_w is False else "of an even temper") + "."
        ]
        portrait.append(
            "In will and ambition the native is "
            + ("resolute and desirous of honour"
               if sun_w is True else "of a modest and unassuming turn"
               if sun_w is False else "moderately ambitious") + ". In courage and "
            "enterprise the native is "
            + ("bold and self-reliant"
               if mars_w is True else "cautious, and better suited to steady effort than to contest"
               if mars_w is False else "capable when the occasion demands") + "."
        )
        # name one governing strength and one weakness from the planets
        strengths = [p for p in ("Jupiter", "Venus", "Mercury", "Sun", "Mars")
                     if well_placed(p) is True]
        weaknesses = [p for p in ("Saturn", "Mars", "Mercury", "Moon")
                      if well_placed(p) is False]
        if strengths:
            g = _PLANET_QUALITY[strengths[0]][0]
            portrait.append(f"The horoscope inclines the native to {g}.")
        if weaknesses:
            sh = _PLANET_QUALITY[weaknesses[0]][1]
            portrait.append(
                f"The chief failing to be guarded against is {sh}.")
        if cites_by_house.get(1):
            portrait.append("Of the ascendant the texts observe: "
                            + " ".join(cites_by_house[1][:2]))
        chapters.append({"n": 2, "title": "The Ascendant and the native's character",
                         "paras": [" ".join(s), " ".join(portrait)]})

        # ---- 3. The Ascendant lord ------------------------------------------
        llh = houses.get(lagna_lord)
        s = [
            f"The lord of the ascendant is {lagna_lord}, placed in the "
            f"{_HOUSE_ORD.get(llh, str(llh))} house — {_house_class(llh) if llh else 'its place'} — "
            f"and {planet_state_clause(lagna_lord)}."
        ]
        if llh in _KENDRAS or llh in _TRIKONAS:
            s.append(
                "Its situation in a favourable house lends the native capacity for "
                "self-assertion and lays a sound foundation for the horoscope."
            )
        elif llh in _DUSTHANAS:
            s.append(
                "Its situation in a difficult house is a source of some anxiety, "
                "though this may be relieved by other supporting factors."
            )
        s.append(
            f"On balance the lord of the ascendant is {_grade_word((lord_h1.get('lord') or {}).get('grade_index'))}, "
            f"and the self, health and general fortune partake of that condition."
        )
        chapters.append({"n": 3, "title": "The Ascendant lord",
                         "paras": [" ".join(s)]})

        # ---- 4. The Moon -----------------------------------------------------
        mh = houses.get("Moon")
        m_conj = [p for p in _PLANET_SIG if p != "Moon" and houses.get(p) == mh]
        s = [
            f"The Moon, the significator of the mind, is in "
            f"{_SIGN_NAMES[signs.get('Moon', lagna_sign)]} in the "
            f"{_HOUSE_ORD.get(mh, str(mh))} house, "
            f"{'waxing and therefore strong in paksha-bala' if moon_waxing else 'waning and therefore weak in paksha-bala'}."
        ]
        if m_conj:
            s.append(
                f"It is joined by {_andlist(m_conj)}, whose nature affects the "
                f"emotional temperament."
            )
        s.append(
            "The mental disposition is accordingly "
            + ("steady and well composed" if moon_waxing and mh in _KENDRAS | _TRIKONAS
               else "sensitive and at times unsettled")
            + ", and the native's happiness of mind should be judged largely from this."
        )
        qm = quality_clause("Moon")
        if qm:
            s.append(qm)
        chapters.append({"n": 4, "title": "The Moon and the mind",
                         "paras": [" ".join(s)]})

        # ---- 5. The Sun ------------------------------------------------------
        sh = houses.get("Sun")
        pre = ("The Sun, already noticed as lord of the ascendant, further signifies "
               if lagna_lord == "Sun" else "The Sun signifies ")
        s = [
            f"{pre}will, authority and the father. It occupies the "
            f"{_HOUSE_ORD.get(sh, str(sh))} house, {planet_state_clause('Sun')}."
        ]
        s.append(
            ("Its situation favours a desire for prominence and a capacity for "
             "authority" if sh in _KENDRAS | _TRIKONAS
             else "It confers a measured degree of authority")
            + f"; the state of the father may be inferred from the {_HOUSE_ORD.get(sh, '')} house it tenants."
        )
        qs = quality_clause("Sun")
        if qs:
            s.append(qs)
        chapters.append({"n": 5, "title": "The Sun, authority and the father",
                         "paras": [" ".join(s)]})

        # ---- 6. The remaining planets ---------------------------------------
        rem = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        parts = []
        for p in rem:
            ph = houses.get(p)
            if ph is None:
                continue
            qc = quality_clause(p)
            parts.append(
                f"{p}, signifying {_PLANET_SIG[p]}, is in the "
                f"{_HOUSE_ORD.get(ph, str(ph))} house, {planet_state_clause(p)}."
                + (f" {qc}" if qc else "")
            )
        node_bits = []
        for p in ("Rahu", "Ketu"):
            ph = houses.get(p)
            if ph is not None:
                node_bits.append(
                    f"{p} occupies the {_HOUSE_ORD.get(ph, str(ph))} house, "
                    f"lending its {'worldly and unconventional' if p == 'Rahu' else 'detached and intuitive'} "
                    f"colour to those affairs."
                )
        paras6 = [" ".join(parts)]
        if node_bits:
            paras6.append(" ".join(node_bits))
        chapters.append({"n": 6, "title": "The remaining planets", "paras": paras6})

        # ---- 7. The house lords ---------------------------------------------
        lord_sentences = []
        for h in range(1, 13):
            lord = SIGN_RULERS[((lagna_sign - 1 + h - 1) % 12) + 1]
            lh = houses.get(lord)
            lv = (hd.get(str(h)) or {}).get("lord") or {}
            sent = (
                f"The {_HOUSE_ORD[h]} lord {lord}, in the "
                f"{_HOUSE_ORD.get(lh, str(lh))} house, is "
                f"{_grade_word(lv.get('grade_index'))}, so that matters of "
                f"{_HOUSE_SIG[h].split(',')[0]} are "
                f"{_fav_phrase(lv.get('grade_index'))}."
            )
            # Weave the house's own cited Raman phrase here (house 1 handled in ch.2).
            if h != 1 and cites_by_house.get(h):
                sent += " Here the texts note: " + cites_by_house[h][0]
            lord_sentences.append(sent)
        # group into two paragraphs of six for readability
        chapters.append({
            "n": 7, "title": "The house lords",
            "paras": [" ".join(lord_sentences[:6]), " ".join(lord_sentences[6:])],
        })

        # ---- 8. The important yogas -----------------------------------------
        paras8: list[str] = []
        top_yogas = sorted(yogas, key=lambda y: float(y.get("intensity", 0.0)),
                           reverse=True)[:5]
        for y in top_yogas:
            parts_ = y.get("participants") or []
            full = float(y.get("intensity", 0.0)) >= 1.0
            afflicted_p = [p for p in parts_ if combust.get(p)
                           or (pstr.get(p) or {}).get("dignity") == "debilitated"]
            # Keep only the plain-language effect; drop engine shorthand tails.
            desc = str(y.get("description", ""))
            for cut in ("Triggers:", " — ", "  "):
                if cut in desc:
                    desc = desc.split(cut)[0]
            desc = desc.split(". ")[0].rstrip(". ")
            sent = (
                f"{y.get('name', '')} is present"
                f"{', formed by ' + _andlist(list(parts_)) if parts_ else ''}, "
                f"{'fully constituted' if full else 'partly constituted'} — "
                f"{desc}."
            )
            if afflicted_p:
                sent += (f" The {'combustion' if combust.get(afflicted_p[0]) else 'weakness'} "
                         f"of {_andlist(afflicted_p)} somewhat diminishes its fuller effect, "
                         f"yet the combination remains a source of good.")
            paras8.append(sent)
        if not paras8:
            paras8 = ["No yoga of the first importance is formed; the horoscope is to "
                      "be judged chiefly from the strength of the bhāvas and their lords."]
        chapters.append({"n": 8, "title": "The important yogas", "paras": paras8})

        # ---- 9. Synthesis of the bhāvas -------------------------------------
        order = ["career", "wealth", "marriage", "children", "health",
                 "education", "foreign", "spirituality"]
        dmap = {d["key"]: d for d in decisions}
        label = {"career": "Profession and standing", "wealth": "Wealth",
                 "marriage": "Marriage and domestic life", "children": "Children",
                 "health": "Health and constitution", "education": "Education and learning",
                 "foreign": "Travel and foreign residence",
                 "spirituality": "Fortune and spiritual life"}
        judgements = extras.get("judgements") or {}
        paras9 = []
        for k in order:
            d = dmap.get(k)
            if not d:
                continue
            # Prefer the conflict-resolution engine's single reconciled verdict so
            # the narrative and the dashboard deliver the SAME judgement.
            jv = (judgements.get(k) or {}).get("verdict")
            if jv:
                paras9.append(jv)
                continue
            idx = int(round((d.get("potential_index") or 0)))
            fav = _fav_phrase(idx)
            active = d.get("timing") == "Active now"
            if idx >= 4 and active:
                tclause = "and the present period supports their manifestation"
            elif idx >= 4:
                tclause = ("though a fuller fruition awaits a more favourable "
                           "period than the one now running")
            elif idx <= 2 and active:
                tclause = ("and, though the period stirs this matter, success comes "
                           "only through effort")
            else:
                tclause = "and they may be looked for rather in a later period"
            paras9.append(
                f"In the matter of {label[k].lower()}, the prospects are {fav}, {tclause}."
            )
        paras9_all = [" ".join(paras9)] if paras9 else []

        # Reconcile the leading contradiction, as Raman habitually did.
        idxof = {d["key"]: int(round(d.get("potential_index") or 0)) for d in decisions}
        recon = []
        car, wl, gn = idxof.get("career"), idxof.get("wealth"), None
        if car is not None and wl is not None and car >= 4 and wl <= 2:
            recon.append(
                "A characteristic contradiction deserves notice: recognition and "
                "position in the world are promised, yet the accumulation of wealth "
                "may not keep pace with the professional standing, and the native "
                "should temper worldly expectation accordingly."
            )
        elif idxof:
            hi = max(idxof, key=lambda k: idxof[k])
            lo = min(idxof, key=lambda k: idxof[k])
            if idxof[hi] - idxof[lo] >= 3 and hi != lo:
                recon.append(
                    f"The horoscope favours {label.get(hi, hi).lower()} far more than "
                    f"{label.get(lo, lo).lower()}; these opposite indications must be "
                    "held together in judgement, the one being promised where the "
                    "other is wanting."
                )
        if recon:
            paras9_all.append(" ".join(recon))

        chapters.append({"n": 9, "title": "Synthesis of the several bhāvas",
                         "paras": paras9_all})

        # ---- 10. Timing ------------------------------------------------------
        md = (dn.get("md") or {}).get("md_lord")
        ad = (dn.get("ad") or {}).get("ad_lord")
        active = [d["label"] for d in decisions if d.get("timing") == "Active now"]
        s10 = []
        if md:
            s10.append(
                f"The native at present passes through the mahādaśā of {md}"
                f"{' and the antardaśā of ' + ad if ad else ''}."
            )
            if active:
                s10.append(
                    f"This period chiefly bears upon {_andlist([a.lower() for a in active[:3]])}."
                )
            s10.append(
                "It should be remembered that the daśā only brings to fruition what "
                "the natal chart has promised; where the promise is strong the period "
                "yields its good freely, and where it is weak the period affords but "
                "limited results. Delays, where they occur, should not discourage the "
                "native, for what is promised is delayed rather than denied."
            )
        else:
            s10.append("The current period could not be determined from the timeline.")
        chapters.append({"n": 10, "title": "Timing — the daśā and the present period",
                         "paras": [" ".join(s10)]})

        return chapters
    except Exception:  # noqa: BLE001 — narrative is additive; never block a reading
        return []
