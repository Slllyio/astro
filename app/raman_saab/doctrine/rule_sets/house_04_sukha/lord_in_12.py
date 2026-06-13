"""House 4 (Sukha) — Lord-in-12-houses RuleRecords (HTJAH-I:4144-4205).

Moved verbatim from the former flat ``house_04_sukha.py`` (Stage-4 split)."""
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
)
