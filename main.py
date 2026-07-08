import random
import discord
import os
import logging
import time
import asyncio
from dotenv import load_dotenv
from discord.ext import commands
from typing import Literal
import json
from datetime import datetime, timezone, timedelta

load_dotenv() # All of these need to be set in the .env file. If not, the bot will not run.
token = os.getenv('DISCORD_TOKEN')
guildId = int(os.getenv('guildId')) # Guild ID where the bot will run.
owner = int(os.getenv('owner')) # Bot Owner. Change it in the .env file.

reconnect = 0
handler = logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='w')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
activity = discord.Activity(type=discord.ActivityType.listening, name="TESTING BOT", details="TESTING TESTING") # bot
bot = commands.Bot(command_prefix='!', intents=intents, activity=activity, status=discord.Status.idle, help_command=None)

MY_GUILD = discord.Object(id=guildId)
SCORES_FILE = 'scores.json'

def say(message): # Because the logging handler can't do both console and log file at the same time, this function is used to print to both. Bloaty, I know.
    from rich import print
    print(f"[blue]BOT:[/blue] {message}")


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

def add_user(user_id): # adds a new user to scores.json, fallback if user doesn't exist
    scores = load_scores()
    user_id_str = str(user_id)
    
    if user_id_str not in scores: # JSON, all necessary fields are initialized to default values
        scores[user_id_str] = {
            'total_score': 0,
            'daily_debt': 0,
            'bonus_multiplier': 1,
            'dig': 0,
            'level': 1,
            'xp': 0,
            'last_daily_claimed': 0,
            'temporary_multiplier': {
                'value': 1.0,
                'expires_at': 0
            }
        }
        save_scores(scores)
        return True
    return False

def can_claim_daily(user_id): # function to check if user can claim daily points
    scores = load_scores()
    user_id_str = str(user_id)
    
    if user_id_str not in scores:
        return True
    
    today = datetime.now().strftime('%Y-%m-%d')
    last_claimed = scores[user_id_str].get('last_daily_claimed')
    
    return last_claimed != today

def scoreCheck(user_id): # checks if user exists in scores.json
    scores = load_scores()
    user_id_str = str(user_id)

    try:
        if user_id_str not in scores:
            add_user(user_id)
            return    
    except KeyError:
        logging.error(f"KeyError: User ID {user_id_str} not found in scores.")
        return False


def add_score(user_id, points): # modify a user's score
    scores = load_scores() # gets current scores
    user_id_str = str(user_id)
    
    if user_id_str not in scores:
        add_user(user_id)
    scores[user_id_str]['total_score'] += points
    
    save_scores(scores) # make sure to always save after modifying
    return points

def add_debt(user_id, points): # modify a user's daily debt
    scores = load_scores() # gets current scores
    user_id_str = str(user_id)

    if user_id_str not in scores:
        add_user(user_id)

    scores[user_id_str]['daily_debt'] += points
    save_scores(scores)
    return points

def add_bonus_multiplier(user_id, multiplier): # modify a user's bonus multiplier
    scores = load_scores() # gets current scores
    user_id_str = str(user_id)

    if user_id_str not in scores:
        add_user(user_id)

    scores[user_id_str]['bonus_multiplier'] = multiplier
    save_scores(scores)
    return multiplier

def check_score(user_id): # returns a user's score
    scores = load_scores()
    user_id_str = str(user_id)
    
    if user_id_str not in scores:
        add_user(user_id)
        scores = load_scores()

    return scores[user_id_str]['total_score']
    
def check_daily_loan(user_id):
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str not in scores:
        add_user(user_id)
        scores = load_scores()

    return scores[user_id_str]['daily_debt']


def check_hasDailyYet(user_id):
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str not in scores:
        add_user(user_id)
        scores = load_scores()

    last_claimed = scores[user_id_str].get('last_daily_claimed')
    today = datetime.now().strftime('%Y-%m-%d')
    if last_claimed == today:
        return False # has already claimed today
    else: # has not claimed today
        embed = discord.Embed(title="Daily Reminder", description="You have not claimed your daily points yet! Use `!daily` to claim them.", color=0xffff00)
        return embed

def check_debt(user_id):
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str not in scores:
        add_user(user_id)
        scores = load_scores()

    return scores[user_id_str]['daily_debt']

def check_bonus_multiplier(user_id): # because im too lazy to rewrite the function's name everywhere and miss something
    return get_effective_multiplier(user_id)


def get_effective_multiplier(user_id): # the permanent multiplier
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str not in scores:
        add_user(user_id)

    user_data = scores[user_id_str]
    base_multiplier = float(user_data.get('bonus_multiplier', 1))
    temp = user_data.get('temporary_multiplier', {'value': 1.0, 'expires_at': 0})
    expires_at = int(temp.get('expires_at', 0) or 0)
    now = int(datetime.utcnow().timestamp())

    if expires_at > now:
        return base_multiplier * float(temp.get('value', 1.0))

    if temp.get('value', 1.0) != 1.0:
        user_data['temporary_multiplier'] = {'value': 1.0, 'expires_at': 0}
        save_scores(scores)

    return base_multiplier


def set_temporary_multiplier(user_id, multiplier_value, duration_seconds): # temporary shop multiplier, expires after duration_seconds
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str not in scores:
        add_user(user_id)
        scores = load_scores()

    expires_at = int(datetime.utcnow().timestamp()) + int(duration_seconds)
    scores[user_id_str]['temporary_multiplier'] = {
        'value': float(multiplier_value),
        'expires_at': expires_at
    }
    save_scores(scores)
    return expires_at


########### LEVELS

MAX_LEVEL = 50 # maximum level a user can reach, aka level cap


def xp_required_for_level(level):
    if level >= MAX_LEVEL:
        return 0
    # each new level requires 30-50 more XP than the previous level:
    # level 1 -> 2 = 100, level 2 -> 3 = 150, level 3 -> 4 = 180, etc.
    return 100 + 40 * (level - 1) + 10 * ((level - 1) % 2)


def add_xp(user_id, amount):
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str not in scores:
        add_user(user_id)
        scores = load_scores()

    user_data = scores[user_id_str]
    level = int(user_data.get('level', 1))
    xp = int(user_data.get('xp', 0))
    leveled_up = 0

    if level >= MAX_LEVEL:
        return {
            'gained': 0,
            'leveled_up': 0,
            'level': MAX_LEVEL,
            'xp': 0,
            'next_level_xp': 0
        }

    xp += int(amount)
    while level < MAX_LEVEL: # Stop progressing if reached max level
        required = xp_required_for_level(level)
        if xp < required:
            break
        xp -= required
        level += 1
        leveled_up += 1

    if level >= MAX_LEVEL:
        level = MAX_LEVEL
        xp = 0

    user_data['xp'] = xp
    user_data['level'] = level
    save_scores(scores)

    return {
        'gained': int(amount) if level < MAX_LEVEL else 0,
        'leveled_up': leveled_up,
        'level': level,
        'xp': xp,
        'next_level_xp': xp_required_for_level(level)
    }


def get_xp_progress(user_id):
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str not in scores:
        add_user(user_id)
        scores = load_scores()

    user_data = scores[user_id_str]
    level = int(user_data.get('level', 1))
    xp = int(user_data.get('xp', 0))
    next_level = xp_required_for_level(level)
    return level, xp, next_level


def get_multiplier_status(user_id):
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str not in scores:
        add_user(user_id)
        scores = load_scores()

    temp = scores[user_id_str].get('temporary_multiplier', {'value': 1.0, 'expires_at': 0})
    expires_at = int(temp.get('expires_at', 0) or 0)
    now = int(datetime.utcnow().timestamp())

    if expires_at > now and float(temp.get('value', 1.0)) > 1.0:
        remaining = expires_at - now
        return float(temp['value']), remaining

    return 1.0, 0


