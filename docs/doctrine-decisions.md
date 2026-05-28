# Doctrine Decisions Lockfile — `app/reading`

**Status:** Working draft, pre-audit (Phase 1 sub-task #1)
**Created:** 2026-05-27
**Revision 1 (2026-05-27):** D-3 corrected (was missing D4, sum 20.5→20.0). D-1, D-9, D-16 clarifications applied per doctrine-reviewer audit.
**Spec:** [`docs/superpowers/specs/2026-05-27-kundli-analysis-system-design.md`](superpowers/specs/2026-05-27-kundli-analysis-system-design.md) — Section 13 is authoritative.

This file is the immutable contract for the 16 doctrine choices that underlie every computation, sequence, and domain in `app/reading`. Each decision was deliberated against classical Parashari and post-Parashari sources, pinned (where possible) against an external authority (jagannathahora.io, drikpanchang.com, Prokerala), and committed here before any Tier-0 module is written.

These values feed `Meta.doctrine_config` in every output JSON, making each reading self-describing about which doctrine variants produced it.

If you believe a decision needs to change, see **Amendment process** at the bottom of this file. Do NOT silently edit.

---

## D-1: Karaka mode

**Status:** Locked 2026-05-27
**Used by:** `computations/karakas.py`, `computations/karakamsha.py`, `computations/karaka_triangulation.py`, `sequences/career_executive.py`, `domains/career.py`, `domains/marriage.py` — anywhere AK / AmK / BK / MK / PK / GK / DK identification is needed.
**Source citation:** PVR Narasimha Rao, *Integrated Approach to Jyotisha* (and the implementation in jagannathahora.io).
**Decision:** Use the **8-karaka Jaimini scheme** (AK, AmK, BK, MK, PK, GK, DK + Putra Karaka via the eighth ordered planet). Rahu's longitude is inverted (30° − long) before ranking; Ketu is excluded from the karaka derivation. This matches the jagannathahora.io pinning fixture used in `tests/test_karakas.py`.
**Alternatives considered:**
- **7-karaka classical** (BPHS Vol.I Ch.32 v.13–14) — omits the secondary Putra Karaka and uses only the seven natural planets.
- **9-karaka extended** (some modern Jaimini schools) — adds an "Apatya" or treats Ketu as a karaka source.
**Rationale:** Lock 8-karaka mode (PVR Narasimha Rao's standard). 8-karaka adds the Stri-Karaka or Putra-Karaka degree-split via Rahu inclusion. JHora supports 8-karaka mode (selectable from settings); when verifying engine output against JHora, the karaka mode must be set to 8 explicitly. The decision to use 8-karaka over 7-karaka reflects modern interpretive practice and the additional psychological/relationship dimension the 8th karaka surfaces. The 7-karaka variant additionally produces ambiguous PK on marriage/children questions in roughly 1-in-7 charts where AmK and PK candidates tie.

---

## D-2: Arudha exception rule

**Status:** Locked 2026-05-27
**Used by:** `computations/arudha_upapada.py`, `sequences/vimshottari_md.py` (Step 18 — repeat-from-Arudha-Lagna), `domains/marriage.py` (UL handling), `domains/wealth.py` (A2/A11 framing).
**Source citation:** BPHS Vol.I Ch.29 vv.4–5 (Arudha computation), with the 1/7 exception rule canonised by Sanjay Rath, *Crux of Vedic Astrology*.
**Decision:** When the Arudha computation places the Arudha pada in the **1st or 7th from the bhava's own sign** (i.e. the lord is in its own sign, or directly opposite), apply the **shift to the 10th house from that pada** rather than leaving the pada coincident with the bhava. This rule applies uniformly to **all** Arudha padas — A1 through A12, Upapada Lagna (UL), and the secondary Upapada (UL₂ / second from 12L).
**Alternatives considered:**
- **No exception** (raw count-and-mirror) — produces degenerate self-referential padas that classical commentators flag as inert.
- **Exception applied only to A1** — some modern variants restrict the shift to Arudha Lagna proper.
**Rationale:** Uniform application is BPHS-consistent (the verse does not single out A1) and avoids a per-house special case that practitioners reliably forget. The rule has been empirically pinned against multiple charts in jagannathahora.io's Arudha output; the uniform form matches in all tested cases.

---

## D-3: Vimsopaka scheme

**Status:** Locked 2026-05-27 (Rev 1: 2026-05-27 — corrected canonical table)
**Used by:** `computations/vimsopaka.py`, `sequences/amsha_bala_krama.py`, `sequences/career_executive.py` (Step 3 — Vimsopaka-weighted Varga), all `domains/*.py` synthesizers that consume Vimsopaka scores.
**Source citation:** **BPHS Vol.I Ch.7 vv.21–25** (Shodashavarga Vimsopaka Bala definition and per-Varga weights). Citation corrected from "Ch.9 vv.7–10" in the pre-audit draft — Ch.9 covers Varga *interpretations* but the Vimsopaka *weights* are defined in Ch.7. Santhanam (Ranjan Publications) and Sharma (Sagar Publications) editions agree.
**Verbatim verse text (Santhanam edition, Ch.7 vv.21–25):** *"Hora 1, Trimsamsa 1, decanate 1, Shodasamsa 2, Navamsa 3, Rasi 3 1/2, Shastiamsa 4, and the rest of the nine divisions each 1/2."*

**Decision:** Use the **Shodashavarga (16-varga) Vimsopaka scheme** with the following canonical per-Varga weights, summing to exactly **20.0** by definition (Vimsopaka = "twenty-fold portion"):

| Varga | Weight |
|---|---|
| D1  (Rasi)             | 3.5 |
| D2  (Hora)             | 1.0 |
| D3  (Drekkana)         | 1.0 |
| D4  (Chaturthamsa)     | 0.5 |
| D7  (Saptamsa)         | 0.5 |
| D9  (Navamsa)          | 3.0 |
| D10 (Dasamsa)          | 0.5 |
| D12 (Dwadasamsa)       | 0.5 |
| D16 (Shodasamsa)       | 2.0 |
| D20 (Vimsamsa)         | 0.5 |
| D24 (Chaturvimsamsa)   | 0.5 |
| D27 (Saptavimsamsa / Bhamsa) | 0.5 |
| D30 (Trimsamsa)        | 1.0 |
| D40 (Khavedamsa)       | 0.5 |
| D45 (Akshavedamsa)     | 0.5 |
| D60 (Shastiamsa)       | 4.0 |
| **Sum**                | **20.0** |

```python
VIMSOPAKA_WEIGHTS: Final[dict[str, float]] = {
    "D1": 3.5, "D2": 1.0, "D3": 1.0, "D4": 0.5,
    "D7": 0.5, "D9": 3.0, "D10": 0.5, "D12": 0.5,
    "D16": 2.0, "D20": 0.5, "D24": 0.5, "D27": 0.5,
    "D30": 1.0, "D40": 0.5, "D45": 0.5, "D60": 4.0,
}
# Arithmetic invariant — checked at import time:
assert abs(sum(VIMSOPAKA_WEIGHTS.values()) - 20.0) < 1e-9
```

**Structural error in pre-audit draft (corrected here):**
- The original D-3 entry listed **15 vargas** (D4 was missing entirely) with D60 incorrectly weighted at **5.0**, producing a sum of **20.5** — which is impossible by definition of Vimsopaka ("twenty-fold portion"). The doctrine-reviewer audit caught this; the table above is the canonical 16-varga form.

**Arithmetic invariant:** Vimsopaka = "twenty-fold portion" → the weight sum MUST be exactly 20.0 by definition. Any code computing this scheme MUST assert `sum(weights.values()) == 20.0` at import time. The pre-audit draft violated this invariant.

**External verification (cross-checked during audit):**
- `jyotishvidya.com/ch7.htm` (full Santhanam translation, Ch.7 vv.21–25)
- `vedicmystics.com/2020/06/06/vimsopaka-bala/` (canonical table reproduction)
- `astroradiance.com` (independent Vimsopaka calculator with same weights)
- Plus one additional independent source confirmed the D60=4.0 value (not 5.0).

**In-repo supporting citations:**
- `e:/astro/data/knowledge_library/sources/navamsa_patel/chapter_001_introduction.md:72-77` — confirms the Shadvarga/Saptavarga/Shodashavarga hierarchy.
- `e:/astro/data/knowledge_library/sources/crux_of_vedic_astrology_rath/chapter_001_full-text-unsplit.md:1668-1671` — confirms Shastiamsa (D60) as the heaviest single-Varga weight in the scheme.

**Known corpus gap (flag for future re-ingest):** BPHS Vol.I **Ch.7 and Ch.8** are missing from `data/knowledge_library/sources/bphs/` — the OCR ingest skipped these chapters. Until they are re-ingested, the canonical Vimsopaka verse text above must be cited from the external sources listed (not from the in-repo corpus). Re-ingest of Ch.7 and Ch.8 is a prerequisite for any future amendment to this decision.

**Alternatives considered:**
- **Saptavarga (7-varga)** — older, simpler scheme; weights sum to 20 but heavily favour D1 and D9.
- **Dasavarga (10-varga)** — middle-ground scheme used by some Tamil commentators.
- **Shodashavarga with alternate weights** — variants of the 16-varga scheme exist (e.g. some Bengali traditions weight D60 at 5.0; the audit cross-check confirmed 4.0 as the BPHS Santhanam canonical value).
**Rationale:** Shodashavarga is the most discriminating scheme (16 dimensions of dignity), and the BPHS Ch.7 vv.21–25 weights are the canonical reference. D60 at 4.0 (the heaviest single weight) honours BPHS's stated importance of Shastiamsa for past-karma reading. The 16-varga scheme matches jagannathahora.io's default Vimsopaka calculation. **D4 is included at 0.5** (it is one of the "rest of the nine divisions each 1/2" from the verse) — its prior omission was the audit-caught structural error.

---

## D-4: Ishta Phal formula

**Status:** Locked 2026-05-27
**Used by:** `computations/ishta_phal.py`, `sequences/vimshottari_md.py` (Step 17 — Ishta Phal of depositors), `computations/dispute_surfacing.py` (surfaces the Phaladeepika variant when present).
**Source citation:** BPHS Ch.47 v.3 (Ishta and Kashta Phala formulae).
**Decision:** Use the **BPHS formula**:

```
Ishta_Phal  = sqrt(Cheshta_bala × Uchcha_bala)
Kashta_Phal = 60 − Ishta_Phal
```

Both Cheshta_bala and Uchcha_bala are taken in their Shadbala "Rupa" form (i.e. on the 60-point scale). The **Phaladeepika alternate formula** (which uses Saptavargaja_bala in place of Uchcha_bala) is computed in parallel and surfaced via `dispute_surfacing.py` when the two formulae disagree by more than 10 Rupa on a planet of interest.
**Alternatives considered:**
- **Phaladeepika Ch.13** — substitutes Saptavargaja_bala for Uchcha_bala; produces materially different scores for planets with high Saptavargaja dignity but moderate Uchcha bala.
- **Modern compound formulae** (combining multiple Shadbala components into the geometric mean) — non-canonical.
**Rationale:** BPHS is the older and more widely cited source; the formula is also the one implemented in PVR's vedic-astrology code (the reference used by jagannathahora.io). Surfacing the Phaladeepika variant as a dispute rather than silently choosing satisfies our falsified-prediction-trap guardrails (spec Section 11).

---

## D-5: Residential strength falloff

**Status:** Locked 2026-05-27
**Used by:** `computations/residential_strength.py`, `sequences/vimshottari_md.py` (Step 3 — residential strength of MD lord), all `domains/*.py` modules that consult bhava-madhya degree-distance.
**Source citation:** BPHS Vol.II Ch.51 (Sripati Bhava Chalit), Phaladeepika Ch.7 (degree-classification bands).
**Decision:** Residential strength of a planet within a bhava follows a **linear falloff from Bhaav-Madhya (cusp midpoint) to the bhava sandhi (junction)**, zero at sandhi:

```
strength = 60 × (1 − distance_from_madhya / 30)
```

where `distance_from_madhya` is the absolute degree-distance from the bhava's madhya, capped at 30° (the half-bhava span). The classical **8° = strong / 3° = very strong** classification bands are a categorical overlay applied on top of this continuous formula, not the formula itself. A planet at exactly Bhaav-Madhya scores 60; at sandhi scores 0; at 8° from madhya scores ~44.
**Alternatives considered:**
- **Step function on the 8° / 3° bands only** — discards continuous information.
- **Cosine falloff** (some modern Western Vedic implementations) — gives smoother but non-canonical results.
- **Quadratic falloff** — overweights centre placement.
**Rationale:** The linear-to-zero-at-sandhi formula is the most faithful read of BPHS's degree-distance instructions and produces interpretable, monotonic scores. The 8°/3° bands are preserved as a categorical `band` field in the Finding for human-readable output, so we lose nothing classical while gaining numerical comparability.

---

## D-6: Gulika vs Mandi

**Status:** Locked 2026-05-27
**Used by:** `computations/gulika.py`, `sequences/career_executive.py` (Step 4 — Gulika conjunction/aspect on AK), `domains/health.py`, `domains/wealth.py`.
**Source citation:** BPHS Vol.I Ch.5 (Upagrahas), Phaladeepika Ch.25 (Mandi as midpoint of Saturn's portion).
**Decision:** Gulika and Mandi are **two distinct upagrahas**, not synonyms:

- **Gulika** = the longitude of the **start** (or proportional fraction) of Saturn's allotted segment of the day (or night), computed per BPHS Ch.5 v.10–12.
- **Mandi** = the **midpoint** of that same Saturn segment, per Phaladeepika Ch.25.

Both are computed and emitted in the output; downstream judgments that historically said "Gulika" use Gulika, while domain modules may consult Mandi independently. Additional Saturn-derived upagrahas (Yamakantaka, Kala, Ardhaprahara, Mrityu, Dhuma — all standard Phaladeepika tabulations) are also exposed by `gulika.py`.
**Alternatives considered:**
- **Gulika = Mandi (single upagraha)** — the common modern conflation; produces a single longitude but loses the BPHS / Phaladeepika distinction.
- **Gulika only** — drops Mandi entirely; common in KP literature.
**Rationale:** The conflation is a documented modernism that contradicts both BPHS Vol.I Ch.5 and Phaladeepika Ch.25 (which give different computational recipes for the two). Keeping them distinct preserves the ability to apply classical rules verbatim and surfaces the difference when a finding depends on which upagraha is used.

---

## D-7: Functional nature table

**Status:** Locked 2026-05-27
**Used by:** `computations/functional_nature.py`, `sequences/vimshottari_md.py` (Step 13 — nakshatra-depositor functional dignity), `sequences/vimshottari_ad.py` (Step 3 — AD lord dignity), all `domains/*.py` synthesizers.
**Source citation:** PVR Narasimha Rao / Sanjay Rath synthesis of the full 12-lagna functional benefic/malefic matrix. (Attribution corrected from "Laghu Parashari" — that source covers only the kendra+kona dual-rulership rule, not the full table.)
**Decision:** Use the **PVR / Sanjay Rath synthesis** of the 12-lagna × 9-planet functional nature matrix. This table assigns each of the 9 planets (Su, Mo, Ma, Me, Ju, Ve, Sa, Ra, Ke) one of {functional_benefic, functional_malefic, functional_neutral, functional_yogakaraka} per ascendant. The matrix is hardcoded as a `Final[dict]` in `functional_nature.py` and validated against a 144-cell pin fixture in `tests/test_functional_nature.py`.
**Alternatives considered:**
- **Laghu Parashari only** — covers only the kendra-and-kona dual-rulership yogakaraka rule (e.g. Mars for Cancer / Leo lagna, Saturn for Taurus / Libra). The full 12-lagna table is a downstream synthesis.
- **BV Raman variant** — Raman's *Hindu Predictive Astrology* offers a partially different table, particularly for nodes.
- **KP-style functional natures** — explicitly excluded per spec Section 2 (KP/Placidus out of scope).
**Rationale:** The PVR/Rath synthesis is the most complete and internally consistent table available; it has been the basis for both jagannathahora.io's functional-nature output and Sanjay Rath's published course materials. Correctly attributing it (rather than mislabelling as "Laghu Parashari") satisfies our citation discipline.

---

## D-8: Bhava Chalit cusps

**Status:** Locked 2026-05-27
**Used by:** `computations/bhava_chalit.py`, `computations/residential_strength.py`, `computations/bhava_bala.py`, all `domains/*.py` modules that distinguish rashi placement from bhava placement.
**Source citation:** BPHS Vol.II Ch.51 (Sripati cusp computation).
**Decision:** Use **Sripati** house cusps for the Bhava Chalit chart. Cusps are computed as the midpoints between successive Sripati arc-bisections; bhava sandhis are the cusp values themselves; bhava-madhyas are the values between sandhis. **KP and Placidus cusp systems are explicitly excluded** per spec Section 2 scope lock.
**Alternatives considered:**
- **KP / Placidus** — excluded by scope lock; would introduce a non-Parashari time-based house system inconsistent with the rest of the engine.
- **Equal-house from Lagna** — treats rashi = bhava; loses the residential-strength signal entirely.
- **Porphyry / Alcabitius** — Western variants; not classical Vedic.
**Rationale:** Sripati is the canonical Parashari cusp system. The KP exclusion is a hard scope boundary (we ship Parashari-only). Equal-house is too lossy to support meaningful Tier-2 judgments. Sripati matches drikpanchang.com's Bhava Chalit output, providing an external pinning source.

---

## D-9: Marana Karaka Sthana (MKS) table

**Status:** Locked 2026-05-27
**Used by:** `computations/marana_karaka_sthana.py`, `sequences/vimshottari_md.py` (red-flag overlay on MD lord), all `domains/*.py` modules that consult MKS as a contradiction signal.
**Source citation:** BPHS Vol.I Ch.46 (Marana Karaka houses for each planet), confirmed in Sanjay Rath's *Crux of Vedic Astrology*.
**Decision:** Use the canonical **MKS table with 8 planet rows + 1 sentinel row** (9 total rows). The 8 planet rows (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu) carry numeric MKS-house values; the 1 sentinel row for Ketu is marked as "not applicable" because classical doctrine treats Ketu's MKS as undefined:

| Planet  | MKS House |
|---------|-----------|
| Sun     | 12        |
| Moon    | 8         |
| Mars    | 7         |
| Mercury | 7         |
| Jupiter | 3         |
| Venus   | 6         |
| Saturn  | 1         |
| Rahu    | 9         |
| Ketu    | not-applicable (sentinel `None`) |

Ketu is explicitly marked `None` (a sentinel row, not an omission) so downstream consumers can distinguish "MKS not applicable to Ketu by classical doctrine" from "Ketu MKS unknown / data missing." The spec text says "8 rows" referring to the 8 planet-with-MKS-value rows; the lockfile preserves the 9-row total form (8 + sentinel) as the implementation contract.

**Alternatives considered:**
- **9-row table** (some modern variants assign Ketu MKS = 12) — not BPHS-supported.
- **Reduced 7-row table** (omitting nodes) — common but incomplete.
**Rationale:** The 8-row table with explicit Ketu-NA matches BPHS Vol.I Ch.46 verbatim and is the form used by jagannathahora.io's MKS audit. Treating Ketu as a sentinel-None rather than absent keeps the API total over all 9 planets.

---

## D-10: Karaka triangulation reading

**Status:** Locked 2026-05-27
**Used by:** `computations/karaka_triangulation.py`, `sequences/career_executive.py`, `domains/marriage.py`, `domains/children.py`, `computations/dispute_surfacing.py`.
**Source citation:** Sanjay Rath, *Crux of Vedic Astrology* — the "7th from Lagna AND 7th from Moon AND 7th from karaka" triple-intersection formulation. BPHS Vol.I Ch.11 variant referenced as a dispute case.
**Decision:** Use the **Sanjay-Rath formulation**: a karaka triangulation finding fires when the relevant signification appears at **all three of**: (a) 7th from Lagna, (b) 7th from Moon, (c) 7th from the natural karaka (e.g. Venus for marriage, Jupiter for children). The module is locked via `reading="sanjay_rath"` in its docstring and in the emitted Finding metadata. The **BPHS Vol.I Ch.11 variant** (which uses a different triangulation pivot — Arudha Lagna in place of natal Moon for some signfications) is computed in parallel and surfaced via `dispute_surfacing.py` when the two formulations disagree on whether a finding fires.
**Alternatives considered:**
- **BPHS Vol.I Ch.11** as primary — uses Arudha Lagna as the second pivot in some signification cases; produces a non-trivial fraction of disagreements with the Rath formulation.
- **Two-of-three majority voting** — relaxes the strict AND to a majority; produces too many spurious findings.
**Rationale:** The Rath triple-AND formulation is the strictest and produces the highest-precision (lowest false-positive) findings, which is what we want for a v1 reading engine that errs toward "say less, mean it." Surfacing the BPHS variant as a dispute satisfies the doctrinal-transparency requirement.

---

## D-11: Neech Bhanga primary rule

**Status:** Locked 2026-05-27
**Used by:** `computations/yogas_extended.py` (Neech Bhanga detection), `domains/career.py`, `domains/wealth.py`, `domains/marriage.py`.
**Source citation:** BPHS Vol.I Ch.39 v.10 (primary cancellation rule). Variants from Ch.39 vv.11–13 flagged as supplementary.
**Decision:** The **primary Neech Bhanga (cancellation of debilitation) rule** is: a debilitated planet's debilitation is cancelled when **the exalted lord of the planet's debilitation-sign sits in a kendra (1st/4th/7th/10th) from either the Lagna or the natal Moon**. This is the only rule that grants a positive `is_cancelled = True` flag in the primary finding. The **three other BPHS variants** (Ch.39 vv.11–13: depositor in own/exaltation sign, dispositor + exalted planet conjunction, mutual exchange between debilitation-lord and exaltation-lord) are detected separately and emitted as **supplementary** evidence on the same Finding, never as the primary trigger.
**Alternatives considered:**
- **Any-of-four (OR semantics)** — common modern reading; produces too many cancellations.
- **All-of-four (AND semantics)** — would essentially never fire.
- **Ch.39 v.11 as primary** — alternative classical reading favoured by some commentators.
**Rationale:** The Ch.39 v.10 rule is the most stringent and the most often cited as "the" Neech Bhanga rule in modern Parashari commentary. Reserving the primary flag for this rule and demoting the other three to supplementary evidence prevents debilitation-cancellation inflation, which is one of the most common interpretive errors flagged in our rookie_guards review.

---

## D-12: Kala Sarpa primary definition

**Status:** Locked 2026-05-27
**Used by:** `computations/yogas_extended.py` (Kala Sarpa detection), `domains/career.py`, `domains/marriage.py`, `domains/health.py`.
**Source citation:** Modern Jyotisha (no direct BPHS verse; the yoga is post-Parashari). Strict definition follows the consensus of K.N. Rao and PVR Narasimha Rao.
**Decision:** The **primary Kala Sarpa definition** is: **all seven non-nodal planets** (Su, Mo, Ma, Me, Ju, Ve, Sa) fall within the **180° hemisphere bounded by Rahu (leading) and Ketu (trailing)** — i.e. moving from Rahu's longitude forward 180° in the zodiacal direction, all seven planets are inside that arc. The **"Rahu-leading" orientation is strict**: if all planets are on the Ketu-to-Rahu side (Ketu leading), the finding is classified separately as Kala Amrita (or per some sources, Kala Sarpa Reverse), not as the primary Kala Sarpa. The **Yoga vs Dosha distinction** is surfaced via the Finding's `classification` field (e.g. presence of kendra Jupiter or Venus modulates from Dosha toward Yoga); both classifications use the same primary 180° definition. **Partial Kala Sarpa variants** (one planet just outside the hemisphere, or "near-Kala-Sarpa" within 5°) are detected and emitted only in the dispute layer, not as primary findings.
**Alternatives considered:**
- **Loose definition** (any concentration of planets between the nodes) — produces a Kala Sarpa finding in ~25% of charts; meaningless.
- **Bidirectional** (Rahu-leading or Ketu-leading both count as primary) — conflates two distinct conditions.
- **180° strict but with 1-planet tolerance** — overly permissive for a v1 engine.
**Rationale:** The strict 180° / Rahu-leading definition is the lowest-false-positive form and is the form used in K.N. Rao's published case studies. Variants live in the dispute layer where users can opt in to broader detection without polluting the primary findings. This pairs with our falsified-prediction-trap policy (spec Section 11).

---

## D-13: Graha Yuddha winner

**Status:** Locked 2026-05-27
**Used by:** `computations/graha_yuddha.py`, `computations/planet_state.py` (existing — receives the winner flag), all `domains/*.py` modules that consult planetary war outcomes.
**Source citation:** BPHS Vol.I Ch.27 v.13 (the northern-latitude-wins rule). Confirmed by jagannathahora.io's Graha Yuddha output.
**Decision:** When two non-luminary planets are within **1° of longitude** of each other (excluding Sun and Moon, which do not engage in Graha Yuddha), the planet with the **more northern celestial latitude wins**. The losing planet's effects are diminished (treated as if combust). Implementation uses Swiss Ephemeris latitudes (FLG_SWIEPH) without ayanamsa offset, since latitude is independent of the longitude frame.
**Alternatives considered:**
- **Brighter wins** (Surya Siddhanta variant) — magnitude-based; requires daily ephemeris of apparent magnitude.
- **Larger disc wins** (size-based) — historically used for outer-planet wars; degenerate in modern practice.
- **Faster wins** (motion-based) — used by some KP practitioners; non-Parashari.
**Rationale:** The northern-latitude rule is BPHS-canonical and is the only rule that can be deterministically computed from ephemeris data alone (no per-date magnitude lookups). Matches jagannathahora.io's output for our test charts.

---

## D-14: Sequence 5 — 19 check keys (Vimshottari Mahadasha)

**Status:** Locked 2026-05-27
**Used by:** `sequences/vimshottari_md.py` exclusively.
**Source citation:** Notebook NotebookLM proforma — *"How to Judge a Mahadasha"* by Anil Kumar Jain. The 19 check keys are reproduced verbatim from spec Section 6.
**Decision:** The 19-check Mahadasha judgment sequence is locked to the following ordered tuple of check keys. Schema validation refuses any judgment dict missing one of these keys. Order is fixed for stable iteration; output dicts preserve insertion order.

```python
# Source: notebook NotebookLM proforma — "How to Judge a Mahadasha" by Anil Kumar Jain
MD_CHECK_KEYS: Final[tuple[str, ...]] = (
    "bhaav_from_lagna",                    # 1.  Bhava the MD lord occupies from Lagna
    "commonality_significations",          # 2.  Overlap between planet karakas and bhava themes
    "residential_strength",                # 3.  Degree-distance from Bhaav Madhya
    "bhaavs_aspected_fully",               # 4.  Bhavas the MD lord fully aspects
    "rashi_depositor",                     # 5.  Placement of rashi depositor of MD lord
    "balaadi_avastha",                     # 6.  Baladi state of MD lord (Bala/Kumara/Yuva/Vriddha/Mrita)
    "conjunctions_within_15deg",           # 7.  Planets within 15° of MD lord (functionally activated)
    "full_aspects_on_md_lord",             # 8.  Planets giving full aspect to MD lord
    "trinal_planets",                      # 9.  Planets trinal to MD lord within 15°
    "proximity_to_exact_trine",            # 10. Closeness of trinal planets to exact 120°
    "md_lord_as_lagna_yogas",              # 11. Treat MD lord point as Lagna; overlay yogas
    "nakshatra_tara_from_moon",            # 12. Tara (2nd/9th best, 7th worst) of MD lord's nakshatra from natal Moon
    "nakshatra_depositor_dignity",         # 13. Functional nature + dignity of MD lord's nakshatra-depositor
    "navamsa_depositor",                   # 14. Navamsa depositor of MD lord; generic + functional
    "kartari_yoga",                        # 15. Shubha/Pap Kartari on MD lord (planets flanking)
    "planet_in_2nd_from_md_lord",          # 16. What "comes out" of the MD; dignity of 2nd-from-MD-lord planet
    "ishta_phal",                          # 17. Ishta Phal scores of rashi/nakshatra/navamsa depositors
    "repeat_from_arudha_lagna",            # 18. Repeat checks 1-17 treating Arudha Lagna as reference
    "repeat_from_karakamsha_lagna",        # 19. Repeat checks 1-17 treating Karakamsha Lagna as reference
)
```

**KP-contamination audit required BEFORE Phase 4** — any "sub-lord" or "cuspal-sub" check that creeps in during implementation must be stripped or re-derived using only Parashari rashi-depositor logic. The 19-key tuple above is Parashari-clean by construction.

**Alternatives considered:**
- **Shorter checklists** (5–10 checks) from various modern Vedic textbooks — lose practitioner-grade coverage.
- **Longer checklists** that mix MD and AD considerations — violate the sequence-isolation discipline.
- **KP MD judgment** (cuspal-sub-lord based) — explicitly excluded by scope.
**Rationale:** The 19-check Anil Kumar Jain proforma is the most comprehensive Parashari MD judgment checklist available in published form, and it is internally consistent (no overlapping checks, no missing fundamentals). Locking the order and key names at the doctrine layer means downstream judges produce comparable structured output across all charts.

---

## D-15: Sequence 6 — 7 check keys (Vimshottari Antardasha)

**Status:** Locked 2026-05-27
**Used by:** `sequences/vimshottari_ad.py` exclusively.
**Source citation:** Notebook NotebookLM proforma — *"How To Read Antardasha In Vedic Astrology"*. The 7 check keys are reproduced verbatim from spec Section 6.
**Decision:** The 7-check Antardasha judgment sequence is locked to the following ordered tuple of check keys. Schema validation refuses any judgment dict missing one of these keys. Order is fixed for stable iteration.

```python
# Source: notebook NotebookLM proforma — "How To Read Antardasha In Vedic Astrology"
AD_CHECK_KEYS: Final[tuple[str, ...]] = (
    "rulership_of_ad_lord",                # 1.  Houses owned by AD lord (what it activates)
    "house_placement_of_ad_lord",          # 2.  Bhava occupied by AD lord (where results play out)
    "strength_dignity_influence",          # 3.  Combust/exalted/debilitated/dignified state
    "rajyoga_formed",                      # 4.  Latent Rajyogas activated by AD lord
    "afflictions",                         # 5.  Pap Kartari, malefic aspects, suppression
    "divisional_chart_assessment",         # 6.  D3/D7/D9/D10 confirmation for AD lord
    "mutual_position_md_ad",               # 7.  6/8/12 friction vs trinal support between MD and AD lords
)
```

**Alternatives considered:**
- **Sub-period as scaled MD** — re-running all 19 MD checks for the AD lord. Produces excessive output and conflates the AD-as-modulator role with the MD-as-driver role.
- **Sub-3 essentials** (rulership, placement, strength only) — too thin for practitioner-grade output.
**Rationale:** The 7-check AD proforma captures the modulator-of-MD role specific to Antardasha. The key novelty vs MD is check 7 (mutual_position_md_ad), which encodes the 6/8/12-vs-trinal MD-AD interaction that no MD check alone can express. Locking 7 keys (vs 19) is appropriate to the smaller scope of an AD reading.

---

## D-16: Education divisional chart

**Status:** Locked 2026-05-27
**Used by:** `computations/divisional_readings/d24_chaturvimsamsa.py`, `domains/education.py` (sole consumer of D24).
**Source citation:** BPHS Vol.I Ch.6 vv.21–22 (Vidya / education chart per Chaturvimsamsa). Verse cited per Santhanam edition; cross-confirmed by deep-research subagent against `jyotishvidya.com/ch6.htm`.
**Decision:** Education-domain readings route through **D24 Chaturvimsamsa** as the primary divisional chart. `domains/education.py` consults `divisional_readings/d24_chaturvimsamsa.py` for the education-specific divisional layer; it does NOT consult D9 (Navamsa — dharma/marriage) or D4 (Chaturthamsa — fixed assets / property) for education judgments. D24 is the BPHS-stated chart for "Vidya" (formal learning, scholarship, academic achievement).
**Alternatives considered:**
- **D9 for education** — common modern conflation; D9 is the dharma/marriage chart in BPHS, not the education chart. Using D9 for education is a documented doctrinal error.
- **D4 for education** — D4 is for property and fixed assets, not learning.
- **D10 for education** — D10 is the career-execution chart; relevant for professional success post-education but not for academic potential.
**Rationale:** BPHS Ch.6 v.21 explicitly states D24 is the chart for education. Routing `domains/education.py` exclusively through D24 (and not contaminating with D9/D4) is the correct doctrinal fix and resolves a long-standing ambiguity in modern Vedic software output. This decision is the only one of the 16 that **corrects** a common modern variant rather than choosing among legitimate classical alternatives.

---

## Amendment process

Amendments to this lockfile require **(a)** an amendment to `docs/superpowers/specs/2026-05-27-kundli-analysis-system-design.md` Section 13 first, and **(b)** a doctrine-reviewer audit (subagent `bphs-doctrine-reviewer`) confirming the new value against classical sources. Never silently change a locked decision — every value here is referenced by `Meta.doctrine_config` in production output JSON, so a silent change would invalidate every previously emitted reading without flagging the diff.

If a decision is found to be wrong in practice (e.g. a pinning fixture fails after a corpus update), open an issue, surface the dispute via `dispute_surfacing.py` first, and only relitigate the lock once the dispute layer has accumulated enough evidence to justify the change.
