# `app/parashara/` — a faithful BPHS engine (engine #2)

The second stream of a multi-stream astrology platform. `app/raman_saab/` encodes Sri B. V.
Raman's system and is finished and frozen; this engine encodes **Parashara's own system** from
BPHS and its allied classical texts. More streams (KP, Jaimini, Nadi, Tajika…) are intended to
follow the same pattern.

## The one idea: root authority per stream

Every stream answers a different question and so has a different **root authority**:

| Engine | Question | Root (wins ties) | BPHS is… |
|---|---|---|---|
| `raman_saab` | "what would Raman say?" | B. V. Raman | corroboration-only (not natal-citable) |
| `parashara` | "what does Parashara say?" | **BPHS** | **root** |

Where BPHS and Raman disagree, this engine follows **BPHS**; Raman is at most corroboration here.
That inversion is why it is a separate engine and not a mode of the existing one — the two cannot
share a verdict layer without breaking `raman_saab`'s Raman-only guarantee.

## Isolation (the platform contract)

`tests/parashara/test_engine_isolation.py` enforces, both directions:
- `raman_saab` imports **nothing** from `parashara` — the finished 259/293 ratchet is untouchable.
- `parashara` imports **no** `raman_saab` doctrine or judging — only a named substrate allowlist
  (varga sign-arithmetic) may cross. Maths is shared; judgment never is.

Shared deliberately: the **fidelity apparatus** — `Citation(work, line)` into real corpus lines,
`verify`/`passage`, and (per stream) its own registry. Re-derived per stream would be waste; the
authority assigned to a text is what differs, not the machinery.

## The engine's number — the BPHS fidelity ratchet

**`[bphs-fidelity] reproduced=15/15 of Parashara's own worked results`** (`test_fidelity_ledger.py`,
built from `tools/parashara/fidelity_ledger.py`).

