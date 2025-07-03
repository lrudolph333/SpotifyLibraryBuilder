from __future__ import annotations

"""Generic helper utilities used across the package."""

import re
from pathlib import Path

# Simplistic filename slugifier – sufficient for most track titles
_invalid_chars_re = re.compile(r"[^A-Za-z0-9._-]+")

# TODO: we want the name to be song name - artist name, not a random slug
def slugify(value: str, *, max_length: int = 200) -> str:
    """Return *value* converted to a safe filename.

    Parameters
    ----------
    value:
        The original (potentially unsafe) string.
    max_length:
        Truncate the resulting slug to at most this length (including the
        extension) so that we stay within common filesystem limits (255 chars).
    """

    # Convert whitespace to hyphens so that words are separated in filenames.
    value = value.strip().replace(" ", "-")
    value = _invalid_chars_re.sub("", value)
    return value[:max_length]


def ensure_directory(path: Path) -> None:
    """Ensure *path* exists, creating it (and parents) if necessary."""

    path.mkdir(parents=True, exist_ok=True)


def unique_path(directory: Path, base_name: str, extension: str = "") -> Path:
    """Return a file path that does not collide by appending a numeric suffix.

    Example
    -------
    >>> unique_path(Path("/tmp"), "song", ".mp3")
    PosixPath('/tmp/song.mp3')
    >>> # If /tmp/song.mp3 already exists:
    PosixPath('/tmp/song-1.mp3')
    """

    candidate = directory / f"{base_name}{extension}"
    counter = 1
    while candidate.exists():
        candidate = directory / f"{base_name}-{counter}{extension}"
        counter += 1
    return candidate


__all__ = [
    "slugify",
    "ensure_directory",
    "unique_path",
] 