def format_duration(seconds):
    seconds = int(seconds)
    if seconds <= 0:
        return "0s"
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if sec:
        parts.append(f"{sec}s")
    return " ".join(parts)


def get_leaderboard(limit=10): # returns top 10 users by score
    scores = load_scores()
    sorted_users = sorted(scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
    return sorted_users[:limit]

def calc_bonus(user_id, limit, multiplier=None):
    # Use provided multiplier if given, otherwise fetch user's multiplier
    if multiplier is None:
        multiplier = check_bonus_multiplier(user_id=user_id)
    limit_calc = random.randint(1, limit)
    return limit_calc, multiplier

def get_dig(user_id): # basically how much stamina or shovel's durability. maximum 5. (see down below.)
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str not in scores:
        add_user(user_id)
        scores = load_scores()

    return scores[user_id_str].get('dig', 0)

def set_dig(user_id, value): # sets the dig value for a user
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str not in scores:
        add_user(user_id)
        scores = load_scores()

    scores[user_id_str]['dig'] = value  
    save_scores(scores)
    return scores[user_id_str]['dig']

# pending trivia questions: message_id -> {author, correct, answers, wager}
TRIVIA_PENDING = {}

################

@bot.event
async def on_ready():
    assert bot.user is not None
    say("               ")
    say("[green][bold]----------------------------")
    say(f'[green]logged in as {bot.user}')
    say("[green][bold]----------------------------")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown): # Command cooldown (ratelimits)
            embed = discord.Embed(
                title="Command on Cooldown",
                description=f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=0xff0000
            )
    else: # Other errors, bugs, etc.
        embed = discord.Embed(title="Error", description="An error occurred while processing the command.", color=0xff0000)
        embed.add_field(name="Details", value=str(error), inline=False)
        embed.set_footer(text="ping scotty for this")
        say(f"[red]Error: {error}")
        logging.error(f"Error processing command from {ctx.author}: {error}")

@bot.hybrid_command(name="help", description="shows this message")
@discord.app_commands.describe(type="Choose a help category")
async def help(ctx, type: Literal["general", "social", "gambling", "admin", "fun"] = None):
    say(f"Help command called by [blue]{ctx.author} with type: {type}")
    if type is None:
        embed = discord.Embed(title="Help Menu", description="List of available commands:", color=0x00ff00)
        embed.add_field(name="!sync", value="Syncs slash commands.", inline=False)
        embed.add_field(name="!ping", value="Checks the bot's latency.", inline=False)
        embed.add_field(name="!pin <message_id>", value="Pins a message to the announcements channel.", inline=False)
        embed.add_field(name="!source", value="Shows the bot source code link.", inline=False)
        embed.set_footer(text="created by ScottyFM. help categories: admin, social, gambling, fun")
        await ctx.reply(embed=embed)
        say(f"[green]Displayed general help menu to {ctx.author}")
        logging.info(f"Displayed general help menu to {ctx.author}")

    if type == "social":
        embed = discord.Embed(title="Social Help Menu", description="List of social commands:", color=0x0000ff)
        embed.add_field(name="!daily", value="Gives daily points. Used in gambling.", inline=False)
        embed.add_field(name="!leaderboard", value="Shows the total points leaderboard.", inline=False)
        embed.add_field(name="!loan <amount>", value="Takes a loan of points (max 3000).", inline=False)
        embed.add_field(name="!paydebt <amount>", value="Pays off debt.", inline=False)
        embed.add_field(name="!donate <user> <amount>", value="Donates points to another user.", inline=False)
        embed.add_field(name="!stats [user]", value="Shows your or another user's score stats.", inline=False)
        embed.add_field(name="!shop", value="Brings up the multiplier shop.", inline=False)
        embed.set_footer(text="created by ScottyFM. help categories: admin, social, gambling")
        await ctx.reply(embed=embed)
        say(f"[green]Displayed social help menu to {ctx.author}")
        logging.info(f"Displayed social help menu to {ctx.author}")

    if type == "gambling":
        embed = discord.Embed(title="Gambling Help Menu", description="List of gambling commands:", color=0xffff00)
        embed.add_field(name="!roll <wager> <sides>", value="Rolls a dice and risks your points.", inline=False)
        embed.add_field(name="!flip <wager> <side>", value="Flips a coin. Bet on heads or tails.", inline=False)
        embed.add_field(name="!spin <wager> <color>", value="Spins a roulette wheel. Bet on red or black.", inline=False)
        embed.set_footer(text="created by ScottyFM. help categories: admin, social, gambling, fun")
        await ctx.reply(embed=embed)
        say(f"[green]Displayed gambling help menu to {ctx.author}")
        logging.info(f"Displayed gambling help menu to {ctx.author}")

    if type == "fun":
        embed = discord.Embed(title="Fun Help Menu", description="List of fun commands:", color=0xFF6B6B)
        embed.add_field(name="!joke", value="Tells a random joke.", inline=False)
        embed.add_field(name="!dex <word>", value="Looks up a word on Urban Dictionary.", inline=False)
        embed.add_field(name="!magic8ball <question>", value="Ask the magic 8-ball a question.", inline=False)
        embed.add_field(name="!trivia <wager>", value="Answer a trivia question and wager points.", inline=False)
        embed.add_field(name="!meme [top_text] [bottom_text]", value="Generate a random meme.", inline=False)
        embed.set_footer(text="created by ScottyFM. help categories: admin, social, gambling, fun")
        await ctx.reply(embed=embed)
        say(f"[green]Displayed fun help menu to {ctx.author}")
        logging.info(f"Displayed fun help menu to {ctx.author}")

    if type == "admin":
        embed = discord.Embed(title="Admin Help Menu", description="List of admin commands:", color=0xff0000)
        embed.add_field(name="!createrules <title> <description>", value="Creates the server rules embed.", inline=False)
        embed.add_field(name="!enlist <user> <role_type>", value="Enlists a user into the server with specified role type (friends, member, trusted).", inline=False)
        embed.add_field(name="!stop", value="Stops the bot (owner only).", inline=False)
        embed.set_footer(text="created by ScottyFM. help categories: admin, social, gambling")
        await ctx.reply(embed=embed)
        say(f"[green]Displayed admin help menu to {ctx.author}")
        logging.info(f"Displayed admin help menu to {ctx.author}")

    elif type not in [None, "social", "gambling", "admin", "fun"]:
        await ctx.reply("you have a stroke? it's `!help`.")
        say(f"[red]{ctx.author} provided invalid help type: {type}")
        logging.warning(f"{ctx.author} provided invalid help type: {type}")

@bot.hybrid_command(name="about", description="shows info about the bot")
async def about(ctx):
    say(f"About command called by [blue]{ctx.author}")
    logging.info(f"About command used by {ctx.author}")
    embed = discord.Embed(title="about", description="i was spawncamped!", color=0x0000ff)
    embed.add_field(name="made by", value="ScottyFM", inline=False)
    embed.add_field(name="", value="do `!source` for github repo", inline=False)
    # embed.set_footer(timestamp=ctx.message.created_at) this one brokey

    #todo: add system stats like uptime, latency, version, platform, etc.

    await ctx.reply(embed=embed)


@bot.hybrid_command(name="source", description="shows the bot source code link")
async def source(ctx):
    say(f"Source command called by [blue]{ctx.author}")
    await ctx.reply("You can find my source code [here](https://github.com/ScottN13/spawncamped)")
    logging.info(f"Provided source code link to {ctx.author}")

