---
title: "Raman Saab — GBB Shadbala Reference (Phase 1c doctrine spec)"
kind: reference
topic: doctrine
measured: false
updated: 2026-07-24
words: 2233
tags: [raman-saab, reference, doctrine]
---
# Raman Saab — GBB Shadbala Reference (Phase 1c doctrine spec)

> Line-cited extraction of **B.V. Raman's *Graha & Bhava Balas*** (GBB) Shadbala, the
> authority for `app/raman_saab/primitives/shadbala.py` et al. Synthesised from a 4-agent
> parallel read of GBB Ch.3–10 + a direct read of Ch.4, cross-validated against the book's
> own fully-worked example. Citations are `GBB-N:line` (N = chapter, file
> `data/knowledge_library/sources/graha_bhava_balas_raman/chapter_00N_*.md`).
>
> **This is the single source of truth for Phase 1c.** Every constant/formula below is what
> the engine must implement; the §11 fidelity traps are where naive/modern Shadbala silently
> diverges; the §10 fixture is the ±1-rupa regression target.

## 0. Units (GBB-3:38-41)

- **1 Rupa = 60 Shashtiamsas** (Shashtiamsa = Virupa = 1/60 Rupa). All component math is in
  Shashtiamsas; divide the total by 60 for Rupas.
- **Only the 7 visible grahas** get Shadbala (Sun..Saturn). **No Rahu/Ketu** (every GBB table
  lists exactly Ravi..Sani) — consistent with the repo's chayagraha lock.

## 1. Sthana Bala (positional) — GBB-3 — **5** sub-components, summed

> The total-table header says "six sub-divisions" (GBB-3:701) but lists **five** rows — an OCR
> slip from "Shad-Bala". Implement **five**.

### 1.1 Ochcha Bala (exaltation) — GBB-3:43-115
```
diff = (planet_lon − debilitation_point) mod 360
if diff > 180: diff = 360 − diff          # "corrected difference", GBB-3:112
Ochcha = diff / 3                          # Shashtiamsas (0 at debilitation, 60 at exaltation)
```
Debilitation points (deep-fall longitudes; exaltation = +180°), GBB-3:85-110 — match the
project's `relationships.EXALTATION`/`DEBILITATION` exactly:
`Sun 190°, Moon 213°, Mars 118°, Mercury 345°, Jupiter 275°, Venus 177°, Saturn 20°`.

### 1.2 Saptavargaja (Moolatrikonadi) Bala — GBB-3:447-543
Sum a dignity value over the **7 classical vargas D1,D2(Hora),D3,D7,D9,D12,D30** (GBB-3:339):

| Dignity in the varga | Shashtiamsas |
|---|---|
| Moolatrikona | **45** — *only in D1* (GBB-3:469-476) |
| Own (Swavarga) | 30 |
| Great friend (Adhi Mitra) | 22.5 |
| Friend (Mitra) | 15 |
| Neutral (Sama) | 7.5 |
| Enemy (Satru) | 3.75 |
| Great enemy (Adhi Satru) | 1.875 |

Relationship = **compound** naisargika+tatkalika (GBB-3:247-265): temporary friend = other
planet in the 2/3/4/10/11/12 from it (GBB-3:210). Compound table: T-friend+N-friend=AdhiMitra;
T-friend+N-enemy=Sama; T-friend+N-neutral=Mitra; T-enemy+N-enemy=AdhiSatru; T-enemy+N-friend=Sama;
T-enemy+N-neutral=Satru. **Constants 22.5 and 1.875 are not clean halvings — hard-code literally.**
Reuse the project's `dignity._compound_relation` (already implemented in Phase 1a) per varga;
the only new piece is the per-varga lord lookup (navamsa_lord, drekkana_lord exist; need
hora/saptamsa/dwadasamsa/thrimsamsa lords).

### 1.3 Ojayugma (odd/even) Bala — GBB-3:546-601
`+15` if rasi parity matches preference, `+15` if navamsa-sign parity matches (independent, max 30).
Preference: **even** for Moon & Venus; **odd** for Sun, Mars, Jupiter, Mercury, Saturn.

