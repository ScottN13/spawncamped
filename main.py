import discord
import os
import logging
import time
from rich import print as say
from dotenv import load_dotenv
from discord.ext import commands


load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='w')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
activity = discord.Activity(type=discord.ActivityType.listening, name="i was spawncamped!", details="do !help for help!")
bot = commands.Bot(command_prefix='!', intents=intents, activity=activity, status=discord.Status.idle, help_command=None)

MY_GUILD = discord.Object(id=1433854304678318183)
scotty = 429526435732914188
bbq = 550259849896656907



@bot.event
async def on_ready():
    assert bot.user is not None
    say(f'[green]logged in as {bot.user}')
    say(f"platform: {os.name}, python version: {os.sys.version}, discord.py version: {discord.__version__}")
    say(f"system: {os.uname() if hasattr(os, 'uname') else 'N/A'}")
    say("[green][bold]----------------------------")

@bot.command(name="help", description="shows this message")
async def help(ctx, type: str = None):
    say(f"Help command called by [blue]{ctx.author} with type: {type}")
    if type is None:
        embed = discord.Embed(title="Help Menu", description="List of available commands:", color=0x00ff00)
        embed.add_field(name="!sync", value="Syncs slash commands.", inline=False)
        embed.add_field(name="!ping", value="Checks the bot's latency.", inline=False)
        embed.add_field(name="!add <left> <right>", value="Adds two numbers together.", inline=False)
        embed.add_field(name="!pin <message_id>", value="Pins a message to the announcements channel.", inline=False)
        embed.set_footer(text="created by ScottyFM. ")
        await ctx.send(embed=embed)

    if type == "admin":
        embed = discord.Embed(title="Admin Help Menu", description="List of admin commands:", color=0xff0000)
        embed.add_field(name="!createrules <title> <description>", value="Creates the server rules embed.", inline=False)
        embed.add_field(name="!enlist <user> <role_type>", value="Enlists a user into the server with specified role type (friends, member, trusted).", inline=False)
        embed.add_field(name="!stop", value="Stops the bot (owner only).", inline=False)
        embed.set_footer(text="created by ScottyFM. ")
        await ctx.send(embed=embed)

    elif type not in [None, "admin"]:
        await ctx.send("you have a stroke? it's `!help`.")

@bot.command(name="createrules", description="creates the server rules embed")
async def createrules(ctx, title, *, description):
    rules = bot.get_channel(1433865285097619546) # Rules channel ID
    say(f"CreateRules command called by [blue]{ctx.author}")
    embed = discord.Embed(title=title, description=description, color=0xff0000, timestamp=ctx.message.created_at)
    embed.set_footer(text="By joining the server, you agree to these rules.")
    try:
        # await discord.TextChannel.send(id=rules, embed=embed) # Rules channel ID # this doesnt send it to the rules channel for some reason
        await rules.send(embed=embed)
        await ctx.send("Done, i created the rules embed.")
    except Exception as e:
        await ctx.send(f"i uhm: {e}")
        say(f"[red]Error: {e}") 

@bot.command(name="sync", description="syncs slash commands")
async def sync(ctx):
    bot.tree.copy_global_to(guild=discord.Object(id=1433854304678318183))
    synced = await bot.tree.sync(guild=discord.Object(id=1433854304678318183))
    await ctx.send(f"{len(synced)} Slash commands synced.")
    say(f"[green]{len(synced)}  slash commands synced by {ctx.author}")

@bot.command(name="ping", description="ping") 
async def ping(ctx):
    say(f"Ping command called by [blue]{ctx.author}")
    await ctx.send(f"`Pong! Latency is {bot.latency} ms`")


@bot.command(name='add')
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    say(f"Add command called by {ctx.author} with arguments: {left}, {right}")
    await ctx.send(left + right)

@bot.command(name="stop", description="Stops the bot (owner only)")
async def stop(ctx):
   if ctx.author.id == scotty:
        say(f"Shutdown command issued by {ctx.author}")
        await ctx.send("FUCK ALL OF YOU")
        time.sleep(1)
        await ctx.send("DONT KILL ME PLEASE!")
        time.sleep(1)
        await ctx.send("*AA-*")
        await bot.close()
   else:
     await ctx.send("Foolish mortal, you do not have permission to do that.")

@bot.command(name="enlist", description="enlists a user into the server")
async def enlist(ctx, receiever: discord.Member, role_type: str): 
    # looks up both roles 
    member = discord.utils.get(ctx.guild.roles, id=1433856941163282637) 
    friends = discord.utils.get(ctx.guild.roles, id=1433856406406303776)
    trusted = discord.utils.get(ctx.guild.roles, id=1433854562875215972)

    if ctx.author.id == scotty or ctx.author.id == bbq: # checks if its me or BBQ
        if role_type == "friends" or "friend":
            try: # Necessary as the logs won't say shit.
                await receiever.add_roles(member)
                await receiever.add_roles(friends)
                await ctx.send(f"Done, verified {receiever} to the server (friend privileges).")
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")
                say(f"[red]Error: {e}")

        elif role_type == "member" or "members":
            try: 
                await receiever.add_roles(member)
                await ctx.send(f"Done, verified {receiever} to the server.")
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")
                say(f"[red]Error: {e}")
                
        elif role_type == "trusted":
            try:
                await receiever.add_roles(member)
                await receiever.add_roles(friends)
                await receiever.add_roles(trusted)
                await ctx.send(f"Done, entrusted {receiever}.")
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")
                say(f"[red]Error: {e}")
        else:
            await ctx.send(f"I don't know what {role_type} means. Maybe you made a typo?")

    else:
        await ctx.send("You have no permission to do that!")
        say(f"[red]{ctx.author} just tried to auto verify someone!")

@bot.command(name="pin", description="makes the bot pin a message to annoucements channel")
async def pin(ctx, message_id: int):
    channel = bot.get_channel(1433855475090198579) # Announcements channel ID
    try:
        say(f"Pin command called by {ctx.author} for message ID: {message_id}")
        message = await ctx.channel.fetch_message(message_id)
        await channel.send(content=f"Forwarded by {ctx.author}")
        await discord.Message.forward(message, destination=discord.utils.get(ctx.guild.channels, name="announcements")  )
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        say(f"[red]Error: {e}")



bot.run(token, log_handler=handler, log_level=logging.INFO, root_logger=True)