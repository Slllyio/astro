"""Walled layer: KP rules by authors who wrote after K. S. Krishnamurti.

The user chose (2026-11-01) to encode the later KP books as a separate, labelled
layer. Nothing in ``app.kp`` outside this package imports it, so Krishnamurti's
own verdicts never depend on it (tested). Every result names its author and book,
quotes the page, and carries the framing "A later author's rule, not
Krishnamurti's; ... not a validated prediction." Rulings LR1-LR7 in
``docs/kp/KP_RULINGS.md`` record how the authors' wording is read.

Modules: :mod:`sources` (the books), :mod:`citations` (verbatim quotes),
:mod:`registry` (the rules), :mod:`rules` (the evaluator), :mod:`gulbarga`
(the Gulbarga horary yes/no rule).

Usage:
    from app.kp.later.rules import later_indications
    from app.kp.later.gulbarga import gulbarga
"""
