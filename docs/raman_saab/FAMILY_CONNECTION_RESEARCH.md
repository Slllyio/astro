# Family connection in Vedic astrology — a provenance-honest research map

> **What this is.** A deep-research survey (2026-07-23) of the astrological *theses* and *techniques*
> for **family connection** — why family members are karmically bound, and how to read the bonds
> across charts — mapped onto this engine's corpus + code, with **honest provenance** on every claim.
> No private data. The point is to separate what is *doctrinally real and buildable* from what is
> *modern lore dressed as tradition*, before building anything.

## 0. The honesty frame (read first)

Two firewalls govern what is *citable* here:
- **Live-six Raman rule** (`doctrine/book_registry.py`): only HTJAH-I/II, HPA, GBB, 3HC, NH, AFB are
  `live`/citable on `main`. Everything else on disk is non-citable there.
- **Experiment carve-out**: on the `soul-destiny-experiment` branch, Jaimini (`JAIMINI`, `JS`) is
  unlocked — *branch-only, never merge to main without re-review*.

So a family-connection claim can be: `RAMAN_EXPLICIT` (live), `RAMAN_GENERAL_PRINCIPLE`,
`JAIMINI_EXPLICIT` (branch-only), `CLASSICAL_NONCITABLE` (BPHS / Praśna Mārga / Rath / Phaladeepika —
on disk, firewalled), or `ABSENT` (modern / oral / not in the corpus). **Nothing below is fabricated;
where a thesis has no grounding it is marked ABSENT.**

## 1. Headline — two tracks, one verdict

The grounded knowledge of family connection sorts into two tracks, and the flashiest "family-soul"
ideas fail the honesty test:

- **Track A — cross-chart TECHNIQUES Raman actually used** (derivative houses; two-chart synastry):
  citable, buildable now.
- **Track B — the karmic THESES** ("why" families come together): only **one** (ancestral-curse /
  lineage-karma) is both grounded *and* computable, and it is firewalled (BPHS / Praśna Mārga).
- **Modern lore, ABSENT from the corpus**: souls reincarnating together as a "soul-group"; a shared
  nakṣatra = shared past-life group; AK↔DK "soulmate" exchange between two charts; the Nāḍī
  "pre-scripted family". These are contemporary/oral. The `family_soul_group` layer is honest *only*
  because it already tags such interlocks `EDITORIAL_SYNTHESIS`, not doctrine.

## 2. Track A — cross-chart techniques (ranked by value × buildability)

