# Raman Saab — Methodology Overview

> Canonical build reference for the **Raman Saab** engine, distilled from
> **B.V. Raman, *How to Judge a Horoscope* (Vols I & II)**, with supporting
> doctrine from his *Hindu Predictive Astrology* (HPA) and *Graha & Bhava Balas* (GBB).
> Everything here is grounded in the on-disk corpus; citations are real line numbers.
>
> This overview holds the **chart-wide / cross-cutting** method. The **per-house**
> method (significations, lord-in-12, combinations, planets-in-house, timing,
> nature-of-results, example insights) lives in `house_01_*.md … house_12_*.md`.

## 0. Sources & citation convention

| Tag | Work | On-disk file |
|---|---|---|
| **HTJAH-I** | How to Judge a Horoscope, Vol I (houses 1–6) | [how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md](../../../data/knowledge_library/sources/how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md) |
| **HTJAH-II** | How to Judge a Horoscope, Vol II (houses 7–12) | [how_to_judge_horoscope_raman2/chapter_001_full-text-unsplit.md](../../../data/knowledge_library/sources/how_to_judge_horoscope_raman2/chapter_001_full-text-unsplit.md) |
| **HPA** | Hindu Predictive Astrology | `hindu_predictive_astrology_raman/chapter_0NN_*.md` |
| **GBB** | Graha & Bhava Balas (Shadbala) | `graha_bhava_balas_raman/chapter_0NN_*.md` |
| **3HC** | Three Hundred Important Combinations (yogas) | `three_hundred_combinations_raman/…` |

Citations are written `HTJAH-I:474` = that work, that line in the on-disk file.

---

## 1. The macro sequence — Raman's own chapter order *is* the pipeline

Raman structures the book as a fixed procedure; the engine mirrors it exactly:

```
0. General Introduction — the 12 bhavas & their significations      (HTJAH-I:384)
1. Considerations in Judging a House — the 8 factors;
   functional benefic/malefic per Lagna; Yoga Karakas               (HTJAH-I:468)
2. Determination of Longevity — RUN BEFORE THE HOUSES               (HTJAH-I:761)
3. Houses 1 → 12, each via the identical six-part template
4. Practical Illustrations — whole-chart synthesis
```

Longevity comes first by Raman's explicit instruction: *"when a child has poor
longevity… however promising the horoscope may be, it will be futile to study
the future unless a long life is assured"* (HPA-14:41). → engine: `chart_overview` +
`longevity` are a **pre-pass** that gates and modulates all house judgment.

---

## 2. The unit of judgment

Every matter is judged on a 3 × 3 × 3 lattice:

- **Three pillars** (HTJAH-II:221, HTJAH-I:983): the **House**, its **Lord**, its **Karaka**
  — plus *secondary* factors: occupants of the house and associates of the lord.
- **Three charts** (HTJAH-I:973-979): apply every combination to the **Rashi**, the
  **Bhava (Chalita / cusp)**, and the **Navamsa**, then draw a conclusion.
  *"In the delineation of any house, it is the **Bhava that is important and not the
  Rashi**… The Navamsha is also equally important… the pivot on which the horoscope
  revolves."*
- **Three origins** (HTJAH-II:353, :675): reckon house positions from the **Lagna**,
  from the **Moon**, and — for the karaka's own significations — from the **Karaka**
  treated as a Lagna (e.g. marriage rules read "from Venus"). The master rule:
  *"the starting point should be either the ascendant or the Moon, whichever is
  stronger"* (HTJAH-I:645).

The lord carries a **dual function** (HTJAH-I:985): its **ownership** role *and* its
own intrinsic **karaka** role (e.g. for Aquarius Lagna the 7th-lord Sun is judged both
as 7th-lord and as father-karaka).

---

## 3. The 8 Considerations in Judging a House (verbatim, HTJAH-I:474-493)

1. Strength, aspects, conjunctions, **location of the lord** of the house.
2. **Strength of the house** itself.
3. Natural qualities of the house, its lord, and planets in/aspecting it (**karaka layer**).
4. Whether any **yoga** alters the influence.
5. **Exaltation/debilitation** of the lords.
6. Disposition of the lord (**and its dispositor**) in the **Navamsha**.
7. **Age / status / sex** of the subject.
8. **Functional** disposition — each sign has planets well- or ill-disposed to it.