### 1.4 Kendra Bala — GBB-3:603-651 — **by SIGN (rasi), not Bhava** (GBB-3:609)
Kendra {1,4,7,10}=60 · Panapara {2,5,8,11}=30 · Apoklima {3,6,9,12}=15. **Rasi-varga only.**

### 1.5 Drekkana Bala — GBB-3:653-697 — by planetary sex, 15 each
Masculine {Sun, Jupiter, Mars} → 1st decanate (0-10°); Hermaphrodite {Saturn, Mercury} → 2nd
(10-20°); Feminine {Moon, Venus} → 3rd (20-30°). Else 0.

**Sthana = Ochcha + Saptavargaja + Ojayugma + Kendra + Drekkana** (GBB-3:699).

## 2. Dig Bala (directional) — GBB-4 (read directly; confirmed)

Per-planet powerful house (full 60) / powerless point (0, 180° opposite):
Jupiter & Mercury → **1st** (Lagna) · Sun & Mars → **10th** · Saturn → **7th** · Moon & Venus → **4th** (GBB-4:35-43).
```
arc = (planet_lon − powerless_point) mod 360   # powerless = bhava-madhya 180° from the powerful cusp
if arc > 180: arc = 360 − arc
Dig = arc / 3                                   # Shashtiamsas
```
**FIDELITY TRAP (GBB-4:91):** the reference is the **Bhava-madhya (cusp mid-point)**, NOT the
rasi/bhava-begin. Worked: Saturn lon 124°51′, 7th-bhava-madhya 114°57′ → powerless 294°57′ →
arc 170°6′ → 170.1/3 = **56.7** (GBB-4:95-100). (For ephemeris-free Track-B fixtures lacking
cusps, the engine must accept stated bhava-madhyas; see §10.)

## 3. Kala Bala (temporal) — GBB-5 — 9 sub-components, summed (GBB-5:28-32)

1. **Nathonnatha** (GBB-5:115-147): birth-time-from-midnight → degrees @15°/hr; if >180 use 360−.
   `Diva (Sun,Jup,Venus)=deg/3 ; Ratri (Moon,Mars,Saturn)=(180−deg)/3 ; Mercury=60 always.` (complementary to 60)
2. **Paksha** (GBB-5:215-223): `s=((Moon−Sun) mod 360); if s>180: s=360−s; shubha=s/3`.
   Benefics(Jup,Venus,waxing-Moon,good-Merc)=shubha; malefics(Sun,Mars,Saturn,afflicted-Merc)=60−shubha.
   **Moon's Paksha is DOUBLED** (GBB-5:220).
3. **Tribhaga** (GBB-5:253-320): day & night each in 3; ruler of the birth-third gets **60**;
   day thirds = Mercury/Sun/Saturn, night thirds = Moon/Venus/Mars; **Jupiter always 60** (GBB-5:271).
4-7. **Abda 15 / Masa 30 / Vara 45 / Hora 60** (GBB-5:563-596) to the year/month/weekday/hora lord.
   Lords via Ahargana (yr=360d, mo=30d): year `q×3+1 mod 7`, month `q×2+1 mod 7`, day `Ahargana mod 7`
   (GBB-5:343-450). **Hora order = Chaldean descending Saturn→Jupiter→Mars→Sun→Venus→Mercury→Moon**,
   seeded by the weekday-lord at sunrise (GBB-5:606-627).
8. **Ayana** (declination) — GBB-5:936-957 — **FIDELITY TRAP**:
   ```
   Ayana = ((24 ± kranty) / 48) × 60          # max-decl 24° (NOT 23°27′); denom 48 = 2×24
   DOUBLE for the Sun.
   ```
   Sign of `kranty` per group (GBB-5:949-967): Sun/Mars/Jupiter/Venus → North additive, South subtractive;
   Saturn/Moon → South additive, North subtractive; **Mercury always additive**. Longitudes must be
   **Sayana** (add ayanamsa). Declination via the 6×15° cumulative table (362/703/1002/1238/1388/1440′)
   with linear interpolation (GBB-5:794-878). At equator value = 30.
9. **Yuddha** (planetary war, GBB-5:1001-1043): planets <1° apart; lesser-longitude wins;
   `Yuddha = |ΔBala| / Δdisc-diameter`; victor += , loser −= . Disc diameters (″): Mars 9.4,
   Mercury 6.6, Jupiter 190.4, Venus 16.6, Saturn 158.0. Sun/Moon never at war.

