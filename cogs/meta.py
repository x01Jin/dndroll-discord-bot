"""Meta / utility slash commands."""

from __future__ import annotations

import logging
import platform

import discord
from discord import app_commands
from discord.ext import commands

import dice as dice_module

logger = logging.getLogger(__name__)


class Meta(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction) -> None:
        latency_ms = round(self.bot.latency * 1000)
        # Defer not needed — this is instant. Use ephemeral? No — public pong is fun.
        await interaction.response.send_message(f"Pong! {latency_ms}ms 🏓")

    @app_commands.command(name="about", description="About this bot")
    async def about(self, interaction: discord.Interaction) -> None:
        assert self.bot.user is not None
        embed = discord.Embed(
            title="dndroll 🎲",
            description=("A joke D&D dice bot with a little too much personality.\n"),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Commands",
            value=(
                "`/roll` — roll a d20 (optional modifier)\n"
                "`/roll_plus` — roll XdY with modifier\n"
                "`/r` — roll from a spec like `2d6+3`\n"
                "`/ping` — latency\n"
                "`/about` — this card"
            ),
            inline=False,
        )
        embed.add_field(
            name="Limits",
            value=f"Dice 1–{dice_module.MAX_DICE} • Sides 2–{dice_module.MAX_SIDES} • Modifier ±{dice_module.MAX_MODIFIER_ABS}",
            inline=False,
        )
        embed.set_footer(
            text=f"py {platform.python_version()} • dpy {discord.__version__} • {self.bot.user.name}",
            icon_url=self.bot.user.display_avatar.url
            if self.bot.user.display_avatar
            else None,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Meta(bot))
