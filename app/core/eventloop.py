"""Event-loop policy configuration for Windows.

psycopg3 async requires a selector-based event loop; the default Windows
``ProactorEventLoop`` is incompatible. Call :func:`configure_event_loop`
at the top of every process entry point.
"""

from __future__ import annotations

import asyncio
import sys


def configure_event_loop() -> None:
    """Select a selector event loop on Windows (required by psycopg async)."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
