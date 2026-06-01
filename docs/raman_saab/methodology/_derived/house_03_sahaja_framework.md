---
house: 3
name: Third House
sanskrit: Sahaja / Bhratru Bhava
karaka: Mars (Kuja / Bhratru-Karaka)
special_varga: [D3, D9]
source: HTJAH-I:3322-4116
---

# House 3 Framework — Sahaja / Bhratru Bhava

This document is the engine framework for Raman's third-house chapter. It is
designed to support judgments about younger siblings, courage, communication,
travel, and the 3rd house's martial and mental signification.

## 1. Executive summary

- The 3rd house is a **younger-siblings / courage / communication / travel** house.
- Raman's evaluation is based on the three pillars: **3rd House / 3rd Lord / Mars
as Karaka**.
- The chapter emphasizes the need to filter the 3rd-lord results for the house's
special meaning, because the lord can carry unrelated house results.
- The sibling-count routine is driven by **Navamsa**, with **D3** as a sibling
representation frame and **D9** as the counting/strength frame.
- The engine should compute both:
  - `younger_sibling_count`
  - `elder_sibling_count`
  - `courage_profile`
  - `speech_and_writing_score`
  - `travel_tendency`
  - `ear_throat_risk`
  - `brother_relationship_flag`

## 2. Core engine architecture

### 2.1 Primary evaluation frames

1. **Rasi 3rd House frame**
   - Evaluate sign on the 3rd house, occupancy, aspects, and benefic/malefic
     disposition.
2. **3rd Lord frame**
   - Evaluate the 3rd lord by placement in the 12 houses, strength, and
     association. Filter the lord's generic outcomes to the 3rd's special
     matters.
3. **Mars / Karaka frame**
   - Mars is the natural karaka for brothers and courage. When Mars is also the
     3rd lord, collapse the frames carefully without double-counting.
4. **Navamsa frame (D9)**
   - Required for sibling count and correction of 3rd-lord results.
5. **Drekkana frame (D3)**
   - Used for sibling matter and corroborates the count of brothers/sisters.

### 2.2 Pillars of judgment

- **3rd House strength** — occupancy, aspects, and hemmed status.
- **3rd Lord strength** — physical placement and karaka associations.
- **Mars condition** — sign, occupation, aspect, and whether Mars is combust or
  hemmed.
- **Secondary** — 11th house for elder brother, Moon for related timing rules,
  and Navamsa for sibling count.

### 2.3 Output dimensions

The engine should emit:

- `younger_sibling_count`
- `elder_sibling_count`
- `brother_family_score`
- `courage_score`
- `communication_quality`
- `travel_and_journey_flag`
- `ear_throat_health_risk`
- `writing_literacy_flag`
- `brotherly_attitude_flag`
- `papakartari_penalty`

## 3. Rule ordering and precedence

1. **Evaluate the 3rd house first**.
2. **Evaluate Mars and the 3rd lord simultaneously**.
3. **If Mars equals the 3rd lord, treat it as one collapsed factor**; then assess
   the same planet's afflictions once.
4. **Use the strongest of {3rd House, 3rd Lord, Mars} for sibling counting**.
5. **Check Navamsa count for the strongest factor**; use D3 as a corroborative
   sibling presence frame.
6. **Apply ear/throat and courage rules before broad sibling verdicts.**
7. **Never read the elder brother from the 3rd**; use the 11th for elder siblings.

## 4. House-3 scoring architecture

### 4.1 Core score components

- `third_house_strength`
- `third_lord_strength`
- `mars_courage_strength`
- `navamsa_sibling_signal`
- `drekkana_sibling_support`
- `communication_risk`
- `travel_motivation`
- `ear_throat_penalty`

### 4.2 Aggregation

- `brother_family_score` = weighted combination of
  `third_house_strength`, `third_lord_strength`, and `mars_courage_strength`.
- `courage_score` = function of Mars + 3rd house benefics and sign quality.
- `speech_and_writing_score` = based on Mercury connections to the 3rd and
  Mars/3rd lord associations.
- `younger_sibling_count` uses the **Navamsa count of the strongest factor**.
- `elder_sibling_count` uses 11th-house counts or elder-brother-specific rules.

### 4.3 Recommended weights

- 3rd House strength: 30%
- 3rd Lord strength: 35%
- Mars/Karaka strength: 35%

If Mars is also 3rd lord, allocate 50% to the collapsed planet and 25% to the
house.

## 5. Key House-3 rule categories

### 5.1 3rd Lord in the 12 houses

Use the placement table as a baseline; modulate by fortification and affliction.

- **Lagna** — arts/acting, self-exertion, fame by performance.
- **2nd** — unscrupulous conduct, mean deeds, family friction.
- **3rd** — courage, wealth, many younger siblings; but Mars/Saturn here can
  cause loss of brothers.
- **4th** — rich, learned, may have step-brother issues.
- **5th** — brotherly support, large agriculture, adoption possibility.
- **6th** — sibling enmity, illness through relatives, possible athletic/army
  career.
