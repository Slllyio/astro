# B. V. Raman's transit (gochara) method, and how he combines it with dasa/bhukti

Research extract, 2026-10-24. Read-only survey of Raman's printed books in
`data/knowledge_library/sources/`. No app/, tests/ or data/private/ was read. No engine code was
touched.

**Sources read in full or by every transit hit:**

| Key | File (under `data/knowledge_library/sources/`) | Coverage |
|---|---|---|
| HPA34 | `hindu_predictive_astrology_raman/chapter_034_gocharaphala-or-results-of-transits.md` | read in full; vedha table re-read from page images of `hindu-predictive-astrology-bv-raman.pdf`, printed pp. 257-259 (PDF pp. 264-266) because the markdown OCR garbles it |
| HPA26 | `hindu_predictive_astrology_raman/chapter_026_the-ashtakavarga-system.md` | transit rules 19-43; the Upachaya passage was checked against PDF printed p. 183 |
| HPA24, HPA33, HPA15 | same folder, ch. 24 (dasa results), 33 (annual horoscopes), 15 (marakas) | every transit hit |
| AV1-AV16 | `ashtakavarga_system_raman/chapter_0NN_*.md` (*Ashtakavarga System of Prediction*, 8th ed.) | ch. 12 (Timing Events) and 13 (Transits) in full; transit rules in ch. 3-11, 14 and 15 |
| AFB10, AFB12 | `astrology_for_beginners_raman/chapter_010_timing-events.md`, `chapter_012_transits-or-gochara.md` | read in full |
| HTJ-U | `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md` (Vol I, with Vol II from about line 7865) | every transit hit |
| HTJ2 | `how_to_judge_horoscope_raman2/chapter_001_full-text-unsplit.md` | every hit; it duplicates the Vol II text in HTJ-U |
| NH | `notable_horoscopes_raman/chapter_001_full-text-unsplit.md` | every hit for transit, gochara, sadesathi and elarata |
| 3HC | `three_hundred_combinations_complete/chapter_001_full-text-unsplit.md` | every hit |
| SJ | `studies_jaimini_raman/*.md` | every hit (3 doctrinal sentences) |

Searched and empty of transit doctrine: varshaphal_raman, graha_bhava_balas_raman,
manual_hindu_astrology_raman_1935. prasna_tantra_raman has transit material, but it is horary and
therefore walled per CLAUDE.md, so it was not used. The Prasna Marga epubs are not Raman's own
text.

Citation form: `FILE:line`, using the markdown line numbers as they stand on disk today.

---

## 0. The bottom line (read this first)

1. **The dasa decides what can happen; the transit decides when.** In Raman's words, "Transits are always
   secondary in importance. They are like catalytic agents. All conclusions must be primarily
   drawn on the basis of Dasha-vichara" (HTJ-U:11038-11039). Also: "Gochara or transit results,
   however powerful, are always subordinate to the radical or birth influences" (AV13:60-66). He
   rejects the opposite view outright. Some texts claim transits act "irrespective of directional
   influences", and "such a view cannot be tenable in the light of facts and experience"
   (AV13:66-74).
2. **Transits are reckoned from the natal Moon (Janma Rasi).** The domain they touch is then read
   from the sign's house from Lagna (AV13:394-420), and Ashtakavarga sets their strength. Both
   HPA34 and AV13 give a sign-from-Moon results table.
3. **Strength comes in three layers:** the good/bad house from the Moon, then vedha, then the
   bindus in the planet's own Bhinnashtakavarga (counted before reduction). An optional kakshya
   layer (3°45′ sub-divisions) times the result inside the sign.
4. **The specific timing points are Sodhya Pinda ("Sodya Pinda") stars and signs from
   Ashtakavarga,** transited by Saturn, Jupiter or the Sun. They fire **only if the running dasa
   already shows the event.** Raman repeats this proviso: "if the particular dasa is inclined to
   effect maraka" (HPA26:692), "provided the Dasa also indicates similar results" (AV10, around
   line 300), and "When a particular Dasa and Bhukti shows the birth of children the probable time
   could be arrived at as per Ashtakavarga rules" (AV8:536-540, end of the issue rules).
5. **In his worked cases (NH and HTJAH) the transits he actually cites are few:** Saturn's
   Elarata (sade sati) and its count of 1st, 2nd or 3rd round; Saturn or Rahu crossing a natal
   planet or the Lagna point; Jupiter's transit from the Moon (9th, 11th, over the Moon) or over a
   computed marriage sign; and Mars-Saturn or Saturn-Rahu conjunctions or mutual aspects falling on
   a sensitive house from the Moon. In the chart write-ups he **never** works vedha or bindus.
   Those appear only in the HPA34 death example and in the AV book.

---

## 1. Gochara proper: the reference point, the good and bad houses, vedha

### 1.1 The reference point is the natal Moon

- "In predicting Gochara results, the Moon and the birth constellation play a prominent part.
  Mark the position of the Moon at the time of birth. The sign, in which the birth Moon is placed,
  is called the Janma Rasi." (HPA34:40-44)
- "The passage of planets through certain angular positions from the radical Moon is technically
  termed Gochara." (AFB12, around lines 33-36)
- AV13:82-85 says the same: the results table is for transits "from the sign occupied by the Moon
  at the time of birth".
- **Lagna enters as a second frame, never as the gochara origin:**
  - The bhava affected is the transit sign's house from the Lagna. "Usually, when a planet
    transits a sign, which has the highest number of bindus in its Ashtakavarga, it advances
    results of the bhava represented by the Rasi as reckoned from the ascendant." (AV13:394-401)
    Worked case: Jupiter in Cancer is 6th from the Moon, which is bad, but it is 7th from Lagna,
    so the trouble falls on the husband; 6 bindus then "neutralises the evil to the extent of
    75%" (AV13:402-420).
  - For Upachaya and Apachaya the frame is "the ascendant or the Moon and not from the positions
    of planets (Apachayas are 1, 2, 4, 5, 7, 8, 9 and 12 houses from Lagna; the rest are all
    Upachayas)" (HPA26:151-162; PDF printed p. 183).
  - Transit over the natal Lagna point itself is a trigger (Chart 119, §4).
- He disparages Moon-only gochara: "Delineation of results by considering the movements of
  planets from Janma Rasi or the radical Moon has invariably been a rule rather than an exception
  with the rank and file of astrologers in India. The factor of [OCR: 'latta'] or the dominant
  nature of the directional influences is hardly considered." (AV13:42-48)
  - **OCR caution:** the word printed "latta" most likely corrupts "the latter". Raman gives
    **no latta (nakshatra-kick) rules anywhere in the corpus**, and the sentence's own gloss is
    "the dominant nature of the directional [dasa] influences". Do not encode latta as Raman
    doctrine on the strength of this line.

### 1.2 Good houses from the Moon (sign count; Janma Rasi = 1)

The good houses are the numerators of HPA34's vedha table, checked against the PDF page images.
They are corroborated by AFB12's "Benefic Signs" table (AFB12:219ff).

