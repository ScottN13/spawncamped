import random
import discord
import os
import logging
import time

from dotenv import load_dotenv
from discord.ext import commands
import json
from datetime import datetime

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
guildId = int(os.getenv('guildId'))
owner = int(os.getenv('owner')) # Bot Owner. Change it in the .env file.

reconnect = 0
handler = logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='w')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
activity = discord.Activity(type=discord.ActivityType.listening, name="i was spawncamped!", details="do !help for help!")
bot = commands.Bot(command_prefix='!', intents=intents, activity=activity, status=discord.Status.idle, help_command=None)

MY_GUILD = discord.Object(id=guildId)
SCORES_FILE = 'scores.json'

def say(message):
    from rich import print
    print(f"[blue]BOT:[/blue] {message}")

# external helper functions
async def shutdownBot():
    # await bot.close()
    return True

async def isBotOnline():
    online = bot.is_ready() and not bot.is_closed()
    return {"online": online}


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

def scoreCheck(user_id): # checks if user exists in scores.json
    scores = load_scores()
    user_id_str = str(user_id)

    try:
        if user_id_str not in scores:
            scores[user_id_str] = {'total_score': 0, 'daily_debt': 0, 'daily_score': 0, 'bonus_multiplier': 1}
            return    
    except KeyError:
        logging.error(f"KeyError: User ID {user_id_str} not found in scores.")
        return False


def add_score(user_id, points): # modify a user's score
    scores = load_scores() # gets current scores
    user_id_str = str(user_id)
    
    if user_id_str not in scores:
        scores[user_id_str] = {'total_score': 0, 'daily_debt': 0, 'daily_score': 0}

    scores[user_id_str]['total_score'] += points
    scores[user_id_str]['last_daily_claimed'] = datetime.now().strftime('%Y-%m-%d')
    
    save_scores(scores) # make sure to always save after modifying
    return points

def add_debt(user_id, points): # modify a user's daily debt
    scores = load_scores() # gets current scores
    user_id_str = str(user_id)

    if user_id_str not in scores:
        scores[user_id_str] = {'total_score': 0, 'daily_debt': 0, 'daily_score': 0, 'bonus_multiplier': 1}

    scores[user_id_str]['daily_debt'] += points
    save_scores(scores)
    return points

def add_bonus_multiplier(user_id, multiplier): # modify a user's bonus multiplier
    scores = load_scores() # gets current scores
    user_id_str = str(user_id)

    if user_id_str not in scores:
        scores[user_id_str] = {'total_score': 0, 'daily_debt': 0, 'daily_score': 0, 'bonus_multiplier': 1}

    scores[user_id_str]['bonus_multiplier'] = multiplier
    save_scores(scores)
    return multiplier

def check_score(user_id): # returns a user's score
    scores = load_scores()
    user_id_str = str(user_id)
    
    if user_id_str in scores:
        return scores[user_id_str]['total_score']
    else:
        return None
    
def check_daily_loan(user_id):
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str in scores:
        return scores[user_id_str]['daily_debt']
    else:
        return None

def check_hasDailyYet(user_id):
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str in scores:
        last_claimed = scores[user_id_str].get('last_daily_claimed')
        today = datetime.now().strftime('%Y-%m-%d')
        if last_claimed == today:
            return False # has already claimed today
        else: # has not claimed today
            embed = discord.Embed(title="Daily Reminder", description="You have not claimed your daily points yet! Use `!daily` to claim them.", color=0xffff00)
            return embed
    else:
        return Exception("User not found in `scores.json`")
    

def check_debt(user_id):
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str in scores:
        return scores[user_id_str]['daily_debt']
    else:
        return None

def check_bonus_multiplier(user_id):
    scores = load_scores()
    user_id_str = str(user_id)

    if user_id_str not in scores:
        scores[user_id_str] = {'total_score': 0, 'daily_debt': 0, 'daily_score': 0, 'bonus_multiplier': 1}

    if user_id_str in scores:
        return scores[user_id_str].get('bonus_multiplier', 1)
    else:
        return 1


