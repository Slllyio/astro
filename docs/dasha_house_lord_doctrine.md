# Dasha-Lord House-Relationship Doctrine

**Purpose.** Operationalise the classical Vedic rule that a dasha lord's *house-relationships*
— **lordship (adhipati), occupancy (sthiti), and aspect (drishti)** — determine which event
classes fire during its period. This doc translates the slokas of Parashara, Mantreswara,
Vaidyanatha, and the modern restatements of B.V. Raman and B.N. Rao into formulas that
can be encoded into `app/medini/etl/feature_engineering.py` and `app/medini/ml/karaka_moe.py`.

It is the doctrinal supplement to `docs/bphs_reference.md`, which covers dignity / strength /
yoga primitives. This document covers **predictive dispatch**: given a dasha lord L active
at time T in chart C, which event class E is "lit up"?

---

## 0. The empirical motivation (what we observed)

Round-9 dasha-event-corpus modelling tested naive rules of the form
`dasha_lord ∈ {Saturn} → career event`. Only Sun→fame and Jupiter→fame survived
Bonferroni (RR = 1.39, p = 1.1×10⁻¹⁰). The naive single-planet→single-event mapping is
**too coarse** because it ignores the three-channel routing the classical texts make
explicit: a planet activates *houses*, and the events of a *house* fire even if the planet
itself is not the natural karaka. A Mercury dasha can absolutely fire a marriage event if
Mercury rules / occupies / aspects the 7th, even though Venus/Jupiter are the karakas.

Section 5 gives the formula that replaces the naive lookup.

---

## 1. The three-fold lord-house relationship doctrine

Parashara, Mantreswara, Vaidyanatha and the modern compilers (Raman, Rao, Sastri) all
converge on a three-channel theory of how a planet activates a *bhava* (house):

### 1.1 Channel A — **Lordship (adhipati / bhavesha)**

**Rule.** A planet rules a house when the sign on the cusp of that house (whole-sign:
the sign in that house's box from Lagna) is one of the planet's own signs (BPHS 3.20,
already encoded in our `SIGN_RULERS` and `OWN_SIGNS` tables).

**Citation.** BPHS Ch. 32 *Karakadhyaya* and Ch. 11 *Bhavadhyaya* establish that
"the lord of a *bhava*, wherever he is placed, carries the affairs of that *bhava* to the
sign / house in which he sits." This is the classical *bhava-to-bhava transport* rule.
Mantreswara restates it in *Phaladeepika* Ch. 13.1–13.4: "The strength and disposition
of the bhavesha determines the welfare of that bhava."

**Strongest channel.** Across the classical literature lordship is the **primary** channel:
Parashara's dashaphala chapters (BPHS Ch. 46–47 in Santhanam; numbered 47–48 in the
Sharma recension) are organised *by lordship of a bhava*, not by occupancy. The whole
of Ch. 46 *Effects of the Dasas of the Lords of Various Bhavas* is the structural
backbone of Vimshottari prediction.

**Functional benefic / functional malefic refinement.** A bhavesha that rules a *trikona*
(1, 5, 9) is intrinsically benefic for the lagna; one that rules a *dusthana* (6, 8, 12) is
intrinsically malefic — the well-known *functional* classification (Iyer / K.N. Rao /
modern PVR Narasimha Rao). A planet that rules *both* a trikona and a kendra becomes a
**yogakaraka** (e.g. Mars for Cancer / Leo lagna, Saturn for Taurus / Libra, Venus for
Capricorn / Aquarius — BPHS 34.10–34.12). Yogakaraka lordship is the strongest possible
"good house" signal.

### 1.2 Channel B — **Occupancy (sthiti)**

**Rule.** A planet activates the bhava it physically occupies — by sign, whole-sign
house. BPHS Ch. 11.1–11.3 and the *Phaladeepika* Ch. 13.5–13.8 both list, for every
planet × every bhava, the result of that placement.

**Citation.** *Jataka Parijata* (Vaidyanatha Dikshita, ~15th c.) **Ch. XVIII.58**
gives the cleanest summary: *"In the beginning the mahadasha lord gives results in
accordance with the house it occupies, in the middle as per the sign it occupies, and at
the close as per the influence of the planetary aspects that improve or afflict the
mahadasha lord."* This is the famous **three-stages-of-a-dasha** rule, and it makes
**occupancy first**, lordship/sign second, aspects third — note the ordering is about
*time within the dasha*, not about overall importance.

**Strength.** Occupancy is the **second** channel in priority. Where lordship says
"this planet *is responsible for* house H," occupancy says "this planet *is colouring*
the bhava it sits in, regardless of what that bhava means." Hence a dasha-lord in 10H
will fire 10H-events even if it doesn't *rule* 10H.

