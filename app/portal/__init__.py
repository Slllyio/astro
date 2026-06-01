"""Family-charts portal package.

Persists relatives' birth data and serves master readings on demand. The
reading layer (app.integration / app.reading) is read-only from here — this
package only adds persistence + UI on top.

Importing this package imports `app.portal.models` so the Person table is
registered with the shared DeclarativeBase before `init_db()` runs
`Base.metadata.create_all`.
"""
from __future__ import annotations

from app.portal import models  # noqa: F401  (side-effect: register Person with Base)
