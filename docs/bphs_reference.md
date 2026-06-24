# BPHS Reference — Classical Sources for `app/core/` Primitives

**Purpose**: every rule in our dignity / strength / yoga engine cites a BPHS sloka here. When traditions disagree, we name the chosen convention and the alternatives considered.

**Anchor translation**: Santhanam (1984, Ranjan Publications) unless otherwise noted. Cross-checked against Sharma (1995) and Sastri/Iyer (1992) where the sloka is ambiguous.

**How to use this doc**:
- Adding a new rule → add a section here citing the sloka BEFORE shipping the code.
- Auditing a failing reference chart → start here, check whether our code matches the documented convention.
- Disagreement between Jagannatha Hora and our output → check the "Tradition-choice register" at the bottom; usually a documented difference, not a bug.

---

## 1. Dignity (`app/core/dignity.py`)

### 1.1 Own signs (sva-kshetra)

**Sloka**: BPHS 3.20 (Graha Guna Swaroopa Adhyaya)
**Rule**: each planet rules specific signs. Sun rules Leo (5); Moon rules Cancer (4); Mars rules Aries (1) and Scorpio (8); Mercury rules Gemini (3) and Virgo (6); Jupiter rules Sagittarius (9) and Pisces (12); Venus rules Taurus (2) and Libra (7); Saturn rules Capricorn (10) and Aquarius (11).
**Code**: `OWN_SIGNS` constant. Matches BPHS exactly.
**Tradition register**: none — universally agreed.

### 1.2 Exaltation (uchcha)

**Sloka**: BPHS 3.40
**Rule**: Sun exalted in Aries; Moon in Taurus; Mars in Capricorn; Mercury in Virgo; Jupiter in Cancer; Venus in Pisces; Saturn in Libra.
**Code**: `EXALTATION` constant. Matches BPHS exactly.

### 1.3 Debilitation (neecha)

**Derivation**: 180° / 6 signs from exaltation (BPHS implicit).
**Code**: `DEBILITATION` derived programmatically as `(exalt_sign − 1 + 6) % 12 + 1`.
**Tradition register**: universally agreed.

### 1.4 Naisargika friendship matrix

**Sloka**: BPHS 3.55
**Rule** (asymmetric by design):
- Sun:     friends — Moon, Mars, Jupiter; neutral — Mercury; enemies — Venus, Saturn.
- Moon:    friends — Sun, Mercury; neutrals — Mars, Jupiter, Venus, Saturn; **no enemies**.
- Mars:    friends — Sun, Moon, Jupiter; neutrals — Venus, Saturn; enemy — Mercury.
- Mercury: friends — Sun, Venus; neutrals — Mars, Jupiter, Saturn; enemy — Moon.
- Jupiter: friends — Sun, Moon, Mars; neutral — Saturn; enemies — Mercury, Venus.
- Venus:   friends — Mercury, Saturn; neutrals — Mars, Jupiter; enemies — Sun, Moon.
- Saturn:  friends — Mercury, Venus; neutral — Jupiter; enemies — Sun, Moon, Mars.

**Code**: `NAISARGIKA_FRIENDSHIP`. Audit confirmed exact match for 7 lights.
**Asymmetric pairs (important — do NOT mistakenly symmetrise)**: Mars views Saturn as neutral, but Saturn views Mars as enemy; Sun views Mercury as neutral, but Mercury views Sun as friend.

**Rahu/Ketu rows (NON-BPHS extension)**:
- Rahu: friends — Mercury, Venus, Saturn; neutral — Jupiter; enemies — Sun, Moon, Mars.
- Ketu: friends — Mars, Venus, Saturn; neutrals — Mercury, Jupiter; enemies — Sun, Moon.

**Tradition register**: BPHS proper only covers the 7 lights. The nodal extensions follow Mantreshwara's *Phaladeepika* and the most-cited modern derivative tables. Alternative: some KP-flavoured traditions swap Mars between Rahu's and Ketu's friendship — we DO NOT use that.

### 1.5 Temporal (situational) friendship

**Sloka**: BPHS 3.56
**Rule**: from planet A's position, planet B in the 2nd, 3rd, 4th, 10th, 11th, or 12th sign → temporal friend. In 1st (same sign), 5th, 6th, 7th, 8th, or 9th → temporal enemy.
**Code**: `temporal_relation` in `dignity.py`. Matches BPHS.

### 1.6 Compound (Pancha-vidha) relation

**Sloka**: BPHS 3.58
**Rule**: combine naisargika + temporal:
- friend + friend → adhi_mitra (great friend)
- friend + enemy → sama (neutral)
- neutral + friend → mitra (friend)
- neutral + enemy → shatru (enemy)
- enemy + friend → sama
- enemy + enemy → adhi_shatru (great enemy)