@bot.hybrid_command(name="createrules", description="creates the server rules embed")
async def createrules(ctx, title, *, description):
    rules = bot.get_channel(1433865285097619546) # Rules channel ID
    say(f"CreateRules command called by [blue]{ctx.author}")
    # ctx.message may be None for slash invocations; fall back to current time
    created = getattr(ctx, 'message', None)
    timestamp = created.created_at if created is not None else datetime.utcnow()
    embed = discord.Embed(title=title, description=description, color=0xff0000, timestamp=timestamp)
    embed.set_footer(text="By joining the server, you agree to these rules.")
    try:
        # await discord.TextChannel.send(id=rules, embed=embed) # Rules channel ID # this doesnt send it to the rules channel for some reason
        await rules.send(embed=embed)
        await ctx.reply("Done, i created the rules embed.")
        logging.info(f"Created rules embed for {ctx.author} with contents: {title} - {description}")
    except Exception as e:
        await ctx.reply(f"error: {e}")
        say(f"[red]Error: {e}") 
        logging.error(f"Error creating rules embed for {ctx.author}: {e}")

@bot.hybrid_command(name="sync", description="syncs slash commands")
async def sync(ctx):
    # Ensure cogs are added before syncing so their hybrid/slash commands are registered
    await bot.add_cog(Social(bot))
    await bot.add_cog(leaderboard(bot))
    await bot.add_cog(Gambling(bot))
    await bot.add_cog(Fun(bot))
    await bot.add_cog(Utility(bot))
    bot.tree.copy_global_to(guild=discord.Object(id=1433854304678318183))
    synced = await bot.tree.sync(guild=discord.Object(id=1433854304678318183))
    await ctx.reply(f"{len(synced)} Slash commands synced. Enabled cogs.")
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
        say(f"Shutdown command issued by {ctx.author}")
        await ctx.reply("*ok*")
        logging.info(f"stopped by {ctx.author}")
        await bot.close()
   else:
     await ctx.reply("Foolish mortal, you do not have permission to do that.")
     logging.info(f"{ctx.author} tried to stop bot")
     say(f"{ctx.author} tried to stop bot")

@bot.hybrid_command(name="enlist", description="enlists a user into the server") # this command is specific to my server, as we change the name of the roles alot.
async def enlist(ctx, receiever: discord.Member, role_type: str):  # Rewrite to discord.Role
    # looks up both roles 
    member = discord.utils.get(ctx.guild.roles, id=1433856941163282637) 
    friends = discord.utils.get(ctx.guild.roles, id=1433856406406303776)
    trusted = discord.utils.get(ctx.guild.roles, id=1433854562875215972)
    role_type = role_type.lower()

    if ctx.author.id == owner: # checks if its me or BBQ
        if role_type in ["friends", "friend"]:
            try: 
                await receiever.add_roles(member)
                await receiever.add_roles(friends)
                await ctx.reply(f"Done, verified {receiever} to the server (friend privileges).")
                logging.info(f"{ctx.author} granted {role_type} role to {receiever}")
                say(f"[green]{ctx.author} granted {role_type} role to {receiever}")
            except Exception as e:
                await ctx.reply(f"An error occurred: {e}")
                say(f"[red]Error: {e}")
                logging.error(f"Error: {e}")

        elif role_type in ["member", "members"]:
            try: 
                await receiever.add_roles(member)
                await ctx.reply(f"Done, verified {receiever} to the server.")
                logging.info(f"{ctx.author} granted {role_type} role to {receiever}")
                say(f"[green]{ctx.author} granted {role_type} role to {receiever}")
            except Exception as e:
                await ctx.reply(f"An error occurred: {e}")
                say(f"[red]Error: {e}")
                logging.error(f"Error: {e}")
                
        elif role_type == "trusted":
            try:
                await receiever.add_roles(member)
                await receiever.add_roles(friends)
                await receiever.add_roles(trusted)
                await ctx.reply(f"Done, entrusted {receiever}.")
                logging.info(f"{ctx.author} granted {role_type} role to {receiever}")
                say(f"[green]{ctx.author} granted {role_type} role to {receiever}")
            except Exception as e:
                await ctx.reply(f"An error occurred: {e}")
                say(f"[red]Error: {e}")
                logging.error(f"Error: {e}")

        elif role_type not in ["friends", "friend", "member", "members", "trusted"]:
            await ctx.reply(f"I don't know what `{role_type}` means. Maybe you made a typo?")
            logging.warning(f"{ctx.author} tried verifying {receiever} with provided invalid role type: {role_type}")

    else:
        await ctx.reply("You have no permission to do that!")
        say(f"[red]{ctx.author} just tried to auto verify someone!")
        logging.warning(f"{ctx.author} tried to enlist {receiever} with role type: {role_type} without permission")

@bot.hybrid_command(name="pin", description="makes the bot pin a message to annoucements channel")
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

