from __future__ import annotations

"""Spotify Web API helper.

Only the endpoints required for this application are implemented. Currently
that means authentication via *Client Credentials* flow and fetching tracks
from a playlist.
"""

import base64
import logging
from dataclasses import dataclass
from typing import List

import requests

from . import config

logger = logging.getLogger(__name__)


@dataclass
class Track:
    """Represents a simplified track – only the information we actually need."""

    title: str
    artists: List[str]

    @property
    def search_query(self) -> str:
        """Return a string suitable for feeding into the YouTube search API."""

        return f"{self.title} {' '.join(self.artists)}".strip()


class SpotifyClient:
    """Minimal client for the Spotify Web API (https://developer.spotify.com/)."""

    _AUTH_URL = "https://accounts.spotify.com/api/token"
    _BASE_URL = "https://api.spotify.com/v1"

    def __init__(self, *, client_id: str | None = None, client_secret: str | None = None) -> None:
        self._client_id = client_id or config.SPOTIFY_CLIENT_ID
        self._client_secret = client_secret or config.SPOTIFY_CLIENT_SECRET
        self._access_token: str | None = None

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------

    def get_playlist_tracks(self, playlist_id: str) -> List[Track]:
        """Return all tracks contained in *playlist_id*.

        Parameters
        ----------
        playlist_id:
            The Spotify ID of the playlist (the part after ``playlist/`` in the
            share URL).
        """

        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self._BASE_URL}/playlists/{playlist_id}/tracks"
        params = {
            "limit": 100,  # max allowed by Spotify
            "offset": 0,
        }

        tracks: List[Track] = []
        while url:
            logger.debug("Fetching tracks from %s", url)
            resp = requests.get(url, headers=headers, params=params, timeout=config.REQUEST_TIMEOUT)
            resp.raise_for_status()
            payload = resp.json()

            for item in payload.get("items", []):
                track_info = item.get("track", {})
                # Skip local or unavailable tracks
                if track_info.get("is_local") or track_info.get("id") is None:
                    continue

                title = track_info.get("name", "Unknown Title")
                artists = [artist.get("name", "") for artist in track_info.get("artists", [])]
                tracks.append(Track(title=title, artists=artists))

            # Spotify API gives us a *next* URL we can follow for pagination
            url = payload.get("next")
            # ``params`` only needs to be supplied on the first request – the *next*
            # URL already contains the correct query parameters.
            params = {}

        logger.info("Fetched %d tracks from playlist %s", len(tracks), playlist_id)
        return tracks

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_access_token(self) -> str:
        """Return a cached access token, refreshing it if necessary."""

        if self._access_token:
            return self._access_token

        if not (self._client_id and self._client_secret):
            raise RuntimeError(
                "Spotify client ID/secret not provided. Set them in your .env file."
            )

        basic_auth = base64.b64encode(f"{self._client_id}:{self._client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        resp = requests.post(self._AUTH_URL, headers=headers, data=data, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        self._access_token = resp.json().get("access_token")

        if not self._access_token:
            raise RuntimeError("Could not obtain Spotify access token – check your credentials.")

        return self._access_token


__all__ = ["SpotifyClient", "Track"] 