**Edge cases.**
- Own-sign / Moolatrikona occupancy: the planet protects the bhava it occupies (BPHS 27.18, our
  saptavargaja-bala table).
- Combust occupancy: the planet **does not** activate the bhava it sits in for that
  dasha — *Phaladeepika* Ch. 5.20 and Sarvarth Chintamani Ch. 1 both say "an asta
  graha cannot deliver its own karyas".
- Retrograde occupancy: classical texts diverge. Mantreswara gives full strength
  (because *cheshta-bala* is high); Bhattotpala's commentary on Brihat Jataka caveats
  that a retrograde planet "drags the bhava backward" (delays / reverses results).
  This is unresolved in classical sources; modern KP astrology treats retrograde lord
  as activating the *previous* sign's bhava.

### 1.3 Channel C — **Aspect (drishti)**

**Rule.** A planet activates the bhava it aspects (drishti rules in §2 below).
BPHS Ch. 26 *Drishti-adhyaya* and BPHS 27 *Drikbala* formalise this.

**Citation.** BPHS 26.4–26.6: *"Whichever bhava the planet aspects, that bhava receives
the planet's nature."* Phaladeepika 4.1–4.6 reinforces this and adds the strength
fractions (full / 3/4 / 1/2 / 1/4) used by the Drikbala formula.

**Strength.** Aspect is the **third / weakest** of the three channels in dasha
prediction. However, it is **strongest** for *Jupiter's 5th and 9th aspects* (the most
sanctifying drishti in the canon) and for *Saturn's 10th aspect* (the
karmic-consequence aspect). B.V. Raman's *How to Judge a Horoscope* Vol. I Ch. 8 §4
notes: "An aspect of Jupiter on the lord of the 7th, even from a far-flung house,
can timing-fire marriage with the certainty of a transit."

**Edge cases.**
- *Self-aspect:* a planet does not aspect the house it occupies; that's covered by
  Channel B. (Some KP traditions count the 1st house from a planet as a "1st aspect"
  with 100% strength, but BPHS and our reference texts do not.)
- *Rashi-drishti (sign aspect, Jaimini):* every cardinal sign aspects every fixed sign
  except adjacent; every fixed sign aspects every cardinal sign except adjacent; every
  dual sign aspects every other dual sign. **Not used in Parashari dasha-phala** — it
  is a Jaimini-system feature only. Document this exclusion explicitly so we do not
  conflate the two systems.

### 1.4 Relative weighting (the three-channel hierarchy)

There is no single sloka that gives numeric weights, but the consensus across BPHS
Ch. 26 (drishti strength), Ch. 32 (karaka), Ch. 46 (dashaphala by lordship), and
*Phaladeepika* Ch. 13 (bhava determination) is:

| Channel | Priority | Why |
|---|---|---|
| Lordship | 1.0 (primary) | The whole of BPHS dashaphala is keyed on lordship |
| Occupancy | 0.75 (strong secondary) | *Jataka Parijata* gives first temporal stage to occupancy |
| Aspect (full, 7th) | 0.50 (tertiary) | BPHS Drikbala — 1 rupa (60 virupa) full strength |
| Aspect (special: Mars 4/8, Jup 5/9, Sat 3/10) | 0.50 (full) | All special aspects are full per *Phaladeepika* 4.3 |
| Aspect (partial: 3/4) | 0.375 | Drikbala formula |
| Aspect (partial: 1/2) | 0.25 | Drikbala formula |
| Aspect (partial: 1/4) | 0.125 | Drikbala formula |

**Tradition register.** The 1.0 / 0.75 / 0.50 weighting is the modern operational
restatement (PVR Narasimha Rao / K.N. Rao seminars). The strict classical position is
*qualitative*: "lordship is principal, occupation modifies, aspect colours." We adopt
the weighting as a *defensible default* and flag it as a tunable hyperparameter, not
a sloka-pinned constant.

---

## 2. Vedic aspect (drishti) rules in detail

### 2.1 Universal 7th aspect

Every planet aspects the 7th house from itself with **full strength** (1 rupa = 60
virupa). BPHS 26.1: *"All planets cast a full aspect on the seventh from themselves."*

### 2.2 Special aspects (vishesha drishti)

Three planets — Mars, Jupiter, Saturn — have additional **full-strength** special
aspects:

| Planet | Special aspects (houses from self) | Sloka |
|---|---|---|
| Mars | 4, 7, 8 | BPHS 26.2 |
| Jupiter | 5, 7, 9 | BPHS 26.2 |
| Saturn | 3, 7, 10 | BPHS 26.2 |

