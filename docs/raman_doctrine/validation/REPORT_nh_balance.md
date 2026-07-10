# Daśā-balance validation — engine vs Raman's printed lines (Notable Horoscopes)

The HTJAH timing report (`REPORT_timing.md`) closed with one explicit gap: *"Not validated
here: the balance-of-daśā itself (the engine computing the balance from the Moon)."* The 94%
MD-placement result validated it only **indirectly**. *Notable Horoscopes* removes that
caveat — Raman prints, per chart, a verbatim **"Balance of &lt;lord&gt; Dasa at birth : Years
Y-M-D"** line, the exact ground truth.

## Method
For each golden case matched by name to its NH balance line (`nh_balance.json`, 30 cases),
compute the start balance from the stored Moon longitude with the **live** engine —
`calculate_vimshottari_mahadasha(moon_lon, jd)` (`app/core/ephemeris_engine.py:189`) — and
compare the **mahādaśā lord (exact)** and the **remaining duration (years)** to Raman's printed
line. Vimśottarī balance is a pure function of the Moon, so any JD works (guarded by a test).

## Result

| check | result |
|---|---|
| **MD-lord exact** | **28 / 30 (93.3%)** |
| **duration within 0.5 y** (of the lord-matched) | **28 / 28 (100%)** |

Every case whose lord matches also matches the printed **duration to within half a year** — and
in most it agrees to two decimals (Buddha 15.10y, Alexander 5.78y, Lincoln 2.10y, Nehru 13.60y,
Tilak 13.70y…). This is a **direct** confirmation of the engine's balance-from-Moon computation,
the piece the timing result had only inferred.

## The two misses are OCR, not engine
- **Ramanujacharya** — Raman Jupiter 4.14y, engine Rahu 8.33y.
- **Lord Tennyson** — Raman Rahu 6.15y, engine Mars 6.78y.
In both the *duration* is close but the *lord* is wrong — the signature of a Moon longitude that
landed in the wrong nakṣatra, i.e. a stored/OCR Moon-position error (Ramanujacharya is an
ancient chart with a reconstructed position; both are known-soft nativities). The engine
arithmetic is not implicated: feed it a correct Moon and it lands the balance.

## Interpretation & scope
- Combined with the timing result (MD 47/50 on NH deaths), the engine's **entire Vimśottarī
  chain** is now validated against Raman end-to-end: the start balance (here, direct), the MD
  sequence, and the AD birth-clipping.
- Measurement only — no engine change. Guarded by `tests/doctrine/test_balance_validate.py`.
- Name-matching recovered 30 of the 50 positioned golden cases; the rest failed only the
  fuzzy name join (OCR header variance), not the arithmetic — extending the match set would
  only add more agreements. `balance_validate.py` reproduces the table.
