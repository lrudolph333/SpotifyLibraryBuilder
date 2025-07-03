from __future__ import annotations

"""YouTube Data API (v3) helper functions."""

import logging
from typing import Optional

import requests

from . import config

logger = logging.getLogger(__name__)


class YouTubeClient:
    """Very small wrapper around the YouTube search endpoint."""

    _SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

    def __init__(self, *, api_key: str | None = None) -> None:
        self._api_key = api_key or config.YOUTUBE_API_KEY
        if not self._api_key:
            raise RuntimeError(
                "YouTube API key not provided. Set YOUTUBE_API_KEY in your .env file."
            )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def search_first_video(self, query: str) -> Optional[str]:
        """Return the full YouTube URL for the top search result.

        If no result is found ``None`` is returned.
        """

        params = {
            "part": "snippet",
            "type": "video",
            "q": query,
            "key": self._api_key,
            "maxResults": 1,
            "safeSearch": "strict",
        }

        logger.debug("Searching YouTube for: %s", query)
        resp = requests.get(self._SEARCH_URL, params=params, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        items = resp.json().get("items", [])

        if not items:
            logger.warning("No YouTube results for query: %s", query)
            return None
        # TODO: we may want to save multiple videos instead of the top result
        video_id = items[0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={video_id}"


__all__ = ["YouTubeClient"] 