| Planet | Good (from Moon) | Vedha (obstruction) point, paired in order | Bad (AFB12 table) |
|---|---|---|---|
| Sun | 11, 3, 10, 6 | 5, 9, 4, 12 | 1, 2, 4, 5, 7, 8, 9, 12 |
| Moon | 7, 1, 6, 11, 10, 3 | 2, 5, 12, 8, 4, 9 | 2, 4, 5, 8, 9, 12 |
| Mars | 3, 11, 6 | 12, 5, 9 | 1, 2, 4, 5, 7, 8, 9, 10, 12 |
| Mercury | 2, 4, 6, 8, 10, 11 | 5, 3, 9, 1, 7, 12 | 1, 3, 5, 7, 9, 12 |
| Jupiter | 2, 11, 9, 5, 7 | 12, 8, 10, 4, 3 | 1, 3, 4, 6, 8, 10, 12 |
| Venus | 1, 2, 3, 4, 5, 8, 9, 11, 12 | 8, 7, 1, 10, 9, 5, 11, 6, 3 | 6, 7, 10 |
| Saturn | 3, 11, 6 | 12, 5, 9 | 1, 2, 4, 5, 7, 8, 9, 10, 12 |
| Rahu / Ketu | 3, 6, 11 (AFB12 table) | **none given** | 1, 2, 4, 5, 7, 8, 9, 10, 12 |

Source for the vedha column: HPA PDF printed pp. 257-258 (PDF pp. 264-265). The markdown OCR at
HPA34:187-232 is garbled for Mercury, Venus and Saturn. **Use the image reading above.**

- **Rahu = Saturn, Ketu = Mars:** "Rahu transitting the 12 houses produce results similar to
  those of Saturn, and Kethu to those of Mars." (HPA34:594-596)
  - AFB12 and AV15 give one joint Rahu/Ketu results list: 3, 6 and 11 good; 8 is "danger to
    life" (AV15, around lines 263-272).
  - AV15 adds an optional Rahu Ashtakavarga (Sambhu Hora Prakasa). Raman frames it as outside the
    standard scheme: "Whether or not to consider Rahu's Ashtakavarga is left to the discretion"
    (AV15, near the end).
- **The sign-by-sign results texts differ by book.** HPA34:46-120 and 383-594 (Sun, Moon, Mars,
  Mercury, Jupiter, Venus, Saturn), AV13:86-250, and the shorter AFB12 lists do not always agree.
  - Example: Venus 12th is "very few clothes" in HPA34:544-545 but "new friends, money, perfumes"
    in AV13:215-216. Venus 10th and 11th also swap between the two.
  - Treat the house-good/bad table above (HPA34 = AFB12) as authoritative for good/bad. The
    narrative texts are classical lists and are not internally consistent.

### 1.3 Vedha: the rule and its exceptions

- **Definition:** "The Sun, for instance, transiting the 11th, 3rd, 10th and 6th signs from the
  radical Moon is supposed to yield good results. The smooth flowing of such good results will be
  obstructed if there are any other planets (simultaneously) transiting 5th, 9th, 4th and 12th
  signs from the Moon respectively." (HPA34:141-150)
- **Reverse vedha, which cancels an evil:** "...if the Sun is in the 5th, in the course of
  Gochara, no evil will be produced provided the 11th is being transitted at the same time by any
  other planet, excepting Saturn." (HPA34:161-164) "Similarly the Vedhasthanas must be considered
  for all the planets." (HPA34:165-166)
- **Exceptions:** "It must be noted that no Vedha occurs between the Sun and Saturn, and the Moon
  and Mercury." (HPA34:179-181) These are the only two exempt pairs.
- **Which bodies obstruct:** "any other planet". The worked example lets Mars and Saturn cause
  vedha (§4, case 1). Raman never says whether Rahu or Ketu can cause or suffer vedha, so that is
  unspecified.
- **Order of precedence in the worked example (HPA34:237-301):** vedha **overrides** a good bindu
  count. The Moon in the 11th with **6 bindus** is ruled "bad" because Mars in the 8th causes
  vedha. Venus in the 1st with 4 bindus is ruled bad because Mars in the 8th causes vedha. Saturn
  in the 12th with **3 bindus** is "exceedingly bad", that is, bad house and low bindus compound.
  The verdict is the tally: "only Jupiter and the Sun are good while the others have been
  inclined to produce evil. Hence the worst evil, viz., death, befell the native, especially
  because, Saturn is in the 12th and Mars in the 8th." (HPA34:303-310)
- **An unexplained step in the same example:** "Saturn in the 12th ... but Mercury's position in
  the 11th has mitigated the evil to some extent." By the table, Saturn's evil 12th is reversed
  only by a planet in the 3rd (pair 3/12), not the 11th. Raman gives no rule for this. **Do not
  generalise it.**
- **Vedha is not used in any NH or HTJAH chart write-up.** It appears only in HPA34. (The
  "obstruction" in AV ch. 12 is kakshya-based, not gochara vedha.)

### 1.4 Effective portion of the sign (degree zones)

- HPA34:83-85: "when passing through the first 10 degrees of a sign, Mars and the Sun produce
  results."
- AFB12:197-201 adds: "Jupiter and Venus become effective when they are in the 2nd ten degrees
  while Rahu produces results throughout the entire sign."
- **Raman gives nothing for the Moon, Mercury or Saturn.** The classical third-decanate rule for
  Moon and Saturn is not in his text, so an engine must not add it as Raman's.

### 1.5 Relative weight and time-scale of planets

- "Of the different planets, the Gochara results of the slowly-moving planets, Jupiter and
  Saturn, are held to be the most powerful. The triennial results may be ascertained from Saturn,
  the yearly effects from Jupiter, the monthly results from other planets and the daily
  influences from the Moon." (HPA34:85-91)
- AFB12:203-207 adds Rahu to the slow, powerful group and gives "monthly ... from the Sun and
  Mercury".
- "The transits of Jupiter and Saturn are of primary importance while those of the other planets
  will have a secondary importance." (AV13:618-620)

### 1.6 Sade sati (Elarata), Saturn

