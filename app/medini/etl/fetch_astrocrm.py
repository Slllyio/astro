"""Fetch the redistributable ASTROCRM corpus files for run 3.

Downloads the Astro-Databank-derived CSVs from the ASTROCRM GitHub repo
(raw.githubusercontent.com — the repo UI/clone path is blocked by this
environment's proxy, raw files are not) into ``data/holos/`` and records a
``MANIFEST.json`` with URL, sha256 and fetch date for the pre-registration.

Files:
- ``holos_clean.csv``            — 61,583 Rodden AA/A rows with birth
                                    date + time + lat/lon + utc_offset.
- ``astro_people.csv``           — wikitext with {{ASTRODATABANK_evn}} event
                                    templates (the death-date source).
- ``astro_analytics_quality.csv``— categories side-table (optional, larger
                                    coverage than astro_people for labels).

The lapaas booster (github.com/lapaasindia/good-time-finder) is attempted
best-effort across common branch names; failure is logged and non-fatal
(pre-registered as optional).

Usage:
    python -m app.medini.etl.fetch_astrocrm --out data/holos
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

_ASTROCRM_BASE = "https://raw.githubusercontent.com/jfsagro-glitch/ASTROCRM/main"
_ASTROCRM_FILES = (
    "holos_clean.csv",
    "astro_people.csv",
    "astro_analytics_quality.csv",
)

_LAPAAS_CANDIDATES = tuple(
    f"https://raw.githubusercontent.com/lapaasindia/good-time-finder/{branch}/{path}"
    for branch in ("main", "master")
    for path in ("personalities.json", "data/personalities.json",
                 "events.json", "data/events.json")
)

_UA = "astro-raman-validation/0.3 (research; run-3 corpus fetch)"
_CHUNK = 1 << 20


def _download(url: str, dest: Path, retries: int = 3) -> dict | None:
    """Stream url -> dest; return manifest entry or None on failure."""
    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, headers={"User-Agent": _UA},
                              timeout=300, stream=True) as r:
                if r.status_code == 404:
                    logger.warning("404 %s", url)
                    return None
                r.raise_for_status()
                sha = hashlib.sha256()
                size = 0
                dest.parent.mkdir(parents=True, exist_ok=True)
                with dest.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=_CHUNK):
                        f.write(chunk)
                        sha.update(chunk)
                        size += len(chunk)
            logger.info("fetched %s (%.1f MB)", dest.name, size / 1e6)
            return {"url": url, "path": str(dest), "bytes": size,
                    "sha256": sha.hexdigest()}
        except requests.RequestException as exc:
            logger.warning("attempt %d/%d failed for %s: %s",
                           attempt, retries, url, exc)
    return None


def fetch_all(out_dir: Path) -> dict:
    manifest: dict = {
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "files": {},
        "lapaas": {},
    }
    ok = True
    for name in _ASTROCRM_FILES:
        entry = _download(f"{_ASTROCRM_BASE}/{name}", out_dir / name)
        if entry is None:
            ok = False
            logger.error("REQUIRED file failed: %s", name)
        else:
            manifest["files"][name] = entry

    # Best-effort lapaas booster (optional; pre-registered as such).
    fetched_lapaas: set[str] = set()
    for url in _LAPAAS_CANDIDATES:
        fname = url.rsplit("/", 1)[-1]
        if fname in fetched_lapaas:
            continue
        entry = _download(url, out_dir.parent / "lapaas" / fname, retries=1)
        if entry is not None:
            manifest["lapaas"][fname] = entry
            fetched_lapaas.add(fname)

    manifest["required_complete"] = ok
    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    logger.info("manifest -> %s (required_complete=%s)",
                out_dir / "MANIFEST.json", ok)
    return manifest


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("data/holos"))
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    manifest = fetch_all(args.out)
    if not manifest["required_complete"]:
        print("FETCH INCOMPLETE — required ASTROCRM file(s) missing")
        return 1
    print(f"fetched {len(manifest['files'])} required + "
          f"{len(manifest['lapaas'])} lapaas files -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
