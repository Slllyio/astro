---
title: "Raman doctrine compendium"
kind: reference
topic: doctrine
measured: false
updated: 2026-06-27
words: 974
tags: [raman-saab, reference, doctrine]
---
# Raman doctrine compendium

A structured digest of engine-relevant doctrine from the prioritized B.V. Raman corpus,
produced by the Phase-1 extraction sweep (2026-06-14/15). Each entry: the doctrine, its
`WORK:line` citation, and the engine channel it maps to. The actionable, ranked version is
`DOCTRINE_BACKLOG.md`; this file is the reference. (Consolidated into one file per-book
section rather than separate files, for scannability.)

Corpus reach: the engine cites 4 of 13 Raman books today (HTJAH-I/II, 3HC, HPA-20). GBB-N
citation resolvers exist and pass `verify()` — these books are citable, just un-mined.

---

## How to Judge a Horoscope Vol I (HTJAH-I) — the three-factor method
*Headline: when bhava, lord, and karaka conflict, the **strongest single factor dominates**;
two-of-three strong assures the matter; a weak/combust dominant factor denies it.*

- **HTJAH-I:3713** — "Of the three elements, the third lord is more powerful than the third
  house or Mars." → strongest factor decides. `judge-mechanism`
- **HTJAH-I:3788** — "Though the Karaka Mars is well disposed, the ruler of the third becoming
  combust and hence powerless, renders the third house weak. This stands against his having
  any brothers." → a combust/weak **lord** denies despite a strong karaka (**chart_59**).
- **HTJAH-I:3815** — "the Karaka and the third house are subject to affliction. The native has
  no brothers." → house+karaka afflicted → denied even with a good lord (**chart_60**).
- **HTJAH-I:2760** — "all the three factors connected with the second house are strong and
  well-fortified → immense wealth." (tri-strong → decisive favourable)
- **HTJAH-I:2111** — "a steady flow of fortune is assured if at least two of the three are
  well disposed." (≥2-of-3 preponderance)
- **HTJAH-I:13961** — "the reckoning made from the strongest of these three centers
  (Lagna/Moon/Sun) gives good results." (strength-based frame selection)
- **HTJAH-I:4374** — "the evils will be somewhat tempered if the fourth lord is more powerful
  than the twelfth lord." (comparative dual-lord weighing)
- **HTJAH-I:8170** — Mars in the 7th → "clashes and tensions or there may be two wives."
  `new-rule` (H7)
- Neechabhanga conditions (HTJAH-I:1822/1984/2037) — **already encoded**.

## How to Judge a Horoscope Vol II (HTJAH-II) — marriage & Kuja-Dosha
*Headline: Kuja-Dosha cancellation is a sign-exception table (already encoded); the live H7
gaps are the blemishless-Venus override and dual-sign multiplicity.*

