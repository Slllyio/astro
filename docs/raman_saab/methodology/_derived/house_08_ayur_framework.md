---
house: 8
name: Eighth House
sanskrit: Ayur / Mrityu Bhava
karaka:
  - Saturn (Ayur-Karaka)
  - Rahu/Ketu (death, sudden events)
special_varga: [D8, D60, D3, D9]
source: HTJAH-II:2884-4226
---

# House 8 Framework — Ayur / Mrityu Bhava

This document defines Raman's eighth-house engine logic. It centers on
**longevity, death, transformation, secrets, and sudden misfortune**.

## 1. Executive summary

- The 8th house is primarily a **death/longevity house** and secondarily a house
  of **secrets, inheritance, and transformations**.
- Raman uses **Saturn as the main dual karaka** for the 8th, with Rahu/Ketu and
  the ascendant lord playing vital supporting roles.
- The engine should produce:
  - `longevity_rating`
  - `sudden_death_risk`
  - `hidden_crisis_flag`
  - `inheritance_flag`
  - `recovery_after_loss_flag`
  - `inherited_obstacle_flag`
  - `death_kind_score`
- Special vargas: D8 for death timing, D60 for hidden karmic issues, D3 for
  sibling-related life threads, and D9 for overall promise.

## 2. Core engine architecture

### 2.1 Primary evaluation frames

1. **Rasi 8th House frame**
   - Evaluate the 8th house, occupants, and aspects.
2. **8th Lord frame**
   - Assess the 8th lord by house placement, strength, and associations.
3. **Saturn / Ayur-Karaka frame**
   - Saturn is the decisive karaka for longevity and chronic afflictions.
4. **Rahu/Ketu sudden-death frame**
   - Rahu/Ketu patterns signal sudden, hidden, or occult death events.
5. **D8 and D60 frames**
   - D8 for death timing, D60 for hidden weaknesses and the quality of life.
6. **Navamsa frame (D9)**
   - Required for confirmation of strong/weak life conclusions.

### 2.2 Pillars of judgment

- **8th House** — core transformation and longevity house.
- **8th Lord** — its placement, condition, and associations.
- **Saturn** — longevity karaka and chronic adversity indicator.
- **Rahu/Ketu** — sudden, secretive, and karmic death signatures.
- **Supporting** — ascendant lord, 1st, 2nd, 4th, 6th, and 12th house links.

### 2.3 Output dimensions

- `longevity_rating`
- `sudden_death_risk`
- `death_by_violence_flag`
- `death_by_illness_flag`
- `inheritance_and_shared_wealth_flag`
- `hidden_crisis_flag`
- `mate_loss_risk`
- `secret_adversity_score`
- `spiritual_transformation_flag`

## 3. Rule ordering and precedence

1. **Assess Saturn and the 8th house together.**
2. **If Saturn is also the 8th lord, treat it as the dominant life indicator.**
3. **Use D8 to time death or major crisis.**
4. **Use D60 to validate hidden or karmic weaknesses.**
5. **Rahu/Ketu patterns override ordinary timing when they are strongly placed
   in the 8th or 2nd/12th houses.**
6. **Always confirm with Navamsa (D9) before making longevity declarations.**

## 4. House-8 scoring architecture

### 4.1 Core score components

- `eighth_house_strength`
- `eighth_lord_strength`
- `saturn_ayur_strength`
- `rahu_ketu_suddenness`
- `d8_timing_score`
- `d60_karmic_penalty`
- `navamsa_confirmation`
- `hidden_crisis_score`

### 4.2 Aggregation

- `longevity_rating` = inverse of combined death risk signals moderated by
  Saturn and D60.
- `sudden_death_risk` = high when Rahu/Ketu strongly influence the 8th or when
  8th lord is malefic and afflicted.
- `inheritance_flag` = positive when the 8th lord is strong, benefics are in the
  8th, or 2nd/4th/9th lord relationships exist.
- `hidden_crisis_flag` = raised by secretive planets in the 8th and D60
  afflictions.

### 4.3 Recommended weights

- 8th House: 25%
- 8th Lord: 25%
- Saturn: 25%
- Rahu/Ketu: 15%
- D8/D60: 10%

If `d8_timing_score` is high, increase death risk sharply during the identified
period.

## 5. Key House-8 rule categories

### 5.1 8th Lord placements