**Code**: `compound_relation` in `dignity.py`. Matches BPHS.

### 1.7 Moolatrikona — **NOT YET IMPLEMENTED**

**Sloka**: BPHS 3.20 (with degree ranges in 3.34)
**Rule**: each planet has a Moolatrikona range within its own sign (sun 0-20° Leo; Moon 4-30° Taurus; Mars 0-12° Aries; Mercury 16-20° Virgo, followed by exaltation 20-30°; Jupiter 0-10° Sagittarius; Venus 0-15° Libra; Saturn 0-20° Aquarius).
**Status**: scheduled for Phase 1 audit-fix. `is_moolatrikona(planet, longitude)` to be added to `dignity.py`.
**Why it matters**: Saptavargaja Bala assigns 45 virupa to Moolatrikona and 20 to plain exaltation. Without Moolatrikona we over-credit exaltation and under-credit MT.

### 1.8 Sign rulers (sign → ruling planet)

**Sloka**: BPHS 3.20 (consequence of own-sign rule).
**Code**: `SIGN_RULERS`. Matches BPHS.

---

## 2. Planet state (`app/core/planet_state.py`)

### 2.1 Combustion (asta)

**Sloka**: BPHS 50 (Graha Drishti / Asta Adhyaya); BPHS 27 in some recensions.
**Code orbs**: Moon 12°, Mars 17°, Mercury 14°, Jupiter 11°, Venus 10°, Saturn 15°.
**Tradition register**:
- Santhanam BPHS gives Mercury **13°** direct (12° retrograde). We use 14°, matching Jagannatha Hora and Parashara's Light.
- Venus retrograde tradition gives 8° (we use the direct value 10° regardless — Phase 1 will add retrograde-aware orbs).

### 2.2 Vargottama

**Sloka**: not from a single BPHS sloka — convention is that a planet in the same rashi in D1 and D9 is "vargottama" (lit. "best in the varga"), treated as own-sign-equivalent for divisional strength.
**Code**: `is_vargottama(d1_sign, d9_sign) -> bool` — pure equality check.
**Tradition register**: universally agreed.

### 2.3 Retrograde (vakri)

**Definition**: ecliptic longitude speed < 0 (Lahiri sidereal).
**Code**: `is_retrograde(planet_entry)` — passthrough from ephemeris layer.
**Note**: BPHS gives retrograde planets bonus Cheshta-bala (60 virupa) regardless of direction; that's a Phase 2 implementation when Cheshta-bala lands.

---

## 3. Shadbala (`app/core/shadbala.py`) — **Phase 0 (incomplete) + audit-pending fixes**

Total Shadbala in BPHS 27 = sum of six components in *virupa* units (60 virupa = 1 rupa):
1. Sthana-bala — positional strength (Phase 0 implemented; bugs documented below)
2. Dig-bala — directional strength (Phase 2)
3. Kala-bala — temporal strength (Phase 2)
4. Cheshta-bala — motional strength (Phase 2)
5. Naisargika-bala — natural / innate strength (Phase 2; trivial constants per planet)
6. Drik-bala — aspectual strength (Phase 2)

### 3.1 Uchcha bala (exaltation arc)

**Sloka**: BPHS 27.10
**Rule**: 60 virupa at deep exaltation, 0 at deep debilitation, linear in shortest arc from the debilitation point. Formula: `bala = D / 3` where `D ∈ [0, 180]` is the shortest arc to debilitation.
**Deep exaltation degrees**: Sun Aries 10°, Moon Taurus 3°, Mars Capricorn 28°, Mercury Virgo 15°, Jupiter Cancer 5°, Venus Pisces 27°, Saturn Libra 20°.
**Code**: `uchcha_bala()`. Matches BPHS.

### 3.2 Saptavargaja bala — **AUDIT-FLAGGED, FIX IN PHASE 1**

**Sloka**: BPHS 27.18-27.22
**Correct BPHS values per varga**:
- Moolatrikona ⇒ **45 virupa** (highest)
- Own sign ⇒ 30
- Exaltation ⇒ **20** (NOT 45 — common mistake)
- Adhi-mitra (great friend by compound relation) ⇒ 15
- Mitra (friend) ⇒ 7.5
- Sama (neutral) ⇒ 3.75
- Shatru (enemy) ⇒ 1.875
- Adhi-shatru (great enemy) ⇒ 0

