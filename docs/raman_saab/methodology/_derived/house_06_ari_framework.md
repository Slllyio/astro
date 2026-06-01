---
house: 6
name: Sixth House
sanskrit: Ari / Roga / Shatru / Rina Bhava
karaka:
  - Mars (Roga-Karaka)
  - Saturn (Ayush/Ayush-Karaka)
special_varga: [D9, D3]
source: HTJAH-I:5982-6967
---

# House 6 Framework — Ari / Roga / Shatru / Rina Bhava

This document captures Raman's sixth-house methodology for disease, enemies,
debts, litigation, and misfortunes. The 6th is a dusthana and its logic is inverted
compared to benefic houses.

## 1. Executive summary

- The 6th house governs **diseases, debts, enemies, litigation, and service**.
- It is a dusthana: **malefics in the 6th are protective; benefics are often
  harmful for the 6th's enemy-related matters**.
- The engine should compute:
  - `disease_risk`
  - `enemy_count_flag`
  - `debt_risk`
  - `litigation_risk`
  - `service_career_flag`
  - `maternal_uncle_influence`
  - `mental_affliction_risk`
- The chapter uses two karakas: **Mars for disease/enemies** and **Saturn for
  the dusthana's sorrow/debt function**.
- Mandatory frames include Navamsa and the 6th-from-Moon reading.

## 2. Core engine architecture

### 2.1 Primary evaluation frames

1. **Rasi 6th House frame**
   - Evaluate occupancy, benefic/malefic disposition, and the dusthana inversion.
2. **6th Lord frame**
   - Evaluate house placement, strength, and associations.
3. **Mars / Roga-Karaka frame**
   - Evaluate Mars as primary disease indicator.
4. **Saturn / Ayush-Karaka frame**
   - Evaluate Saturn for long-term debt, disease, and longevity-of-suffering logic.
5. **Moon and Mercury frames**
   - Moon first for mind; Mercury for nerves and mental health.
6. **Navamsa frame (D9)**
   - Mandatory for disease moderation and timing reversal.

### 2.2 Pillars of judgment

- **6th House itself** — dusthana logic and protective inversion.
- **6th Lord** — its placement and malefic functional status.
- **Mars** — disease and enemies.
- **Saturn** — sorrow, debts, chronic illness, and Ayushkaraka.
- **Secondary** — 6th from Moon and associated yogas.

### 2.3 Output dimensions

- `disease_risk`
- `chronic_illness_flag`
- `mental_health_risk`
- `debt_risk`
- `enemy_tendency_flag`
- `litigation_risk`
- `service_employment_flag`
- `maternal_uncle_influence`
- `maraka_event_risk`

## 3. Rule ordering and precedence

1. **Assess the 6th first as a dusthana.**
2. **Evaluate Mars and Saturn together; both are karakas.**
3. **Read the 6th-from-Moon as a parallel secondary frame.**
4. **If evil planets occupy the 6th, decrease enemy count but increase disease
   potential in a protective sense.**
5. **If benefic planets occupy/aspect the 6th, the number of enemies may
   increase.**
6. **Use Navamsa to moderate strong or weak disease signatures.**

## 4. House-6 scoring architecture

### 4.1 Core score components

- `sixth_house_strength`
- `sixth_lord_strength`
- `mars_rogakaraka_strength`
- `saturn_ayush_strength`
- `moon_mind_strength`
- `mercury_nervous_strength`
- `navamsa_mitigation`
- `debt_penalty`
- `enemy_inversion_factor`

### 4.2 Aggregation

- `disease_risk` = high if Mars/Saturn are afflicted in the 6th or if the 6th
  is occupied by evil planets with poor Moon/Mercury support.
- `enemy_tendency_flag` = low when evil planets occupy the 6th; high when
  benefics occupy/aspect it.
- `debt_risk` = high when Saturn is weak or 6th/12th/2nd lords combine badly.
- `litigation_risk` = high when 6th lord is afflictive and associated with Mars.

### 4.3 Recommended weights

- 6th House: 30%
- 6th Lord: 30%
- Mars: 20%
- Saturn: 15%
- Moon/Mercury: 5%

If `enemy_inversion_factor` is triggered, invert the sign of the enemy score.

## 5. Key House-6 rule categories

### 5.1 6th Lord placements

- **Lagna** — army/police/hospital service; can become criminal if weak.
- **2nd** — money loss, defective vision, family stress.
- **3rd** — sibling enmity, illness in siblings, no younger brothers.
- **4th** — miserable domestic life, education failure.
- **5th** — sickly children, possible maternal uncle fortune.
- **6th** — Rajayoga if strong; if weak, disease and enmity.
- **7th** — marriage to cousin, doubtful spouse character when afflicted.
- **8th** — debts, loathsome diseases, and unpleasant circumstances.
- **9th** — father may be judge, maternal uncle strong; weak → poverty.
- **10th** — destructive conduct, possible dismissal.
- **11th** — litigation success if benefic; poor reputation if afflicted.
- **12th** — miserable existence, chronic sorrow.

