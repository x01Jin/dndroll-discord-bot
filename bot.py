"""Bot subclass — owns lifecycle, cogs and command sync."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from config import Settings

logger = logging.getLogger(__name__)

# Keep _COGS in sync with cogs/*.py `setup` entry points.
_COGS: tuple[str, ...] = (
    "cogs.roll",
    "cogs.meta",
)


class DndRollBot(commands.Bot):
    """Slash-only bot. No prefix commands, no message_content intent."""

    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        # Slash-only => no message_content, no members, no presences.
        intents.message_content = False
        super().__init__(
            command_prefix="!",  # unused — kept only because Bot requires one; slash-only via tree
            intents=intents,
            help_command=None,
            activity=discord.Game(name="D&D 🎲 /roll"),
        )
        self.settings = settings

    async def setup_hook(self) -> None:
        for cog in _COGS:
            try:
                await self.load_extension(cog)
                logger.info("Loaded extension %s", cog)
            except Exception:
                logger.exception("Failed to load extension %s", cog)
                raise

        # Sync strategy:
        # - If GUILD_ID is set: guild-scoped sync for instant iteration (no 1h global propagation).
        # - Otherwise: global sync.
        try:
            if self.settings.guild_id:
                guild = discord.Object(id=self.settings.guild_id)
                # Copy global commands to guild for dev; keeps prod globals intact.
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info("Synced %d commands to guild %d", len(synced), self.settings.guild_id)
                # Also ensure globals are synced (idempotent).
                global_synced = await self.tree.sync()
                logger.info("Synced %d global commands", len(global_synced))
            else:
                synced = await self.tree.sync()
                logger.info("Synced %d global commands", len(synced))
        except Exception:
            logger.exception("Command sync failed")
            raise

    async def on_ready(self) -> None:
        assert self.user is not None
        logger.info("Logged in as %s (id=%s)", self.user, self.user.id)
        logger.info("Guilds: %d | Latency: %.0fms", len(self.guilds), self.latency * 1000)

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError
    ) -> None:
        # Global fallback — cog-local handlers get first shot; this catches the rest.
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            msg = f"On cooldown — try again in {error.retry_after:.1f}s."
        elif isinstance(error, discord.app_commands.CheckFailure):
            msg = "You can't use that command here."
        else:
            logger.exception("Unhandled app command error in %s", interaction.command, exc_info=error)
            msg = "Something went wrong running that command. Try again?"

        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except discord.HTTPException:
            logger.warning("Failed to send error response for %s", interaction.command)