- **Definition:** "The period of Saturn's transit of the 12th, 1st and 2nd places from the radical
  Moon" (NH glossary, NH:16544-16547). AFB12:155-160 says the same: "his transit in the 12th, the
  1st and the 2nd from the radical Moon ... Sade Sati (7½ years' Saturn)". Raman's names for it
  are Elarata, sadesathi and "7½ years Saturn".
- **The dasa decides how bad it is:** "unless the ruling period is powerful, the subject of the
  horoscope is bound to suffer unexpected miseries" (AFB12:160-163). Typical results follow at
  AFB12:164-169.
- **The cycle count matters** (AFB12:169-176): "One having good longevity can come under the sway
  of '7½ years' Saturn' thrice in his lifetime. During the first time most of the above results
  will manifest; the second time, no evil results will occur while during the third time the
  death of the native is invariably caused, unless ruling Dasa does not warrant death." The
  closing clause is a printed double negative; the sense is "unless the dasa does not warrant
  death".
  - HPA33:283-292 confirms the second round: "As this is the second time that the native has been
    undergoing 7½ years Saturn, the evil effects will only be moderate."
  - The cases confirm the third round: Aurangzeb, Marx, Roosevelt, the 3HC insanity case (§4).
- **A Sarvashtakavarga mitigation:** "The intensity of evil results produced during the period
  7½ years' Saturn gets minimised if the 12th, 1st and 2nd from the Moon has more than 30 bindus
  in the Sarvashtakavarga." (AV13:613-617) Whether "more than 30" means each sign or the total is
  ambiguous. Each sign is the natural reading, since 30 is his per-bhava SAV threshold.
- **Raman also uses sade sati at birth** as an aggravating natal fact:
  - Jesus: "born under the influence of Elarata" (NH:2343).
  - HTJAH Chart 64: "the native at birth was passing through sade-sathi", which "accelerated the
    death of the mother" (HTJ-U:4462).

### 1.7 Jupiter's transit for marriage and children

- Gochara table: Jupiter is good in 2, 5, 7, 9 and 11 from the Moon. The 5th from the Moon gives
  "sons" (HPA34:474-477) or "birth of a son" (AV13:177). The 9th gives "birth of an issue"
  (AV13:185). The 7th gives "the company of an excellent woman" (HPA34:484-488).
- **Marriage, HTJAH Vol II "Timing Marriage" (HTJ-U:8389-8411; HTJ2:870-883):**
  - "Another method is to add the longitude of the lords of the Lagna and 7th house. When Jupiter
    transits the resultant Rashi or its trines, it is favourable for marriage. The resultant
    obtained by adding the Moon's longitude to that of the 7th lord or its trines when transited
    by Jupiter can also give marriage."
  - Followed immediately by the precedence clause: "Primary importance must be given to the natal
    positions and Dasha and only secondary consideration to transiting planets."
  - **In his own two worked marriages Raman adds the Lagna BHAVA and the 7th BHAVA longitudes, not
    the two lords' longitudes** (HTJ-U:18296-18299, 18424-18427). So his practice differs from
    the rule he states. He also counts Jupiter's transit **aspect** on the natal 7th house and on
    the dispositor of the sum sign as fulfilment (§4, cases 10-11).
- **Ramakrishna's marriage (NH:6929-6936):** "The acquisition of a wife may happen in the Dasa or
  Bhukti period of a planet (i) occupying the 7th, (ii) aspecting the 7th, (iii) owning the 7th,
  (iv) or when the lord of Lagna transits the 7th. In this case Saturn was transiting Leo the 7th
  and as his Dasa was operating he brought about the marriage."
- **Ashtakavarga timing points for marriage and children:** see §2.4 (Venus and Jupiter Sodhya
  Pinda rules, AV8 and AV9).

### 1.8 Transit over natal planets and points

- **Degree-level contact is used, with an orb:**
  - Mussolini: "Jupiter is in the 27th of Gemini. Saturn by transit passes through the orb of this
    degree by about October 1944 and the exact degree is transited by about July 1945. Thus about
    this time something tragic may happen" (NH:10797-10800).
  - 3HC insanity case: "Saturn was transiting the exact degree occupied by Mercury" as Mercury
    Dasa began (3HC:10129-10130).
  - Chart 119: "When Gochara Saturn passed through Lagna point, facial paralysis set in"
    (HTJ-U:6892).
- **The orb is never quantified.** The one numeric hint is for conjunction between two transiting
  bodies: Rahu and Saturn "about 10 degrees, implying for all practical purposes conjunction
  according to Hindu astrology" (NH:12264-12267, Hitler).
- **Sign-level contact is used too:**
  - Saturn over natal Rahu: Golwalkar, NH:14578-14580.
  - Rahu over natal Saturn in the 2nd from the Moon: Nehru, NH:12452-12453.
  - Saturn over the natal Moon sign (Janma Rashi): HTJ-U:6692.
- **Saturn over the natal places of the 8th or 12th lord:** "When Saturn passes through the houses
  occupied by the 8th lord or the 12th lord from Lagna, death occurs. Passage of Saturn through
  these houses or their trines with reference to any other house in the horoscope results in the
  destruction of that house." (HTJ-U:10996-10999) This sits under the death-only-if-the-dasa-
  warrants caveat, §3.
- **Transit-to-transit configurations** count when they fall on a sensitive house from the Moon:
  - Mars-Saturn mutual aspect plus Elarata: Chart 116, HTJ-U:6716-6719.
  - "When the disease becomes acute and dangerous, there will usually be found an affliction in
    the 5th or 6th house by the transit of Mars and mutual aspects between transiting Mars and
    transiting Saturn" (HTJ-U:6733-6736).
  - Saturn-Rahu conjunction in Janma Rasi: Roosevelt NH:10212-10213; NH 65 NH:13489-13491.
  - Saturn-Rahu conjunction in the 8th from Janma Rasi: Hitler NH:12267-12269.
  - Mars-Saturn conjunction in the 11th from the Moon (favourable): Franco NH:12795-12797.
- **Navamsa transit is used** when the transiting planet enters the natal planet's Navamsa sign:
  - First wife's death when "Saturn (lord of the 2nd) was transiting Scorpio Navamsa in which
    Mercury [sub-lord] is placed" (NH:13784-13786).
  - Father's death when "Saturn was about to leave Gemini by transit and the Sun [Pitrukaraka] is
    placed in Gemini Navamsa" (NH:13791-13793).
  - The death rule "Saturn in his transit passes through the Rashi and Amsa occupied by him at
    birth or its trines" (HTJ-U:11227-11229).
  - So the transiting **sign** is compared with natal **Navamsa** signs.

### 1.9 Rahu and Ketu transits

- They follow Saturn and Mars respectively (HPA34:594-596). Joint results list in AFB12 and AV15:
  "(1) Sickness and fear ... (3) happiness and good tidings ... (6) pleasure and happiness ...
  (8) danger to life ... (11) happiness and acquisition of money, (12) expenses and danger."
- Effective through the whole sign (AFB12:200-201).
- Rahu's kakshya order is reversed because of his retrograde motion: Lagna, Moon, Mercury, Venus,
  Sun, Mars, Jupiter, Saturn, about 2¼ months each (AV15, around lines 274-280; worked at
  AV15:301-335).
- Used in cases:
  - Rahu in the 8th from Janma Rashi at death: HTJ-U:6642.
  - Rahu over natal Saturn: NH:12452.
  - Rahu receding into, and conjoining Saturn in, the 8th from the Moon: NH:12264-12269.

---

## 2. Ashtakavarga in transit

### 2.1 Bindu thresholds in the planet's own Bhinnashtakavarga

- **The general rule (AV13:261-276):** "When a planet transits a Rasi, declared favourable and has
  less than 4 bindus in his own Ashtakavarga, the favourable results will be minimum. If the
  number [is] 4, they will be optimum and if more than 4 the maximum. Similarly if a planet
  transits an unfavourable place, but has bindus in it, the malefic effects are reduced
  proportionately depending upon the number of bindus in it. Conversely, a favourable transit in
  a Rasi devoid of bindus reduces the benefic effects while an unfavourable transit in such a Rasi
  will further increase the malefic effects."
- **The scale is proportional, bindus ÷ 8,** as Raman's worked figures show:
  - Sun transiting Aries, 3rd from the Moon, with 5 bindus: "the good effects produced should be
    to the extent of 62%" (AV13:277-282).
  - Capricorn, 12th from the Moon, with 0 bindus: "evil results ... to the brim" (AV13:282-285).
  - 6 bindus neutralises evil "to the extent of 75%" (AV13:415-417).
  - 4 bindus offsets evil "to the extent of 50%, gain and loss being in equal measure"
    (AV13:457-459).
  - "This is only a general method of gauging the extent of benefic or malefic results"
    (AV13:286-288).
- **The bindus used are BEFORE reduction.** The worked examples quote Sun-Aries 5, Jupiter-Cancer
  6 and Jupiter-Aquarius 4, which are before-reduction figures (compare AV2 Table I). Reduced
  figures are named explicitly only for Saturn's transit through signs void of bindus in
  **Mercury's** Ashtakavarga "after reduction" (AV13:497-504, 582-592).
- HPA34:122-139 is cruder: "unless Gochara is combined with Ashtakavarga, results cannot be
  predicted with appreciable accuracy ... The Moon produces beneficial results provided the
  benefic dots there are above 4. If they are below 4, then the Moon cannot certainly do as much
  good."
- **An older formulation in HPA26:270-286 conflicts with AV13.** Net benefit = (benefic − malefic)
  ÷ 8, so 5 bindus gives (5 − 3) ÷ 8 = 1/4. Then an Upachaya/Apachaya override applies, counted
  from Lagna or the Moon: "Planets in Upachaya (3, 6, 10, 11) places, in friendly and own houses
  or exaltation signs produce benefic effects fully if such houses contain more benefic dots for
  the planets than malefic ones. And planets when they pass through Apachaya houses or unfriendly
  or depression signs produce malefic effects fully" (HPA26:151-157).
  - AV13 (1962, the later monograph) supersedes this with the bindus ÷ 8 proportion and the gochara
    house from the Moon. **Recommend AV13 as canonical and record HPA26 as a superseded variant.**
- **AV13 rule 5 (AV13:563-569):** benefit rises if the transited sign is the planet's own or
  exaltation sign as well as holding bindus, and is "correspondingly low" in debilitation.
- **Per-bindu result texts** (classical, quoted at AV13:289-376):
  - For each of the seven planets, 8 bindus down to 0, for example Sun: 8 "wealth and royal
    favour"; 4 "both good and bad will be equal"; 0 "death".
  - Raman immediately limits them: if the indicated matter cannot apply, such as brothers when the
    native has none, "the astrologer must have recourse to commonsense and modify judgment"
    (AV13:377-393).
  - AV4:76-99 says he also applies these lists to natal positions, "which is quite impracticable"
    if confined to transits alone.

### 2.2 Sarvashtakavarga in transit

- "If there are more than 30 bindus in a sign, then planets transiting over it produce happiness,
  wealth and mental peace and prosperity, if the figure is between 25 and 30, no good will happen,
  nor does he suffer from evil effect; if the bindus are less than 25, the results will be very
  bad." (HPA26:982-988)
- The natal bhava strength thresholds use the same numbers: less than 25 not auspicious, 30 fairly
  good, more than 30 full (AV11, around lines 30-35).
- Sade sati mitigation by SAV of more than 30 in the 12th, 1st and 2nd from the Moon: AV13:613-617.
- SAV Sodhya Pinda × a bhava's bindus, ÷ 27, gives a star; "When Saturn transits the asterism
  represented by the remainder, evil results pertaining [to] the bhava in question will
  materialise" (AV11 rule 35). The Rekha version improves the bhava (rule 36).
  - Raman's own testing: "Studies conducted by me in respect of Jupiter's transit of asterisms as
    arrived at above have been found to be mainly favourable for the bhavas concerned. Such
    transits on the basis of Ashtakavarga if combined with directional influences appear to yield
    encouraging results." (AV11, rule 35 commentary)

### 2.3 Kakshya (Prasthara) sub-divisions

- "Each sign of the zodiac stands divided into 8 parts or Kakshyas (of 3°45′ each) in the order of
  Saturn, Jupiter, [Mars], Sun, Venus, Mercury, Moon and the Lagna" (AV13:421-427). The OCR drops
  Mars from the sentence, but the table at AV13:443-451 and the footnote at AV8 (around line 485)
  both give Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna. This is the descending
  orbital order used in the Prasthara Chakra (AV2:500-507).
- **The core rule:** "A planet transiting a sign can give beneficial results only during the
  period of its passage through the Kakshyas, of which the lords have contributed bindus."
  (AV13, rule 2, lines 505-512)
- Rule 3: when four or more planets simultaneously transit kakshyas whose lords contributed bindus
  in their own Ashtakavargas, "increasing good results happen" (AV13:513-518).
- Rule 4, the content of the result (AV13:519-562). A planet transiting a sign with bindus in its
  own Ashtakavarga produces effects:
  - (a) of its karakatwa;
  - (b) from its house position relative to the kakshya lord's natal sign;
  - (c) of its house from Lagna at the time of transit.
- Rule 6: "Where the Kakshya lord and the transiting planet are friends, the results will be highly
  beneficial. Otherwise, the effects will be adverse." The worked case tones down the Sun in
  Saturn's kakshya even though Saturn gave a bindu (AV13:570-577).
- **The kakshya lord's houses:** "There is a school of thought according to which the results also
  partake of the karaka characteristics of the planet contributing a bindu. I think there is much
  truth in this view. It has also been found that a planet contributing a bindu produces the
  result of the bhava it aspects much more than the bhava it occupies." (AV13:476-482)
- Worked case: Standard Horoscope, Jupiter through Aquarius, 19-2-1962 to 17-4-1963, with
  kakshya dates at AV13:443-451.
  - Saturn kakshya, no bindu: sickness, and financial loss because Saturn owns the 12th.
  - Jupiter's own kakshya, no bindu: unfavourable.
  - Mars kakshya, bindu: good income and land.
  - Recorded outcomes: financial losses in Jupiter's kakshya, explained by Jupiter's natal aspect
    on the 2nd; anxiety over children in Saturn's kakshya, explained by Saturn's aspect on the 5th
    (AV13:452-490).
- Further kakshya rules (AV13:578-612):
  - Mercury in a kakshya with no bindu brings quarrels and nervous debility.
  - Jupiter in a kakshya with no bindu brings worry, distress and expense.
  - Saturn in a kakshya with a bindu can bring a legacy; with no bindu, accidents.
  - The sign with the fewest bindus in Saturn's Ashtakavarga causes daily annoyance whenever it
    rises.

### 2.4 Sodhya Pinda transit points (the AV book's precise timing)

Sodhya Pinda = Rasi Pinda + Graha Pinda after both reductions (AV14). Every rule has the same
form: (Sodhya Pinda or reduced total) × (bindus in some house from a planet, usually before
reduction) ÷ 27 gives a nakshatra (counted from Aswini, or by some authors from the star Saturn or
Jupiter holds), or ÷ 12 gives a sign (counted from Aries). Trines of the star or sign also count.
The trigger is the transit of Saturn, Jupiter or the Sun. Representative rules:

| Event | Factor | Trigger | Cite |
|---|---|---|---|
| Father's death | Sun's Sodhya Pinda × 9th from Sun | Saturn over star (or trines); "if the particular Dasa [is] inclined to effect maraka" | AV4 rule 12; HPA26:681-700 (uses the reduced total) |
| Father's death | Sun's Sodhya Pinda × 7th from Jupiter | Jupiter over star | AV4 rule 14 |
| Father's death | Sun's Sodhya Pinda × 7th from Sun | Sun over star | AV4 rule 15 |
| Native's death | Sun's Sodhya Pinda × 8th from Sun, ÷ 12 | Saturn over sign | AV4 rule 16; HPA26:701-713 ("if that is his Maraka period") |
| Mother's death | Moon's Sodhya Pinda × 4th from Moon | Saturn over star | AV5 rule 11; HPA26:748-762 ("if the dasa period also supports") |
| Brothers suffer or prosper | Mars' Sodhya Pinda × 3rd from Mars | Saturn over star (suffer); Jupiter over sign (prosper) | AV6 rules 27-28 |
| Education, friends | Mercury's Sodhya Pinda × 2nd from Mercury, ÷ 12 | "the Dasa and the Bhukti of the lord of which ... Similar results ... when Jupiter transits the said Rasi" | AV7 rule 20 |
| Birth of an issue | Jupiter's Sodhya Pinda × 5th from Jupiter | Jupiter over star; month from Sun's transit | AV8 rules 27-35 |
| Marriage | Venus' Sodhya Pinda × 7th from Venus | Jupiter over star (÷ 27) or sign (÷ 12); "or marriage may be likely in the Dasa of the lord of the sign" | AV9 rules 20-23 |
| Partner's affliction or death | the same star under Saturn; Venus' Sodhya Pinda × 7th from Jupiter under Jupiter | Saturn or Jupiter | AV9 rules 24-25 ("if other factors warrant") |
| Native's death | Saturn's Sodhya Pinda × 8th from Saturn (star); × bindus in Jupiter's sign (sign for Jupiter); × bindus in Sun's sign (month) | Saturn, Jupiter, Sun | AV10 rules 23-24: "may prove critical provided the Dasa also indicates similar results" |

- Raman's own evaluation: "It has been found in actual practice that in all the cases where
  certain transits are said to prove fatal, misfortunes, mental affliction and illness and
  financial losses have occurred." (AV10, end of rule 26) That is, these points mark **misfortune
  generally**, and death only when the dasa is maraka.
- Two outcome checks Raman reports:
  - 1912 Bangalore chart: "The father of the native actually died when Saturn was transiting
    Mrigasira", the star derived from natal Saturn's star (AV4, rule 12).
  - Stalin: no bindu in Scorpio in Saturn's Ashtakavarga; when Saturn transited Scorpio in 1902
    "Stalin's life was at stake ... imprisoned" (AV10 rule 1).

### 2.5 Trikona and Ekadhipatya reduction

- The procedure is given at AV2:261-360 (and in HPA26). "These reduced figures are made use of
  both for the purpose of longevity determination and for making certain predictions in the birth
  horoscope." (AV2:265-268)
- **For gochara strength Raman uses BEFORE-reduction bindus** (§2.1). Reduction enters transit
  timing only through:
  - (i) the Sodhya Pinda (always computed after both reductions);
  - (ii) "total after reductions" factors in some star rules (HPA26:681-683; AV4 rule 13; AV5
    rule 13);
  - (iii) Saturn's transit of signs void of bindus in Mercury's Ashtakavarga after reduction.
- Sarvashtakavarga is always summed before reduction (HPA26:877-893).
- The longevity system itself is disowned: "the Ashtakavarga system of Ayurdaya generally does not
  hold good in actual practice ... Correct assessment of longevity should be based upon the
  various Yogas and directional influences as per Vimshottari" (AV14, around lines 430-438).

---

## 3. The combination rule: dasa first, transit as trigger

### 3.1 Raman's precedence statements, verbatim

1. "Gochara or transit results, however powerful, are always subordinate to the radical or birth
   influences. Some astrological texts claim that irrespective of directional influences, planets
   while in transit can produce results ... Such a view cannot be tenable in the light of facts
   and experience." (AV13:60-74)
2. "As earlier cautioned these transits must be looked into only after determining the Maraka
   Dasha and Bhuktis on the strength of the Ascendant, the Moon and other planets. Transits are
   always secondary in importance. They are like catalytic agents. All conclusions must be
   primarily drawn on the basis of Dasha-vichara (analysis of Dasha)." (HTJ-U:11037-11039;
   HTJ2:4679-4683)