**Code (currently WRONG, audit finding 3)**: `_SAPTAVARGAJA_D1_VIRUPA` has `exalted=45, own=30, friend=15, neutral=7.5, enemy=3.75, debilitated=1.875`. Three errors:
1. Exalted should be 20, not 45.
2. Moolatrikona (45) is not represented.
3. Uses naisargika 3-tier (friend/neutral/enemy) instead of compound 5-tier (adhi_mitra/mitra/sama/shatru/adhi_shatru). Loses half the dignity resolution.

**Phase 1 fix**: replace `_SAPTAVARGAJA_D1_VIRUPA` table with the corrected eight-tier classical version above; add `is_moolatrikona()` helper; route through `dignity_state_compound()` instead of `naisargika_relation()`.

Also: BPHS Saptavargaja sums over 7 vargas (D1, D2, D3, D7, D9, D12, D30). Phase 0 simplifies to D1 only. Phase 2 will add the other 6 vargas.

### 3.3 Oja-Yugma bala — **AUDIT-FLAGGED, FIX IN PHASE 1**

**Sloka**: BPHS 27.28-27.30
**Rule**: each chart (D1 + D9) contributes 15 virupa when the planet sits in a sign of its preferred parity:
- Male planets (Sun, Mars, Jupiter, **Mercury, Saturn**) → +15 per odd-sign placement.
- Female planets (Moon, Venus) → +15 per even-sign placement.

**Code (currently WRONG, audit finding 4)**: `_NEUTER_PLANETS = {Mercury, Saturn}` gets 0. BPHS proper treats Mercury and Saturn as **masculine** for parity (some derivative texts disagree; the Santhanam translation is unambiguous).

**Phase 1 fix**: merge Mercury and Saturn into `_MALE_PLANETS`, remove `_NEUTER_PLANETS` for Oja-Yugma purposes.

### 3.4 Kendradi bala (Yugmayugma bala)

**Sloka**: BPHS 27.27
**Rule**: 60 virupa in kendra (1, 4, 7, 10); 30 in panaphara (2, 5, 8, 11); 15 in apoklima (3, 6, 9, 12).
**Code**: `kendradi_bala()`. Matches BPHS.

### 3.5 Drekkana bala

**Sloka**: BPHS 27.31-27.32
**Rule**: 15 virupa when the planet's gender aligns with its drekkana (0–10° / 10–20° / 20–30°):
- Male planets (Sun, Mars, Jupiter) → 1st drekkana (0–10°)
- Neuter planets (Mercury, Saturn) → 2nd drekkana (10–20°)
- Female planets (Moon, Venus) → 3rd drekkana (20–30°)

**Code**: `drekkana_bala()`. Matches the modern reading.
**Tradition register**: BPHS doesn't specify the boundary convention (whether 10.000° belongs to 1st or 2nd drekkana). We use `[0, 10) [10, 20) [20, 30)` — matches Jagannatha Hora. Parashara's Light uses the opposite boundary convention.

### 3.6 Phase-0 strength ceiling — **AUDIT-FLAGGED, FIX IN PHASE 1**

The Sthana-bala normalisation ceiling is hardcoded as 210 virupa (60 + 45 + 30 + 60 + 15). But neuter planets (Mercury, Saturn) can never earn the 30-virupa Oja-Yugma component → their true max is 180. We currently under-credit Mercury/Saturn Sthana-bala by 14%.

**Phase 1 fix**: replace constant with `_max_sthana_bala_for_planet(planet)` returning 180 for Mercury/Saturn, 210 for others.

---

## 4. Yogas (`app/core/yogas.py`) — **Phase 0 partial (7 yogas + Vipareeta Harsha); Phase 3B expands to 16**

### 4.1 Pancha Mahapurusha Yogas (Ruchaka, Bhadra, Hamsa, Malavya, Sasa)

**Sloka**: BPHS 36.1-36.6 (Yogadhyaya)
**Rule**: each star-planet, when in own or exalted sign AND in a kendra from Lagna, forms its yoga (Mars → Ruchaka, Mercury → Bhadra, Jupiter → Hamsa, Venus → Malavya, Saturn → Sasa).
**Code**: matches BPHS. Currently returns `Yoga` TypedDict (binary present/absent).
**Phase 3B**: upgrade to `YogaInstance` with strength.

### 4.2 Gajakesari

**Sloka**: BPHS 36.10
**Rule**: Jupiter and Moon in mutual kendra (1st, 4th, 7th, or 10th from each other).
**Code**: matches.
**Tradition register**: some texts add benefic-aspect requirement; we use the unconditional form.

### 4.3 Budha-Aditya

**Sloka**: BPHS 36.7
**Rule**: Sun and Mercury in the same sign.
**Code**: matches.
**Tradition register**: some texts exclude combust Mercury cases. Audit findings note our code does NOT check combustion; Phase 3B upgrade should add the option.

