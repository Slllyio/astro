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
        # HTJAH-I:4236-4243 base + 4282-4283 modifiers. The base entry is unconditioned;
        # only 4282-4283 carries the pair. The Saturn/Mars clause is an ASPECT condition.
        # HTJAH-I:4236-4243 base + 4282-4283 modifiers. The base entry is unconditioned;
        # only 4282-4283 carries the pair. The Saturn/Mars clause is an ASPECT condition.
        general="generally unhappy and mentally worried; roaming about; the position promises "
                "some inheritance; interest in occult and philosophical studies; in the "
                "political field success is difficult; obstacles if Saturn or Mars aspects (an "
                "aspect, not an affliction)",
        fortified="the Sun strengthened -> financial benefits by inheritance",
        afflicted="the Sun afflicted -> trouble through political sources",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4236)),
    RuleRecord(
        id="H4.P.Moon", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Moon", 4),
        # LEAVE the afflicted slot - 4247 and 4284-4285 are genuine ('early separation from
        # the mother IF THE MOON IS AFFLICTED'; 'If afflicted, adverse changes'; 'If the
        # afflicted planet is Saturn, the mother dies early'). The MIRROR defect is in
        # fortified, which held the unconditioned base. Restores 'proud and somewhat
        # quarrelsome' (4246), dropped by the old encoding.
        # LEAVE the afflicted slot - 4247 and 4284-4285 are genuine ('early separation from
        # the mother IF THE MOON IS AFFLICTED'; 'If afflicted, adverse changes'; 'If the
        # afflicted planet is Saturn, the mother dies early'). The MIRROR defect is in
        # fortified, which held the unconditioned base. Restores 'proud and somewhat
        # quarrelsome' (4246), dropped by the old encoding.
        general="possesses a house; derives happiness from relatives; cheerful and contented; "
                "becomes important as a leader or ruler; proud and somewhat quarrelsome; fond "
                "of sensual pleasures unless aspected by Jupiter",
        fortified="the Moon fortified, that is well aspected or conjoined -> mental peace",
        afflicted="the Moon afflicted -> early separation from the mother, and adverse "
                  "changes; if the afflicting planet is Saturn, the mother dies early",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4245)),
    RuleRecord(
        id="H4.P.Mars", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mars", 4),
        # SENTIMENT-SPLIT. 4250-4251 is ONE sentence joined by Raman's own contrastive:
        # 'The person will be deprived of happiness from mother, relations and friends, BUT
        # will have success in the political line.' Its halves sat in opposite slots. His
        # headline 'This is generally a bad combination' (4250) was dropped entirely.
        # SENTIMENT-SPLIT. 4250-4251 is ONE sentence joined by Raman's own contrastive:
        # 'The person will be deprived of happiness from mother, relations and friends, BUT
        # will have success in the political line.' Its halves sat in opposite slots. His
        # headline 'This is generally a bad combination' (4250) was dropped entirely.
        general="this is generally a bad combination; deprived of happiness from mother, "
                "relations and friends, but will have success in the political line; quarrels "
                "with the mother and domestic affairs go awry; owns houses but will not be "
                "happy on that account; Mars with Rahu or Ketu -> a tendency to suicide (a "
                "conjunction, not an affliction)",
        fortified="Mars involved in benefic association or aspect -> the evil is tempered to a "
                  "certain amount",
        afflicted="Mars the afflicted planet -> loss through theft, deception and even "
                  "litigation; tragic developments in the personal life, quarrels, strife and "
                  "misunderstandings",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4250)),
    RuleRecord(
        id="H4.P.Mercury", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mercury", 4),
        # LEAVE the afflicted slot (4288-4289, 'Mercury afflicted'). Mirror defect only:
        # the unconditioned base reading moves out of fortified.
        # LEAVE the afflicted slot (4288-4289, 'Mercury afflicted'). Mirror defect only:
        # the unconditioned base reading moves out of fortified.
        general="shines as an educationist or diplomat; boldly criticises Government; held in "
                "esteem; a self-made father; good conveyance; taste for music and the fine "
                "arts; foreign travel; witty",
        fortified="Mercury well disposed -> intellectual and literary attainments",
        afflicted="Mercury afflicted -> mental distress, frauds and misery",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4255)),
    RuleRecord(
        id="H4.P.Jupiter", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Jupiter", 4),
        # LEAVE the afflicted slot (4289-4291, 'Jupiter afflicted'). Mirror defect only.
        # LEAVE the afflicted slot (4289-4291, 'Jupiter afflicted'). Mirror defect only.
        general="philosophical, learned and happy; favour of the ruling class; a terror to "
                "enemies; religious, respected and fortunate; a peaceful domestic environment; "
                "great spiritual advancement",
        fortified="Jupiter well-fortified -> prosperity in regard to all the events of the "
                  "fourth house, and a peaceful home-life",
        afflicted="Jupiter afflicted -> hardships and obstacles",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4260)),
    RuleRecord(
        id="H4.P.Venus", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Venus", 4),
        # LEAVE the afflicted slot (4291-4293, 'Venus in affliction'). Mirror defect only.
        # LEAVE the afflicted slot (4291-4293, 'Venus in affliction'). Mirror defect only.
        general="versed in music; polished manners; deep attachment to the mother; many "
                "friends, conveyances and houses; religious; achieves his desires; favourable "
                "for domestic concord",
        fortified="Venus well-fortified -> a great asset for the horoscope, a bright career as "
                  "an artist",
        afflicted="Venus in affliction -> looseness in morals and abuse of artistic talents",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4264)),
    RuleRecord(
        id="H4.P.Saturn", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Saturn", 4),
        # SPLIT. The base list (4268-4271) is unconditioned, and 4294 ('deprives the man of
        # peace of mind and the affection of the mother') was absent entirely. NOTE the old
        # fortified OVERSTATED Raman: he says the position IS NOT FAVOURED unless Saturn is
        # Lagnadhipati or beneficially aspected - a lordship/aspect condition, not a
        # fortification result - so it is restated in his own direction.
        # SPLIT. The base list (4268-4271) is unconditioned, and 4294 ('deprives the man of
        # peace of mind and the affection of the mother') was absent entirely. NOTE the old
        # fortified OVERSTATED Raman: he says the position IS NOT FAVOURED unless Saturn is
        # Lagnadhipati or beneficially aspected - a lordship/aspect condition, not a
        # fortification result - so it is restated in his own direction.
        general="sickly early; deprived of the mother and unhappy; windy and phlegmatic "
                "complaints; lethargic; no inherited property; troubles from houses and "
                "vehicles; disliked by relatives; desires seclusion; deprives the man of peace "
                "of mind and the affection of the mother",
        fortified="the position is NOT favoured unless Saturn is the Lagnadhipati, or is "
                  "beneficially aspected or associated (a lordship or aspect condition, not "
                  "fortification)",
        afflicted="an affliction by Mars -> a sudden downfall, and a combination for insanity; "
                  "(attribution UNVERIFIED - Raman states these inside the Saturn discussion "
                  "without naming a house-occupant) Rahu-Mars or Ketu-Mars affliction -> "
                  "tragedy or violence; Rahu-Saturn or Ketu-Saturn affliction -> mental "
                  "disorder, hysteria and even insanity",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4268)),
    RuleRecord(
        id="H4.P.Rahu", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Rahu", 4),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="foolish behaviour; few friends; subjected to fraud or guilty of fraud; "
                "Rahu-Mars affliction causes tragedy or violence; Rahu-Saturn affliction "
                "causes mental disorder, hysteria or insanity",
        fortified="foolish behaviour; few friends; subjected to fraud or guilty of fraud; "
                  "Rahu-Mars affliction causes tragedy or violence; Rahu-Saturn affliction "
                  "causes mental disorder, hysteria or insanity",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4273)),
    RuleRecord(
        id="H4.P.Ketu", house=4, signification="mother_home", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Ketu", 4),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="deprived of mother, property and happiness; lives in foreign place; "
                "exceptional experiences at end of life; reversals and sudden changes; "
                "Ketu-Mars causes tragedy or violence; Ketu-Saturn causes mental disorder, "
                "hysteria or insanity",
        fortified="deprived of mother, property and happiness; lives in foreign place; "
                  "exceptional experiences at end of life; reversals and sudden changes; "
                  "Ketu-Mars causes tragedy or violence; Ketu-Saturn causes mental disorder, "
                  "hysteria or insanity",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4277)),
)
