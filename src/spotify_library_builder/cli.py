from __future__ import annotations

"""Command-line interface entry point for *spotify-library-builder*.

Typical usage::

    $ sp-lib-builder 37i9dQZF1DXcBWIGoYBM5M
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from . import config
from .converter import ConverterClient
from .spotify_client import SpotifyClient
from .utils import ensure_directory
from .youtube_client import YouTubeClient

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s – %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt="%H:%M:%S")


def build_library(
    playlist_id: str,
    output_dir: Path,
    *,
    date_added_threshold: Optional[datetime] = None,
    song_name_threshold: Optional[str] = None,
) -> None:
    """End-to-end orchestration for building the local MP3 library."""

    # Create a timestamped sub-folder for this run so downloads stay organised
    ensure_directory(output_dir)

    session_dir = output_dir / f"sp-lib-builder-{datetime.now().strftime('%m-%d-%Y-%H-%M-%S')}"
    ensure_directory(session_dir)

    spotify = SpotifyClient()
    youtube = YouTubeClient()
    converter = ConverterClient()

    logging.info("Fetching tracks from Spotify playlist %s", playlist_id)
    tracks = spotify.get_playlist_tracks(playlist_id)
    logging.info("Found %d playable tracks", len(tracks))

    # ------------------------------------------------------------------
    # Optional sub-list filtering
    # ------------------------------------------------------------------
    if date_added_threshold:
        before_count = len(tracks)
        tracks = [t for t in tracks if t.added_at > date_added_threshold]
        logging.info(
            "Filtered tracks by date_added_threshold (%s) – %d → %d", date_added_threshold, before_count, len(tracks)
        )

    if song_name_threshold:
        # Find the first occurrence of the threshold song (case-insensitive match)
        threshold_index = next(
            (i for i, t in enumerate(tracks) if t.title.lower() == song_name_threshold.lower()),
            None,
        )
        if threshold_index is None:
            raise RuntimeError(
                f"Song '{song_name_threshold}' not found in playlist – cannot apply song-name threshold."
            )

        before_count = len(tracks)
        tracks = tracks[threshold_index + 1 :]
        logging.info(
            "Filtered tracks by song_name_threshold ('%s') – %d → %d",
            song_name_threshold,
            before_count,
            len(tracks),
        )

    for track in tqdm(tracks, desc="Processing", unit="track"):
        query = track.search_query
        try:
            yt_url = youtube.search_first_video(query)
            if yt_url is None:
                logging.warning("Skipping '%s' – no YouTube results", query)
                continue
        except Exception as exc:
            logging.error("YouTube search failed for '%s': %s", query, exc)
            continue

        # Build a filename like "Song-Name-Artist.mp3"
        base_name = f"{track.title}-{track.artists[0]}" if track.artists else track.title
        try:
            converter.convert_and_download(yt_url, session_dir, filename_base=base_name)
        except Exception as exc:
            logging.error("Conversion failed for '%s': %s", yt_url, exc)
            continue


def _parse_datetime(value: str) -> datetime:
    """Argparse *type* that parses an ISO-8601 datetime string.

    Supports the common 'Z' suffix for UTC. Raises an ``ArgumentTypeError`` on
    invalid input so argparse can surface a clean error message.
    """

    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Invalid datetime format for --date-added-threshold. Use ISO 8601, e.g. 2025-07-02T18:00:00Z"
        ) from exc


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sp-lib-builder",
        description="Download a Spotify playlist as MP3 files via YouTube.",
    )
    parser.add_argument("playlist_id", help="Spotify playlist ID")

    # Mutually exclusive threshold options
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--date-added-threshold",
        type=_parse_datetime,
        help=(
            "Only download tracks added *after* the given ISO 8601 timestamp. "
            "Example: 2025-07-02T18:00:00Z"
        ),
    )
    group.add_argument(
        "--song-name-threshold",
        help=(
            "Only download tracks that appear *after* the first occurrence of the given song title "
            "within the playlist order. Case-insensitive exact match."
        ),
    )

    parser.add_argument(
        "--log-level",
        "-l",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set logging verbosity (default: info)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=config.DOWNLOADS_DIR,
        help="Directory under which a timestamped run folder will be created (default: ~/Downloads)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    # Adjust root logger level as early as possible.
    numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(numeric_level)

    build_library(
        args.playlist_id,
        args.output,
        date_added_threshold=getattr(args, "date_added_threshold", None),
        song_name_threshold=getattr(args, "song_name_threshold", None),
    )


# Allow ``python -m spotify_library_builder`` for convenience
if __name__ == "__main__":
    main() 