Supporting rule (HTJAH-I:503): *if the lord is badly placed but the house itself has
good conjunctions/aspects, do **not** predict evil* — the bhava can rescue its lord.

---

## 4. Functional benefic / malefic — per-Lagna table (HTJAH-I:523-566)

Raman's own classification (note: "best/most" markers retained):

| Lagna | Benefics | Malefics | Neutrals |
|---|---|---|---|
| **Aries** | Jupiter (best), Mars, Sun | Mercury (worst, 3&6), Saturn, Venus | — |
| **Taurus** | Saturn (best, 9&10), Mercury, Mars, Sun | Jupiter, Moon | Venus (lagna lord) |
| **Gemini** | Venus (best) | Mars (worst, 6&11), Jupiter, Sun | Moon, Mercury |
| **Cancer** | Mars (best, 5&10), Jupiter | Venus, Mercury | Saturn, Moon, Sun |
| **Leo** | Mars (best), Sun | Mercury, Venus | Jupiter, Moon, Saturn |
| **Virgo** | Venus (best) | Moon, Mars, Jupiter | Saturn, Sun, Mercury |
| **Libra** | Saturn (best), Mercury, Venus | Sun, Jupiter, Moon | Mars (feeble benefic) |
| **Scorpio** | Moon (best), Jupiter, Sun | Mercury, Venus | Mars, Saturn |
| **Sagittarius** | Mars, Sun | Venus, Saturn, Mercury | Jupiter, Moon |
| **Capricorn** | Venus (best), Mercury, Saturn | Mars (worst), Jupiter, Moon | Sun (8th lord) |
| **Aquarius** | Venus, Sun, Mars | Jupiter, Moon | Mercury |
| **Pisces** | Moon, Mars | Saturn, Sun, Venus, Mercury | Jupiter |

**Generating rules** (HTJAH-I:573-604) — encode these, not just the table:
- **Benefic lords**: 1st (unless Moon); 5th & 9th (trikona); 4th/7th/10th *when not natural benefics*. Rank: 9th > 5th; 10th > 7th; 4th least benefic.
- **Malefic lords**: 3rd/6th/11th; 4th/7th/10th *if natural benefics* (**Kendradhipati dosha**). Rank: 11th worst, 6th less, 3rd least.
- **Neutrals**: Moon as Lagna-lord; Sun/Moon as 8th; Sun/Moon as 2nd or 12th.
- A natural benefic owning a kendra turns malefic — **but is redeemed when occupying its own kendra sign** (e.g. Venus in Libra for Cancer Lagna). Symmetric for a natural malefic kendra-lord.

---

## 5. Yoga Karakas & Raja Yogas (HTJAH-I:606-644)

- A planet owning **both a kendra and a trikona** is a **Yoga Karaka**. Only possible for **Mars** (Cancer/Leo), **Saturn** (Libra/Taurus), **Venus** (Capricorn/Aquarius).
- **Kendra-lord + trikona-lord association** → Raja Yoga. The **9th + 10th** lords give the most powerful; the combos 4&5, 7&5, 10&5, 4&9, 7&9, 10&9 are strong enough to overcome minor blemish.
- 9th & 10th lords **exchange**, or 9th-in-10th / 10th-in-9th, or **mutual aspect** → Raja Yoga.
- **Jupiter + Moon** mutual aspect / mutual kendra → fame & dignity (Gajakesari-class).
- Effective only within **~12° orb**; realised strength read from **Shadbala** (GBB).
- *Yogas are deliberately omitted from the house combination-lists in HTJAH* (HTJAH-I:337) — Raman treats them in **3HC**. → engine sources the yoga catalogue from **3HC**, not from the house chapters.

---

## 6. The per-house chapter template (shared shape)

Each house chapter (and each `house_NN_*.md`) follows six parts:

1. **Significations** of the house (karyas).
2. **Main Considerations** — the three pillars named, karaka identified, primary guidance.
3. **Lord-in-the-12-houses** — twelve readings, **each bifurcated** `fortified → … / afflicted → …` (HTJAH-II:235-340 pattern).
4. **Important Combinations** — rule records: `{condition, result, reference-frame ∈ {Lagna, Moon, Karaka}, citation}`; heavy use of *from-Karaka* and *from-Moon* origins.
5. **Planets-in-the-house** — the nine grahas, each a base reading + **aspect/association modifiers** (HTJAH-II:584).
6. **Timing of fructification** + **Nature of results** (dasha-phala) — see §7.

