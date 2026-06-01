---
house: 11
name: Eleventh House
sanskrit: Labha / Artha Bhava
karaka:
  - Jupiter (gain and co-borns)
  - Mars (effort and network)
special_varga: [D9]
source: HTJAH-II:7165-8265
---

# House 11 Framework — Labha / Artha Bhava

This document captures Raman's eleventh-house engine logic. It emphasizes **gains,
income, friends, elder siblings, and ambition**.

## 1. Executive summary

- The 11th house is the house of **profits, gains, elder siblings, and social
  networks**.
- Raman uses a dual-karaka model with **Jupiter for gains and elder sibling
  support** and **Mars for effort and ambition**.
- The engine should compute:
  - `profit_potential`
  - `income_stability`
  - `social_network_strength`
  - `elder_sibling_support_flag`
  - `wish_fulfillment_score`
  - `business_gain_flag`
  - `charity_or_help_flag`
  - `jealousy_risk`
- Navamsa is required for confirming gains and elder-sibling signals.

## 2. Core engine architecture

### 2.1 Primary evaluation frames

1. **Rasi 11th House frame**
   - Evaluate occupancy, aspects, and benefic/malefic disposition.
2. **11th Lord frame**
   - Assess placement and associations of the 11th lord.
3. **Jupiter frame**
   - Evaluate gain and elder-sibling potential.
4. **Mars frame**
   - Evaluate effort, ambition, and income through exertion.
5. **Navamsa frame (D9)**
   - Confirm earned gains and wish fulfillment.

### 2.2 Pillars of judgment

- **11th House** — the core gain house.
- **11th Lord** — placement and strength.
- **Jupiter** — profits, elder support, and wish fulfillment.
- **Mars** — energy, enterprise, and push toward gains.
- **Occupants** — planets in 11th and their associations.

### 2.3 Output dimensions

- `gain_probablity`
- `earned_income_flag`
- `social_support_score`
- `elder_sibling_support_flag`
- `wish_fulfillment_score`
- `business_income_flag`
- `race_or_network_flag`
- `favour_from_older_men_flag`

## 3. Rule ordering and precedence

1. **Assess the 11th and the 11th lord as the first priority.**
2. **Read Jupiter for elder siblings and gains.**
3. **Read Mars for effort-oriented success and the ability to realize gains.**
4. **Use Navamsa to confirm actual gain manifestation and elder-sibling support.**
5. **If the 11th house is weak but the 11th lord is strong in kendras, expect
   gains through effort rather than easy luck.**

## 4. House-11 scoring architecture

### 4.1 Core score components

- `eleventh_house_strength`
- `eleventh_lord_strength`
- `jupiter_gain_strength`
- `mars_effort_strength`
- `navamsa_confirmation`
- `wish_fulfillment_modifier`
- `income_stability_score`

### 4.2 Aggregation

- `profit_potential` = average of 11th house strength, 11th lord strength, and
  Jupiter gain signal.
- `income_stability` = high when 11th lord and Jupiter are well-supported and
  Navamsa is favourable.
- `wish_fulfillment_score` = enhanced by benefics occupying/aspecting the 11th.
- `elder_sibling_support_flag` = positive when Jupiter or 11th lord is strong.

### 4.3 Recommended weights

- 11th House: 30%
- 11th Lord: 30%
- Jupiter: 25%
- Mars: 10%
- Navamsa: 5%

If 11th lord is weak in a kendra with benefics, favour realization of wishes
late rather than early.

## 5. Key House-11 rule categories

### 5.1 11th Lord placements

- **Lagna** — strong gains, honour, elder brother advantage.
- **2nd** — wealth and family income, speech power.
- **3rd** — networking, short journeys, enterprise.
- **4th** — property gains, supportive mother/family.
- **5th** — education-based gains, creativity, intellectual profit.
- **6th** — gain after struggle, litigation success, service pay.
- **7th** — partnership gains, business collaboration.
- **8th** — sudden income, inheritance, gains by accident.
- **9th** — gains through foreign travel, religion, or luck.
- **10th** — career gains, public money, professional reward.
- **11th** — consistent profit and wide networks.
- **12th** — overseas gain, charity, loss through generosity.

### 5.2 Important combinations

- Benefic 11th lord → stable income and wish fulfilment.
- 11th lord in 2nd/11th with Jupiter → good gains and elder-sibling help.
- Mars in 11th with benefics → success through action and ambition.
- 11th lord in 6th → gain through struggle or litigation.
- 11th lord in 12th → foreign income, support from distant friends.
- Jupiter in 11th → social support and elder relative favor.
- 11th in kendra with malefics → gains after effort, with jealousy or rivalry.

### 5.3 Social and elder-sibling archetypes

- Jupiter in 11th → elder sibling support and help from older persons.
- Mars in 11th → ambitious friends, youthful network, competitive circles.
- Sun in 11th → authority among peers, political allies.
- Mercury in 11th → commerce, communication, and marketing networks.
- Venus in 11th → arts patrons, luxury gains, friendly association.
- Saturn in 11th → slow-but-steady gain, older mentors.

### 5.4 Gain types and wish fulfillment

- 11th with strong benefics → wish fulfilment, consistent earning.
- 11th with malefics → inconsistent gains, jealousy, or blocked wishes.
- Jupiter/11th lord connection → large profits through fatherly or mentor
  support.
- 11th lord in 9th → gains through foreign or philosophical work.

### 5.5 Wish fulfillment versus earned gains

- `wish_fulfillment_score` should reflect ease of gain, not just amount.
- When the 11th is strong but the 11th lord is weak, mark gains as more
  aspirational than realized unless Navamsa confirms them.
- Use benefic occupancy in the 11th as the primary wish-fulfilment signal and the
  11th lord's strong house placement as the earned-income signal.
- If the 11th is occupied by Venus and Jupiter, favor spiritual or charitable
  help rather than purely commercial profit.

### 5.6 Elder sibling and co-born support rules

- `elder_sibling_support_flag` should be raised when Jupiter or the 11th lord is
  strong and when the 3rd/4th/5th houses support elder relative resources.
- If Jupiter is weak but the 11th is strong, expect help from friends rather than
  biological elder siblings.
- Use the 11th-from-Moon frame to confirm whether the support is paternal or
  peer-based.
- If the 11th lord is in 2nd/4th/5th, favor family-based gains; if in 3rd/7th/11th,
  favor network-based gains.

## 6. Timing and period architecture

- Major factors: 11th lord, Jupiter, planets in 11th, and benefics to the 11th.
- Gains are most realized when the Dasa/Bhukti lords influence the 11th.
- Wish fulfilment appears when a benefic planet directly aspects or occupies
  the 11th during its period.

## 7. Engineering notes

- Build the 11th engine with a separate gain and elder-sibling support model.
- The 11th house is the source of objective income; the 2nd is the method of
  income retention.
- Model `social_network_strength` independently of `profit_potential`.
- Use Navamsa for confirmation of elder-sibling support and network outcomes.
- Treat Mars as effort and Jupiter as fortune, not as identical gain signals.

## 8. Validation anchors

- Strong Jupiter in 11th with benefics → solid income and elder brother favour.
- 11th lord in 2nd with benefics → stable family wealth from gains.
- 11th lord in 12th with good support → foreign income and charity.
- 11th with malefic involvement → delayed or contested gains.
- Mars in 11th with benefics → energetic network and business success.
