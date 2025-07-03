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
        """Return a YouTube URL for the best-guess audio source.

        The method tries several increasingly relaxed searches:

        1. ``"<query> lyrics"`` with *high-definition* filter.
        2. ``"<query> lyrics"`` without the HD filter.
        3. Original ``query`` with *high-definition* filter.
        4. Original ``query`` with no extra filters.

        Rationale: lyric videos often carry album-quality audio and are less
        likely to contain long intros/outros or crowd noise. We also prefer HD
        uploads (``videoDefinition=high``) which typically have better audio
        streams.
        """

        def _attempt(search_query: str, hd_only: bool) -> Optional[str]:
            params = {
                "part": "snippet",
                "type": "video",
                "q": search_query,
                "key": self._api_key,
                "maxResults": 1,
                "safeSearch": "strict",
            }
            if hd_only:
                params["videoDefinition"] = "high"

            logger.debug("YouTube search – query='%s' hd_only=%s", search_query, hd_only)
            resp = requests.get(self._SEARCH_URL, params=params, timeout=config.REQUEST_TIMEOUT)
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if not items:
                return None
            return items[0]["id"].get("videoId")

        search_plan = [
            (f"{query} lyrics", True),
            (f"{query} lyrics", False),
            (query, True),
            (query, False),
        ]

        for q, hd in search_plan:
            video_id = _attempt(q, hd)
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"

        logger.warning("No YouTube results for query: %s (after trying lyric/HD variants)", query)
        return None


__all__ = ["YouTubeClient"] 