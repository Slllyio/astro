"""Practitioner extended yoga detectors — fortune yogas beyond core BPHS set.

Doctrine source: BPHS Ch.40 (Adhi, Lakshmi) + Phaladeepika (Saraswati,
Daridra, Chamara) — classical "fortune" yogas that augment the core
yoga catalogue already detected by :mod:`app.core.yogas`.

This sub-package decomposes the extended-yoga detectors into one module
per yoga, each emitting Findings with a stable id pattern
``practitioner.yogas_extended.<name>.<variant>``.

Sub-modules (each ~80-120 LOC, RED-GREEN-COMMIT discipline):

- :mod:`adhi`       — BPHS Ch.40 Adhi Yoga (Maha/Madhya/Alpa variants)
- :mod:`lakshmi`    — BPHS Ch.40 Lakshmi Yoga
- :mod:`saraswati`  — Phaladeepika Saraswati Yoga
- :mod:`daridra`    — Phaladeepika Daridra Yoga (poverty indicator)
- :mod:`chamara`    — Phaladeepika Chamara Yoga (regal yoga)

The unified ``detect_yogas`` entry point that aggregates these into a
single dict envelope will be populated by sub-wave 3e2.
"""
from __future__ import annotations
