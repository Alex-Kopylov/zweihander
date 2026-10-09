#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["youtube-transcript-api"]
# ///
r"""Fetch a YouTube video transcript and output it as structured JSON.

Usage:
    python fetch_transcript.py <url_or_video_id> [--language en,tr] [--timestamps]

Output (JSON):
    {
        "video_id": "...",
        "segment_count": 2,
        "duration": "0:07",
        "full_text": "complete transcript as plain text",
        "timestamped_text": "0:00 first line\n0:05 second line"
    }

`uv run` installs youtube-transcript-api from the metadata above.
"""

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any


def extract_video_id(url_or_id: str) -> str:
    """Extract the 11-character video ID from various YouTube URL formats.

    Args:
        url_or_id: A YouTube watch, short, shorts, embed or live URL, or a bare video ID.

    Returns:
        The video ID, or the stripped input unchanged when no ID is recognized.
    """
    url_or_id = url_or_id.strip()
    patterns = [
        r"(?:v=|youtu\.be/|shorts/|embed/|live/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id


def format_timestamp(seconds: float) -> str:
    """Convert seconds to H:MM:SS, or M:SS under an hour.

    Args:
        seconds: Offset from the start of the video; fractions are truncated.

    Returns:
        The formatted timestamp.
    """
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _import_transcript_api():
    """Import youtube-transcript-api, exiting with an install hint when it is missing.

    Returns:
        The youtube_transcript_api module.
    """
    try:
        import youtube_transcript_api
    except ImportError:
        script = shlex.quote(str(Path(__file__).resolve()))
        print(
            f"Error: youtube-transcript-api not installed. Run the helper with `uv run {script} URL`, "
            "which installs it from the script metadata.",
            file=sys.stderr,
        )
        sys.exit(1)
    return youtube_transcript_api


def fetch_transcript(video_id: str, languages: list[str] | None = None) -> list[dict[str, Any]]:
    """Fetch transcript segments from YouTube.

    Compatible with youtube-transcript-api v1.x.

    Args:
        video_id: The 11-character YouTube video ID.
        languages: Language codes in priority order; the library default when empty.

    Returns:
        A list of dicts with 'text', 'start', and 'duration' keys.
    """
    api = _import_transcript_api().YouTubeTranscriptApi()
    result = api.fetch(video_id, languages=languages) if languages else api.fetch(video_id)

    # v1.x returns FetchedTranscriptSnippet objects; normalize to dicts
    return [{"text": seg.text, "start": seg.start, "duration": seg.duration} for seg in result]


def main() -> None:
    """Parse the command line, fetch the transcript and print it as JSON or plain text."""
    parser = argparse.ArgumentParser(description="Fetch YouTube transcript as JSON")
    parser.add_argument("url", help="YouTube URL or video ID")
    parser.add_argument(
        "--language", "-l", default=None, help="Comma-separated language codes (e.g. en,tr). Default: auto"
    )
    parser.add_argument("--timestamps", "-t", action="store_true", help="Include timestamped text in output")
    parser.add_argument("--text-only", action="store_true", help="Output plain text instead of JSON")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    languages = [code.strip() for code in args.language.split(",")] if args.language else None

    api_error = _import_transcript_api().YouTubeTranscriptApiException
    try:
        segments = fetch_transcript(video_id, languages)
    # requests' network errors subclass OSError
    except (api_error, OSError) as e:
        error_msg = str(e)
        if "disabled" in error_msg.lower():
            print(json.dumps({"error": "Transcripts are disabled for this video."}))
        elif "no transcript" in error_msg.lower():
            print(json.dumps({"error": "No transcript found. Try specifying a language with --language."}))
        else:
            print(json.dumps({"error": error_msg}))
        sys.exit(1)

    full_text = " ".join(seg["text"] for seg in segments)
    timestamped = "\n".join(f"{format_timestamp(seg['start'])} {seg['text']}" for seg in segments)

    if args.text_only:
        print(timestamped if args.timestamps else full_text)
        return

    result = {
        "video_id": video_id,
        "segment_count": len(segments),
        "duration": format_timestamp(segments[-1]["start"] + segments[-1]["duration"]) if segments else "0:00",
        "full_text": full_text,
    }
    if args.timestamps:
        result["timestamped_text"] = timestamped

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
