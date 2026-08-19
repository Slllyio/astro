"""Sweep merge gate — every extracted rule enters the compendium through here.

Extraction agents emit DRAFT records (JSONL) that may omit ``quote_sha256``,
``page`` and ``quote_verified``. This tool is the deterministic gate that:

  1. stamps each draft against the pinned source text — quote verification
     (the honesty gate) + mechanical page assignment (folio-aware),
  2. computes the quote sha256,
  3. schema-validates and integrity-checks every record (compendium rules),
  4. compiles every executable antecedent (unknown DSL ops fail here),
  5. merges into ``data/raman_doctrine/compendium/<book>.jsonl`` (existing
     ids are immutable — a colliding id is an error, corrections mint _rN),
  6. updates the coverage manifest for the swept chapters.

A draft with a single unverifiable quote or uncompilable antecedent fails
the whole merge (exit 1) and nothing is written — extraction cannot
introduce invented doctrine or dead rules.

CLI:
    python -m app.medini.doctrine.tools.sweep \
        --book hpa --draft drafts/hpa_ch14.jsonl \
        --source <scratch>/raman_sources/hpa.txt \
        --sweep-id p4_t1 [--mark XVII=swept:12] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from app.medini.doctrine.compendium import (
    COMPENDIUM_DIR,
    CompendiumError,
    load_book,
    load_schema,
    quote_sha256,
    validate_rule,
    write_book,
)
from app.medini.doctrine.engine.evaluate import compile_rule
from app.medini.doctrine.tools.coverage import load_manifest, mark, save_manifest
from app.medini.doctrine.tools.fetch_sources import MANIFEST
from app.medini.doctrine.tools.page_map import load_page_map
from app.medini.doctrine.tools.verify_quotes import SourceVerifier

logger = logging.getLogger(__name__)

PAGE_MAPS_DIR = Path("data/raman_doctrine/page_maps")


def stamp_drafts(drafts: list[dict], book: str, source_text: str) -> list[dict]:
    """Verify + page-stamp + sha every draft; raise on any unverified quote."""
    spec = next(s for s in MANIFEST if s.key == book)
    pmap = load_page_map(PAGE_MAPS_DIR / f"{book}.json")
    verifier = SourceVerifier(source_text, pmap, folio_at=spec.folio_at)
    stamped: list[dict] = []
    failures: list[str] = []
    for draft in drafts:
        rule = dict(draft)
        rule.setdefault("book", book)
        rule.setdefault("archive_item", spec.item)
        rule.setdefault("page", None)
        rule.setdefault("quote_verified", False)
        rule.setdefault("ambiguity_notes", None)
        rule.setdefault("conflicts_with", [])
        rule.setdefault("supersedes", None)
        rule["quote_sha256"] = quote_sha256(rule.get("quote", ""))
        rule = verifier.stamp(rule)
        if not rule["quote_verified"]:
            failures.append(rule.get("id", "<no id>"))
        stamped.append(rule)
    if failures:
        raise CompendiumError(
            f"{len(failures)} quote(s) NOT FOUND in {book} source "
            f"(first: {failures[:5]}) — drafts rejected")
    return stamped


def validate_and_compile(rules: list[dict], book: str) -> None:
    schema = load_schema()
    for rule in rules:
        validate_rule(rule, book=book, schema=schema)
        compile_rule(rule)


def merge(book: str, new_rules: list[dict], *, compendium_dir: Path = COMPENDIUM_DIR) -> int:
    path = compendium_dir / f"{book}.jsonl"
    existing = load_book(path) if path.exists() else []
    existing_ids = {r["id"] for r in existing}
    collisions = [r["id"] for r in new_rules if r["id"] in existing_ids]
    if collisions:
        raise CompendiumError(
            f"ids already in compendium (records are immutable; mint _rN): "
            f"{collisions[:5]}")
    write_book(path, existing + new_rules)
    return len(existing) + len(new_rules)


def run(book: str, draft_paths: list[Path], source_path: Path, sweep_id: str,
        marks: list[str], *, dry_run: bool = False) -> int:
    drafts: list[dict] = []
    for dp in draft_paths:
        for lineno, line in enumerate(dp.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                try:
                    drafts.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise CompendiumError(f"{dp.name}:{lineno}: bad JSON: {exc}") from exc
    logger.info("%s: %d draft records from %d file(s)", book, len(drafts), len(draft_paths))
    source_text = source_path.read_text(encoding="utf-8")
    stamped = stamp_drafts(drafts, book, source_text)
    validate_and_compile(stamped, book)
    logger.info("%s: all %d records verified + compiled", book, len(stamped))
    if dry_run:
        logger.info("dry run — nothing written")
        return 0
    total = merge(book, stamped)
    logger.info("%s: compendium now %d records", book, total)
    manifest = load_manifest(book)
    known = {c["label"] for c in manifest["chapters"]}
    for spec in marks:
        label, rest = spec.split("=", 1)
        status, _, count = rest.partition(":")
        if label not in known:
            # a sweep may cover a chapter the manifest hasn't seen yet;
            # append it rather than fail (title backfilled at render time).
            manifest["chapters"].append({
                "label": label, "title": "", "status": "pending",
                "rule_count": 0, "sweep_id": None, "notes": None,
            })
            known.add(label)
        mark(manifest, label, status, rule_count=int(count or 0), sweep_id=sweep_id)
    if marks:
        save_manifest(manifest)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book", required=True)
    parser.add_argument("--draft", type=Path, nargs="+", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sweep-id", required=True)
    parser.add_argument("--mark", action="append", default=[],
                        help="chapter coverage, e.g. XVII=swept:12")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        return run(args.book, args.draft, args.source, args.sweep_id,
                   args.mark, dry_run=args.dry_run)
    except CompendiumError as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
