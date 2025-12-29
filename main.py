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

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

reconnect = 0
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
SCORES_FILE = 'scores.json'

# functions for score management
def load_scores(): # fetches scores from scores.json
    try:
        with open(SCORES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_scores(scores): # writes to scores.json
    with open(SCORES_FILE, 'w') as f:
        json.dump(scores, f, indent=2)

def can_claim_daily(user_id): # function to check if user can claim daily points
    scores = load_scores()
    user_id_str = str(user_id)
    
    if user_id_str not in scores:
        return True
    
    today = datetime.now().strftime('%Y-%m-%d')
    last_claimed = scores[user_id_str].get('last_daily_claimed')
    
    return last_claimed != today

def add_score(user_id, points): # modify a user's score
    scores = load_scores() # gets current scores
    user_id_str = str(user_id)
    
    if user_id_str not in scores:
        scores[user_id_str] = {'total_score': 0, 'daily_score': 0}

    
    scores[user_id_str]['total_score'] += points
    scores[user_id_str]['last_daily_claimed'] = datetime.now().strftime('%Y-%m-%d')
    
    save_scores(scores) # make sure to always save after modifying
    return points

def check_score(user_id): # returns a user's score
    scores = load_scores()
    user_id_str = str(user_id)
    
    if user_id_str in scores:
        return scores[user_id_str]['total_score']
    else:
        return None

def get_leaderboard(limit=10): # returns top 10 users by score
    scores = load_scores()
    sorted_users = sorted(scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
    return sorted_users[:limit]

################

@bot.event
async def on_ready():
    assert bot.user is not None
    say("               ")
    say("[green][bold]----------------------------")
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
        embed.add_field(name="!pin <message_id>", value="Pins a message to the announcements channel.", inline=False)
        embed.add_field(name="!source", value="Shows the bot source code link.", inline=False)
        embed.set_footer(text="created by ScottyFM. help categories: admin, social, gambling")
        await ctx.send(embed=embed)
        say(f"[green]Displayed general help menu to {ctx.author}")
        logging.info(f"Displayed general help menu to {ctx.author}")

    if type == "social":
        embed = discord.Embed(title="Social Help Menu", description="List of social commands:", color=0x0000ff)
        embed.add_field(name="!mc", value="Shows details of the Minecraft server (Currently Xander's).", inline=False)
        embed.add_field(name="!daily", value="Gives daily points. Used in gambling.", inline=False)
        embed.add_field(name="!leaderboard", value="Shows the total points leaderboard.", inline=False)
        embed.set_footer(text="created by ScottyFM. help categories: admin, social, gambling")
        await ctx.send(embed=embed)
        say(f"[green]Displayed social help menu to {ctx.author}")
        logging.info(f"Displayed social help menu to {ctx.author}")

    if type == "gambling":
        embed = discord.Embed(title="Gambling Help Menu", description="List of gambling commands:", color=0xffff00)
        embed.add_field(name="!roll <sides>", value="Rolls a dice with specified number of sides (default 6).", inline=False)
        embed.add_field(name="!flip <wager>", value="Flips a coin. Heads is win, tails is lose.", inline=False)
        embed.add_field(name="!spin", value="Spins a roulette wheel. (NOT PROGRAMMED YET.)", inline=False)
        embed.set_footer(text="created by ScottyFM. help categories: admin, social, gambling")
        await ctx.send(embed=embed)
        say(f"[green]Displayed gambling help menu to {ctx.author}")
        logging.info(f"Displayed gambling help menu to {ctx.author}")

    if type == "admin":
        embed = discord.Embed(title="Admin Help Menu", description="List of admin commands:", color=0xff0000)
        embed.add_field(name="!createrules <title> <description>", value="Creates the server rules embed.", inline=False)
        embed.add_field(name="!enlist <user> <role_type>", value="Enlists a user into the server with specified role type (friends, member, trusted).", inline=False)
        embed.add_field(name="!stop", value="Stops the bot (owner only).", inline=False)
        embed.set_footer(text="created by ScottyFM. help categories: admin, social, gambling")
        await ctx.send(embed=embed)
        say(f"[green]Displayed admin help menu to {ctx.author}")
        logging.info(f"Displayed admin help menu to {ctx.author}")

    elif type not in [None, "social", "gambling", "admin"]:
        await ctx.send("you have a stroke? it's `!help`.")
        say(f"[red]{ctx.author} provided invalid help type: {type}")
        logging.warning(f"{ctx.author} provided invalid help type: {type}")

@bot.command(name="about", description="shows info about the bot")
async def about(ctx):
    say(f"About command called by [blue]{ctx.author}")
    logging.info(f"About command used by {ctx.author}")
    embed = discord.Embed(title="about", description="i was spawncamped!", color=0x0000ff)
    embed.add_field(name="made by", value="ScottyFM", inline=False)
    embed.add_field(name="", value="do `!source` for github repo", inline=False)
    embed.set_footer(timestamp=ctx.message.created_at)

    #todo: add system stats like uptime, latency, version, platform, etc.

    await ctx.send(embed=embed)


@bot.command(name="source", description="shows the bot source code link")
async def source(ctx):
    say(f"Source command called by [blue]{ctx.author}")
    await ctx.send("You can find my source code [here](https://github.com/ScottN13/spawncamped)")
    logging.info(f"Provided source code link to {ctx.author}")

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
        logging.info(f"Created rules embed for {ctx.author} with contents: {title} - {description}")
    except Exception as e:
        await ctx.send(f"i uhm: {e}")
        say(f"[red]Error: {e}") 
        logging.error(f"Error creating rules embed for {ctx.author}: {e}")

@bot.command(name="sync", description="syncs slash commands")
async def sync(ctx):

    bot.tree.copy_global_to(guild=discord.Object(id=1433854304678318183))
    synced = await bot.tree.sync(guild=discord.Object(id=1433854304678318183))
    await ctx.send(f"{len(synced)} Slash commands synced.")
    await bot.add_cog(Social(bot))
    await bot.add_cog(leaderboard(bot))
    await bot.add_cog(Gambling(bot))
    say(f"[green]{len(synced)}  slash commands synced by {ctx.author}")
    logging.info(f"{len(synced)} slash commands synced by {ctx.author}")

@bot.command(name="ping", description="ping") 
async def ping(ctx):
    say(f"Ping command called by [blue]{ctx.author}")
    await ctx.send(f"`Pong! Latency is {bot.latency} ms`")
    logging.info(f"Ping command used by {ctx.author} with latency {bot.latency} ms")


"""
@bot.command(name='add')
async def add(ctx, left: int, right: int):
    # adds two numbers together
    say(f"Add command called by {ctx.author} with arguments: {left}, {right}")
    await ctx.send(left + right)
    logging.info(f"Add command used by {ctx.author} with arguments: {left}, {right}")
"""


@bot.command(name="stop", description="Stops the bot (owner only)")
async def stop(ctx):
   if ctx.author.id == scotty:
        say(f"Shutdown command issued by {ctx.author}")
        await ctx.send("FUCK ALL OF YOU")
        time.sleep(1)
        await ctx.send("DONT KILL ME PLEASE!")
        time.sleep(1)
        await ctx.send("*AA-*")
        logging.info(f"stopped by {ctx.author}")
        await bot.close()
   else:
     await ctx.send("Foolish mortal, you do not have permission to do that.")
     logging.info(f"{ctx.author} tried to stop bot")
     say(f"{ctx.author} tried to stop bot")

@bot.command(name="enlist", description="enlists a user into the server")
async def enlist(ctx, receiever: discord.Member, role_type: str): 
    # looks up both roles 
    member = discord.utils.get(ctx.guild.roles, id=1433856941163282637) 
    friends = discord.utils.get(ctx.guild.roles, id=1433856406406303776)
    trusted = discord.utils.get(ctx.guild.roles, id=1433854562875215972)
    role_type = role_type.lower()

    if ctx.author.id == scotty or ctx.author.id == bbq: # checks if its me or BBQ
        if role_type in ["friends", "friend"]:
            try: 
                await receiever.add_roles(member)
                await receiever.add_roles(friends)
                await ctx.send(f"Done, verified {receiever} to the server (friend privileges).")
                logging.info(f"{ctx.author} granted {role_type} role to {receiever}")
                say(f"[green]{ctx.author} granted {role_type} role to {receiever}")
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")
                say(f"[red]Error: {e}")
                logging.error(f"Error: {e}")

        elif role_type in ["member", "members"]:
            try: 
                await receiever.add_roles(member)
                await ctx.send(f"Done, verified {receiever} to the server.")
                logging.info(f"{ctx.author} granted {role_type} role to {receiever}")
                say(f"[green]{ctx.author} granted {role_type} role to {receiever}")
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")
                say(f"[red]Error: {e}")
                logging.error(f"Error: {e}")
                
        elif role_type == "trusted":
            try:
                await receiever.add_roles(member)
                await receiever.add_roles(friends)
                await receiever.add_roles(trusted)
                await ctx.send(f"Done, entrusted {receiever}.")
                logging.info(f"{ctx.author} granted {role_type} role to {receiever}")
                say(f"[green]{ctx.author} granted {role_type} role to {receiever}")
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")
                say(f"[red]Error: {e}")
                logging.error(f"Error: {e}")

        elif role_type not in ["friends", "friend", "member", "members", "trusted"]:
            await ctx.send(f"I don't know what `{role_type}` means. Maybe you made a typo?")
            logging.warning(f"{ctx.author} tried verifying {receiever} with provided invalid role type: {role_type}")

    else:
        await ctx.send("You have no permission to do that!")
        say(f"[red]{ctx.author} just tried to auto verify someone!")
        logging.warning(f"{ctx.author} tried to enlist {receiever} with role type: {role_type} without permission")

@bot.command(name="pin", description="makes the bot pin a message to annoucements channel")
async def pin(ctx, message_id: int):
    channel = bot.get_channel(1433855475090198579) # Announcements channel ID
    try:
        say(f"Pin command called by {ctx.author} for message ID: {message_id}")
        message = await ctx.channel.fetch_message(message_id)
        await channel.send(content=f"Forwarded by {ctx.author}")
        await discord.Message.forward(message, destination=discord.utils.get(ctx.guild.channels, id=channel.id))
        logging.info(f"Pinned message for {ctx.author} with id {message_id}")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        say(f"[red]Error: {e}")
        logging.error(f"Error pinning message for {ctx.author} with id {message_id}: {e}")

class Social(commands.Cog): # Social stuff for servers 
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="mc", description="shows details of mc server")
    async def mc(self, ctx):
        embed = discord.Embed(title="Minecraft Server Info", color=0x00ff00)
        embed.add_field(name="Server IP", value="none yet", inline=False)
        embed.add_field(name="Version", value="Java 1.20.1 - Forge 47.4.9", inline=False)
        embed.add_field(name="Modpack link:", value="[click here](https://drive.google.com/drive/folders/1QC7TeQf4ISNDqhdWa06QLQbj7MVGeqCE)", inline=False)
        await ctx.send(embed=embed)

class leaderboard(commands.Cog): # i seperated these for organization
    def __init__(self, bot):
        self.bot = bot
    

    @commands.command(name="daily", description="gives daily points")
    async def daily(self, ctx):
        if not can_claim_daily(ctx.author.id):
            await ctx.send(f"You already claimed your daily points.")
            logging.info(f"{ctx.author} tried to claim daily reward twice in one day")
            return
        
        points = random.randint(10, 100)
        add_score(ctx.author.id, points)
        
        scores = load_scores()
        total = scores[str(ctx.author.id)]['total_score']
        
        embed = discord.Embed(title="Daily Reward Claimed!", color=0x00ff00)
        embed.add_field(name="Points Earned", value=f"+{points}", inline=True)
        embed.add_field(name="Total Score", value=total, inline=True)
        embed.set_footer(text="Come back tomorrow for more points!")
        
        await ctx.send(embed=embed)
        logging.info(f"{ctx.author} claimed daily reward: {points} points")
        say(f"[green]{ctx.author} claimed daily reward: +{points} points")

    @commands.command(name="leaderboard", description="shows the leaderboard")
    async def leaderboard(self, ctx):
        top_users = get_leaderboard(10)
        
        if not top_users:
            await ctx.send("No scores yet! Use `!daily` to get started.")
            return
        
        embed = discord.Embed(title="Score Leaderboard", color=0x0000ff)
        
        leaderboard_text = ""
        for rank, (user_id, data) in enumerate(top_users, 1):
            total = data['total_score']
            leaderboard_text += f"{rank}. <@{user_id}> - {total} points\n"
        
        embed.description = leaderboard_text
        embed.set_footer(text="Use !daily to earn points! Use points to gamble.")
        
        await ctx.send(embed=embed)
        logging.info(f"{ctx.author} viewed the leaderboard")
        say(f"[green]{ctx.author} viewed the leaderboard")


class Gambling(commands.Cog): # gambling commands
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", description="rolls a dice")
    async def roll(self, ctx, sides: int = 6): # default to 6 sided dice
        import random
        if sides < 2:
            await ctx.send("Dice must have at least 2 sides.")
            logging.warning(f"{ctx.author} tried to roll a dice with invalid sides: {sides}")
            return
        if sides > 32:
            await ctx.send("Dice cannot have more than 32 sides.")
            logging.warning(f"{ctx.author} tried to roll a dice with too many sides: {sides}")
            return
        result = random.randint(1, sides)
        bonus: int = random.randint(1,6)
        scored = add_score(ctx.author.id, result + bonus) # dice side + bonus (a reroll kinda)
        embed = discord.Embed(title="Dice Roll", description=f"{ctx.author} rolled a {result} on a {sides}-sided dice.", color=0x00ff00)
        embed.add_field(name="Points Earned", value=f"+{scored}", inline=True)
        embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
        embed.set_footer(text=f"Calulated: {result} + {bonus} bonus points")
        await ctx.send(embed=embed)
        logging.info(f"{ctx.author} rolled a {result} on a {sides}-sided dice and earned {scored} points.")

    @commands.command(name="flip", description="flips a coin. Heads is win, tails is lose")
    async def flip(self, ctx, wager: int = 0):
        import random
        user_score = check_score(ctx.author.id)
        if user_score is None or user_score < wager: # check if user has enough points, would break the leaderboard otherwise
            await ctx.send("You don't have enough points to make that wager. (you'll go in debt lol)")
            logging.warning(f"{ctx.author} tried to flip a coin with insufficient points for wager: {wager}")
            return

        if wager <= 0: # must wager
            await ctx.send("please wager some points bro.")
            logging.warning(f"{ctx.author} tried to flip a coin with invalid wager: {wager}")
            return

        result = random.choice(["Heads", "Tails"])
        bonus = random.randint(1,15)
        scored = wager + bonus
        if result == "Heads":
            add_score(ctx.author.id, wager + bonus)
            embed = discord.Embed(title="Coin Flip", description=f"{ctx.author} won {scored} points!", color=0x00ff00) 
            embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            embed.set_footer(text=f"Score is calculated as amount wagered ({wager}) + {bonus} bonus points")
            await ctx.send(embed=embed)
        else:
            add_score(ctx.author.id, -wager)
            embed_fail = discord.Embed(title="Coin Flip", description=f"{ctx.author} lost {wager} points!", color=0xff0000)
            embed_fail.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            embed_fail.set_footer(text="oof you suck lol")
            await ctx.send(embed=embed_fail)
        logging.info(f"{ctx.author} flipped a coin and got {result}.")

    """
    @commands.command(name="spin", description="spins a roulette wheel")
    async def spin(self, ctx):
        import random
        result = random.randint(0, 36)
        colors = "Red" if result % 2 == 0 and result != 0 else "Black" if result % 2 == 1 else "Green"
        embed = discord.Embed(title="Roulette Spin", description=f"The ball landed on {result} ({colors})", color=0x00ff00)
        await ctx.send(embed=embed)
    """

bot.run(token, log_handler=handler, log_level=logging.INFO, root_logger=True)