"""Typed configuration for the bot. Fail-fast on missing token."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Settings:
    token: str
    guild_id: int | None = None
    log_level: str = "INFO"

    @property
    def is_dev_guild(self) -> bool:
        return self.guild_id is not None


def load_settings() -> Settings:
    """Load Settings from environment / .env.

    Token resolution order:
      1. DISCORD_TOKEN (preferred)
      2. dctoken       (legacy, kept for back-compat)
    """
    load_dotenv()

    token = os.getenv("DISCORD_TOKEN") or os.getenv("dctoken")
    if token:
        # Warn if only legacy var present so user migrates.
        if not os.getenv("DISCORD_TOKEN") and os.getenv("dctoken"):
            logger.warning(
                "Using legacy env var 'dctoken' — rename it to 'DISCORD_TOKEN' in your .env"
            )
        token = token.strip().strip('"').strip("'")
    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN not set. Create a .env file (see .env.example) "
            "or set the DISCORD_TOKEN environment variable."
        )

    guild_id: int | None = None
    raw_guild = (os.getenv("GUILD_ID") or "").strip()
    if raw_guild:
        try:
            guild_id = int(raw_guild)
        except ValueError as exc:
            raise RuntimeError(f"GUILD_ID must be an integer, got {raw_guild!r}") from exc

    log_level = (os.getenv("LOG_LEVEL") or "INFO").upper().strip()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        logger.warning("Unknown LOG_LEVEL %r, defaulting to INFO", log_level)
        log_level = "INFO"

    return Settings(token=token, guild_id=guild_id, log_level=log_level)