---

## 7. Timing model

- **Governing factors of a house** (HTJAH-II:671): (a) the lord, (b) planets aspecting the house, (c) occupants, (d) planets aspecting the lord, (e) associates of the lord, (f) **the lord of that house from the Moon**, (g) the **karaka**. Any of these can fructify the matter in its **Dasha / Bhukti / Antara**.
- **Two-level activation rule** (HTJAH-II:685): intensity is a function of *both* period lords —
  - MD-lord **and** AD-lord both related to the house → results *"par excellence"*.
  - only one related → results *"to a limited extent"*.
- **Tara modifier** (HTJAH-I:1142): a lord occupying the **3rd (vipat) / 5th (pratyak) / 7th (naidhana)** nakshatra from the Janma-Nakshatra **intensifies evil**; strong-lord in those taras lessens good.
- **Transit (gochara) confirmation** (HTJAH-I:932): death/events are corroborated by transit of the dasha-lord / Saturn over the relevant bhava, *judged from the Moon*.

---

## 8. Longevity sub-engine (Ayurdaya) — full procedure

Two stages **in strict order** (HPA-14:76): fix the **span class**, *then* find the **maraka** and time death within it. Raman's practical preference is **maraka-on-Vimshottari**, with **Pindayu/Amsayu as mathematical cross-checks** (he favours **Amsayu**) (HTJAH-II:3925).

