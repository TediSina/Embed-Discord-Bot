import discord
import sqlite3
import os
from discord import app_commands
from discord.embeds import Embed
from typing import Optional
from config import TOKEN, GUILD, STATUS, ACTIVITY # Please check config.py.

dirname = os.path.dirname(__file__)
db_filename = os.path.join(dirname, "messages.db")

conn = sqlite3.connect(db_filename)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    colour INTEGER,
    image_url TEXT,
    thumbnail_image_url TEXT,
    author_name TEXT,
    author_name_url TEXT,
    author_icon_url TEXT,
    footer_text TEXT,
    footer_icon_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""")

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


# Close the database connection when the bot shuts down.
@client.event
async def on_disconnect():
    conn.close()


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

@client.tree.command(name="create_message", description="Create a custom embed message")
@app_commands.describe(colour="Pick a colour:")
@app_commands.choices(colour=get_colour_list())
async def create_message(interaction: discord.Interaction,
                        title: Optional[str],
                        description: Optional[str],
                        colour: Optional[int],
                        image_url: Optional[str],
                        thumbnail_image_url: Optional[str],
                        author_name: str,
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

    # Insert the message details into the SQLite database.
    cursor.execute("""INSERT INTO messages 
                    (title, description, colour, image_url, thumbnail_image_url, 
                    author_name, author_name_url, author_icon_url, footer_text, 
                    footer_icon_url) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (title, description, colour, image_url, thumbnail_image_url,
                    author_name, author_name_url, author_icon_url, footer_text,
                    footer_icon_url))
    
    # Get the ID of the newly inserted message.
    message_id = cursor.lastrowid

    # Commit the transaction.
    conn.commit()

    # Send a message to the user with the newly created message ID and embed.
    await interaction.response.send_message(content=f"Your message has successfully been created with ID: {message_id}!", embed=embed)


async def get_message_by_id(message_id: int) -> discord.Embed:
    cursor.execute("SELECT * FROM messages WHERE message_id = ?", (message_id,))
    message = cursor.fetchone()
    if message:
        # Extract message details.
        title, description, colour, image_url, thumbnail_image_url, author_name, author_name_url, author_icon_url, footer_text, footer_icon_url = message[1:11]
        # Create an embed with the retrieved details.
        embed = discord.Embed(
            title=title,
            description=description,
            colour=colour
        )
        embed.set_footer(text=footer_text, icon_url=footer_icon_url)
        embed.set_author(name=author_name, url=author_name_url, icon_url=author_icon_url)
        embed.set_image(url=image_url)
        embed.set_thumbnail(url=thumbnail_image_url)
        return embed
    else:
        return None

@client.tree.command(name="show_message", description="Show a message by its ID")
async def show_message(interaction: discord.Interaction, message_id: int):
    # Retrieve the message by its ID.
    embed = await get_message_by_id(message_id)
    if embed:
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Message not found.")


async def get_all_messages() -> str:
    cursor.execute("SELECT message_id, title, created_at FROM messages")
    messages = cursor.fetchall()
    if messages:
        message_list = "\n".join([f"{message[0]} - {message[1]} (Created at: {message[2]} UTC)" for message in messages])
        return message_list
    else:
        return "No messages found."

@client.tree.command(name="list_messages", description="List all messages in the database")
async def list_messages(interaction: discord.Interaction):
    message_list = await get_all_messages()
    await interaction.response.send_message(message_list)


async def delete_message_by_id(message_id: int) -> bool:
    cursor.execute("DELETE FROM messages WHERE message_id = ?", (message_id,))
    conn.commit()
    return cursor.rowcount > 0

@client.tree.command(name="delete_message", description="Delete a message by its ID")
async def delete_message(interaction: discord.Interaction, message_id: int):
    deleted = await delete_message_by_id(message_id)
    if deleted:
        await interaction.response.send_message(f"Message with ID {message_id} deleted successfully.")
    else:
        await interaction.response.send_message("Message not found.")


async def edit_message_by_id(message_id: int, **kwargs) -> bool:
    # Construct the SET clause dynamically based on the provided kwargs.
    set_clause = ', '.join(f"{key} = ?" for key in kwargs.keys() if kwargs[key] is not None)
    values = tuple(kwargs[key] for key in kwargs.keys() if kwargs[key] is not None) + (message_id,)
    
    cursor.execute(f"UPDATE messages SET {set_clause} WHERE message_id = ?", values)
    conn.commit()
    return cursor.rowcount > 0

@client.tree.command(name="edit_message", description="Edit a message by its ID")
async def edit_message(interaction: discord.Interaction, message_id: int,
                        title: Optional[str] = None, description: Optional[str] = None,
                        colour: Optional[int] = None, image_url: Optional[str] = None,
                        thumbnail_image_url: Optional[str] = None, author_name: Optional[str] = None,
                        author_name_url: Optional[str] = None, author_icon_url: Optional[str] = None,
                        footer_text: Optional[str] = None, footer_icon_url: Optional[str] = None):
    edited = await edit_message_by_id(message_id, title=title, description=description,
                                        colour=colour, image_url=image_url,
                                        thumbnail_image_url=thumbnail_image_url, author_name=author_name,
                                        author_name_url=author_name_url, author_icon_url=author_icon_url,
                                        footer_text=footer_text, footer_icon_url=footer_icon_url)
    if edited:
        await interaction.response.send_message(f"Message with ID {message_id} edited successfully.")
    else:
        await interaction.response.send_message("Message not found or no changes were made.")


# Run the bot.
client.run(TOKEN) # Please check config.py if you haven't already.
