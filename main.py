import random
import discord
import os
import logging
import time
from rich import print as say
from dotenv import load_dotenv
from discord.ext import commands
import json
from datetime import datetime
import psutil
import requests

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
owner = os.getenv('owner')
MY_GUILD = os.getenv('guildId')

reconnect = 0
handler = logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='w')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
activity = discord.Activity(type=discord.ActivityType.listening, name="up and running...", details="do !help for help!")
bot = commands.Bot(command_prefix='!', intents=intents, activity=activity, status=discord.Status.idle, help_command=None)


isMainBotUp = requests.get("http://localhost:1300/api/status").text

################

@bot.event
async def on_ready():
    assert bot.user is not None
    say("               ")
    say("[green][bold]----------------------------")
    say(f'[green](re)logged in as {bot.user}')
    say("[green][bold]----------------------------")



@bot.hybrid_command(name="help", description="shows this message")
async def help(ctx):
    say(f"Help command called by [blue]{ctx.author} with type: {type}")
    embed = discord.Embed(title="Help Menu", description="List of available commands:", color=0x00ff00)
    embed.add_field(name="!sync", value="Syncs slash commands.", inline=False)
    embed.add_field(name="!ping", value="Checks the bot's latency.", inline=False)
    embed.add_field(name="!status", value="shows server status.", inline=False)
    embed.add_field(name="!source", value="Shows the bot source code link.", inline=False)
    embed.set_footer(text="created by ScottyFM. help categories: admin, social, gambling")
    await ctx.send(embed=embed)
    say(f"[green]Displayed general help menu to {ctx.author}")
    logging.info(f"Displayed general help menu to {ctx.author}")


@bot.hybrid_command(name="about", description="shows info about the bot")
async def about(ctx):
    say(f"About command called by [blue]{ctx.author}")
    logging.info(f"About command used by {ctx.author}")
    embed = discord.Embed(title="about", description="i was spawncamped!", color=0x0000ff)
    embed.add_field(name="made by", value="ScottyFM", inline=False)
    embed.add_field(name="", value="do `!source` for github repo", inline=False)
    embed.set_footer(timestamp=ctx.message.created_at)

    #todo: add system stats like uptime, latency, version, platform, etc.

    await ctx.send(embed=embed)


@bot.hybrid_command(name="source", description="shows the bot source code link")
async def source(ctx):
    say(f"Source command called by [blue]{ctx.author}")
    await ctx.reply("You can find my source code [here](https://github.com/ScottN13/spawncamped)")
    logging.info(f"Provided source code link to {ctx.author}")

@bot.hybrid_command(name="sync", description="syncs slash commands")
async def sync(ctx):
    bot.tree.clear_commands(guild=discord.Object(id=1433854304678318183))
    bot.tree.copy_global_to(guild=discord.Object(id=1433854304678318183))
    synced = await bot.tree.sync(guild=discord.Object(id=1433854304678318183))
    await ctx.reply(f"{len(synced)} Slash commands synced.")
    say(f"[green]{len(synced)}  slash commands synced by {ctx.author}")
    logging.info(f"{len(synced)} slash commands synced by {ctx.author}")

@bot.hybrid_command(name="ping", description="ping") 
async def ping(ctx):
    say(f"Ping command called by [blue]{ctx.author}")
    await ctx.reply(f"`Pong! Latency is {bot.latency} ms`")
    logging.info(f"Ping command used by {ctx.author} with latency {bot.latency} ms")


@bot.hybrid_command(name="stop", description="Stops the bot (owner only)")
async def stop(ctx):
   if ctx.author.id == owner:
        await ctx.reply("stopped")
        logging.info(f"stopped by {ctx.author}")
        await bot.close()
   else:
     await ctx.reply("You do not have permission to do that.")
     logging.info(f"{ctx.author} tried to stop bot")
     say(f"{ctx.author} tried to stop bot")

@bot.hybrid_command(name="status", description="shows server status")
async def status(ctx):
    say(f"Status command called by [blue]{ctx.author}")
    embed = discord.Embed(title="Server Status", description="Here's the current status of the server:", color=0x00ff00)
    embed.add_field(name="Latency", value=f"{bot.latency} ms", inline=False)
    # Add here server specs
    embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent()}%", inline=False)
    embed.add_field(name="Memory Usage", value=f"{psutil.virtual_memory().percent}%", inline=False)
    embed.add_field(name="Disk Usage", value=f"{psutil.disk_usage('/').percent}%", inline=False)
    #embed.add_field(name="Temps:", value=f"{psutil.()}", inline=False)
    embed.add_field(name="Platform", value=f"{os.name}", inline=False)
    embed.add_field(name="Python Version", value=f"{os.sys.version}", inline=False)
    await ctx.send(embed=embed)
    logging.info(f"Status command used by {ctx.author}")

@bot.hybrid_command(name="botinfo", description="shows bot info")
async def botinfo(ctx):
    say(f"BotInfo command called by [blue]{ctx.author}")
    embed = discord.Embed(title="spawncamped Info", description="This is stats for the main bot.", color=0x0000ff)
    embed.add_field(name="Active?", value=f"{isMainBotUp}", inline=False)
    embed.add_field(name="Library", value="discord.py", inline=False)
    embed.add_field(name="Uptime", value=f"{datetime.now() - bot.launch_time}", inline=False)
    embed.add_field(name="Latency", value=f"{bot.latency} ms", inline=False)
    await ctx.send(embed=embed)
    logging.info(f"BotInfo command used by {ctx.author}")

bot.run(token, log_handler=handler, log_level=logging.INFO, root_logger=True)