def get_leaderboard(limit=10): # returns top 10 users by score
    scores = load_scores()
    sorted_users = sorted(scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
    return sorted_users[:limit]

def calc_bonus(user_id, limit, multiplier):
    multiplier = check_bonus_multiplier(user_id=user_id)
    limit_calc = random.randint(1, limit)
    return limit_calc, multiplier

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
        embed.add_field(name="!loan <amount>", value="Takes a loan of points (max 3000).", inline=False)
        embed.add_field(name="!paydebt <amount>", value="Pays off debt.", inline=False)
        embed.add_field(name="!donate <user> <amount>", value="Donates points to another user.", inline=False)
        embed.add_field(name="!stats [user]", value="Shows your or another user's score stats.", inline=False)
        embed.add_field(name="!shop", value="Brings up the multiplier shop.", inline=False)
        embed.set_footer(text="created by ScottyFM. help categories: admin, social, gambling")
        await ctx.send(embed=embed)
        say(f"[green]Displayed social help menu to {ctx.author}")
        logging.info(f"Displayed social help menu to {ctx.author}")

    if type == "gambling":
        embed = discord.Embed(title="Gambling Help Menu", description="List of gambling commands:", color=0xffff00)
        embed.add_field(name="!roll <sides>", value="Rolls a dice with specified number of sides (default 6).", inline=False)
        embed.add_field(name="!flip <wager> <side>", value="Flips a coin. Bet on which side you think it'lk land on and win.", inline=False)
        embed.add_field(name="!spin <wager> <color>", value="Spins a roulette wheel. Bet on either red or black.", inline=False)
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
    await ctx.reply("You can find my source code [here](https://github.com/ScottN13/spawncamped)")
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
        await ctx.reply("Done, i created the rules embed.")
        logging.info(f"Created rules embed for {ctx.author} with contents: {title} - {description}")
    except Exception as e:
        await ctx.reply(f"i uhm: {e}")
        say(f"[red]Error: {e}") 
        logging.error(f"Error creating rules embed for {ctx.author}: {e}")

@bot.command(name="sync", description="syncs slash commands")
async def sync(ctx):

    bot.tree.copy_global_to(guild=discord.Object(id=1433854304678318183))
    synced = await bot.tree.sync(guild=discord.Object(id=1433854304678318183))
    await bot.add_cog(Social(bot))
    await bot.add_cog(leaderboard(bot))
    await bot.add_cog(Gambling(bot))
    await ctx.reply(f"{len(synced)} Slash commands synced. Enabled cogs.")   
    say(f"[green]{len(synced)}  slash commands synced by {ctx.author}")
    logging.info(f"{len(synced)} slash commands synced by {ctx.author}")

@bot.command(name="ping", description="ping") 
async def ping(ctx):
    say(f"Ping command called by [blue]{ctx.author}")
    await ctx.reply(f"`Pong! Latency is {bot.latency} ms`")
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
   if ctx.author.id == owner:
        say(f"Shutdown command issued by {ctx.author}")
        await ctx.reply("*ok*")
        logging.info(f"stopped by {ctx.author}")
        await bot.close()
   else:
     await ctx.reply("no.")
     logging.info(f"{ctx.author} tried to stop bot")
     say(f"{ctx.author} tried to stop bot")

@bot.command(name="enlist", description="enlists a user into the server")
async def enlist(ctx, receiever: discord.Member, role_type: str): 
    # looks up both roles 
    member = discord.utils.get(ctx.guild.roles, id=1433856941163282637) 
    friends = discord.utils.get(ctx.guild.roles, id=1433856406406303776)
    trusted = discord.utils.get(ctx.guild.roles, id=1433854562875215972)
    role_type = role_type.lower()

    if ctx.author.id == owner: # checks if its bot owner
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
        await ctx.reply(f"An error occurred: {e}")
        say(f"[red]Error: {e}")
        logging.error(f"Error pinning message for {ctx.author} with id {message_id}: {e}")

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
        
        embed = discord.Embed(title="Multiplier Shop", description="Thank you for your purchase! You bought 1.1x mult!", color=0xffff00)

        add_score(user_id, -100)
        add_bonus_multiplier(user_id, 1.1)
        await interaction.response.edit_message(embed=embed, view=None)
        logging.info(f"{interaction.user} purchased 1.1x multiplier")
    
    @discord.ui.button(label="Buy 1.25x (300)", style=discord.ButtonStyle.green, custom_id="buy_1.25")
    async def buy_1_25(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        user_score = check_score(user_id)
        
        if user_score is None or user_score < 300:
            await interaction.response.send_message("You don't have enough points (need 300).", ephemeral=True)
            logging.warning(f"{interaction.user} tried to buy 1.25x multiplier with insufficient points")
            return
        
        embed = discord.Embed(title="Multiplier Shop", description="Thank you for your purchase! You bought 1.25x mult!", color=0xffff00)

        add_score(user_id, -300)
        add_bonus_multiplier(user_id, 1.25)
        await interaction.response.edit_message(embed=embed, view=None)
        logging.info(f"{interaction.user} purchased 1.25x multiplier")
    
    @discord.ui.button(label="Buy 1.5x (500)", style=discord.ButtonStyle.green, custom_id="buy_1.5")
    async def buy_1_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        user_score = check_score(user_id)
        
        if user_score is None or user_score < 500:
            await interaction.response.send_message("You don't have enough points (need 500).", ephemeral=True)
            logging.warning(f"{interaction.user} tried to buy 1.5x multiplier with insufficient points")
            return
        
        embed = discord.Embed(title="Multiplier Shop", description="Thank you for your purchase! You bought 1.5x mult!", color=0xffff00)
        
        add_score(user_id, -500)
        add_bonus_multiplier(user_id, 1.5)
        await interaction.response.edit_message(embed=embed, view=None)
        logging.info(f"{interaction.user} purchased 1.5x multiplier")

class Social(commands.Cog): # Social stuff for servers 
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="mc", description="shows details of mc server")
    async def mc(self, ctx):
        embed = discord.Embed(title="Minecraft Server Info", color=0x00ff00)
        embed.add_field(name="Server IP", value="none yet", inline=False)
        embed.add_field(name="Version", value="Java 1.20.1 - Forge 47.4.9", inline=False)
        embed.add_field(name="Modpack link:", value="[click here](https://drive.google.com/drive/folders/1QC7TeQf4ISNDqhdWa06QLQbj7MVGeqCE)", inline=False)
        await ctx.reply(embed=embed)

class leaderboard(commands.Cog): # i seperated these for organization
    def __init__(self, bot):
        self.bot = bot
    

    @commands.command(name="daily", description="gives daily points")
    async def daily(self, ctx):
        if not can_claim_daily(ctx.author.id):
            await ctx.reply(f"You already claimed your daily points.")
            logging.info(f"{ctx.author} tried to claim daily reward twice in one day")
            return
        
        limit_calc, multiplier = calc_bonus(user_id=ctx.author.id, limit=50, multiplier=check_bonus_multiplier(ctx.author.id))

        points = 100
        bonus = int(limit_calc * multiplier)
        add_score(ctx.author.id, points + bonus)
        
        scores = load_scores()
        total = scores[str(ctx.author.id)]['total_score']
        
        embed = discord.Embed(title="Daily Reward Claimed!", color=0x00ff00)
        embed.add_field(name="Points Earned", value=f"+{points+bonus} (100 + {bonus})", inline=True)
        embed.add_field(name="Total Score", value=total, inline=True)
        embed.set_footer(text="come back tomorrow for more!")
        
        await ctx.reply(embed=embed)
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

    @commands.command(name="loan", description="takes a loan of points")
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

    @commands.command(name="paydebt", description="pays off debt")
    async def paydebt(self, ctx, amount: int):
        debt = check_debt(ctx.author.id)
        score = check_score(ctx.author.id)

        if amount is None:
            amount = debt

        if debt is None or debt <= 0:
            await ctx.reply("You have no debt to pay off. :)")
            logging.info(f"{ctx.author} tried to pay debt but has none")
            return

        if amount <= 0:
            await ctx.reply("tf you want me to do with 0 money")
            logging.warning(f"{ctx.author} tried to pay debt with invalid amount: {amount}")
            return

        if amount is None:
            debt = check_debt(ctx.author.id)
            add_score(ctx.author.id, -debt)
            add_debt(ctx.author.id, -debt)
            embed = discord.Embed(title="Banker - Debt Payment", description=f"You have paid off all of your debt ({debt} points).", color=0x00ff00)
            await ctx.reply(embed=embed)
            logging.info(f"{ctx.author} paid off all of their debt: {debt} points")
            return

        else:
            add_score(ctx.author.id, -amount)
            add_debt(ctx.author.id, -amount)
            embed = discord.Embed(title="Banker - Debt Payment", description=f"You have paid off {amount} points of your debt.", color=0x00ff00)
            await ctx.reply(embed=embed)
            logging.info(f"{ctx.author} paid off {amount} points of their debt")
            return

    @commands.command(name="donate", description="donates points to another user")
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

    @commands.command(name="stats", description="shows your score stats")
    async def stats(self, ctx, member: discord.Member = None):

        if member is None:
            score = check_score(ctx.author.id)
            debt = check_debt(ctx.author.id)

            if score is None:
                await ctx.send("You have no score yet. Use `!daily` to start earning points!")
                logging.info(f"{ctx.author} checked stats with no score")
                return

            embed = discord.Embed(title=f"{ctx.author}'s Score Stats", color=0x0000ff)
            embed.add_field(name="Total Score", value=f"{score} points", inline=False)
            embed.add_field(name="Total Debt", value=f"{debt} points", inline=False)
            embed.add_field(name="Bonus Multiplier", value=f"{check_bonus_multiplier(ctx.author.id)}x", inline=False)
            embed.set_footer(text="Use !daily to earn more points! Use points to gamble.")

            await ctx.send(embed=embed)
            logging.info(f"{ctx.author} viewed their score stats")

        else:
            score = check_score(member.id)
            debt = check_debt(member.id)

            if score is None:
                await ctx.send(f"{member} has no score yet.")
                logging.info(f"{ctx.author} checked stats of {member} with no score")
                return

            embed = discord.Embed(title=f"{member}'s Score Stats", color=0x0000ff)
            embed.add_field(name="Total Score", value=f"{score} points", inline=False)
            embed.add_field(name="Total Debt", value=f"{debt} points", inline=False)
            embed.add_field(name="Bonus Multiplier", value=f"{check_bonus_multiplier(member.id)}x", inline=False)
            embed.set_footer(text="Use !daily to earn more points! Use points to gamble.")

            await ctx.send(embed=embed)
            logging.info(f"{ctx.author} viewed {member}'s score stats")

    @commands.command(name="shop", description="shows the multiplier shop")
    async def shop(self, ctx):
        embed = discord.Embed(title="Multiplier Shop", description="Buy bonus multipliers to increase your earnings!", color=0xffff00)
        embed.add_field(name="1.1x Multiplier", value="Cost: 100 points\nIncreases all earnings by 10%.", inline=False)
        embed.add_field(name="1.25x Multiplier", value="Cost: 300 points\nIncreases all earnings by 25%.", inline=False)
        embed.add_field(name="1.5x Multiplier", value="Cost: 500 points\nIncreases all earnings by 50%.", inline=False)
        
        view = ShopView()
        await ctx.send(embed=embed, view=view, ephemeral=True)
        logging.info(f"{ctx.author} viewed the multiplier shop")

class Gambling(commands.Cog): # gambling commands
    def __init__(self, bot):
        self.bot = bot
        for command in self.get_commands():
            command.add_check(commands.cooldown(1, 5, commands.BucketType.user))

    @commands.command(name="roll", description="rolls a dice")
    async def roll(self, ctx, sides: int = 6): # default to 6 sided dice
        import random
        
        user_score = check_score(ctx.author.id)
        if user_score is None or user_score <= 0: # check if user has any points
            await ctx.send("You don't have any points yet.")
            logging.warning(f"{ctx.author} tried to roll dice with no score")
            return

        if sides < 2:
            await ctx.send("Dice must have at least 2 sides.")
            logging.warning(f"{ctx.author} tried to roll a dice with invalid sides: {sides}")
            return
        if sides > 32:
            await ctx.send("Dice cannot have more than 32 sides.")
            logging.warning(f"{ctx.author} tried to roll a dice with too many sides: {sides}")
            return
        
        limit_calc, multiplier = calc_bonus(user_id=ctx.author.id, limit=sides//2, multiplier=check_bonus_multiplier(ctx.author.id))

        result = random.randint(1, sides)
        bonus = int(limit_calc * multiplier)

        if result <= sides / 2 or result == 1: # if the user rolls half the sides or 1, they lose points
            lost = add_score(ctx.author.id, -result)
            embed = discord.Embed(title="Dice Roll", description=f"{ctx.author} rolled a {result} on a {sides}-sided dice and lost.", color=0xffff00)
            embed.add_field(name="Points Lost", value=f"{lost}", inline=True)
            embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            embed.set_footer(text="oof you suck lol")
            await ctx.send(embed=embed)
            logging.info(f"{ctx.author} rolled a {result} on a {sides}-sided dice and lost {lost} points.")
            return
        
        else:
            scored = add_score(ctx.author.id, result + bonus) # dice side + bonus (a reroll kinda)
            embed = discord.Embed(title="Dice Roll", description=f"{ctx.author} rolled a {result} on a {sides}-sided dice.", color=0x00ff00)
            embed.add_field(name="Points Earned", value=f"+{scored}", inline=True)
            embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            embed.set_footer(text=f"Calulated: {result} + ({limit_calc} x {multiplier}x) bonus points")
            await ctx.send(embed=embed)
            logging.info(f"{ctx.author} rolled a {result} on a {sides}-sided dice and earned {scored} points.")
            return

    @commands.command(name="flip", description="flips a coin. Heads is win, tails is lose")
    async def flip(self, ctx , wager: int = 0, side: str = "heads"): 
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

        if side.lower() in ["heads"]: # defaults to heads
            result = random.choice(["Heads", "Tails"])

            limit_calc, multiplier = calc_bonus(user_id=ctx.author.id, limit=50, multiplier=check_bonus_multiplier(ctx.author.id))
            bonus = int(limit_calc * multiplier)
            scored = wager + bonus
            if result == "Heads":
                add_score(ctx.author.id, wager + bonus)
                embed = discord.Embed(title="Coin Flip - Heads", description=f"{ctx.author} won {scored} points!", color=0x00ff00) 
                embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
                embed.set_footer(text=f"Score is calculated as amount wagered ({wager}) + ({limit_calc} x {multiplier}) bonus points")
                await ctx.send(embed=embed)
            else:
                add_score(ctx.author.id, -wager)
                embed_fail = discord.Embed(title="Coin Flip - Heads", description=f"{ctx.author} lost {wager} points!", color=0xff0000)
                embed_fail.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
                embed_fail.set_footer(text="oof you suck lol")
                await ctx.send(embed=embed_fail)
            logging.info(f"{ctx.author} flipped a coin and got {result}.")

        else:
            result = random.choice(["Heads", "Tails"])
            limit_calc, multiplier = calc_bonus(user_id=ctx.author.id, limit=50, multiplier=check_bonus_multiplier(ctx.author.id))
            bonus = int(limit_calc * multiplier)
            scored = wager + bonus
            if result == "Tails":
                add_score(ctx.author.id, wager + bonus)
                embed = discord.Embed(title="Coin Flip - Tails", description=f"{ctx.author} won {scored} points!", color=0x00ff00) 
                embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
                embed.set_footer(text=f"Score is calculated as amount wagered ({wager}) + ({limit_calc} x {multiplier}x) bonus points")
                await ctx.send(embed=embed)
                return
            else:
                add_score(ctx.author.id, -wager)
                embed_fail = discord.Embed(title="Coin Flip - Tails", description=f"{ctx.author} lost {wager} points!", color=0xff0000)
                embed_fail.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
                embed_fail.set_footer(text="oof you suck lol")
                await ctx.send(embed=embed_fail)
                logging.info(f"{ctx.author} flipped a coin and got {result}.")
                return


    @commands.command(name="spin", description="spins a roulette wheel")
    async def spin(self, ctx, wager: int = 0, color: str = "red"):
        user_score = check_score(ctx.author.id)
            
        if user_score is None or user_score < wager:
            await ctx.send("You don't have enough points to make that wager.")
            logging.warning(f"{ctx.author} tried to spin with insufficient points for wager: {wager}")
            return
            
        if wager <= 0:
            await ctx.send("Please wager some points.")
            logging.warning(f"{ctx.author} tried to spin with invalid wager: {wager}")
            return
            
        color = color.lower()
        if color not in ["red", "black"]:
            await ctx.send("Invalid color. Choose 'red' or 'black'.")
            logging.warning(f"{ctx.author} tried to spin with invalid color: {color}")
            return
            
        # Roulette wheel: 0-36
        # Red: 1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35
        # Black: 2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36
        # 0: House wins
        red_numbers = [1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35]
        black_numbers = [2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36]
            
        result = random.randint(0, 36)
            
        if result == 0:  # House wins
            add_score(ctx.author.id, -wager)
            embed = discord.Embed(title="Roulette Spin - 0 (House)", description=f"{ctx.author} landed on 0 and lost!", color=0xff0000)
            embed.add_field(name="Points Lost", value=f"{wager}", inline=True)
            embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
            embed.set_footer(text="The house always wins")
            await ctx.send(embed=embed)
        else:
            result_color = "red" if result in red_numbers else "black"
            if result_color == color:  # Player wins
                limit_calc, multiplier = calc_bonus(user_id=ctx.author.id, limit=100, multiplier=check_bonus_multiplier(ctx.author.id))
                bonus = int(limit_calc * multiplier)
                scored = wager + bonus
                add_score(ctx.author.id, scored)
                embed = discord.Embed(title=f"Roulette Spin - {result} ({result_color.capitalize()})", description=f"{ctx.author} bet on {color} and won!", color=0x00ff00)
                embed.add_field(name="Points Earned", value=f"+{scored}", inline=True)
                embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
                embed.set_footer(text=f"Score is calculated as amount wagered ({wager}) + {bonus} bonus points")
                await ctx.send(embed=embed)
            else:  # Player loses
                add_score(ctx.author.id, -wager)
                embed = discord.Embed(title=f"Roulette Spin - {result} ({result_color.capitalize()})", description=f"{ctx.author} bet on {color} and lost!", color=0xff0000)
                embed.add_field(name="Points Lost", value=f"{wager}", inline=True)
                embed.add_field(name="Your points after this:", value=f"{check_score(ctx.author.id)}", inline=True)
                embed.set_footer(text="Better luck next time")
                await ctx.send(embed=embed)
            
            logging.info(f"{ctx.author} spun roulette and landed on {result}")
            say(f"[green]{ctx.author} spun roulette and landed on {result}")

if __name__ == "__main__":
    bot.run(token, log_handler=handler, log_level=logging.INFO, root_logger=True)