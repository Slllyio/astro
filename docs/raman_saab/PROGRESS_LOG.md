# Raman Saab — Progress Log (durable, append-only)

**Purpose:** chronological build ledger that survives session limits / context compaction. Append
a dated entry at **every commit or milestone**. Complements the other durable artifacts:
- **Execution plan:** `C:\Users\S.C.C\.claude\plans\compressed-mixing-trinket.md` (v3, the full
  staged plan with per-possibility contingencies).
- **Resume anchor:** `docs/raman_saab/BUILD_STATUS.md` (structured current-state + resume pointers).
- **Spec:** `docs/superpowers/specs/2026-06-01-raman-saab-engine-design.md`.
- **Golden validation:** `docs/raman_saab/golden_validation_worksheet.md` (user DRAFT→CONFIRMED).
- **The ratchet:** `tests/fixtures/golden_accuracy_baseline.json` (accuracy floor, human-bumped).

**Convention:** never lose a decision. Review findings (which otherwise live only in ephemeral
`tasks/*.output` temp files) get archived here. Commits are on branch `round8-unification`,
surgical staging, no Co-Authored-By.

---

## Where we are (top — keep current)

- **HEAD `a90414d`** · suite **1212 passed, 5 skipped, 3 xfailed** · **ratchet floor 7/12**.
- Phases **A + B + A-deps + wiring COMPLETE**. Next: **Stage 1** (H1 deep combination encoding,
  mismatch-targeted) — workflow `wf_4cbd3be9-afb` in flight (predicates + house split + 6 group
  encoders + adversarial verify).
- Open H1 mismatches to flip: charts 09, 10, 17, 20, 31 (each diagnosed in the plan, Stage 1e).

---

## Commit ledger

### Phase 0–2 (pre-accuracy-first; the working vertical slice)
| sha | what | state |
|---|---|---|
| (earlier) | Phase 0/1: chart adapter, all primitives, full 6-fold **Shadbala** reconciled to GBB to the decimal; `app/core` import-guarded out | — |
| `6d622ee`,`6673978` | lord-in-12 layer, all 12 houses (147 cited rules) | — |
| `485cd6a` | rule-firing bridge (Shadbala picks fortified/afflicted branch) | engine produces cited readings |
| `e0b3938`,`036906c`,`e26cd35` | planets-in-house layer, all 12 houses (108 rules) → **255 cited rules** | — |
| `f11e8ae` | Phase-3 house-level judge (ordinal verdict from rules + pillars) | — |
| `7e3519e`,`b71abf9` | proforma + render + CLI `--format reading` | **full vertical slice**: birth data → cited worksheet (706 tests) |

