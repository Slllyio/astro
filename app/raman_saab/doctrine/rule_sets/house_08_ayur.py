"""House 8 (Ayur / Randhra / Mrityu Bhava — longevity/death) RuleRecords.

Lord of the 8th in the 12 Houses (Phase 2 encoding). Each entry encodes one
row of the "Lord of the 8th in the 12 Houses" table from the methodology doc
``house_08_ayur.md``, carrying the real corpus ``Citation`` (HTJAH-II, Vol II).

Source span: HTJAH-II:2884–7282. Karaka: Saturn (Ayushkaraka AND Mrutyukaraka
simultaneously — ``HTJAH-II:4606``).

Standing mitigator (recurs across all 12 placements): 8th lord in 6th/8th/12th
from Navamsa-Lagna **reduces** the evil (``HTJAH-II:2905``, 2923, 2965, 3023,
3037); fortification in a kendra/trikona **intensifies** it (``HTJAH-II:2967``).
Results are explicitly general and must be modified by Ascendant + Moon + Dasas
in operation (``HTJAH-II:3071–3072``).

Work tag: HTJAH-II (Vol II).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    # — Lord of the 8th in the 12 Houses (HTJAH-II:2902–3069) —
    RuleRecord(
        id="H8.L.1", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(8, 1),
        fortified="misfortune reduced when 8th lord is weak or placed in 6/8/12 of Navamsa-Lagna",
        afflicted="penury, heavy debts, misfortune at every step; disease, disfiguration, "
                  "weak body, trouble from government",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2902)),
    RuleRecord(
        id="H8.L.2", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(8, 2),
        fortified="evil reduced if 8th lord falls in 6/8/12 of Navamsa-Lagna",
        afflicted="eye and tooth trouble, putrid food, domestic discontent; wife estrangement "
                  "or separation; severe illness if longevity is otherwise good",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2916)),
    RuleRecord(
        id="H8.L.3", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(8, 3),
        fortified="conjunction with 6th/12th lords → monetary windfall via writing or a co-born",
        afflicted="deafness or ear trouble, quarrels with siblings, fears, hallucinations, "
                  "debts; unbearable if malefic-afflicted",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2927)),
    RuleRecord(
        id="H8.L.4", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(8, 4),
        fortified=None,
        afflicted="mental peace shattered; domestic and financial trouble; mother's health "
                  "endangered; loss of land and conveyance; pets die; native forced to seek "
                  "fortune abroad",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2940)),
    RuleRecord(
        id="H8.L.5", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(8, 5),
        fortified="mitigated if 8th lord is in 6/12/8 of Navamsa-Lagna; fortified in "
                  "kendra/trikona → evil intensified",
        afflicted="children get into crime or sickness; child may die at birth or be "
                  "retarded; nervous breakdown (5th = buddhisthana); 9th and 8th lords in "
                  "5th with debilitated Lagna-lord → no knowledge or wealth, lustful, reviled",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2957)),
    RuleRecord(
        id="H8.L.6", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(8, 6),
        fortified="Rajayoga — affluence, fame, desired objects",
        afflicted="ill-health (6th = disease); theft, court and police trouble; intensified "
                  "in kendra/trikona; maternal uncle suffers",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 2978)),
    RuleRecord(
        id="H8.L.7", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(8, 7),
        fortified="if 7th and 8th lords both strong → diplomatic foreign missions, distinction",
        afflicted="curtails longevity; wife's ill-health; native's disease; ill-health abroad",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2993)),
    RuleRecord(
        id="H8.L.8", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(8, 8),
        fortified="long life, happiness; lands, conveyance, power and position by past-life merit",
        afflicted="if weak → no serious trouble but no luck; father may die or face crisis; "
                  "if afflicted → failure, prompted to wrong acts",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3001)),
    RuleRecord(
        id="H8.L.9", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(8, 9),
        fortified="with benefics → inherits father's property; harmony with father",
        afflicted="with malefics → loses father's property; if Sun afflicted, father dies in "
                  "9th-lord period; weak 9th lord → hardship, deserted by kin",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3011)),
    RuleRecord(
        id="H8.L.10", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(8, 10),
        fortified="may confer unexpected gains via death of superiors or elders",
        afflicted="slow career, superseded by subordinates, deceit, government or law wrath, "
                  "poverty; with afflicted 2nd lord → reputation ruined by debts",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3027)),
    RuleRecord(
        id="H8.L.11", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(8, 11),
        fortified="benefic influence → friends and elder brother help overcome troubles",
        afflicted="trouble to close friends; elder brother's hard time, strained relations or "
                  "misconduct; business losses, debts",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3042)),
    RuleRecord(
        id="H8.L.12", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(8, 12),
        fortified="Rajayoga; if 12th lord in trine/quadrant → religious learning, piety, "
                  "post of authority",
        afflicted="benefics joining → treachery of friends, grief, unexpected loss; "
                  "malefic-afflicted → rape, adultery, counterfeiting, smuggling",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3053)),
)
