"""Ari / Roga Bhava (enemies / disease / debts / accidents) — Planets-in-the-house RuleRecords.

Moved verbatim from the former flat ``house_06_ari.py`` (Stage-4 split)."""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    # — Planets in the 6th House (HTJAH-I:6115–6157) —
    RuleRecord(
        id="H6.P.Sun", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Sun", 6),
        fortified="good politician, famous, successful; administrative ability; few enemies; "
                  "wealthy; with Mercury → handles Govt trouble well",
        afflicted="not very good for health; long troublesome illness; Saturn affliction → "
                  "heart trouble/chest pain unless relieved by Jupiter's aspect",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6115)),
    RuleRecord(
        id="H6.P.Moon", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Moon", 6),
        fortified="ability and success in subordinate positions; success as caterer",
        afflicted="Balarishta / much ill-health in childhood; Mars+Saturn affliction → "
                  "curious incurable diseases and revengeful enemies; fixed sign → stone in "
                  "bladder, submissive to women, stomach troubles; common sign afflicted → "
                  "lung danger; Rahu/Ketu → mental derangement",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 6120)),
    RuleRecord(
        id="H6.P.Mars", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mars", 6),
        fortified="highly passionate, victorious, successful as ruler/politician; well-disposed "
                  "— an asset",
        afflicted="worries from near relatives; accidents, losses, troubles through employees; "
                  "Saturn → death by operation/animal injury; Rahu → suicide; Ketu → poisoning; "
                  "Saturn-on-Mars → litigation with brothers/cousins",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6126)),
    RuleRecord(
        id="H6.P.Mercury", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mercury", 6),
        fortified="sharp intellect; terror to enemies; with Jupiter → spiritual gains; "
                  "quarrelsome and showy yet respected; interrupted education",
        afflicted="mental troubles, nervous breakdown; Mars+Rahu or Saturn+Rahu → insanity "
                  "through excitement, servant troubles; Rahu/Ketu/Saturn → despondency, "
                  "abnormal behaviour",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 6131)),
    RuleRecord(
        id="H6.P.Jupiter", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Jupiter", 6),
        fortified="feared by enemies; health generally good",
        afflicted="inactive, suffers disrespect, indulges in black magic, unlucky, dyspeptic; "
                  "health suffers through over-indulgence; hardships and intemperance in food",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 6138)),
    RuleRecord(
        id="H6.P.Venus", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Venus", 6),
        fortified="no enemies; favours from women; well-placed → success in nursing, films, drama",
        afflicted="corrupted by young women; health affected by sexual indulgence, licentious; "
                  "urinary and sexual troubles",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 6141)),
    RuleRecord(
        id="H6.P.Saturn", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Saturn", 6),
        fortified="foeless, courageous; gains through contract, mining, masonry; quarrelsome "
                  "and obstinate but voracious eater",
        afflicted="sickness through privation/neglect; subordinate troubles; Mars → dangerous "
                  "illness and operations; Rahu → hysteria; incurable/undiagnosable psychic "
                  "conditions",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6145)),
    RuleRecord(
        id="H6.P.Rahu", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Rahu", 6),
        fortified="long-lived and wealthy; many cousins",
        afflicted="troubled by enemies, ghosts, diseases in private parts; puzzling sickness; "
                  "scandalous private life; Moon+Saturn join Rahu → mental derangement; "
                  "Rahu's affliction — huge debts, unexpected enmities, incurable diseases; "
                  "Rahu+Saturn+Moon → psychological misfit",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6150)),
    RuleRecord(
        id="H6.P.Ketu", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Ketu", 6),
        fortified="best position for Ketu in a horoscope; fame, authority, foeless; "
                  "intuitive and occult powers",
        afflicted="moral character loose",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6155)),
)