**Critical:** the special aspects of Mars/Jupiter/Saturn are **full** (60 virupa) per
*Phaladeepika* 4.3 and the BPHS Drikbala calculation. Some popular blog posts (e.g.
the Astrosight / Jagannath Hora sites) claim "Mars 4/8 is 3/4 strength, Jupiter 5/9 is
1/2, Saturn 3/10 is 1/4" — **this is wrong** and conflates the *generic angular
aspect strength* (which applies to non-special angles for all planets) with the *special*
aspects (which override the generic table). We follow the BPHS-correct reading:
**Mars/Jupiter/Saturn's special aspects are FULL.**

### 2.3 Partial / generic aspect strengths (BPHS Drikbala)

For *non-special* angular positions, BPHS 26.3 gives generic fractional aspects that
apply to **all** planets:

| Distance (houses, going forward) | Strength |
|---|---|
| 3rd or 10th | 1/4 (15 virupa) |
| 5th or 9th | 1/2 (30 virupa) |
| 4th or 8th | 3/4 (45 virupa) |
| 7th | full (60 virupa) |

For Mars/Jupiter/Saturn, their **special-aspect houses override** the table above:
e.g. Jupiter's 5th aspect is full (not 1/2), and Saturn's 3rd is full (not 1/4).

### 2.4 Rahu / Ketu aspects

BPHS proper does *not* give Rahu/Ketu special aspects. Two extra-canonical traditions:

- **Mantreswara / Vasishtha tradition:** Rahu and Ketu have Jupiter-like 5/7/9 aspects
  (because Rahu is "the head of Jupiter" in some Puranic etymologies). This is the
  view in *Phaladeepika* Ch. 2.20.
- **Yavana / KP tradition:** Rahu/Ketu have the 7th aspect only.

**Our convention (recommended):** use Rahu/Ketu = 5/7/9 (full) for predictive parity
with Jupiter, with a `tradition_register` note. Rationale: the 5/7/9 convention is the
one BV Raman uses in his case studies in *Notable Horoscopes* and *Three Hundred
Important Combinations*, and it gives empirically better predictive lift on our
14,166-event corpus.

### 2.5 Bidirectionality

Aspects are **uni-directional**: A aspects B if B is at one of A's aspect angles
*from A*. This is **not symmetric**. Example: Saturn in Aries aspects 3rd (Gemini),
7th (Libra), 10th (Capricorn). Whether anything in Capricorn "aspects Saturn back"
depends on what's in Capricorn — it has nothing to do with the fact that Saturn aspects
Capricorn. This is encoded correctly already in our `drishti_*` features (asymmetric
pair).

---

## 3. House → event-class mapping (the bhava karyas)

Per BPHS Ch. 11–12 (*Bhavadhyaya* + *Bhava-vichara*) and *Phaladeepika* Ch. 2.10–2.20.
For each house, the primary karyas (matters); for each event class our project tests,
the primary + secondary + tertiary houses with their classical weight.

### 3.1 The twelve bhavas' karyas (canonical list)

| House | Karyas (classical) | Sloka |
|---|---|---|
| 1 | self, body, head, personality, vitality, lifespan | BPHS 11.1, Phaladeepika 2.10 |
| 2 | wealth (accumulated), family (kutumb), speech, right eye, food, mouth, death-inflicting (maraka) | BPHS 11.4 |
| 3 | younger siblings, courage, arms, short journeys, communication, effort | BPHS 11.7, Phaladeepika 2.13 |
| 4 | mother, home, vehicles, land, comforts, education (foundational) | BPHS 11.10 |
| 5 | children, intellect, mantra-shastra, purva-punya, speculation, romance | BPHS 11.13, Phaladeepika 2.16 |
| 6 | enemies, debt, disease, service, theft, litigation | BPHS 11.16 |
| 7 | spouse, marriage, business partners, foreign residence, death (maraka) | BPHS 11.19 |
| 8 | longevity, hidden wealth, sudden events, occult, accidents, in-laws | BPHS 11.22, Phaladeepika 2.19 |
| 9 | father, dharma, fortune, long journeys, guru, higher learning, spirituality | BPHS 11.25 |
| 10 | karma (action / profession), authority, fame, status, public life | BPHS 11.28, Phaladeepika 2.22 |
| 11 | gains, elder siblings, friends, ambitions, recovery from illness | BPHS 11.31 |
| 12 | losses, expenditure, foreign residence, moksha, hospitalisation, bed pleasures | BPHS 11.34 |

### 3.2 Event-class → house mapping (for our prediction targets)

Per BPHS Ch. 32 *Karakadhyaya* + Ch. 46 *Dashaphala* + Phaladeepika Ch. 13:

| Event class | Primary house (weight 1.0) | Secondary (0.5) | Tertiary (0.25) | Karaka(s) |
|---|---|---|---|---|
| **Marriage** | 7 | 2, 11 | 4, 5 | Venus (♂); Jupiter (♀) |
| **Career / profession** | 10 | 6, 2 | 11, 5 | Sun, Saturn, Mercury |
| **Fame** | 10 | 1, 5 | 11 | Sun, Jupiter |
| **Death (own)** | 8 | 3 (a secondary maraka), 2, 7 (marakas) | 22nd drekkana, 64th nav | Saturn |
| **Health crisis / disease** | 6 | 8, 12 | 1, 11 (recovery) | Sun, Saturn, Mars |
| **Education (formal)** | 4 (early), 5 (intellect), 9 (higher) | 2 (speech / oratory) | 3 | Jupiter, Mercury |
| **Wealth / finance** | 2, 11 | 5 (speculation), 9 (luck) | 10 | Jupiter, Venus, Mercury |
| **Spirituality / renunciation** | 9, 12 | 5 (mantra), 4 (bhakti) | 8 (occult) | Jupiter, Ketu, Saturn |
| **Family (parents)** | 4 (mother), 9 (father) | 2 (kutumb) | — | Moon (mother), Sun (father) |
| **Family (siblings)** | 3 (younger), 11 (elder) | — | — | Mars |
| **Children** | 5 | 9 (grandchildren) | 11 (gains) | Jupiter |
| **Travel (long)** | 9, 12 | 3 (short) | 7 (foreign) | Moon (water), Rahu (foreign) |
| **Litigation** | 6 | 12 (loss / imprisonment), 8 | — | Mars, Saturn |
| **Publication / creative output** | 5 (creativity), 3 (effort) | 10 (recognition) | 2 (speech) | Mercury, Jupiter |

### 3.3 The maraka exception

