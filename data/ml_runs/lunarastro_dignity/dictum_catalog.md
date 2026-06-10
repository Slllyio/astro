# Classical dictums for event timing — sourced catalogue

A working list of the classical rules (shlokas / principles) that astrologers
have used for **timing life events through Vimshottari dasha**, compiled by
domain with sources, and tagged for testability on this corpus (D1 signs+houses,
D9 planet signs, MD+AD windows, dated events). Where a principle is spread across
several texts I cite the tradition rather than invent a verse number.

Legend: ✅ encoded & tested · ◐ partially (data limits) · ✗ needs data we lack
(exact degrees / D9 lagna / transits).

---

## A. Marriage (Kalatra) — 7th house

| # | Dictum (paraphrase) | Source | Test |
|---|---|---|---|
| M1 | Marriage occurs in the Dasha–Antardasha of the **lord of the 7th**. | Phaladeepika 27; BPHS (Dasha-phala) | ✅ |
| M2 | …or of **Venus, the Kalatra-karaka**. | Brihat Jataka; Saravali | ✅ |
| M3 | …or of the lord of the **2nd** (family) and **11th** (fulfilment of desire). | Sarvartha Chintamani; Phaladeepika | ✅ |
| M4 | …or of a **planet placed in, or aspecting, the 7th**. | BPHS; Jataka Parijata | ✅ |
| M5 | …or of the **lord of the Navamsa occupied by the 7th-lord / by Venus**. | Uttara Kalamrita (Khanda 4) | ◐ (7L navamsa disp.; no D9 lagna) |
| M6 | A **strong 7th-lord / well-placed 7th** marries in time; the **7th-lord in 6/8/12** delays marriage. | Phaladeepika 9 | ✅ (marriage-age proxy) |
| M7 | **Mangal/Kuja Dosha** — Mars in 1,2,4,7,8,12 from Lagna (also from Moon, Venus) → discord, delay or break-up. | Mansagari; regional tradition | ✅ (vs divorce/relationship) |

## B. Profession (Karma) — 10th house

| # | Dictum | Source | Test |
|---|---|---|---|
| C1 | Career results manifest in the Dasha of the **10th-lord**, or a **planet in the 10th**. | BPHS; Phaladeepika 9 | ✅ |
| C2 | …or of the planet **aspecting the 10th**. | Brihat Jataka (Karma-jiva) | ✅ |
| C3 | …or of the **Karma-karakas Sun, Mercury, Jupiter, Saturn**. | BPHS | ✅ |
| C4 | **Raja-yoga**: a Kendra-lord + Trikona-lord in relation → rise in status during their Dasha. | BPHS (Raja-yoga adhyaya) | ◐ (lordship encodable; "relation" coarse) |

## C. Death / Longevity (Ayus) — 8th & Maraka houses

| # | Dictum | Source | Test |
|---|---|---|---|
| D1 | **Marakas** — the lords of the **2nd and 7th**, and planets placed therein, act as killers; death in their Dasha–Antardasha. | BPHS (Maraka adhyaya); Jataka Parijata | ✅ |
| D2 | …also the **8th-lord** and **malefics in maraka houses**. | Phaladeepika 26 | ✅ |
| D3 | **Saturn is Ayushkaraka**; its Dasha is critical for longevity. | BPHS; Saravali | ✅ |
| D4 | Lord of the **22nd Drekkana** from Lagna is a strong maraka. | BPHS | ✗ (needs Lagna degree) |
| D5 | Longevity bands (**Alpa/Madhya/Purna ayus**) from Lagna/8th/Saturn strength. | BPHS (Ayurdaya) | ◐ (coarse strength index) |

## D. Children (Santana) — 5th house

| # | Dictum | Source | Test |
|---|---|---|---|
| P1 | Progeny in the Dasha of the **5th-lord**, of **Jupiter (Putra-karaka)**, or of a **planet in the 5th**. | Phaladeepika 9; BPHS | ◐ (no "progeny" class; proxy via family/relationship) |

## E. Education (Vidya) — 4th & 5th

| # | Dictum | Source | Test |
|---|---|---|---|
| E1 | Education prospers in the Dasha of the **4th/5th-lord, Mercury (Vidya), or Jupiter (Jnana)**. | Phaladeepika; Sarvartha Chintamani | ✅ |

## F. Wealth (Dhana) — 2nd & 11th

| # | Dictum | Source | Test |
|---|---|---|---|
| W1 | **Dhana-yoga**: connection of the lords of 2,5,9,11 → wealth in their Dasha. | BPHS (Dhana-yoga); Phaladeepika | ◐ (career/finance proxy) |

---

## How these are tested ("the astrologer's way")

Classical practice is **disjunctive and multi-factor**: a jyotishi predicts the
event in the period of *any* of the prescribed significators, reading **MD or AD**
together. So for each event class we form the **union significator set** the
texts prescribe — house-lord(s) ∪ karaka(s) ∪ occupants ∪ aspectors ∪
navamsa-dispositor — and ask the practitioner's question:

> *In what fraction of real events was at least one prescribed significator
> running as Mahadasha or Antardasha?*

We report that **hit-rate** as an astrologer would quote it, alongside the
**chance/exposure expectation** (how often a set of that size would be running
anyway) so the number is interpretable — but we do **not** gate it behind a
permutation null. This is the system judged on its own conjunctive terms.

(Tested in `dasha_classical_dictums.py` → `classical_dictum_test.md`.)
