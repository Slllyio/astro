# H2 (Dhana) DRAFT Golden Validation Worksheet

**File:** `tests/fixtures/raman_goldens.jsonl` (lines 51-63)

**Instructions:** For each chart below, verify:
1. Birth data decode (date, time, tz, lat/lon) is correct
2. The expected verdict matches Raman's text
3. The signification tag is correct

Mark each chart: **CONFIRMED** / **REJECT** / **FIX: <what to change>**

---

## Engine Scoreboard (pre-confirmation)

| # | Chart | Sig | Expected | Engine | Match |
|---|-------|-----|----------|--------|-------|
| 1 | HTJAH-I.chart_38 | wealth | favourable | favourable | YES |
| 2 | HTJAH-I.chart_39 | vision | afflicted | afflicted | YES |
| 3 | HTJAH-I.chart_40 | wealth | favourable | favourable | YES |
| 4 | HTJAH-I.chart_41 | wealth | favourable | favourable | YES |
| 5 | HTJAH-I.chart_42 | wealth | afflicted | favourable | NO |
| 6 | HTJAH-I.chart_43 | wealth | favourable | mixed | NO |
| 7 | HTJAH-I.chart_44 | wealth | afflicted | mixed | NO |
| 8 | HTJAH-I.chart_45 | wealth | favourable | mixed | NO |
| 9 | HTJAH-I.chart_46 | wealth | favourable | mixed | NO |
| 10 | HTJAH-I.chart_48 | wealth | mixed | favourable | NO |
| 11 | HTJAH-I.chart_49 | wealth | favourable | mixed | NO |
| 12 | HTJAH-I.chart_50 | wealth | afflicted | favourable | NO |
| 13 | HTJAH-I.chart_51 | wealth | favourable | favourable | YES |

**Score: 5/13 (38%)**

---

## Chart 1: HTJAH-I.chart_38
**Chart 38 (Speaker in Indian State, Venus pivotal)**

### Birth Data
- **DateTime:** 1893-10-21T04:01:00
- **Timezone:** 5.1722 (= lon/15 = 77.5833/15)
- **Lat/Lon:** 13.0, 77.5833
- **Decode note:** Long '5h 10m 20s E' decoded as 77.5833 deg E; LT -> tz=lon/15=5.1722. Date '20/21-10-1893 at 4-1 a.m.' -> after midnight, date is the 21st.

### Verdict
- **Signification:** wealth
- **Expected verdict:** favourable
- **Raman's reasoning:** Venus (2nd lord) much more than other planets can influence the 2nd house; Venus-bhukti in Saturn-MD was financially pivotal -- appointed Speaker in a leading Indian State.
- **Citations:** ['HTJAH-I:2594-2611']

### Your Review
- [ ] Birth data correct
- [ ] Verdict correct
- [ ] Signification correct
- **Decision:** _CONFIRMED / REJECT / FIX: ___

---

## Chart 2: HTJAH-I.chart_39
**Chart 39 (Loss of eye-sight, every vision factor afflicted)**

### Birth Data
- **DateTime:** 1883-03-24T06:00:00
- **Timezone:** 5.1722 (= lon/15 = 77.5833/15)
- **Lat/Lon:** 13.0, 77.5833
- **Decode note:** Vision signification (not wealth). Long '5h 10m 20s E' = 77.5833 deg E. Time '6 a.m.' exact.

### Verdict
- **Signification:** vision
- **Expected verdict:** afflicted
- **Raman's reasoning:** Ketu in the 2nd aspected by Rahu, hemmed by Sun and Saturn (Papakartari); 2nd lord Mars in 12th with Mercury aspected by Saturn; Netra-Karaka hemmed between Mars/Mercury and Ketu; native lost his eye-sight in Rahu-bhukti within Jupiter-MD.
- **Citations:** ['HTJAH-I:2720-2737']

### Your Review
- [ ] Birth data correct
- [ ] Verdict correct
- [ ] Signification correct
- **Decision:** _CONFIRMED / REJECT / FIX: ___

---

## Chart 3: HTJAH-I.chart_40
**Chart 40 (Inherited an empire, all three pillars strong)**

