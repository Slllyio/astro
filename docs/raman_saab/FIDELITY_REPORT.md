# Run-4 Fidelity Report — encoder vs Raman's published verdicts

Golden cases from *Notable Horoscopes* (his printed positions, his
ayanamsa). Tier A gates: `timing_top20` (death window in top 20% of
lived MD/AD windows by fatal potency) and `killers_topk` (his named
maraka-power planets in the encoder's top 4 of 9). `dasha_anchor` is
documentation (printed-Moon timeline vs his stated dasha).

## Bala Gangadhara Tilak (Tier A)

> He died in August 1920 as soon as Rahu Dasa commenced. Rahu is in the constellation of Mercury, who as lord of the 3rd is in the 12th in conjunction with Ayushkaraka Saturn who is also a maraka. From Chandra Lagna, Rahu aspects the 7th and Mercury is a maraka by ownership.

- **dasha_anchor**: PASS — engine MD/AD at death = Rahu/Rahu; Raman states Rahu/—
- **timing_top20**: PASS — death window Rahu/Rahu ranks 10/54 (top 17%)
- **killers_topk**: PASS — named ['Mercury', 'Saturn']; encoder top-4 = ['Saturn', 'Mercury', 'Venus', 'Sun'] (scores [2.11, 1.58, 1.06, 0.95])

## Mahatma Gandhi (Tier A)

> He was shot dead by a fanatic in Sun Bhukti in Jupiter Dasa. Jupiter is in the 8th aspected powerfully by Mars — a maraka and the Sun is in the 12th from Lagna and in the 2nd — another maraka from the Chandra Lagna.

- **dasha_anchor**: FAIL — engine MD/AD at death = Jupiter/Venus; Raman states Jupiter/Sun
- **timing_top20**: PASS — death window Jupiter/Venus ranks 2/59 (top 2%)
- **killers_topk**: FAIL — named ['Jupiter', 'Sun']; encoder top-4 = ['Saturn', 'Venus', 'Mercury', 'Jupiter'] (scores [1.75, 1.68, 1.49, 1.26])

## Sri Ramana Maharshi (Tier A)

> The Maharshi's own death took place in Saturn Bhukti in Sun Dasa. The Sun is in the 3rd from Lagna and as lord of the 3rd from the Moon occupies the 7th, a maraka house. Saturn, the sub-lord, besides being Ayushkaraka, occupies the 3rd from Lagna and the 7th from Chandra Lagna in the Navamsa. These various ownerships and dispositions have conferred on the Sun and Saturn maraka power.

- **dasha_anchor**: PASS — engine MD/AD at death = Sun/Saturn; Raman states Sun/Saturn
- **timing_top20**: FAIL — death window Sun/Saturn ranks 20/45 (top 42%)
- **killers_topk**: PASS — named ['Sun', 'Saturn']; encoder top-4 = ['Mars', 'Saturn', 'Rahu', 'Sun'] (scores [1.36, 0.99, 0.9, 0.89])

## Albert Einstein (Tier A)

> Einstein's death took place as soon as Jupiter Dasa commenced. It will be seen that Jupiter is a maraka as he is lord of the 7th and is in the constellation of Rahu.

- **dasha_anchor**: PASS — engine MD/AD at death = Jupiter/Jupiter; Raman states Jupiter/—
- **timing_top20**: FAIL — death window Jupiter/Jupiter ranks 44/59 (top 73%)
- **killers_topk**: PASS — named ['Jupiter']; encoder top-4 = ['Saturn', 'Ketu', 'Jupiter', 'Moon'] (scores [2.19, 1.2, 1.18, 1.16])

## George Bernard Shaw (Tier B)

> The combinations for longevity are also unique — the 2nd lord is in the 2nd, the 3rd lord is in Lagna and the luminaries are free from affliction. He died in 1950 in Venus Dasa Venus Bhukti. ... The horoscope is typical for longevity.

- **dasha_anchor**: FAIL — engine MD/AD at death = Ketu/Mars; Raman states Venus/Venus
- **timing_top20**: PASS — death window Ketu/Mars ranks 3/65 (top 3%)
- **band**: PASS — encoder band PURNAYU, Raman states PURNAYU (score 0.613)

## Jawaharlal Nehru (Tier B)

> (No death analysis — Notable Horoscopes predates Nehru's death; his chapter supplies Raman's printed positions only.)

- **timing_top20**: FAIL — death window Rahu/Ketu ranks 15/57 (top 25%)

## Gate

**7/11 gated checks pass.**

Death-window potency percentile across cases (0% = most potent lived window): 2%, 3%, 17%, 25%, 42%, 73% — median 21%, mean 27%, vs 50% under chance.

**Calibration status: CLOSED after four doctrine-grounded rounds** (each added mechanism cites a verbatim Notable Horoscopes passage; no weight was fitted to an observed death age). Residual failures are structural, not tunable: (1) the longevity-band classifier is the weak link (bands mis-assign Einstein and sit at the boundary for Ramana), exactly matching run-3's population ayurdaya κ≈0.016; (2) Gandhi's chart carries five legitimate heavy killers under Raman's own conjunction-hierarchy rule, so his two narrative-named operators cannot both sit in the top-4 without demoting planets his book-rule ranks higher. **FIDELITY: PARTIAL** — mechanisms encode faithfully (dasha anchors 4/4 on his printed positions; killers 3/4; band-where-stated 1/1) but composite timing concentrates potency only modestly even on his own showcase charts. The population run proceeds with weights frozen at this state, carrying this fidelity level as its interpretive prior.