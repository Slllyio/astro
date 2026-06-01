"""Lazy-import discipline: importing the V1.5 query layer must NOT pull in
``sentence_transformers`` or ``torch`` at module-import time.

The RAG retrieval call is the only path that can legitimately load those
modules, and the engine wraps every such call in a lazy-import-inside-
function-body block (see ``engine._retrieve_passages`` and the V1.0
contract documented in ``rag_citations.py``).

This regression test would catch an accidental top-level ``from
app.medini.services.knowledge_search import ...`` in any query-layer
module — a refactor that would re-introduce the ~200-600ms cold-start
cost the V1.0 lockfile defines away.
"""
from __future__ import annotations

import subprocess
import sys


def test_importing_query_does_not_load_sentence_transformers() -> None:
    """``import app.reading.query`` must NOT pull sentence_transformers."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import app.reading.query; "
                "print('sentence_transformers_loaded:', "
                "'sentence_transformers' in sys.modules)"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert "sentence_transformers_loaded: False" in result.stdout, (
        f"sentence_transformers leaked into top-level import. "
        f"stdout={result.stdout[-500:]} stderr={result.stderr[-500:]}"
    )


def test_importing_query_does_not_load_torch() -> None:
    """``import app.reading.query`` must NOT pull torch."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import app.reading.query; "
                "print('torch_loaded:', 'torch' in sys.modules)"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert "torch_loaded: False" in result.stdout, (
        f"torch leaked into top-level import. "
        f"stdout={result.stdout[-500:]} stderr={result.stderr[-500:]}"
    )


def test_importing_engine_directly_does_not_load_sentence_transformers() -> None:
    """``import app.reading.query.engine`` must NOT pull sentence_transformers."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import app.reading.query.engine; "
                "print('sentence_transformers_loaded:', "
                "'sentence_transformers' in sys.modules)"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert "sentence_transformers_loaded: False" in result.stdout, (
        f"sentence_transformers leaked when importing engine module directly. "
        f"stdout={result.stdout[-500:]} stderr={result.stderr[-500:]}"
    )


def test_importing_engine_does_not_load_app_llm_client() -> None:
    """Engine must NOT pull app.llm.client at module top.

    The default-client resolver also lazy-imports it inside the function
    body, so an offline query module (LLM disabled, no client supplied)
    pays no import cost.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import app.reading.query.engine; "
                "print('llm_client_loaded:', 'app.llm.client' in sys.modules)"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert "llm_client_loaded: False" in result.stdout, (
        f"app.llm.client leaked into engine top-level import. "
        f"stdout={result.stdout[-500:]} stderr={result.stderr[-500:]}"
    )
