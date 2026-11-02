"""``app.kp`` — Krishnamurti Paddhati engine, encoded from K. S. Krishnamurti's KP Readers 1, 3-6.

A separate system from ``app.raman_saab`` and ``app.parashara``: it uses the Krishnamurti
ayanamsa and Placidus cusps because KP doctrine requires them, and restores swisseph's global
sidereal mode to Lahiri (the repo lock) after every cast. Nothing outside ``app.kp`` imports it.

Modules: ``subs`` (249 divisions), ``chart`` (cast), ``significators`` (A-D ladder, opt-in level E),
``ruling`` (ruling planets), ``dasa`` (Vimshottari), ``judgment`` (cusp sub-lord verdicts for
marriage, children, health, wealth, service and any house; stability; timing), ``events``
(17 cited event-timing rules), ``transit`` (Reader 5 transit reading and sensitive points),
``indications`` (59 one-line Reader 3/4 rules), ``descriptions`` (Reader 4 partner and
"love and life" tables, parsed from the library at run time), ``selection`` (Krishnamurti's
strong and fruitful significators and ruling-planet agreement, which narrow the timing),
``citations`` (verbatim quotes).
The walled ``horary`` package (Reader 6) holds the horary cast, judgment, the 35 printed
question rules, ruling-planet timing and ruling-planet birth-time correction. The walled
``later`` package holds 132 rules from KP books by authors after Krishnamurti, each labelled
with its author and book; nothing else in ``app.kp`` imports it.

Every choice the source leaves open is a named ruling in ``docs/kp/KP_RULINGS.md``. The engine
is a faithful instrument, not a validated predictor; see the ``docs/kp/KP_PREFLIGHT_*.md`` files.
"""
