"""Dice slash commands — embeds, range validation, pure dice core."""

from __future__ import annotations

import logging
from typing import Annotated

import discord
from discord import app_commands
from discord.ext import commands

import dice
from dice import DiceError

logger = logging.getLogger(__name__)

# Discord option limits via Range — validated before handler runs (nice UI sliders).
DiceCount = Annotated[int, app_commands.Range[int, 1, 100]]
SidesCount = Annotated[int, app_commands.Range[int, 2, 1000]]
Modifier = Annotated[int, app_commands.Range[int, -10000, 10000]]

# Embed palette.
COLOR_DEFAULT = discord.Color.blurple()
COLOR_NAT20 = discord.Color.gold()
COLOR_NAT1 = discord.Color.dark_red()
COLOR_MAXED = discord.Color.green()
COLOR_MINNED = discord.Color.greyple()


def _build_embed(result: dice.RollResult, user: discord.abc.User) -> discord.Embed:
    title: str
    color = COLOR_DEFAULT
    description: str

    # Single die — preserve original joke flavour but in an embed.
    if result.num_dice == 1:
        r = result.rolls[0]
        mod_suffix = f" {result.modifier:+d}" if result.modifier else ""
        total_suffix = f" → **{result.total}**" if result.modifier else ""

        if result.num_sides == 20:
            if r == 20:
                title = "NAT 20! Insane! 🎉"
                color = COLOR_NAT20
                description = f"Rolled a **20** on a D20{mod_suffix}{total_suffix}"
            elif r == 1:
                title = "Natural 1... ☠️"
                color = COLOR_NAT1
                description = f"Rolled a **1** on a D20... bro's luck ran out{mod_suffix}{total_suffix}"
            elif r >= 19:
                title = f"Rolled {r} on a D20"
                description = f"Bro is being edged by fate ☠️ — got **{r}**{mod_suffix}{total_suffix}"
            else:
                title = f"Rolled {r} on a D20"
                description = f"Got **{r}**{mod_suffix}{total_suffix}"
        else:
            title = f"Rolled {r} on a D{result.num_sides}"
            description = f"Got **{r}**{mod_suffix}{total_suffix}"
    else:
        mod_str = f"{result.modifier:+d}" if result.modifier else ""
        base_rolls = ", ".join(map(str, result.rolls))
        # Truncate very long roll lists for embed field limits.
        if len(base_rolls) > 900:
            base_rolls = base_rolls[:900] + " …"

        if result.is_all_max:
            title = f"{result.num_dice}d{result.num_sides}{mod_str} — MAXED! 😭"
            color = COLOR_MAXED
            description = f"`[{base_rolls}]` = **{result.total}** — all {result.num_sides}s! BRO WHAT THE HECK!"
        elif result.is_all_min:
            title = f"{result.num_dice}d{result.num_sides}{mod_str} — all 1s ☠️"
            color = COLOR_MINNED
            description = f"`[{base_rolls}]` all 1s... astronomically unlucky → **{result.total}**"
        else:
            title = f"Rolled {result.spec}"
            subtotal = result.subtotal
            if result.modifier:
                description = f"`[{base_rolls}]` = {subtotal} {result.modifier:+d} = **{result.total}**"
            else:
                description = f"`[{base_rolls}]` = **{result.total}**"

    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url if user.display_avatar else None)
    embed.set_footer(text=f"{result.spec} • 🎲")
    return embed


class Roll(commands.Cog):
    """Dice commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # --- /roll -----------------------------------------------------------
    @app_commands.command(name="roll", description="Roll a D20 (with optional modifier)")
    @app_commands.describe(modifier="Modifier to add, e.g. +5 or -2")
    async def roll(self, interaction: discord.Interaction, modifier: Modifier = 0) -> None:
        result = dice.roll(num_dice=1, num_sides=20, modifier=modifier)
        embed = _build_embed(result, interaction.user)
        await interaction.response.send_message(embed=embed)

    # --- /roll_plus ------------------------------------------------------
    @app_commands.command(name="roll_plus", description="Roll custom dice (XdY with optional modifier)")
    @app_commands.describe(
        num_dice="Number of dice (1–100)",
        num_sides="Sides per die (2–1000)",
        modifier="Modifier to add to the total, e.g. +5 or -2",
    )
    async def roll_plus(
        self,
        interaction: discord.Interaction,
        num_dice: DiceCount,
        num_sides: SidesCount,
        modifier: Modifier = 0,
    ) -> None:
        result = dice.roll(num_dice=num_dice, num_sides=num_sides, modifier=modifier)
        embed = _build_embed(result, interaction.user)
        await interaction.response.send_message(embed=embed)

    # --- /r  (spec string — e.g. /r spec:2d6+3) -------------------------
    @app_commands.command(name="r", description="Roll dice from a spec string, e.g. 2d6+3, d20, 4d6-2")
    @app_commands.describe(spec="Dice spec like 2d6, 1d20+5, d6, 3d8-1")
    async def r(self, interaction: discord.Interaction, spec: str) -> None:
        try:
            result = dice.roll(spec)
        except DiceError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        embed = _build_embed(result, interaction.user)
        await interaction.response.send_message(embed=embed)

    # Per-cog error handler — catches DiceError + range violations nicely.
    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, DiceError):
            msg = str(error)
        elif isinstance(error, app_commands.CommandOnCooldown):
            msg = f"On cooldown — try again in {error.retry_after:.1f}s."
        else:
            # Let global handler log; just send a friendly ephemeral fallback here
            # if the global handler hasn't already responded.
            logger.warning("Roll cog error: %s", error, exc_info=error)
            msg = "Something went wrong rolling that. Check your dice spec?"
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Roll(bot))
