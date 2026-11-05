# The 33 opposite verdicts, read against the texts (2026-11-05)

**Worked from:** the merged study tool on main-local (bdcadef3): 365 scored conclusions on 235
charts, 238 agree, 94 one step apart, **33 opposite**. The older "35 of 389" figure predates the
31 October label re-review and no longer applies. The 33 are exactly the `real_errors` list in
`tests/fixtures/golden_accuracy_baseline.json`.

**How each row was read.** For every row: Raman's whole write-up of that chart, his conclusion,
every reason he gives, and what the engine counted (fired rules, pillars, the decide clause).
The 14 Notable Horoscopes rows were read from the cleaned NH text; the 19 How to Judge rows were
read on the owner's PC, the only place those books are. Book text is not quoted here because this
repository is public; every claim carries the book line so it can be checked. Each row was read
once, by one reader. No second engine-blind review has been done, so treat the classes as a
careful first reading, not a settled verdict.

**Classes.** A = the engine lacks a rule Raman states. B = an engine rule or gate has the wrong
condition, scope or reading. C = Raman's conclusion rests on biography, not on reasons in the
chart. D = an error in the golden record or the cast. E = Raman departs from his own stated rule.

## Result

| Primary class | Rows |
|---|---|
| B, engine condition or scope wrong | 19 |
| A, rule missing | 10 |
| E, Raman departs from his rule | 2 |
| C, biography | 1 |
| D, record error | 1 |

Four more rows carry a record defect as a secondary class (D), listed under "Golden records".

Most of the 33 are not missing doctrine. They are the judge weighing evidence in a way Raman
does not: Shadbala strength stands in for his "strong" or "weak" (he judges by placement,
association, aspect and Navamsa, HTJAH-II:221-222, HTJAH-I:486-487, 499); a weak pillar plus a
maraka afflicts with no malefic rule fired (h5_15, x75, h10_04, h11_08); rules for a sibling
matter create the contradiction (h6_04, x68, h9_12); and yogas Raman decides a matter by are
"noted" but never carry it (Roosevelt, C. R. Das, h10_04, h11_08).

## Fixes measured on the 365 rows

All figures are in-sample: these are the charts the engine was built on, and every hold-out is
already spent, so no fix below can be shown to generalise. A gain here only shows the engine
reads these charts more as Raman wrote them.

| Fix | Text | Result | Recommendation |
|---|---|---|---|
| **F2** make H12.C.G2 evaluable: Ketu in the 12th from the Karakamsa gives final emancipation | HTJAH-II:16527; applied by Raman in NH No. 46 (NH:10039-10041, Moon Atmakaraka, Ketu in the 12th Navamsa) | Ramana Maharshi moksha opposite → one step. No other scored row moves. Fires on 29 of 344 charts (8.4%, about 1 in 12, as chance predicts). | Ship (held behind `F2_KETU_FROM_KARAKAMSA`) |
| **F5** revive the Bhava rescue | HTJAH-I:503-505: a badly placed lord with good conjunctions and aspects on the house is not read as evil. The rescue required `bhava_bala_strong is True`, which has been None for every house since the Bhava Bala vote was withdrawn on 2026-10-23, so it could never fire. The dhana floor hit the same trap and was mended the same way (`is not False`). | 238 → 240 exact on its own: HTJAH-II Chart 217 (h11_08) gains opposite → agrees, and h11_17 gains one step → agrees. No scored row worse. Across all 19,665 sub-matter verdicts on Raman's charts it moves 254 (1.3%), all toward lenient. | Ship (held behind `F5_BHAVA_RESCUE_UNVOTED`) |
| F2 + F5 together | | **240/365 exact (65.8%), 334 within one step, 31 opposite**, from 238/332/33 | |
| F1 count H7.C.86 (7th lord with a node and a malefic aspect) for marital happiness, not only for the spouse | Refuted by its own text: HTJAH-II:1773-1778 and 447-449 speak of the spouse's character, not of unhappiness; unhappiness is HTJAH-II:376-377 | Fixes Marie Antoinette and Dalmia, breaks HTJAH-II Chart 12 and h7_04 | Do not ship |
| F3 read all 108 planet-in-house rules by Bhava | The project's locked "Bhava, not Rasi, for results" (HTJAH-I:973-974), but Raman also reckons by sign in many charts (HTJAH-I:6664-6668, HTJAH-II:8532-8536) | 236/93/36: one fixed, three broken | Do not ship |
| F4 read the 131 lord-in-house rules by Bhava | same | 233/97/35 | Do not ship |

