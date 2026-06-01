---
house: 4
name: Fourth House
sanskrit: Sukha / Matru / Bandhu Bhava
karaka:
  - Moon (mother)
  - Jupiter (happiness / education)
  - Venus (vehicles / music)
  - Mars (houses / real estate)
special_varga: [D9]
source: HTJAH-I:4117-5009
---

# House 4 Framework — Sukha / Matru / Bandhu Bhava

This document captures Raman's fourth-house methodology for mother, property,
education, conveyances, and general happiness. It is organized to support a
multi-backend engine that can judge multiple sub-domains of the 4th house.

## 1. Executive summary

- Raman treats the 4th as a **multi-karaka house**: the house means differ by
  sub-matter.
- The engine should separate at least five outputs:
  - `mother_quality`
  - `property_strength`
  - `education_strength`
  - `vehicle_acquisition_flag`
  - `general_happiness`
- The chapter mandates cross-checking with the **Moon** and the **Navamsa**.
- The dominant karaka depends on the sub-matter:
  - **Moon** for mother
  - **Jupiter** for happiness and education
  - **Venus** for vehicles and the arts
  - **Mars** for houses and landed property
- D4/D12/D24 are not used by Raman here.

## 2. Core engine architecture

### 2.1 Primary evaluation frames

1. **Rasi 4th House frame**
   - Evaluate the 4th house sign, occupancy, aspects, and the presence of yogas.
2. **4th Lord frame**
   - Evaluate 4th lord placement, strength, afflictions, and dignity.
3. **Sub-matter karaka frames**
   - Moon for mother; Jupiter for happiness/education; Venus for vehicles/music;
     Mars for houses/property.
4. **Navamsa frame (D9)**
   - Mandatory for all good/bad outcome moderation and for cross-checking.
5. **Matru-Sthana-as-Lagna frame**
   - Use the 4th or Moon-as-Lagna to judge mother's longevity via the 8th therefrom.

### 2.2 Pillars of judgment

- **4th House** — the basic property of the house.
- **4th Lord** — its quality and placement.
- **Karaka by sub-matter** — Moon, Jupiter, Venus, Mars as appropriate.
- **Occupants** — planets in 4th and their aspects.

### 2.3 Output dimensions

- `mother_life_strength`
- `property_and_homestead_score`
- `education_potential`
- `vehicle_possession_flag`
- `conveyance_quality`
- `general_comfort_flag`
- `house_loss_risk`
- `mother_death_risk`
- `education_obstacle_flag`
- `vehicle_delay_flag`

## 3. Rule ordering and precedence

1. **Choose the sub-matter first**; then pick the appropriate karaka.
2. **Assess the 4th house and its lord together**.
3. **Navamsa confirmation is mandatory**; do not finalize a result without it.
4. **Apply Satyacharya strength scaling**: strong lord amplifies good results;
   afflicted lord intensifies bad ones.
5. **Use the Mahabhava rule** that strong 4th and 9th lords, or 4th and 10th
   exchanges, build property and Rajayoga.
6. **If the 4th lord is in a dusthana or hemmed, expect property loss or
   maternal trouble before happiness.**

## 4. House-4 scoring architecture

### 4.1 Core score components

- `fourth_house_strength`
- `fourth_lord_strength`
- `mother_karaka_strength`
- `education_karaka_strength`
- `vehicle_karaka_strength`
- `property_karaka_strength`
- `navamsa_mitigation`
- `papakartari_penalty`

### 4.2 Aggregation

- `general_happiness` = average of 4th house strength, Jupiter quality, and Moon
  connectivity.
- `property_strength` = function of 4th lord placement, Mars involvement, and
  benefic disposition.
- `education_strength` = Jupiter/Mercury connection to 4th, plus 4th lord strength.
- `vehicle_acquisition_flag` = attributed primarily to Venus + 4th lord position.
- `mother_life_strength` = Moon + 4th lord + Matru-Sthana 8th-from-Moon logic.

