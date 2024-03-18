# Embed Discord Bot settings.

# Needed for STATUS and ACTIVITY constants.
import discord

# These can be ignored and deleted if you change the values of the constants below, else you should create a .env file with the env variables.
import os
from dotenv import load_dotenv
load_dotenv()

# Change these constants' values.

# Change this to match your bot's token ID.
TOKEN = os.getenv("DISCORD_TOKEN")[1:-1]

# Change this to match your guild's ID.
GUILD = os.getenv("DISCORD_GUILD")[1:-1]

# Change this as you'd like your bot to report its status (discord.Status).
STATUS = eval(os.getenv("DISCORD_STATUS")[1:-1])

# Change this as you'd like your bot to report its activity (discord.Activity or one of its slimmed down versions, like discord.Game).
ACTIVITY = eval(os.getenv("DISCORD_ACTIVITY")[1:-1])
