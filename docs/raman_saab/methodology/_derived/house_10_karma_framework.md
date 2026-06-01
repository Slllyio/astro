---
house: 10
name: Tenth House
sanskrit: Karma / Karya Bhava
karaka:
  - Sun (Career / Authority)
  - Mars (Activity / Work)
  - Mercury (Skill / Business)
special_varga: [D9]
source: HTJAH-II:5683-7164
---

# House 10 Framework — Karma / Karya Bhava

This document defines Raman's tenth-house engine logic. It is centered on
**profession, vocation, reputation, authority, and public life**.

## 1. Executive summary

- The 10th house is the house of **career, action, and public reputation**.
- Raman's chapter uses a **multi-karaka model** that includes the Sun,
  Mars, Mercury, and the 10th lord.
- The engine should compute:
  - `career_type`
  - `professional_strength`
  - `public_reputation_flag`
  - `authority_potential`
  - `success_period_flag`
  - `service_or_command_flag`
  - `business_and_trade_flag`
  - `job_change_risk`
- The 10th lord's placement in the 12 houses is fundamental for vocation and
  social outcome.
- Navamsa is mandatory for reputation and professional promise.

## 2. Core engine architecture

### 2.1 Primary evaluation frames

1. **Rasi 10th House frame**
   - Evaluate incumbents, aspects, and public/work significance.
2. **10th Lord frame**
   - Assess house placement, dignity, and aspect relationships.
3. **Sun frame**
   - Authority, honours, and leadership.
4. **Mars frame**
   - Activity, power, and executive energy.
5. **Mercury frame**
   - Skill, business, communication, and accounting.
6. **Navamsa frame (D9)**
   - Confirm professional promise, status, and reputation.

### 2.2 Pillars of judgment

- **10th House** — the central work and status house.
- **10th Lord** — its placement and strength.
- **Sun, Mars, Mercury** — multiple career karakas.
- **Occupants** — planets in 10th and their associations.
- **Supporting** — 2nd, 6th, 7th, and 11th house relationships.

### 2.3 Output dimensions

- `career_type`
- `authority_score`
- `public_status_flag`
- `executive_energy_score`
- `business_skill_flag`
- `service_career_flag`
- `promotion_timing_flag`
- `short_term_job_change_risk`

## 3. Rule ordering and precedence

1. **Assess the 10th and the 10th lord together.**
2. **Use the Sun for leadership and public reputation.**
3. **Use Mars for work, power, and executive action.**
4. **Use Mercury for business, trade, and technical skill.**
5. **Confirm with Navamsa for stable reputation and external success.**
6. **If the 10th lord is in a Kendra or Trikona exchange, favour Rajayoga and
   strong public status.**

## 4. House-10 scoring architecture

### 4.1 Core score components

- `tenth_house_strength`
- `tenth_lord_strength`
- `sun_authority_strength`
- `mars_activity_strength`
- `mercury_skill_strength`
- `navamsa_profession_modifier`
- `career_stability_score`

### 4.2 Aggregation

- `professional_strength` = weighted combination of 10th house, 10th lord, and
  career karakas.
- `authority_potential` = Sun + 10th lord influence.
- `business_and_trade_flag` = Mercury + benefics in 10th + 2nd/11th support.
- `service_or_command_flag` = Mars + 10th lord placement in 1st/6th/10th.
- `public_reputation_flag` = Navamsa-supported Sun/10th lord strength.

### 4.3 Recommended weights

- 10th House: 25%
- 10th Lord: 25%
- Sun: 20%
- Mars: 15%
- Mercury: 10%
- Navamsa: 5%

If the 10th lord is weak but the Sun is strong in the 10th, favour authoritative
public work over secure career stability.

## 5. Key House-10 rule categories

### 5.1 10th Lord placements

