# Source Expansion Research — what to add, and what not to

*Researched 2026-08-08 (corpus audit + web). Requested as: "what can be added so that the
engine can be made more accurate and close to BV Raman sir; also what other non-BV-Raman
sources can be added which can make the Raman engine efficient and accurate."*

## The frame that keeps this honest

**Accuracy against Raman's printed verdicts is at its measured ceiling and is CLOSED.**
259/293 exact · 283/293 within-1 · 10 real-errors; five independent methods proved the ceiling
cannot be faithfully exceeded (CLAUDE.md, Measured Truth). Nothing in this report proposes
chasing that number — a recommendation that moved the ratchet would be overfitting wearing a
research costume.

What "closer to Raman" CAN still mean, and what this report is about:

1. **Coverage** — Raman wrote far more than the engine has encoded. Encoding more of him,
   faithfully, widens what the engine can say without touching how it judges.
2. **The casebook** — more of Raman's own worked readings (validation and attention assets,
   never tuning data).
3. **Corroboration** — non-Raman classical sources in the walled bands that already exist
   (classical corroborates, never overrides; Raman wins).

## Part 1 — The measured gap: what is already here and unencoded

The on-disk library holds **~110 source collections. Only 12 tags are live-citable.**
Encoded-rule density per live tag (cite-count in `app/raman_saab/`):

| tag | cites | reading |
|---|---|---|
| HTJAH-I / HTJAH-II | 540 / 294 | saturated — the engine's spine |
| HPA | 56 | mechanics mined; **HPA-20 named yogas ≈ 0 rule-cites** |
| 3HC | 48 | **~13% of the ~300 combinations encoded** — the largest pure-Raman rule frontier |
| MUHURTHA / PRASNA / VARSHA | 26 / 16 / 5 | walled subsystems, young |
| NH | 23 | used as a golden/attention source; **≈0 doctrine rules encoded** |
| ASP / GBB / AFB / JAIMINI | 12 / 10 / 8 / 12 | targeted use |

Correction to the roadmap's own note: NH is **not** missing — the full 34,742-line text sits at
`data/…/Notable Horoscopes BV Raman.txt` (it built the 31-chart attention benchmark). What is
missing is the *structured chapter split* the registry's loader expects (1 unsplit file).

**Raman-authored works ON DISK but UNREGISTERED (adoption is a registry entry away):**

| source dir | what it is | files |
|---|---|---|
| `prasna_marga_vol1` + `_vol2` | **Raman's own translation of Prasna Marga, with his notes** — his largest horary/remedial corpus, PRASNA-band ready | 21 |
| `manual_hindu_astrology_raman_1935` | his first book — casting mechanics, cross-checks HPA | 5 |
| `astrological_magazine_v75_raman` | one volume of his monthly readings | 3 |

## Part 2 — Raman works ABSENT from disk (the procurement list)

Verified against his full bibliography (Wikipedia/RRRF/publisher listings):

| work | why it matters | availability found |
|---|---|---|
| **My Experiences in Astrology** | autobiographical **casebook** — dozens of his own readings with outcomes, prime attention-benchmark material | in print (UBS); no free scan found |
| **A Catechism of Astrology** | Q&A format — his own **doctrine clarifications**, exactly the ambiguity-resolver Tier 4 of the roadmap wants | in print; no free scan found |
| **Bhavartha Ratnakara** (his translation) | lineage classical with **Raman's commentary** — commentary is citable-Raman | in print |
| Planetary Influences on Human Affairs | scientific-case essays; low rule yield | in print |
| Hindu Astrology and the West | positioning essays; low rule yield | in print |
| Astrology in Predicting Weather & Earthquakes | mundane astrology — out of current scope | in print |
| **The Astrological Magazine** (1895–2008; Raman editor 62 yrs from 1936) | **the largest untapped casebook of his attention and verdicts in existence** — decades of monthly worked charts | barely digitized: IAPSOP holds only 3 items (1906 almanac, 1953, 1959); BORI Library Pune reportedly holds soft copies; relaunched as The Astrological eMagazine (digital, post-2008) |

## Part 3 — Non-Raman sources, band-aware

**3a. The lineage shelf (highest value, already on disk, unregistered).** B. Suryanarain Rao —
Raman's grandfather and teacher, founder of the very magazine (1895). His works are the closest
non-Raman-authored sources to Raman's siddhanta that exist, and five collections are on disk:
`astro_self_instructor_row_1893` (15 files), `brihat_jataka_row_1919` (6), `sarvartha_
chintamani_row_1899` (2), `intro_astrology_row_1900` (1), `chappanna_prasana_sastra_row_1946`
(0 files — empty dir, needs re-import). Proposed: a new **LINEAGE band** between RAMAN_EXPLICIT
and CLASSICAL_NONCITABLE — corroborates with named provenance, never overrides, and where Rao
and Raman differ, Raman wins (he revised his grandfather deliberately).

