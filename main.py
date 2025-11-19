import discord
import os
import logging
import time
from dotenv import load_dotenv
from discord.ext import commands


load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
activity = discord.Activity(type=discord.ActivityType.listening, name="i was spawncamped!", details="do /help for help!", platform="raspberry pi 4", assets={"small_url": "assets/images/icon.png", "small_text": "rei ayanami chikita plush"})
bot = commands.Bot(command_prefix='!', intents=intents)

MY_GUILD = discord.Object(id=1433854304678318183)

@bot.event
async def on_ready():
    assert bot.user is not None
    print(f'logged in as {bot.user}')
    print(f"platform: {os.name}, python version: {os.sys.version}, discord.py version: {discord.__version__}")
    print(f"system: {os.uname() if hasattr(os, 'uname') else 'N/A'}")
    print("----------------------------")
    await bot.change_presence(activity=activity, status=discord.Status.idle)



@bot.command(name="ping", description="ping") 
async def ping(ctx):
    await ctx.send(f"`Pong! Latency is {bot.latency} ms`")


@bot.command(name='add')
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    await ctx.send(left + right)

@bot.command(name="stop", description="Stops the bot (owner only)")
async def stop(ctx):
   if ctx.author.id == 429526435732914188:
        print(f"Shutdown command issued by {ctx.author}")
        await ctx.send("FUCK ALL OF YOU")
        time.sleep(1)
        await ctx.send("DONT KILL ME PLEASE!")
        time.sleep(1)
        await ctx.send("*AA-*")
        await bot.close()
   else:
     await ctx.send("Foolish mortal, you do not have permission to do that.")


async def setup_hook(self):
    self.tree.copy_global_to(guild=MY_GUILD)
    await self.tree.sync()

bot.run(token)