### 8.1 Span classes (HPA-14:53)
- **Balarishta** (infant mortality): death **< 8** — gated first, with antidotes (HPA-14:229).
- **Alpayu** 8–32 · **Madhyayu** 33–75 · **Purnayu** 75–120 (Raman rejects the 32–70/100 variant; natural span = 120).
- Note (HTJAH-II:3917): span is not reliably fixed before age 12 (0–4 mother's karma, 4–8 father's, 8–12 native's).

### 8.2 Maraka (death-inflicting) determination (HTJAH-I:776-814)
Houses of **life** = 3rd & 8th; houses of **death** = **2nd & 7th**.
- **Primary**: lords of 2/7; malefic **occupants** of 2/7; malefic **associates** of those lords. *(Associates kill hardest; the lords themselves least — HTJAH-I:783.)*
- **Secondary**: benefics with 2/7 lords; lords of 3/8; 3rd/8th lord associated with 2/7 lord.
- **Tertiary**: Saturn touching any maraka; lord of 6/8; the **weakest planet** in the chart.
- Per-Lagna maraka list (HTJAH-I:800-814) — *guidance, not absolute* (:818):

  | Lagna | Maraka | Lagna | Maraka |
  |---|---|---|---|
  | Mesha | Mercury, Saturn | Tula | Jupiter |
  | Vrishabha | Jupiter, Mars | Vrischika | Mercury, Venus, Saturn |
  | Mithuna | Mars, Jupiter | Dhanus | Venus, Saturn |
  | Kataka | Venus, Mercury | Makara | Mars, Jupiter |
  | Simha | Mercury, Venus | Kumbha | Mars |
  | Kanya | Mars, Jupiter | Meena | Mercury, Saturn, Venus |
- Death is timed in the maraka's **dasha/bhukti**, confirmed by **transit** (HTJAH-I:932).

### 8.3 Pindayu Method (HTJAH-II:3947) — "Grahadattayurdaya"
**Full terms** (deep exaltation / deep debilitation, years):
Sun 19 / 9.5 · Moon 25 / 12.5 · Mars 15 / 7.5 · Mercury 12 / 6 · Jupiter 15 / 7.5 · Venus 21 / 10.5 · Saturn 20 / 10.

1. **Arc of longevity** = (planet longitude − its exaltation longitude); if < 180° subtract from 360°, else keep.
2. **Contribution** = full_term × arc ÷ 360°.
3. **Four Haranas (reductions), applied in order — each to the *running remainder*, not the original term:**
   - **Chakrapatha** (HTJAH-II:4017) — planets in visible half (bhavas 7→12, *above horizon*) lose a fraction; bhavas 1–6 **exempt**; only the *strongest* planet per house:

     | bhava | 12 | 11 | 10 | 9 | 8 | 7 |
     |---|---|---|---|---|---|---|
     | malefic | 1 | 1/2 | 1/3 | 1/4 | 1/5 | 1/6 |
     | benefic | 1/2 | 1/4 | 1/6 | 1/8 | 1/10 | 1/12 |
   - **Satrukshetra** (HTJAH-II:4050) — planet in enemy sign loses 1/3 of remainder; **Mars & retrograde exempt**.
   - **Astangata** (combustion, HTJAH-II:4062) — combust planet loses 1/2; orbs Moon 12° Mars 17° Mercury 14° Jupiter 11° Venus 10° Saturn 5° (retro Merc 12°, Venus 8°); **Venus & Saturn exempt even when combust**.
   - **Krurodaya** (HTJAH-II:4083) — malefic in Lagna: deduct (Lagna amsas-passed × total terms) ÷ 108; halved if the malefic is aspected by a benefic; use the planet nearest the Lagna degree.
4. Add **Lagna's own contribution** (navamsas passed → years), then total.
   *Worked Chart 33 → 86y 2m 20d (HTJAH-II:4260).*

### 8.4 Amsayu Method (HTJAH-II:4262) — Raman's favoured one
**Base term**: longitude-in-minutes ÷ 200 = navamsas from Aries (quotient); quotient ÷ 12 → remainder = navamsas-in-sign = whole years; fraction = part-year. Same for Lagna.
**Bharanas (increases)**:
- (a) exalted **or** retrograde → ×3
- (b) vargottama **or** own-navamsa **or** own-rasi **or** own-drekkana → ×2
- (c) if both apply, multiply **once** by the stronger factor only.
**Haranas**: same Chakrapatha / Satrukshetra (Mars & retro exempt) / Astangata (Venus & Saturn exempt); **Krurodaya does NOT apply in Amsayu** (HTJAH-II:4327).
**Method selection** (HTJAH-II:4264): use **Amsayu when the Lagna-lord is stronger than both Sun and Moon** (Manittha/Saravali); Pindayu when Sun strongest; Nisargayu when Moon strongest. Satyacharya/Varahamihira: longevity hinges on the **Navamsa** position.

---

## 9. Doctrine locked to Raman (intentional divergences from the repo's blended engine)

| # | Decision | Raman basis | Repo lock it diverges from |
|---|---|---|---|
| D1 | **Ayanamsa = Raman** (`SIDM_RAMAN`) by default; Lahiri configurable | his book charts are cast on it; ~0.9–1.4° behind Lahiri | CLAUDE.md Lahiri lock — namespaced to `app/raman_saab/`, never mutates global |
| D2 | **Bhava (Chalita / Sripati cusp) judged, not Rashi** | HTJAH-I:973 verbatim | repo whole-sign (whole-sign retained for lordship/aspects only) |
| D3 | **Rahu/Ketu cast only the 7th aspect** (no special 5/9) | HTJAH-II nodes used by opposition only | `app/core/drishti_argala.py` 5/9 (Bhasin/Nadi) — own table, guard test |
| D4 | **Fixed naisargika + bhava karakas** (no Jaimini chara) | HTJAH judges via fixed karakas | orthogonal to the Jaimini chara-karaka lock |
| D5 | **Real Shadbala in Rupas** arbitrates contradictions | GBB Ch.3–10 | — (re-derived to Raman's own numbers) |

---

## 10. Engine mapping

| Doctrine here | Module |
|---|---|
| §1 macro sequence | `proforma.py` (orchestration) |
| §2 three origins / three charts | `primitives/chalita_bhava.py`, `primitives/navamsa.py`, origin helpers |
| §3 eight considerations | `judges/house_template.py` |
| §4 functional nature | `doctrine/functional_nature.py` (per-Lagna table + generating rules) |
| §5 yoga karakas / raja yogas | `doctrine/yogas/*` (catalogue from 3HC), `primitives/strength.py` |
| §6 per-house template | `judges/house_01.py … house_12.py` (+ `doctrine/significations.py`, `doctrine/karakas.py`) |
| §7 timing | `judges/timing.py` (two-level MD×AD, tara, gochara) |
| §8 longevity | `judges/longevity.py` + `doctrine/ayus_tables.py` + `primitives/maraka.py` |
| §9 divergences | `doctrine/sources.py` (cited), guard tests |

> **Golden tests**: Raman's worked example charts (e.g. HTJAH-II Chart 33 → 86y 2m 20d longevity; the Chart No. 1–10 personality reads in HTJAH-I) are the regression fixtures — see each house file's *Example Insights* section.