- **Lagna** — great birth, tall, wealthy; may lose health later.
- **2nd** — wealth through spouse, danger from speech, sudden leg problems.
- **3rd** — action, accidents, sudden expenses, wealth by cunning.
- **4th** — inheritance or maternal death; comfortable later life.
- **5th** — religious/spiritual offspring, possible death in holy place.
- **6th** — disease, hospital, surgical operations.
- **7th** — violent death by partner or spouse trouble.
- **8th** — strong rebirth potential or sudden death.
- **9th** — religious/foreign death, long journeys.
- **10th** — public disgrace or death by authority.
- **11th** — late gains, surprising support, estate recovery.
- **12th** — loss of wealth, death in exile or prison.

### 5.2 Important combinations

- 8th lord in Lagna with benefics → unexpected fortune and strong longevity.
- 8th lord in 6th with malefics → chronic illness and hospital stays.
- Saturn in 8th well-placed → recovery, long suffering, mystical power.
- Rahu in 8th → sudden hidden death, occult power, foreign or aquatic demise.
- 8th lord in 12th → foreign/secretive death.
- 4th/8th lord relationship → inherited estate or ancestral loss.

### 5.3 Planet-in-8th archetypes

- **Sun** — hidden authority, heart problems if afflicted.
- **Moon** — secret grief, water or stomach problems.
- **Mars** — surgery, burns, or violent incidents.
- **Mercury** — nervous tension, kidney/nervous system issues.
- **Jupiter** — delayed adversity, hidden wealth, spiritual protection.
- **Venus** — secret pleasures, hidden sexuality, possible sexual illness.
- **Saturn** — chronic disease, endurance, possible hidden mastery.
- **Rahu** — occult influence, sudden crisis, foreign demise.
- **Ketu** — detachment, loss of wealth, strange death.

### 5.4 Longevity and death type

- Use Saturn as the primary longevity ruler; a weak Saturn suggests a shorter
  life regardless of ordinary benefic signals.
- Rahu/Ketu patterns in the 8th or 12th can signal sudden or unnatural death.
- D60 afflictions may shorten life silently through karmic weakness.
- 8th-from-Venus or 8th-from-Moon should be used for death of spouse or close
  relations.

### 5.5 D60 hidden karmic weakness rules

- Treat D60 as a hidden-karmic validator for any serious 8th-house judgement.
- If D60 contains malefic planets or an afflicted 8th-lord placement, increase
  `hidden_crisis_flag` and lower `longevity_rating` regardless of Rasi signals.
- D60 support can save an otherwise weak 8th house; if D60 is strong, reduce
  sudden-death risk by 20% and raise recovery probability.
- Use D60 to distinguish declared crises from karmic weakness that may not
  materialize until later life.

### 5.6 Rahu/Ketu sudden death taxonomy

- **Rahu in 8th** → sudden death by accident, foreign or water-related cause.
- **Ketu in 8th** → hidden illness, isolation before death, spiritual detachment.
- **Rahu in 2nd/12th** → speech-related or foreign sudden crisis.
- **Ketu in 2nd/12th** → secret loss, exile, or subconscious self-sabotage.
- If Rahu/Ketu are also the 8th lord, treat the death signal as both sudden and
  karmic; raise `death_kind_score` for unnatural causes.

## 6. Timing and period architecture

- Major factors: 8th lord, Saturn, Rahu/Ketu, planets in the 8th, and D8/D60
  signals.
- D8 is mandatory for death timing and crisis peaks.
- D60 is necessary for hidden karmic quality and to validate unusual
  configurations.
- If D8 and D60 both signal risk in the same period, treat it as a strong crisis
  or death window.

## 7. Engineering notes

- Implement an **8th longevity engine** where Saturn and 8th lord are core.
- Include D60 as a hidden-karmic validator; do not rely solely on ordinary house
  placements.
- Treat Rahu/Ketu separately: they are not ordinary benefics or malefics in the
  8th but suddenness indicators.
- Record both `longevity_rating` and `inheritance_flag` separately.
- Use the 8th lord's office to determine the kind of difficult event: illness,
  partner loss, foreign danger, or secrecy.
- Validate with 8th lord in Lagna and 8th lord in 6th patterns.

## 8. Validation anchors

- Saturn well-placed in 8th → long but difficult life.
- Rahu in 8th with 8th lord afflicted → sudden death.
- 8th lord in 12th with malefic influence → foreign or secret loss.
- D8 with a strong malefic → confirmed death/crisis period.
- D60 afflictions matching Rasi signals → hidden karmic vulnerability.
