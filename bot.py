import discord
from discord import app_commands
from discord.embeds import Embed
from typing import Optional
from config import TOKEN, GUILD, STATUS, ACTIVITY # Please check config.py.

THIS_GUILD = discord.Object(id=GUILD) # Check config.py.

class ThisClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=THIS_GUILD)
        await self.tree.sync(guild=THIS_GUILD)

intents = discord.Intents.all()
intents.message_content = True
client = ThisClient(intents=intents)


@client.event
async def on_ready():
    await client.change_presence(status=STATUS, activity=ACTIVITY) # Please check config.py if you haven't already.


def get_colour_list(): # Iterate over discord.Colour methods and add 25 (max amount) colours to the choice list.
    colours = discord.Colour(value=0)
    colour_list = []

    for colour in dir(discord.Colour):
        if (not colour.startswith('_') and not colour.startswith("from") and not colour.startswith("to") and not colour.startswith("lighter")
            and not colour.startswith("darker") and not colour.startswith("og") and colour != "random" and not colour.endswith("embed")
            and not colour.endswith("ple")):
            method = getattr(colours, colour)
            if callable(method):
                try:
                    if colour != "default":
                        colour_list.append(app_commands.Choice(name=colour, value=method().value))
                    else:
                        colour_list.append(app_commands.Choice(name="Black", value=method().value))
                except Exception as e:
                    print(e)

    def get_colour_list_key(e):
        return e.name

    colour_list.sort(key=get_colour_list_key)
    return colour_list


@client.tree.command(name="create_msg", description="Create a custom embed message")
@app_commands.describe(colour="Pick a colour:")
@app_commands.choices(colour=get_colour_list())
async def create_msg(interaction: discord.Interaction,
                        title: Optional[str],
                        description: Optional[str],
                        colour: Optional[int],
                        image_url: Optional[str],
                        thumbnail_image_url: Optional[str],
                        author_name: Optional[str],
                        author_name_url: Optional[str],
                        author_icon_url: Optional[str],
                        footer_text: Optional[str],
                        footer_icon_url: Optional[str]):
    embed = Embed(
        title=title,
        description=description,
        colour=colour
    )

    embed.set_footer(text=footer_text, icon_url=footer_icon_url)
    embed.set_author(name=author_name, url=author_name_url, icon_url=author_icon_url)
    embed.set_image(url=image_url)
    embed.set_thumbnail(url=thumbnail_image_url)

    await interaction.response.send_message(embed=embed)

# Run the bot.
client.run(TOKEN) # Please check config.py if you haven't already.