### Birth Data
- **DateTime:** 1895-12-14T03:05:00
- **Timezone:** 0.0 (= lon/15 = 0.5/15)
- **Lat/Lon:** 52.85, 0.5
- **Decode note:** GMT explicitly stated. Long '0-30 E' = 0.5 deg E. Lat '52 51 N' = 52.85. Date '13/14-12-1895 at 3-5 a.m.' -> 14th.

### Verdict
- **Signification:** wealth
- **Expected verdict:** favourable
- **Raman's reasoning:** All three pillars strong: 2nd holds Sun/Moon/Mars/Mercury; Mars own-house cancels blemish; debilitated Moon cancelled by exalted Jupiter aspect; exalted Jupiter (Dhana-Karaka) aspected by exalted Saturn (Yoga Karaka); indications of immense wealth; inherited an empire in Ketu Dasa Mercury Bhukti.
- **Citations:** ['HTJAH-I:2739-2765']

### Your Review
- [ ] Birth data correct
- [ ] Verdict correct
- [ ] Signification correct
- **Decision:** _CONFIRMED / REJECT / FIX: ___

---

## Chart 4: HTJAH-I.chart_41
**Chart 41 (Rs. 1500/month, Raja-Yoga in 2nd)**

### Birth Data
- **DateTime:** 1900-02-04T04:00:00
- **Timezone:** 6.1 (= lon/15 = 91.5/15)
- **Lat/Lon:** 23.0, 91.5
- **Decode note:** Long '91 30 E' degrees. Date '3/4-2-1900 at 4-00 a.m.' -> 4th. tz=91.5/15=6.1.

### Verdict
- **Signification:** wealth
- **Expected verdict:** favourable
- **Raman's reasoning:** Sun (9L), Mercury (7L+10L), Mars (5L) in the 2nd form a Raja-Yoga; 2nd lord Saturn in Lagna; Jupiter (Lagna-lord) in 12th with Rahu but from Moon is 2nd-lord in 10th; quite well off, Rs. 1500/month; Mercury period improved finances.
- **Citations:** ['HTJAH-I:2767-2786']

### Your Review
- [ ] Birth data correct
- [ ] Verdict correct
- [ ] Signification correct
- **Decision:** _CONFIRMED / REJECT / FIX: ___

---

## Chart 5: HTJAH-I.chart_42
**Chart 42 (Ordinary man Rs. 50-60/month, Dwirdwadasa)**

### Birth Data
- **DateTime:** 1909-07-03T21:14:00
- **Timezone:** 5.1722 (= lon/15 = 77.5833/15)
- **Lat/Lon:** 13.0, 77.5833
- **Decode note:** Long '5h 10m 20s E' = 77.5833 deg E. Single date '3-7-1909', PM time.

### Verdict
- **Signification:** wealth
- **Expected verdict:** afflicted
- **Raman's reasoning:** Mars in 2nd; Jupiter (3L+12L) aspects the 2nd -- both bad; 2nd lord Saturn in 3rd (bad for finance); Dwirdwadasa positions throughout; ordinary man drawing Rs. 50-60/month.
- **Citations:** ['HTJAH-I:2788-2805']

### Your Review
- [ ] Birth data correct
- [ ] Verdict correct
- [ ] Signification correct
- **Decision:** _CONFIRMED / REJECT / FIX: ___

---

## Chart 6: HTJAH-I.chart_43
**Chart 43 (Sound finances, no debt, neecha-bhanga Jupiter)**

### Birth Data
- **DateTime:** 1890-08-24T20:44:00
- **Timezone:** 5.1089 (= lon/15 = 76.6333/15)
- **Lat/Lon:** 12.3333, 76.6333
- **Decode note:** Long '76 38 E' degrees. Lat '12 20 N'. Chart 47 is a DUPLICATE of this nativity (same birth data) used for Chandramangala illustration -- skipped.

### Verdict
- **Signification:** wealth
- **Expected verdict:** favourable
- **Raman's reasoning:** Aries 2nd un-aspected (fairly strong); 2nd lord Mars in 9th in own sign (fortunate); Dhana-Karaka Jupiter debilitated in 11th but neecha-bhanga (dispositor Saturn in quadrant from Moon); no debts (no 6th connection); sound finances; Mars Dasha favourable for saving.
- **Citations:** ['HTJAH-I:2807-2823']

