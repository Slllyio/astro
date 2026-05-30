"""Lazy-import perf regression: --no-enrich path must NOT load sentence_transformers."""
from __future__ import annotations

import subprocess
import sys


def test_cli_no_enrich_does_not_import_sentence_transformers():
    """When --no-enrich, sentence_transformers must NOT be imported.

    This catches accidental top-level imports of the RAG stack that would
    cost 200-600ms cold-start even when Tier 3 is disabled.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from app.reading.cli import main; "
                "main(["
                "    '--dob=1990-07-15','--time=12:00','--tz=+05:30',"
                "    '--lat=12.97','--lon=77.59','--no-enrich'"
                "]); "
                "print('sentence_transformers_loaded:', 'sentence_transformers' in sys.modules)"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    # The subprocess output may contain other things (logs, JSON, etc).
    # We only check the final print line, which has our signal.
    assert "sentence_transformers_loaded: False" in result.stdout, (
        f"sentence_transformers leaked into --no-enrich path. stdout: {result.stdout[-500:]}"
    )


def test_cli_no_enrich_does_not_import_torch():
    """torch is a transitive dep of sentence_transformers — same discipline."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from app.reading.cli import main; "
                "main(["
                "    '--dob=1990-07-15','--time=12:00','--tz=+05:30',"
                "    '--lat=12.97','--lon=77.59','--no-enrich'"
                "]); "
                "print('torch_loaded:', 'torch' in sys.modules)"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert "torch_loaded: False" in result.stdout, (
        f"torch leaked into --no-enrich path. stdout: {result.stdout[-500:]}"
    )
