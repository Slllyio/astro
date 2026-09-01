"""House 3 (Sahaja / Bhratru Bhava) — the nine planets in the 3rd house.

Encodes the "Planets in the 3rd House" table from
`docs/raman_saab/methodology/house_03_sahaja.md`; each record cites the first
line of its planet's paragraph (HTJAH-I:3472-3517).
Moved verbatim from the former single-module `house_03_sahaja.py` (Stage-1 split).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    # — Planets in the 3rd House (HTJAH-I:3472-3517) —
    RuleRecord(
        id="H3.P.Sun", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Sun", 3),
        # ★ UNSOURCED CLAUSE REMOVED 2026-09-01. `fortified` ended with "with Mercury →
        # highly intelligent; with Jupiter → spiritually strong". HTJAH-I:3472-3474 — the
        # cited paragraph, quoted in full — is three sentences and names NO other planet:
        # "The Sun.—Makes the person courageous. The mind becomes resourceful and restive,
        # successful. Bad for brothers if afflicted. Discredit through letters. Position of
        # the Sun in the 3rd is one of the strong points in a horoscope."
        # The clause is transplanted from the SEVENTH-house modifier paragraph at
        # HTJAH-I:8218-8220, and its subject is reassigned on the way: Raman writes that the
        # PARTNER "may be a highly evolved spiritual soul", not that the native is
        # spiritually strong. The project's own methodology doc (house_03_sahaja.md:122)
        # carries no such modifier either, so it entered at the encoding step. The same
        # 8218-8219 sentence was independently found transplanted into H6.P.Sun.
        general="makes the person courageous; the mind becomes resourceful, restive and "
                "successful; discredit through letters; the position of the Sun in the 3rd "
                "is one of the strong points in a horoscope",
        fortified="makes the person courageous; the mind becomes resourceful, restive and "
                  "successful; discredit through letters; the position of the Sun in the 3rd "
                  "is one of the strong points in a horoscope",
        # "Bad for brothers if afflicted" (3473) is the ONE conditioned clause. The old slot
        # also restated it a second time as "ill effects on co-borns"; de-duplicated.
        afflicted="bad for brothers",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 3472)),
    RuleRecord(
        id="H3.P.Moon", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Moon", 3),
        # HTJAH-I:3476-3479. One genuine affliction opener ("An unfavourable position for
        # peace of mind, if afflicted", 3479) — kept. "Subordinate to wife" is unconditioned.
        # The waning clause is a LUNAR-PHASE condition, not an affliction; flagged in place.
        general="generally changes in occupation; fond of travelling; active-minded; the wife "
                "will be fair; possesses good knowledge; rather indifferent to the spiritual "
                "values of life; subordinate to wife; attached to children",
        fortified="generally changes in occupation; fond of travelling; active-minded; the "
                  "wife will be fair; possesses good knowledge; rather indifferent to the "
                  "spiritual values of life; subordinate to wife; attached to children",
        afflicted="an unfavourable position for peace of mind; and (a lunar phase, not an "
                  "affliction) the Moon waning → cruel, miserable, impious and unscrupulous",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3476)),
    RuleRecord(
        id="H3.P.Mars", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mars", 3),
        # HTJAH-I:3481-3486. "Reckless, pioneering and unprincipled" (3482) is ONE sentence
        # that was cut across both slots. The genuine afflicted clause is "If the house is
        # further afflicted, it shows thoughts of suicide or violent tendencies" (3483-3484).
        # The Capricorn/Aries/Scorpio clause is a SIGN-identity mitigator (3486), not a
        # fortification result.
        general="this position is bad for brothers and sisters; liability to danger and "
                "accidents by journeys; brave; worried on account of family misunderstandings; "
                "reckless, pioneering and unprincipled; may be troubled with ear defects or "
                "even deafness",
        fortified="(a sign condition, not fortification) the 3rd being Capricorn, Aries or "
                  "Scorpio → the evil effects will be largely modified",
        afflicted="the house further afflicted → thoughts of suicide or violent tendencies",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 3481)),
    RuleRecord(
        id="H3.P.Mercury", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mercury", 3),
        # HTJAH-I:3488-3493. The `afflicted` slot is exactly and only Raman's conditioned
        # clause ("When Mercury is afflicted the native is inclined to nervous break-down",
        # 3492-3493) — correctly encoded, untouched. Only the unconditioned base reading
        # moves out of `fortified`. Restores "but he will not himself be happy" (3488), the
        # entry's one unconditioned negative, whose omission made the reading look purely
        # favourable.
        general="does good for others but he will not himself be happy; sharp mind; fond of "
                "reading and study; persistent; tactful and diplomatic; success in trade and "
                "speculation; a number of brothers and sisters; gain through 3rd-house affairs",
        fortified="does good for others but he will not himself be happy; sharp mind; fond of "
                  "reading and study; persistent; tactful and diplomatic; success in trade "
                  "and speculation; a number of brothers and sisters; gain through 3rd-house "
                  "affairs",
        afflicted="Mercury afflicted → inclined to nervous breakdown",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 3488)),
    RuleRecord(
        id="H3.P.Jupiter", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 3),
        # HTJAH-I:3495-3498. Raman gives the miser / no-love-of-family / heated-body run
        # UNCONDITIONALLY, immediately after "This is also a good position" — the poles
        # coexist in his base reading. Only "He may be devoid of gratitude if Jupiter is
        # afflicted" (3497) is gated. The two sentences that follow it ("He does not have
        # many friends. Does not take advantage of opportunities.") are UNDETERMINED — the
        # reviewer could not tell whether they resume the base run or continue the condition
        # — so they are left in `afflicted` where the encoder put them, and flagged here
        # rather than moved on a guess.
        general="this is also a good position; the mind is optimistic and philosophical; will "
                "have many good brothers; becomes a miser; does not love family and children; "
                "the body gets heated and he suffers from ill-health; adapts himself to "
                "conventionalities",
        fortified="this is also a good position; the mind is optimistic and philosophical; "
                  "will have many good brothers; becomes a miser; does not love family and "
                  "children; the body gets heated and he suffers from ill-health; adapts "
                  "himself to conventionalities",
        afflicted="Jupiter afflicted → devoid of gratitude; (UNDETERMINED whether the "
                  "condition carries) few friends, does not take advantage of opportunities",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 3495)),
    RuleRecord(
        id="H3.P.Venus", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 3),
        # HTJAH-I:3500-3503. "The mental quality is good but health will be poor, lacking in
        # vitality" (3500) is ONE sentence cut across both slots at its "but". The genuine
        # afflicted clause is "If Venus is afflicted, miserly, mean, poor and highly sensual"
        # (3501-3502). "He becomes funky and interested in scandals" (3502) is UNDETERMINED —
        # a fresh sentence after the condition — so it stays where the encoder put it.
        general="the mental quality is good but health will be poor, lacking in vitality; "
                "takes delight in singing, music, dancing and fine arts; financially he will "
                "not be very successful; brothers will be good; not much happiness from "
                "children",
        fortified="the mental quality is good but health will be poor, lacking in vitality; "
                  "takes delight in singing, music, dancing and fine arts; financially he "
                  "will not be very successful; brothers will be good; not much happiness "
                  "from children",
        afflicted="Venus afflicted → miserly, mean, poor and highly sensual; (UNDETERMINED "
                  "whether the condition carries) funky and interested in scandals",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3500)),
    RuleRecord(
        id="H3.P.Saturn", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Saturn", 3),
        # HTJAH-I:3505-3510. "Brave and courageous, wealthy, loss of brothers, eccentric and
        # cruel" (3505) is ONE sentence — Raman packs both poles into a single breath — and
        # it was cut across the two slots. The genuine afflicted clause is "If Saturn is
        # afflicted, the despondency is likely to run into mental affliction" (3509-3510).
        general="brave and courageous, wealthy, loss of brothers, eccentric and cruel; sorrow "
                "through brothers; honoured by rulers; may become head or president of local "
                "boards and municipalities; he will protect many people; success attends him "
                "only after he has suffered disappointments and reverses; the tendency of the "
                "mind is towards gloom, anxiety and misgivings; the mental condition improves "
                "with age",
        fortified="brave and courageous, wealthy, loss of brothers, eccentric and cruel; "
                  "sorrow through brothers; honoured by rulers; may become head or president "
                  "of local boards and municipalities; he will protect many people; success "
                  "attends him only after he has suffered disappointments and reverses; the "
                  "tendency of the mind is towards gloom, anxiety and misgivings; the mental "
                  "condition improves with age",
        afflicted="Saturn afflicted → the despondency is likely to run into mental "
                  "affliction",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3505)),
    RuleRecord(
        id="H3.P.Rahu", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Rahu", 3),
        # HTJAH-I:3512-3513: four flat unconditioned sentences, split by sentiment. Raman
        # marks the reading general in his own words — "The combination is GENERALLY bad for
        # brothers."
        general="brave for outward appearances; sudden and unexpected news; the combination "
                "is generally bad for brothers; he may incur severe criticism on account of "
                "his views and ideas",
        fortified="brave for outward appearances; sudden and unexpected news; the combination "
                  "is generally bad for brothers; he may incur severe criticism on account of "
                  "his views and ideas",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 3512)),
    RuleRecord(
        id="H3.P.Ketu", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 3),
        # HTJAH-I:3517. "Strong and adventurous but funky." is ONE sentence, split at the
        # "but" — the purest instance of the defect found anywhere in this sweep.
        general="strong and adventurous but funky; disturbs the mind with hallucinations",
        fortified="strong and adventurous but funky; disturbs the mind with hallucinations",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 3517)),
)
