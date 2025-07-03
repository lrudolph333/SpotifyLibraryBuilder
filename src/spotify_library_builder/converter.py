from __future__ import annotations

"""YouTube → MP3 conversion using yt-dlp.

Instead of relying on the discontinued third-party *YouTube-to-MP3* API we
directly download the best available audio stream with *yt-dlp* and let it
take care of the conversion to MP3 via ffmpeg.

ffmpeg must be available on the PATH.
"""

import logging
from pathlib import Path

from yt_dlp import YoutubeDL

from . import config, utils

logger = logging.getLogger(__name__)


class ConverterClient:
    """High-level helper that downloads a YouTube video as an MP3 file."""

    def __init__(self, *, ffmpeg_location: str | None = None) -> None:
        # Path to ffmpeg binary if the user wants to override autodetection
        self._ffmpeg_location = ffmpeg_location

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def convert_and_download(
        self, youtube_url: str, output_dir: Path, *, filename_base: str | None = None
    ) -> Path:
        """Download *youtube_url* as MP3 and save it to *output_dir*.

        Returns the absolute path of the downloaded file.
        """

        # Ensure target directory exists.
        utils.ensure_directory(output_dir)

        # Determine filename.
        base_name = utils.slugify(filename_base or "track")
        # Reserve a unique .mp3 path. yt-dlp will first download a temporary
        # media file and then post-process it into this final path.
        final_mp3_path = utils.unique_path(output_dir, base_name, ".mp3")
        outtmpl = str(final_mp3_path.with_suffix(".%(ext)s"))

        logger.debug("Starting yt-dlp download for %s → %s", youtube_url, outtmpl)

        ydl_opts = {
            # Select highest quality audio.
            "format": "bestaudio/best",
            # Use the filename we prepared above.
            "outtmpl": outtmpl,
            # Convert to mp3 after download.
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            # Reduce console noise – we manage our own logging.
            "quiet": True,
            "no_warnings": True,
            "logger": _YtDlpLoggerAdapter(),
            # Respect global request timeout when yt-dlp uses requests internally.
            "socket_timeout": config.REQUEST_TIMEOUT,
        }

        if self._ffmpeg_location:
            ydl_opts["ffmpeg_location"] = self._ffmpeg_location

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        logger.info("Saved MP3 to %s", final_mp3_path)
        return final_mp3_path


class _YtDlpLoggerAdapter:
    """Bridge yt-dlp log messages into our logger hierarchy."""

    def debug(self, msg):
        if msg.startswith("[debug] "):
            logger.debug(msg[8:])
        else:
            logger.info(msg)

    def warning(self, msg):
        logger.warning(msg)

    def error(self, msg):
        logger.error(msg)


__all__ = ["ConverterClient"] 