# Chara dasha: rulings from the texts (Q1–Q6)

Written 2026-10-24 on the owner's instruction "find answers in ancient texts", before any chara dasha code.
Every passage is quoted from the corpus (`data/knowledge_library/sources/`) with file and line number.

## Sources searched, in authority order
| rank | text | corpus | engine status |
|---|---|---|---|
| 1 | BPHS ch.46 (Chara Dasa, sl.155-167), ch.51 (rasi antardasas), ch.50 (effects) | `bphs/` (R. Santhanam, the only BPHS edition on disk) | ROOT |
| 2 | Jaimini Sutras, with B. Suryanarain Rao's notes | `jaimini_sutras/` | added as ALLIED (classical, citable only where BPHS is silent) |
| 3 | B. V. Raman, *Studies in Jaimini Astrology* | `studies_jaimini_raman/` | added as CORROBORATION (not citable by the engine) |
| — | K. N. Rao, Sanjay Rath | `advance_techniques_kn_rao/`, `crux_*_rath*` | not needed: the three above decide every question |

No second BPHS translation is on disk. The 46:4740-4835 example chart and table are lost to OCR in this
edition, so they cannot be recovered. Two of its numbers do survive in the prose (below), and they settle Q1.

Verdicts: **TEXT-SETTLED** means BPHS decides it. **CONVENTION** means BPHS is silent or ambiguous and the commentary and Raman decide it (it is labelled as such in code and prereg). **UNRESOLVED** means the sources disagree, so the rule is deferred.

## Q6: what "odd / even pada" means. TEXT-SETTLED
- BPHS-46:4660-4662: "every three signs from Aries etc. have four padas. For the odd (1,3) padas, the
  counting is done from Rasi onwards… For the even padas (2 & 4) this counting is done in the reverse order."
- The example applies it: Libra (sign 7) is "in an odd pada" (46:4781); "Aquarius is in even pada" and
  "Aries is in odd pada" (46:4785-4789).
- Raman agrees exactly. SJ ch.4:645-652, art.76-77: odd group = "Aries, Taurus, Gemini, Libra, Scorpio and
  Sagittarius"; even group = "Cancer, Leo, Virgo, Capricorn, Aquarius and Pisces".
- **Ruling:** savya (odd pada) = signs 1-3 and 7-9; apasavya (even pada) = 4-6 and 10-12. This applies both to
  the sequence (from the 9th sign) and to counting the years (from the dasa sign). Both existing repo
  implementations (app/raman_saab, app/core) get this wrong, since they use odd/even sign or movable/fixed sign.

## Sequence and repetition. TEXT-SETTLED
- BPHS-46:4733-4736 (sl.167): "If the sign in the ninth house from the Ascendant be in an odd pada, the counting
  should be from the sign in the Ascendant onwards. The counting would be in the reverse order if the pada be even."
- BPHS-46:4837: "After the expiry of these Dasas once, Aquarius will again become the starting point". The cycle
  repeats with the same years (no other rule is given). Raman art.78 (SJ ch.4:657) agrees.

## Q1: how the years are counted. TEXT-SETTLED by BPHS's own numbers
- The rule's wording is ambiguous. BPHS-46:4658-4659: "the number of years of Dasa is reckoned from the Rasi up to the
  house in which its lord is posited."
- BPHS's worked numbers decide it. "the Chara Dasa for Aries will be one year" (46:4789-4790), and "The Chara Dasa
  of Pisces is one year" (46:5037, the Yogardha example on the same chart).
  - Under an inclusive count, a 1-year dasa would need the lord in the sign itself. But a lord in its own sign gives
    12 years: BPHS-46:4703-4705 for the dual-lord case, and the Jaimini commentary (ch.9:752) for every sign.
  - So "1 year" is possible only as **count − 1, with the lord in the 2nd**. This is also how the commentary itself
    phrases it: "If he is in the second house he gives one year" (Jaimini ch.9:754).
  - Raman states the formula outright. SJ ch.4:679: "The Dasa period of a Rasi is equal to n−1 where n represents
    the distance… between the Rasi in question and the lord thereof". He has five worked cases (ch.4:675-720, 806-862).
- **Dissent, recorded:** the Jaimini commentator's own Scorpio example ("Kuja in Makara… 3rd house… gives 3 years",
  ch.9:758) uses the inclusive count, which contradicts his own "2nd gives one year" line two lines earlier. He also
  notes "Some say he gives two years" (ch.9:755).
- **Ruling:** years = n − 1, where n is the inclusive count in the pada direction of the dasa sign.
- **Lord in own sign (CONVENTION, all agree): 12 years.** BPHS states it only for Scorpio/Aquarius (46:4703-4705).
  The Jaimini commentary (ch.9:752) and Raman art.80 (SJ ch.4:734) state it for every sign, and it is forced anyway,
  since n − 1 = 0 otherwise.

## Q2: exaltation / debilitation ±1. CONVENTION (commentary and Raman agree)
- BPHS-46:4727-4730 is ambiguous in scope (it sits inside the Scorpio/Aquarius passage): "1 (one) should be added in
  the number of years in the case of sign with an exalted planet and 1 (one) should be deducted… with a planet in debilitation".
