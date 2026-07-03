"""Load and validate the Raman Doctrine Compendium (JSONL, one file per book).

The compendium is data, not code: every record is a verbatim, page-cited
excerpt from a pinned source text plus a structured encoding of the rule it
states. This module is the single trusted reader — everything downstream
(the DSL engine, the fidelity harness, the domain engines) receives records
that have already passed:

  1. JSON-Schema validation (``data/raman_doctrine/schema/rule.schema.json``)
  2. Integrity checks the schema can't express:
     - ``quote_sha256`` matches the verbatim quote bytes
     - id's ``<book>`` segment matches the file's book
     - computability/antecedent pairing (full|partial need an antecedent;
       manual|unfalsifiable must have ``antecedent: null``)
     - no duplicate ids within a book or across the compendium

Records failing any check raise ``CompendiumError`` — a compendium with a
single bad record does not load. Corrections mint ``_rN`` ids; records are
never edited in place.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path("data/raman_doctrine/schema/rule.schema.json")
COMPENDIUM_DIR = Path("data/raman_doctrine/compendium")

_EXECUTABLE = {"full", "partial"}
_NON_EXECUTABLE = {"manual", "unfalsifiable"}


class CompendiumError(ValueError):
    """A rule record failed validation or integrity checks."""


def load_schema(schema_path: Path = SCHEMA_PATH) -> dict:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _validator(schema: dict) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(schema)


def quote_sha256(quote: str) -> str:
    return hashlib.sha256(quote.encode("utf-8")).hexdigest()


def validate_rule(rule: dict, *, book: str | None = None, schema: dict | None = None) -> None:
    """Validate one record; raises CompendiumError with the offending id."""
    schema = schema or load_schema()
    rid = rule.get("id", "<missing id>")
    errors = sorted(_validator(schema).iter_errors(rule), key=lambda e: e.json_path)
    if errors:
        raise CompendiumError(f"{rid}: schema: {errors[0].message} at {errors[0].json_path}")

    if quote_sha256(rule["quote"]) != rule["quote_sha256"]:
        raise CompendiumError(f"{rid}: quote_sha256 does not match the quote text")

    id_book = rule["id"].split(".")[1]
    if id_book != rule["book"]:
        raise CompendiumError(f"{rid}: id book segment {id_book!r} != book {rule['book']!r}")
    if book is not None and rule["book"] != book:
        raise CompendiumError(f"{rid}: book {rule['book']!r} in file for {book!r}")

    comp = rule["computability"]
    if comp in _EXECUTABLE and rule["antecedent"] is None:
        raise CompendiumError(f"{rid}: computability {comp!r} requires an antecedent")
    if comp in _NON_EXECUTABLE and rule["antecedent"] is not None:
        raise CompendiumError(f"{rid}: computability {comp!r} must have antecedent null")


def load_book(path: Path, *, schema: dict | None = None) -> list[dict]:
    """Load one book's JSONL; every record validated, duplicate ids rejected."""
    schema = schema or load_schema()
    book = path.stem
    rules: list[dict] = []
    seen: set[str] = set()
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rule = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CompendiumError(f"{path.name}:{lineno}: invalid JSON: {exc}") from exc
        validate_rule(rule, book=book, schema=schema)
        if rule["id"] in seen:
            raise CompendiumError(f"{rule['id']}: duplicate id in {path.name}")
        seen.add(rule["id"])
        rules.append(rule)
    return rules


def load_compendium(directory: Path = COMPENDIUM_DIR) -> dict[str, list[dict]]:
    """Load every book file; ids must be unique across the whole compendium."""
    schema = load_schema()
    books: dict[str, list[dict]] = {}
    all_ids: set[str] = set()
    for path in sorted(directory.glob("*.jsonl")):
        rules = load_book(path, schema=schema)
        dupes = {r["id"] for r in rules} & all_ids
        if dupes:
            raise CompendiumError(f"{path.name}: ids already defined elsewhere: {sorted(dupes)[:5]}")
        all_ids.update(r["id"] for r in rules)
        books[path.stem] = rules
    return books


def write_book(path: Path, rules: list[dict], *, schema: dict | None = None) -> None:
    """Validate then write a book file (records sorted by id for stable diffs)."""
    schema = schema or load_schema()
    seen: set[str] = set()
    for rule in rules:
        validate_rule(rule, book=path.stem, schema=schema)
        if rule["id"] in seen:
            raise CompendiumError(f"{rule['id']}: duplicate id")
        seen.add(rule["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in
             sorted(rules, key=lambda r: r["id"])]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