### 5.2 Important combinations

- Evil lord of 6th in Lagna/8th/10th → boils.
- 6th lord with Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn in Lagna → specific
  disease types.
- 6th lord in 6th with Mars and Rahu → loses estates by auction.
- 6th lord in a kendra with Saturn → confinement/imprisonment.
- Moon in 6th with malefics → urgent physical weakness and service.
- Ketu in 6th → best position for Ketu; foeless and protective.
- Saturn or Mars in 6th augmented by malefics → strong but harsh disease profile.

### 5.3 Planet-in-6th archetypes

- **Sun** — political success, wealth; if afflicted → long troublesome illness.
- **Moon** — childhood illness, subordinate success, stomach or mental trouble.
- **Mars** — strong in adversity, possible accidents, legal trouble.
- **Mercury** — smart but nervous; risk of mental breakdown.
- **Jupiter** — dyspepsia, inactive, feared by enemies.
- **Venus** — no enemies, sexual health issues when afflicted.
- **Saturn** — courageous, foeless, chronic illness if afflicted.
- **Rahu** — puzzling illnesses, scandal, foreign wealth.
- **Ketu** — excellent position; intuitive, authority, and occult strength.

### 5.4 Debt and litigation

- 6th lord in 6th with Mars/Rahu → financial loss.
- Parivarthana between 6th and 12th lords → colic and debt years.
- 6th lord in 6th aspected by benefics → enemies may appear actively.
- 6th lord in 6th with Saturn → litigation and hospital service.

### 5.5 Disease and enemy inversion algorithm

- Treat the 6th as a dusthana inversion layer: benefics in the 6th often raise
  enemy and litigation risk, while malefics can reduce open hostility but raise
  disease risk.
- Compute:
  - `enemy_tendency_flag` from benefics and 6th-lord strength.
  - `disease_risk` from malefics, Mars, Saturn, and Moon/Mercury weakness.
- If the 6th is occupied by two or more malefics, apply a `protective_enemy_bonus`
  and increase `disease_risk`.
- If the 6th is occupied by benefics with weak 6th lord, raise `enemy_count_flag`
  and lower the immediate disease severity.

### 5.6 6th lord illness and service taxonomy

- **6th lord in 1st** — health problems through self, claims against self, police
  or hospital service.
- **6th lord in 2nd** — speech disorders, financial stress, family illness.
- **6th lord in 3rd** — sibling or neighbor enmity, nervous disorders.
- **6th lord in 4th** — domestic illnesses, education trouble, maternal service.
- **6th lord in 5th** — child illness, risky recovery, mental stress.
- **6th lord in 6th** — chronic disease, litigation, hospital service.
- **6th lord in 7th** — marital disputes, legal action, health through spouse.
- **6th lord in 8th** — hidden diseases, surgical operations, sudden setbacks.
- **6th lord in 9th** — judicial or religious hospitals, father-related illness.
- **6th lord in 10th** — service career, litigation, public health work.
- **6th lord in 11th** — legal victory after struggle, income from service.
- **6th lord in 12th** — confinement, hospital stays, imprisonment, chronic sorrow.

## 6. Timing and period architecture

- Major factors: 6th lord, planets occupying/aspecting the 6th, Mars, Saturn,
  and Moon/Mercury for mind.
- Disease or litigation results are strongest when both Dasa and Bhukti lords
  influence the 6th.
- Death-in-battle and confinement triggers are special cases with Saturn/Rahu.

## 7. Engineering notes

- Build the 6th engine with a dusthana inversion layer. Mark when benefics in
  6th should increase enemy probability rather than reduce it.
- Include both Mars and Saturn as karaka scores. Mars is the primary disease
  indicator; Saturn is the longer-term misfortune/debt indicator.
- Use the 6th-from-Moon and D9 to moderate results and confirm mental distress.
- Model `enemy_count_flag` separately from `litigation_risk` and `disease_risk`.
- Implement strong disease type mapping from Sun/Moon/Mars/Mercury/Jupiter/Venus
  combinations with the 6th lord.

## 8. Validation anchors

- Malefics in the 6th with no benefic support → fewer enemies, higher disease.
- Benefics in the 6th → more enemies but less serious disease.
- 6th lord in 6th with Mars and Rahu → risk of auction and loss.
- Ketu in 6th → protective and foeless, even if the chart suffers otherwise.
- Saturn in 6th well-placed → enduring work, industry, and government-related
  status.