- **7th** — brothers abroad, travel, distant relations.
- **8th** — debt, danger to siblings, secretive misfortune.
- **9th** — religious/authorial brother, father issues.
- **10th** — brotherly success, professional distinction.
- **11th** — dependent, vindictive, frequent illness.
- **12th** — sorrow through relatives, property loss.

### 5.2 Important combinations

- **3rd lord well-disposed in 3rd/6th/11th** → many younger brothers.
- **Mars in 3rd** → stronger courage but risk of losing younger brothers.
- **Sun in 3rd** → possible harm to elder brothers.
- **3rd house weak / Mars or 3rd lord afflicted** → few brothers.
- **Mars or 3rd lord debilitated/combust/inimical** → destruction of 3rd-house
  indications.
- **Mars + planets in odd signs** → brothers; odd/even sign rules determine
  gender of siblings.
- **Evil planets in 3rd, especially in D12** → throat/ear defects.
- **Mercury in 3rd** → writing, successful communication, mental sharpness.

### 5.3 Planets in the 3rd house archetypes

- **Sun** — success, resourcefulness, risk of brotherly loss when afflicted.
- **Moon** — travel, changeability, attachment to children, potential cruel
  mental state when waning.
- **Mars** — bravery, accidents, possible ear defects.
- **Mercury** — study, diplomacy, commerce, writing.
- **Jupiter** — good brothers, convention, wealth, possible miserliness.
- **Venus** — arts, beauty, sensuality, possible poor health.
- **Saturn** — courage with gloom, eventual maturity, possible mental
  despondency.
- **Rahu** — sudden events, criticism, misfortune to brothers.
- **Ketu** — adventure, hallucinations, mental disturbance.

### 5.4 Sibling count and elder brother rules

- **Count younger siblings** by the number of Navamsas gained by the strongest of
  {3rd lord, Mars, planets in 3rd}.
- **Count elder brothers** from the **11th house / 11th lord** using the Navamsa
  passage rule.
- **Younger sibling count** is the number of Navamsa still to pass by the 3rd
  Bhava when ranked from the strongest factor.

### 5.5 Sibling gender and D3/D9 algorithm

- **D3** determines the sibling expression frame; it is the first sibling
  signal layer.
- **D9** is the strength/count layer: count the number of strong D9 placements
  from the strongest sibling-related factor.
- If the 3rd lord, Mars, and a planet in the 3rd are all in odd signs, favour
  male brothers; if they are in even signs, favour female sisters.
- A mix of odd and even strong factors indicates a mixed-sibling outcome.
- The engine should compute:
  - `younger_brother_signal`
  - `younger_sister_signal`
  - `younger_sibling_balance`

### 5.6 Elder sibling source discipline

- Do not read elder brothers from the 3rd house itself. The 11th house is the
  proper source for elder siblings.
- When the 3rd lord is in the 11th with benefic support, count younger siblings
  from the 3rd and elder siblings from the 11th, then reconcile the family
  picture.
- If the 11th lord is weak but the 3rd lord is strong, expect strong younger
  sibling influence with weaker elder support.

### 5.7 Mars-as-3rd-lord special handling

- When Mars is both the 3rd lord and the natural karaka, collapse the Mars and
  3rd-lord frames into a single composite signal.
- Apply afflictions once, not twice, and then assign separate sibling and courage
  weights to the composite.
- In this case, reduce the Mars vacillation penalty and increase the courage
  and travel weight by 20%.

## 6. Timing and dasha architecture

- Governing factors: 3rd lord, planets associated with/aspecting the 3rd lord,
  planets occupying/aspecting the 3rd house, Mars, and planets associated with
  Mars.
- **Par excellence** results occur when both major and minor-period lords influence
  the 3rd.
- **Limited results** when only one of the two period lords is connected.
- Dasha triggers for sibling birth are the lords of the 3rd, 9th, 11th, and 7th.

## 7. Engineering notes

- Implement a **three-pillar comparator** and choose the strongest for sibling
  count.
- For **ear/throat health**, use D12 to detect deafness-prone afflictions.
- The engine should prevent **elder-brother attribution from the 3rd**;
  elder siblings belong to the 11th.
- **Mars-as-3rd-lord collapse** is a special case: one planet carries both the
  lord and karaka roles.
- **Navamsa is mandatory** for count and quality; D3 is a supporting frame.
- Read the 3rd from the Moon in every chart as a secondary confirmation.

## 8. Validation anchors

The engine should validate against:

- 3rd lord in 3rd with Mars well-disposed → many younger brothers.
- Mars in 3rd and afflicted 3rd lord → brother loss or sibling misfortune.
- Mercury in 3rd with benefic support → good writing, communication, and
  diplomacy.
- 3rd house or lord afflicted in D12 → throat and ear disease.
- Strong 3rd house with weak lord but strong Mars → courage and travel despite
  sibling deficiencies.
