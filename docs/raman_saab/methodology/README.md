# Raman Saab — Methodology Corpus

Canonical, citation-backed extraction of **B.V. Raman's *How to Judge a Horoscope*
(Vols I & II)**, the reference the `app/raman_saab/` engine is built against.
Every rule and example traces to a real line in the on-disk Raman corpus
(`data/knowledge_library/sources/how_to_judge_a_horoscope_raman/` = Vol I,
`how_to_judge_horoscope_raman2/` = Vol II). Citation tags: `HTJAH-I:<line>`,
`HTJAH-II:<line>`, `HPA-<ch>:<line>`, `GBB-<ch>:<line>`.

## Read order

1. **[00_method_overview.md](00_method_overview.md)** — the chart-wide method: macro
   sequence, the 3×3×3 unit of judgment, the 8 considerations, functional
   benefic/malefic per Lagna, Yoga Karakas, the timing model, the **full
   longevity sub-engine** (span classes, maraka, Pindayu & Amsayu arithmetic),
   and the doctrine divergences locked to Raman.
2. The twelve house files below — one per bhava, each self-contained.

## Per-house files

| House | File | Sanskrit | Karaka(s) | Special varga (per Raman) | Rules | Example charts |
|---|---|---|---|---|---|---|
| 1 | [house_01_lagna.md](house_01_lagna.md) | Tanu / Lagna | Sun (+ Lagna) | D1 + D9 | 67 | 8–37 (30) |
| 2 | [house_02_dhana.md](house_02_dhana.md) | Dhana | Jupiter (speech: Mercury) · **maraka** | D2 Hora + D9 | 68 | 38–51 (14) |
| 3 | [house_03_sahaja.md](house_03_sahaja.md) | Sahaja / Bhratru | Mars | D3 Drekkana + D9 | 30 | 52–63 (12) |
| 4 | [house_04_sukha.md](house_04_sukha.md) | Sukha / Matru | Moon·Mercury·Venus·Mars | D9 (Raman); D4/D12/D24 implied | 51 | 64–87 (24) |
| 5 | [house_05_putra.md](house_05_putra.md) | Putra / Suta | Jupiter | D9 + Beeja/Kshetra; D7 implied | 37 | 88–108 (21) |
| 6 | [house_06_ari.md](house_06_ari.md) | Ari / Roga / Rina | Mars & Saturn | D1+6/8/12 + D9; D3 (appendix) | 27 | 109–123 (15) |
| 7 | [house_07_kalatra.md](house_07_kalatra.md) | Kalatra / Yuvati | Venus · **maraka** | D9 (spouse); D7 (progeny) | 90 | 1–32 (32) |
| 8 | [house_08_ayur.md](house_08_ayur.md) | Ayur / Randhra | Saturn | longevity calc; 22nd-Drekkana, 64th-Navamsa | 32 | 33–84 (52) |
| 9 | [house_09_bhagya.md](house_09_bhagya.md) | Bhagya / Dharma / Pitru | Jupiter (dharma) · Sun (father) | D9 (Raman); D12 not invoked | 48 | 85–113 (29) |
| 10 | [house_10_karma.md](house_10_karma.md) | Karma / Rajya | Sun·Mercury·Jupiter·Saturn | D10 Dasamsa overlay on D9 | 59 | 114–208 (95) |
| 11 | [house_11_labha.md](house_11_labha.md) | Labha / Aya | Jupiter (gains) · Mars (elder sib) | D9 only | 54 | 209–232 (24) |
| 12 | [house_12_vyaya.md](house_12_vyaya.md) | Vyaya / Moksha | Saturn (loss) · Ketu (moksha) | D9 overlay; D12 not separately used | 64 | 233–258 (26) |

**Totals: 700+ cited rule-records, ~374 worked example charts** (after the audit gap-fill
pass — see Status below). Vol I and Vol II restart chart numbering, so the two ranges
overlap by number.

## Per-house file structure (shared template)