3. "Death indicated on the basis of transits can happen only when the directional influences in
   the birth charts warrant. Otherwise misfortunes such as ill-health, loss of money,
   misunderstandings with kith and kin and separations, may happen." (HTJ-U:10988-10993)
4. "Primary importance must be given to the natal positions and Dasha and only secondary
   consideration to transiting planets." (HTJ-U:8410-8411, marriage)
5. "Gochara influences must also synchronise with the time of death." Then: "When Maraka Dasha is
   operating the momentum of the last signal for death is given by AyushKaraka Saturn in his
   transits. Death occurs when Saturn in his transit passes through the Rashi and Amsa occupied by
   him at birth or its trines." (HTJ-U:11214, 11226-11229)
6. "The Gochara results should never be interpreted without reference to the ruling period and
   sub-period. Suppose illness is indicated according to the prevailing Dasa and Bhukti; if,
   according to Gochara the period is likely to be bad then the illness would be of serious type.
   The results of the prevailing Dasa and Bhukti should be combined with the effects of Gochara
   before any predictions are ventured." (AFB12:39-53)
7. "The dasa results stand to be modified by the effect of Gochara or transiting planets." (HPA24,
   rule 6, around line 110)
8. "Calculations must be made not only in regard to the dasas and bhukthies ruling at any
   particular period but also due consideration should be bestowed on results of transits ...
   Gochara enables us to predict the effects of the current period." (HPA34:32-38) He also
   criticises those who read Mars, Saturn and Jupiter "irrespective of the part played by the
   prevailing Dasa (period) and Bhukthi (sub-period)", and closes: "Astrological predictions can
   be accurate when the influences of birth chart are blended with those of Gochara and
   Ashtakavarga, together with Vedha or obstructing forces." (HPA34:369-381)
