# Chara dasha: rulings from the texts (Q1–Q6)

Written 2026-10-24 on the owner's instruction "find answers in ancient texts", before any chara dasha code.
It was revised after a bphs-doctrine-reviewer pass (2 blocking, 6 revise; all applied, see "Review" at the end).
Every passage is quoted from the corpus (`data/knowledge_library/sources/`) with file and line number.

## Sources searched, in authority order
| rank | text | corpus | engine status |
|---|---|---|---|
| 1 | BPHS ch.46 (Chara Dasa, sl.155-167), ch.47 (node dignities), ch.51 (rasi antardasas), ch.50 (effects) | `bphs/` (R. Santhanam; the only edition on disk) | ROOT |
| 2 | Jaimini Sutras with B. Suryanarain Rao's notes | `jaimini_sutras/` | ALLIED (added; citable only where BPHS is silent) |
| 3 | B. V. Raman, *Studies in Jaimini Astrology* | `studies_jaimini_raman/` | CORROBORATION (added; not citable by the engine) |
| — | K. N. Rao, Sanjay Rath | `advance_techniques_kn_rao/`, `crux_*_rath*` | not needed |

The worked examples in BPHS ch.46 and ch.51 ("Example :" at 46:4740, "Notes :" at 51:601) are R. Santhanam's
editorial examples, not slokas. They carry the translator's authority, not Parashara's. The ch.46 example chart's
drawing is OCR-garbled. Only some of its placements can be read (see the Q1 section and `fidelity_ledger._chara_example_signs`).

