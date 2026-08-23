"""Run database seeding: python scripts/seed.py"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.eventloop import configure_event_loop
from app.database.seed import seed_all
from app.database.session import async_session_factory


async def main() -> None:
    async with async_session_factory() as session:
        await seed_all(session)
    print("SEED_DONE")


if __name__ == "__main__":
    configure_event_loop()
    asyncio.run(main())
