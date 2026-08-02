"""Exceptions raised by the Reciplease client."""

from __future__ import annotations


class ReciplaseError(Exception):
    """Base error for anything the Reciplease client raises."""


class InvalidAuth(ReciplaseError):
    """The API key was rejected (missing, malformed, or revoked)."""


class ReciplaseConnectionError(ReciplaseError):
    """The Reciplease API could not be reached."""
