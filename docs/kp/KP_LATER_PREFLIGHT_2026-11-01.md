# Later-author KP rules: pre-flight on ordinary charts (2026-11-01)

Tool: `python -m tools.kp.later_rates --n 2000 --seed 20261101` (data:
`docs/kp/kp_later_rates_2026-11-01.json`). Same random births as the earlier KP pre-flights
(uniform 1940-2005, uniform time, 12 Indian cities). No outcome data was read. This measures
how often each rule fires and how often its answer changes when the birth time moves 5 minutes
either way. It says nothing about whether any rule is true.

| | |
|---|---|
| Rules | 132 (88 natal, 44 horary) from 8 later-author books |
| Natal rules firing on the median chart | 28 of 88 |
| Median fire rate per rule | 15% |
| Median ±5-minute flip rate per rule | 29% |
| Rules firing on over 80% of charts | 9 |
| Rules firing on 50-80% | 33 |
| Rules firing on 5-50% | 71 |
| Rules firing on under 5% | 19 |

The nine near-universal rules: the cricket-match rule (94%), "selling in a dignified way" (94%),
marriage via 2/7/11 counting conjunction (93%), "marriage stopped" (88%), 11th-cusp harmony (87%),
provident fund (87%), leaving a job (82%), a meeting possible (81%), recovery after an accident
(80%). A rule that holds for nearly everyone cannot tell one chart from another. One E-zine
author says so of their own health rule ("Lagna sub Lord signifies any one or more of 6 or 8 or
12 in almost all charts", EZN:p.81); it fires on 80% here.

Rules that ask for one named sub-lord, or for several houses at once, are rare and sensitive:
all 19 rules under 5% change answer with a 5-minute shift at least as often as they fire.

Wide "or" lists (LR2) are what make the common rules common. That is the authors' wording, not
an engine choice; the engine does not narrow them.