| Rank | Technique | Method | Provenance | Engine status |
|---|---|---|---|---|
| **⭐1** | **Derivative houses (Bhavat Bhavam)** | Read a relative *as a lagna* from the native's chart: mother = 4th, her longevity = 8th-from-4th, her spouse (=father) = 7th-from-4th = 10th; spouse-maraka from the 7th; father-death from the 8th-from-9th. Pure modular counting, then run the existing house/varga judges from the rotated frame. | **RAMAN_EXPLICIT** for the specific applications (spouse-maraka-from-7th, father-death-from-9th, HTJAH-II); **RAMAN_GENERAL_PRINCIPLE** to generalize; the fully-worked "read the relative's whole life + longevity" chain is **CLASSICAL** (Rath *Crux* §1 L6050-6067). | The rotation primitive **already exists** (`rectification/scoring.py` `_relative_marakas`, HTJAH-I:4479-4481) but is trapped in the rectifier. `app/core/bhavat_bhavam.py` has the full arithmetic (outside the firewall). NEW: a standalone report-only relative-reader. Also closes the **mother's Moon-frame** gap (declared at `significations.py:213` but *unimplemented* — no `house_04_sukha/from_karaka.py`). |
| **⭐2** | **Two-chart synastry** | Overlay two charts: where each person's planets fall in the other's houses (Venus/Mars/Jupiter in the other's trines or 3/11 = good; Sun-Moon harmony except 2/12); cross-points (wife's Moon = husband's Lagna → stable); and Raman's **computable Kuja-Doṣa units** table with the 25%-tolerance matching rule. | **RAMAN_EXPLICIT** — HTJAH-I:9200-9433 gives the house-overlay rules, Mars-Venus, and the Kuja-units table. Raman **de-emphasizes** Aṣṭakūṭa ("more than Kuta agreement, it is the basic structure that matters", HTJAH-I:9263). | Nothing overlays *two* charts today (`two_spouse_children` only cross-references two D-7 *readings*). NEW: the first true two-chart synastry surface. |
| ⭐3 | **Mutual daśā-timing aligner** | For a shared date, intersect two members' running Vimśottarī MD/Bhukti (`dasha_on`) + Chara period on a bond-significator. | Vimśottarī = `RAMAN_EXPLICIT`; **the *alignment* of two people's daśās to time a shared event is `ABSENT_IN_RAMAN`** (editorial); the relative-daśā basis is Jaimini/Rath (`CLASSICAL`). | Thin report over the existing `dasha_on` APIs. |
| 4 | Tāra-bala two-person | Count B's Janma-nakṣatra from A's (mod 9 → the 9 tārās). | Single-chart tāra = RAMAN; two-person use is Muhūrta-matching (`CLASSICAL`/un-ingested). Raman ranks it *below* chart structure. | Trivial; **fold into #2 as one flagged line**, not its own layer. |
| 5 | Relationship vargas cross-referenced | Read D9/D7/D12/D3 *for the relative* and cross-check the relative's own chart's same varga. | Varga→domain map is RAMAN (HPA-11:195-201); the cross-reference step is general-principle. | Heavier; **subsumed by #1**. |
| 6 | Sudarśana Chakra (Lagna+Moon+Sun) | Tri-lagna reading. | **"Sudarśana" = 0 hits in HTJAH I/II + HPA → `ABSENT_IN_RAMAN`.** But the Raman-valid *two*-reference core (read each house from Lagna AND Moon) **already exists** (`house_template.py` Lagna+Chandra frames). | Do **not** build tri-lagna; at most expose a "confirmed across Lagna & Moon" flag. |

## 3. Track B — the karmic theses ("why" families connect)

| Thesis | Best corpus anchor | Provenance | Computable? |
|---|---|---|---|
| **Rinānubandha** (karmic-debt bond draws souls together) | The *term* — `astrological_magazine_v75_raman/…ch007:25119` ("the 'link of destiny' referred to as Rinanubandha… marriages sans Rinanubandha cannot survive"). The *philosophy* — NH:462 (prārabdha = destiny) and **HTJAH-I:10320** (a child's fate bound to the parents' karma). | term = **Raman-corpus but non-live** (Magazine); philosophy = **RAMAN_EXPLICIT**; the "6/8/12 + nodes = rina houses" mapping = **modern/ABSENT**. | Mostly philosophical; the parents-karma → child-longevity rule *is* computable (via bālāriṣṭa). |
| **Pitṛ-doṣa / ancestral curse** | **BPHS Ch. 82-83** — ~11 exact yogas for "no male issue **due to the curse of the father in the previous birth**" (Pitṛ-Śrāpa) + the mother's-curse set; remedy = Śrāddha at Gayā, "the family lineage is prolonged". Praśna Mārga: serpent-curse = "Rahu in the 5th, or with the 5th lord, no benefic aspect." Rath: **D-45 father-lineage, D-40 mother-lineage, D-60 past-births karma**. | **CLASSICAL_NONCITABLE** (BPHS, Praśna Mārga) + Jaimini/Rath (the D-40/45/60 scheme). | **YES — precise, one-line detectors.** The single grounded *and* buildable karmic thesis. |
| **Nodes & 12th = past-life / after-death seat** | BPHS vol1 ch23: "the **12th house relates to whether he will reincarnate**"; Rath: 9th = "past life and cause of birth (Saturn & Rahu)". | 12th-as-reincarnation-seat = **CLASSICAL**; nodes-as-past-life = Jaimini/Rath. **Note the project lock: live-Raman's Mokṣa-kāraka is *Saturn*, not Ketu** — "Ketu = past-life mastery" is **modern/ABSENT** in live Raman. | Partly (house/graha flags). |
| **Soul-group reincarnation** (souls incarnate together; shared nakṣatra = shared group) | none — only Bhṛgu-Nāḍī "Rahu/Ketu = family circle" (non-citable). | **ABSENT / Nāḍī-oral.** | No warrant (shared-nakṣatra detection is trivial but unsourced). |
| **Nāḍī / Bhṛgu "family script"** | method only, not a rule. | **ABSENT as doctrine / oral.** | No. |
| **Cross-chart AK↔DK "soulmate" synastry** | single-chart karaka only (`studies_jaimini/ch049`); no two-chart karaka comparison in the corpus. | cross-chart = **ABSENT / modern**; single-chart karaka = Jaimini. | Computable but **unsourced** — flag as modern if surfaced. |

## 4. The corpus-access decision (the crux for Track B)

The deepest, most personally-relevant thread — **ancestral/lineage karma (Pitṛ-doṣa)** — is *real and
computable*, but its home texts (**BPHS, Praśna Mārga**) are **firewalled**. Building it requires the
same kind of unlock we made for Jaimini: register BPHS/Praśna as branch-only-citable, sentinel-marked,
never-merge-to-main. This is a deliberate decision, not a default. (Alternatively, a Pitṛ-doṣa layer
could be built **report-only + tagged `CLASSICAL_NONCITABLE`** without unlocking, exactly as
`saptamsa_reading` tags the KP/Rath successive-child scheme today.)

## 5. Engine inventory — exists vs absent

- **Mature & citable**: family significations + karakas + rule sets (3 siblings/Mars, 4 mother/Moon,
  5 children/Jupiter, 7 spouse/Venus, 9 father/Sun); *kutumba* = the 2nd = family (**HTJAH, citable**);
  9th = Pitṛ-bhava (doctrine comment). Karaka-as-Lagna frames implemented for **spouse** (Venus,
  `house_07_kalatra/from_karaka.py`) and **father** (Sun, embedded in `house_09_bhagya`).
- **Report-only cross-chart surfaces** (the extension pattern): `two_spouse_children.py`,
  `family_soul_group.py` — distill → detect-on-genuine-agreement → **net nothing**.
- **Gaps**: no general derivative-house module in `app/raman_saab/`; **mother's Moon-frame unimplemented**;
  no dedicated D3-siblings / D12-parents / D9-spouse reader; no two-chart overlay; no family-karma /
  pitṛ / rina topic in `topics.yaml`; no methodology doc on karmic family bonds (this is the first).

## 6. Recommended build roadmap

1. **A1 — derivative-house relative reader** *(highest value, RAMAN_EXPLICIT, reuses existing machinery,
   closes the mother-frame gap)*. Report-only, nets nothing, mirrors `two_spouse_children`.
2. **A2 — two-chart synastry** *(Raman's own Kuja-units + overlay; the first two-chart surface)*. Folds
   Tāra (#4) in as one flagged line.
3. **B — ancestral-karma (Pitṛ-doṣa)** *(the deepest "why", touches the family's real issue-karma)* —
   only after the explicit corpus-access decision (unlock BPHS/Praśna branch-only, **or** ship it
   `CLASSICAL_NONCITABLE`). BPHS Ch.83 childlessness yogas + serpent-curse detector + D-40/45/60 vargas.
4. **A3 — mutual daśā-timing aligner** — lightweight; the alignment tagged editorial.

**Do not build**: soul-group-reincarnation readers, AK↔DK "soulmate" detectors, or a tri-lagna
Sudarśana — all `ABSENT` from the corpus. If ever surfaced, they must be tagged modern/editorial, never
doctrine.

## 7. Key sources (with firewall status)
- **Live / citable**: HTJAH-I:9200-9433 (synastry + Kuja-units), HTJAH-I:10320 (parents-karma→child),
  HTJAH-II:17826 / :2322 / :7891 / :8578 (derivative-house applications), NH:462 (prārabdha), kutumba
  (HTJAH-I:18293). 
- **Branch-only (experiment)**: `studies_jaimini_raman/ch049` (chara karakas), the soul layer's JS/JAIMINI.
- **Firewalled (CLASSICAL_NONCITABLE)**: BPHS vol2 ch82-83 (Pitṛ-Śrāpa yogas), BPHS vol1 ch23 (12th =
  reincarnation), Praśna Mārga vol2 ch18 (serpent-curse), Rath *Crux* ch12/ch15 (lineage vargas, nodes =
  past life), Phaladeepika, Jataka Tattva.
- **Non-live Raman**: `astrological_magazine_v75_raman/ch007` (the explicit "Rinānubandha" passage).
- **ABSENT / oral**: soul-group reincarnation, Nāḍī family-script, cross-chart AK-DK synastry.