This is the BPHS analog of the Raman engine's `259/293`, and it is honestly **different in kind**.
The Raman figure is *verdict accuracy* against Raman's published **chart-verdict gallery** — he
printed hundreds of nativities with his judgment of each. BPHS gives no such gallery; it is a
systematic treatise, so the faithful analog scores the engine's reproduction of the concrete worked
**results Parashara actually printed**: the Ahargana year/month lords (1 Jun 1984 → Jupiter/Venus),
the Vimshottari seed (Revati → Mercury), the Uchcha value (152°15′ → 50.75), the Sun's Trikona
reduction (BPHS-67), every Bhinnashtakavarga total + SAV 337, the full 144-cell ch.24 catalogue, and
the argala of his hypothetical chart. Each row is a number or lookup he stated; the engine reproduces
all 15. It is **textbook fidelity to Parashara's arithmetic — NOT validated prediction of real
lives** (the same caveat the Raman engine's Measured-Truth verdict carries). The ledger is a floor,
ratcheted so a regression cannot pass silently, and every row's citation must resolve.

### The verdict-scale number — cross-engine agreement

For a figure on the *same 293-verdict scale* as Raman's, `tools/parashara/cross_engine_agreement.py`
runs the parashara ch.11 bhava judge on the **same** Raman goldens and scores it against Raman's own
published verdicts (ordinal afflicted<mixed<favourable; parashara flourishing/ordinary/annihilated
maps onto it):

```
Raman engine            vs golden : exact=259/293  within-1=283/293   (the engine tuned to Raman)
Parashara ch.11 only    vs golden : exact=123/293  within-1=198/293   (bare prosperity/annihilation)
Parashara ch.11+str+yoga vs golden: exact=118/293  within-1=197/293   (the richer verdict)
```

**Read this as overlap, not accuracy.** It is NOT "BPHS is 123/293 accurate." Raman deliberately
revised and *elaborated* Parashara across many chapters plus his own refinements; the parashara
number is BPHS's own method, so where they differ the divergence is a real BPHS-vs-Raman doctrinal
difference (each attributed off-axis / boundary / inversion), not a bug. The gap between 259 and 123
IS the measure of how much Raman's system is more than ch.11 alone.

**The richer verdict is the integrity check.** `richer_bhava.py` extends ch.11 with Parashara's own
strength and yoga votes (lord Vimsopaka band ch.7, karaka dignity ch.32, SAV bindus ch.66, a
Mahapurusha yoga on the lord/karaka) — same net-vote rule, every vote cited. It was **not tuned
toward Raman**, and the proof is in the number: it agrees with Raman *slightly LESS* (118 vs 123), not
more. Folding in more faithful BPHS doctrine moves the engine *away* from Raman, not toward him —
confirming these are genuinely different systems, not one an approximation of the other.
`test_cross_engine_agreement.py` re-derives Raman's 259/293 to prove the harness is valid and asserts
the richer verdict never jumps toward Raman.

## Layout

```
doctrine/     book_registry (BPHS=root, allied lineage citable, Raman corroboration), sources
primitives/   vimsopaka, relationships, functional_nature, baladi_avastha, graha_drishti, longevity
              (Nisargayu), shadbala/ (the complete six-fold strength), nakshatra_dasha,
              yogini_dasha, ashtottari_dasha, conditional_dasha_systems, rasi_dasha, sthira_dasha
chart/        cast (birth -> chart via shared ephemeris + Kala-bala time context),
              ephemeris (speeds/ayanamsa/sunrise/calendar), vimsopaka_chart, bhava_chart, brahma_graha
judges/       bhava_prosperity  (the verdict layer — BPHS ch.11, NOT Raman's _decide)
reading.py    the capstone: cast a birth -> one cited reading (bhavas + vimsopaka + shadbala +
              avasthas + dashas + sthira + ayu)
```

End to end:

```python
from app.parashara.chart.cast import cast
from app.parashara.reading import read
r = read(cast(year=1990, month=7, day=15, hour=12, minute=0,
              tz_offset=5.5, latitude=12.97, longitude=77.59))
r.bhavas[10].verdict            # Parashara's ch.11 judgment of the 10th
r.vimsopaka["Jupiter"].score    # 20-point cross-varga strength
r.shadbala["Saturn"].rupas      # complete six-fold strength (Sthana..Kala)
r.dashas                        # Vimshottari (primary) + Yogini + Ashtottari (if applicable)
r.sthira.timeline               # Sthira rasi dasha, seeded by the Brahma Graha
r.nisargayu.natural_years       # natural longevity (pre-reduction)
```

## Phase status

| Phase | What | State |
|---|---|---|
| 0 | Corpus rescue — BPHS 37 → 91/97 chapters; Vol II added; OCR-tolerant splitter | ✅ `5f30ba5` |
| 1 | Scaffold — root-authority registry, sources, isolation guards; Vimsopaka + relationships | ✅ `84a5cac` |
| 2 | Verdict layer — bhava prosperity (ch.11); benefic/avastha/drishti; cross-engine agreement | ✅ `006bd7e` |
| 3 | Conditional dashas — Ashtottari + Yogini + the shared nakshatra-dasha framework | ✅ `5a64a97` |

## Doctrine encoded so far (all cited to BPHS's own slokas)

- **Vimsopaka bala** (ch.7) — all four schemes, the 6-tier Varga Viswa, Parashara's bands.
- **Relationships** (ch.3 sl.55-58) — natural/temporary/compound, derived from the formula and
  checked against Parashara's own worked examples.
- **Functional nature** (ch.3 sl.11) — with Mercury and Moon kept conditional (the documented
  point of divergence from Raman's engine).
- **Avasthas** (ch.45) — the full triad: **Baladi** (age-state by degree), **Jagradadi** (awake/
  dreaming/sleeping by dignity), and **Deeptadi** (dignity/placement state — Deepta/Swastha/Pramudita/
  Santa/Deena/Khala, plus Vikala if sharing its sign with a malefic and Kopa if combust). **Graha
  drishti** (ch.26).
- **Shadbala** (ch.27) — the **complete six-fold** planetary strength in Parashara's virupas:
  Sthana (5 sub-components), Dig, Naisargika, Cheshta (from speed), Drik (aspectual, may be
  negative), and Kala (8 sub-components: Nathonnata, Paksha, Tribhaga, the four calendar-lords
  Varsha/Masa/Vara/Hora, and Ayana). The Kala calendar-lords are resolved from the birth's sunrise
  and the Ahargana, pinned to Parashara's own worked example (1 Jun 1984 → Jupiter year, Venus month).
- **Nisargayu** (ch.43 sl.16-17 + ch.3 sl.49-50) — natural longevity, the 120-year allotment scaled
  by deep-exaltation (the third method, which the Raman engine lacks). Pre-reduction core.
- **Bhava prosperity/annihilation** (ch.11 sl.14-16) — the verdict spine, with antidote clauses.
- **Richer bhava verdict** (`richer_bhava.py`) — ch.11's net-vote method EXTENDED with Parashara's own
  strength and yoga signals: the lord's Vimsopaka band (ch.7), the karaka's dignity (ch.32), the
  house's Sarvashtakavarga bindus (ch.66), a Pancha Mahapurusha yoga on the lord/karaka, and — on a
  cast chart — the lord's full six-fold **Shadbala vs its required strength** (ch.27:3747, Parashara's
  own minimums: Sun 6.5 … Mercury 7.0 rupas). Same verdict rule, every added vote cited; surfaced
  per-nativity alongside the bare ch.11 verdict.
- **Bhava-lord effects** (ch.24) — the full 144-statement catalogue (lord of each house in each
  house), indexed from the corpus in place so every effect cites Parashara's own sloka; surfaced
  per-nativity in the reading against the chart's actual house-lord placements.
- **House effects** (ch.12-23) — a per-house cited index of Parashara's effect-slokas, with topic
  headings where the OCR is clean. Honestly PARTIAL (this scan of ch.12-23 is OCR-damaged;
  `bhava_effects.coverage()` reports the per-house sloka count) — a reference catalogue, not yet a
  fire-on-chart rules layer.
- **Ashtakavarga** (ch.66) — Bhinnashtakavarga per graha and Sarvashtakavarga, the bhava-strength /
  transit backbone. The canonical benefic-place tables, guarded by a HARD checksum (each BAV total
  fixed — Sun 48…Saturn 39 — and SAV always 337), so an OCR/transcription error cannot pass silently;
  asserted at import and in tests. Surfaced per-nativity (SAV per house + the full BAV grid). The
  **Trikona shodhana** (trine reduction) is also encoded and verified against Parashara's own worked
  example (BPHS-67: the Sun's 5,3,2 → 3,1,0). **Deferred** (not faked): Ekadhipatya shodhana (ch.68)
  and the Pinda Sadhana that needs it — this scan's ch.68 worked examples are internally inconsistent,
  so a faithful deterministic encoding isn't possible from this source.
- **Bhava karakas** (ch.32 sl.31-34) — the natural significator of each house (1→Sun, 2/5/9/11→
  Jupiter, 3/6→Mars, 4→Moon, 7→Venus, 8/12→Saturn, 10→Mercury), Parashara's stated order. Queryable
  `karaka_of`.
- **Vargottama** (Saravali ch.3 sl.13) — a body in the same sign in Rasi (D1) and Navamsa (D9), a
  recognized strength; the positional definition (1st navamsa of movable, 5th of fixed, 9th of dual)
  is verified equivalent to D9==D1. Grahas + the Lagna; surfaced per-nativity.
- **Gochara** — transit by Ashtakavarga (ch.70): a graha transiting a sign is judged by its own
  Bhinnashtakavarga benefic-count there (>=5 favourable, <=3 unfavourable, around the 0-8 midpoint) —
  Parashara's OWN transit method, reusing the checksum-guarded ashtakavarga. `transit_quality` /
  `all_transits` + a `chart.ephemeris.transit_signs(date)` helper; a queryable capability applied
  on-demand with a transit date. The Pinda-scaled ch.70 predictions stay deferred (they need the
  OCR-inconsistent Sodhya Pinda).
- **Argala** — planetary intervention (ch.31): for any target sign, the argalas acting on it (from
  the 2nd/4th/11th/5th), their obstructors (12th/10th/3rd/9th), whether each prevails by count, and
  the Vipareeta argala of 3+ malefics in the 3rd. Pinned to Parashara's own hypothetical chart. A
  queryable analytical module (`argala_for`), applied on-demand rather than dumped per-reading.
- **General corpus index** (`corpus_index.slokas_of`) — a faithful numbered-sloka index for ANY
  chapter (BPHS or allied), each cited to its own line. The shared backbone the structured modules
  build meaning on; `find_slokas` is a cited grep over a chapter. Coverage: **BPHS** 88/97 chapters
  (~1035 slokas, root) + the **allied lineage** — **Saravali** 55 chapters/~1020 slokas and **Brihat
  Jataka** ~19/268 (allied tier, citable where BPHS is silent). Phaladeepika, Uttara Kalamrita, Hora
  Sara and Jataka Parijata are sparsely imported / OCR-damaged in this snapshot — a recorded
  source-quality gap, not hidden (see `BPHS_CORPUS_COVERAGE.md`).
- **Nabhasa yogas** (ch.35) — the cited catalogue of all 32 distribution yogas, plus detectors for
  the two computationally-unambiguous families: Asraya (Rajju/Musala/Nala, by shared modality) and
  Sankhya (Gola…Veena, by count of signs occupied). Surfaced per-nativity in the reading; the Dala
  and 20 Akriti figures are catalogued, their pattern-detection a documented next step.
- **Lunar (Chandra) yogas** (ch.37) — detectors for the yogas reckoned from the Moon: Sunapha /
  Anapha / Durudhara (a graha in her 2nd / 12th / both), Kemadruma (the Moon bare, with the
  kendra-from-lagna cancellation), Adhi (benefics in her 6th/7th/8th) and the Moon-Dhana yoga. Each
  cites its ch.37 sloka; surfaced per-nativity in the reading.
- **Yoga catalogue** (ch.35-42) — a cited index of every yoga chapter. The Raja yogas (ch.39,
  Karakamsa-based), royal-association (ch.40), Dhana/wealth (ch.41) and penury (ch.42) yogas are
  bespoke specific combinations with no single citable general rule, so they are preserved faithfully
  as a queryable catalogue (`catalogue`, `find`) rather than synthesized into misattributed detectors.
- **Solar (Ravi) yogas** (ch.38) — Vesi / Vasi / Ubhayachari: a tara-graha (barring the Moon) in the
  2nd / 12th / both from the Sun. The Sun-analogue of the lunar yogas; cited, surfaced per-nativity.
- **Pancha Mahapurusha yogas** (Saravali ch.37 — allied) — Ruchaka/Bhadra/Hamsa/Malavya/Sasa, each
  formed by its non-luminary in own or exaltation sign in a kendra. Cited to the allied text (BPHS is
  silent — exactly the allied tier's job); surfaced per-nativity. Detector + effect citations.
- **Combustion / Astangata** (ch.7) — a planet within its Sun-orb loses its rays; the BPHS
  combustion table (Moon 12°, Mars 17/8, Mercury 14/12, Jupiter 11, Venus 10/8, Saturn 16°, direct/
  retrograde), Sun and nodes never combust. A reusable primitive (`is_combust`, `combust_planets`).
- **Gaja-Kesari** (ch.36) — encoded in Parashara's STRICT form (not the loose "Jupiter in a kendra
  from the Moon" his own Notes criticise): Jupiter in a kendra from lagna OR Moon, conjunct/aspected
  by a benefic, and free of debilitation, combustion and an enemy's sign. Uses the combustion
  primitive + ch.3 relationships; surfaced per-nativity.
- **A chart caster + unified reading** — cast a birth and get one cited reading combining all of
  the above.
- **Vimshottari dasha** (ch.46 sl.12-15) — the PRIMARY 120-year system, encoded from Parashara's own
  Krittika-reckoned formulation (which reproduces the standard Aswini→Ketu scheme); the canonical
  baseline's Revati Moon correctly seeds the Mercury mahadasha. Reported first in every reading, now
  **with its antardashas (bhuktis)** — each mahadasha subdivided into proportional sub-periods
  (BPHS-46:110; bhukti = antardasha_years × mahadasha_years ÷ total), summing exactly to the
  mahadasha's length. **Pratyantardashas** (sub-sub-periods) go one level deeper by the same
  proportional rule (`pratyantar_timeline`; a queryable capability — 9×9×9 would swamp the reading).
- **Conditional dashas** (ch.46) — NINE further nakshatra-seeded systems over one shared framework:
  Ashtottari (108), Yogini (36), Shodasottari (116), Dwadasottari (112), Panchottari (105),
  Shatabdika (100), Chaturashiti-sama (84), Dwisaptati-sama (72), Shattrimsat-sama (36). Each cited,
  with its applicability condition; the inclusive counting convention is pinned by Parashara's own
  worked examples. **Not encoded:** Shastihayani (its ch.46 OCR is internally inconsistent — 69≠60);
  Kalachakra/Chara (rasi-based, a different framework).
- **Sthira rasi dasha** (ch.46) — the rasi-based Sthira sequence, seeded by the **Brahma Graha**
  (ch.46 sl.170-173), which is itself selected using the complete Shadbala for its strength tie-break.

## Next tranches (documented, not yet built)

- Rasi dashas: Kalachakra (ch.46 sl.100+), Chara — the remaining rasi-based framework.
- Shastihayani — once a clean source resolves the 69-vs-60 inconsistency.
- The Jagradadi/Sayanadi avasthas (Sayanadi needs the name-Anka); Nisargayu's four haranas.
- A full chart adapter + report surface; BPHS goldens from worked nativities where the text gives
  them.
- The 6 Vol II chapters (54, 65, 75, 81, 83, 94) whose title lines the scan lost — recover via a
  TOC-page-number anchor when a citation needs one (see `BPHS_CORPUS_COVERAGE.md`).