F2 and F5 are in the code with their flags OFF, so the shipped engine and the ratchet are
unchanged until the owner decides.

## Decisions only the owner can make

1. **Ship F2 and F5?** Recommended. Both mend a rule to say what its own citation says; neither
   was tuned to the score.
2. **The fertility gate.** Raman's text gives Beeja for the man and Kshetra for the woman, and
   reads "both weak" only across the couple's two charts (HTJAH-I:5499-5501, 5507-5509,
   5517-5520). The gate tests both sphutas in one native's chart and treats both weak as denial.
   It decides four of the 33 (Victoria, h5_15, h5_16, NH No. 74, where the native is a woman and
   her Kshetra is strong). Routing by sex needs a sex field in the goldens and reopens the
   user-signed "O1" decision.
3. **Golden record corrections** (no score claimed; each needs sign-off because goldens are the
   answer key): HTJAH-II Chart 35 is a longevity verdict filed under manner of death; HTJAH-I
   Chart 121 cites the 6th-house section for an education verdict; HTJAH-II Chart 211 cites the
   elder-sibling passage for a spouse verdict (the verdict is at HTJAH-II:1625-1685, Chart 12,
   same native); NH No. 35's verdict words quote the intelligence sentence, not children; NH
   No. 74 prints the Moon at 34°17' (Taurus) while Raman's own text puts it in the 2nd, Aquarius,
   as the ephemeris does (changing it moves no verdict).
4. **Soft labels worth a second reader:** HTJAH-I Chart 31, h5_16, x73 (which reads as mixed), and
   NH No. 37 (loss of the first wife, then remarriage, which reads two-sided).

## The 33 rows

R = Raman, E = engine. Lines: NH = Notable Horoscopes, I = HTJAH-I, II = HTJAH-II.

