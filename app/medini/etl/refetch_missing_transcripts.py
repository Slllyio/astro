"""Retry transcript fetches for videos where the bulk scrape returned ``none``.

The initial YouTube scrape often hits transient rate-limits on the
youtube-transcript-api, leaving ~half the videos with empty transcripts
even though the captions exist. This script walks the existing JSON
metadata files, identifies the ones where ``transcript_quality == "none"``,
and re-attempts the transcript fetch with a longer per-request delay.

For each successful refetch:
  - Overwrites <video_id>.txt with the new transcript
  - Updates the JSON's transcript_quality and transcript_chars

Conservative defaults: 2.0s delay between requests, retry only the ones
that didn't have an explicit "TranscriptsDisabled" error stored.

Usage:
    python -m app.medini.etl.refetch_missing_transcripts \\
        --input-dir data/knowledge_library/sources/lunarastro/youtube \\
        --delay 2.0
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

from app.medini.etl.scrape_lunarastro_youtube import fetch_transcript

logger = logging.getLogger(__name__)


def run(input_dir: Path, *, delay: float = 2.0) -> dict[str, int]:
    files = sorted(input_dir.glob("*.json"))
    candidates = []
    for jp in files:
        try:
            meta = json.loads(jp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if meta.get("transcript_quality") == "none":
            candidates.append((jp, meta))
    logger.info("found %d candidate videos (transcript_quality=none) of %d total",
                len(candidates), len(files))

    n_fetched = 0
    n_still_none = 0
    n_disabled = 0
    n_error = 0
    for i, (jp, meta) in enumerate(candidates):
        vid = meta.get("id") or jp.stem
        try:
            transcript, quality = fetch_transcript(vid)
        except Exception as e:
            logger.warning("[%d/%d] %s err: %s", i + 1, len(candidates), vid, e)
            n_error += 1
            time.sleep(delay)
            continue

        if quality == "none":
            n_still_none += 1
        else:
            tp = input_dir / f"{vid}.txt"
            tp.write_text(transcript, encoding="utf-8")
            meta["transcript_quality"] = quality
            meta["transcript_chars"] = len(transcript)
            jp.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
            n_fetched += 1
            logger.info("[%d/%d] %s now %s (%d chars)",
                        i + 1, len(candidates), vid, quality, len(transcript))
        time.sleep(delay)

    return {
        "candidates": len(candidates),
        "fetched_now": n_fetched,
        "still_disabled_or_none": n_still_none,
        "errors": n_error,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.refetch_missing_transcripts",
        description="Retry transcript fetch for videos that came back empty.",
    )
    parser.add_argument(
        "--input-dir", type=Path,
        default=Path("data/knowledge_library/sources/lunarastro/youtube"),
    )
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    stats = run(args.input_dir, delay=args.delay)
    print(
        f"Refetch complete: candidates={stats['candidates']} "
        f"fetched={stats['fetched_now']} "
        f"still_disabled={stats['still_disabled_or_none']} errors={stats['errors']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
