"""Platform-wide citation guard — no Parashara citation may resolve to frontmatter or empty text.

The 2026-08-22 audit found `bhava_prosperity` citing sloka NUMBERS as line numbers, landing in YAML
frontmatter: `verify()` passed (the line existed) but the "source" was `topics:`. This walks EVERY
module-level `Citation` across the parashara engine and asserts each resolves to real doctrine text,
so that subtle failure cannot reappear in any future module unnoticed.
"""
from __future__ import annotations

import importlib
import pkgutil
from typing import Iterator

import app.parashara as parashara_pkg
from app.parashara.doctrine.sources import Citation, passage, verify

_FRONTMATTER_MARKERS = ("topics:", "classical_refs:", "content_type:", "scraped_at:", "source_url:")


def _all_citations() -> Iterator[tuple[str, str, Citation]]:
    """Every Citation reachable as a module-level constant (scalar, in a dict, or in a tuple/list)
    across app.parashara.*."""
    for mod_info in pkgutil.walk_packages(parashara_pkg.__path__, parashara_pkg.__name__ + "."):
        mod = importlib.import_module(mod_info.name)
        for attr in dir(mod):
            val = getattr(mod, attr)
            if isinstance(val, Citation):
                yield mod_info.name, attr, val
            elif isinstance(val, dict):
                for k, v in val.items():
                    if isinstance(v, Citation):
                        yield mod_info.name, f"{attr}[{k!r}]", v
            elif isinstance(val, (tuple, list)):
                for i, v in enumerate(val):
                    if isinstance(v, Citation):
                        yield mod_info.name, f"{attr}[{i}]", v


def test_some_citations_were_found():
    """Guard the guard — if the walk finds nothing, the test is vacuous."""
    assert sum(1 for _ in _all_citations()) >= 15


def test_every_citation_resolves_to_real_doctrine():
    bad: list[str] = []
    for mod, name, cit in _all_citations():
        where = f"{mod}.{name} -> {cit.work}:{cit.line}"
        if not verify(cit):
            bad.append(f"{where} (does not resolve)")
            continue
        p = passage(f"{cit.work}:{cit.line}")
        text = (p or {}).get("text", "").strip().lower()
        if not text:
            bad.append(f"{where} (empty line)")
        elif any(m in text for m in _FRONTMATTER_MARKERS):
            bad.append(f"{where} (frontmatter: {text[:40]!r})")
    assert not bad, "citations pointing at non-doctrine:\n" + "\n".join(bad)
