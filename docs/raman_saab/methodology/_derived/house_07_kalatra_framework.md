---
house: 7
name: Seventh House
sanskrit: Kalatra / Yuvati Bhava
karaka: Venus (Kalatra-Karaka)
special_varga: [D9]
source: HTJAH-II:198-2883
---

# House 7 Framework — Kalatra / Yuvati Bhava

This document is the engine blueprint for Raman's seventh-house chapter. It
focuses on marriage, spouse character, partnership, sexuality, and the 7th house's
maraka nature.

## 1. Executive summary

- The 7th house is principally about **marriage and spouse** and secondarily
  about business partnership, diplomacy, and foreign residence.
- Raman emphasizes that the 7th is also a **maraka house**; marital indicators may
  time death or loss as well as marriage.
- The engine should compute:
  - `marriage_potential`
  - `spouse_quality_flag`
  - `marital_happiness`
  - `multiple_marriage_risk`
  - `sexual_health_risk`
  - `partner_death_risk`
  - `foreign_partnership_flag`
  - `maraka_period_flag`
- The primary karaka is **Venus**, but Venus must be read both as a planet and as
  a Lagna in the **from-Venus frame**.
- Navamsa is mandatory, especially for spouse quality and 6/8/12-from-Venus tests.

## 2. Core engine architecture

### 2.1 Primary evaluation frames

1. **Rasi 7th House frame**
   - Evaluate the house, occupancy, aspects, and benefic/malefic tenor.
2. **7th Lord frame**
   - Evaluate placement, strength, and associations of the 7th lord.
3. **Venus-as-Lagna frame**
   - Read from Venus as if Venus were Lagna: 4th/7th/8th/12th from Venus.
4. **Navamsa frame (D9)**
   - Essential for spouse quality and marital timing.
5. **Moon frame**
   - Read the 7th from the Moon in parallel for confirmation.

### 2.2 Pillars of judgment

- **7th House** — the core marriage house.
- **7th Lord** — its placement and functional strength.
- **Venus-as-Lagna** — for spouse death, happiness, and impotency tests.
- **Occupants** — planets in the 7th and their associations.

### 2.3 Output dimensions

- `marriage_potential`
- `spouse_quality_flag`
- `marital_happiness`
- `multiple_marriage_risk`
- `sexual_dysfunction_flag`
- `spouse_death_risk`
- `foreign_residence_flag`
- `maraka_death_flag`
- `dowry_or_wealth_from_wife_flag`
- `partner_character_flag`

## 3. Rule ordering and precedence

1. **Assess the 7th and the 7th lord.**
2. **Evaluate Venus as both planet and Lagna.**
3. **Check the 7th from Venus for danger to spouse** and for impotency.
4. **Use Navamsa for the quality and number of marriages.**
5. **Maraka logic is mandatory**: if the 7th is afflicted while the Lagna lord
   is weak, treat the configuration as potentially death-timing.

## 4. House-7 scoring architecture

### 4.1 Core score components

- `seventh_house_strength`
- `seventh_lord_strength`
- `venus_karaka_strength`
- `from_venus_malefic_count`
- `navamsa_marriage_quality`
- `moon_frame_confirmation`
- `maraka_penalty`

### 4.2 Aggregation

- `marriage_potential` = weighted sum of 7th house, 7th lord, and Venus strength.
- `spouse_quality_flag` = reduced when Venus or 7th lord is afflicted.
- `marital_happiness` = enhanced by benefics in 7th, Jupiter/Venus support,
  and good 7th-from-Venus frame.
- `spouse_death_risk` = high when malefics occupy 4th/8th/12th from Venus or when
  Mars/Saturn afflict the house/karaka.

### 4.3 Recommended weights

- 7th House: 30%
- 7th Lord: 30%
- Venus: 25%
- Venus-as-Lagna frame: 15%

If malefics occupy 4th/8th/12th from Venus, apply a severe marital/happiness
penalty.

## 5. Key House-7 rule categories

### 5.1 7th Lord placements

- **Lagna** — stable marriage with someone known early in life.
- **2nd** — wealth through marriage, morality questions, possible multiple
  partners.
- **3rd** — foreign marriage, brotherly support, strong travel component.
- **4th** — comfortable, educated spouse, but potential home unrest.
- **5th** — early marriage, affluent partner, possible issue issues if afflic-
  ted.