9. "These directional influences should always be interpreted taking into account transit
   indications." (AV12:123-124) "It is the combined effects of the transits as well as the
   directions, that can indicate, for any given period, the nature of the results to happen."
   (AV13:620-623)
10. "When there are no combinations for incarceration in the birth horoscope, imprisonment
    indicated by a transit should not be predicted. Similarly when there are no powerful yogas in
    the radical chart, reputation, fame, etc., denoted by a transit will have a very limited scope
    for expression." (AV13:254-260)
11. "Whether this timing relates to the birth of the first issue or subsequent ones, should be
    ascertained on the basis of the current directional influences. When a particular Dasa
    (period) and a particular Bhukti (sub-period) shows the birth of children the probable time
    could be arrived at as per Ashtakavarga rules." (AV8, end of rule 35)
12. "But what is the channel through which the results can be felt, excepting the Dasas and the
    transits. The effects of any yoga, Nabhasa or otherwise, can only be realised during the
    periods and sub-periods of, or during the times of favourable transits of the planets causing
    the yoga." (3HC:10585-10591)
13. "...according to Parasara, the results due to various combinations come into operation during
    the various Dasas and Bhuktis influenced to some extent by the Gochara or transits of planets."
    (SJ ch. 5, lines 29-32) "Of the predictive methods, rules for Maraka determination plus the
    Gochara dispositions would enable one to anticipate the probable duration of life fairly
    accurately." (SJ ch. 6, lines 28-31)