### 4.3 Recommended weights

- 4th House: 25%
- 4th Lord: 30%
- Sub-matter Karaka: 30%
- Navamsa modifier: 15%

If `papakartari_penalty` is present, reduce the relevant sub-matter score by
30–50%.

## 5. Key House-4 rule categories

### 5.1 4th Lord placements

Baseline outcomes by house. Fortified results are strong, afflicted results are
weak or damaging.

- **Lagna** — learned, rich, likely to lose inherited wealth if weak.
- **2nd** — fortunate and courageous, inherits maternal property.
- **3rd** — generous, self-made, but troubled by step-relations if weak.
- **4th** — happy, rich, religious; weak → sensual.
- **5th** — respected, religious, acquires vehicles.
- **6th** — roaming, mean, full of trouble.
- **7th** — happy and commanding, good in distant lands.
- **8th** — misery, loss of property, forced travel.
- **9th** — fortunate toward father and property.
- **10th** — political success, possible reputation loss when afflicted.
- **11th** — generous, mother fortunate; sickly if weak.
- **12th** — deprived of happiness, maternal loss, poverty.

### 5.2 Important combinations

- 4th lord in 6th/8th/12th with no benefic → early maternal death.
- 4th lord in Lagna or 7th → easy acquisition of a house.
- 4th house or lord under Papakartari → bad social company / poor mother.
- Jupiter in 4th + 4th lord with good planets → clean heart and happiness.
- Venus in 4th → good conveyances if well-placed.
- Mercury in 4th → proficiency in astrology and intellectual learning.
- Sun/Moon in 4th → aptitude for political science, psychology, or metaphysics.
- 4th/9th/10th lord combinations → royal favour, property, or political status.

### 5.3 Planets in the 4th house archetypes

- **Sun** — dignity, potential public life, may suffer head wounds if afflicted.
- **Moon** — mother issues, emotional nature, can kill the mother if afflicted.
- **Mars** — vehicles, wounds from stones, strength of the mind.
- **Mercury** — astrology, logical pursuits, mental facility.
- **Jupiter** — learning, convention, Vedas, high education.
- **Venus** — music, arts, good conveyances.
- **Saturn** — durability, work through hardship, may lose property.
- **Rahu** — hypocrisy, hidden danger, dangerous spouse.
- **Ketu** — worldly detachment, spiritual learning, property loss if weak.

### 5.4 Mother's longevity

- Apply the Matru-Sthana-as-Lagna technique: treat the 4th or the Moon as
  mother's ascendant and judge the 8th therefrom.
- Early loss signs: 4th lord in 6th/12th weak, waning Moon with malefic in 6th/8th,
  Saturn in 4th with the Moon.

## 6. Timing and period architecture

- Major activation factors: 4th lord, planets in the 4th, planets aspecting the
  4th, and the karaka for the relevant sub-matter.
- Results strengthen when both Dasa and Bhukti lords influence the 4th.
- Use the 4th from Moon for added confirmation, especially for mother and
  education timing.

## 7. Engineering notes

- Build the 4th engine as a **multi-output house model** with separate scoring
  paths for mother, education, vehicles, property, and happiness.
- Implement the karaka selector by sub-matter; do not force a single planet to
  govern all 4th outputs.
- Navamsa is mandatory; D4/D12/D24 are not used by Raman in this chapter.
- Papakartari and dusthana placements should be resolved before positive
  conclusions.
- Use the **Moon + 4th lord + Navamsa** trio for mother's longevity.
- For education, combine Jupiter's natural karaka role with Mercury's intelligence
  rulership.

## 8. Validation anchors

- 4th lord in Lagna with benefics → property, learning, and strong mother.
- Moon in 4th with malefics → early maternal loss.
- Jupiter well-placed in/assoc with 4th → clean heart, happiness, strong learning.
- Venus in 4th with 4th lord → good conveyances and comforts.
- 4th lord in 8th or 12th with affliction → property loss and mother trouble.
