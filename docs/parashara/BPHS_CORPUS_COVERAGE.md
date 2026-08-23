# BPHS corpus coverage — R. Santhanam translation (archive.org `BPHSEnglish`)

**91 of 97 chapters** present as clean per-chapter files (`data/knowledge_library/sources/bphs/chapter_NNN_*.md`). Vol I ch.1-45 **complete**; Vol II ch.46-97 has 46 of 52.

Regenerate: `python -m app.medini.etl.import_archive_text --bundle classical_jyotisha` (both BPHS volumes are in the bundle; chapter numbering is continuous, so `BPHS-46:…` resolves the same way as `BPHS-7:…`).

## Missing chapters (6)

| Ch | TOC title | Why |
|---|---|---|
| 54 | Effects of the Antardasas in the Dasa of the Moon | heading present, **title line lost in the scan** |
| 65 | Effects of Dasas of Rasis in Aries Amsa | heading present, title line lost |
| 81 | (female horoscopy cont.) | heading present, title line lost |
| 83 | (moles/marks cont.) | heading present, title line lost |
| 94 | Remedies from Evil Effects of Birth in Jyeshta | heading present, title line lost |

These five have a surviving `Chapter N` marker but no legible title line, so the two-line heading shape cannot anchor them; their text is absorbed into the preceding chapter. They are **antardasa result-tables and remedial chapters** — none carries a dasha *system* definition or a computational rule. Recovering them needs a TOC-page-number anchor, which is deferred until a citation actually lands in one.

**Ch.75 (Panchamahapurusha) was recovered 2026-08-23** — its text had been absorbed into the ch.74 (Sudarshana) file; when the Mahapurusha doctrine needed a root citation it was split out to `chapter_075_*.md` (both the definition and all five effect descriptions are legible). Because the corpus is gitignored (provisioned per machine), the split is committed as the idempotent, content-keyed repair `tools/parashara/repair_corpus_ch75.py` — **run it once after provisioning the BPHS corpus** so `BPHS-75` resolves. This is the pattern for the five above: split on demand, when a citation lands.

## Present chapters

