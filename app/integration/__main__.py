"""Allow ``python -m app.integration ...`` invocation."""

from __future__ import annotations

import sys

from app.integration.cli import main

if __name__ == "__main__":
    sys.exit(main())
