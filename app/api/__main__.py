"""Backend process entry point: python -m app.api"""

from __future__ import annotations

import uvicorn

from app.core.config import get_settings
from app.core.eventloop import configure_event_loop
from app.core.logging import configure_logging


def main() -> None:
    configure_event_loop()
    settings = get_settings()
    configure_logging("INFO", settings.debug)
    uvicorn.run(
        "app.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        loop="none",  # use the selector loop configured by configure_event_loop()
    )


if __name__ == "__main__":
    main()