| Ch | Title | Size | ASCII |
|---|---|---|---|
| 1 | The Creation | 6K | 100% |
| 2 | Great Incarnations (Of The Lord) | 3K | 100% |
| 3 | Planetary Characters And | 36K | 99% |
| 4 | Zodiacal signs Described | 23K | 100% |
| 5 | Special Ascendants | 9K | 100% |
| 6 | The Sixteen Divisions Of A Sign | 32K | 99% |
| 7 | Divisional Consideration | 21K | 100% |
| 8 | Aspects Of The Signs | 4K | 100% |
| 9 | Evils At Birth | 14K | 100% |
| 10 | Antidotes For Evils | 3K | 100% |
| 11 | Judgement of Houses | 9K | 100% |
| 12 | Effects Of First House | 8K | 100% |
| 13 | Effects of Second House | 8K | 100% |
| 14 | Effects Of The Third House | 8K | 100% |
| 15 | Effects Of The Fourth House | 4K | 100% |
| 16 | Effects Of The Fifth House | 10K | 100% |
| 17 | Effects Of The Sixth House | 14K | 100% |
| 18 | Effects Of The Seventh House | 13K | 100% |
| 19 | Effects Of The Eighth House | 5K | 100% |
| 20 | Effects Of The Ninth House | 8K | 100% |
| 21 | Effects of The Tenth Mouse | 7K | 100% |
| 22 | Effects Of The Eleventh House | 3K | 99% |
| 23 | Effects Of The Twelfth House | 4K | 99% |
| 24 | Effects Of The Bhava Lords | 70K | 100% |
| 25 | Effects Of Non -Luminous Planets | 24K | 100% |
| 26 | Evaluation of Planetary Aspects | 15K | 100% |
| 27 | Evaluation Of Strengths | 37K | 100% |
| 28 | Ishta And Kashta Balas | 5K | 100% |
| 29 | Bhava Padas | 14K | 100% |
| 30 | Upa Pada | 11K | 100% |
| 31 | Argala Or Planetary Intervention | 9K | 99% |
| 32 | Planetary Karakatwas | 13K | 100% |
| 33 | Effects Of Karakamsa | 21K | 100% |
| 34 | Yoga Karakas | 31K | 100% |
| 35 | Nabhasa Yogas | 11K | 100% |
| 36 | Many Other Yogas | 26K | 100% |
| 37 | Lunar Yogas | 2K | 100% |
| 38 | Solar Yogas | 1K | 99% |
| 39 | Raja Yogas | 18K | 100% |
| 40 | Yogas For Royal Association | 4K | 100% |
| 41 | Combinations For Wealth | 17K | 100% |
| 42 | Combinations For Penury | 4K | 100% |
| 43 | Longevity | 37K | 100% |
| 44 | Maraka (Killer) Planets | 13K | 100% |
| 45 | Avasthas Of Planets | 58K | 100% |
| 46 | Dasas (Periods) of Planets | 94K | 99% |
| 47 | Effects of Dasas | 19K | 100% |
| 48 | Distinctive Effects of the Nakshatra | 8K | 100% |
| 49 | Effects of the Kalachakra Dasa | 10K | 99% |
| 50 | Effects of the Chara etc, Dasas | 20K | 99% |
| 51 | Working out of Antardasas (sub- | 12K | 100% |
| 52 | Effects of the Antardasas in the | 16K | 100% |
| 53 | Effects of the Antardasas in the | 31K | 100% |
| 55 | Effects in the Antardasas of Rahu | 17K | 100% |
| 56 | Effects of the Antardasas of Jupiter | 17K | 99% |
| 57 | Effects of the Antardasas in the | 17K | 100% |
| 58 | Effects of the Antardasas in the | 15K | 100% |
| 59 | Effects of the Antardasas in the | 16K | 100% |
| 60 | Effects of the Antardasas in the | 29K | 99% |
| 61 | Pratyantar Dasas In the Antardasa of Ketu | 14K | 99% |
| 62 | Effects of the Sookshmantar Dasas | 16K | 99% |
| 63 | Effects of Prana Dasas in | 15K | 99% |
| 64 | Effects of Antardasas in the | 45K | 99% |
| 66 | Ashtakavarga | 29K | 100% |
| 67 | Rekh a 'Chakra of Sun's Ash taka varga | 5K | 100% |
| 68 | Ekadhipatya Shodhana in the | 4K | 100% |
| 69 | Pinda Sadhana in the Ashtakavarga | 3K | 100% |
| 70 | Effects of the Ashtakavarga | 19K | 100% |
| 71 | Determination of Longevity Through | 2K | 99% |
| 72 | Aggregrhtional Ashtakavarga | 12K | 100% |
| 73 | Effects of the Rays of the Planents | 9K | 100% |
| 74 | Effects of the Sudarshana Chakra | 18K | 100% |
| 75 | Characteristic Features of Panchamahapurushas | 3K | 100% |
| 76 | Effects of the Five Elements — Earth, | 5K | 100% |
| 77 | Effects of the Satwa Guna etc | 6K | 100% |
| 78 | Lost Horoscopy | 20K | 100% |
| 79 | Yogas Leading to Ascetism | 6K | 100% |
| 80 | Female Horoscopy | 38K | 100% |
| 82 | Effects of Moles, Marks, Signs etc., | 27K | 99% |
| 84 | Remedial measures to obtain relief | 6K | 100% |
| 85 | Inauspicious Births | 1K | 99% |
| 86 | Remedial Measures for Birth on | 2K | 99% |
| 87 | Remedies from the Evil Effects | 3K | 99% |
| 88 | Remedies from evil Effects of birth | 1K | 99% |
| 89 | Remedies from Nakshatra Birth | 2K | 99% |
| 90 | Remedies from Sankranti Birth | 4K | 99% |
| 91 | Remedies from Birth in | 3K | 99% |
| 92 | Remedies from Birth in | 3K | 100% |
| 93 | Remedies from Birth in | 7K | 99% |
| 95 | Remedies from Effects of Birth of | 2K | 100% |
| 96 | Remedies from Evil Effects | 3K | 99% |
| 97 | Iras) can understand this Hora Shatra. Only that person who | 2K | 99% |
