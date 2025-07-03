from __future__ import annotations

"""Command-line interface entry point for *spotify-library-builder*.

Typical usage::

    $ sp-lib-builder 37i9dQZF1DXcBWIGoYBM5M
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from . import config
from .converter import ConverterClient
from .spotify_client import SpotifyClient
from .utils import ensure_directory
from .youtube_client import YouTubeClient

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s – %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt="%H:%M:%S")


def build_library(playlist_id: str, output_dir: Path) -> None:
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


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sp-lib-builder",
        description="Download a Spotify playlist as MP3 files via YouTube.",
    )
    parser.add_argument("playlist_id", help="Spotify playlist ID")
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

    build_library(args.playlist_id, args.output)


# Allow ``python -m spotify_library_builder`` for convenience
if __name__ == "__main__":
    main() 