14. Hitler, in the moment of prediction: "He is still powerful in Navamsa so that the evil effects
    in his sub-period can be accelerated only by Gochara or transit influences." (NH:12258-12259)
15. Subhas Bose, the negative case: the Jupiter/Mars dasa lord's "location and ownership would not
    have invested him with power to kill the native, especially that Gochara or transiting
    positions were not adverse" (NH:14074-14078). **Non-adverse gochara is part of the reason
    Raman withholds a death verdict.**

### 3.2 The combination procedure these statements imply

- **Step A, dasa:** decide what the running MD/AD can deliver: house influence, the four-tier
  bhukti grading (HTJAH-I "When Do Indications Fructify"), and maraka status. This is the gate.
- **Step B, natal promise:** a transit cannot produce an event the natal chart lacks (statement 10).
- **Step C, transit as amplifier:**
  - Bad dasa + bad gochara = the event is "serious" (AFB12:47-51).
  - Good dasa + bad gochara = "resultant is still favourable", with the evil moderated. HPA33's
    example: Guru/Budha well placed against second-round sade sati with Jupiter and Saturn in the
    12th and Rahu in the 5th.
  - Bad dasa + benign gochara = the event is withheld or softened (statement 15, Bose).
- **Step D, transit as trigger** inside a dasa that already shows the event:
  - Saturn's Elarata or a Saturn transit to a natal maraka or ayush point for death.
  - Jupiter's transit of the Moon-relative good houses or of computed marriage or issue
    signs/stars for marriage and children.
  - Ashtakavarga stars for parents, siblings and the bhavas.
- **Step E, a transit "death" point outside a maraka dasa** degrades to misfortune: ill-health,
  loss, separation (statement 3; AV10 rule 26).
- **The one place Raman lets transit act alone:** "the 'active diseases' may make their appearance
  with every evil transit, if the Lagna is weak and afflicted" (HTJ-U:6205-6206). Here natal
  weakness is the gate in place of the dasa.

---

## 4. Worked examples: event, MD/AD, transits cited, Raman's reasoning

Dates and periods are as Raman printed them. "Moon-rel." is the house counted from the natal Moon.

1. **HPA34 death example, "about the end of the second week of March 1937"** (HPA34:237-361; PDF
   pp. 258-259).
   - Dasa: not given.
   - Transits: Sun 11th (4 bindus, no vedha, good); Moon 11th (6 bindus, vedha from Mars in the
     8th, bad); Mars 8th (4 bindus, bad); Mercury 11th (5 bindus, vedha from Saturn in the 12th,
     bad); Jupiter 9th (4 bindus, good); Venus 1st (4 bindus, vedha from Mars in the 8th, bad);
     Saturn 12th (3 bindus, exceedingly bad, mitigated by Mercury in the 11th).
   - Reasoning: a majority of bad transits, especially Saturn in the 12th and Mars in the 8th from
     the Moon, meant death.
   - **Non-general step:** the Mercury-mitigates-Saturn reversal (see §1.3).
   - This is the **only** fully worked vedha and bindu tally in the corpus, and it uses no dasa.
     It sits uneasily with his precedence statements.
2. **HTJAH Chart 5, Tagore (b. 7/6-5-1861), death 7-8-1940 in Guru Dasa, Guru Bhukti**
   (HTJ-U:909-933).
   - Dasa: Guru gets maraka power in the Navamsa.
   - Transit: "Saturn was transiting the 2nd from the radical Moon", which is the final phase of
     Elarata. Raman prefaces it with "in the determination of death, the transiting influences have
     a great bearing."
3. **HTJAH Chart 64 (b. 16-11-1914):** the mother died in Mars Dasa, Saturn Bhukti.
   - Raman adds that "the native at birth was passing through sade-sathi. All these accelerated the
     death" (HTJ-U:4445-4463). This is natal sade sati used as an aggravating factor.
4. **HTJAH Chart 109 (b. 28-1-1919):** typhoid in Venus/Venus/Saturn antara with "Saturn
   transiting Scorpio"; pneumonia and suspected TB in Venus Dasa with Saturn transiting Aquarius
   (HTJ-U:6613-6620).
   - Reasoning: Venus with the 6th lord, aspected by the 8th lord.
   - The transit is recorded as a co-factor without its own explanation.
5. **HTJAH Chart 110 (b. 2/3-9-1921):** TB suspected in 1947, Rahu/Jupiter/Sun, Saturn transiting
   Cancer. She died "as soon as the sub-period of Saturn commenced"; "at the time of her death,
   Saturn was transiting Leo and Rahu Aries, the 8th from Janma Rashi" (HTJ-U:6633-6642).
   - Moon in Virgo, so Saturn in Leo was the 12th from the Moon (Elarata beginning) and Rahu the
     8th from the Moon.
   - The sub-lord Saturn is the 7th lord from the Moon and Ayushkaraka.
6. **HTJAH Chart 114 (b. 9-9-1911):** hydrocele operation in Mercury/Jupiter. "At the time of the
   operation, Saturn was transiting Janma Rashi." (HTJ-U:6680-6692)
7. **HTJAH Chart 116 (b. 4/5-5-1895):** appendicitis operation and death, about August 1926, in
   Rahu/Venus.
   - Dasa: Rahu gives Saturn's results, and Saturn is in a maraka house from the Moon; Venus is
     with Mars.
   - Transits: "Mars was transiting Cancer and Saturn Libra. The Elarata influence coupled with
     powerful mutual aspects between transiting Mars and Saturn all contributed to the
     acceleration of death." (HTJ-U:6705-6719)
   - Moon in Virgo, so Saturn in Libra = 2nd from the Moon. Mars in Cancer aspects Libra by his
     4th; Saturn in Libra aspects Cancer by his 10th. Raman's generalisation follows at
     HTJ-U:6733-6736.
8. **HTJAH Chart 119 (b. 12-4-1912):** "When Gochara Saturn passed through Lagna point, facial
   paralysis set in" (HTJ-U:6886-6892).
   - Natal Mars, the 6th lord, is almost exactly on the ascendant degree, aspected by debilitated
     Saturn.
   - No dasa is given. This is a **degree-level** transit over the Lagna point.
9. **HTJAH Chart 124, a prediction (not an outcome):** the mother's death was forecast for the end
   of Rahu Dasa, Mars Bhukti to 21-11-1969.
   - Transit rule: Sun − Moon = Capricorn; "When Saturn or Jupiter pass through that sign and
     Navamsha or through the triangular positions ... the demise of the mother may take place."
   - Applied: "In March 1969 Jupiter would transit the triangular sign of Virgo. Saturn would be in
     ... Aries which being the twelfth sign from the Moon heralds the beginning of sadesati."
     (HTJ-U:6999-7019)
   - **Non-general step:** Sun-minus-Moon point for the mother, with Rasi and Navamsa matched
     jointly.
