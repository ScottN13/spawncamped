# spawncamped!
ive been spawncamped!

# i made a personal bot
made it for my friend group's discord server
its fun to play with.

# Make it your own
# First time setup
Clone the repo via whichever way you want. I recomment using git for this.

Creating a virtual requirement is recommended, especially for Raspberry PIs.
If you're planning to host this on another linux machine, you may skip this part.

Then you should
```
cd spawncamped (if not in the directory already)
python3 -m venv botenv
source botenv/bin/activate
```
Whenever you want to update the bot, remember to activate the bot's virtual enviroment by typing `source botenv/bin/activate`

Then go ahead and install all dependencies using `pip install -r requirements.txt`

Now you should create these 4 things: (if not already existing.)
- scores.json
- logs/discord.log
- logs/webpanel.log
- .env

Skipping these will make the bot **not** work properly.

In .env, add `DISCORD_TOKEN=""` and insert your bot's token there. Also make sure you add an `owner=""` variable and your discord user id as well.

That's it! You may run the bot via `update.sh`. Make sure to give the script appropiate permissions via chmod first.
Web panel is active at port `8000`. You can change the port at the bottom of `webpanel.py`.

## Updating bot

Always use `update.sh` to update. Make sure git is installed first!

## Important
Some code in this bot is specific to my (closed) discord server and will not work unless you do some editing.