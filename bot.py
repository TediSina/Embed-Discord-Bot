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
        """
        Initializes a new instance of the class.

        Args:
            intents (discord.Intents): The intents to use for the Discord bot.

        Returns:
            None
        """
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        """
        Asynchronously sets up the hook for the given instance.

        This function copies the global commands to the specified guild and synchronizes the tree with the guild.

        Parameters:
            self (ClassName): The instance of the class.

        Returns:
            None
        """
        self.tree.copy_global_to(guild=THIS_GUILD)
        await self.tree.sync(guild=THIS_GUILD)

intents = discord.Intents.all()
intents.message_content = True
client = ThisClient(intents=intents)


@client.event
async def on_ready():
    """
    A event handler that is called when the client is done preparing the data received from Discord. It changes the presence of the client.
    """
    await client.change_presence(status=STATUS, activity=ACTIVITY) # Please check config.py if you haven't already.


# Close the database connection when the bot shuts down.
@client.event
async def on_disconnect():
    """
    A function that handles the event when the client disconnects.
    """
    conn.close()


def get_colour_list():
    """
    This function retrieves a list of non-private, non-special method colours from the discord.Colour class and appends them to a colour_list array.
    
    It then sorts the colour_list based on the 'name' attribute of the elements and returns the sorted list.
    """
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
    """
    A function to create a custom embed message with various details like title, description, colour, images, author information, and footer details. 
    It inserts the message details into an SQLite database, retrieves the newly inserted message ID, commits the transaction, and sends a success message to the user with the created message ID and embed.
    
    Parameters:
    - interaction: discord.Interaction
    - title: Optional[str]
    - description: Optional[str]
    - colour: Optional[int]
    - image_url: Optional[str]
    - thumbnail_image_url: Optional[str]
    - author_name: str
    - author_name_url: Optional[str]
    - author_icon_url: Optional[str]
    - footer_text: Optional[str]
    - footer_icon_url: Optional[str]

    Returns:
    - None
    """
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
    """
    Retrieves a message from the database based on its ID and returns it as a Discord Embed object.

    Parameters:
        message_id (int): The ID of the message to retrieve.

    Returns:
        discord.Embed: The retrieved message as a Discord Embed object, or None if the message does not exist.
    """
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
    """
    Show a message by its ID.

    Parameters:
        interaction (discord.Interaction): The interaction object representing the user's interaction with the command.
        message_id (int): The ID of the message to be shown.

    Returns:
        None

    Description:
        This function retrieves a message by its ID and sends it as an embedded message in response to the user's interaction. If the message is not found, it sends a message indicating that the message was not found.

    Example Usage:
        await show_message(interaction, 123456789)
    """
    embed = await get_message_by_id(message_id)
    if embed:
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Message not found.")


async def get_all_messages() -> str:
    """
    Retrieves all messages from the database and returns them as a formatted string.

    Returns:
        str: A formatted string containing the message IDs, titles, and creation dates of all messages in the database.
            If no messages are found, returns "No messages found."
    """
    cursor.execute("SELECT message_id, title, created_at FROM messages")
    messages = cursor.fetchall()
    if messages:
        message_list = "\n".join([f"{message[0]} - {message[1]} (Created at: {message[2]} UTC)" for message in messages])
        return message_list
    else:
        return "No messages found."

@client.tree.command(name="list_messages", description="List all messages in the database")
async def list_messages(interaction: discord.Interaction):
    """
    List all messages in the database.

    This function is a command handler for the "list_messages" command. It retrieves all messages from the database using the `get_all_messages` function and sends the message list as a response to the Discord interaction.

    Parameters:
        interaction (discord.Interaction): The Discord interaction object representing the user's interaction with the command.

    Returns:
        None
    """
    message_list = await get_all_messages()
    await interaction.response.send_message(message_list)


async def delete_message_by_id(message_id: int) -> bool:
    """
    Deletes a message from the database by its ID.

    Args:
        message_id (int): The ID of the message to be deleted.

    Returns:
        bool: True if the message was successfully deleted, False otherwise.
    """
    cursor.execute("DELETE FROM messages WHERE message_id = ?", (message_id,))
    conn.commit()
    return cursor.rowcount > 0

@client.tree.command(name="delete_message", description="Delete a message by its ID")
async def delete_message(interaction: discord.Interaction, message_id: int):
    """
    Delete a message by its ID.

    Parameters:
        interaction (discord.Interaction): The interaction object representing the user's interaction with the command.
        message_id (int): The ID of the message to be deleted.

    Returns:
        None
    """
    deleted = await delete_message_by_id(message_id)
    if deleted:
        await interaction.response.send_message(f"Message with ID {message_id} deleted successfully.")
    else:
        await interaction.response.send_message("Message not found.")


async def edit_message_by_id(message_id: int, **kwargs) -> bool:
    """
    Edits a message in the database by its ID.

    Args:
        message_id (int): The ID of the message to be edited.
        **kwargs: Additional keyword arguments representing the fields to be updated.
            - Any field that is not None will be updated.
            - If no fields are provided, the function returns False.

    Returns:
        bool: True if the message was successfully edited, False otherwise.

    Raises:
        None

    Example:
        >>> edit_message_by_id(123, content="New content", author_id=456)
        True
    """
    # Construct the SET clause dynamically based on the provided kwargs.
    set_clause = ', '.join(f"{key} = ?" for key in kwargs.keys() if kwargs[key] is not None)
    if not set_clause:
        return False  # No parameters provided to update.
    
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
    """
    Edit a message by its ID.

    Parameters:
        interaction (discord.Interaction): The interaction object representing the user's interaction with the command.
        message_id (int): The ID of the message to be edited.
        title (Optional[str]): The new title of the message (default: None).
        description (Optional[str]): The new description of the message (default: None).
        colour (Optional[int]): The new color of the message (default: None).
        image_url (Optional[str]): The new image URL of the message (default: None).
        thumbnail_image_url (Optional[str]): The new thumbnail image URL of the message (default: None).
        author_name (Optional[str]): The new author name of the message (default: None).
        author_name_url (Optional[str]): The new author name URL of the message (default: None).
        author_icon_url (Optional[str]): The new author icon URL of the message (default: None).
        footer_text (Optional[str]): The new footer text of the message (default: None).
        footer_icon_url (Optional[str]): The new footer icon URL of the message (default: None).

    Returns:
        None
    """
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
