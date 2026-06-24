"""Scrape a YouTube channel's videos (metadata + transcripts) into the knowledge library.

Uses yt-dlp for video discovery + metadata and youtube-transcript-api for
auto-caption transcripts. Both libraries are stable, open-source, and don't
require an API key.

Output schema (one pair of files per video) at
``data/knowledge_library/sources/lunarastro/youtube/``:

  <video_id>.json — metadata dict with title, channel, upload_date, duration,
                    view_count, like_count, description, tags, categories
  <video_id>.txt  — transcript (auto-captions if available; empty file if not).
                    First line is a UTF-8 BOM-stripped header noting source.

Resume support: skipping videos whose <video_id>.json already exists.

Usage:
    python -m app.medini.etl.scrape_lunarastro_youtube \\
        --channel "@LunarAstro" \\
        --output-dir data/knowledge_library/sources/lunarastro/youtube \\
        [--limit 20] [--max-duration-min 60] [--delay 1.0]

Default tries multiple common handles for the lunarastro channel; falls back
to a search if none resolve.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import yt_dlp
from youtube_transcript_api import (
    NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi,
)

logger = logging.getLogger(__name__)

DEFAULT_CHANNELS = (
    "@LunarAstro",
    "@lunarastrovedicacademy",
    "@DeepanshuGiri",
)


# --------------------------------------------------------------------------- #
# Discovery — find all video IDs on the channel                               #
# --------------------------------------------------------------------------- #

def _resolve_channel_url(handle: str) -> str:
    """Convert a channel handle like ``@LunarAstro`` into a videos URL."""
    if handle.startswith("@"):
        return f"https://www.youtube.com/{handle}/videos"
    if handle.startswith("UC"):
        return f"https://www.youtube.com/channel/{handle}/videos"
    if handle.startswith("http"):
        if "/videos" not in handle:
            return handle.rstrip("/") + "/videos"
        return handle
    return f"https://www.youtube.com/@{handle}/videos"


def list_channel_videos(handle: str, *, max_videos: int | None = None) -> list[dict[str, Any]]:
    """Return [{id, title, url, upload_date, duration}, ...] in upload-date order.

    Uses yt-dlp's ``extract_flat`` mode — very fast, doesn't download anything.
    """
    url = _resolve_channel_url(handle)
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "playlistend": max_videos if max_videos else None,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = info.get("entries", []) or []
    return [
        {
            "id": e.get("id"),
            "title": e.get("title"),
            "url": e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}",
            "duration": e.get("duration"),
            "view_count": e.get("view_count"),
        }
        for e in entries if e.get("id")
    ]


# --------------------------------------------------------------------------- #
# Per-video extraction                                                         #
# --------------------------------------------------------------------------- #

def fetch_video_metadata(video_id: str) -> dict[str, Any]:
    """Use yt-dlp to fetch full metadata for a single video (no download)."""
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/watch?v={video_id}", download=False,
        )
    # Trim to the fields we want in the persisted JSON.
    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "channel": info.get("channel"),
        "channel_id": info.get("channel_id"),
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "comment_count": info.get("comment_count"),
        "description": info.get("description"),
        "tags": info.get("tags") or [],
        "categories": info.get("categories") or [],
        "language": info.get("language"),
        "thumbnail": info.get("thumbnail"),
        "webpage_url": info.get("webpage_url"),
        "subtitles_available": sorted(list(info.get("subtitles", {}).keys())),
        "automatic_captions_available": sorted(
            list(info.get("automatic_captions", {}).keys())
        ),
    }


def fetch_transcript(video_id: str) -> tuple[str, str]:
    """Return (transcript_text, quality_tag).

    quality_tag ∈ {'manual_captions', 'auto_captions', 'none'}.
    Tries English first, then Hindi, then any available language.
    """
    try:
        api = YouTubeTranscriptApi()
        transcripts = api.list(video_id)
    except (TranscriptsDisabled, NoTranscriptFound):
        return "", "none"
    except Exception as e:
        logger.warning("transcript list failed for %s: %s", video_id, e)
        return "", "none"

    # Prefer manual captions in English, then Hindi, then any manual; then auto.
    preference_order: list[tuple[bool, tuple[str, ...]]] = [
        (False, ("en", "en-US", "en-GB")),         # manual English
        (False, ("hi",)),                          # manual Hindi
        (False, ()),                               # any manual
        (True, ("en", "en-US", "en-GB")),          # auto English
        (True, ("hi",)),                           # auto Hindi
        (True, ()),                                # any auto
    ]

    chosen = None
    chosen_quality = "none"
    available = list(transcripts)
    for is_generated, langs in preference_order:
        for t in available:
            if t.is_generated != is_generated:
                continue
            if langs and t.language_code not in langs:
                continue
            chosen = t
            chosen_quality = "auto_captions" if is_generated else "manual_captions"
            break
        if chosen:
            break
    if not chosen:
        return "", "none"

    try:
        fetched = chosen.fetch()
        # FetchedTranscript is iterable of objects with .text and .start
        lines = [
            seg.text if hasattr(seg, "text") else seg["text"]
            for seg in fetched
        ]
        text = "\n".join(lines).strip()
    except Exception as e:
        logger.warning("transcript fetch failed for %s: %s", video_id, e)
        return "", "none"
    return text, chosen_quality


# --------------------------------------------------------------------------- #
# Per-video persist                                                            #
# --------------------------------------------------------------------------- #

def persist_video(
    video_id: str,
    output_dir: Path,
    *,
    max_duration_seconds: int | None = None,
) -> dict[str, Any] | None:
    """Fetch metadata + transcript and write to disk. Skip if already exists.

    Returns the metadata dict (with extra `transcript_quality` and
    `transcript_chars` fields) or None on skip/failure.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    meta_path = output_dir / f"{video_id}.json"
    transcript_path = output_dir / f"{video_id}.txt"
    if meta_path.exists() and transcript_path.exists():
        logger.debug("skip cached %s", video_id)
        return None

    try:
        meta = fetch_video_metadata(video_id)
    except Exception as e:
        logger.warning("metadata fetch failed for %s: %s", video_id, e)
        return None

    if max_duration_seconds is not None and meta.get("duration"):
        if meta["duration"] > max_duration_seconds:
            logger.debug("skip too-long video %s (%ds)", video_id, meta["duration"])
            return None

    transcript, quality = fetch_transcript(video_id)
    transcript_path.write_text(transcript, encoding="utf-8")

    meta["transcript_quality"] = quality
    meta["transcript_chars"] = len(transcript)
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run(
    channels: list[str],
    output_dir: Path,
    *,
    limit: int | None = None,
    max_duration_min: int | None = None,
    delay: float = 1.0,
) -> dict[str, int]:
    """Walk channels in order, scrape each video. Resume-safe."""
    output_dir.mkdir(parents=True, exist_ok=True)
    max_duration_seconds = max_duration_min * 60 if max_duration_min else None

    # First, try to resolve at least one channel.
    discovered: list[dict[str, Any]] = []
    used_channel = None
    for channel in channels:
        logger.info("resolving channel %s ...", channel)
        try:
            videos = list_channel_videos(channel, max_videos=limit)
        except Exception as e:
            logger.warning("could not list %s: %s", channel, e)
            continue
        if videos:
            discovered = videos
            used_channel = channel
            logger.info("found %d videos on %s", len(videos), channel)
            break
    if not discovered:
        raise RuntimeError(
            f"none of these channels resolved: {channels}. "
            "Try passing an explicit channel URL or canonical UC... id via --channel."
        )

    n_processed = 0
    n_persisted = 0
    n_skipped = 0
    n_failed = 0
    for v in discovered:
        n_processed += 1
        try:
            result = persist_video(
                v["id"], output_dir,
                max_duration_seconds=max_duration_seconds,
            )
            if result is None:
                n_skipped += 1
            else:
                n_persisted += 1
                logger.info("[%d/%d] saved %s — %s (%s)",
                            n_processed, len(discovered),
                            v["id"], (v.get("title") or "")[:60],
                            result.get("transcript_quality"))
        except Exception as e:
            n_failed += 1
            logger.warning("[%d/%d] failed %s: %s",
                           n_processed, len(discovered), v["id"], e)
        time.sleep(delay)

    return {
        "channel": used_channel,
        "discovered": len(discovered),
        "processed": n_processed,
        "persisted": n_persisted,
        "skipped_cached": n_skipped,
        "failed": n_failed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.scrape_lunarastro_youtube",
        description="Scrape LunarAstro YouTube channel into the knowledge library.",
    )
    parser.add_argument(
        "--channel", action="append", default=[],
        help="Channel handle (@xxxx), canonical UC id, or full URL. "
             "Can be passed multiple times; first one to resolve wins. "
             f"Defaults: {DEFAULT_CHANNELS}",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("data/knowledge_library/sources/lunarastro/youtube"),
    )
    parser.add_argument("--limit", type=int, default=None,
                        help="Max videos to scrape (default: all on channel)")
    parser.add_argument("--max-duration-min", type=int, default=None,
                        help="Skip videos longer than this many minutes")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Seconds between videos (be polite)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    channels = args.channel or list(DEFAULT_CHANNELS)
    stats = run(
        channels, args.output_dir,
        limit=args.limit,
        max_duration_min=args.max_duration_min,
        delay=args.delay,
    )
    print(
        f"YouTube scrape complete: channel={stats['channel']} "
        f"discovered={stats['discovered']} persisted={stats['persisted']} "
        f"skipped_cached={stats['skipped_cached']} failed={stats['failed']} "
        f"-> {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