10. **HTJAH II marriage case (Mercury Dasa, married within 6 months of its start, January 1950)**
    (HTJ-U:18284-18299).
    - Dasa: Mercury, with the 9th lord Moon and aspected by exalted Jupiter.
    - Transit: Lagna bhava + 7th bhava = Sagittarius 26°22′. "Transit Jupiter was in Capricorn ...
      Jupiter from here was aspecting natal 7th house and natal Jupiter who is also the ruler of
      the sign signified by the sum."
    - **Non-general step:** Jupiter is not in the sum sign or its trines; Raman accepts Jupiter's
      transit aspect on the 7th and on the sum sign's lord.
11. **HTJAH II marriage case (Jupiter Dasa, Saturn Bhukti, about age 27)** (HTJ-U:18418-18427).
    - Dasa: Jupiter rules the Navamsa of the 7th lord; Saturn rules the 9th and 10th and aspects
      the 7th.
    - Transit: Lagna 56°47′ + 7th 236°47′ = Capricorn; "Jupiter in transit was moving over this
      sign as well as 7th lord Mars."
12. **HTJAH II longevity case, died 7-2-1966**, predicted in Rahu Dasa, Sun Bhukti
    (25-9-1965 to 19-8-1966) (HTJ-U:11200-11233).
    - Dasa: maraka analysis by units of killing power; the Sun is 2nd lord from the Moon and in the
      7th from the Moon; 2/12 from the dasa lord.
    - Transit: Saturn natally in Libra Rasi and Gemini Navamsa; Aquarius is trine to both; "He will
      occupy Aquarius Rashi and Gemini Navamsha by February-March 1966."
    - **Non-general step:** Saturn returns to a trine of its own natal Rasi **and** its own natal
      Navamsa simultaneously.
13. **NH 6, Jesus:** "The resurrection also took place in Ketu Dasa on 9-4-30 A.D., when Jupiter
    was transiting the radical Moon and the 7th from Lagna." Also "born under the influence of
    Elarata" (NH:2343, 2489-2492).
14. **NH 16, Milton:** Venus Bhukti in Jupiter Dasa brought blindness and the deaths of son and
    wife. Venus owns the 7th and 12th and is with Saturn and the Sun. "Added to all these, the
    Poet was passing through sadesathi." (NH:4447-4461)
15. **NH 17, Aurangzeb:** died early 1707 in Mercury Dasa, Saturn Bhukti.
    - Dasa: Mercury owns the 8th from Lagna and the 2nd from the Moon; MD and AD lords 6/8.
    - Transit: "Note also the fact that Saturn was transiting Taurus and thus causing sadesathi for
      the third time." (NH:4749-4756)
16. **NH 18, Shivaji** (NH:5053-5079):
    - Jupiter/Mercury: an heir was born, and the defeat by Nowshar Khan "may be explained by the
      elarata influences".
    - Jupiter/Moon: an attempted murder (failed) and Shahji's death; "Moreover, Saturn was
      transiting the 4th from Shivaji's Janma Rasi."
    - Jupiter/Mars: his only defeat. "Mars is doubtless a yogakaraka ... but by transit, Mars and
      Saturn were afflicting the 9th and 4th houses respectively."
    - Reasoning: the transit explains why a good dasa lord gave a reverse. This is transit
      **modifying** the dasa.
17. **NH 26, Marx:** died 1883 in Saturn/Mercury. "Saturn was transiting Taurus, the 2nd from Marx's
    Janma Rasi, with the result he was having sadesathi for the third time." (NH:6609-6622)
18. **NH 28, Ramakrishna:** married 1859 in Saturn/Moon. The rule includes "when the lord of Lagna
    transits the 7th. In this case Saturn was transiting Leo the 7th and as his Dasa was operating
    he brought about the marriage." (NH:6926-6936) The MD lord's own transit fulfils the event.
19. **NH 38, Henry Ford:** married in Rahu/Moon "when Jupiter was transiting Scorpio ... Jupiter,
    being placed in the 9th from the Moon with Kalatrakaraka Venus, gave the gain of a wife while
    transiting the 11th" (NH:8537-8544).
    - Natal Moon 290°12′ (Capricorn), so Scorpio = 11th from the Moon, a good gochara house for
      Jupiter.
20. **NH 47, Roosevelt:** died as Ketu/Saturn began. "Roosevelt was having the Elarata for the third
    time in his life and Saturn-Rahu conjunction was taking place in his Janma Rasi, all these
    hastening his end." (NH:10202-10213)
21. **NH 49, Savarkar:** arrest and transportation in Jupiter/Ketu and Jupiter/Venus. "When he was
    running sadesathi for the first time, the native was persecuted, arrested, tried and finally
    convicted." (NH:10583-10591) Consistent with "first round, most results manifest" (AFB12).
22. **NH 50, Mussolini, a published prediction (November 1943):** Saturn transits the orb of natal
    Jupiter's 27° Gemini by October 1944, exact by July 1945. Mars-Saturn conjunction in late
    Taurus in March 1944. "The time will be the present sub-period of Rahu in the major period of
    Saturn." (NH:10796-10810)
    - Dasa: Saturn/Rahu; Saturn in the 7th; MD and AD lords 2/12. Death came in Saturn/Jupiter.
    - **Non-general step:** a degree-orb transit of a natal planet.
23. **NH 58, Hitler, a published prediction** (NH:12249-12272).
    - Dasa: Moon Bhukti (vipat tara); "only the latter part of his Bhukti that can prove harmful"
      because the natal Moon is in the 2nd hora of Sagittarius. The bhukti is halved by hora, and
      the window runs from 18-10-1944 for nine months.
    - Transits: Saturn in the 8th from the Moon; Rahu entering Gemini, "the distance between Rahu
      and Saturn will be about 10 degrees, implying for all practical purposes conjunction"; exact
      in the second week of May 1945 "in the 8th from Hitler's Janma Rasi"; plus "the recent solar
      eclipse".
    - **Non-general steps:** hora-halving of the bhukti, a 10° conjunction orb, and an eclipse.
24. **NH 59, Nehru:** last detention in Moon/Mercury. "Rahu was then transiting radical Saturn being
    the 2nd from the Moon." (NH:12449-12453)
25. **NH 61, Franco:** Nationalist Government proclaimed 7-2-1938 in Mercury Bhukti. "Mars almost
    in conjunction with Saturn in Pisces — the 11th from Franco's Janma Rasi and Jupiter and Venus
    were transiting the 9th." (NH:12791-12797) Malefics in a good gochara house (11) count as
    favourable.
26. **NH 64, Duke of Windsor:**
    - Father's death 8-1-1936 at the end of Saturn/Rahu: "the subject was undergoing sadesati so
      that father's death was inevitable."
    - Abdication 10-12-1936 as Saturn/Jupiter began: Dasa Chidra, plus a vipat-star dasa, plus "the
      Prince was installed on the throne at an inauspicious moment, when he was undergoing
      sadesati." (NH:13257-13285)
27. **NH 65:** Mercury/Moon, "undergoing elarata influences for the second time and the conjunction
    of Rahu and Saturn in his Janma Rasi was least conducive to a happy state of mind ... following
    Saturn-Rahu conjunction the native had a change for good." (NH:13486-13492)
    - A second-round sade sati gives mental strain, not disaster, consistent with AFB12.
