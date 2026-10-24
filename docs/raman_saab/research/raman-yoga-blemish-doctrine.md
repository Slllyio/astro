# Raman on "a good yoga with a small blemish attached": what he actually does

Research note for the Raman-fidelity engine. Date: 2026-10-24.
Question: *a horoscope has a positive thing through a combination (yoga), but one small negative
thing is attached to it. How does Raman deal with that, so we can code it?*

**Scope and method.** Sources were Raman's printed books only, under
`data/knowledge_library/sources/`. No engine code, tests or private data were read.

| Abbrev | File | Notes |
|---|---|---|
| **HJ** | `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md` | HTJAH Vol I. The same file carries Vol II from about line 7865. Vol II passages are cited by this file's line numbers. The same text is in `how_to_judge_horoscope_raman2/…` at other line numbers (for example HJ 9359 = HJ2 2590, HJ 11893 = HJ2 6113). |
| **NH** | `notable_horoscopes_raman/chapter_001_full-text-unsplit.md` | Notable Horoscopes |
| **3HC** | `three_hundred_combinations_complete/chapter_001_full-text-unsplit.md` | Three Hundred Important Combinations (OCR has noise; quotes are cleaned only of obvious OCR letter errors) |
| **HPA** | `hindu_predictive_astrology_raman/chapter_0NN_*.md` | Hindu Predictive Astrology |

The search used keyword sweeps for: blemish, marred, spoil, neutralis, counteract, cancel, bhanga,
mitigat, relief, compensat, offset, counterbalanc, preponderan, "on the whole", "net result",
"evil is", "but for", partially, "more than", defunct, infructuous, lower plane, transformed and
others. Every hit was then read in context. **47 cases** are recorded below: 33 worked-chart
judgments and 14 general or doctrinal statements. A case can show more than one mechanism.

Verdict labels: **FAV** = favourable; **FAV-Q** = favourable with a stated qualification;
**MIX** = mixed or neutral; **AFF** = afflicted.

---

## 1. The short answer (for coding)

Raman almost never lets one small malefic touch **cancel** a strong yoga. When a yoga carries a
blemish, he does one or more of the following:

