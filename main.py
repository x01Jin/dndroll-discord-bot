"""Entrypoint — thin, no business logic here."""

from __future__ import annotations

import asyncio
import logging
import sys

from bot import DndRollBot
from config import load_settings

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # Quiet noisy libs unless DEBUG.
    if numeric > logging.DEBUG:
        for noisy in ("discord.http", "discord.gateway", "aiohttp.access"):
            logging.getLogger(noisy).setLevel(logging.WARNING)


async def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    bot = DndRollBot(settings)

    try:
        async with bot:
            await bot.start(settings.token)
    except KeyboardInterrupt:
        logger.info("Shutting down (KeyboardInterrupt)")
    except RuntimeError as exc:
        # Config error — already has a nice message, just surface it.
        logger.error("%s", exc)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