- **HTJAH-II:2579** — Kuja-Dosha is about **death** of the spouse ("the death of the husband
  will occur"), in ascending strength 2<12<4<7<8. → distinct from marital *happiness*
  (basis for the B3 non-death-marital maraka guard). `judge-mechanism`
- **HTJAH-II:2593-2601** — cancellation: Mars exempt in 2nd if Gemini/Virgo, 12th if
  Taurus/Libra, 4th if Aries/Scorpio, 7th if Cancer/Capricorn, 8th if Sagittarius/Pisces;
  Leo/Aquarius wholly exempt; Mars+Jupiter or Mars+Moon conjunction cancels. → **already
  encoded** in `_KujaDosha`. `cancellation` (closed)
- **HTJAH-II:1207, 368** — a **blemishless Venus** (exalted/own/good-vargas) as karaka+7th-lord
  aspecting the 7th → chaste devoted wife. `new-rule` (B4; chart_03/08)
- **HTJAH-II:1474** — a **Yogakaraka Venus in a fixed sign** overrides dual-sign multiplicity
  ("fixity of affections"). `new-rule`
- **HTJAH-II:484, 997** — 7th lord & Venus in common/dual signs → ≥2 marriages. `new-rule`
- **HTJAH-II:361** — Mars+Saturn in the 7th in **Capricorn** → chaste/beautiful/lucky wife
  (exalted Saturn converts Mars). `cancellation`
- **HTJAH-II:966-977** — widowhood vs mutual-death vs survival discriminators (7th/8th lords
  in 8th; Rahu+Saturn+Mars in 7th/8th; papakartari on 7th; benefics in 9th → long life
  together). `new-rule` (H8 maraka differentiation)

## Graha & Bhava Balas (GBB) — strength methodology
*Headline: strength is continuous (0 at bhava-sandhi → full at madhya); paksha-bala already
in the engine — the marginal gap is threshold handling.*

- **GBB-1:38-60** — "If a planet is in a Bhava Sandhi it is utterly powerless"; residential
  strength scales 0→1 from cusp to midpoint. `threshold` (B2; chart_03/08 Venus marginal)
- **GBB-5:215-223** — paksha-bala: benefics strong in Sukla, malefics in Krishna; Moon's
  doubled. → **already implemented** (`kala.py:81`). `shadbala` (closed)
- **GBB-3** sthana, **GBB-5** kala (9 sub-balas incl Nathonnatha/Thribhaga/Ayana), **GBB-6**
  cheshta, **GBB-10** ishta/kashta — the strength stack; mostly **already encoded**. Ishta/
  kashta phala (√(ochcha×cheshta)) is a unified good/bad scalar useful for dasa-lord eval
  (`judge-mechanism`, longer-horizon).

## Hindu Predictive Astrology (HPA) — 3 yogas live (2026-06-27)
*Headline: ~16 named yogas + avastha doctrine + house rules the HTJAH-only engine lacks.*

- **HPA-20 named yogas** `new-rule` (B5): **ENCODED (additive, zero-regression, reviewer KEEP):**
  - **Y.CHAMARA** (HPA-20:65) — lagna-lord exalted in a kendra + Jupiter's aspect (strict first
    arm only; the "two benefics in 1/7/10" arm OMITTED — over-fired 35/164).
  - **Y.SREENATHA** (HPA-20:90) — exalted 7th-lord in the 10th + 9th/10th lords conjoined.
  - **Y.KHADGA** (HPA-20:184) — 2↔9 lord exchange (parivartana) + lagna-lord in kendra/trikona.
  **DEFERRED (over-fire under current primitives — need B1 effective-strength):** Shankha
  (HPA-20:77, hinges on "powerful lord", fired 102/164), Kahala (HPA-20:151, 48/164), Lakshmi
  (HPA-20:190, strict dignity arm still 16/164). **REJECTED (noise):** Sun-based Vasi/Vesi/
  Obhayachari (near-universal). Remaining un-mined: Bheri, Sarada, Matsya, Mridanga, Konrma,
  Kusimia, Daridra, Rajju — revisit with goldens that exercise them.
- **HPA-19:47** — a planet's results vary by its **avastha/disposition**, not mere occupancy
  (exalted Jupiter in 4th = religious learning; debilitated differs). `judge-mechanism`
- **HPA-7:39-83** — the 10 avasthas (Deeptha…Bhita). `shadbala` (longer-horizon)
- **HPA-19:247** — 4th lord in 12th → loss of ancestral property. `new-rule` (B6, H4)

## Three Hundred Important Combinations (3HC) — ~9 of ~300 used
*Headline: Dhana yogas for H2/H11 and Nabhasa distribution yogas are the highest-value adds.*

- **3HC:7632** Dhana #122 (Venus-5th + Saturn-11th); **3HC:7645** #125 (Sun-5th-own +
  Moon/Jupiter-11th); **3HC:8184** Bahudravyarjana #133 (lagna→2nd→11th→lagna lord chain).
  `new-rule` (H2/H11)
- **3HC:4256** Lakshmi #72 (lagna-lord powerful + 9th-lord own/exalt in kendra/trikona).
  `new-rule` (H9/H11)
- **3HC:2442** Adhi #7 — **already encoded** (Y.ADHI).
- **3HC:7083** Rajju/Musala/Nala; **3HC:7175** Srik/Sarpa; **3HC:7320** Harsha/Sarala/Vimala
  (Vipareeta family — audit overlap with Y.VIPAREETA). `new-rule` (chart health)
- **3HC:4080** Mahabhagya (Sun/Moon/Lagna all odd [m] / even [f]); **3HC:4172** Pushkala.
  `new-rule` (general fortune)

---

### Skim-only catalog (deferred — `catalog-only`)
Jaimini (alternate system), Varshaphal (annual), Prasna Tantra (horary), Manual of Hindu
Astrology (superseded by HPA), Astrological Magazine (periodical). Out of scope for the
current Parashari natal engine; revisit only if the roadmap expands to those domains.