28. **NH 67 (Dhana Yoga example)** (NH:13780-13793):
    - First wife's death in October 1926, end of Venus/Mercury, "when Saturn (lord of the 2nd) was
      transiting Scorpio Navamsa in which Mercury is placed."
    - Father's death in 1930, Sun/Jupiter: "Saturn was about to leave Gemini by transit and the Sun
      is placed in Gemini Navamsa."
    - **Non-general step:** transit sign = the natal **Navamsa** sign of the dasa or sub-lord.
29. **NH 68, Subhas Bose:** 1945, Jupiter/Mars. Death was not attributable to the dasa lord, in part
    because "Gochara or transiting positions were not adverse"; danger was read from Pratyak tara
    and the "death while journeying" yoga (NH:14072-14083).
30. **NH 71, Golwalkar:** "arrested in Rahu Dasa Rahu Bhukti, exactly when Gochara Saturn was
    passing through the radical Rahu who occupies the 8th Bhava" (NH:14578-14580).
    - Raman's footnote quotes Sathya Nadi: death "in Venus Sub-period in Jupiter's Dasa, when he is
      aged 68 and the Sun transits through Libra" (NH:14620-14623). This is a nadi quotation, not
      Raman's rule.
31. **3HC insanity case:** "Mercury's Dasa commenced and the man was taken violently insane ... At
    this time Saturn was transiting the exact degree occupied by Mercury."
    - Death prediction: "Saturn causing elarata for the third time and a Maraka Dasa operating, we
      predicted that his death would happen when Saturn entered Aswini. Unfortunately the
      prediction was realised." (3HC:10125-10140)
    - **Non-general step:** the choice of Aswini (a star entry) is not explained.
32. **AV Standard Horoscope (b. 16-10-1918):**
    - Jupiter Dasa and its eight-fold Prasthara sub-division: she married as soon as Jupiter Dasa
      began. Raman adds, "The indications of Dasas should be interpreted in the light of the
      transit influences also." (AV12, around lines 160-175)
    - Jupiter's kakshya transit through Aquarius 1962-63, with outcomes (AV13:443-490).
    - Rahu's kakshya transit through Cancer 1961-63 (AV15).
33. **HPA33 annual example:** Guru Dasa, Budha Bhukti, well placed, against Gochara second
    sade sati with Jupiter and Saturn in the 12th and Rahu in the 5th. "Combining the above two sets
    of influences, the resultant is still favourable." (HPA33:280-292) **The cleanest statement of
    dasa precedence in a worked case.**

**Patterns that recur across the cases, and are not stated as general rules:**

- **Elarata, and its round number, is the transit Raman cites most:** cases 2, 3, 5, 7, 13-17,
  20, 21, 26, 27 and 31. A third round plus a maraka dasa equals death.
- **Raman often cites Saturn's transit with no house rationale at all** (cases 4 and 6). It is a
  "co-present affliction", not a derived trigger.
- **Natal Navamsa signs are treated as transit targets** (cases 9, 12 and 28).
- **Jupiter's transit aspect is accepted as fulfilment** (case 10).
- **Mars-Saturn and Saturn-Rahu configurations** on the Moon sign or the 8th from it count as
  malefic; in the 11th from the Moon they count as good (cases 7, 20, 23, 25 and 27).

---

## 5. Precision items

- **Sign versus degree:**
  - The gochara table, vedha and sade sati are **sign-based** (whole-sign, counted from the Janma
    Rasi).
  - Transit over a natal planet or the Lagna point is **degree-based when Raman wants precision**
    ("orb of this degree", "exact degree", "Lagna point"). No numeric orb is given for a transit
    over a natal point.
  - For conjunction of two transiting bodies, about 10° = conjunction (NH:12266).
  - Kakshya = 3°45′ arcs. Sodhya Pinda points are nakshatras of 13°20′ or signs.
- **Effective decanate:** Sun and Mars in the first 10° (HPA34:83-85; AFB12:197-198); Jupiter and
  Venus in the middle 10°; Rahu the whole sign (AFB12:199-201). Silent for the Moon, Mercury and
  Saturn.
- **Retrograde:**
  - No rule for transiting retrograde planets anywhere in the corpus: no vakra modification, no
  re-entry rule.
  - The only motion-related statement is Rahu's reversed kakshya order "because of his backward
    motion" (AV15).
  - **Do not invent a retrograde rule as Raman's.**
- **Dates as Raman states them:** he quotes calendar months for sign ingresses, for example
  "Saturn enters Aquarius by February 1964"; "Sun transits Cancer (17th July to 16th August)"
  (AV8 rule 29); "Sun ... Virgo (14th September to 14th October)" (AV9 rule 23). These sidereal
  solar-month boundaries match his own ayanamsa of the time.
- **Ayanamsa and positions:**
  - All his charts are sidereal (nirayana) with **his own ayanamsa.** The AV book's illustrated
    horoscopes print it per chart: 20°42′ for 1878, 20°46′ for 1882, 21°6′ for 1906 (AV16).
  - AFB Appendix I gives the formula: (year − 397) × 50⅓″, for example 21°30′12″ for 1935 (AFB12,
    Appendix lines after the table).
  - Transit positions in the cases are the same sidereal frame. **The engine's Raman-ayanamsa
    default (CLAUDE.md) is therefore the correct frame for transits too.**
- **Bhava longitudes:** the marriage-sum rule uses **bhava** longitudes (Lagna bhava + 7th bhava)
  in Raman's worked cases (§1.7).
- **Gochara counting:** sign count, Janma Rasi = 1. A transit "over the radical Moon" = 1st.

---

## 6. Implications for the engine (for the caller to weigh; nothing implemented)

1. **Transit must not create a verdict.** Encode it as a modifier and trigger on dasa and bhukti
   windows that already carry the matter: the four-tier bhukti grade from "When Do Indications
   Fructify" stays the gate. This matches statements 1-6 and 10.
2. **The minimal Raman-faithful transit layer, in his own order of use:**
   - (a) Elarata state plus its round number (1st, 2nd or 3rd);
   - (b) Saturn, Jupiter and Rahu by sign from the Janma Rasi against the good-house table;
   - (c) Saturn, Rahu or Jupiter over natal Rasi **and** Navamsa signs of the dasa/sub-lords,
     the maraka planets, the Lagna and the Moon;
   - (d) Jupiter's transit (including aspect) over the marriage sum sign (Lagna bhava + 7th bhava)
     and the AV marriage and issue points;
   - (e) the bindu proportion (bindus ÷ 8, before reduction) and SAV thresholds (more than 30 /
     25-30 / less than 25) as intensity.
   - Vedha and kakshya are doctrinally Raman's, but are used only in HPA34 and AV12-15.
3. **Label death-point transits.** Death-point transits outside a maraka dasa must degrade to
   "misfortune" (statement 3; AV10 rule 26). CLAUDE.md's decree-voice guard still applies.
4. **Known conflicts to record, not resolve silently:**
   - HPA26 (benefic − malefic)/8 with an Upachaya override, versus AV13 bindus ÷ 8. **Prefer AV13.**
   - The marriage-sum rule says lords; Raman's practice uses bhavas.
   - The HPA34 Mercury-mitigates-Saturn step is unexplained.
   - The sign-results texts differ between HPA34, AV13 and AFB12.
   - "latta" at AV13:46 is probably OCR for "latter"; there is no latta doctrine.
