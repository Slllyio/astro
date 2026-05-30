"""Spike A — measure cold-start cost of expected Phase 1 imports (each in isolated subprocess)."""
from __future__ import annotations
import subprocess
import sys
import time

IMPORTS = [
    "import json",
    "import argparse",
    "import datetime",
    "import logging",
    "import pydantic",
    "import swisseph",
    "import numpy",
    "import pandas",
    "from app.core import ephemeris_engine",
    "from app.core import shodashavarga",
    "from app.core import dignity",
    "from app.medini.services.knowledge_search import get_default_service",
]

print("Spike A: Import-chain cold-start measurements")
print("=" * 70)
for imp in IMPORTS:
    start = time.perf_counter()
    result = subprocess.run([sys.executable, "-c", imp], capture_output=True, text=True)
    elapsed = time.perf_counter() - start
    status = "OK" if result.returncode == 0 else "FAIL"
    print(f"  {elapsed*1000:7.0f}ms  {status}  {imp}")
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        print(f"    stderr: {stderr[:200]}")
