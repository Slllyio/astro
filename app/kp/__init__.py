"""``app.kp`` — Krishnamurti Paddhati engine, encoded from K. S. Krishnamurti's KP Readers 1, 3-6.

A separate system from ``app.raman_saab`` and ``app.parashara``: it uses the Krishnamurti
ayanamsa and Placidus cusps because KP doctrine requires them, and restores swisseph's global
sidereal mode to Lahiri (the repo lock) after every cast. Nothing outside ``app.kp`` imports it.

Modules: ``subs`` (249 divisions), ``chart`` (cast), ``significators`` (A-D ladder),
``ruling`` (ruling planets), ``dasa`` (Vimshottari), ``judgment`` (cusp sub-lord verdicts for
marriage, children, health, wealth, service and any house; stability; timing), ``events``
(17 cited event-timing rules), ``transit`` (Reader 5 transit reading and sensitive points),
``citations`` (verbatim quotes). The walled ``horary`` package (Reader 6) holds the horary cast,
judgment, ruling-planet timing and ruling-planet birth-time correction.

Every choice the source leaves open is a named ruling in ``docs/kp/KP_RULINGS.md``. The engine
is a faithful instrument, not a validated predictor; see the ``docs/kp/KP_PREFLIGHT_*.md`` files.
"""