## 4. Cheshta Bala (motional) — GBB-6 — **5 planets only** (Mars,Mercury,Jupiter,Venus,Saturn)

> **FIDELITY TRAP (the single most important divergence):** GBB gives the **Sun and Moon NO
> Cheshta Bala** in the six-component Shadbala (their cells are blank, GBB-6:23-28, GBB-8:286).
> Modern blended Shadbala wrongly assigns Sun→Ayana and Moon→Paksha as Cheshta. Do NOT.
> (Sun/Moon Cheshta surrogates are computed ONLY for Ishta/Kashta — §9.)

```
ChestaKendra = Seegrochcha − (MeanLong + TrueLong) / 2    # Sripathi (CORRECTED, see note)
if ChestaKendra < 0:   ChestaKendra += 360
if ChestaKendra > 180: ChestaKendra = 360 − ChestaKendra  # reduced Chesta Kendra
Chesta = ChestaKendra / 3                                 # Shashtiamsas (0 at 0°, 60 at 180°)
```
> **OCR CORRECTION (resolved + validated):** Raman's text prints the formula as `Seegrochcha −
> (Mean Long − true long)` (GBB-6:547-551), but that does NOT reproduce his own worked Chesta
> Kendras. The real Sripathi formula is `Seegrochcha − (Mean + True)/2` (the OCR mangled `+ … ÷2`
> into `−`). Confirmed against an external Sripathi source and **validated to the decimal** against
> all 5 of Raman's Ex.49-51 values: Kuja CK 293.15→22.28, Budha 353.60→2.13, Guru 105.99→35.33,
> Sukra 342.70→5.76, Sani 63.19→21.06. Use the corrected form.

**Inputs (GBB-6:88-104):** **5 planets only** (Mars,Mercury,Jupiter,Venus,Saturn — Sun/Moon get
NO Cheshta in the Shadbala total). `Seegrochcha` = **Mean Sun** for superior planets (Mars,Jup,Sat);
for Budha/Sukra it's their own apogee from epoch tables. `MeanLong` of superior planets + the Sun
via Raman's **epoch method** (epoch 1 Jan 1900 Ujjain 76°E: mean-Sun const 257.4568; Mars 270.22;
Jup 220.04 −(3.33+.0067·t); Sat 236.74 +(5+.001·t); t=birthyear−1900) — Mean Budha/Sukra = Mean Sun.
For the **Track-B fixture**, inject Raman's stated Standard-Horoscope means (MeanSun/Budha/Sukra
181.2275, Mars 266.34, Jup 66.91, Sat 111.23; Seeg Budha 174.49, Sukra 158.35) and pin the 5
ChestaBala values. For **real charts**, compute mean longitudes via the epoch constants OR
`swisseph` mean elements (`swe.get_orbital_elements` exists in 2.10.x). **No discrete 8-state
table** — pure Sripathi arc. Sun/Moon Cheshta surrogates (Ishta/Kashta only) = §9.

## 5. Naisargika Bala (natural) — GBB-7 — fixed constants (the 60/7 ladder)

`Sun 60.00 · Moon 51.43 · Venus 42.85 · Jupiter 34.28 · Mercury 25.70 · Mars 17.14 · Saturn 8.57`
(Shashtiamsas; = rank×60/7, Saturn rank1…Sun rank7). Identical in every chart. (GBB-7:44-63)

## 6. Drik Bala (aspectual) — GBB-8

Aspect angle `K = (aspected_lon − aspecting_lon) mod 360`. Sripathi piecewise Dristi value (Sh):

| K range | value |
|---|---|
| 30–60 | **(K−30)/2** |
| 60–90 | (K−60)+15 |
| 90–120 | 45 − (K−90)/2 |
| 120–150 | 150−K |
| 150–180 | (K−150)×2 |
| 180–300 | (300−K)/2 |
| else | 0 |

*(Branches verified live to hit Raman's stated anchors GBB-8:27-46 — 30°→0, 60°→**15**, 90°→45,
150°→0, 180°→60, 300°→0 — and to be continuous at every join. The 30–60 branch is `(K−30)/2`
NOT `K−30` (the latter gives 30 at 60° and breaks the 15-at-60° anchor); the 90–120 branch
`45−(K−90)/2` is OCR-reconstructed but forced by the 45@90°/30@120° anchors. Pin the whole
function against an external Sripathi Shadbala table before Phase-3 verdicts lock.)*

**Visesha (special) Dristi** added for the aspecting planet when it truly casts it (GBB-8:172-191):
Mars 4th(90-120)&8th(210-240)=+15 · Jupiter 5th(120-150)&9th(240-270)=+30 · Saturn 3rd(60-90)&10th(270-300)=+45.
Sign: benefic (Jup,Venus,waxing-Moon,good-Merc) **+**, malefic (Sun,Mars,Saturn,waning-Moon,bad-Merc) **−**.
```
DristiPinda(target) = Σ signed Dristi values of all aspecting planets
Drik = DristiPinda / 4                          # signed, Shashtiamsas (GBB-8:241)
```

## 7. Total Shadbala + min-required thresholds — GBB-8

```
ShadbalaPinda = Sthana + Dik + Kala + Chesta + Naisargika ± Drik    # Drik signed (GBB-8:262)
Rupas = ShadbalaPinda / 60
```
**Minimum-required total Shadbala (Rupas)** — the verdict-engine thresholds (GBB-8:303-312):

| Sun | Moon | Mars | Mercury | Jupiter | Venus | Saturn |
|---|---|---|---|---|---|---|
| 5 | 6 | 5 | 7 | 6.5 | 5.5 | 5 |

## 8. Bhava Bala (house strength) — GBB-9 — 3 factors, summed (GBB-9:38,281)

1. **Bhavadhipathi** = the **full Shadbala Pinda of the bhava's lord** (lord = owner of the
   sign holding the bhava-madhya). (GBB-9:47)
2. **Bhavadig** = strength from the bhava-madhya sign-class (GBB-9:76-178): Nara
   {Gem,Vir,Lib,1st-half-Sag,Aqu}→max 1st; Jalachara {Can,2nd-half-Cap,Pis}→max 4th; Chatushpada
   {Ari,Tau,Leo,2nd-half-Sag,1st-half-Cap}→max 10th; Keeta {Sco}→max 7th. Rule: |ref−bhava|
   (ref by class: 1/4/7/10); if >6 use 12−; ×10 = Shashtiamsas.
3. **Bhava Drig** = aspect on the bhava-madhya (treat as a Drushya); **full** Dristi for Jupiter
   & Mercury, **¼** for others; signed (GBB-9:210-219).

## 9. Ishta / Kashta Phala — GBB-10 (Shashtiamsas, 0-60)

```
Ishta  = sqrt(OchchaBala × ChestaBala)               # GBB-10:93
Kashta = sqrt((60 − OchchaBala) × (60 − ChestaBala)) # GBB-10:114
```
**Sun/Moon Chesta surrogates (ONLY here, GBB-10:46-90):** Sun `ChestaKendra = Sayana_lon + 90`
(>180 → 360−), /3 ; Moon `ChestaKendra = (Moon−Sun) mod 360` (>180 → 360−), /3.

## 10. The regression fixture — GBB "Standard Horoscope" (GBB-8:280-298)

**Birth:** 16 Oct 1918, ~2:00 PM LMT (2:14 LAT), Wednesday, **Libra Lagna**. Lat/long not stated
(Raman's nativity; ~Bangalore). **Stated Nirayana longitudes** (use via `from_stated_positions`,
Track-B / ephemeris-free): Sun 179°08′, Moon 311°40′, Mars 229°49′, Mercury 180°33′, Jupiter
83°35′, Venus 170°04′, Saturn 124°51′ (Rahu 53°23′, Ketu 233°23′). 7th-bhava-madhya 114°57′ (for Dig).

**The gold table — all six Graha-Balas (Shashtiamsas) + total (Rupas):**

| Component | Sun | Moon | Mars | Mercury | Jupiter | Venus | Saturn |
|---|---|---|---|---|---|---|---|
| Sthana | 147.975 | 141.650 | 194.700 | 294.800 | 157.450 | 157.925 | 162.400 |
| Dik | 48.070 | 32.250 | 55.030 | 21.860 | 10.450 | 14.950 | 56.700 |
| Kala | 104.490 | 202.750 | 28.390 | 219.920 | 211.930 | 116.810 | 115.690 |
| Chesta | — | — | 22.280 | 2.130 | 35.330 | 5.760 | 21.060 |
| Naisargika | 60.000 | 51.430 | 17.140 | 25.700 | 34.280 | 42.850 | 8.570 |
| Drik | +16.720 | −11.900 | +5.350 | +16.050 | −6.570 | +18.670 | +7.370 |
| **Total (Rupas)** | **6.288** | **6.936** | **5.381** | **9.743** | **7.381** | **5.949** | **6.196** |

Verdict (GBB-8:317): all 7 clear their minimums → **all powerful**; Mercury strongest, Mars weakest.
**Bhava-bala totals (Rupas, GBB-9:289):** I 6.70 · II 6.66 · III 7.54 · IV 6.43 · V 10.20 · VI 9.78
· VII 7.48 · VIII 7.45 · IX 7.06 · X 7.64 · XI 8.50 · XII 9.66 (5th strongest, 4th weakest).
**Ishta/Kashta (GBB-10):** e.g. Venus Ishta 3.63 / Kashta 55.94 (misery); Jupiter Ishta 44.56 / Kashta 9.73.

> **Fixture caveats:** OCR damaged some *intermediate* cells, but the three independently-clean
> totals (Jupiter 157.450, Venus 157.925, Saturn 162.400 Sthana) reconcile exactly with summed
> sub-components, validating the method end-to-end. The Sthana Sun/Moon totals here (147.975/141.650)
> differ slightly from Ch.3's standalone Ex.13 (162.975/126.650) due to OCR in the Drekkana column —
> **pin to the Ch.8 Ex.56 totals**, the consolidated authority. Pin component tests at **±1 rupa**
> (per spec §4.6), not to the Shashtiamsa decimals.

## 11. Fidelity traps & external-pin flags (the whole point of re-deriving)

1. **Sun/Moon get NO Cheshta Bala** in the Shadbala total (only in Ishta/Kashta). §4. — biggest divergence.
2. **Dig-bala from the bhava-madhya cusp**, not rasi/bhava-begin. §2.
3. **Ayana-bala: max-decl 24°, denom 48°, Sun doubled**, planet-group sign table. §3.8.
4. **Paksha-bala: Moon doubled.** §3.2.
5. **Kendra-bala by SIGN, not bhava.** §1.4.
6. **Saptavargaja: 45 only in D1**; 22.5 & 1.875 hard-coded. §1.2.
7. **Drekkana-bala by planetary sex** (Raman's groupings, not other sexings). §1.5.
8. **Hora-lord = Chaldean descending order**, seeded at sunrise. §3.4-7.
9. **EXTERNAL-PIN before locking:** the Drik 90-120° branch (`45−(K−90)/2`, OCR-reconstructed)
   and the navamsa64 +63/+64 (Phase 1b carry-over) — pin against Jagannatha Hora / an external
   Sripathi Shadbala table.

## 12. Phase 1c build decomposition (each pinned to the §10 fixture)

| Sub-plan | Components | Ephemeris? | Fixture columns |
|---|---|---|---|
| **1c-1** | Sthana, Naisargika, Dig, Drik (the **pure / cusp** components) | no (Track-B + stated cusps) | Sthana, Naisargika, Dik, Drik |
| **1c-2** | Cheshta (mean longitudes), Kala (declination, sunrise/ghatis, Ahargana) | **yes** (epoch/ephemeris) | Chesta, Kala |
| **1c-3** | total Shadbala assembly + min-required verdict; Bhava-bala; Ishta/Kashta; wire `shadbala_rupas`/`ishta`/`kashta` into `PlanetPos`; backfill maraka `strength_rank` + weakest-planet, balarishta strength checks | composite | Total, Bhava, Ishta/Kashta |

`ShadbalaBreakdown(sthana, dig, kala, cheshta, naisargika, drik, total)` already exists in
`app/raman_saab/chart/model.py` — 1c fills it. `PlanetPos.shadbala_rupas/ishta/kashta` are the
`Optional=None` fields 1c-3 wires.