### Your Review
- [ ] Birth data correct
- [ ] Verdict correct
- [ ] Signification correct
- **Decision:** _CONFIRMED / REJECT / FIX: ___

---

## Chart 7: HTJAH-I.chart_44
**Chart 44 (Lost all fortune, Rs. 50000 debt)**

### Birth Data
- **DateTime:** 1888-09-30T04:35:00
- **Timezone:** 4.9833 (= lon/15 = 74.75/15)
- **Lat/Lon:** 26.5, 74.75
- **Decode note:** Long '74 45 E' (OCR prints '74' 45' E' with apostrophe for degree). Date '29/30-9-1888 at 4-35 a.m.' -> 30th.

### Verdict
- **Signification:** wealth
- **Expected verdict:** afflicted
- **Raman's reasoning:** Virgo 2nd with Sun (Lagna-lord) aspected by Saturn (6L+7L); 2nd lord Mercury in 3rd with Venus (3L+10L turned malefic); from Moon, Saturn and Rahu in 2nd; Dwirdwadasa in rashi and navamsa; lost all fortune and incurred Rs. 50000 debt in Ketu Dasha Venus Bhukti.
- **Citations:** ['HTJAH-I:2827-2848']

### Your Review
- [ ] Birth data correct
- [ ] Verdict correct
- [ ] Signification correct
- **Decision:** _CONFIRMED / REJECT / FIX: ___

---

## Chart 8: HTJAH-I.chart_45
**Chart 45 (Under-Secretary Rs. 1000+/month, Yoga Karaka Saturn)**

### Birth Data
- **DateTime:** 1898-01-22T22:07:00
- **Timezone:** 5.35 (= lon/15 = 80.25/15)
- **Lat/Lon:** 13.0667, 80.25
- **Decode note:** Long '80 15 E', Lat '13 4 N'. tz=80.25/15=5.35.

### Verdict
- **Signification:** wealth
- **Expected verdict:** favourable
- **Raman's reasoning:** Libra 2nd un-afflicted, fairly well disposed; 2nd lord Venus in 5th; from Moon, Saturn (2nd lord from Moon) in 11th and is Yoga Karaka from Moon; favourable finances; became Under-Secretary to Central Government in Saturn Dasha, salary over Rs. 1000/month.
- **Citations:** ['HTJAH-I:2850-2873']

### Your Review
- [ ] Birth data correct
- [ ] Verdict correct
- [ ] Signification correct
- **Decision:** _CONFIRMED / REJECT / FIX: ___

---

## Chart 9: HTJAH-I.chart_46
**Chart 46 (Financially sound via Chandramangala Yoga)**

### Birth Data
- **DateTime:** 1891-01-30T19:00:00
- **Timezone:** 5.1722 (= lon/15 = 77.5833/15)
- **Lat/Lon:** 13.0, 77.5833
- **Decode note:** Long '5h 10m 20s E' = 77.5833 deg E. Time '7-0 p.m.'.

### Verdict
- **Signification:** wealth
- **Expected verdict:** favourable
- **Raman's reasoning:** Saturn in 2nd aspected by Jupiter (6L+9L); 2nd lord Sun in 7th in inimical sign (ordinary); but Mars-Moon mutual aspect forms Chandramangala Yoga -- Mars is Yoga-Karaka, Moon is Lagna-lord; Moon in 3rd, Mars in 9th; Dhana-Karaka in 8th (adverse) but yoga gains strength; financially sound.
- **Citations:** ['HTJAH-I:2898-2912']

### Your Review
- [ ] Birth data correct
- [ ] Verdict correct
- [ ] Signification correct
- **Decision:** _CONFIRMED / REJECT / FIX: ___

---

## Chart 10: HTJAH-I.chart_48
**Chart 48 (Moderate wealth by hard labour, govt loss)**

### Birth Data
- **DateTime:** 1887-10-21T03:10:00
- **Timezone:** 5.7611 (= lon/15 = 86.4167/15)
- **Lat/Lon:** 25.3333, 86.4167
- **Decode note:** Long '5h 45m 40s E' = 86.4167 deg E. Time 'about 3-10 a.m.' (approximate). Date '20/21-10-1887' -> 21st.

