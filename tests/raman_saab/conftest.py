"""Pytest config local to the Raman Saab test suite.

Registers custom markers so they don't warn as unknown. Hierarchical conftest:
this is merged with the repo-level tests/conftest.py, so both pytest_configure
hooks run — no need to touch the shared file.

Also provides `section_text`, the order-independent way to isolate one report section.
"""
from __future__ import annotations

import pytest

from app.raman_saab.detailed_report import HTML_SECTION_ORDER, SECTION_CONTRACT


def _section_text(rendered: str, section_id: str, *, html: bool = False) -> str:
    """The text of ONE report section — from its marker to whichever section follows it.

    Tests used to slice to a hardcoded neighbour (`markdown[your_reading : information_content]`,
    `body[ruler : now]`). That silently encodes the document ORDER into assertions about
    CONTENT, so the v33 re-sequencing broke nine tests that were not actually about order — and
    broke them confusingly, because a neighbour that moves ahead yields an empty slice and the
    assertion then fails against "".

    Deriving the neighbour from the contract keeps content assertions about content. Assertions
    that genuinely concern order belong in test_report_template_contract.py, which pins the
    sequence in one reviewed place.
    """
    markers = {s.section_id: (s.html_marker if html else s.md_marker) for s in SECTION_CONTRACT}
    order = [sid for sid in (HTML_SECTION_ORDER if html
                             else [s.section_id for s in SECTION_CONTRACT]) if markers[sid]]
    i = order.index(section_id)
    start = rendered.index(markers[section_id])
    end = (rendered.index(markers[order[i + 1]]) if i + 1 < len(order) else len(rendered))
    assert end > start, f"{section_id!r} slice is empty — the marker order is inconsistent"
    return rendered[start:end]


@pytest.fixture(scope="session")
def section_text():
    """`section_text(rendered, section_id, html=False)` — see :func:`_section_text`.

    Exposed as a fixture rather than an import because `tests/` is not a package.
    """
    return _section_text


def pytest_configure(config) -> None:
    config.addinivalue_line(
        "markers",
        "external_pin: test pinned to an external reference (drikpanchang.com / "
        "Jagannatha Hora); no-ops until the expected value is filled in.",
    )
