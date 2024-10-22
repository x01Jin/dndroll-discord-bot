import discord
import random
import re
import os
from discord.ext import commands
import webserver

TOKEN = os.environ['dctoken']

if TOKEN is None:
    raise ValueError("No dctoken found in environment variables")

intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

def roll_dice(dice_str):
    if not dice_str:
        dice_str = '1d20'

    match = re.match(r'(\d*)d(\d+)', dice_str)
    if not match:
        return "Invalid dice format. Use XdY, where X is the number of dice and Y is the number of sides."

    num_dice = int(match.group(1)) if match.group(1) else 1
    num_sides = int(match.group(2))

    rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
    total = sum(rolls)
    return f"Rolls: {rolls} | Total: {total}"

@tree.command(name="ping", description="Check the dndroll's latency")
async def ping(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    await interaction.response.send_message(f'Pong! {latency}ms')

@tree.command(name="roll", description="Rolls a dice")
async def roll(interaction: discord.Interaction):
    result = roll_dice("2d10")
    await interaction.response.send_message(result)

@tree.command(name="roll_plus", description="Rolls how many dice and sides you want")
async def roll_plus(interaction: discord.Interaction, num_dice: int, num_sides: int):
    dice = f"{num_dice}d{num_sides}"
    result = roll_dice(dice)
    await interaction.response.send_message(result)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await client.change_presence(status=discord.Status.online, activity=discord.Game("DnD"))
    try:
        await client.tree.sync()
        print("Slash commands synchronized successfully.")
    except Exception as e:
        print(f"Failed to synchronize commands: {e}")

webserver.keep_alive()

async def start_bot():
    while True:
        try:
            await client.start(TOKEN)
        except Exception as e:
            print(f"Error occurred: {e}")
            print("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
        else:
            print("Reconnected successfully.")
            break

async def main():
    await start_bot()

import asyncio
if __name__ == "__main__":
    asyncio.run(main())
