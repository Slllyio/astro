# BV Raman knowledge-coverage map (2026-06-29)

A coverage audit of everything BV Raman wrote (16 works in the corpus) vs what the engine encodes,
to find the gaps in HIS OWN system before extending any parallel school (Jaimini). 5-agent survey
against the 845 encoded rules + 21 primitives.

## Domain coverage (breadth)

| Domain | Raman source | Engine | Notes |
|---|---|---|---|
| Natal house judgment | HTJAH I/II | **ENCODED** | 845 rules / 47 significations; depth gaps below |
| Strength (Shadbala) | Graha & Bhava Balas | **ENCODED** | full 6-bala + ishta/kashta + bhava-bala |
| Dignity / friendship / combustion | HPA, Manual | **ENCODED** | primitives complete |
| Aspects (graha drishti) | HPA | **ENCODED** | whole-sign 5/7/9, 3/10, 4/8; nodes 7th (Raman) |
| Dashas (Vimshottari) | HPA Ch.13 | **ENCODED** | Raman's chosen dasha; full MD/Bhukti |
| Ashtakavarga | HPA | **ENCODED** | BAV/SAV, 337 checksum |
| Transits (Gochara) | HPA | **ENCODED** | Moon-frame + AV + Sade-Sati |
| Divisional charts | various | **ENCODED** | all 16 cast; D9 + D7-children feed verdicts, rest report-only |
| Longevity (math) | HTJAH II | **ENCODED** | Pindayu/Amsayu/maraka/balarishta primitives |
| **Yogas** | **300 Combinations** | **~13%** | **biggest depth gap — see below** |
| **Avasthas** | **HPA Ch.7** | **PARTIAL** | Baladi+Jagradadi only; **Deeptadi (10) MISSING** |
| **Muhurta** | Muhurtha | **NOT ENCODED** | whole domain, firewalled, corpus folder empty |
| **Prasna (horary)** | Prasna Marga/Tantra | **NOT ENCODED** | whole domain, firewalled |
| **Varshaphal (Tajika)** | Varshaphal | **NOT ENCODED** | whole domain, firewalled |
| Jaimini | Jaimini Sutras/Studies | PARTIAL | parallel school (AK, karakamsa, chara, arudha) |

## Gaps in Raman's OWN (Parashari) knowledge — prioritized

These are missing pieces of Raman's *core* system (NOT parallel schools), ranked by value/effort:

1. **Panchamahapurusha yogas (Ruchaka/Bhadra/Hamsa/Malavya/Sasa) — 5 of 5 MISSING.** The most
   universally-cited classical yogas, absent from a "Raman" engine. Trivially encodable: own/exalted
   sign in a kendra; the dignity primitive already exists. **Highest value-per-effort.**
2. **Deeptadi avasthas (10 states) — MISSING.** HPA Ch.7 names them (Deepta/Swastha/Mudita/.../Bhita);
   every input (dignity, combustion, retro, friendship) is already computed and there is an avastha
   hook in the judge. Low cost, deepens result-intensity exactly as Raman uses it.
3. **Navamsa-dispositor-of-lord routing — MISSING (cross-house).** Raman opens every chapter with
   "read the matter from the navamsa-dispositor of the house-lord"; it is stubbed in H10/H5/H4/H8.
   One primitive unblocks descriptive->evaluable conversions in 4+ houses at once.
4. **H10 career-by-sign + trade-by-navamsa catalogues (HTJAH-II:10249-10800).** The single largest
   unencoded doctrine block (~460 lines) — exactly why H10 is the thinnest house (41 rules). Same
   shape as the existing decanate_cause lookup grid.
5. **Solar yogas (Vesi/Vasi/Ubhayachari).** Sun-flank analogues of the encoded Moon-flank trio; the
   predicate just needs a Sun-flank twin.
6. **Alpayu/Madhyayu/Purnayu longevity COMBINATIONS (~51) + the rest of Balarishta (~22 of 29).**
   The engine computes a longevity *number* but not Raman's *qualitative* longevity-judgment combos.
7. **Nabhasa yogas (~32).** The whole Akriti/Sankhya scheme; one new occupied-house-shape primitive.
8. **Strength-gated qualifiers (pervasive descriptive stubs).** A shared weak/debil/affliction-grade
   gate would convert dozens of inert `descriptive` rules to `evaluable` across all 12 houses.
9. **Panchanga (tithi/karana/yoga-of-day) into the reading** — computed in core/, never wired in.
10. **Rasi drishti (Jaimini sign aspects), special nakshatras** — minor fundamentals.

## The three firewalled domains (separate systems, not gaps in the natal core)
Muhurta, Prasna, and Varshaphal are deliberately quarantined behind `book_registry.py` (NON-citable),
treated as different systems. Each is a greenfield sub-package (needs panchanga/tarabala for muhurta;
solar-return/muntha/varshesha/Tajika-aspects for varshaphal; question-moment/nimitta/prasna-rules for
prasna), reusing the ephemeris/chart/sphuta/upagraha scaffolding but not the natal doctrine.

## Verdict
**Raman's natal Parashari CORE is well-encoded** (judgment + strength + dashas + ashtakavarga +
transits + divisional + longevity-math). The real remaining gaps in HIS OWN system are the **yogas
(~13% of the 300)** — above all the **Panchamahapurusha** — the **Deeptadi avasthas**, the
**navamsa-dispositor routing**, and the **H10 sign-catalogue**. These should be closed before
extending the parallel Jaimini school. The three whole domains (Muhurta/Prasna/Varshaphal) are
separate, larger efforts that the engine deliberately firewalls.

## Gaps CLOSED (2026-06-29) — implemented one by one, each verdict-invariant (ratchet 208/241 held)

1. **Pancha Mahapurusha (5/5)** — Ruchaka/Bhadra/Hamsa/Malavya/Sasa in `doctrine/yogas.py` (own/exalt
   in a kendra; 3HC-cited; fire across 66 golden occurrences).
2. **Systematic yogas (+19)** — solar Vesi/Vasi/Ubhayachari + Nabhasa Asraya(3)/Dala(2)/Sankhya(7)/
   contiguous-Akriti(4) in `doctrine/yogas.py`. (16 shape-Akriti + the named Raja/Dhana tail remain
   a backlog.)
3. **Deeptadi avasthas (10)** — `primitives/deeptadi.py`, each graha's result-state (HPA Ch.7),
   surfaced in the synthesis. (Bhita/acceleration needs speed data.)
4+5. **Navamsa-dispositor routing + H10 career** — `primitives/career.py`: profession via the
   navamsa-dispositor of the 10th lord (HTJAH-II:10249-10274), surfaced in the synthesis. (The
   ~460-line career-by-SIGN prose catalogue remains a backlog.)
6. **Alpayu/Madhyayu/Purnayu longevity combos** — `primitives/longevity_combos.py`, the
   cleanly-evaluable combinations per class (HTJAH-II:3251-3474), surfaced in the synthesis. (The
   navamsa/aspect-chain death-age combos remain a backlog.)

All six are ADDITIVE/parallel readings (cited, tested) that never move the Parashari verdict, so the
208/241 faithful core is untouched while the engine now encodes substantially more of Raman's system.
Remaining (documented) Raman backlog: the shape-Akriti + named Raja/Dhana yoga tail, the career-by-sign
prose catalogue, the strength-gated descriptive stubs, panchanga-into-the-reading, rasi-drishti; and
the three firewalled domains (Muhurta/Prasna/Varshaphal).
