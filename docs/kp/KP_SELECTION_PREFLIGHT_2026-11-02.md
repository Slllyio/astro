# Significator selection (R24-R26): pre-flight on ordinary charts (2026-11-02)

Tool: `python -m tools.kp.selection_rates --n 2000 --seed 20261102` (data:
`docs/kp/kp_selection_rates_2026-11-02.json`). Random births as in the earlier KP pre-flights.
No outcome data was read. This measures how much of ages 20-40 the candidate periods cover
before and after Krishnamurti's selection steps. Narrower is not more correct: whether the
narrowed windows hit real events is untested.

Moment of judgment for R26: the native's 25th birthday at birth time and place, and again one
day later.

| Matter | R17 all significators | R25 fruitful | R26 + ruling planets | R26 leaves no window | R26 set changes next day |
|---|---|---|---|---|---|
| Marriage | 53% (mean 52%) | 27% (38%) | 2% (9%) | 41% of charts | 81% |
| Children | 51% (52%) | 27% (38%) | 2% (9%) | 41% | 81% |
| Service | 64% (59%) | 39% (46%) | 4% (10%) | 35% | 85% |

Figures are medians of the share of ages 20-40 covered (means in brackets).

What this shows:

- **R25 halves the windows.** That is the sub-lord test Krishnamurti states as elimination. It
  depends only on the birth chart.
- **R26 narrows sharply, but the narrowing comes from the moment of asking.** Ask one day later
  and the selected planets change for about four charts in five. For two in five charts no
  window is left in twenty years. This is his method ("ruling planets at the moment of
  judgement must agree"), and it is why the engine applies it only when a moment of judgment is
  given and reports it separately.
- Neither step is tested against real lives. A real test needs dated events, judged blind,
  against a shuffled-chart baseline.