- The Jaimini commentary, ch.9:756-764, says it applies to every sign and to the LORD: "If the lord of the Rasi is in
  exaltation, he will add one more year… if he is in debilitation he takes away one year".
- Raman art.80, SJ ch.4:735-737: "If the Rasi lord is exalted… increased by one year. If… debilitated… diminished by one year."
- **Ruling:** every sign; the lord; applied to the n − 1 figure (Raman: "the Rasi Dasa period obtained as per
  article 79"), not to the own-sign 12. The nodes have no exaltation entry in this engine (`relationships.EXALTATION`),
  so they never adjust.

## Q3: the dual lords of Scorpio and Aquarius. TEXT-SETTLED on order; CONVENTION on the final tie-break
- Co-lords, BPHS-46:4669-4670: "Mars and Ketu are both lords of Scorpio. Similarly Saturn and Rahu are lords of Aquarius."
- **Both lords in the sign: 12 years.** BPHS-46:4703-4705; Jaimini ch.9; Raman art.82. All agree.
- **One lord in the sign and the other elsewhere: count to the other.** BPHS-46:4707-4710: "If one planet be in his own
  sign and the other in any other sign, the Dasa will be of the number of years counted from the above first sign to
  the other." Raman art.85 agrees (SJ ch.4:779, "ignore the former and prefer the latter").
  - **Dissent, recorded and overruled by root:** the Jaimini commentary (ch.9:771-775) says to take the one in his own
    house. BPHS wins.
- **Both lords elsewhere, in different signs: the stronger.** BPHS-46:4710-4724, Jaimini ch.9:780-797 and Raman art.86
  give the same chain:
  1. the lord with a planet;
  2. the one with more planets;
  3. the one in the stronger sign by nature, dual > fixed > movable.
- **Final tie-break (CONVENTION):** BPHS 46:4724-4725 reads "counting should be done up to the sign with bigger number".
  This is ambiguous. The Jaimini commentary (ch.9:797, "take that lord who gives the larger number of years") and Raman
  art.86 (SJ ch.4:796) both read it as the **larger number of years**. Ruling: larger years.
- **Exaltation override:** BPHS 46:4725-4726: "If one sign be occupied by a planet in exaltation, the counting should be
  done up to that sign only". Jaimini ch.9:800: "If one of them is in exaltation, he should be preferred". Ruling: if
  exactly one candidate lord is exalted, it is chosen over the chain. The nodes never qualify (see Q2).
- "Associated with a planet" = another graha in the same sign (BPHS's example, 46:4783: "Rahu is associated with a
  planet", i.e. Rahu with the Moon).

## Q4: antardasha order. UNRESOLVED, so DEFERRED
Three sources give three different orders:
- BPHS-51:541-544 (sl.6): "The Antardasas will start from the Dasa rasi or from the rasi 7th therefrom, whichever is
  stronger… onwards order if the Dasa rasi is odd, in the reverse order if it is even."
- BPHS-51:576-588 (sl.7-12): movable → the 12 in order; fixed → "every sixth rasi"; dual → "rasis in kendra to it, …
  the 5th… the 9th".
- Raman art.87 (SJ ch.4:952-970): the direction is set by the 9th from the dasa rasi, and the "first sub-period being
  that of the 2nd Rasi", the dasa rasi last.
- The Jaimini Sutras (pada-4 Su.8-10, lines 186-218) put BPHS's sl.7-12 pattern on the sequence of mahadashas, not
  antardashas.

The length is settled (1/12 of the dasa, BPHS-51:529-531; Raman art.88), but the order is not. **Antardashas are not
encoded.** The mahadasha level stands on its own. Phase 3J tests the MD level only.

## Q5: how a running sign activates a house. CONVENTION (Raman only), so it goes in the validation instrument, not the engine
- BPHS ch.50 judges a rasi dasa by its lord's strength (50:39-46) and does not define which house a dasa "activates".
- The Jaimini Sutras in the corpus give no rule.
- Raman, SJ ch.9:870-874 (art.159): "The nature of the results produced by a Rasi Dasa will pertain to the events of
  the Bhava which it happens to represent from Lagna or Atmakaraka or even Karakamsa."
- **Ruling:** the dasa sign activates house H when it IS the H-th sign from the Lagna (primary). A sensitivity arm uses
  "from Lagna OR from the Atmakaraka's sign OR from the Karakamsa", using the engine's `chara_karaka.atmakaraka` /
  `karakamsa` (BPHS-32/33).
- Because only a corroboration source supports it, it lives in `tools/validation/`, not in engine doctrine (the same
  split as Phase 3's lord-from-the-Moon factor).
- **Death events are excluded from Phase 3J.** The same Raman passage (SJ ch.9:864-883) assigns death, own and
  relatives', to Sthira / Niryana Shula Dasa or to separate articles, not to this bhava rule. Applying the bhava rule to
  death would be an invention.

## What is encoded, and what is deferred
Encoded in `app/parashara/primitives/chara_dasha.py`:
- the sequence and direction;
- the years (n − 1, own sign 12, ±1);
- the dual lords;
- cycle repetition.

Not encoded:
- antardashas (Q4);
- the BPHS-46 example chart (lost to OCR);
- any node exaltation.