Front-matter (`house`, `sanskrit`, `karaka`, `special_varga`, `source`), then:
**Significations → Three Pillars → Main Considerations → Lord-of-N-in-the-12-houses
(fortified/afflicted) → Important Combinations (rule records) → Planets-in-the-house →
Timing of Fructification → Nature of Results (dasha-phala) → Example-Chart Insights →
Engine Notes.** Rule records carry a **reference frame** ∈ {Lagna, Moon, Karaka}.

## Cross-cutting techniques surfaced by the readers (beyond the basic template)

These recur across houses and must be first-class in the engine — several were **not**
in the first design draft and were discovered by reading every chapter:

- **Bhava ≠ Rashi, enforced**: a planet late/early in a sign falls into the adjacent
  *bhava* (e.g. H1 Chart 17: "Ketu in Lagna" is actually 12th-bhava). Chalita is mandatory.
- **Conjunction needs an orb gate**: H1 treats Sun ~18° from Saturn as *unconjoined* — a
  circular-orb gate (`min(diff,360−diff)`) decides conjunction, not mere sign-sharing.
- **Karaka-as-Lagna + Maraka-from-Karaka** generalizes: marriage read *from Venus* (H7),
  father-longevity *from Sun* (H9), mother-longevity *from the Moon/4th as Lagna* (H4).
- **Dusthana inversion & Vipareeta**: malefics in the 6th can *protect* (H6); 6/8/12 lords
  in dusthanas can *enrich* (Vipareeta Raja Yoga).
- **Bhanga/cancellation gates run before scoring**: neecha-bhanga, subha/papa-kartari
  (hemming, positionally **asymmetric**), parivartana — evaluate these first (H2, H5, H7, H9).
- **Sub-engine pre-passes**: Beeja/Kshetra-sphuta fertility before judging children (H5);
  the longevity sub-engine before any house (overview §8); Special Dhana Lagna for wealth (H2).
- **Sensitive points**: Mandi/Gulika (H5, H6, H12), 22nd-Drekkana & 64th-Navamsa death
  points (H8), Bandhana-yoga for confinement (H12).
- **Counting via Navamsa**: number of siblings/children/co-borns derived from D9, not D1
  (H3, H5, H11).
- **Polarity inversions**: Bhavartha-Ratnakara — karaka-in-12-from-Lagna *helps* its own
  matter (H12); 8th-lord in 6/8/12-of-Navamsa *mitigates* while kendra/trikona *aggravates* (H8).
- **Named historical charts** as externally-verifiable golden tests: Gandhi, Hitler, JFK,
  Lincoln, Napoleon, Nehru, Indira Gandhi, George VI, Elizabeth II, Subhas Bose, Tippu
  Sultan, Bhutto, Hyder Ali, Krishnaraja Wadiyar IV (H8, H10).

## Provenance & verification

Each house file was extracted by an independent reader, then **independently audited** for
fidelity (mis-citations, wrong example-chart verdicts, hallucinations) and completeness
(dropped rules) against the source chapter. All files passed fidelity; the audit-flagged
completeness gaps were then **gap-filled** (e.g. House 6's disease-diagnosis tables, House 8's
30 cause-of-death combinations, House 7's Kuja-Dosha numeric grid + synastry block, House 12's
Eyes/Vision rule-group, House 2's Drekkana financial table) and two citation line-errors in
House 9 were corrected. The longevity arithmetic was independently recomputed and verified.

`_derived/` holds **unaudited, agent-generated engine-design drafts** — not doctrine; see
`_derived/README.md`. The source of truth is this folder's `00_method_overview.md` + the 12
`house_*.md` files.

## Status & caveats

- OCR source: a few example charts lack a printed "Balance of Dasha" line; some rasi grids
  are OCR-mangled — the **prose** (House → Lord → Karaka → from-Moon → Conclusion) is the
  reliable layer, not the diagrams. Flagged inline per chart where relevant.
- The "special varga" column records **what Raman actually invokes in that chapter** (mostly
  D1 + D9), which sometimes differs from the conventional varga card — noted per file so the
  engine doesn't fabricate divisional logic Raman didn't use.