| Row | R / E | Class | What Raman does, and what the engine misses | Lines |
|---|---|---|---|---|
| NH 22 Marie Antoinette, marital happiness | aff / fav | A | 7th lord with Rahu aspected by Mars, karaka with the debilitated Sun under Saturn's aspect. The node rule in the store is about the spouse's character, and no marital-happiness rule covers an afflicted 7th lord | NH:5864-5866, 5878-5880 |
| NH 27 Queen Victoria, children | fav / aff | E (B) | He names three malefic aspects on the 5th and still reads prolific, on the 5th lord's links and Jupiter's sthanabala. The gate's both-weak denial overrides | NH:6764-6770 |
| NH 35 Tagore, children | aff / fav | C (D) | Loss of three of five children is stated as fact, with no 5th-house reason. The verdict words quote another matter | NH:7896-7898 |
| NH 36 Vivekananda, learned profession | fav / aff | B | "Jupiter in Karmasthana": Jupiter is Bhava 10, sign 11, and Raman says Saturn is in the 9th house though in the 10th sign. Planet rules read the sign | NH:8155, 8197 |
| NH 37 Gaekwar, spouse | aff / fav | E | He weighs the afflictions against named relief and concludes one wife lost and a second marriage. Two-sided; the label is contestable | NH:8353-8359 |
| NH 40 H. G. Wells, marital happiness | aff / fav | A | Karaka with Saturn and Mandi, 7th lord with Ketu in the Navamsa, 7th lord from the Moon with Rahu in the 8th from the Moon | NH:8945-8963 |
| NH 42 C. R. Das, career | fav / aff | B | The neecha Sun has neechabhanga and is in the Lagna Bhava, giving leadership. The engine fires "10th lord in the 12th" by sign and calls the karaka weak | NH:9325-9332 |
| NH 46 Ramana Maharshi, moksha | fav / aff | A | Ketu in the 12th from the Karakamsa. The rule exists as an unfinished TODO; 12th-house poverty rules were counted instead. **F2 fixes it** | NH:10039-10041 |
| NH 47 Roosevelt, career | fav / aff | B | Vipareeta Rajayoga gave "the highest position", and Ketu in the 10th is well placed. The yoga is only noted, and Ketu's table entry counts against | NH:10141-10155, 10183-10196 |
| NH 62 Dalmia, marital happiness | aff / fav | A | 7th lord with Rahu, Moon in the 7th aspected by Mars, Venus with two malefics under Saturn's aspect | NH:12941-12945 |
| NH 64 Duke of Windsor, career | aff / fav | A (C) | 10th lord in the 8th from the 10th, Mars aspecting the 10th. No general 6/8/12-from-the-house rule was found in HTJAH-I | NH:13306-13309 |
| NH 73 poverty example, wealth | aff / fav | A | Debilitated Lagna and 2nd lord with Rahu; "the whole structure is rotten". No rule fires for it; the record also lacks Shadbala | NH:14755-14760, 14848-14875 |
| NH 74 Raja yoga example, children | fav / aff | B (A, D) | A woman with a strong Kshetra; Mars and Rahu defused by Mercury's constellation; Navamsa count gives seven. The gate denies on her weak Beeja | NH:14973-14980 |
| NH 74, marital happiness | fav / none | A (D) | Well-placed 7th lord, karaka with neechabhanga. No rule fires and the engine abstains | NH:14981-14985 |
| I Chart 31, self | aff / fav | B (A) | He calls the Lagna lord weak and hemmed; Shadbala says strong and clause 2 lifts | I:2218-2221 |
| I Chart 42, wealth | aff / fav | B | Saturn read in the 3rd house; the engine fires him in the 4th by sign | I:2794-2797 |
| I Chart 60, siblings | aff / fav | B (A) | Karaka and 3rd house afflicted, Jupiter-Ketu in Bhava | I:3807-3813 |
| I Chart 100, children | aff / fav | B | The 5th lord rule never takes its afflicted branch | I:5115 |
| I Chart 105, children | fav / aff | B | Clause 6 afflicts on a maraka alone; sphuta gate | I:503-505, 5517-5520 |
| I Chart 106, children | fav / aff | B | Navamsa, Saptamsa and sphuta steps Raman does not use here | I:5517-5520, 5929 |
| I Chart 112, chronic disease | aff / fav | B (A) | A sibling-matter rule; Navamsa lift on an affliction matter | I:6007-6008, 6062-6065 |
| I Chart 113, enemies and disease | aff / fav | B (A) | 6th lord rule on its benefic branch; clause 5 ignores a hard-afflicted lord | I:6055-6057, 6062-6065 |
| I Chart 121, education | aff / fav | A (D) | 4th lord with Saturn; no general line found, so hold; citation wrong | I:4887-4907 |
| I Chart 65, mother | aff / fav | A | Lord and karaka joined by the 3rd/6th lord | I:4472-4473 |
| I Chart 68, mother | aff / fav | B | A sibling benefic rule forces clause 2; the Moon-affliction rule is not decisive | I:4551-4556 |
| I Chart 73, mother | aff / fav | A (C) | No Saturn-on-Moon rule; the label leans on the death and reads as mixed | I:4646-4656 |
| I Chart 75, mother | fav / aff | B (D) | Clause 6 on a maraka alone; chart re-timed 48 minutes | I:503-505 |
| II Chart 35, death | fav / aff | D | A longevity verdict filed under manner of death | II:4707-4710 |
| II Chart 198, authority | fav / aff | B | Clause 6 on a maraka; yogas not routed | II:13518-13519, 13547-13549 |
| II Chart 210, elder siblings | aff / fav | B | Primary karaka Jupiter where the cited line favours Mars | II:14742-14745 |
| II Chart 211, spouse | fav / aff | B (D) | Papakartari arm decisive against his preponderance; citation wrong | II:353-356, 1673-1685 |
| II Chart 217, gains | fav / aff | B | Clause 6; the Bhava rescue cannot fire; Dhana Yoga not routed. **F5 fixes it** | I:503-505, II:15242-15245 |
| II Chart 96, father | aff / fav | B | Fortune rules create the contradiction; the Moon-led frame hides Jupiter | II:8569-8571 |

Per-row evidence (golden record, cast, decide clause, pillars, fired rules) is in `packets/`.
The packets with book text are on the owner's PC only.
