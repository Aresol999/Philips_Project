"""
Network/bootstrap hardening for demo environments.

Goal: prevent global environment misconfig (e.g., SSLKEYLOGFILE pointing to a
protected location) from crashing SSL context initialization inside
httpx/aiohttp/google-generativeai and friends.

This module is intentionally side-effectful on import.
"""

from __future__ import annotations

import os


def disable_ssl_key_logging() -> None:
    """
    Disable TLS key logging globally for this process.

    Some environments set SSLKEYLOGFILE to a protected path (e.g. a Windows
    virtual volume path). Python's ssl module will try to open it when creating
    default contexts, causing PermissionError and crashing network stacks.
    """
    # Unset entirely, and also set to empty to neutralize inherited env.
    if "SSLKEYLOGFILE" in os.environ:
        os.environ.pop("SSLKEYLOGFILE", None)
    os.environ["SSLKEYLOGFILE"] = ""


# Execute immediately on import (must run before importing SSL/network libs).
disable_ssl_key_logging()