- **6th** — cousin marriage, doubtful spouse, disease, multiple unions.
- **7th** — charming spouse or loneliness if weak.
- **8th** — partner loss, separation, suffering abroad.
- **9th** — foreign success, religious/spiritual partner.
- **10th** — successful career spouse, diplomatic/professional partner.
- **11th** — many partners or one wealthy partner.
- **12th** — spiritual or distant marriage, separation, wandering spouse.

### 5.2 Important combinations

- 7th in benefic/strong sign → happy marriage.
- 7th lord in 5th/9th with benefics → favorable partner and children.
- Malefics in 4th/8th/12th from Venus → spouse dies soon.
- Saturn in 6th/8th from Venus → impotency.
- 2nd & 7th lords in depression with benefics in kendras → one marriage only.
- 7th lord weak + malefics in 7th → additional marriages or separation.
- Venus in 7th is positive, not destructive, unless heavily afflicted.

### 5.3 Partner character and sexual health

- Moon in 7th in malefic sign → wicked spouse.
- Ketu in 7th → shrewish or outcaste partner.
- Saturn in 7th with weak Venus → barren or impotent configuration.
- Mars in 7th → spouse may die or there may be sexual disease.
- Venus+Saturn in 10th/8th → impotency, especially without benefic aspect.

### 5.4 Multiple marriages and timing

- 7th lord in common/dual signs or mutual Venus/Mars patterns → multiple
  marriages.
- 7th lord weak/in afflicted Navamsa → second wife while first still alive.
- 2nd, 7th, 10th lords in the 7th → many wives.
- 7th from Moon and 7th from Venus can produce parallel marriage indicators.

### 5.5 Venus-as-Lagna danger table

- **4th from Venus malefic** → spouse death, domestic grief.
- **8th from Venus malefic** → marital suffering, partner illness, divorce.
- **12th from Venus malefic** → impotence, separation, exile.
- **4th/8th/12th from Venus benefic** → spouse health and hidden support.
- Use a separate `from_venus_penalty` when any of these positions are occupied by
  Mars, Saturn, Rahu, or Ketu.

### 5.6 Partner character matrix

- Venus strong + Moon strong → kind, affectionate spouse.
- Venus afflicted + Mars strong → violent or domineering spouse.
- Saturn in 7th with weak Venus → cold, distant, or barren partner.
- Ketu in 7th → unconventional, detached, or foreign partner.
- Sun in 7th → authoritative, proud, or fatherly spouse.

### 5.7 Multiple-marriage and separation rules

- Use `multiple_marriage_risk` when the 7th lord is weak and the 2nd/7th/10th
  lords are all in movable or dual signs.
- If the 7th lord is in 6th/8th/12th and Venus is afflicted, raise both
  `multiple_marriage_risk` and `partner_death_risk`.
- If the 7th is strong but the 7th lord is weak, expect separation or late
  second marriage rather than early divorce.

## 6. Timing and period architecture

- Major factors: 7th lord, Venus, planets in 7th, and the 7th from the Moon.
- **Maraka periods** appear during the Dasa of the Lagna lord if it is weak and
  the 7th is afflicted.
- **Marriage occurs** in the Dasa of 7th-related planets or planets influencing
  the 7th house.

## 7. Engineering notes

- **Implement Venus-as-Lagna** exactly; the 4th/7th/8th/12th from Venus are
  decisive for spouse death/happiness/impotency.
- Treat the 7th as a **two-faced house**: marriage and maraka. Carry a separate
  `maraka_death_flag`.
- **Navamsa is mandatory** for partner quality and the number of marriages.
- Do not reject Venus in 7th as inherently bad; it is usually favourable unless
  malefic.
- Model `multiple_marriage_risk` and `spouse_death_risk` independently.
- For spouse character, combine Venus, Moon, Mars, and Saturn readings.

## 8. Validation anchors

- Venus exalted/in own varga and 7th strong → happy marriage.
- Malefics in 4th/8th/12th from Venus → wife dies soon.
- Saturn in 6th/8th from Venus → impotency.
- 7th lord in 7th or Lagna → strong partnership, especially with benefics.
- 2nd & 7th with malefics → money or moral trouble via marriage.