- **Lagna** — high honor, administrative ability, self-employed authority.
- **2nd** — financial gain through profession, good oratory, speech-based career.
- **3rd** — travel, trade, writing, service, perhaps military.
- **4th** — land/properties, service, dignity in family.
- **5th** — education, religion, author, high-status creative work.
- **6th** — service, litigation, hospitals, competition.
- **7th** — partnership, business, marriage-related career.
- **8th** — sudden changes, research, insurance, occult work.
- **9th** — foreign service, publishing, teaching, religious office.
- **10th** — high authority, leadership, political/military career.
- **11th** — wealth through work, gains, networks, corporate success.
- **12th** — secret work, exile, confinement, philanthropy.

### 5.2 Important combinations

- 10th lord in 10th with benefics → strong career and honor.
- 10th lord in 2nd → speech, banking, and family business.
- 10th lord in 3rd → travel, action, commerce.
- 10th lord in 6th with Mars → government service or litigation work.
- 10th lord in 7th → partnership, diplomacy, foreign business.
- 10th lord in 8th → research, hidden industries, sudden fame.
- Sun/Mars/Mercury in 10th with strong 10th lord → successful and respected
  vocation.
- 10th lord afflicted in 2nd or 12th → unstable work, marriage or health-related
  professional problems.

### 5.3 Career type signals

- **Sun** — government, administration, politics, leadership.
- **Mars** — military, surgery, police, engineering, manual work.
- **Mercury** — commerce, writing, teaching, accounting, analysis.
- **Venus** — arts, luxury, design, beauty, pleasure industries.
- **Jupiter** — teaching, law, religion, medicine.
- **Saturn** — industry, labor, age-related authority, discipline.

### 5.4 Rajayoga and professional success

- Rajayoga if the 10th lord is strong and associated with Lagna, 9th, or 5th
  lord.
- Mutual exchange involving the 10th lord and a Kendra or Trikona often boosts
  status.
- 10th lord in 1st or with the Sun signals visible success and public recognition.

### 5.5 Career type matrix by 10th lord placement

- **10th lord in 1st** — self-employed authority, leadership roles, personal
  brand.
- **10th lord in 2nd** — speech, writing, finance, family business.
- **10th lord in 3rd** — travel, journalism, sales, military.
- **10th lord in 4th** — land, real estate, politics, education.
- **10th lord in 5th** — teaching, publishing, creative work.
- **10th lord in 6th** — service, litigation, healthcare, competition.
- **10th lord in 7th** — diplomacy, law, foreign trade, partnerships.
- **10th lord in 8th** — research, insurance, occult professions, sudden change.
- **10th lord in 9th** — religion, law, higher studies, foreign affairs.
- **10th lord in 11th** — corporate success, networking, income through work.
- **10th lord in 12th** — secret service, exile, philanthropy, hospital work.

### 5.6 Rajayoga status ranking

- Rank professional outcomes by the number of strong exchanges involving the
  10th lord and the presence of benefics in kendras/trikonas.
- A weak 10th lord with strong benefic 10th occupancy may still yield respect via
  `public_reputation_flag` but lower `career_stability_score`.
- If the 10th lord is in 1st or 10th and the Sun is strong, prioritize
  `authority_score` over `business_and_trade_flag`.

## 6. Timing and period architecture

- Major factors: 10th lord, planets occupying the 10th, Sun, Mars, Mercury, and
  benefics to the 10th.
- Promotions and public success are more likely when the Dasa/Bhukti lords
  connect to the 10th house or its lord.
- Periods of 10th lord with supporting transit or aspect produce pronounced
  career peaks.

## 7. Engineering notes

- Implement the 10th engine as a **vocation classifier** with separate career
  tracks for authority, service, trade, and intellectual professions.
- Treat the 10th house and 10th lord as the base, with Sun/Mars/Mercury as
  modifiers.
- Use Navamsa to validate reputation and stability.
- Map 10th lord placements directly into career archetypes and then adjust by
  planetary dignity and aspect.
- Output both `career_type` and vectors for `authority`, `service`, and
  `business`.

## 8. Validation anchors

- Sun in 10th with strong 10th lord → leadership and high honor.
- 10th lord in 3rd with Mercury → commerce, travel, or writing work.
- 10th lord in 6th with Mars → service, litigation, or military work.
- 10th lord in 11th with benefics → gaining through profession.
- 10th lord in 8th with Rahu → research or occult profession and sudden change.