### 4.4 Vipareeta Harsha Raja Yoga — **AUDIT-FLAGGED, FIX IN PHASE 1**

**Sloka**: BPHS 36 (Yogadhyaya, Harsha/Sarala/Vimala block); reinforced by Mantreshwara Phaladeepika Ch. 7 and B.V. Raman's "Three Hundred Important Combinations" §62.
**Classical rule**: the 6th-house lord placed in another dusthana (6, 8, or 12) — **alone**, not joined by or aspected by a lord of a kendra/trikona — yields Harsha. Optimally the 6L is in **neecha** or **shatru-kshetra** (weak placement amplifies the yoga).

**Code (currently incomplete, audit findings 1 + 2)**:
1. Detector lacks the "alone in dusthana" gate (no check for benefic kendra/trikona-lord conjunction). Fires on false positives.
2. Strength scoring is monotonically WRONG-SIGNED: rewards strong 6L; classically a strong 6L damages the yoga (the lord delivers 6th-house results — debt, enemies — instead of canceling them).

**Phase 1 fixes**:
1. Add "alone in dusthana" gate: 6L must NOT be conjunct any lord of {1, 2, 4, 5, 7, 9, 10}. Returns `None` if contaminated.
2. Invert strength: `strength = 1.0 − (sthana_total / max_ceiling[planet])` when the yoga is present.

**Empirical confirmation of inversion** (from Round-9 wedge audit, feature-eng review):
- Among yoga-havers in screening_career cohort: LOW-strength → 39.0% career-event rate, HIGH-strength → 29.8%. A −9.2pp swing in the empirically-correct direction.

---

## 5. Tradition-choice register (deviations from strict Santhanam BPHS, justified)

When our code differs from the strict Santhanam translation, the reason is documented here. Tier-2 numeric pinning tests will fail on these — that's expected, not a bug.

| Item | Strict Santhanam BPHS | Our convention | Why |
|---|---|---|---|
| Mercury combustion orb | 13° (12° retrograde) | 14° | Matches Jagannatha Hora + Parashara's Light + most modern software |
| Drekkana boundary | Unspecified | `[0,10) [10,20) [20,30)` | Matches Jagannatha Hora |
| Rahu/Ketu friendships | Not in BPHS | Mantreshwara-style table | BPHS proper has no nodal friendship; modern extension |
| Saturn friend-sign exception | Some texts give Capricorn/Aquarius "friendly to whoever rules nearby" | We use strict naisargika only | Simplification; Phase 1 compound-relation may revisit |
| Mercury Oja-Yugma | (Some commentators say variable; main BPHS gives "masculine") | Currently 0 (will be 15 in Phase 1) | Audit-flagged; fix in Phase 1 |
| Moolatrikona ranges | BPHS 3.34 | Not yet implemented | Phase 1 task |

---

## 6. Sources referenced

1. **Santhanam, R.** (1984). *Brihat Parashara Hora Shastra* (English translation, 2 vols). Ranjan Publications, New Delhi. — Primary anchor.
2. **Sharma, G.C.** (1995). *Brihat Parasara Hora Sastra of Maharsi Parasara* (English with Sanskrit). Sagar Publications. — Cross-check.
3. **Sastri, V.S. / Iyer, B.V. Raman** (1992). *Three Hundred Important Combinations*. — Yoga catalog reference.
4. **Mantreshwara** (~16th century). *Phaladeepika* (English: G.S. Kapoor, 1976). Ranjan Publications. — Yoga catalog supplement.
5. **Jagannatha Hora** software (Sanjay Rath, freeware). — Numeric Tier-2 reference for shadbala / dignity pinning.
6. **Parashara's Light** software (Geovision Software). — Cross-reference for shadbala / yoga outputs.
7. **Astro-Databank** (astro.com). — Birth data with Rodden ratings for the 5 reference charts.

---

## 7. Adding new rules — checklist

Before merging any new yoga / strength / dignity rule:

- [ ] Sloka citation added to a section of this document.
- [ ] Chosen convention named explicitly (especially if Santhanam vs Sharma disagree).
- [ ] Alternative conventions listed in the section.
- [ ] Code carries a docstring referencing this document section.
- [ ] BPHS-compliance test (`tests/bphs_compliance.py`) attached to at least one test of the rule.
- [ ] If the rule has a numeric component (e.g., a virupa value), ≥1 reference-chart test pins it to within ±5% of Jagannatha Hora.
- [ ] If the new rule contradicts what was previously documented here, the previous entry is preserved with strikethrough and the reason for the change is noted.
