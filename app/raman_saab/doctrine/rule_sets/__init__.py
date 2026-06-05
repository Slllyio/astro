"""Encoded RuleRecord sets, aggregated. Each `house_NN_*` module exposes a `RULES`
tuple; `ALL_RULES` concatenates them so judges can fire the whole corpus at once."""
from __future__ import annotations

from app.raman_saab.doctrine.rule_sets import (
    house_01_lagna, house_02_dhana, house_03_sahaja, house_04_sukha, house_05_putra,
    house_06_ari, house_07_kalatra, house_08_ayur, house_09_bhagya, house_10_karma,
    house_11_labha, house_12_vyaya)

_MODULES = (
    house_01_lagna, house_02_dhana, house_03_sahaja, house_04_sukha, house_05_putra,
    house_06_ari, house_07_kalatra, house_08_ayur, house_09_bhagya, house_10_karma,
    house_11_labha, house_12_vyaya)

ALL_RULES = tuple(rule for mod in _MODULES for rule in mod.RULES)
