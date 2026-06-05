"""House 6 (Ari — enemies/disease/debt) RuleRecords.

Lord of the 6th in the 12 Houses: 12 evaluable RuleRecords encoded from
B.V. Raman, *How to Judge a Horoscope*, Vol. I, Chapter IX.  Each record
corresponds to one row of the Lord-of-the-6th table in
``docs/raman_saab/methodology/house_06_ari.md``.

Source span: HTJAH-I:6001–6060.  Signification covers the three principal
arishtas — enemies (shatru), disease (roga), debt (rina) — but the lord's
placement governs which of the three is principally activated; apply
modifications per HTJAH-I:6063–6065.

The 6th is a dusthana: results labelled "fortified" apply when the lord is
strong and well-aspected; "afflicted" when weak and ill-disposed.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H6.L.1", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 1),
        fortified="joins army as soldier or commander, or becomes Minister of War / prison official; "
                  "lives in maternal uncle's house",
        afflicted="becomes a robber, thief, or leader of a criminal gang",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 6001)),
    RuleRecord(
        id="H6.L.2", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 2),
        fortified="(with benefic conjunction/aspect) untold family suffering, deep sorrows, "
                  "loss of money through enemies, defective vision, uneven teeth, stammering",
        afflicted="loss of wife in Dasha/Bhukti of malefic lord; if Venus weak — celibate and "
                  "poverty-stricken",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6007)),
    RuleRecord(
        id="H6.L.3", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 3),
        fortified="enmity with brothers; maternal uncle works against native's interests; "
                  "native's brother suffers frequent ill-health",
        afflicted="no younger brothers",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6013)),
    RuleRecord(
        id="H6.L.4", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 4),
        fortified="lives in a dilapidated building; breaks in education; discards mother; "
                  "maternal uncles are land cultivators",
        afflicted="quarrels with mother; ancestral property in debts; works as a menial, "
                  "miserable life; trouble through servants",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6018)),
    RuleRecord(
        id="H6.L.5", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 5),
        fortified="sickly children; native adopted by maternal uncle and becomes fortunate",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6024)),
    RuleRecord(
        id="H6.L.6", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 6),
        fortified="increase of cousins; maternal uncle becomes famed",
        afflicted="(with weak Lagna-lord) incurable disease; increase of enmity with kith and kin",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 6027)),
    RuleRecord(
        id="H6.L.7", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 7),
        fortified="marries mother's/father's-sister's daughter; maternal uncle in far-off place; "
                  "wife's character doubtful",
        afflicted="early divorce or wife dies; hermaphrodite Rashi/Navamsha — sickly or barren "
                  "wife; with Lagna-lord in hermaphrodite sign — eunuch",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6031)),
    RuleRecord(
        id="H6.L.8", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 8),
        fortified="Madhyayu (middle life)",
        afflicted="plenty of debts; loathsome diseases; chases other women; takes pleasure in "
                  "inflicting pain",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6039)),
    RuleRecord(
        id="H6.L.9", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 9),
        fortified="father becomes a judge; maternal uncle highly fortunate; benefits from cousins "
                  "(but misunderstandings with father)",
        afflicted="poverty, sinful acts, misfortunes through relatives, ungrateful to preceptors; "
                  "(moderate) mason/timber-merchant/stone-cutter",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6045)),
    RuleRecord(
        id="H6.L.10", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 10),
        fortified="sinful and destructive nature; poses as orthodox/pious but really unscrupulous "
                  "in religion",
        afflicted="(lord weak) dismissal; formidable enemies; low life or begging",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6051)),
    RuleRecord(
        id="H6.L.11", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 11),
        fortified="(with benefic) eldest brother a judge; (ordinary) elder brother a judge but "
                  "loses the job",
        afflicted="(with malefic) poor wretched life; suffering on account of convictions",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 6055)),
    RuleRecord(
        id="H6.L.12", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 12),
        fortified="difficulty and sorrow through destructive nature; causes harm to others",
        afflicted="miserable, hard and wretched existence",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6059)),

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
