"""House 4 (Sukha) — Planets-in-the-4th RuleRecords (HTJAH-I:4234-4299).

Moved verbatim from the former flat ``house_04_sukha.py`` (Stage-4 split)."""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    # — planets in the 4th house (HTJAH-I:4234–4299) —
    RuleRecord(
        id="H4.P.Sun", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Sun", 4),
        fortified="financial benefits by inheritance; occult and philosophical interest",
        afflicted="generally unhappy and mentally worried; roaming; political success difficult; "
                  "obstacles if Saturn or Mars aspects; trouble through political sources",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4236)),
    RuleRecord(
        id="H4.P.Moon", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Moon", 4),
        fortified="possesses house; happiness from relatives; cheerful and contented; "
                  "important as leader or ruler; mental peace",
        afflicted="early separation from mother if afflicted; fond of sensual pleasures unless "
                  "aspected by Jupiter; adverse changes; Saturn affliction kills mother early",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4245)),
    RuleRecord(
        id="H4.P.Mars", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mars", 4),
        fortified="success in political line; owns houses (though unhappy on that account); "
                  "benefic association tempers evil",
        afflicted="deprived of happiness from mother, relations and friends; quarrels with mother; "
                  "domestic discord; Mars-Rahu/Ketu tendency to suicide; loss by theft, deception "
                  "or litigation; tragic developments",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4250)),
    RuleRecord(
        id="H4.P.Mercury", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mercury", 4),
        fortified="shines as educationist or diplomat; boldly criticises Government; held in "
                  "esteem; self-made father; good conveyance; taste for music and fine arts; "
                  "foreign travel; witty; intellectual and literary attainments",
        afflicted="mental distress, frauds and misery",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4255)),
    RuleRecord(
        id="H4.P.Jupiter", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Jupiter", 4),
        fortified="philosophical, learned, happy; favour of ruling class; terror to enemies; "
                  "religious, respected, fortunate; peaceful domestic environment; great spiritual "
                  "advancement; prosperity in all 4th-house matters",
        afflicted="hardships and obstacles",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4260)),
    RuleRecord(
        id="H4.P.Venus", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Venus", 4),
        fortified="versed in music; polished manners; deep attachment to mother; many friends, "
                  "conveyances and houses; religious; achieves desires; favourable for domestic "
                  "concord; bright career as artist",
        afflicted="looseness in morals; abuse of artistic talents",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4264)),
    RuleRecord(
        id="H4.P.Saturn", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Saturn", 4),
        fortified="favourable when Saturn is Lagnadhipati or beneficially aspected/associated",
        afflicted="sickly early; deprived of mother and unhappy; windy/phlegmatic complaints; "
                  "lethargic; no inherited property; troubles from houses and vehicles; disliked "
                  "by relatives; desires seclusion; Mars affliction causes sudden downfall or "
                  "insanity; Rahu/Ketu-Saturn affliction causes mental disorder, hysteria or insanity",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4268)),
    RuleRecord(
        id="H4.P.Rahu", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Rahu", 4),
        fortified=None,
        afflicted="foolish behaviour; few friends; subjected to fraud or guilty of fraud; "
                  "Rahu-Mars affliction causes tragedy or violence; Rahu-Saturn affliction "
                  "causes mental disorder, hysteria or insanity",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4273)),
    RuleRecord(
        id="H4.P.Ketu", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Ketu", 4),
        fortified=None,
        afflicted="deprived of mother, property and happiness; lives in foreign place; "
                  "exceptional experiences at end of life; reversals and sudden changes; "
                  "Ketu-Mars causes tragedy or violence; Ketu-Saturn causes mental disorder, "
                  "hysteria or insanity",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4277)),
)
