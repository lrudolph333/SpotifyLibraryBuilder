from __future__ import annotations

"""Configuration utilities for Spotify Library Builder.

This module centralises access to environment variables and other global
configuration that the application relies on. On import it will load a
``.env`` file from the project root (if present) so that API secrets do not
have to be exported in your shell directly.

All configuration access should go through the attributes exposed here rather
than reading environment variables throughout the codebase. This keeps the
code clean and makes it easy to provide defaults or additional validation in
one place.

Note: *Never* commit real secrets – only keep them in your local ``.env`` file
which is ignored by Git.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables from a .env file (if it exists)
# ---------------------------------------------------------------------------

# By default we look for a .env file in the project root – one directory up
# from ``src``.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_env_path = _PROJECT_ROOT / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    # Fallback to default loading behaviour (search upward) so that users can
    # locate their .env elsewhere if desired.
    load_dotenv()

# ---------------------------------------------------------------------------
# Mandatory API credentials – raise early if they are missing to guide the user
# ---------------------------------------------------------------------------

SPOTIFY_CLIENT_ID: str | None = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET: str | None = os.getenv("SPOTIFY_CLIENT_SECRET")
YOUTUBE_API_KEY: str | None = os.getenv("YOUTUBE_API_KEY")
# Legacy keys retained for backward compatibility but no longer required
# YT2MP3_API_KEY: str | None = os.getenv("YT2MP3_API_KEY")
# YT2MP3_RAPIDAPI_KEY: str | None = os.getenv("YT2MP3_RAPIDAPI_KEY")
# YT2MP3_BASE_URL: str = os.getenv("YT2MP3_BASE_URL", "https://youtube-to-mp315.p.rapidapi.com/")

# The legacy YouTube-to-MP3 service is no longer used, so the associated key
# is optional.
_legacy_YT2MP3_API_KEY: str | None = os.getenv("YT2MP3_API_KEY")  # kept for backward compatibility

MANDATORY_VARS = {
    "SPOTIFY_CLIENT_ID": SPOTIFY_CLIENT_ID,
    "SPOTIFY_CLIENT_SECRET": SPOTIFY_CLIENT_SECRET,
    "YOUTUBE_API_KEY": YOUTUBE_API_KEY,
}


class MissingEnvironmentVariable(RuntimeError):
    """Raised when a mandatory environment variable is missing."""


for _var_name, _value in MANDATORY_VARS.items():
    if not _value:
        raise MissingEnvironmentVariable(
            f"Environment variable '{_var_name}' is not set. "
            "Create a `.env` file from `env.template` (or export the variable) "
            "before running the application."
        )

# ---------------------------------------------------------------------------
# Other runtime configuration
# ---------------------------------------------------------------------------

# Default download directory – the user's *Downloads* folder
DOWNLOADS_DIR: Path = Path.home() / "Downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)  # Ensure it exists

# HTTP timeouts (in seconds) for all outbound requests
REQUEST_TIMEOUT: int = 15

__all__ = [
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "YOUTUBE_API_KEY",
    # "YT2MP3_API_KEY",
    "DOWNLOADS_DIR",
    "REQUEST_TIMEOUT",
    "MissingEnvironmentVariable",
] 