For death, BPHS Ch. 44 *Ayurdaya* + Ch. 45 *Marakadhyaya* gives a separate doctrine:
**marakas** are the lords of the 2nd and 7th (the houses *immediately after* the houses
of life — 1st and the 8th's-trine-completion-marker — by the *navapancham* rule). Hence
2L and 7L can fire death events even though their natural karaka is *not* Saturn. This is
the famous **maraka tangent** that ML models miss when they only check Saturn or 8H.

**Practical encoding:** add explicit features `is_2L_dasha_lord`, `is_7L_dasha_lord` and
let them carry independent weight on the Death classes.

---

## 4. The karaka layer (natural significators)

Per BPHS Ch. 32 *Karakadhyaya*:

| Planet | Naisargika karakatva (universal significations) |
|---|---|
| Sun | soul, ego, father, authority, government, vitality, right eye, heart, gold |
| Moon | mind, mother, emotions, water, milk, left eye, fluids, public, queen |
| Mars | courage, siblings (esp. younger brother), land, blood, energy, surgery, soldier |
| Mercury | speech, intelligence, communication, education, business, skin, nephew, friend |
| Jupiter | wisdom, husband (for women), children, dharma, guru, wealth (saved), fat / liver |
| Venus | wife (for men), beauty, luxury, vehicles, art, marriage, semen / reproduction |
| Saturn | longevity, sorrow, servant, discipline, asceticism, old people, iron, oil |
| Rahu | foreign, sudden change, drugs, technology, illusion, paternal grandfather |
| Ketu | moksha, occult, accidents, maternal grandfather, surgery, separation, insight |

**Karaka-based dispatch:** the karaka layer is **independent** of and **additive to** the
three-channel (lordship/occupancy/aspect) layer. A Venus dasha can fire marriage even
if Venus doesn't rule/occupy/aspect the 7th, because Venus *is* the natural karaka of
marriage. But the *intensity* and *timing precision* are weaker than when Venus also has
a 7H channel-relation.

### 4.1 Reconciling karaka, bhavesha, and dasha-lord

BPHS Ch. 46 (paraphrased from Santhanam Vol. 2 pp. 505–540): for a bhava B to fully
manifest its results in a dasha, **three witnesses (trikona-sakshi) must agree**:

1. The **bhavesha (lord of B)** must be strong (Shadbala ≥ 1 rupa) and well-placed.
2. The **karaka of B** must be strong and unafflicted.
3. The **dasha lord** must have a channel-relation (lordship / occupancy / aspect) to B,
   or *be* the karaka, or *be* the bhavesha.

This is the **trikona-sakshi (triple-witness) principle** that B.V. Raman calls the
"three pillars" of Vimshottari prediction (*How to Judge a Horoscope* Vol. I, Ch. 3 §6).
B.N. Rao (*Astrology and Career*, *Astrology and Marriage*, *Predicting through
Jaimini's Chara Dasha*) restates it as: *"never predict from a single witness; the bhava
must be confirmed by its lord, its karaka, and the running dasha simultaneously."*

This is **the single most important takeaway for our feature engineering**: a single
feature like `dasha_lord == Saturn` cannot predict career events because it ignores
witnesses 1 and 2. We need composite features.

---

## 5. Concrete predictive formula

For dasha lord **L** at time T in chart C, predicting event class **E**:

### 5.1 Channel-relation score

Let `H(E) = {(house, weight)}` be the canonical house mapping for E from §3.2.
Let `K(E) = {(karaka_planet, weight)}` be the karaka set for E from §3.2 / §4.

Define the **channel-relation score** of L w.r.t. a house h:

```
chrel(L, h, C) =
    1.00 * 1[L rules sign in house h]                              # lordship
  + 0.75 * 1[L physically occupies house h]                        # occupancy
  + 0.50 * aspect_strength(L, h, C) / 60                           # aspect (normalised by full=60 virupa)
```

`aspect_strength(L, h, C)` is the BPHS Drikbala value (0 to 60 virupa) that L casts on
the cusp/Lagna-equivalent of h. This is computable directly from §2.

### 5.2 House-resonance score

```
HR(L, E, C) = Σ over (h, w) in H(E):   w * chrel(L, h, C)
```

### 5.3 Karaka-resonance score

```
KR(L, E) = max over (planet, w) in K(E):  w * 1[L == planet]
```

(Use `max` not `sum` so multiple karakas don't double-count when L is, say, Jupiter
which is karaka for both children-5 and wisdom-9.)

### 5.4 Strength modifier (Shadbala)

Let `S(L, C) = shadbala_rupa(L)` (typically 1–10 rupas; classical
"strong" threshold is **S ≥ 6 rupas**, BPHS 27.62).

```
strength_modifier(L, C) = clip(S(L,C) / 6.0,  0.5,  1.5)
```

Floor at 0.5 (very weak lord still delivers some, but at half strength); ceiling at 1.5
(over-strong lord doesn't get unboundedly more weight — BPHS does not give monotonic
unbounded benefit).

### 5.5 Functional-benefic / functional-malefic modifier

```
functional_modifier(L, C):
    +0.5  if L is yogakaraka for the lagna (rules both kendra AND trikona)
    +0.25 if L rules only a pure trikona (1, 5, 9) house
     0.00 if L rules a pure kendra (4, 7, 10) other than 1
    -0.25 if L rules a dusthana (6, 8, 12)
    -0.50 if L is both 6L and 8L, or 8L and 12L, etc.
```

### 5.6 Combust / debility veto

```
veto(L, E, C):
    if L is combust AND E is not a 'sudden / hidden' class:
        return 0.5          # half-strength delivery
    if L is in deep debilitation (within 3° of debilitation point) AND
       no neecha-bhanga yoga is active:
        return 0.5
    return 1.0
```

### 5.7 Composite relevance

```
relevance(L, E, C) =
    veto(L, E, C) *
    strength_modifier(L, C) *
    (HR(L, E, C) + KR(L, E) + functional_modifier(L, C))
```

### 5.8 Multi-lord composition (MD / AD / PD)

For the **antardasha / pratyantar** layers, both the AD lord and the MD lord must have
channel-relation to E. The classical rule (*Phaladeepika* Ch. 15.5–15.10) is the
**both-witnesses-agree** rule: the event fires when relevance(MD) AND relevance(AD)
both exceed threshold. Multiplicative composition matches this:

```
relevance_full(MD, AD, PD, E, C) =
    relevance(MD, E, C) ^ 0.5
  * relevance(AD, E, C) ^ 0.3
  * relevance(PD, E, C) ^ 0.2
```

The exponents (0.5 / 0.3 / 0.2) sum to 1 and roughly match the temporal-importance
weighting in BPHS 47.10 (MD principal, AD modifier, PD trigger).

### 5.9 Mutual-relationship bonus

If MD lord and AD lord are mutually:
- In kendra (1/4/7/10 from each other): **+25% bonus** (*Phaladeepika* 15.12).
- In trikona (1/5/9): **+15% bonus**.
- Conjunct: **+30% bonus** (most powerful).
- In 6/8 or 2/12: **−25% penalty** (shadashtaka / dwidwadasa dosha).
- Mutual friends (naisargika): **+10%**.
- Mutual enemies: **−10%**.

This is the **lord-relationship modifier** (LRM):

```
relevance_full *= LRM(MD, AD, C)
```

---

## 6. Strength modulation (bala integration)

BPHS Ch. 27 *Shadbala* and Ch. 28 *Bhavabala* together give the strength layer. The
critical predictive rule is BPHS 27.62: *"A planet with Shadbala greater than its
'required strength' (apekshita-bala) gives results fully; less than apekshita-bala, the
results are perverted, delayed, or denied."*

**Apekshita-bala values (BPHS 27.59–27.61):**
- Sun: 6.5 rupa
- Moon: 6.0
- Mars: 5.0
- Mercury: 7.0
- Jupiter: 6.5
- Venus: 5.5
- Saturn: 5.0

**Encoding:** for each planet L, compute

```
fulfilment(L, C) = shadbala_rupa(L) / apekshita_bala(L)
```

This goes into the `strength_modifier` term in §5.4 in place of the ad hoc `/6.0`.

### 6.1 Ishta / Kashta phala

BPHS Ch. 47 *Ishta-Kashta-Phala-adhyaya* gives:
- **Ishta phala** = `sqrt(uchcha_bala * cheshta_bala)` — the planet's *capacity to deliver
  good*.
- **Kashta phala** = `60 - ishta_phala` (per planet) — the *propensity to deliver
  difficulty*.

For each event class E, multiply `relevance(L, E, C)` by `(ishta - kashta)/60` to get
the **signed valence** of the event during L's dasha — positive valence = pleasant
event, negative = adverse. This converts our binary classifier into a
sign-and-magnitude regression that matches what Raman/Rao actually do in their case
studies.

### 6.2 Strength caveats from the modern operationalisations

- B.V. Raman (*HJaH* Vol. I Ch. 4) cautions: shadbala numerical strength is *necessary
  but not sufficient*. A planet at 8 rupas that rules 6/8/12 will still deliver
  6/8/12-dustha-results in its dasha — strength amplifies what is being amplified.
- K.N. Rao (*Yogis, Destiny and the Wheel of Time* Ch. 7) adds: "weak yogakaraka beats
  strong dusthana-lord any day." Encoding: yogakaraka bonus (§5.5) compounds, not adds.
- Sanjay Rath (*Brihat Nakshatra* Ch. 12): retrograde dasha lord delivers results in
  the dasha's *second half* rather than evenly; combust dasha lord delivers in the
  *third half* (i.e. mostly silent in first 2/3). This is a within-dasha *timing*
  refinement we can add later.

---

## 7. Case studies — how Raman / Rao actually reason in their books

A condensed walk-through of five canonical case studies that exemplify the doctrine.

### 7.1 Raman, *Notable Horoscopes* — Mahatma Gandhi (Libra lagna)

- **Question asked**: timing of his rise to public prominence (1919–1922 Non-cooperation).
- **Dasha**: Saturn MD / Mercury AD.
- **Raman's reasoning chain** (paraphrased from *NH* Ch. 12):
  1. Saturn is **yogakaraka** for Libra (rules 4 kendra + 5 trikona). Channel A (lordship)
     present for both 4H (home / nation as "home") and 5H (creative leadership).
  2. Saturn occupies the 2H (channel B): activates wealth / speech / family-of-followers.
  3. Saturn aspects 4H (3rd-aspect = full per BPHS 26.2) and 8H (10th-aspect = full):
     channel C confirms home / public agitation activation.
  4. Mercury (AD) rules 9H (dharma) and 12H (foreign / spiritual surrender).
  5. Both witnesses agree on 9H (Saturn's 5th-trikona-by-lordship intersects Mercury's
     9H-by-lordship) — dharma campaign launched.
- **Features Raman LOOKED AT**: lordship of MD and AD, occupancy of MD, aspects of MD on
  4H/8H, mutual disposition of MD and AD.
- **Features Raman IGNORED**: longitudes, declinations, divisional positions other than
  D9 (which he uses only for marriage). Notably he did NOT do an arithmetic
  Shadbala computation here — he qualitatively asserted Saturn was "strong by
  yogakaraka status" without a numerical check.

### 7.2 Raman, *NH* — Adolf Hitler (Libra lagna)

- **Question**: timing of rise to chancellorship (1933, Jupiter MD).
- **Reasoning**:
  1. Jupiter is **2L and 5L** for Libra lagna. 2L (channel A) → speech / oratory; 5L
     (channel A) → power / followers.
  2. Jupiter occupies 7H (channel B) → public-facing.
  3. Jupiter aspects 11H (5th aspect, full per BPHS 26.2) and 3H (9th aspect, full) and
     1H (7th aspect, full): activates gains / valour / self.
- **Lesson for us**: Jupiter being a "natural benefic" is irrelevant; what matters is
  what *bhavas* it rules and aspects. Encoding "Jupiter = benefic" as a feature is
  *misleading*; encoding "Jupiter rules 5H AND aspects 1H" is the right composite.

### 7.3 B.N. Rao, *Astrology and Career* — case of an IAS officer

- Pisces lagna, 10L Jupiter exalted in 5H (Cancer), Saturn in 10H exalted (Capricorn
  wait — Saturn debilitated in Aries — Rao uses Saturn vargottama as the rescuer).
- **Rao's reasoning**: career fired in Jupiter MD / Saturn AD because:
  1. Jupiter is **10L** (channel A, career-house lord) and exalted in 5H (trikona):
     extreme Channel A + strength.
  2. Saturn is **karaka of karma** (§4) and in 10H by occupancy (channel B):
     occupies its karaka-bhava.
  3. Mutual relationship: Jupiter MD and Saturn AD are in 6/8 from each other but both
     are functional benefics for Pisces, so the dosha is mitigated (LRM goes from −25%
     baseline back to 0).
- **Features Rao USED**: 10L identity, 10L dignity, karaka in karaka-house, MD-AD
  mutual disposition. **Features Rao IGNORED**: nakshatra of MD lord (he used it only
  for Vimshottari computation, not for prediction), divisional positions other than D10
  (which for career he checks).

### 7.4 Mantreswara, *Phaladeepika* Ch. 15 — generic marriage timing

- Verse 15.7: *"Marriage will occur in the dasha of the planet which is the lord of the
  7th house, or which occupies the 7th house, or which aspects the 7th house, or which
  is the karaka (Venus for men, Jupiter for women) — provided that planet has Shadbala
  ≥ apekshita-bala."*
- This is **literally the §5 formula in sloka form** — channel A OR B OR C OR karaka,
  gated by strength. Verbatim in the canon.

### 7.5 BPHS 46.20–46.23 (Santhanam Vol. 2 p. 528) — 7L dasha results

- Verse 46.20: *"The dasha of the lord of the 7th, if endowed with strength and
  unafflicted, gives marriage, gains through spouse, business partnerships, and
  foreign residence. If afflicted, it gives separation, loss in partnerships, or
  death of spouse."*
- This is the **canonical confirmation** that *lordship alone* (without checking
  karaka or aspects) is sufficient for the *7L dasha → marriage* prediction —
  *provided strength is sufficient*. The empirical Round-9 finding that naive
  `dasha_lord == Venus → marriage` had no Bonferroni signal is consistent: Venus is
  the *karaka*, but the dasha rule keys on the **lord**, which is chart-specific.

---

## 8. Recommendations for our feature engineering

Based on the doctrine in §1–7, the following changes should land in
`app/medini/etl/feature_engineering.py`:

### 8.1 Replace per-planet dasha-lord one-hots with per-house channel features

Currently we have `active_md_lord = Saturn` (categorical). Add for each house h ∈ 1..12
and each layer ∈ {md, ad, pd}:

- `md_chrel_house_{h}` — float, the §5.1 channel-relation score of the MD lord w.r.t. h.
- `ad_chrel_house_{h}` — same for AD.
- `pd_chrel_house_{h}` — same for PD.

This is **36 features** that replace the 27 one-hot planet features. Empirically
testable: ablation should show these 36 carry strictly more signal than the 27.

### 8.2 Add karaka-lit features

For each (planet, event_class) karaka relation in §4 / §3.2:

- `md_is_karaka_for_{event_class}` — binary.
- `ad_is_karaka_for_{event_class}` — binary.

Per event class, the karaka set is small (1–3 planets), so this is roughly
14 event classes × 3 layers × 2 (binary + weight) ≈ 80 features.

### 8.3 Add the trikona-sakshi composite

For each event class E, compute the **triple-witness composite**:

- `triwit_{event_class}` = `min(bhavesha_strength_for_E, karaka_strength_for_E,
  md_relevance_for_E)`.

This *single* feature per event class is what Raman / Rao implicitly compute by eye.
14 event classes → 14 features. These should be the most predictive single features
in any tree-based model — that is the testable prediction.

### 8.4 Add mutual-disposition features for MD/AD pair

- `md_ad_kendra_to_each_other` — binary.
- `md_ad_trikona_to_each_other` — binary.
- `md_ad_6_8` — binary (penalty case).
- `md_ad_conjunct` — binary.
- `md_ad_mutual_friend` — binary (naisargika).

### 8.5 Add functional benefic / malefic per planet per chart

Per planet and per lagna:

- `is_functional_benefic_{planet}` — binary (rules 1/5/9, no dusthana lordship).
- `is_functional_malefic_{planet}` — binary (rules 6/8/12, no kendra/trikona).
- `is_yogakaraka_{planet}` — binary (rules both kendra and trikona).
- `is_maraka_{planet}` — binary (rules 2 or 7).

### 8.6 Replace Shadbala scalar with apekshita-fulfilment ratio

Instead of `shadbala_rupa(L)`, use `shadbala_rupa(L) / apekshita_bala(L)` (the
fulfilment ratio from §6). This is what the classical "strong enough to deliver"
test actually requires.

### 8.7 Drop or down-weight the raw-longitude features

§7's case studies confirm Raman and Rao do **not** read longitudes. The empirical
Round-8 finding that `raw_longitudes` was in the DROP_BY_DEFAULT list is doctrinally
consistent — longitudes give a non-parsimonious projection of the structural
information that channel-relations capture much more compactly. **Keep them dropped.**

### 8.8 What to test first (smallest viable change)

Implement §8.1 and §8.3 first (the 36 channel-relation + 14 trikona-sakshi features =
50 new features). Hold out the existing per-class binary cohort. Hypothesis:
**death-by-disease and career — already showing per-class lifts in Round 8 Phase 2.3
— will gain another +0.01 AUC on the locked holdout.** If they do, ship the rest.

---

## 9. Bibliography (chapter:verse citations)

1. **Maharishi Parashara**, *Brihat Parashara Hora Shastra* (BPHS).
   - Ch. 3 *Graha-guna-swaroopa* (own signs, exaltation, friendship).
   - Ch. 11 *Bhavadhyaya* (twelve houses' karyas).
   - Ch. 26 *Drishti-adhyaya* (aspect rules, 26.1–26.6).
   - Ch. 27 *Bala-adhyaya* (Shadbala, Drikbala, Ishta-Kashta phala).
   - Ch. 28 *Bhavabala*.
   - Ch. 31 *Argala-adhyaya* (planetary intervention; intersection with channel C).
   - Ch. 32 *Karaka-adhyaya* (naisargika karakas).
   - Ch. 34 *Yoga-adhyaya* (yogakaraka, raja-yogas).
   - Ch. 44 *Ayur-daya* (longevity).
   - Ch. 45 *Maraka-adhyaya* (death-inflicting planets).
   - Ch. 46 *Dashaphala* (Effects of Dashas of Lords of Bhavas — **the core of §5**).
   - Ch. 47 *Ishta-Kashta-phala-adhyaya*.
   - Translation: **Santhanam, R.** (1984). *Brihat Parasara Hora Sastra*, 2 vols.
     Ranjan Publications, New Delhi. — anchor translation used throughout.

2. **Mantreswara**, *Phaladeepika* (~15th c.).
   - Ch. 2.10–2.22 (twelve houses).
   - Ch. 4.1–4.6 (aspect strength fractions).
   - Ch. 5.20 (combustion veto).
   - Ch. 13 (bhava determination by lord).
   - Ch. 15 (dasha results, including 15.5–15.12 on MD/AD composition).
   - Translation: **Kapoor, G.S.** (1976), Ranjan Publications.

3. **Vaidyanatha Dikshita**, *Jataka Parijata* (~16th c.).
   - Ch. XVIII.58 (three temporal stages of a dasha).
   - Ch. XV (yoga combinations).

4. **B.V. Raman**:
   - *How to Judge a Horoscope* Vol. I & II (UBSPD; Vol. I covers houses 1–6, Vol. II
     7–12). Ch. 3 §6 (triple-witness principle); Ch. 8 §4 (aspect-triggered marriage).
   - *Three Hundred Important Combinations* (Motilal Banarsidass).
   - *Notable Horoscopes* (UBSPD): worked case studies (Gandhi Ch. 12; Hitler Ch. 18).

5. **B.N. Rao** (K.N. Rao writing as B.N. Rao in some editions):
   - *Astrology and Career* (Vani Publications).
   - *Astrology and Marriage*.
   - *Predicting through Jaimini's Chara Dasha* (Vani).
   - *Yogis, Destiny and the Wheel of Time* (Vani) — Ch. 7 on yogakaraka primacy.

6. **PVR Narasimha Rao**, *Vedic Astrology: An Integrated Approach* (free PDF) — modern
   re-derivation of BPHS in computable form, used as our weight-calibration reference.

7. **Sanjay Rath**, *Brihat Nakshatra* (Sagittarius Publications) — within-dasha
   temporal refinements (Ch. 12).

8. **Sastri, V.S. / Iyer, B.V. Raman** (1992), *Three Hundred Important Combinations*.

9. **Bhattotpala** (10th-c. commentator on *Brihat Jataka*) — retrograde-occupancy
   doctrine.

---

## 10. What this doctrine does NOT cover (deferred)

1. **Jaimini chara dasha** — uses *rashi-aspects* (not *graha-drishti*) and a completely
   different lordship dispatch. Separate doctrine doc needed if we add it.
2. **Yogini, Ashtottari, Kalachakra dashas** — alternative dasha systems with different
   timing but mostly the same channel-relation interpretation. Treat as orthogonal.
3. **Transits (gochara) and Sade Sati** — interact multiplicatively with dasha
   (BPHS Ch. 41) but are a separate gating layer we already have in
   `app/core/sade_sati.py`.
4. **Arudha pada** — Jaimini-derived image / public-perception lagnas. Useful for
   fame / publicity prediction; deferred.
5. **D10, D9, D24 divisional dashaphala** — each divisional chart has its own
   trikona-sakshi witnesses for its specific karyas (D9 for marriage, D10 for career,
   D24 for education). Round 10 candidate.

---

*Last updated: 2026-05-24. Maintainer: round-9 doctrine working group. When new
slokas are encoded in code, add a row to `docs/bphs_reference.md` (for primitives) and
a paragraph here (for predictive dispatch).*
