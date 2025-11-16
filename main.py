import discord
import os
import logging
from dotenv import load_dotenv
from discord.ext import commands


load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
client = discord.Client(intents=intents)
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    print(f'logged in as {client.user}')
    print(f"platform: {os.name}, python version: {os.sys.version}, discord.py version: {discord.__version__}")
    print(f"system: {os.uname() if hasattr(os, 'uname') else 'N/A'}")
    print("----------------------------")

class general(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping')
    async def ping(self, ctx):
        await ctx.send('Pong!')

client.run(token)