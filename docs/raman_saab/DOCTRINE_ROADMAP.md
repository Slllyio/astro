# Raman-fidelity encoding roadmap — what's left

> A prioritized map of what remains to encode for full fidelity to Sri B. V. Raman's natal
> Parashari system (the Prime Directive). Synthesized 2026-07-24 from a three-agent gap survey of
> the engine, the corpus, and the scope/backlog docs. Each item cites its anchor; nothing here is
> speculative — where a technique is present it says so.

## Already complete (do not re-do)

The engine is **saturated exactly where HTJAH is densest**: the 144 bhava-lord-in-house placements
+ 108 planet-in-house effects (verbatim HTJAH-I/II citations), the full six-source **Shadbala** +
**Bhava Bala** (GBB), the numeric **Ayurdāya** (Piṇḍāyu + Aṁśāyu + all four hāraṇas, method-selected,
validated to-the-day vs Raman's Charts 33/34, `primitives/ayurdaya.py`), **Vimśottarī** (MD→Bhukti→
Pratyantar) + Jaimini **Chara Dasha**, and the **Baladi / Jāgradādi / Deeptādi** avasthas. The golden
ratchet holds at **~77% exact / ~90% within-1** — the documented *honest ceiling*; the 12 dist≥2
misses are declared **over-fit-risk, not fixable by faithful general rules** (`DOCTRINE_BACKLOG.md`).

## Tier 1 — clean net-new (zero ratchet risk, build freely)

| Item | Status | Anchor | What's missing |
|---|---|---|---|
| ~~**Gochara Vedha** (transit obstruction)~~ | ✅ DONE (23e2efc) | `primitives/transits.py` — `_VEDHA` table + exempt pairs + `net_good` on `TransitRow` | — the Vedha cancellation table is now wired, with a table-completeness invariant. |
| **300 Combinations breadth** | ~72 of ~300 | `doctrine/yogas.py` (3HC + HPA-20) | the Akriti/shape set + named Raja/Dhana tail are DONE; the 4 clean HPA-20 named yogas landed (Sāradā/Kusuma/Brihadbija/Asatyavadi, 4cabcac). Remaining: Bherī/Shankha/Kahala/Lakshmi (deferred, need the B1 strength measure); Matsya (definition needs cross-verification — the OCR reading is unsatisfiable). |
| **Ashtakavarga sodhana + kakshya** | PARTIAL | `primitives/ashtakavarga.py` (raw BAV/SAV present) | Trikoṇa + Ekādhipatya *sodhana* reductions; Kakṣyā 8-fold transit subdivision; Sodhya-Piṇḍa AV longevity. |
| **H10 career-by-sign / trade-by-navāṁśa** | ABSENT | `rule_sets/house_10_karma/combinations.py:13` | the ~460-line HTJAH-II:10249-10800 catalogue — the single largest unencoded block (why H10 is the thinnest house). |
| Nisargāyu · Lajjitādi avasthas · Deeptadi 'Bhīta' | small gaps | `ayurdaya.py`, `primitives/deeptadi.py:37` | self-contained completeness items. |

## Tier 2 — unlock the half-wired (incremental predicates)

**~130 inert `RuleRecord(kind="descriptive", condition=None)` + 125 `TODO(predicate:…)` markers**
(~16% of the 828 rules) are cited Raman dicta that *cannot fire* — each blocked on a named missing
predicate. Landing one predicate unlocks a cluster:
- **Landed (4cabcac):** `TaraOf` (Tara-Bala, unlocked H1.C.35/36) and `LordHasDignity` (a
  conservative dynamic-lord strength proxy); `NeechaBhanga` now resolves `LORD_OF:n` subjects.
- **Missing predicates** (`conditions.py` "still to add"): `ArudhaLagna`, `MarakaDetection`,
  `NavamsaDispositor`, `StrongerThan`/`WeakerThan` + the B1 Shadbala `Strongest`/`Weakest`
  (the effective-strength measure that unblocks the bulk of the strength-gated inert cluster),
  `KARAKAMSA`-origin, `STRONGEST_OF`.
- **Biggest inert clusters**: H12 (22), H1 navāṁśa-qualifiers (10 still descriptive), H11 (21),
  H2 (19).
- **The D9 auxiliary gaps (D9-2)**: 10 H1 navamsa rules still descriptive
  (`navamsa_qualifiers.py`), blocked on lord-strength + `StrongerThan` + `AspectsBetweenLords`.
- **UNIMPLEMENTED H4 mother-from-Moon frame**: `significations.py:218` declares
  `alternate_frame_core="Moon"` but `house_04_sukha/` has **zero** frame rules — the mother's
  Moon-as-Lagna maraka reading is not evaluated. (H9/H10 karaka frames are PARTIAL/mislabeled.)

## Tier 3 — HIGH-risk verdict-path (holdout-tuner research, not clause work)

- **B1 comparative-weighing** — the dominant deferred mechanism (~17 NH charts + the chart_52/60
  siblings misses). **Empirically proven un-hand-codeable** (`NH_GAP_ANALYSIS.md:72-120`: every
  hand-coded effective-strength form regressed −4 to −40); buildable *only* as a calibrated re-fit
  via `tune_thresholds.py` with a holdout-lock. Highest yield, highest risk. Unblocks the HPA
  avastha + Shankha/Kahala/Lakshmi yogas too.
- **D9-6 / D7-4-item-3 netting** — let navamsa / saptamsa move a *decisive* verdict (not just a
  borderline mixed). Same tuner-gated HIGH-risk profile as B1 (`D9_LAYER_SCOPE.md:55-60`,
  `D7_LAYER_SCOPE.md:143-148`).
- **H3 bhava-rescue** — the one *clean* real-outcome fix (HTJAH-I:503-505), written + gated on an
  n=2 confirmation (`FEEDBACK_UTILIZATION_PLAN.md:82-87`).

## Tier 4 — resolve one ambiguity first

The **longevity verdict release**: the survey disagreed — ayurdāya is wired into the maraka
death-window and confirmed span goldens, yet `LONGEVITY_GUARD` (`house_template.py:930-941`) still
neutralises the `longevity` signification into insufficient-evidence. A direct check will tell
whether the guard can now be cleanly released to emit a real longevity verdict.

## Out of scope (not gaps)

**Muhūrta / Praśna / Varṣaphal** — different systems, firewalled (`book_registry.py`), corpus
present but non-citable. Greenfield sub-packages if ever pursued, never core Raman-natal gaps.

## Doctrine-source coverage (proxy for under-encoding)

HTJAH-II (442 citations) + HTJAH-I (403) are saturated. The under-encoded *live* books:
**3HC** (58 cites, yogas only, ~13%), **HPA-20** named yogas (0 rule-cites beyond mechanics),
**NH** (0 encoded rules — used only as a golden source; 2 of ~50 chapters acquired). The corpus is
mined for house-judgment; yogas + the worked casebook are the frontier.
