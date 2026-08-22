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
primitives/   vimsopaka, relationships, functional_nature, baladi_avastha, graha_drishti,
              nakshatra_dasha, yogini_dasha, ashtottari_dasha
chart/        vimsopaka_chart, bhava_chart  (thin adapters over the shared caster)
judges/       bhava_prosperity  (the verdict layer — BPHS ch.11, NOT Raman's _decide)
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
- **Bhava prosperity/annihilation** (ch.11 sl.14-16) — the verdict spine, with antidote clauses.
- **Conditional dashas** (ch.46) — NINE nakshatra-seeded systems over one shared framework:
  Ashtottari (108), Yogini (36), Shodasottari (116), Dwadasottari (112), Panchottari (105),
  Shatabdika (100), Chaturashiti-sama (84), Dwisaptati-sama (72), Shattrimsat-sama (36). Each cited,
  with its applicability condition; the inclusive counting convention is pinned by Parashara's own
  worked examples. **Not encoded:** Shastihayani (its ch.46 OCR is internally inconsistent — 69≠60);
  Kalachakra/Chara/Sthira (rasi-based, a different framework).

## Next tranches (documented, not yet built)

- Rasi dashas: Kalachakra (ch.46 sl.100+), Chara, Sthira — a separate rasi-based framework.
- Shastihayani — once a clean source resolves the 69-vs-60 inconsistency.
- Nisargayu (the third longevity method) and the Jagradadi/Sayanadi avasthas.
- A full chart adapter + report surface; BPHS goldens from worked nativities where the text gives
  them.
- The 6 Vol II chapters (54, 65, 75, 81, 83, 94) whose title lines the scan lost — recover via a
  TOC-page-number anchor when a citation needs one (see `BPHS_CORPUS_COVERAGE.md`).
