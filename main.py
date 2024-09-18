import discord
import random
import re
import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv('cheese.env')
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

if TOKEN is None:
    raise ValueError("No DISCORD_BOT_TOKEN found in environment variables")

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)

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

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await client.change_presence(status=discord.Status.online, activity=discord.Game("DnD"))
    try:
        await client.tree.sync()
        print("Slash commands synchronized successfully.")
    except Exception as e:
        print(f"Failed to synchronize commands: {e}")

@client.tree.command(name="ping", description="Check the dndroll's latency")
async def ping(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    await interaction.response.send_message(f'Pong! {latency}ms')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!roll'):
        dice_str = message.content[len('!roll '):].strip()
        result = roll_dice(dice_str)
        await message.channel.send(result)

async def main():
    async with client:
        await client.start(TOKEN)

import asyncio
asyncio.run(main())
