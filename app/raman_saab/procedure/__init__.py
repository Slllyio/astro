"""The procedure reader: Raman's house-reading procedure from his worked charts, as code.

A SEPARATE INSTRUMENT from the scored judge: it never feeds ``house_template``, the golden
ratchet, the doctrine snapshot or the report. Specification:
``docs/raman_saab/RAMAN_READING_PROCEDURE_2026-10-25.md``; record and measurement:
``docs/raman_saab/PROCEDURE_READER_2026-10-25.md``.

Usage:
    from app.raman_saab.procedure import read_procedure
    reading = read_procedure(chart)
    python -m app.raman_saab.procedure --date 1990-07-15 --time 12:00 --lat 12.97 --lon 77.59 --tz 5.5
"""
from __future__ import annotations

from app.raman_saab.procedure.model import ProcedureReading
from app.raman_saab.procedure.reader import read_matter, read_procedure

__all__ = ["ProcedureReading", "read_matter", "read_procedure"]
