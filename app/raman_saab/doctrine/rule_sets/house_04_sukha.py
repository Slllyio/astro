"""House 4 (Sukha — mother/home/happiness) RuleRecords.

Lord-of-the-4th in the 12 houses, encoded from B.V. Raman,
*How to Judge a Horoscope*, Vol. I, Chapter VII "Concerning the
Fourth House."  Each record is one row of Raman's placement table
(HTJAH-I:4149–4188) with Satyacharya's fortified/afflicted scaling
rule (HTJAH-I:4193–4198): the listed result is the baseline;
4th-lord strength augments the good column, weakness/affliction
augments the evil column.

Primary signification: "mother_home" (covers mother, home, ancestral
property, general happiness, vehicles, education — judged together at
the lord level before sub-matter routing).

Source span: HTJAH-I:4117–5009.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H4.L.1", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 1),
        fortified="highly learned; born in a rich family",
        afflicted="afraid to speak in public; likely loses inherited wealth; poor family if weak",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4149)),
    RuleRecord(
        id="H4.L.2", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 2),
        fortified="highly fortunate, courageous, happy; inherits property from maternal grandfather",
        afflicted="sarcastic nature",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4153)),
    RuleRecord(
        id="H4.L.3", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 3),
        fortified="generous, man of character; acquires wealth by self-effort",
        afflicted="sickly; suffers from machinations of step-brothers/step-mother; "
                  "very little immovable property, even loss of meagre possessions",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4156)),
    RuleRecord(
        id="H4.L.4", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 4),
        fortified="religiously inclined, respects tradition; rich, respected, happy",
        afflicted="sensual",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4159)),
    RuleRecord(
        id="H4.L.5", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 5),
        fortified="loved and respected, devotee of Vishnu, rich by self-effort; "
                  "mother from respectable family; acquires vehicles",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4162)),
    RuleRecord(
        id="H4.L.6", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 6),
        fortified="active, prone to roaming",
        afflicted="short-tempered, mean, dissimulating, evil thoughts, always roaming",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4165)),
    RuleRecord(
        id="H4.L.7", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 7),
        fortified="generally happy; commands houses and lands; livelihood in distant place "
                  "(movable sign) or near birthplace (fixed sign)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4168)),
    RuleRecord(
        id="H4.L.8", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 8),
        fortified="no specific benefit noted",
        afflicted="miserable; father dies early; impotent or loose sex-life; "
                  "loses landed property or faces litigation",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4172)),
    RuleRecord(
        id="H4.L.9", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 9),
        fortified="fortunate — happiness regarding father and properties",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4175)),
    RuleRecord(
        id="H4.L.10", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 10),
        fortified="political success; expert chemist; vanquishes enemies; makes personality felt",
        afflicted="loss of reputation possible if 4th lord afflicted",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4180)),
    RuleRecord(
        id="H4.L.11", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 11),
        fortified="self-made, generous; mother fortunate; success in selling and buying cattle and lands",
        afflicted="sickly; may have step-mother",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4184)),
    RuleRecord(
        id="H4.L.12", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 12),
        fortified="no specific benefit noted",
        afflicted="deprived of happiness and properties; early death of mother; "
                  "bad finances; miserable existence",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4187)),

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