### Verdict
- **Signification:** wealth
- **Expected verdict:** mixed
- **Raman's reasoning:** Virgo 2nd aspected by Saturn (6L+7L, neutral); 2nd lord Mercury in 3rd with Jupiter (5L+8L) in friendly sign; Dhana-Karaka Jupiter with 2nd lord but in inimical sign; 6th lord aspects house of finance; wealth not very considerable, acquired by hard labour; navamsa Rahu in 2nd + 2nd lord in 12th indicates loss via Government displeasure.
- **Citations:** ['HTJAH-I:2923-2943']

### Your Review
- [ ] Birth data correct
- [ ] Verdict correct
- [ ] Signification correct
- **Decision:** _CONFIRMED / REJECT / FIX: ___

---

## Chart 11: HTJAH-I.chart_49
**Chart 49 (New Method, earns well in Jupiter Dasha)**

### Birth Data
- **DateTime:** 1912-08-08T19:35:00
- **Timezone:** 5.5 (= lon/15 = 77.5833/15)
- **Lat/Lon:** 13.0667, 77.5833
- **Decode note:** IST explicitly stated (tz 5.5). Same nativity as chart 10 (H1 golden) -- different house tested. Long '5h 10m 20s E', Lat '13 4 N'.

### Verdict
- **Signification:** wealth
- **Expected verdict:** favourable
- **Raman's reasoning:** Special Dhana Lagna = Taurus (root numbers: Venus 12 + Saturn 1 = 13, remainder 1 from Taurus Moon); two malefics on Dhana Lagna aspected by Jupiter; Moon exalted; earns well in Jupiter Dasha; Saturn (pure malefic on it) gives better prospects; Saturn-Dasa Moon-Bhukti decisively favourable.
- **Citations:** ['HTJAH-I:3274-3293']

### Your Review
- [ ] Birth data correct
- [ ] Verdict correct
- [ ] Signification correct
- **Decision:** _CONFIRMED / REJECT / FIX: ___

---

## Chart 12: HTJAH-I.chart_50
**Chart 50 (Aristocrat reduced to poverty, debt, mental torture)**

### Birth Data
- **DateTime:** 1883-04-15T13:30:00
- **Timezone:** 4.6667 (= lon/15 = 70.0/15)
- **Lat/Lon:** 30.0, 70.0
- **Decode note:** Long '70 E' degrees. Lat '30 N'. tz=70/15=4.6667.

### Verdict
- **Signification:** wealth
- **Expected verdict:** afflicted
- **Raman's reasoning:** Special Dhana Lagna = Libra (root numbers: Mars 6 + Jupiter 10 = 16, remainder 4 from Cancer Moon); Rahu on Dhana Lagna aspected by Sun, combust Mercury, Ketu; incendiary node on Dhana Lagna with weakened aspects; once an aristocrat, now reduced to poverty, debts and mental torture.
- **Citations:** ['HTJAH-I:3295-3303']

### Your Review
- [ ] Birth data correct
- [ ] Verdict correct
- [ ] Signification correct
- **Decision:** _CONFIRMED / REJECT / FIX: ___

---

## Chart 13: HTJAH-I.chart_51
**Chart 51 (New Method, commands lakhs of rupees)**

### Birth Data
- **DateTime:** 1887-08-07T13:30:00
- **Timezone:** 5.1333 (= lon/15 = 77.0/15)
- **Lat/Lon:** 11.0, 77.0
- **Decode note:** Long '5h 8m E' = 77.0 deg E. tz=77/15=5.1333.

### Verdict
- **Signification:** wealth
- **Expected verdict:** favourable
- **Raman's reasoning:** Special Dhana Lagna = Sagittarius (root numbers: Moon 16 + Mars 6 = 22, remainder 10 from Pisces Moon); pure malefic Mars aspects Dhana Lagna; Venus (exalted in Navamsa) in the 10th from Dhana Lagna; commands lakhs of rupees; Venus Dasha gave immense wealth.
- **Citations:** ['HTJAH-I:3307-3318']

### Your Review
- [ ] Birth data correct
- [ ] Verdict correct
- [ ] Signification correct
- **Decision:** _CONFIRMED / REJECT / FIX: ___

---