### Accuracy-first rebuild (the current architecture)
| sha | what | ratchet / tests |
|---|---|---|
| `924d7b6` | **A1** `significations.py` — 42 routings, mandatory frames (H4/H7/H9/H10); doctrine PASS | — |
| `60c7664` | **A2/A3** lazy `EvalContext` cache + `functional_nature()` accessor | 731 |
| `f81d051` | **A4-A6** per-signification judge: 3-frame immutable ledgers, §6.3 `_decide`, veto/salvage/identity/parivartana | 753 |
| `ff96590` | **A judge fixes** (adversarial review caught: citation misattribution, inert longevity guard, lord/strength frame mismatch — see Findings) | 764 |
| `780ac15` | **B framework** golden harness (Track A/B/Tier-3 + DRAFT-gate + condition-solver + tuner skeleton) | 770 |
| `2506ad2` | **B** first 19 DRAFT goldens (DOB/TOB/POB charts + 3 longevity) | 827 |
| `0eb5af8` | **B review fixes** (chart_33 IST tz; Aquarius Lagna per HTJAH-II:4253; Lincoln Western lon; Track-A lagna assertion; schema guard #11; tuner Final removed) | 855 |
| `c053eaf` | **user-CONFIRMED 12 H1 verdicts** + **Track-B accuracy ratchet armed** | **baseline 6/12** |
| `3dbd4dc` | yoga catalogue — 16 cited (3HC corpus found on disk) + **kemadruma bhanga corrected to 3HC:2182-2185** | 826 (doctrine) |
| `db84a35` | sphuta engines — Beeja/Kshetra (mirrored odd/odd vs even/even), Special-Dhana-Lagna, Sahams (arc-minute pins) | 1063 |
| `4d18430` | special-grid lookups — 93 cited rows (decanate/source-of-gains/Bhavartha/confinement/disease) | 1150 |
| `a90414d` | wire deps into judge — H5 fertility gate, yoga modulation (never-overturn-decisive), lookup metadata, chart_overview | 1212 · **ratchet 6/12→7/12** (Sakata corrects chart_33) |

---

## Locked corrections (caught by review against the corpus — do NOT regress)

1. **Harana order (longevity)** — Chakrapatha → Satrukshetra (Mars+retro exempt) → Astangata
   (Venus/Saturn **fully** exempt, not ½) → Krurodaya (**absolute**, Pindayu-only). The earlier
   draft (Krurodaya-first, ½ exemptions, "no double jeopardy") **contradicted `HTJAH-II:4006-4101`**
   and was corrected. Corpus is authority.
2. **Vipareeta** = Raman's narrow form (dusthana lords conjoined in a dusthana, `HTJAH-I:6302`);
   the Phaladeepika isolation clauses were stripped (NOVEL-tagged if ever re-added).
3. **§6.3 heuristics provenance** — the 5-step rule, Rupa thresholds, 1-Rupa canceller gate are
   **golden-tuned engine heuristics, NOT cited to Raman**. The salvage/rescue *principle* is real:
   bhava-rescue = `HTJAH-I:503-505` (the HOUSE's good aspects, not karaka strength — the original
   miscitation); strong-karaka demotion = three-pillar doctrine `HTJAH-II:221`/`HTJAH-I:985`.
4. **Kemadruma bhanga** must include **kendra-from-Moon** + **Moon-conjunction** cancellations
   (`3HC:2182-2185`) — the Phase-1b primitive had only kendra-from-Lagna; the benefic-drishti
   branch is labeled EXTENDED (not from 3HC).
5. **Beeja/Kshetra** strength is **mirrored**: Beeja odd-sign/odd-navamsa, **Kshetra even/even**
   (`HTJAH-I:5521/5523`).
6. **chart_33's affliction** is driven by **Y.SAKATA** (Moon 12th from Jupiter, `3HC:2984`), NOT
   Kemadruma (which doesn't form there) — pinned by `test_chart33_h1_drop_is_sakata_not_kemadruma`
   (right-for-the-right-reason guard).
7. **Maraka tie-break** = Chart-35 unit-counting (`HTJAH-II:4733-4791`), not a fixed ladder.
8. **Span bands** 8-32 / 33-75 / 75-120; Raman rejects 32-70/100.

---

## Adversarial review findings archive (substantive only; temp outputs are ephemeral)

- **Phase-A judge (`ff96590`):** karaka-salvage cited the wrong verse (`:503-505` is the house
  rescue, not karaka); longevity guard was inert (flag set, never read → maraka still drove H8
  afflicted); `as_house_verdict` reported Lagna lord's name with the lead (Moon) frame's strength.
  All fixed + pinned.
- **Phase-A deps (`3dbd4dc`):** kemadruma bhanga incomplete vs its cited 3HC line; `Y.RAJA.910X`
  dropped a printed disjunct. Fixed.
- **Wiring (`a90414d`):** arishta drop could act on a contradiction-mixed (hiding benefic
  testimony) — guarded; chart_33 right-for-wrong-stated-reason (Sakata not Kemadruma) — pinned;
  Beeja metadata over-claimed "strong" → renamed `numeric_strong`; LONGEVITY_GUARD arishta
  suppression is dead-code-but-defensive (documented).
- **Plan v3 deep review (17 findings):** F1 tuner-holdout excludes all book charts → empty fit
  set (real defect; fix = id-list + crc32 slice + holdout SCORING code); F2 fine-tag ordering
  would inert Groups 4/5 before re-tag (fix = encode coarse `self`, re-tag AFTER measure); F3
  chart_33 crutch-removal most-likely-failure is contradiction-mixed not non-firing; F4 missing
  `LordsConjunct`/`LORD_OF` predicate shapes; F5 no Tier-3 snapshot-churn protocol; F7 H8
  LONGEVITY_GUARD mutes Stage-4-H8 measurement (interleave Stage 6); F8 no longevity assertion
  track in harness yet; F9 golden-key invariant needed; F13 intermediate accuracy gates +
  plateau checkpoint + abstain ceiling. All folded into plan v3.

---

## Decisions owned by the USER (domain authority)

- Validated the 12 H1 verdicts (some stronger than the reviewer: chart_10 & chart_31 →
  **afflicted** not mixed; "weak constitution is purely negative H1 testimony", "career is H10").
- Validation method: agents draft → user confirms (DRAFT→CONFIRMED). Pending: batches A2..G.
- Fresh-cast from DOB/TOB/POB where given (computed degrees must match Raman's print — this caught
  the Capricorn-vs-Aquarius methodology error on chart_10/33).

---

## Append new entries below this line