**3b. Classical corroboration (band exists; coverage partial).** Already citable-in-band and on
disk with room to widen: BPHS (both vols), Uttara Kalamrita, Saravali, Phaladeepika (3
editions), Ashtakavarga of Patel, Laghu Parashari. On disk but unused: **Brihat Jataka**
(Varahamihira — the classical Raman himself cites most; his own grandfather's translation is
the on-disk edition), **Jataka Parijata**, **Sarvartha Chintamani**, **Hora Sara**, **Jataka
Tattva**, Sripatipaddhati (house mechanics), Daivajna Vallabha, Hora Ratnam. Adoption cost per
work is small (registry entry + rules as they earn their way in through the existing
synthesis-rule review gate).

**3c. Validation assets (never tuning).** Other authors' worked-chart casebooks usable for
NEW attention benchmarks (methodology already exists: admission by Lagna check, frozen splits):
Deva Keralam / Chandrakala Nadi vols (on disk), Saptarishi Nadi (on disk), K.N. Rao's Advanced
Techniques (on disk — modern, so validation-only, never doctrine). These grow n for benchmark
programmes without touching the golden set.

**3d. Computational primitives.** Swiss Ephemeris already at full precision; on-disk Surya
Siddhanta / Aryabhatiya / Indian Ephemeris (Swamikannu) serve historical-date cross-checks
(the pre-1906 fix made 19th-century charts renderable; these let panchanga claims be verified
against period almanacs like the on-disk 1906 Sharvari panchanga).

## Part 4 — Do NOT adopt (each violates a lock)

| source (on disk) | lock it violates |
|---|---|
| KP readers (3 collections) | non-Lahiri sub-lord chain — locked out (CLAUDE.md; "recorded, not encoded") |
| Lal Kitab (3 vols) | outside every admitted scope; no band exists that could take it |
| Systems Approach (Choudhry) | modern system contradicting Raman's; same class as KP |
| Nadi leaf collections *as doctrine* | unfalsifiable per-chart claims; usable ONLY as 3c validation charts, never rules |
| Any source *as ratchet fuel* | Measured Truth: the ceiling is closed; no source may be adopted to "improve accuracy" |

## Recommended sequence

1. **Register what is already here** (hours): Prasna Marga I–II → PRASNA band; Manual 1935 →
   live; the Rao shelf → new LINEAGE band; re-import the empty Chappanna Prasna dir.
2. **Split NH into chapters** (a day): the text exists; structure unlocks NH-cited rule
   encoding and widens the attention benchmark toward its full ~60-chart run.
3. **3HC completion** (the big one) — **CORRECTED 2026-08-08 by the inventory tool**
   (`tools/raman_saab/inventory_3hc.py` → `THREE_HUNDRED_INVENTORY.md`): both on-disk copies
   are the SAME truncated scan ending at combination 162, so the original "~260 on disk"
   claim was wrong. The honest arithmetic: **78 combinations parsed, on disk and unencoded**
   (the immediately-workable frontier), ~68 more present-but-OCR-mangled (manual-audit list in
   the inventory), and **138 (nos. 163-300) absent — a complete edition must be procured
   first**. Still the largest pure-Raman gain; half of it is a purchase, not a coding task.
4. **HPA-20 named yogas** (with 3HC — same registry).
5. **Procure the casebook**: My Experiences + Catechism (in print, cheap); the magazine archive
   is the long game — BORI Pune and the eMagazine successor are the leads found.
6. **Classical widening as needed**: Brihat Jataka first (Raman's own most-cited classical,
   in the grandfather's translation), then Jataka Parijata / Sarvartha Chintamani rows as
   synthesis rules earn them.

Every row above is coverage or corroboration. None touches a verdict, a threshold, or the
ratchet — by construction, since all of it lands in report-layer registries behind the
existing review gates.

*Sources: [Wikipedia — B.V. Raman](https://en.wikipedia.org/wiki/B._V._Raman) ·
[IAPSOP Astrological Magazine archive](http://iapsop.com/archive/materials/astrological_magazine_india/) ·
[RRRF](http://www.rrrf.in/raman.html) ·
[archive.org — Manual of Hindu Astrology 1935](https://archive.org/details/AManualOfHinduAstrologyBVRaman1935Edition) ·
[Goodreads author listing](https://www.goodreads.com/author/list/246583.B_V_Raman) ·
[astrolearn — The Astrological Magazine](https://www.astrolearn.com/astrology-bibliography/the-astrological-magazine/)*