Verdicts:
- **TEXT-SETTLED**: decided by BPHS (its slokas, or its translator's worked numbers, as labelled).
- **CONVENTION**: BPHS is silent or ambiguous, and the reading named is used and labelled.
- **UNRESOLVED / DEFERRED**: not encoded.

## Q6: "odd / even pada". TEXT-SETTLED
- BPHS-46:4660-4662: "every three signs from Aries etc. have four padas. For the odd (1,3) padas, the counting is done
  from Rasi onwards… For the even padas (2 & 4) this counting is done in the reverse order."
- The worked example applies it: Libra is "in an odd pada" (46:4781), "Aquarius is in even pada", "Aries is in odd
  pada" (46:4785-4789).
- Raman agrees (SJ ch.4:645-652, art.76-77).
- **Ruling:** savya = signs 1-3 and 7-9; apasavya = 4-6 and 10-12. It is used for both the sequence direction and the
  year count. Both existing repo chara dashas (`app/raman_saab`, `app/core`) use a different grouping.

## Sequence and repetition. TEXT-SETTLED (repetition years: inference)
- BPHS-46:4733-4736 (sl.167): "If the sign in the ninth house from the Ascendant be in an odd pada, the counting should
  be from the sign in the Ascendant onwards. The counting would be in the reverse order if the pada be even."
- BPHS-51:655 confirms the order on the example chart: after Aquarius, "The next rasi in the order of the Dasas is Pisces".
- BPHS-46:4837: "After the expiry of these Dasas once, Aquarius will again become the starting point". That the
  second round repeats **the same years** is an inference (no other rule is given), labelled as such.
- **Zero-year periods:** n = 2 with a debilitated lord gives 0 years. Such a sign has no length and is skipped. This
  is arithmetic, not doctrine.

## Q1: how the years are counted. TEXT-SETTLED (by the translator's worked number), and Raman agrees
- The sloka's wording is ambiguous. BPHS-46:4658-4659: "the number of years of Dasa is reckoned from the Rasi up to the
  house in which its lord is posited."
- A worked number decides it without relying on any convention:
  - The example chart puts Jupiter in the Lagna box: "Ascdt* / Mercury / • Jupiter / Venus" (46:4750-4753).
  - The ch.51 note on the same chart confirms the Lagna "is associated with benefics" (51:652).
  - Pisces counts in reverse (even pada), so Aquarius is n = 2 from it. The printed "The Chara Dasa of Pisces is one
    year" (46:5037) therefore holds only as **n − 1**. An inclusive count gives 2.
  - The independent ch.51 figure "The Dasa years are 8" for Aquarius (51:610) agrees with 46:4787.
- Raman states the formula outright (SJ ch.4:679, art.79: "equal to n−1 where n represents the distance… between the
  Rasi in question and the lord thereof") and works five cases. All five are reproduced (`test_chara_dasha.py`).
- **Dissent, recorded:** the Jaimini Sutras' translator counts inclusively throughout: Mesha to Simha = 5
  (ch.9:678-680), the 7th = 7 and the 3rd = 3 (ch.9:691-696), Mesha to Kataka 4 − 1 = 3 for debilitation (ch.9:762-765),
  Makara as the "12th from Kumbha" = 12 (ch.9:783). His "If he is in the second house he gives one year. Some say he
  gives two years" (ch.9:754-755) is the outlier. BPHS wins.
- **Ruling:** years = n − 1, where n is the inclusive count in the dasa sign's pada direction.

## Q1b: lord in its own sign = 12 years. CONVENTION (Raman's form)
- BPHS states 12 only for Scorpio/Aquarius with both lords in the sign (46:4703-4705).
- The Jaimini commentary says "If the lord of the Rasi is in his own house, the sign gives 12 years… If he is in the
  12th house the Rasi gives a similar period" (ch.9:752-754). That is its inclusive scheme. Under n − 1 the 12th gives 11.
- So the encoded form (own sign = 12, and the 12th = 11) is Raman's (SJ ch.4:734-735, art.80). It is a CONVENTION, and
  the code cites the commentary's own-sign line as its classical anchor. The 12th-house line is dissent.
- Under n − 1, own sign = 12 is forced anyway, since the count would otherwise give 0.
- Edge case: Mercury in Virgo (own sign and exalted) gives 12, with no +1 (Q2 applies only to the n − 1 figure).

## Q2: exaltation / debilitation ±1. CONVENTION
- BPHS-46:4727-4730 is ambiguous on two counts: scope (it sits in the dual-lord passage) and whether "a planet" means
  the lord or any planet. "1 (one) should be added… in the case of sign with an exalted planet and 1 (one) should be
  deducted… with a planet in debilitation".
- The Jaimini commentary (ch.9:756-765) applies it to every sign and to the LORD, on its inclusive figure.
- Raman (SJ ch.4:736-739, art.80) does the same, on the n − 1 figure ("obtained as per article 79").
- **Ruling:** every sign; the lord; added to or taken from the n − 1 figure.
- **Nodes:** BPHS-47:280-284 says "The sign of exaltation of Rahu is Taurus… of Ketu is Scorpio". The engine's general
  table omits the nodes, so `chara_dasha.NODE_EXALTATION` adds them for this rule (the nodes co-own Aquarius and
  Scorpio). BPHS gives no node debilitation, so the nodes never lose a year.

## Q3: the dual lords of Scorpio and Aquarius. TEXT-SETTLED except the last rung (CONVENTION)
- Co-lords, BPHS-46:4669-4670: "Mars and Ketu are both lords of Scorpio. Similarly Saturn and Rahu are lords of Aquarius."
- **Both lords in the sign: 12 years.** BPHS-46:4703-4705; Raman art.82; Jaimini ch.9.
- **One in the sign, the other elsewhere: count to the other.**
  - BPHS-46:4707-4710: "If one planet be in his own sign and the other in any other sign, the Dasa will be of the number
    of years counted from the above first sign to the other."
  - Raman art.85 agrees (SJ ch.4:779). The Jaimini commentary agrees at ch.9:770-771 ("If one of them is not there,
    then the presence of the other gives no years").
  - It contradicts itself at ch.9:773-784 ("take the planet in his own house"). Root wins.
- **Both elsewhere, in different signs (TEXT-SETTLED order):** BPHS-46:4710-4724 = Jaimini ch.9:786-797 = Raman art.86:
  1. the lord with a planet;
  2. the one with more planets;
  3. the one in the stronger sign by nature, dual > fixed > movable.
- **The last rung (CONVENTION), when all three tie:**
  1. **A lone exalted lord is preferred.** All three sources put exaltation last:
     - BPHS lists it after the tie-break (46:4725-4726, "If one sign be occupied by a planet in exaltation, the
       counting should be done up to that sign only");
     - Jaimini completes the chain first (ch.9:800, "If one of them is in exaltation, he should be preferred");
     - Raman limits it to the final tie (SJ ch.4:797-800).
     - The code applies it only at this rung, never over association. The first encoding put it first, and the review
       (blocking) corrected that.
     - Scope: BPHS says "a planet"; the commentary and Raman say the lord. The lord is used.
  2. **Then the larger number of years.** BPHS's "counting should be done up to the sign with bigger number"
     (46:4724-4725) is read as Jaimini ch.9:797 ("the larger number of years") and Raman art.86 read it.
- "Associated" = another graha in the same sign. BPHS 46:4783 ("Rahu is associated with a planet", here the Moon).
  `cast()` puts exactly the nine grahas in `longitudes`.

## Q4: antardasha order. ENCODED (owner decision 2026-10-24: "go with ur recommendation" = BPHS-51 sl.7-12)
- **Length (TEXT-SETTLED):** 1/12 of the dasa. BPHS-51:529-531: "dividing the Dasa years by 12".
- **Order (TEXT-SETTLED by sl.7-12, 51:576-588):** movable → the twelve in order; fixed → "every sixth rasi"; dual →
  "rasis in kendra to it, rasis in kendra to the 5th from it and rasis in kendra to the 9th from it". Direction: "onwards,
  if the Dasa asraya rasi be an odd one, and in the reverse order if it be an even one" (51:587-588).
- The translator's worked note on the same chart settles the two points sl.7-12 leaves open.
  - **The Paka (dasa asraya) rasi is the dasa rasi itself:** "Here Aquarius is the first Dasaprada rasi. There it will
    be both Paka and Bhoga rasi" (51:650-651); "Here Pisces is Paka rasi" (51:663).
  - **Every order starts from the dasa rasi, and odd/even is the SIGN's parity, not the pada:** for fixed and dual
    the verse says so ("start from it" 51:580-581; "the first Antardasa will belong to it" 51:582-583). For
    **movable** the verse is silent, so starting at the dasa rasi is a CONVENTION: the translator's "including Aries"
    (51:670), plus analogy with fixed and dual. This is where sl.6's 7th option is least ruled out. Aquarius (an odd
    sign in an even pada, run onwards) is what proves sign parity rather than pada.
    - "Aquarius is a fixed and odd rasi. Therefore, starting from Aquarius there will be in onwards the Antardasa of
      every sixth Rasi" (51:602-604), and the printed table gives all twelve (51:613-648);
    - Pisces "the first Antardasa will be of Pisces itself. Then in the reverse order… Sagittarius, Virgo and
      Gemini… Scorpio, Leo, Taurus and Aquarius… Cancer, Aries, Capricorn and Libra" (51:655-663);
    - "In the Dasa of Aries there will be Antardasas of the 12 rasis (including Aries) in onwards order as Aries is
      Moveable and odd sign" (51:669-671).
  - These three orders are fidelity-ledger rows, reproduced exactly. They depend only on the sign, not on placements.
- **Recorded dissent, not encoded:**
  - BPHS-51 sl.6 (51:541-545): "The Antardasas will start from the Dasa rasi or from the rasi 7th therefrom,
    whichever is stronger" [OCR normalised: "front", ",7th"]. sl.6 agrees with sl.7-12 on direction and differs only on the start sign. The worked note never takes the 7th.
  - Raman art.87 (SJ ch.4:952-971): a straight sequence for every modality, from the 2nd rasi and ending with the
    dasa rasi, with the direction set by the 9th from the dasa rasi.
  - The Jaimini Sutras pada-4 Su.8-10 apply the sl.7-12 pattern to the mahadashas.
- Paka/Bhoga *effects* (51:588-599) are a reading rule, not timing, so they are not encoded.

## Q5: how a running sign activates a house. CONVENTION (Raman only), so it lives in the validation instrument
- BPHS ch.50 judges a rasi dasa by its lord's strength (50:39-46) and defines no house-activation rule. The Jaimini
  Sutras on disk give none either.
- Raman, SJ ch.9:870-874 (art.159): "The nature of the results produced by a Rasi Dasa will pertain to the events of the
  Bhava which it happens to represent from Lagna or Atmakaraka or even Karakamsa."
- **Ruling:**
  - The dasa sign activates house H when it is the H-th sign from the Lagna (primary).
  - Sensitivity arm: from the Lagna OR the Atmakaraka's sign OR the Karakamsa (engine `chara_karaka`, BPHS-32/33).
  - It sits in `tools/validation/`, not in engine doctrine.
- **Death events are excluded from Phase 3J.** SJ ch.9:864-883 assigns death (the native's and relatives') to Sthira /
  Niryana Shula Dasa or to separate articles, not to this bhava rule.

## Encoded / deferred
Encoded in `app/parashara/primitives/chara_dasha.py`:
- pada, sequence, repetition;
- years (n − 1; own sign 12; ±1, with node exaltation);
- dual lords.

The fidelity ledger carries the three example rows that are independent of the rule they test: Aquarius takes Rahu;
Pisces = 1; the sequence onwards from Aquarius. The Aries = 1 and Aquarius = 8 checks need the back-derived Mars and
Rahu signs, so they are not ledger rows.

Also encoded: antardashas (Q4, sl.7-12), with three ledger rows.

Deferred:
- node debilitation (not stated in BPHS-47).

## Review of the antardashas (bphs-doctrine-reviewer, 2026-10-24, second pass)
VALIDATED, nothing blocking. All three printed orders reproduce. Citation-range fixes were applied, and the movable start was relabelled CONVENTION.

## Review (bphs-doctrine-reviewer, 2026-10-24)
**Confirmed:** pada, sequence, dual-lord in/out rules, association, the zero-year skip.

**Applied:**
- Exaltation moved to the last rung (blocking).
- Ledger relabelled, and back-derived rows dropped (blocking).
- Q1 re-argued from the Jupiter-in-Lagna figure.
- Own-sign 12 attributed to Raman's form.
- Node exaltation encoded from BPHS-47.
- Q4 rationale rewritten around BPHS-51:601-660.
- Repetition years marked as an inference.
- The zero-year skip documented.
