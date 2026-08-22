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
r.dashas                        # Yogini (general) + Ashtottari (if applicable)
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
- **Baladi avastha** (ch.45) and **graha drishti** (ch.26).
- **Shadbala** (ch.27) — the **complete six-fold** planetary strength in Parashara's virupas:
  Sthana (5 sub-components), Dig, Naisargika, Cheshta (from speed), Drik (aspectual, may be
  negative), and Kala (8 sub-components: Nathonnata, Paksha, Tribhaga, the four calendar-lords
  Varsha/Masa/Vara/Hora, and Ayana). The Kala calendar-lords are resolved from the birth's sunrise
  and the Ahargana, pinned to Parashara's own worked example (1 Jun 1984 → Jupiter year, Venus month).
- **Nisargayu** (ch.43 sl.16-17 + ch.3 sl.49-50) — natural longevity, the 120-year allotment scaled
  by deep-exaltation (the third method, which the Raman engine lacks). Pre-reduction core.
- **Bhava prosperity/annihilation** (ch.11 sl.14-16) — the verdict spine, with antidote clauses.
- **A chart caster + unified reading** — cast a birth and get one cited reading combining all of
  the above.
- **Conditional dashas** (ch.46) — NINE nakshatra-seeded systems over one shared framework:
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
