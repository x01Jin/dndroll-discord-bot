import discord
import random
import re
import os
import logging
import asyncio
from discord.ext import commands
import webserver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('dctoken')
if not TOKEN:
    raise ValueError("Discord bot token not found in environment variables")

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

def roll_dice(dice_str, interaction):
    dice_str = dice_str or '1d20'

    match = re.match(r'(\d*)d(\d+)', dice_str)
    if not match:
        return "Invalid dice format. Use XdY, where X is the number of dice and Y is the number of sides."

    num_dice = int(match.group(1)) if match.group(1) else 1
    num_sides = int(match.group(2))

    rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
    total = sum(rolls)

    if num_dice == 1:
        if num_sides == 20:
            if rolls[0] == 20:
                return f"{interaction.user.mention} rolled a nat 20! fuckin' insane!"
            elif rolls[0] == 1:
                return f"{interaction.user.mention} rolled a 1 on a D20... Blud's luck ran out ☠️"
            return f"{interaction.user.mention} rolled a D20 and got {rolls[0]}!"
        return f"{interaction.user.mention} rolled a die with ' {num_sides} ' sides and got {rolls[0]}!"
    
    if all(roll == num_sides for roll in rolls):
        return f"{interaction.user.mention} rolled ' {num_dice} ' dice with ' {num_sides} ' sides each and got {rolls} = {total} maxed all of them! BRO WHAT THE FUCK!😭😭😭"
    
    if all(roll == 1 for roll in rolls):
        return f"{interaction.user.mention} rolled ' {num_dice} ' dice with ' {num_sides} ' sides each and got {rolls} all 1s... Blud's luck ran out astronomically ☠️☠️☠️"

    return f"{interaction.user.mention} rolled ' {num_dice} '  dice with ' {num_sides} '  sides each and got {rolls} = {total}"

@tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    await interaction.response.send_message(f'Pong! {latency}ms')

@tree.command(name="roll", description="Roll a D20")
async def roll(interaction: discord.Interaction):
    result = roll_dice("1d20", interaction)
    await interaction.response.send_message(result)

@tree.command(name="roll_plus", description="Roll custom dice (e.g. 2d6)")
async def roll_plus(interaction: discord.Interaction, num_dice: int, num_sides: int):
    if num_dice < 1 or num_sides < 4:
        await interaction.response.send_message("Invalid input. You must roll at least 1 die with at least 4 sides.")
        return
    
    dice = f"{num_dice}d{num_sides}"
    result = roll_dice(dice, interaction)
    await interaction.response.send_message(result)

webserver.keep_alive()

@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')
    await client.change_presence(status=discord.Status.online, activity=discord.Game("D&D"))
    try:
        await client.tree.sync()
        logger.info("Slash commands synchronized successfully.")
    except Exception as e:
        logger.error(f"Failed to synchronize commands: {e}")

async def start_bot():
    while True:
        try:
            await client.start(TOKEN)
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            logger.info("Reconnecting in 3 seconds...")
            await asyncio.sleep(3)
        else:
            logger.info("Reconnected successfully.")
            break

async def main():
    await start_bot()

if __name__ == "__main__":
    asyncio.run(main())
