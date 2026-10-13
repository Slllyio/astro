"""House 5 (Putra) — Lord-in-12-houses RuleRecords (HTJAH-I:5040-5169).

Moved verbatim from the former flat ``house_05_putra.py`` (Stage-4 split)."""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H5.L.1", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 1),
        # "will have foes" (HTJAH-I:5114) was silently DROPPED. Raman lists it between "few
        # children" and "gives happiness to others"; the encoding kept both flanking items and
        # deleted the one in the middle -- a negative result trimmed out of a favourable arm
        # by sentiment.
        fortified="commands servants; Judge / Magistrate / Minister empowered to punish the "
                  "evil-minded; earns grace of God; few children; will have foes; gives "
                  "happiness to others",
        afflicted="no issues; invokes kshudra-devatas; evil-minded; leader of a gang of "
                  "deceitful persons; tale-bearer with a sting",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5112)),
    RuleRecord(
        id="H5.L.1a", house=5, signification="children", group="lord_in_house",
        kind="descriptive", condition=None,
        fortified=None,
        general="the 5th lord moderately good - mixed results will follow. TODO(predicate: "
                "the MIDDLE tier of Raman's benefic / moderating / malefic partition, named "
                "in this table's own closing disclaimer at HTJAH-I:5173-5175; no nature-scalar "
                "Condition exists)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5117)),
    RuleRecord(
        id="H5.L.2", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 2),
        fortified="beautiful wife and well-behaving children; gains from Government/King; "
                  "becomes learned and a good astrologer",
        afflicted="poor; loss of money via Government displeasure; cannot maintain family; "
                  "family troubles; becomes a priest in a Siva temple",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5119)),
    RuleRecord(
        id="H5.L.3", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 3),
        fortified="many good children and brothers",
        afflicted="loss of children; misunderstandings with brothers; continuous occupational "
                  "troubles; stingy, a tale-bearer",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5125)),
    RuleRecord(
        id="H5.L.4", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 4),
        fortified="a few sons (one lives by agriculture); mother lives long; "
                  "may advise a ruler or be his preceptor",
        # The slot welded TWO antecedents with different outcomes: "The lord, afflicted,
        # causes death of children" (5134) and "The lord, moderately strong, confers daughters
        # and no sons" (5134-5135). Under the binary branch both displayed together, telling
        # one reader that children die AND that daughters are born. Raman assigns them to
        # different tiers and states neither for a merely weak lord.
        afflicted="the 5th lord afflicted - death of children",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5129)),
    RuleRecord(
        id="H5.L.4a", house=5, signification="children", group="lord_in_house",
        kind="descriptive", condition=None,
        fortified=None,
        general="the 5th lord moderately strong - daughters and no sons. TODO(predicate: "
                "PARKED by research 2026-10-13 -- Raman prints no middle strength level "
                "(GBB-8:303 is one bar); his 'middling' is a tally of mixed testimony "
                "across Rasi and Navamsa, not a Shadbala band. Do NOT build a Shadbala band "
                "for it; see DOCTRINE_BACKLOG 'Middle and upper strength levels')",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5134)),
    RuleRecord(
        id="H5.L.5", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 5),
        fortified="number of sons; becomes great in his own line; expert in Mantra Shastra; "
                  "befriends the powerful; expert in mathematics or head of a religious institution",
        afflicted="children will die; will not keep his word; wavering mentality; cruel",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5137)),
    RuleRecord(
        id="H5.L.6", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 6),
        fortified="maternal uncle becomes famous; enmity with his own son",
        afflicted="no issues born; may adopt one from maternal uncle's line",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5143)),
    RuleRecord(
        id="H5.L.7", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 7),
        fortified="son lives abroad and attains distinction, wealth and fame; or many issues; "
                  "renowned, learned, prosperous, devoted to master, charming personality",
        afflicted="loss of children, one of whom dies abroad after attaining name and fame",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5147)),
    RuleRecord(
        id="H5.L.8", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 8),
        # "no specific benefit noted" was ENCODER EDITORIAL -- the phrase appears nowhere in
        # either volume. Cleared, NOT relocated, per the H10.L.1 precedent: moving unsourced
        # prose into `general` would launder it into a slot asserting Raman said it.
        # HTJAH-I:5153-5154 is four flat declaratives with no conditional clause anywhere, so
        # both poles are empty and the whole entry is the unconditioned reading. Every
        # strong-5th-lord chart was being shown the editorial line INSTEAD of Raman's only
        # reading for this placement.
        fortified=None,
        general="paternal property lost due to debts; extinction of the family; lung "
                "troubles; peevish, unhappy but not poor",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5153)),
    RuleRecord(
        id="H5.L.9", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 9),
        # No favourable opener exists: HTJAH-I:5156-5157 states these flatly and only then
        # introduces "If the lord is afflicted". Structurally identical to H9.L.6 (7340) and
        # H9.L.8 (7359), repaired on 2026-09-01 for exactly this reason. A weak-5th-lord chart
        # was shown ONLY "earns divine wrath" and never saw the base reading.
        fortified=None,
        general="becomes a teacher or preceptor; renovates ancient temples, wells, choultries "
                "and gardens; one of the sons attains distinction as an orator or author",
        afflicted="the 5th lord afflicted - earns divine wrath and consequent destruction of "
                  "fortune",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5156)),
    RuleRecord(
        id="H5.L.10", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 10),
        # The Sun-aspect clause (5162-5163) is a separate antecedent with its own outcome,
        # folded into the fortification arm -- so a strong 5th lord with no solar aspect
        # anywhere was told it may join the intelligence service.
        fortified="a Raja Yoga; landed property; goodwill of the rulers; constructs temples "
                  "and performs religious sacrifices; a son becomes a gem of the family",
        afflicted="faces the wrath of the rulers, and contrary results will happen",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5160)),
    RuleRecord(
        id="H5.L.10a", house=5, signification="children", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(5, 10), C.Aspects("Sun", "LORD_OF:5")),
        fortified=None,
        general="the 5th lord in the 10th aspected by the Sun - the native may join the "
                "intelligence department",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5162)),
    RuleRecord(
        id="H5.L.11", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 11),
        # HTJAH-I:5166-5167 carries no gate of any kind. `fortified` is KEPT alongside
        # `general` per the H1.L.10/11/12 precedent -- where Raman gives no conditioned
        # paragraph, both slots carry the sentence and `house_general_readings` suppresses the
        # duplicate. The defect was labelling an unconditioned reading strength-conditioned.
        general="benefits through sons; success in all undertakings; rich, learned, helpful; "
                "many sons; becomes an author",
        fortified="benefits through sons; success in all undertakings; rich, learned, helpful; "
                  "many sons; becomes an author",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5166)),
    RuleRecord(
        id="H5.L.12", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 12),
        # HTJAH-I:5169-5171, likewise ungated. Same shape and same precedent as H5.L.11.
        general="quest for the Ultimate Reality; non-attachment; spiritual; wanders; "
                "ultimately attains Moksha",
        fortified="quest for the Ultimate Reality; non-attachment; spiritual; wanders; "
                  "ultimately attains Moksha",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5169)),
)
