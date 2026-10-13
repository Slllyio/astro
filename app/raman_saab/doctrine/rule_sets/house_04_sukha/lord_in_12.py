"""House 4 (Sukha) — Lord-in-12-houses RuleRecords (HTJAH-I:4144-4205).

Moved verbatim from the former flat ``house_04_sukha.py`` (Stage-4 split).

SLOT MAPPING CORRECTED 2026-09-01 after an engine-blind doctrine review. This section is
GENERAL-ONLY: across HTJAH-I:4149-4188 there are ZERO fortification openers and exactly ONE
affliction opener (4181-4182, H4.L.10). Raman closes the section saying so himself
(4190-4193): "these combinations are very general and they should not be applied verbatim.
The good and bad nature of results ascribed to the fourth lord occupying a certain house
becomes augmented or minimised according to the strength or weakness of the fourth lord."

So each placement is ONE unconditioned sentence. The encoder had split most of them across
`fortified` and `afflicted` BY SENTIMENT — cutting Raman mid-list, and in H4.L.4 filing his
own final adjective ("sensual") as though it were an affliction. Those are reunited in the
`general` slot; `fortified` carries the same text so the fired prose is never empty.

H4.L.3 was worse than mis-slotted: it was INVERTED. Its "very little immovable property, even
loss of meagre possessions" comes from the Satyacharya note at 4193-4196, whose condition is
the OPPOSITE of affliction — "when the fourth lord, SUBJECTED TO SUBHA VARGAS OR FAVOURABLE
ASPECTS, is in the third, one acquires very little of immovable property". Raman's whole point
is that even a WELL-DISPOSED 4th lord in the 3rd gives little property. Filed under
`afflicted`, the encoding taught the reverse of the sentence's reason for existing.

Not encoded, and deliberately so: Raman's three-way strength modifier at 4196-4198 ("If the
fourth lord is moderately afflicted, the evil nature is somewhat tempered. If the fourth lord
is strongly afflicted, there will be an intensification") is a SECTION-WIDE modifier, not a
per-placement branch, and there is no slot for a middling grade.

CORRECTED 2026-10-13 (House-4 strength-slot sweep). Two claims above were half-right, and one
count was wrong:
- The Satyacharya note's condition is favourable, but it is subha VARGAS or favourable ASPECTS --
  not Shadbala strength -- so `fortified` was the wrong home as well. It is now H4.L.3a, fired on
  benefic aspect (the only encodable half), and H4.L.3's base reading is back in `fortified`.
- 4181 IS the section's one affliction opener, but the `afflicted` slot is a STRENGTH label
  (`_branch` selects it on weak Shadbala). It is now H4.L.10a with an affliction predicate.
- "ZERO fortification openers" misses 4150-4151, which grades the 4th lord in Lagna strong /
  middling / weak. Its outer tiers sit in the strength slots correctly; the middle tier is
  H4.L.1a."""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H4.L.1", house=4, signification="mother_home", group="lord_in_house",
        # 2026-10-13 House-4 sweep: 4150-4151 grades the 4th lord in Lagna strong / middling
        # / weak (rich / mediocre / poor family). The middle tier was in general; a binary
        # branch cannot express it, so it is H4.L.1a.
        kind="evaluable", condition=C.LordIn(4, 1),
        # HTJAH-I:4149-4151. The base sentence is unconditioned; only the family's wealth
        # is graded, and Raman grades it THREE ways — "strong, middling or weak... rich,
        # mediocre or poor". The middling grade has no slot and is deliberately NOT folded
        # into either branch; it is named here so the omission is visible.
        general="highly learned, but afraid to speak in public assemblies; likely to lose "
                "inherited wealth",
        fortified="highly learned, but afraid to speak in public assemblies; likely to lose "
                  "inherited wealth; born in a rich family",
        afflicted="the 4th lord in Lagna weak - born in a poor family",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4149)),
    RuleRecord(
        id="H4.L.1a", house=4, signification="mother_home", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="the 4th lord in Lagna middling in strength - born in a mediocre family. "
                "TODO(predicate: a MIDDLE Shadbala band; is_powerful is binary)",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4150)),
    RuleRecord(
        id="H4.L.2", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 2),
        # HTJAH-I:4153-4154 is one unconditioned sentence; "He will have a sarcastic
        # nature" is the middle of Raman's own list, not an afflicted reading.
        general="highly fortunate, courageous and happy; will have a sarcastic nature; "
                "inherits property from the maternal grandfather",
        fortified="highly fortunate, courageous and happy; will have a sarcastic nature; "
                  "inherits property from the maternal grandfather",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4153)),
    RuleRecord(
        id="H4.L.3", house=4, signification="mother_home", group="lord_in_house",
        # 2026-10-13 House-4 sweep: the Satyacharya note (4193-4196) is gated on subha
        # VARGAS or favourable ASPECTS, not Shadbala, so it left fortified for H4.L.3a. A
        # strong lord had been losing its base reading to it.
        kind="evaluable", condition=C.LordIn(4, 3),
        # HTJAH-I:4156-4157 unconditioned. The property clause was INVERTED: it comes from
        # the Satyacharya note at 4193-4196, conditioned on the 4th lord being "subjected to
        # subha vargas or favourable aspects" — the OPPOSITE of affliction. Moved to
        # `fortified`, where its actual condition puts it.
        general="sickly, generous, a man of character, and acquires wealth by self-effort; "
                "suffers from the machinations of step-brothers and step-mother",
        fortified="sickly, generous, a man of character, and acquires wealth by "
                  "self-effort; suffers from the machinations of step-brothers and "
                  "step-mother",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4156)),
    # Only the favourable-ASPECT half of Raman's 'subha vargas or favourable aspects' is
    # encodable (no subha-varga predicate); Jupiter and Venus only, since the Moon and
    # Mercury are benefic only conditionally. Fires less often than the text allows, never
    # wrongly. Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H4.L.3a", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(4, 3), C.Or(C.Aspects("Jupiter", "LORD_OF:4"), C.Aspects("Venus", "LORD_OF:4"))),
        general="the 4th lord in the 3rd under favourable aspects (Satyacharya) - acquires "
                "very little immovable property, and may even be deprived of his meagre "
                "possessions, besides trouble on account of step-mother and step-brothers",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4193)),
    RuleRecord(
        id="H4.L.4", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 4),
        # HTJAH-I:4159-4160. "sensual" is the last adjective of Raman's own list
        # ("rich, respected, happy and sensual"), not an afflicted reading.
        general="religiously inclined, with respect for traditions; rich, respected, happy "
                "and sensual",
        fortified="religiously inclined, with respect for traditions; rich, respected, happy "
                  "and sensual",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4159)),
    RuleRecord(
        id="H4.L.5", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 5),
        # HTJAH-I:4162-4163, unconditioned throughout.
        general="loved and respected by others, a devotee of Vishnu, becomes rich by "
                "self-effort; the mother comes from a respectable family; acquires vehicles",
        fortified="loved and respected by others, a devotee of Vishnu, becomes rich by "
                  "self-effort; the mother comes from a respectable family; acquires vehicles",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4162)),
    RuleRecord(
        id="H4.L.6", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 6),
        # HTJAH-I:4165-4166, one unconditioned sentence. `fortified` held "active, prone
        # to roaming" — a positive re-spin of Raman's "He will always be roaming about", with
        # "active" appearing nowhere in the section. Raman gives NO favourable variant for
        # this placement, and inventing one to fill the slot is exactly what the slot must
        # not invite.
        general="short-tempered and mean, with dissimulating habits, evil thoughts and "
                "intentions; he will always be roaming about",
        fortified="short-tempered and mean, with dissimulating habits, evil thoughts and "
                  "intentions; he will always be roaming about",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4165)),
    RuleRecord(
        id="H4.L.7", house=4, signification="mother_home", group="lord_in_house",
        # 2026-10-13 House-4 sweep: the livelihood clause (4168-4170) is gated on the 7th
        # being a movable or fixed SIGN -- testable exactly, since the 4th lord in the 7th
        # sits in that sign. Now H4.L.7a/b; neither fires in a dual sign, where Raman says
        # nothing.
        kind="evaluable", condition=C.LordIn(4, 7),
        # HTJAH-I:4168-4170, unconditioned. The distant-place clause is a SIGN-MODALITY
        # configuration ("according as the seventh happens to be a movable or fixed sign"),
        # not a strength branch.
        general="generally happy; commands houses and lands",
        fortified="generally happy; commands houses and lands",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4168)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H4.L.7a", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(4, 7), C.Or(C.InSign("LORD_OF:4", 1), C.InSign("LORD_OF:4", 4), C.InSign("LORD_OF:4", 7), C.InSign("LORD_OF:4", 10))),
        general="the 4th lord in the 7th in a movable sign - ekes out a livelihood in "
                "distant places",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4168)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H4.L.7b", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(4, 7), C.Or(C.InSign("LORD_OF:4", 2), C.InSign("LORD_OF:4", 5), C.InSign("LORD_OF:4", 8), C.InSign("LORD_OF:4", 11))),
        general="the 4th lord in the 7th in a fixed sign - ekes out a livelihood near his "
                "birthplace",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4169)),
    RuleRecord(
        id="H4.L.8", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 8),
        # HTJAH-I:4172-4173, unconditioned. `fortified` held the encoder's honest
        # disclosure "no specific benefit noted" — correct as a note, but it displayed to
        # the reader AS the strong-lord reading. Raman's own text takes the slot; the
        # disclosure survives as this comment: he gives no favourable variant here.
        general="the person becomes miserable; the father dies early; either impotent or "
                "loose in sex-life; likely to lose landed properties or face litigation",
        fortified="the person becomes miserable; the father dies early; either impotent or "
                  "loose in sex-life; likely to lose landed properties or face litigation",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4172)),
    RuleRecord(
        id="H4.L.9", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 9),
        # HTJAH-I:4175-4176. Raman's own "Generally a fortunate combination" flags this as
        # the unconditioned base, not a fortification.
        general="generally a fortunate combination, favouring happiness in regard to father "
                "and properties",
        fortified="generally a fortunate combination, favouring happiness in regard to "
                  "father and properties",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4175)),
    RuleRecord(
        id="H4.L.10", house=4, signification="mother_home", group="lord_in_house",
        # 2026-10-13 House-4 sweep: 'Loss of reputation is possible if the 4th lord is
        # afflicted' (4181) is an AFFLICTION clause, not a weakness clause -- now H4.L.10a.
        kind="evaluable", condition=C.LordIn(4, 10),
        # HTJAH-I:4180-4182. The ONE genuine affliction opener in this section:
        # "Loss of reputation is possible if the 4th lord is afflicted."
        general="political success; an expert chemist; vanquishes his enemies and makes his "
                "personality felt by the world",
        fortified="political success; an expert chemist; vanquishes his enemies and makes "
                  "his personality felt by the world",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4180)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H4.L.10a", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(4, 10), C.AfflictedBy("LORD_OF:4")),
        general="the 4th lord in the 10th afflicted - loss of reputation is possible",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4181)),
    RuleRecord(
        id="H4.L.11", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 11),
        # HTJAH-I:4184-4185, one unconditioned sentence; "sickly" and the step-mother
        # clause sit inside Raman's own list.
        general="self-made, generous, sickly; the mother fortunate, but he may have a "
                "step-mother also; favours success in selling and buying cattle and lands",
        fortified="self-made, generous, sickly; the mother fortunate, but he may have a "
                  "step-mother also; favours success in selling and buying cattle and lands",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4184)),
    RuleRecord(
        id="H4.L.12", house=4, signification="mother_home", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(4, 12),
        # HTJAH-I:4187-4188, unconditioned. Same disclosure-in-the-slot as H4.L.8: Raman
        # gives no favourable variant for this placement.
        general="deprived of happiness and properties; early death to the mother; bad "
                "finances and generally a miserable existence",
        fortified="deprived of happiness and properties; early death to the mother; bad "
                  "finances and generally a miserable existence",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4187)),
)
