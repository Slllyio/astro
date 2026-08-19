# Doctrine engine — worked examples

## `chart_report.py` — full HTML reading of a chart

Casts a chart from printed positions, runs `judge_chart_doctrine`, and renders a
self-contained HTML page: the Rāśi (D1) + Navāṁśa (D9) South-Indian squares, the
12-house verdict matrix (colour-coded on the 9-grade scale), each house's scored
testimony *and* every applicable encoded sūtra that fired (verbatim, cited), plus the
chart-wide combinations (yogas, balas, avasthās).

```
PYTHONPATH=. python3 docs/raman_doctrine/examples/chart_report.py > /tmp/mainpuri.html
```

Ships with the **Mainpuri kundalī** (Scorpio lagna) — the chart used in PR #10's review
thread. Swap the `MAINPURI` dict for any `{positions, lagna, jd}` to report another
nativity. The output is the live engine, so it reflects the current increments:

- **21** — full natal firing (every applicable natal sūtra surfaces, 114/114 on Mainpuri);
- **22** — natal-scope filter (no horary *Prāśna* / electional *Muhūrta* / past-life rule
  fires on a birth chart);
- **23** — Kemadruma-bhaṅga (a cancelled yoga no longer surfaces).

**Honest scope.** The quoted sūtras and the reading are the strong product. The numeric
grades are the best *linear* fit to Raman's own printed verdicts (~54.7% within-one
held-out, vs a ~33% base rate) — a weak-but-real triage signal, not holistic synthesis.
The engine sums testimony where Raman weighs it; that additive ceiling is documented in
`../HOUSE_SCHEME_AUDIT.md` (increments 8/12/13/18/20) and `../VALIDATION_SUMMARY.md`.