class ConfirmView(discord.ui.View):
    def __init__(self, purchase_type: str, cost: int, purchaser_id: int, multiplier_value: float = None, duration_seconds: int = None, stamina_amount: int = None):
        super().__init__(timeout=120)
        self.purchase_type = purchase_type
        self.cost = int(cost)
        self.purchaser_id = int(purchaser_id)
        self.multiplier_value = multiplier_value
        self.duration_seconds = duration_seconds
        self.stamina_amount = stamina_amount

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.purchaser_id:
            await interaction.response.send_message("You did not initiate this purchase.", ephemeral=True)
            return

        user_id = interaction.user.id
        user_score = check_score(user_id)
        if user_score is None or user_score < self.cost:
            await interaction.response.edit_message(embed=discord.Embed(title="Purchase Failed", description=f"You do not have enough points (need {self.cost}).", color=0xff0000), view=None)
            return

        if self.purchase_type == 'multiplier':
            expires_at = set_temporary_multiplier(user_id, float(self.multiplier_value), int(self.duration_seconds))
            add_score(user_id, -self.cost)
            embed = discord.Embed(title="Purchase Complete", description=f"You bought a temporary {self.multiplier_value}x multiplier.", color=0xffff00)
            embed.add_field(name="Multiplier", value=f"{self.multiplier_value}x", inline=True)
            embed.add_field(name="Duration", value=f"{format_duration(self.duration_seconds)}", inline=True)
            embed.add_field(name="Expires At", value=f"<t:{expires_at}:F>", inline=False)
            await interaction.response.edit_message(embed=embed, view=None)
            logging.info(f"{interaction.user} purchased {self.multiplier_value}x temporary multiplier for {self.cost} points")

        elif self.purchase_type == 'dig':
            current = get_dig(user_id) or 0
            new = current + int(self.stamina_amount)
            set_dig(user_id, new)
            add_score(user_id, -self.cost)
            embed = discord.Embed(title="Dig Stamina Purchased", description=f"You purchased +{self.stamina_amount} stamina. Current stamina: {new}", color=0x00ff00)
            await interaction.response.edit_message(embed=embed, view=None)
            logging.info(f"{interaction.user} purchased +{self.stamina_amount} dig stamina (now {new}) for {self.cost} points")

        else:
            await interaction.response.edit_message(content="Unknown purchase type.", view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.purchaser_id:
            await interaction.response.send_message("You did not initiate this purchase.", ephemeral=True)
            return
        await interaction.response.edit_message(content="Purchase cancelled.", embed=None, view=None)
        logging.info(f"{interaction.user} cancelled a purchase confirmation")

    async def on_timeout(self):
        try:
            # disable buttons to prevent further interaction
            for child in self.children:
                child.disabled = True

            if hasattr(self, 'message') and self.message:
                try:
                    await self.message.edit(content="Purchase timed out.", embed=None, view=self)
                except Exception:
                    pass
        except Exception:
            pass

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
    
    @discord.ui.button(label="Buy 1.1x (100)", style=discord.ButtonStyle.green, custom_id="buy_1.1")
    async def buy_1_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        user_score = check_score(user_id)
        
        if user_score is None or user_score < 100:
            await interaction.response.send_message("You don't have enough points (need 100).", ephemeral=True)
            logging.warning(f"{interaction.user} tried to buy 1.1x multiplier with insufficient points")
            return

        # send ephemeral confirmation
        confirm_embed = discord.Embed(title="Confirm Purchase", description="Buy temporary 1.1x multiplier for 100 points?", color=0xffff00)
        confirm_embed.add_field(name="Multiplier", value="1.1x", inline=True)
        confirm_embed.add_field(name="Duration", value="1 hour", inline=True)
        await interaction.response.send_message(embed=confirm_embed, view=ConfirmView(purchase_type='multiplier', cost=100, multiplier_value=1.1, duration_seconds=60*60, purchaser_id=user_id), ephemeral=True)
    
    @discord.ui.button(label="Buy 1.25x (300)", style=discord.ButtonStyle.green, custom_id="buy_1.25")
    async def buy_1_25(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        user_score = check_score(user_id)
        
        if user_score is None or user_score < 300:
            await interaction.response.send_message("You don't have enough points (need 300).", ephemeral=True)
            logging.warning(f"{interaction.user} tried to buy 1.25x multiplier with insufficient points")
            return

        confirm_embed = discord.Embed(title="Confirm Purchase", description="Buy temporary 1.25x multiplier for 300 points?", color=0xffff00)
        confirm_embed.add_field(name="Multiplier", value="1.25x", inline=True)
        confirm_embed.add_field(name="Duration", value="2 hours", inline=True)
        await interaction.response.send_message(embed=confirm_embed, view=ConfirmView(purchase_type='multiplier', cost=300, multiplier_value=1.25, duration_seconds=2*60*60, purchaser_id=user_id), ephemeral=True)
    
    @discord.ui.button(label="Buy 1.5x (500)", style=discord.ButtonStyle.green, custom_id="buy_1.5")
    async def buy_1_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        user_score = check_score(user_id)
        
        if user_score is None or user_score < 500:
            await interaction.response.send_message("You don't have enough points (need 500).", ephemeral=True)
            logging.warning(f"{interaction.user} tried to buy 1.5x multiplier with insufficient points")
            return

        confirm_embed = discord.Embed(title="Confirm Purchase", description="Buy temporary 1.5x multiplier for 500 points?", color=0xffff00)
        confirm_embed.add_field(name="Multiplier", value="1.5x", inline=True)
        confirm_embed.add_field(name="Duration", value="3 hours", inline=True)
        await interaction.response.send_message(embed=confirm_embed, view=ConfirmView(purchase_type='multiplier', cost=500, multiplier_value=1.5, duration_seconds=3*60*60, purchaser_id=user_id), ephemeral=True)


class ShopMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Multipliers", style=discord.ButtonStyle.primary, custom_id="shop_multipliers")
    async def multipliers(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Multiplier Shop", description="Buy temporary multipliers to increase your earnings!", color=0xffff00)
        embed.add_field(name="1.1x Multiplier", value="Cost: 100 points — Duration: 1 hour", inline=False)
        embed.add_field(name="1.25x Multiplier", value="Cost: 300 points — Duration: 2 hours", inline=False)
        embed.add_field(name="1.5x Multiplier", value="Cost: 500 points — Duration: 3 hours", inline=False)
        await interaction.response.edit_message(embed=embed, view=ShopView())

    @discord.ui.button(label="Dig Stamina", style=discord.ButtonStyle.secondary, custom_id="shop_dig")
    async def dig_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Dig Stamina Shop", description="Buy shovels/stamina to dig for treasure.", color=0x00ff00)
        embed.add_field(name="+1 Stamina", value="Cost: 50 points — Adds 1 stamina", inline=False)
        embed.add_field(name="+3 Stamina", value="Cost: 120 points — Adds 3 stamina", inline=False)
        await interaction.response.edit_message(embed=embed, view=DigShopView())

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, custom_id="shop_close")
    async def close_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Shop closed.", embed=None, view=None)
        logging.info(f"{interaction.user} closed the shop")


class DigShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Buy +1 Stamina (50)", style=discord.ButtonStyle.green, custom_id="buy_dig_1")
    async def buy_dig_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        user_score = check_score(user_id)
        if user_score is None or user_score < 50:
            await interaction.response.send_message("You don't have enough points (need 50).", ephemeral=True)
            return

        confirm_embed = discord.Embed(title="Confirm Purchase", description="Buy +1 Stamina for 50 points?", color=0x00ff00)
        confirm_embed.add_field(name="Amount", value="+1 Stamina", inline=True)
        await interaction.response.send_message(embed=confirm_embed, view=ConfirmView(purchase_type='dig', cost=50, stamina_amount=1, purchaser_id=user_id), ephemeral=True)

    @discord.ui.button(label="Buy +3 Stamina (120)", style=discord.ButtonStyle.green, custom_id="buy_dig_3")
    async def buy_dig_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        user_score = check_score(user_id)
        if user_score is None or user_score < 120:
            await interaction.response.send_message("You don't have enough points (need 120).", ephemeral=True)
            return

        confirm_embed = discord.Embed(title="Confirm Purchase", description="Buy +3 Stamina for 120 points?", color=0x00ff00)
        confirm_embed.add_field(name="Amount", value="+3 Stamina", inline=True)
        await interaction.response.send_message(embed=confirm_embed, view=ConfirmView(purchase_type='dig', cost=120, stamina_amount=3, purchaser_id=user_id), ephemeral=True)

class Social(commands.Cog): # Social stuff for servers 
    def __init__(self, bot):
        self.bot = bot

    # tbd.

class leaderboard(commands.Cog): # i seperated these for organization
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="daily", description="gives daily points")
    async def daily(self, ctx):
        if not can_claim_daily(ctx.author.id):
            await ctx.send(f"You already claimed your daily points.")
            logging.info(f"{ctx.author} tried to claim daily reward twice in one day")
            return
        
        limit_calc, multiplier = calc_bonus(user_id=ctx.author.id, limit=50, multiplier=check_bonus_multiplier(ctx.author.id))

        points = 100 # Daily points
        bonus = int(limit_calc * multiplier)
        add_score(ctx.author.id, points + bonus) # add total points to user's score
        xp_result = add_xp(ctx.author.id, 20) # add xp
        # mark last daily claimed
        scores = load_scores()
        scores[str(ctx.author.id)]['last_daily_claimed'] = datetime.now().strftime('%Y-%m-%d')
        save_scores(scores)
        
        scores = load_scores()
        total = scores[str(ctx.author.id)]['total_score']
        
        embed = discord.Embed(title="Daily Reward Claimed!", color=0x00ff00)
        embed.add_field(name="Points Earned", value=f"+{points+bonus} (100 + {bonus})", inline=True)
        embed.add_field(name="Total Score", value=total, inline=True)
        embed.add_field(name="XP Earned", value=f"+{xp_result['gained']} XP", inline=False)
        embed.add_field(name="Level", value=f"{xp_result['level']} ({xp_result['xp']}/{xp_result['next_level_xp']} XP)", inline=False)
        if xp_result['leveled_up'] > 0:
            embed.add_field(name="Level Up!", value=f"You advanced to level {xp_result['level']}!", inline=False)
        embed.set_footer(text="come back tomorrow for more!")
        
        await ctx.send(embed=embed)
        logging.info(f"{ctx.author} claimed daily reward: {points} points")
        say(f"[green]{ctx.author} claimed daily reward: +{points} points")

    @commands.hybrid_command(name="leaderboard", description="shows the leaderboard")
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

    @commands.hybrid_command(name="loan", description="takes a loan of points")
    async def loan(self, ctx, amount: int):
        if amount <= 0:
            await ctx.send("Loan amount must be positive.")
            logging.warning(f"{ctx.author} tried to take a loan with invalid amount: {amount}")
            return
        if amount > 3000:
            await ctx.send("You can't scam me out of 3000 points.")
            logging.warning(f"{ctx.author} tried to take a loan exceeding limit: {amount}")
            return
        
        # amount is how much you want to loan
        # score is user's current score
        # debt is user's current debt

        score = check_score(ctx.author.id)
        debt = check_debt(ctx.author.id)

        if debt is not None and debt > score * 2:
            await ctx.send("You cannot take a loan that exceeds double your current score in debt. **Pay off!**")
            logging.warning(f"{ctx.author} tried to take a loan exceeding debt limit: {amount}")
            return 
        else:
            add_score(ctx.author.id, amount)
            add_debt(ctx.author.id, amount)
            embed = discord.Embed(title="Banker - Loans", description=f"You have taken a loan of {amount} points.", color=0x00ff00)
            embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            embed.add_field(name="Your total debt:", value=f"{check_debt(ctx.author.id)}", inline=True)
            await ctx.send(embed=embed)
            logging.info(f"{ctx.author} took a loan of {amount} points")
            return

    @commands.hybrid_command(name="paydebt", description="pays off debt")
    async def paydebt(self, ctx, amount: int):
        debt = check_debt(ctx.author.id)
        score = check_score(ctx.author.id)

        if amount is None:
            amount = debt

        if debt is None or debt <= 0:
            await ctx.send("You have no debt to pay off. :)")
            logging.info(f"{ctx.author} tried to pay debt but has none")
            return

        if amount <= 0:
            await ctx.send("tf you want me to do with 0 money")
            logging.warning(f"{ctx.author} tried to pay debt with invalid amount: {amount}")
            return

        if amount is None:
            debt = check_debt(ctx.author.id)
            add_score(ctx.author.id, -debt)
            add_debt(ctx.author.id, -debt)
            embed = discord.Embed(title="Banker - Debt Payment", description=f"You have paid off all of your debt ({debt} points).", color=0x00ff00)
            await ctx.send(embed=embed)
            logging.info(f"{ctx.author} paid off all of their debt: {debt} points")
            return

        else:
            add_score(ctx.author.id, -amount)
            add_debt(ctx.author.id, -amount)
            embed = discord.Embed(title="Banker - Debt Payment", description=f"You have paid off {amount} points of your debt.", color=0x00ff00)
            await ctx.send(embed=embed)
            logging.info(f"{ctx.author} paid off {amount} points of their debt")
            return

    @commands.hybrid_command(name="donate", description="donates points to another user")
    async def donate(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            await ctx.send("tf do they wanna do with NO points?")
            logging.warning(f"{ctx.author} tried to donate invalid amount: {amount}")
            return

        score = check_score(ctx.author.id)
        if score is None or score < amount:
            await ctx.send("lol u poor. earn more points")
            logging.warning(f"{ctx.author} tried to donate {amount} points with insufficient score")
            return

        else:
            add_score(ctx.author.id, -amount)
            add_score(member.id, amount)
            embed = discord.Embed(title="You donated!", description=f"You have donated {amount} points to {member}.", color=0x00ff00)
            embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            embed.set_footer(text="wow you're kind :)")
            await ctx.send(embed=embed)
            logging.info(f"{ctx.author} donated {amount} points to {member}")

    @commands.hybrid_command(name="stats", description="shows your score stats")
    async def stats(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        target_id = target.id

        score = check_score(target_id)
        debt = check_debt(target_id)

        if score is None:
            if member is None:
                await ctx.send("You have no score yet. Use `!daily` to start earning points!")
                logging.info(f"{ctx.author} checked stats with no score")
            else:
                await ctx.send(f"{member} has no score yet.")
                logging.info(f"{ctx.author} checked stats of {member} with no score")
            return

        level, xp, next_level = get_xp_progress(target_id)
        temp_mult, remaining = get_multiplier_status(target_id)
        effective = check_bonus_multiplier(target_id)

        display_xp = "MAX" if level >= MAX_LEVEL else f"{xp}/{next_level}"
        temp_text = f"{temp_mult:.2f}x for {format_duration(remaining)}" if remaining > 0 else "None active"

        avatar_url = None
        if getattr(target, 'avatar', None):
            avatar_url = target.avatar.url
        else:
            avatar_url = target.default_avatar.url

        embed = discord.Embed(
            title=f"{target.display_name}'s Stats",
            description=f"Statistics for {target.mention}",
            color=0x0000ff
        )

        xp_result = get_xp_progress(ctx.author.id)

        embed.set_author(name=target.display_name, icon_url=avatar_url)
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="Total Score", value=f"{score} points", inline=True)
        embed.add_field(name="Total Debt", value=f"{debt} points", inline=True)
        embed.add_field(name="Level", value=f"{level}{' (MAX)' if level >= MAX_LEVEL else f''}", inline=False)
        embed.add_field(name="Permanent Multiplier", value=f"{effective:.2f}x", inline=True)
        embed.add_field(name="Temporary Multiplier", value=temp_text, inline=False)
        embed.set_footer(text="Use !daily to earn more points! Use points to gamble.")

        await ctx.send(embed=embed)
        if member is None:
            logging.info(f"{ctx.author} viewed their score stats")
        else:
            logging.info(f"{ctx.author} viewed {member}'s score stats")

    @commands.hybrid_command(name="shop", description="shows the multiplier shop")
    async def shop(self, ctx):
        embed = discord.Embed(title="Shop", description="Welcome to the shop — select a category below to browse items.", color=0xffff00)
        embed.add_field(name="Categories", value="• Multipliers\n• Dig Stamina", inline=False)

        view = ShopMainView()
        await ctx.send(embed=embed, view=view)
        logging.info(f"{ctx.author} viewed the shop")

class Gambling(commands.Cog): # gambling commands
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="roll", description="rolls a dice (wager, sides)")
    async def roll(self, ctx, wager: int = 1, sides: int = 6): # default to 1 point wager, 6 sided dice
        import random
        import math

        user_score = check_score(ctx.author.id)
        if user_score is None or user_score < wager:
            await ctx.send("You don't have enough points to make that wager.")
            logging.warning(f"{ctx.author} tried to roll dice with insufficient points for wager: {wager}")
            return

        if wager <= 0:
            await ctx.send("Please wager a positive number of points.")
            logging.warning(f"{ctx.author} tried to roll with invalid wager: {wager}")
            return

        if sides < 2:
            await ctx.send("Dice must have at least 2 sides.")
            logging.warning(f"{ctx.author} tried to roll a dice with invalid sides: {sides}")
            return
        if sides > 32:
            await ctx.send("Dice cannot have more than 32 sides.")
            logging.warning(f"{ctx.author} tried to roll a dice with too many sides: {sides}")
            return

        # fair odds: probability to win is number of outcomes > sides/2
        wins = sides - (sides // 2)
        losses = sides - wins
        p_win = wins / sides

        result = random.randint(1, sides)

        # base fair profit for a win so expected value ~ 0: profit = wager * (losses / wins)
        base_profit = max(1, int(round(wager * (losses / wins))))

        # optional bonus from shop (keeps small extra player benefit)
        limit_calc, multiplier = calc_bonus(user_id=ctx.author.id, limit=sides//2, multiplier=check_bonus_multiplier(ctx.author.id))
        bonus = int(limit_calc * multiplier)

        profit = base_profit + bonus

        if result > sides / 2:  # player wins
            add_score(ctx.author.id, profit)
            xp_result = add_xp(ctx.author.id, 10)
            embed = discord.Embed(title="Dice Roll", description=f"{ctx.author} rolled a {result} on a {sides}-sided dice and won!", color=0x00ff00)
            embed.add_field(name="Points Earned", value=f"+{profit}", inline=True)
            embed.add_field(name="XP Earned", value=f"+{xp_result['gained']} XP", inline=True)
            embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            if xp_result['leveled_up'] > 0:
                embed.add_field(name="Level Up!", value=f"You reached level {xp_result['level']}!", inline=False)
            embed.set_footer(text=f"Fair payout: profit={base_profit}, bonus={bonus}")
            await ctx.send(embed=embed)
            logging.info(f"{ctx.author} rolled a {result} on a {sides}-sided dice and won {profit} points.")
            return
        else:
            add_score(ctx.author.id, -wager)
            xp_result = add_xp(ctx.author.id, 3)
            embed = discord.Embed(title="Dice Roll", description=f"{ctx.author} rolled a {result} on a {sides}-sided dice and lost.", color=0xffff00)
            embed.add_field(name="Points Lost", value=f"{wager}", inline=True)
            embed.add_field(name="XP Earned", value=f"+{xp_result['gained']} XP", inline=True)
            embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            if xp_result['leveled_up'] > 0:
                embed.add_field(name="Level Up!", value=f"You reached level {xp_result['level']}!", inline=False)
            embed.set_footer(text="Better luck next time")
            await ctx.send(embed=embed)
            logging.info(f"{ctx.author} rolled a {result} on a {sides}-sided dice and lost {wager} points.")
            return

    @commands.hybrid_command(name="flip", description="flips a coin. wager and pick heads/tails")
    async def flip(self, ctx , wager: int = 1, side: str = "heads"): 
        import random
        user_score = check_score(ctx.author.id)
        if user_score is None or user_score < wager:
            await ctx.send("You don't have enough points to make that wager.")
            logging.warning(f"{ctx.author} tried to flip a coin with insufficient points for wager: {wager}")
            return

        if wager <= 0:
            await ctx.send("Please wager a positive number of points.")
            logging.warning(f"{ctx.author} tried to flip a coin with invalid wager: {wager}")
            return

        side_choice = side.lower()
        if side_choice not in ["heads", "tails"]:
            await ctx.send("Choose 'heads' or 'tails' as your side.")
            logging.warning(f"{ctx.author} tried to flip with invalid side: {side}")
            return

        result = random.choice(["heads", "tails"])

        # fair coin: p=0.5 -> profit = wager (winning doubles)
        base_profit = max(1, int(round(wager)))
        limit_calc, multiplier = calc_bonus(user_id=ctx.author.id, limit=50, multiplier=check_bonus_multiplier(ctx.author.id))
        bonus = int(limit_calc * multiplier)
        profit = base_profit + bonus

        if result == side_choice:
            add_score(ctx.author.id, profit)
            xp_result = add_xp(ctx.author.id, 10)
            embed = discord.Embed(title=f"Coin Flip - {result.capitalize()}", description=f"{ctx.author} won {profit} points!", color=0x00ff00)
            embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            embed.add_field(name="XP Earned", value=f"+{xp_result['gained']} XP", inline=True)
            if xp_result['leveled_up'] > 0:
                embed.add_field(name="Level Up!", value=f"You reached level {xp_result['level']}!", inline=False)
            embed.set_footer(text=f"Fair payout: profit={base_profit}, bonus={bonus}")
            await ctx.send(embed=embed)
        else:
            add_score(ctx.author.id, -wager)
            xp_result = add_xp(ctx.author.id, 3)
            embed_fail = discord.Embed(title=f"Coin Flip - {result.capitalize()}", description=f"{ctx.author} lost {wager} points!", color=0xff0000)
            embed_fail.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            embed_fail.add_field(name="XP Earned", value=f"+{xp_result['gained']} XP", inline=True)
            if xp_result['leveled_up'] > 0:
                embed_fail.add_field(name="Level Up!", value=f"You reached level {xp_result['level']}!", inline=False)
            embed_fail.set_footer(text="Better luck next time")
            await ctx.send(embed=embed_fail)

        logging.info(f"{ctx.author} flipped a coin and got {result}.")
        return


    @commands.hybrid_command(name="spin", description="spins a roulette wheel (wager, red/black)")
    async def spin(self, ctx, wager: int = 1, color: str = "red"):
        import random
        user_score = check_score(ctx.author.id)

        if user_score is None or user_score < wager:
            await ctx.send("You don't have enough points to make that wager.")
            logging.warning(f"{ctx.author} tried to spin with insufficient points for wager: {wager}")
            return

        if wager <= 0:
            await ctx.send("Please wager a positive number of points.")
            logging.warning(f"{ctx.author} tried to spin with invalid wager: {wager}")
            return

        color = color.lower()
        if color not in ["red", "black"]:
            await ctx.send("Invalid color. Choose 'red' or 'black'.")
            logging.warning(f"{ctx.author} tried to spin with invalid color: {color}")
            return

        # Roulette wheel: 0-36 (37 slots)
        red_numbers = [1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35]
        black_numbers = [2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36]

        result = random.randint(0, 36)

        if result == 0:  # House wins
            add_score(ctx.author.id, -wager)
            embed = discord.Embed(title="Roulette Spin - 0 (House)", description=f"{ctx.author} landed on 0 and lost!", color=0xff0000)
            embed.add_field(name="Points Lost", value=f"{wager}", inline=True)
            embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            embed.set_footer(text="House number landed")
            await ctx.send(embed=embed)
        else:
            result_color = "red" if result in red_numbers else "black"
            # fair payout: p_win = 18/37, losses = 19 -> profit = wager * (losses / wins)
            wins = 18
            total = 37
            losses = total - wins
            p_win = wins / total
            base_profit = max(1, int(round(wager * (losses / wins))))
            limit_calc, multiplier = calc_bonus(user_id=ctx.author.id, limit=100, multiplier=check_bonus_multiplier(ctx.author.id))
            bonus = int(limit_calc * multiplier)
            profit = base_profit + bonus

            if result_color == color:  # Player wins
                add_score(ctx.author.id, profit)
                xp_result = add_xp(ctx.author.id, 10)
                embed = discord.Embed(title=f"Roulette Spin - {result} ({result_color.capitalize()})", description=f"{ctx.author} bet on {color} and won!", color=0x00ff00)
                embed.add_field(name="Points Earned", value=f"+{profit}", inline=True)
                embed.add_field(name="XP Earned", value=f"+{xp_result['gained']} XP", inline=True)
                embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
                if xp_result['leveled_up'] > 0:
                    embed.add_field(name="Level Up!", value=f"You reached level {xp_result['level']}!", inline=False)
                embed.set_footer(text=f"Fair payout: profit={base_profit}, bonus={bonus}")
                await ctx.send(embed=embed)
            else:  # Player loses
                add_score(ctx.author.id, -wager)
                xp_result = add_xp(ctx.author.id, 3)
                embed = discord.Embed(title=f"Roulette Spin - {result} ({result_color.capitalize()})", description=f"{ctx.author} bet on {color} and lost!", color=0xff0000)
                embed.add_field(name="Points Lost", value=f"{wager}", inline=True)
                embed.add_field(name="XP Earned", value=f"+{xp_result['gained']} XP", inline=True)
                embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
                if xp_result['leveled_up'] > 0:
                    embed.add_field(name="Level Up!", value=f"You reached level {xp_result['level']}!", inline=False)
                embed.set_footer(text="Better luck next time")
                await ctx.send(embed=embed)

        logging.info(f"{ctx.author} spun roulette and landed on {result}")
        say(f"[green]{ctx.author} spun roulette and landed on {result}")

class Fun(commands.Cog): # fun commands
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="joke", description="tells a random joke")
    async def joke(self, ctx):
        say(f"Joke command called by [blue]{ctx.author}")
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://v2.jokeapi.dev/joke/Any') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('type') == 'single':
                            joke_text = data.get('joke', 'No joke returned')
                        else:
                            joke_text = f"{data.get('setup', '')}\n{data.get('delivery', '')}"
                        embed = discord.Embed(title="Joke", description=joke_text, color=0xFFD700)
                        await ctx.send(embed=embed)
                        logging.info(f"{ctx.author} requested a joke")
                    else:
                        await ctx.send("Failed to fetch joke.")
        except Exception as e:
            await ctx.send(f"Error fetching joke: {e}")
            logging.error(f"Error fetching joke: {e}")

    @commands.hybrid_command(name="dex", description="looks up a word on Urban Dictionary")
    async def urban(self, ctx, word: str):
        say(f"Urban Dictionary command called by [blue]{ctx.author} for word: {word}")
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://api.urbandictionary.com/v0/define?term={word}') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('list'):
                            definition = data['list'][0]
                            embed = discord.Embed(title=f"Urban Dictionary: {word}", color=0x1f8b4c)
                            embed.add_field(name="Definition", value=definition.get('definition', 'N/A')[:1024], inline=False)
                            embed.add_field(name="Example", value=definition.get('example', 'N/A')[:1024], inline=False)
                            embed.set_footer(text=f"source: urbandictionary.com")
                            await ctx.send(embed=embed)
                            logging.info(f"{ctx.author} looked up '{word}' on Urban Dictionary")
                        else:
                            await ctx.send(f"No definition found for '{word}'.")
                    else:
                        await ctx.send("Failed to fetch definition.")
        except Exception as e:
            await ctx.send(f"Error fetching definition: {e}")
            logging.error(f"Error fetching definition: {e}")

    @commands.hybrid_command(name="magic8ball", description="ask the magic 8-ball a question")
    async def magic8ball(self, ctx, *, question: str):
        say(f"Magic 8-ball command called by [blue]{ctx.author}: {question}")
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes definitely.",
            "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.",
            "Yes.", "Signs point to yes.", "Reply hazy, try again.", "Ask again later.",
            "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.", "Outlook not so good.",
            "Very doubtful."
        ]
        response = random.choice(responses)
        embed = discord.Embed(title="Magic 8-Ball", description=f"{ctx.author} asked: *{question}*", color=0x000000)
        embed.add_field(name="Answer", value=response, inline=False)
        await ctx.send(embed=embed)
        logging.info(f"{ctx.author} asked the magic 8-ball: {question}")

    @commands.hybrid_command(name="trivia", description="answer a trivia question and wager points")
    async def trivia(self, ctx, wager: int = 10):
        say(f"Trivia command called by [blue]{ctx.author} with wager: {wager}")
        import aiohttp
        import html
        
        user_score = check_score(ctx.author.id)
        if user_score is None or user_score < wager:
            await ctx.send("You don't have enough points to wager that much.")
            logging.warning(f"{ctx.author} tried trivia with insufficient wager: {wager}")
            return
        
        if wager <= 0:
            await ctx.send("Please wager a positive amount of points.")
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://opentdb.com/api.php?amount=1&type=multiple') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('results'):
                            question_data = data['results'][0]
                            question = html.unescape(question_data.get('question', ''))
                            correct = html.unescape(question_data.get('correct_answer', ''))
                            incorrect = [html.unescape(a) for a in question_data.get('incorrect_answers', [])]
                            
                            all_answers = incorrect + [correct]
                            random.shuffle(all_answers)
                            
                            answer_text = "\n".join([f"{i+1}. {ans}" for i, ans in enumerate(all_answers)])
                            embed = discord.Embed(title="Trivia Question", description=question, color=0x00BFFF)
                            embed.add_field(name="Options", value=answer_text, inline=False)
                            embed.add_field(name="Wager", value=f"{wager} points", inline=False)
                            embed.set_footer(text="React with the number of your answer (1-4)")
                            
                            # compute fair profit and escrow it from asker
                            choices = len(all_answers)
                            base_profit = max(1, int(round(wager * (choices - 1))))
                            limit_calc, multiplier = calc_bonus(user_id=ctx.author.id, limit=50, multiplier=check_bonus_multiplier(ctx.author.id))
                            bonus = int(limit_calc * multiplier)
                            profit = base_profit + bonus

                            # ensure asker can cover potential payout
                            asker_score = check_score(ctx.author.id) or 0
                            if asker_score < profit:
                                await ctx.send(f"You need at least {profit} points to start this trivia (covers potential payout). Reduce your wager or earn more points.")
                                return

                            # escrow profit from asker
                            add_score(ctx.author.id, -profit)
                            xp_start = add_xp(ctx.author.id, 5)

                            embed.add_field(name="XP Earned", value=f"+{xp_start['gained']} XP", inline=False)
                            if xp_start['leveled_up'] > 0:
                                embed.add_field(name="Level Up!", value=f"You reached level {xp_start['level']}!", inline=False)

                            msg = await ctx.send(embed=embed)

                            # Add number reactions for choices (unicode)
                            emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']
                            for e in emojis:
                                try:
                                    await msg.add_reaction(e)
                                except Exception:
                                    pass

                            # Store question data for reaction-based answer checking
                            TRIVIA_PENDING[msg.id] = {
                                'asker': ctx.author.id,
                                'correct': correct,
                                'answers': all_answers,
                                'wager': wager,
                                'profit': profit,
                                'channel_id': msg.channel.id,
                                'winners': [],
                                'answered_users': []
                            }

                            # start timeout task to refund if unanswered
                            async def _trivia_timeout(mid, delay=60):
                                end_time = time.time() + delay
                                while True:
                                    remaining = int(end_time - time.time())
                                    if remaining <= 0:
                                        break
                                    await asyncio.sleep(min(10, remaining))
                                    entry = TRIVIA_PENDING.get(mid)
                                    if not entry:
                                        return
                                    winners = entry.get('winners', [])
                                    if msg and msg.channel:
                                        embed = msg.embeds[0] if msg.embeds else discord.Embed(title="Trivia Question", description=question, color=0x00BFFF)
                                        embed.set_footer(text=f"Time remaining: {remaining} seconds | Current winners: {len(winners)}")
                                        try:
                                            await msg.edit(embed=embed)
                                        except Exception:
                                            pass

                                entry = TRIVIA_PENDING.pop(mid, None)
                                if entry:
                                    winners = entry.get('winners', [])
                                    profit_total = entry.get('profit', 0)
                                    asker = entry.get('asker')
                                    ch = bot.get_channel(entry.get('channel_id'))
                                    if winners:
                                        per_winner = profit_total // len(winners)
                                        for uid in winners:
                                            add_score(uid, per_winner)
                                            xp_result = add_xp(uid, 15)
                                            if ch:
                                                await ch.send(embed=discord.Embed(title="Trivia XP", description=f"<@{uid}> earned +{xp_result['gained']} XP for answering correctly!", color=0x00ff00))
                                        remainder = profit_total - (per_winner * len(winners))
                                        if remainder > 0:
                                            add_score(asker, remainder)
                                        if ch:
                                            await ch.send(embed=discord.Embed(title="Trivia Results", description=f"Trivia ended! Winners: {len(winners)}\nEach winner receives {per_winner} points.\nRemainder refunded to asker.", color=0x00ff00))
                                    else:
                                        # refund escrow to asker
                                        add_score(asker, profit_total)
                                        if ch:
                                            await ch.send(f"No correct answers within {delay} seconds. Wager refunded to <@{asker}>.")

                            asyncio.create_task(_trivia_timeout(msg.id, 60))

                            logging.info(f"{ctx.author} started a trivia question and wagered {wager} points (msg {msg.id})")
                        else:
                            await ctx.send("Failed to fetch trivia question.")
                    else:
                        await ctx.send("Failed to connect to trivia API.")
        except Exception as e:
            await ctx.send(f"Error fetching trivia: {e}")
            logging.error(f"Error fetching trivia: {e}")


    @bot.event
    async def on_reaction_add(reaction, user):
        # handle trivia reaction answers
        try:
            if user.bot:
                return
            msg = reaction.message
            entry = TRIVIA_PENDING.get(msg.id)
            if not entry:
                return

            emoji_map = {'1️⃣': 0, '2️⃣': 1, '3️⃣': 2, '4️⃣': 3} #blame copilot
            idx = emoji_map.get(str(reaction.emoji))
            if idx is None:
                return

            if user.id in entry.get('answered_users', []):
                try:
                    await msg.remove_reaction(reaction.emoji, user)
                except Exception:
                    pass
                return

            answers = entry.get('answers', [])
            correct = entry.get('correct')
            profit = entry.get('profit', 0)
            asker = entry.get('asker')
            chosen = answers[idx] if idx < len(answers) else None
            entry.setdefault('answered_users', []).append(user.id)

            # asker's reactions now count as normal (they may win their own trivia)

            if chosen == correct:
                winners = entry.get('winners', [])
                if user.id not in winners:
                    winners.append(user.id)
                    entry['winners'] = winners
                    # do not announce immediately; winners will be announced after timeout
                    logging.info(f"{user} recorded as trivia winner on msg {msg.id}")
                # leave pending until timeout to allow multiple winners
            else:
                # incorrect: keep the reaction so users can see attempts
                pass
        except Exception as e:
            logging.error(f"Error processing trivia reaction: {e}")

    @commands.hybrid_command(name="dig", description="Try to dig to find treasure.")
    async def dig(self, ctx):
        import random
        user_score = check_score(ctx.author.id)

        if user_score is None:
            await ctx.send("You have no points profile. Use `!daily` to start earning points!")
            logging.info(f"{ctx.author} tried to dig with no points profile")
            return
        
        dig_stamina = get_dig(ctx.author.id)

        if dig_stamina is None or dig_stamina <= 0:
            await ctx.send("You have no shovels left. Use `!daily` to restore your stamina or buy from the shop.")
            logging.info(f"{ctx.author} tried to dig with no stamina")
            return
        # continues if stamina isnt 0
        # consume one stamina point, make sure it doesn't go below 0
        new_stamina = max(0, dig_stamina - 1)
        set_dig(ctx.author.id, new_stamina)

        found_chance = random.randint(1, 100)
        multiplier = float(check_bonus_multiplier(ctx.author.id) or 1.0)

        # outcomes
        if found_chance in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:  # lucky numbers - big treasure
            base_points = 500
            total_points = int(base_points * multiplier)
            add_score(ctx.author.id, total_points)
            embed = discord.Embed(title="Digging for treasure...", description=f"{ctx.author} dug and found a treasure! Got {total_points} points!", color=0x00ff00)
            embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            embed.set_footer(text="Wowie!")
            await ctx.send(embed=embed)
            say(f"{ctx.author} dug and found a treasure! Got {total_points} points")
            logging.info(f"{ctx.author} dug and found a treasure! Got {total_points} points")
            return

        elif found_chance in [31, 37, 41, 43, 67]:  # prime numbers, basic win
            base_points = random.randint(10, 50)
            total_points = int(base_points * multiplier)
            add_score(ctx.author.id, total_points)
            embed = discord.Embed(title="Digging for treasure...", description=f"{ctx.author} dug and found {total_points} points!", color=0x00ff00)
            embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            embed.set_footer(text="Lucky you!")
            await ctx.send(embed=embed)
            say(f"{ctx.author} dug and found {total_points} points")
            logging.info(f"{ctx.author} dug and found {total_points} points")
            return

        elif found_chance >= 90:  # unlucky
            points_lost = random.randint(5, 20)
            add_score(ctx.author.id, -points_lost)
            embed = discord.Embed(title="Digging for treasure...", description=f"{ctx.author} dug and found a landmine! Lost {points_lost} points!", color=0xff0000)
            embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            embed.set_footer(text="ouchies!")
            await ctx.send(embed=embed)
            say(f"{ctx.author} dug and hit a landmine! Lost {points_lost} points")
            logging.info(f"{ctx.author} dug and lost {points_lost} points")
            return

        else:  # found nothing
            embed = discord.Embed(title="Digging for treasure...", description=f"{ctx.author} dug and found no points!", color=0xff0000)
            embed.set_footer(text="Better luck next time!")
            await ctx.send(embed=embed)
            say(f"{ctx.author} dug and found no points, {found_chance}")
            logging.info(f"{ctx.author} dug and found no points")
            return
    
 
   
class Utility(commands.Cog): # utility commands
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="timestamp", description="converts any selected time to a discord timestamp")
    async def timestamp(self, ctx, days: int = 0, hours: int = 0, minutes: int = 0):

        try:
            # base datetime is now (UTC)
            dt = datetime.utcnow().replace(tzinfo=timezone.utc)

            # apply optional offsets (days/hours/minutes)
            try:
                offset = timedelta(days=days or 0, hours=hours or 0, minutes=minutes or 0)
                if offset != timedelta(0):
                    dt = dt + offset
            except Exception:
                if getattr(ctx, 'interaction', None):
                    await ctx.reply("Invalid offset values. Use integers for days/hours/minutes.", ephemeral=True)
                else:
                    await ctx.author.send("Invalid offset values. Use integers for days/hours/minutes.")
                return

            ts = int(dt.timestamp())

            # prepare Discord timestamp variants
            long_fmt = f"<t:{ts}:F>"  # Full timestamp
            short_fmt = f"<t:{ts}:f>"  # Short
            relative = f"<t:{ts}:R>"   # Relative

            message_text = (
                "Discord timestamp (UTC) — copy any line to use:\n"
                f"{long_fmt}\n{short_fmt}\n{relative}\n\n"
                "Single copy-paste value: " + long_fmt
            )

            # send as ephemeral reply when possible, otherwise DM the user
            if getattr(ctx, 'interaction', None):
                await ctx.reply(message_text, ephemeral=True)
            else:
                try:
                    await ctx.author.send(message_text)
                    await ctx.send("I've DM'd you the timestamp.", delete_after=6)
                except Exception:
                    # fallback to normal reply
                    await ctx.send(message_text)

            logging.info(f"{ctx.author} created a discord timestamp at {ts}")
        except Exception as e:
            logging.error(f"Error in timestamp command: {e}")
            if getattr(ctx, 'interaction', None):
                await ctx.reply(f"Error: {e}", ephemeral=True)
            else:
                await ctx.send(f"Error: {e}")

bot.run(token, log_handler=handler, log_level=logging.INFO, root_logger=True)