1. **Keeps the yoga and sends the blemish somewhere else.** The blemish lands on a different
   matter or a sub-matter (accidents, children, the spouse, the father's longevity). It does not
   lower the yoga's own verdict. His clearest statement is Truman, NH 10921-10926: *"due allowance
   must be made to the evil lordships of some of these planets causing the various yogas, but their
   inherent capacity to confer the blessings of the yoga are in no way affected or lessened, though
   the evil due to lordship could manifest in terms of accidents, etc."*
2. **Weighs it by strength.** The yoga's results are scaled by the strength of the planets that
   form it. 3HC gives an explicit +1/-1 unit procedure. Its key clause is that negative units do
   **not** turn a beneficial yoga into an evil one: *"no evil results will be given by him in regard
   to a beneficial yoga if the negative units predominate"* (3HC 877-888).
3. **Lets a benefic tempering factor neutralise the blemish**, usually Jupiter's aspect or
   association. This works only if the rescuing benefic is itself unblemished (Hitler, Aurangzeb).
4. **Neutralises the blemish through the afflicter's own condition**: it is the dispositor, it sits
   in a friendly nakshatra, it is a functional benefic, it is in a bhava-sandhi, or the two planets
   are far apart in degrees.
5. **Moves the blemish into time**: a delay, a bad half of a dasa, a bad sub-period, or "set right
   in appropriate periods".
6. **Lowers the plane** of the yoga. The yoga still fires, in a degraded or redirected form
   (Kesari "manifested in its lower plane"; Rajayogas "transformed into Parivraja Yogas").
7. **Cancels the yoga (bhanga / defunct / infructuous) only under heavy or named conditions.** These
   are: the yoga falls in a dusthana (12th or 6th); "all the evil forces have been focussed on it";
   the yoga planet is debilitated with no cancellation and also in a Dainya exchange; a named
   Raja-yoga-bhanga combination is present; or a whole-chart yoga such as Kemadruma or Kalasarpa,
   which has its own cancellation rules. Even then Raman warns: *"the mere debilitation of the Sun
   cannot destroy all the Raja Yogas"* (3HC 10264-10267).

For the engine, a yoga-with-blemish should usually resolve to **FAV-Q**. That means the yoga's
verdict stands and the blemish appears as a separate qualification, routed to its own matter or
period. The verdict should be **AFF** only when one of the cancellation conditions in §4 is met.

---

## 2. Case table

### 2A. Worked chart judgments (NH, HTJAH)

| # | Source:line | Chart / matter | Positive factor | Blemish | Raman's final call | What decided it | Mechanism |
|---|---|---|---|---|---|---|---|
| 1 | NH 10918-10926 | Truman, Rajayogas | 9/10 exchange, Jupiter exalted in 10th, Mars neechabhanga in 10th | Evil lordships of the yoga-forming planets | **FAV** (yoga intact). Blemish goes to "accidents, etc." | Lordship evil does not touch the yoga's "inherent capacity" | M3, M7 |
| 2 | NH 11333-11343 | Rajendra Prasad, Adhi Yoga | "Adhi Yoga is very powerfully marked" (Venus and Mercury 6/8 from Moon) | Mars in the 8th from Moon | **FAV-Q** | Mars "merely denotes liability to accidents and violence in the course of his own sub-period". Scope also limited because Venus could act "only as a sub-lord" | M3, M4 |
| 3 | NH 11330-11332 | Rajendra Prasad, Sun-Saturn 6/8 | (general) | Shashtashtaka Sun-Saturn | Struggle "unless relief is given by a powerful benefic" | A conditional rule: benefic relief is the test | M1 |
| 4 | NH 2223-2226 | Sankara, Moon | Jupiter aspects the Moon | Saturn and Mars aspect the Moon | **FAV-Q**: a "spirit of compromise" | "there is also the neutralising effect of Jupiter's aspect". The blemish is softened and still shows as character | M1, M5 |
| 5 | NH 5135-5141 | Shivaji, the whole chart | Many Rajayogas, Adhi Yoga | Mars-Rahu association | **FAV**: "fundamentally, the horoscope is a constructive one" | Planets "nearly 16° apart", different bhavas, and "even the slight stigma, if any … is more than compensated by the powerful aspect of Jupiter" | M1, M7 |
| 6 | NH 5154-5158 | Shivaji, the tripod (Lagna, Sun, Moon) | Lagna and Sun unafflicted | Moon aspected by Mars | **FAV** | "but for the Moon being aspected by Mars, which indicates mental sharpness". The blemish is turned into a trait | M5 |
| 7 | NH 4962-4967 | Shivaji, education | Jupiter (Gnanakaraka) aspects the 4th lord | 4th house in Papakarthari | **MIX**: unlettered, yet "more than compensated" by mastery of the epics | The blemish shows on formal schooling; the benefic gives the result through another channel | M3, M1 |
| 8 | NH 4978-4985 | Shivaji, children | Adhi Yoga; 5th lord "doubtless well placed" | 5th has Ketu and the aspects of Mars and Saturn | **FAV-Q**: "had five children but was not very happy" | Number given by the lord; happiness taken by the house's affliction | M3 |
| 9 | NH 3301-3309 | Chengiz Khan, Yuga Yoga (an evil yoga) | "formidable Rajayogas" | Yuga Yoga (irreligion, childlessness) | **FAV**: evil yoga "fully neutralised" | The yoga refers to the 3rd and 4th houses, and stronger Rajayogas are present | M2, M6 |
| 10 | NH 7193-7200 | Tilak, Gajakesari Rajayoga | Powerful Gajakesari plus Lagna and 9th lords | Rahu's association and Saturn's aspect | **FAV-Q**: patriotism and pride shown, but "the actual enjoyment of the yoga results is denied. But for this affliction he might have wielded power" | The affliction blocks the material fruit, not the character fruit | M5 |
| 11 | NH 7262-7269 | Tilak, Guru-Chandala | Jupiter (religion) | Jupiter-Rahu conjunction | **FAV**: "the yoga stands neutralised" | Rahu is in Mercury's nakshatra and "removed from Jupiter by nearly 10°" | M7, M6 |
| 12 | NH 7269-7271 | Tilak, overall | Rajayogas; Lagna and its lord fortified | Arishta (suffering) yogas | **MIX**: "Arishta yogas for suffering evenly balanced with Rajayogas" | Both poles delivered: suffering and stainless purity | M2 |
| 13 | NH 12169-12177 | Hitler, Kesari and Mahabhagya | Kesari (Moon-Jupiter), Mahabhagya | Ketu's contact; afflicted luminaries | **FAV-Q / degraded**: "Kesari has manifested in its lower plane. It made Hitler a ruler but … an object of hatred" | The yoga still fires, but in its lower form | M5 |
| 14 | NH 12290-12294 | Hitler, 7th house | Jupiter aspects the afflicted 7th | Jupiter is a "Chandala-Guru having become incendiary by association with Ketu" | **AFF** | The rescuing benefic is itself blemished, so the relief fails | M1 (failure) |
| 15 | NH 4643-4648 | Aurangzeb, Lagna | Jupiter almost conjunct the Lagna | Mars and Saturn aspect the Lagna | **AFF**: Jupiter "could have neutralised the affliction … but he actually occupies the constellation of Rahu" | The rescuer's nakshatra lord spoils it | M1 (failure), M7 |
| 16 | NH 12072-12081 | Swami Sivananda (NH No. 57), Raja yogas | Gajakesari, Amala and other yogas | Rahu and Saturn in Lagna | **Redirected**: "the Rajayogas have become transformed into Parivraja Yogas" | The blemish changes the kind of yoga, not its strength | M5 |
| 17 | NH 8155-8160 | Vivekananda, Saturn period | Saturn has caused Parivraja Yoga | Saturn as 2nd lord brings riches and distraction | **FAV** (spiritual) | The Parivraja Yoga let him put up "stout resistance against these distractions" | M5 |
| 18 | NH 5683-5689, 5736-5748 | Tippu Sultan, Rajayoga | "very powerful Rajayoga" from the 9th, 10th, 2nd and 5th lords | The yoga falls in the 12th; Mercury combust and "in the grip of Rahu" | **AFF**: "caused the disappearance of all the indications of the combined yoga" | Dusthana placement of the whole yoga, plus combustion and an eclipse | M6 |
| 19 | HJ 15911-15941 | Tippu (Chart 202), the same yoga in HTJAH-II | Sun-Mercury Dharma-Karmadhipa yoga | Mercury combust | **FAV-Q**: combustion "greatly minimised resulting in a distinct Raja-Yoga. But as the Raja-Yoga occurs in the 12th … he could not enjoy it fully" | Jupiter's aspect on combust Mercury cancels the combustion. The 12th-house placement limits enjoyment and shapes the manner of the end | M1, M6 |
| 20 | HJ 15950-15976, 15993-15997 | Napoleon (Chart 203) | "quite a number of Raja-Yogas" | Raja-yogas "loosely knit"; Mercury's 12th lordship given to Saturn | **FAV then fall**: "a powerful Raj a-Yoga delicately balanced", "the very seeds of destruction" | The rise was delivered; the blemish governs how long it lasted and the collapse, through dasas | M4, M5 |
| 21 | HJ 16107-16112 | Indira Gandhi (Chart 206) | Three parivartanas, Rajayogas | "latent seeds for Rajabhanga": Saturn's aspect on the 10th; Saturn-Venus periods | **FAV with a timed bhanga**: lost power in Saturn-Venus, then returned | "if the Raja-Yoga is powerful enough, the bhanga (loss of power) will be set right in appropriate Periods" | M4 |
| 22 | HJ 16146-16151 | Bhutto (Chart 207) | Powerful Raja-yoga, Ruchaka, Adhi | Yoga occurs in the 6th; the nodes eclipse it | **FAV then ousted**: "must suffer bhanga" | Dusthana placement of the yoga, plus nodal eclipse; it acts in the Moon bhukti | M6, M4 |
| 23 | HJ 16063-16078 | Nixon (Chart 205) | Four-planet Raja-yoga in the 5th | Saturn in the 10th; the yoga falls 12th from the Moon | **FAV then fall**: Saturn in the 10th "confers initial success, it also gives defeat and humiliation" | The blemish shows as a later reversal, timed by the dasa | M4 |
| 24 | HJ 16022-16027 | Mussolini (Chart 204) | Saturn is yogakaraka from the Moon | Saturn aspects the 10th lord Sun | **FAV then AFF**: "good results in the first half … very unfavourable results" in the second | The same planet is split across halves of its dasa | M4 |
| 25 | NH 15255-15268 | Farouk, Raja yoga | Saturn as yogakaraka conferred Raja Yoga | Saturn in the 2nd half of Leo; Mercury in Mars's nakshatra | **FAV-Q**: first half of Saturn dasa popular, second "a bed of thorns" but "did not get dethroned"; the fall came in Mercury dasa, Mars bhukti | The yoga is protected while its own dasa runs; the blemish acts in the afflicted planet's sub-period | M4 |
| 26 | NH 15200-15203 | Farouk, Hamsa | Hamsa (Jupiter exalted in the 10th) | Jupiter neecha in Navamsa | **FAV-Q**: "Hamsa Yoga has lost some of its strength" | A Navamsa weakness reduces the yoga; it does not cancel it | M2 |
| 27 | NH 12493-12500 | Nehru | "strength par excellence of Lagna and its lord", Malavya etc. | Papakarthari on the Lagna and its lord | **FAV-Q**: "preventing their early expression" | Pure delay | M4 |
| 28 | NH 14293-14304 | Golwalkar, Chandra-Mangala and Sasa | Chandra-Mangala; Sasa (Saturn in own house, kendra) | Leo with Mars as Netrakaraka; Saturn a natural malefic | **FAV-Q**: eye trouble but "no permanent eye trouble"; Sasa's evil "minimised considerably" | 12th lord unafflicted; Jupiter associates with Saturn; the yoga refers to the 6th from Chandra Lagna | M3, M1 |
| 29 | NH 14544-14548 | Golwalkar, Mercury-Saturn | Mercury tempers the effect | Saturn conjunction (slander, imprisonment) | **FAV-Q**: "the evil is considerably lessened because of the sign being Aquarius Saturn's Moolatrikona" | The afflicter's sign dignity | M7 |
| 30 | NH 11256-11259 | Rajendra Prasad (NH No. 53), Lagna | Jupiter aspects strongly | Mars-Mercury in Lagna (rashness) | **FAV**: "the evil is considerably tempered" into discrimination | Benefic aspect | M1, M5 |
| 31 | NH 13746-13752 / HJ 3943-3945 | NH No. 67 "Example for Dhana Yoga" = HJ Chart 63, mind | Moon-Jupiter association | "partially blemished by Saturn's aspect" | **FAV**: "of very great importance"; "Jupiter restores the equilibrium" | Benefic association outweighs a partial blemish | M1 |
| 32 | NH 9979-9983 | Ramana Maharshi (NH No. 46), 7th | Brahmacharya theme | Mars, 7th lord in the 7th | **FAV**: "What little mischief Mars … could do has been offset by his occupying the constellation of Ketu" | The afflicter's nakshatra | M7 |
| 33 | NH 4145-4150 | Akbar, Rajayoga | Saturn and Venus Rajayoga | Jupiter a temporal malefic (3rd and 6th lord) | **FAV**: Jupiter "rendered harmless owing to his disposition in a Bhava sandhi" | The afflicter has no residential strength | M7 |
| 34 | NH 4238-4243 | Akbar, Sasa, Malavya, Ruchaka | Three Mahapurusha yogas | none: "absence of mutual associations or aspects between Rahu and Mars, Rahu and Saturn and Mars and Saturn" | **FAV**: the results "seem to have fully manifested" | Control case: full manifestation needs freedom from malefic mutual contacts | (control) |
| 35 | NH 11144-11154 | Mysore Maharaja, overall | Many virtues; Sun-Saturn in the 11th "doubtless a good combination" | The Sun and Saturn are enemies ruling the 2nd and 7th; Saturn aspects Lagna and Venus | **FAV-Q**: domestic life "quite miserable", but "Leaving due margin for some of these evil combinations … the horoscope has several virtues" | The overall verdict stands; the blemish goes to the family and spouse sub-matter | M3, M2 |
| 36 | NH 11053-11064 | Maharaja (another), Dhana and Raja yogas | "powerful Dhana yogas", several Rajayogas | 5th lord with Mandi; 5th aspected by three malefics | **FAV-Q**: "rendered the native issueless. In spite of the wealth …" | The blemish is confined to the 5th-house matter | M3 |
| 37 | NH 8346-8360 | Gaekwar of Baroda | Immense wealth and power; Venus exalted | 5th lord afflicted (children died); Venus aspected by Saturn | **FAV-Q**: wealth and power kept; children lost; "lost his first wife and had to marry a second" | For marriage, "the relief of the evil" (7th in Navamsa free, Jupiter's aspect, Venus exalted) turned denial into loss and remarriage | M3, M1 |
| 38 | NH 5480-5497 | Goethe | Sunapha, Shankha, Samrajya yoga ("equal to a king") | "5th house is completely spoiled when viewed from Chandra Lagna" | **FAV-Q**: greatness kept; his only son died | The blemish is confined to the 5th | M3 |
| 39 | NH 7885-7892 | Tagore | Jupiter exalted in the 5th ("intellectual giant"); Sun exalted | Sun in Navamsa with Rahu and Venus | **FAV-Q**: "He should have been actively associated with day-to-day politics but for" this | One sub-expression of the yoga (politics) is removed | M3 |
| 40 | NH 14157-14163 | Suddhananda Bharathi | Mars yogakaraka in Lagna | Association with Ketu | **FAV redirected**: "not desirable for political success. But it gives him a real sense of political values" | The blemish redirects the yoga's expression | M5 |
| 41 | NH 6559-6566 | Karl Marx, 10th | Saturn glorified in Lagna | 10th lord Mars neecha, "he has not obtained neechabhanga", in parivartana with the 6th lord = Dainya | **AFF**: "The 10th house is rendered null and void … of absolutely no practical importance" | Debility with no cancellation plus a Dainya exchange | M6 |
| 42 | NH 14845-14877 | "An Example for Poverty" | Moon in the 9th; 2nd lord neechabhanga; six planets in the 10th | "the whole structure is rotten": mutual aspects of all malefics; Rekha; strongest planet afflicted | **AFF**: "whilst it should have made the subject a millionaire it has been so spoiled …" | Many blemishes converging, not one | M6 |
| 43 | NH 13306-13318 | Duke of Windsor, 10th | "potentiality of the 10th house which would have made him a great monarch" | 10th lord in the 8th from the 10th; 10th aspected by Mars; Rekha-like concentration | **AFF**: "completely shattered"; the bhava "becomes almost defunct" | Malefics concentrated on one bhava | M6 |
| 44 | NH 12981-12985 | Ramakrishna Dalmia (NH No. 62) | Dhana and Rajayogas; Hamsa in Navamsa | Jupiter's kendra lordship, association with Rahu, Karthari by the 6th and 12th lords | **FAV-Q**: success, but Jupiter "could not save the native from suffering incarceration" | Jupiter's blemishes take away only his protective role | M3 |
| 45 | HJ 12969-12976 | Chart 86 (b. 1857 London, royal birth), 9th / father | Sun exalted with Vargottama Jupiter in the 9th; 9th lord in a kendra | Papakartari to the 9th house, its lord and karaka | **Split**: "native's father could enjoy Raja-Yoga results but his longevity was curtailed" | Status goes to the strong factors; longevity goes to the afflicted ones | M3 |
| 46 | HJ 9143-9148 | Chart 23 (female), 7th | 7th lord Jupiter strongly placed | Exchange with the 5th lord; heavy affliction to the 8th from the Moon (Vaidhavya) | **Split**: "The strength of the 7th lord gave a good husband and did not deny marriage. But the several afflictions …" brought widowhood in a year | Strength decides whether the event happens; the afflictions decide how long it lasts | M3 |
| 47 | HJ 8862-8871 | Chart 12, 7th | Aspect of the benefics Jupiter and Venus | Mars aspects the 7th (ruler of malefic bhavas) | **FAV**: "There is a preponderance of benefice influences … his maleficence is kept in check by the aspect of 9th lord neechabhanga Saturn. The native has a happy married life" | Preponderance plus a check on the afflicter | M2, M1 |

### 2B. Additional HTJAH house-level weighings (same machinery, not strictly "yoga")

These are listed because they show Raman's weighing rule on a single bhava. They are not counted
in the 47 above.

- HJ 4669-4678 (Chart 74): Moon exalted "but in association with Ketu and Mars. This is
  counterbalanced by Jupiter's aspect … All the three elements are feebly blemished." Mother lived
  until he was 46. **M1.**
- HJ 4686-4695 (Chart 75): Navamsa affliction "negligible as fourth lord Mars aspects the fourth";
  "moderate affliction … in Navamsha is more than counterbalanced by his strong disposition in
  Rashi" → "quite strong". **Rasi strength outweighs a Navamsa blemish (M2).**
- HJ 4552-4561 (Chart 68): the reverse case. A benefic aspect on the Matrukaraka "is more than
  counterbalanced by the combined aspect of two first-rate malefic". Raman adds that Saturn's aspect
  as 4th lord "could have been construed as beneficial but for the fact Saturn happens to be a
  natural malefic". **Natural vs functional roles are balanced against each other (M8).**
- HJ 3788-3790, 3815-3817, 3854-3855: "Though the Karaka Mars is well disposed … ruler of the third
  becoming combust … stands against his having any brothers"; "Though the third house is somewhat
  favourable, as the lord cum the Karaka is severely afflicted, the subject has no brothers." **For
  "living" significations, an afflicted lord or karaka outweighs a favourable house.**
- HJ 4485-4486, 4584-4586, 4619-4621, 4656-4658: fourth house "moderately strong, but the lord and
  the Karaka are considerably afflicted. Hence the native lost his mother very early." Same rule.
- HJ 4762-4764 (Vidya): Jupiter "well fortified but for his ownership of the 8th and 11th, which
  may be ignored for purposes of assessing VidyaBhava". **An evil lordship is ignored for a
  karaka-specific matter (M7).**
- HJ 5704-5710 (Chart 95): "The 5th house and the 5th lord are rendered neutral by the almost equal
  distribution of benefice and malefic influences." **An explicit MIX verdict when the testimonies
  are equal (M2).**
- HJ 5874-5880 (Chart 103): Ketu in the 5th aspected by Mars, "in the absence of any relief … is
  formidable", BUT "as 5th lord Saturn is aspected by Jupiter and PutraKaraka Jupiter is himself
  free from affliction, birth of children is not denied." **A house blemish is outvoted by a sound
  lord and karaka (M3).**
- HJ 5839-5842 (Chart 101): the lord aspects the 5th → "birth of issue is denoted. But as the 5th
  house is afflicted and the 5th lord almost weak, their survival is not shown." **Split between the
  event happening and the issue surviving (M3).**
- HJ 7092-7099 (Chart 125, the long synthesis): a Rasi testimony and a Navamsa "redeeming feature"
  cancel → "the balanced position seen in Rashi is maintained … while the native will have a number
  of children, the family will not be large." **MIX expressed as a quantity (M3).**
- HJ 7158-7162 (Chart 125): Saturn dasa "will not be entirely trouble-free … Even with regard to
  Saturn, there are redeeming factors … His debilitation is more than relieved by his being
  retrograde." **M7.**
- HJ 16722-16726 (Chart 212): "Saturn's influence as a malefic lord on the 11th house must give a
  limited number of elder brothers. The aspect of the Sun on the 11th house prevents denial."
  **The blemish limits quantity; the benefic prevents denial (M3).**
- HJ 13219-13223 (Vol II Chart 94, 9th): "The aspect of Mars, even if malefic, is not really so harmful as
  being the lord of the sign occupied by 9th lord it only strengthens the 9th lord." **An afflicter
  that is also the dispositor (M7).**
- HJ 11729-11733: Venus "would seem afflicted by Rahu but both planets occupy a Venusian
  constellation which is ruled by Lagna lord … has conferred the full span of life." **M7.**
- HJ 11890-11896: "Mars is debilitated in Lagna but this is offset by his occupation of the asterism
  of the 8th lord." **M7.**
- HJ 18413-18418: Saturn's aspect on the 7th "has a delaying effect but since he happens to be a
  functional benefice and his sign dispositor Mercury is exalted, he cannot push the event too far
  ahead." **A blemish expressed as a bounded delay (M4, M7).**
- HJ 1820-1825 (Vol I Chart 12): Subhakarthari in Rasi, Papakarthari in Navamsa → "The Lagna therefore is
  fairly strong on the whole." **M2.**
- HJ 13137-13147 (Charts 90 / 91): papakartari on the karaka Sun in Chart 91 is outweighed by
  "Kendra with the 9th lord" and the 9th-lord's nakshatra. The father lived until the native was 24,
  against 11 in Chart 90 where the Sun is "debilitated with no relief". **Relief changes the timing,
  not whether the loss happens (M4).**

### 2C. General and doctrinal statements

| # | Source:line | Statement (verbatim, short) | What it codifies |
|---|---|---|---|
| G1 | 3HC 862-895 | Units: +1 benefic lord, +1 with a benefic lord, +1 benefic aspect, +1 exaltation or friendly sign; −1 for each converse. "If the positive units predominate, the yogakaraka will confer predominantly beneficial results in respect of a beneficial yoga; and no evil results will be given by him in regard to a beneficial yoga if the negative units predominate." | **A quantitative preponderance rule.** Negatives reduce a good yoga; they never invert it. |
| G2 | 3HC 888-898 | "the planet whose inherent strength is more will fulfil the larger part of the indications of the yoga in his Dasa … the extent of the results depends upon the residential strength of the yogakarakas." | The yoga is scaled by shadbala (which planet carries it) and by residential strength (what percentage of it is delivered). |
| G3 | 3HC 954-990 (Chart 1) | Gajakesari: the Moon "can produce the results of the yoga only as sub-lord and that too to the extent of only 40%" | A worked example of percentage scaling and dasa gating. |
| G4 | 3HC 1033-1044 | "The results ascribed to a yoga are subject to qualification or modification according as the yogakarakas are strong or weak." | Strength scales the yoga. |
| G5 | HPA ch.20 l.54-58 | "The results ascribed to each yoga will completely manifest themselves if the yogakarakas … are not afflicted." | Affliction means partial manifestation, not none. |
| G6 | 3HC 3320-3326 (Chandika) | "a conglomeration of good and evil forces are blended so that the net result is a good Yoga. The evil attendant upon the 6th lordship seems to lose its effect … The native will be highly war-like and aggressive because of the element of the 6th lordship." | Net result is FAV; the blemish survives only as a flavour of temperament. |
| G7 | 3HC 10221-10224 | "When Raja Yogas are really more powerful than Rajabhanga Yogas, then alone the former could function." | Bhanga is decided by relative strength, not by presence. |
| G8 | 3HC 10264-10267 | "in the absence of other powerful arishtas, the mere debilitation of the Sun cannot destroy all the Raja Yogas and render the person unfortunate" | **A single blemish does not overturn the yogas.** |
| G9 | 3HC 10269-10272 (Chart 143) | Leo Lagna, Saturn exalted in Rasi, debilitated in Navamsa, aspected by Mars: "The Raja Yoga formed in the 10th house has been rendered infructuous." | A named bhanga condition does cancel. |
| G10 | 3HC 1176-1182 (Chart 4) | Sunapha "practically defunct because all the evil forces have been focussed on it … The yoga has produced no results and the native is a non-entity." | Cancellation needs a concentration of evils. |
| G11 | 3HC 1514-1518 | Adhi Yoga with benefics "devoid of strength … will be present but the influence it exerts would indeed be feeble." | A weak yoga is still present, but feeble. |
| G12 | 3HC 3612-3617 | "If, say, three factors are necessary to make up a certain yoga, the presence of even one or two cannot but suggest that the yoga does operate, may be feeble." | A partial yoga still counts, scaled down. |
| G13 | 3HC 2064-2072 (Hamsa) | "The ownership of Kendra by Jupiter is not desirable but when Hamsa Yoga is present, the general principle loses its significance … even the trace of evil … disappears" (when in uccha) | The yoga overrides the lordship blemish. |
| G14 | 3HC 4524-4533; 4164-4171; 4696-4707; 1886-1888 | "no Yoga can exclusively manifest itself"; an evil yoga's effects apply "unless counterbalanced by other horoscopic factors, such as more powerful yogas or inherent strength"; precedence when Nabhasa yogas coincide (one becomes "defunct"); "Parvata Yoga cannot be so powerful as to minimise the strength of other important yogas" | Yogas compete and the stronger one prevails. Some yoga families carry explicit precedence rules. |

Further named-condition cancellations, all of them conditions, none of them "a small touch":
- Kemadruma: HPA ch.20 l.209-211 says it is "capable of neutralising all beneficial yogas". 3HC
  1379-1385 (Chart 9) gives "distinct cancellation" when the kendras from the Moon and from Lagna
  are occupied.
- Kalasarpa: 3HC 11134-11137, 11180-11199. The fear that it nullifies other yogas "is not without
  justification", but "it may not be the main cause". Its intensity drops if the associated planet
  is exalted or in its own sign. It is "defunct even if a single planet is with Rahu or Ketu or
  outside the axis".
- Kuja dosha: HJ 9359-9374. Sign exceptions; "countered by the conjunction of Mars and Jupiter or
  Mars and the Moon"; "The Dosha is not absolute", graded by sign dignity.
- Balarishta: HJ 9805-9814. "When the Ascendant lord is strong in a Kendra … aspected by a benefice
  and is free of malefic aspects, any Balarishta Yoga is nullified."
- Bandhana: 3HC 9310-9313. "If the lord of Lagna happens to be Saturn … the evil is either lessened
  or completely neutralised. Benefic aspects lessen the evil."
- Dehakashta: 3HC 4834-4835. "defunct if a benefic aspects the ascendant lord".
- Sarpasapa: 3HC 6886-6889. "If Jupiter and the 5th lord are strong, then the yoga gets somewhat
  modified."
- Raman's method statements: HJ 2426-2429, Satyacharya's "YUKTA VICHARYA … all sources of strength
  and weakness … should be evenly balanced before pronouncing an opinion"; NH 714-719, "weigh and
  balance the relative strength of each factor and then synthesise".

---

## 3. Taxonomy of mechanisms, with counts

The counts are over the 47 tabled cases (2A) plus the 14 general statements (2C). A case tagged
with two mechanisms counts once for each. The 2B house-level items are shown separately in
brackets.

| Code | Mechanism | What Raman does | Charts (2A) | General (2C) | [2B] | Typical decider |
|---|---|---|---|---|---|---|
| **M3** | **Blemish narrows scope / split verdict** | The yoga's main result stands; the blemish is delivered on another matter or a sub-matter (accidents, children, spouse's longevity, schooling, politics) | **17** (#1,2,7,8,28,35-39,44,45,46 and others) | 0 | [6] | The blemish is attached to a different house, lord or karaka from the yoga's core. The strength of the core decides whether the event happens; the blemish decides its quality or how long it lasts |
| **M1** | **Benefic aspect/association neutralises or tempers** | Jupiter (sometimes Venus, Mercury, or a neechabhanga functional benefic) aspects or joins the afflicted point → "neutralised / more than compensated / tempered / kept in check" | **12** (incl. 3 failures: #14, #15, and the "slight relief" non-rescues NH 3014, 15177) | 1 (G14 partly) | [3] | **The rescuer must itself be clean.** A Chandala-Guru or a Jupiter in Rahu's nakshatra fails. "Slight relief" does not rescue a heavy affliction (NH 3014: "Jupiter's aspect lends a slight relief. Consequently … domestic life does not appear to have been very happy") |
| **M4** | **Blemish delays or confines itself to a period** | Delay ("preventing their early expression"); first half of a dasa good and second half bad; fall in the afflicted planet's bhukti; "bhanga … set right in appropriate Periods" | **9** (#2,20-25,27, plus HJ 13137) | 2 (G2, G3) | [2] | Which planet carries the blemish, and when its dasa or bhukti runs |
| **M7** | **The afflicter's own condition defuses it** | The afflicter is the dispositor; it sits in a friendly or own-lord nakshatra; it is a functional benefic or Lagna lord; it is in a bhava-sandhi; the conjunction is wide (10-18°); it is in its own moolatrikona sign; the lordship evil does not touch the yoga | **8** (#1,5,11,15,29,32,33, plus Truman's lordship) | 1 (G13) | [6] | Degree separation, nakshatra lord, dispositorship, bhava-sandhi |
| **M5** | **Blemish lowers the plane or redirects the yoga** | The yoga fires in a degraded form, or turns into a different yoga (Raja → Parivraja), or shows as character rather than material fruit | **9** (#4,6,10,13,16,17,20,30,40) | 0 | [0] | Which planet afflicts (nodes, Saturn) and where it sits (Lagna) |
| **M2** | **Strength-weighted preponderance / net result** | Count or weigh the testimonies; the stronger set wins; equal testimonies give MIX; Rasi outweighs Navamsa | **6** (#9,12,26,35,47 and others) | **8** (G1, G2, G4, G5, G6, G7, G11, G12) | [3] | Shadbala, residential strength, the unit tally |
| **M6** | **Cancellation (bhanga / defunct / null and void)** | The yoga produces nothing or is "rendered infructuous" | **7** (#9 evil-yoga cancelled, #11, #18, #22, #41, #42, #43) | 4 (G7-G10) + 7 named | [0] | **Only under heavy or named conditions** (§4) |
| **M8** | **Balance natural vs functional role** | A natural benefic that is a malefic lord, or the reverse, is weighed both ways | 1 (NH 14705) | 0 | [2] | Lordship versus natural character |

Rough proportions over the 47 chart cases: in about **38 of 47 (≈80%) the yoga's positive verdict
survives**, either as FAV or as FAV-Q with the blemish routed elsewhere. About **9 of 47** end
AFF or effectively cancelled. Every one of those 9 has a heavy or structural cause, never one small
touch.

---

## 4. Does ONE small malefic touch ever overturn a strong yoga?

**Raman's printed position is no.** He says so directly:
- Truman (NH 10921-10926): evil lordship of the yoga planets: "their inherent capacity to confer
  the blessings of the yoga are in no way affected or lessened".
- 3HC 10264-10267: "the mere debilitation of the Sun cannot destroy all the Raja Yogas".
- 3HC 877-888: negative units predominating means "no evil results … in regard to a beneficial
  yoga".
- Shivaji (NH 5139-5141): "even the slight stigma, if any … is more than compensated".

**When a yoga is overturned in his worked charts, the cause is one of these, not a light touch:**

1. **The yoga itself falls in a dusthana (12th or 6th).** Tippu ("the yoga, having occurred in the
   12th … caused the disappearance of all the indications", NH 5687-5689) and Bhutto ("occurs in
   the 6th house … must suffer bhanga", HJ 16146). Even so, Tippu Chart 202 in HTJAH-II is softened
   to "a distinct Raja-Yoga … he could not enjoy it fully" (HJ 15939-15941). **Raman's two books
   disagree in degree on the same chart.** This should be recorded as a genuine ambiguity.
2. **A concentration of evils** on the yoga: "all the evil forces have been focussed on it" (3HC
   1180); "the whole structure is rotten" (NH 14848); Rekha-like concentration (NH 13313-13318).
3. **The yoga planet's own dignity fails twice over**: debilitated with **no** neechabhanga AND in
   a Dainya (6th-house) exchange (Marx, NH 6562-6566).
4. **A named bhanga combination** is present (3HC 298 / Chart 143), or a whole-chart arishta such
   as Kemadruma or Kalasarpa, each with its own cancellation clauses.
5. **The rescuer is itself blemished**, so a malefic affliction that would have been neutralised is
   not (Hitler NH 12290-12294; Aurangzeb NH 4643-4648). This is the case closest to "one small
   thing decides". In it the small thing (a nakshatra lord, a node contact) disables the relief, not
   the yoga directly.

**Ambiguous or borderline cases. These are real, so do not hide them:**
- **Tagore** (NH 7891-7893): one Navamsa contact (the Sun with Rahu and Venus) removed his political
  career. Read narrowly, that is M3: one sub-expression removed while the intellectual yoga is
  untouched. It shows that a single contact can delete one channel of a yoga.
- **Tilak** (NH 7197-7199): "Rahu's association and the aspect of Saturn" denied "the actual
  enjoyment of the yoga results". Two afflicters, but on a powerful Gajakesari. Raman keeps the
  character results and removes the material ones.
- **Napoleon** (HJ 15975-15997): "loosely knit", "delicately balanced", "the very seeds of
  destruction". The rise was delivered in full and the collapse came later. This is a timing
  judgment, not a cancellation, but the book's tone is close to "the blemish was decisive".
- **Ramanuja** (NH 3013-3017) and **Farouk** (NH 15177): "slight relief" from Jupiter did not save
  the matter. So a small benefic rescue is not enough against a heavy affliction. The rule is
  symmetric: small touches change little in either direction.

---

## 5. Suggested encoding (doctrine sketch, not code)

1. **Score the yoga** with the 3HC unit tally (G1), scaled by the yogakarakas' shadbala and
   residential strength (G2, G3). The output is a strength band, never a sign flip: a negative
   tally gives "feeble / fails to fructify", not "evil".
2. **Classify each blemish** by:
   (a) **where it lands**: the yoga's own core (house, lords) or a different house, lord or karaka;
   (b) **its weight**: a single contact, or a concentration (≥ 3 malefic influences, or "all the
       evil forces");
   (c) **defusers on the afflicter**: dispositor of the afflicted point; afflicter in a friendly or
       own-lord nakshatra; functional benefic; bhava-sandhi; orb > ~10° for conjunctions (Raman uses
       10°, 16° and 18° in the cases above); own sign or moolatrikona;
   (d) **benefic rescue** on the afflicted point, valid only if the rescuer is unblemished (not with
       the nodes, not in a node's nakshatra, not combust).
3. **Resolve:**
   - The blemish is defused (c), or rescued (d) and light → **FAV**. Record the blemish as a trait
     if Raman voices one (M5).
   - The blemish is light and lands outside the core → **FAV-Q**. Emit a separate qualified finding
     on the affected matter (M3), timed to the afflicter's period (M4).
   - The blemish is light and lands on the core → **FAV-Q** with reduced strength (e.g. "Hamsa has
     lost some of its strength"), or a delay (Nehru).
   - Cancellation only if: the yoga is placed in a dusthana; or there is a concentration of evils;
     or the yoga planet is debilitated with no neechabhanga AND in a Dainya exchange; or a named
     bhanga yoga; or a whole-chart arishta whose cancellations fail → **AFF / infructuous**. Even
     then, check G7/G8: a stronger Raja yoga can override, and a bhanga can be "set right in
     appropriate Periods".
   - Testimonies equal → **MIX** ("rendered neutral by the almost equal distribution", HJ 5704).
4. **Timing hooks (M4):** the yoga delivers in its strongest karaka's dasa (3HC 888-893). The
   blemish delivers in the afflicter's bhukti, or in the second half of a dasa (Mussolini, Farouk).
   Saturn-Venus mutual periods are "fatal to Raja-Yogas" (HJ 16104-16106).
5. **Living significations (siblings, mother, father, children, spouse)** follow HTJAH's
   three-factor rule. An afflicted lord AND karaka outweighs a favourable house for longevity or
   survival. The strong factor still decides whether the event occurs (#45, #46; HJ 3854, 4485,
   5839).

**Caveats.**
- Raman repeatedly calls for *yukta vichara* (judgment). Several cases (Tippu across two books,
  Napoleon, Tagore) are tone-dependent. They cannot be reduced to a rule without choosing an
  interpretation, so treat them as contestable labels.
- Some quotes come from Vol II of HTJAH, which Raman co-authored with his daughter's assistance
  (HJ 7886: "But for her assistance, the second volume would not …"). They are still printed under
  his name.
- Chart identities were checked against the nearest preceding "No. NN" (NH) or "Chart No." (HTJAH)
  header; the HTJAH-I Chart 12 / 23 / 86 numbers follow the OCR text (Chart 86 prints as "S6").
- 3HC OCR is noisy. The quoted wording was cleaned only of obvious OCR letter errors.
