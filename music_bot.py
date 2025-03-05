import os  # Import the os module for environment variable and file operations.
import json  # Import json for handling JSON data.
import urllib.parse  # Import urllib.parse to parse URLs.
import discord  # Import discord.py library for Discord API.
from discord.ext import commands  # Import commands extension from discord.py.
from dotenv import load_dotenv  # Import load_dotenv to load environment variables from a .env file.
import wavelink  # Import wavelink for Lavalink (music) functionality.
import spotipy  # Import spotipy for Spotify API interactions.
from spotipy.oauth2 import SpotifyClientCredentials  # Import SpotifyClientCredentials for Spotify API authentication.

# Load tokens and credentials from .env file
load_dotenv()  # Load environment variables from the .env file.
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # Get the Discord bot token from environment variables.
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")  # Get the Spotify client ID from environment variables.
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")  # Get the Spotify client secret from environment variables.
# Spotify credentials are used by Lavalink if configured appropriately in your Lavalink config

# Set up spotipy client for Spotify API calls.
spotify_auth = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)  # Initialize Spotify authentication.
sp = spotipy.Spotify(auth_manager=spotify_auth)  # Create a Spotify client instance using the authentication manager.

# Intents setup (ensure "message_content" is enabled in your Developer Portal)
intents = discord.Intents.default()  # Get the default intents for the bot.
intents.message_content = True  # Enable access to message content (must be enabled in the Developer Portal).
intents.voice_states = True  # Enable access to voice state updates.

bot = commands.Bot(command_prefix="b!", intents=intents)  # Create a new bot instance with specified prefix and intents.

# Volume settings file and helper functions for persistence.
volumes_file = "volumes.json"  # Define the file name where volume settings are stored.

def load_volumes():
    try:
        with open(volumes_file, "r") as f:  # Try opening the volumes file in read mode.
            return json.load(f)  # Return the loaded JSON data as a dictionary.
    except FileNotFoundError:
        return {}  # If the file doesn't exist, return an empty dictionary.

def save_volumes():
    with open(volumes_file, "w") as f:  # Open the volumes file in write mode.
        json.dump(volume_settings, f)  # Save the current volume settings to the file in JSON format.

volume_settings = load_volumes()  # Load the volume settings from file at startup.

# Helper function to create a sleek embed
def make_embed(title: str, description: str, color=discord.Color.blue()) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)  # Create a new Discord embed with title, description, and color.
    embed.set_footer(text="Music Bot")  # Set the footer text for the embed.
    return embed  # Return the constructed embed.

##############################
# Setup Lavalink Node in setup_hook
##############################
async def connect_nodes():
    """Connect to Lavalink node(s) using Wavelink Pool."""
    node = wavelink.Node(uri="http://localhost:2333", password="youshallnotpass")  # Create a Lavalink node with specified URI and password.
    await wavelink.Pool.connect(nodes=[node], client=bot, cache_capacity=100)  # Connect to the Lavalink node(s) using the Wavelink pool.
    print("Connected to Lavalink.")  # Print a confirmation message in the console.

@bot.event
async def setup_hook():
    await connect_nodes()  # Connect to Lavalink nodes when the bot's setup hook is triggered.

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} - Ready to play music!")  # Print a message when the bot is ready and logged in.

##############################
# Event: When a track ends, play the next track from the queue.
##############################
@bot.event
async def on_wavelink_track_end(payload: wavelink.TrackEndEventPayload):
    player = payload.player  # Get the player instance from the payload.
    # If the queue isn't empty, play the next track
    if not player.queue.is_empty:
        next_track = player.queue.get()  # Retrieve the next track from the queue.
        await player.play(next_track)  # Play the next track.
        if getattr(player, "text_channel", None):  # Check if a text channel is associated with the player.
            embed = make_embed("Now Playing", f"🎶 **{next_track.title}** by **{next_track.author}**")  # Create an embed for the now playing track.
            await player.text_channel.send(embed=embed)  # Send the embed to the text channel.
    else:
        await player.disconnect()  # Disconnect the player if the queue is empty.

##############################
# Helper: Connect to voice channel
##############################
async def connect_to_voice(ctx: commands.Context) -> wavelink.Player:
    if not ctx.author.voice or not ctx.author.voice.channel:  # Check if the user is in a voice channel.
        await ctx.send(embed=make_embed("Error", "You need to join a voice channel first!", discord.Color.red()))  # Send an error embed if not.
        return None  # Return None to indicate failure.
    channel = ctx.author.voice.channel  # Get the voice channel the user is in.
    if ctx.voice_client is None:  # If the bot is not connected to any voice channel.
        player: wavelink.Player = await channel.connect(cls=wavelink.Player)  # Connect the bot to the user's voice channel.
    else:
        player: wavelink.Player = ctx.voice_client  # Use the existing voice client.
        if player.channel != channel:  # If the bot is connected to a different channel.
            await player.move_to(channel)  # Move the bot to the user's voice channel.
    player.text_channel = ctx.channel  # Set the text channel attribute to the channel where the command was issued.
    player.autoplay = wavelink.AutoPlayMode.disabled  # Disable autoplay mode.
    guild_id = str(ctx.guild.id)  # Get the guild ID as a string.
    if guild_id in volume_settings:  # If there is a saved volume setting for this guild.
        saved_volume = volume_settings[guild_id]  # Retrieve the saved volume.
        await player.set_volume(saved_volume)  # Set the player's volume to the saved value.
    return player  # Return the connected player.

##############################
# Command: join
##############################
@bot.command(name="join", help="Join your voice channel.")
async def join(ctx: commands.Context):
    if not ctx.author.voice or not ctx.author.voice.channel:  # Check if the user is in a voice channel.
        return await ctx.send(embed=make_embed("Error", "You need to join a voice channel first!", discord.Color.red()))  # Send an error if not.
    channel = ctx.author.voice.channel  # Get the user's voice channel.
    player: wavelink.Player = ctx.voice_client  # Get the bot's current voice client.
    if player is None:  # If the bot is not connected to any channel.
        player = await channel.connect(cls=wavelink.Player)  # Connect to the user's voice channel.
    else:
        if player.channel != channel:  # If connected to a different channel.
            await player.move_to(channel)  # Move to the user's voice channel.
    player.text_channel = ctx.channel  # Set the text channel attribute.
    guild_id = str(ctx.guild.id)  # Get the guild ID as a string.
    if guild_id in volume_settings:  # Check if a saved volume exists for this guild.
        saved_volume = volume_settings[guild_id]  # Retrieve the saved volume.
        await player.set_volume(saved_volume)  # Set the player's volume.
    await ctx.send(embed=make_embed("Connected", f"Joined {channel.mention}!"))  # Send a confirmation embed.

##############################
# Command: leave
##############################
@bot.command(name="leave", help="Clear the queue, stop playback, and disconnect from the voice channel.")
async def leave(ctx: commands.Context):
    player: wavelink.Player = ctx.voice_client  # Get the bot's voice client.
    if player:
        player.queue.clear()  # Clear the player's queue.
        if player.playing:  # If a track is currently playing.
            await player.skip(force=True)  # Force skip the current track.
        await player.disconnect()  # Disconnect the player from the voice channel.
        await ctx.send(embed=make_embed("Disconnected", "Left the voice channel and cleared the queue."))  # Send a confirmation embed.
    else:
        await ctx.send(embed=make_embed("Error", "I'm not connected to any voice channel.", discord.Color.red()))  # Send an error if not connected.

##############################
# Command: volume
##############################
@bot.command(name="volume", help="Set the playback volume for the server (0-100).")
async def volume(ctx: commands.Context, vol: int):
    if vol < 0 or vol > 100:  # Validate that the volume is within the allowed range.
        return await ctx.send(embed=make_embed("Error", "Volume must be between 0 and 100.", discord.Color.red()))  # Send an error if invalid.
    guild_id = str(ctx.guild.id)  # Get the guild ID as a string.
    volume_settings[guild_id] = vol  # Save the new volume setting for this guild.
    save_volumes()  # Persist the updated volume settings to file.
    player: wavelink.Player = ctx.voice_client  # Get the current voice client.
    if player:
        await player.set_volume(vol)  # Update the player's volume if connected.
    await ctx.send(embed=make_embed("Volume Set", f"Volume has been set to **{vol}%** for this server."))  # Send a confirmation embed.

##############################
# Helper: Process Spotify Links
##############################
def process_spotify_link(query: str):
    """
    Given a Spotify URL, extract the type and ID.
    Returns a tuple (spotify_type, spotify_id).
    """
    parsed = urllib.parse.urlparse(query)  # Parse the Spotify URL.
    path_parts = parsed.path.split("/")  # Split the URL path into parts.
    if len(path_parts) >= 3:  # Check if the URL has enough parts.
        return path_parts[1], path_parts[2].split("?")[0]  # Return the type and ID of the Spotify item.
    return None, None  # Return None if extraction fails.

##############################
# Command: play
##############################
@bot.command(name="play", aliases=["p"], help="Play a song from YouTube or Spotify URL, or search query.")
async def play(ctx: commands.Context, *, query: str):
    player = await connect_to_voice(ctx)  # Connect to the user's voice channel.
    if not player:
        return  # Exit if connection failed.

    # Check if the query is a Spotify URL
    if "open.spotify.com" in query:
        spotify_type, spotify_id = process_spotify_link(query)  # Process the Spotify URL.
        if spotify_type == "track":
            # Get track details from Spotify
            track_info = sp.track(spotify_id)  # Fetch track details from Spotify API.
            track_name = track_info["name"]  # Extract the track name.
            artist_name = track_info["artists"][0]["name"]  # Extract the artist name.
            query = f"ytsearch:{track_name} {artist_name}"  # Convert to a YouTube search query.
        elif spotify_type == "playlist":
            # For playlists, retrieve tracks and convert to YouTube search queries.
            playlist_data = sp.playlist_tracks(spotify_id)  # Fetch playlist tracks from Spotify.
            queries = []  # Initialize an empty list for search queries.
            for item in playlist_data["items"]:
                track = item["track"]  # Get track details from each item.
                if track is None:  # Skip local or unavailable tracks.
                    continue
                track_name = track["name"]  # Get the track name.
                artist_name = track["artists"][0]["name"]  # Get the artist name.
                queries.append(f"ytsearch:{track_name} {artist_name}")  # Append the YouTube search query.
            results = []  # Initialize an empty list for search results.
            for q in queries:
                try:
                    res = await wavelink.Playable.search(q)  # Search for the track on YouTube.
                    if res:
                        results.append(res[0])  # Append the first result if available.
                except Exception as e:
                    print(f"Error searching for {q}: {e}")  # Print an error message if search fails.
            if results:
                await player.queue.put_wait(results)  # Add the found tracks to the player's queue.
                await ctx.send(embed=make_embed("Playlist Added", f"➕ Added **{len(results)}** tracks from Spotify playlist to the queue."))  # Send a confirmation embed.
                if not player.playing:
                    next_track = player.queue.get()  # Get the next track in the queue.
                    await player.play(next_track)  # Play the next track.
                    await ctx.send(embed=make_embed("Now Playing", f"🎶 Now playing: **{next_track.title}** by **{next_track.author}**"))  # Send now playing embed.
            else:
                await ctx.send(embed=make_embed("Error", "No tracks were found for the Spotify playlist.", discord.Color.red()))  # Inform the user if no tracks were found.
            return  # Exit the command after processing the playlist.
        else:
            return await ctx.send(embed=make_embed("Error", "Unsupported Spotify URL type.", discord.Color.red()))  # Send error if URL type is unsupported.
    
    # If the query is not a URL (or has been converted from a Spotify URL), assume a YouTube search.
    if not query.startswith("http://") and not query.startswith("https://"):
        query = f"ytsearch:{query}"  # Prepend "ytsearch:" to treat the query as a YouTube search.

    try:
        tracks = await wavelink.Playable.search(query)  # Search for tracks using the query.
    except Exception as e:
        return await ctx.send(embed=make_embed("Error", f"Error fetching track: {e}", discord.Color.red()))  # Send an error if the search fails.
    if not tracks:
        return await ctx.send(embed=make_embed("Error", "No results found for your query.", discord.Color.red()))  # Inform the user if no tracks were found.
    if isinstance(tracks, wavelink.Playlist):
        added = await player.queue.put_wait(tracks)  # Add all tracks from the playlist to the queue.
        await ctx.send(embed=make_embed("Playlist Added", f"➕ Added **{added}** tracks from playlist **{tracks.name}** to the queue."))  # Send a confirmation embed.
    else:
        track: wavelink.Playable = tracks[0]  # Select the first track from the search results.
        added = await player.queue.put_wait(track)  # Add the track to the queue.
        await ctx.send(embed=make_embed("Track Added", f"➕ Added **{track.title}** by **{track.author}** to the queue."))  # Send a confirmation embed.
    if not player.playing:
        next_track = player.queue.get()  # Retrieve the next track if nothing is currently playing.
        await player.play(next_track)  # Start playback of the next track.
        await ctx.send(embed=make_embed("Now Playing", f"🎶 Now playing: **{next_track.title}** by **{next_track.author}**"))  # Inform the channel which track is playing.

##############################
# Command: pause
##############################
@bot.command(name="pause", help="Pause the current playback.")
async def pause(ctx: commands.Context):
    player: wavelink.Player = ctx.voice_client  # Get the current voice client.
    if player and player.playing:  # Check if there is a player and it is currently playing.
        await player.pause(True)  # Pause the playback.
        await ctx.send(embed=make_embed("Paused", "⏸️ Paused the music."))  # Send a confirmation embed.
    else:
        await ctx.send(embed=make_embed("Error", "No music is playing to pause.", discord.Color.red()))  # Inform the user if nothing is playing.

##############################
# Command: resume
##############################
@bot.command(name="resume", help="Resume paused playback.")
async def resume(ctx: commands.Context):
    player: wavelink.Player = ctx.voice_client  # Get the current voice client.
    if player and player.paused:  # Check if the player is paused.
        await player.pause(False)  # Resume playback.
        await ctx.send(embed=make_embed("Resumed", "▶️ Resumed the music."))  # Send a confirmation embed.
    else:
        await ctx.send(embed=make_embed("Error", "The music is not paused or there's nothing to resume.", discord.Color.red()))  # Inform the user if nothing is paused.

##############################
# Command: stop
##############################
@bot.command(name="stop", help="Stop playback and clear the queue.")
async def stop(ctx: commands.Context):
    player: wavelink.Player = ctx.voice_client  # Get the current voice client.
    if player:
        player.queue.clear()  # Clear the player's queue.
        await player.skip(force=True)  # Force skip the current track.
        await player.disconnect()  # Disconnect from the voice channel.
        await ctx.send(embed=make_embed("Stopped", "⏹️ Stopped playback and cleared the queue."))  # Send a confirmation embed.
    else:
        await ctx.send(embed=make_embed("Error", "Bot is not connected to a voice channel.", discord.Color.red()))  # Inform the user if the bot is not connected.

##############################
# Command: skip
##############################
@bot.command(name="skip", aliases=["next"], help="Skip the current song.")
async def skip(ctx: commands.Context):
    player: wavelink.Player = ctx.voice_client  # Get the current voice client.
    if player and player.playing:  # Check if a track is currently playing.
        await player.skip()  # Skip the current track.
        await ctx.send(embed=make_embed("Skipped", "⏭️ Skipped the current track."))  # Send a confirmation embed.
    else:
        await ctx.send(embed=make_embed("Error", "No music is playing to skip.", discord.Color.red()))  # Inform the user if nothing is playing.

##############################
# Command: queue (with pagination)
##############################
@bot.command(name="queue", aliases=["q"], help="Show the upcoming songs in the queue with pagination.")
async def queue_cmd(ctx: commands.Context):
    player: wavelink.Player = ctx.voice_client  # Get the current voice client.
    if not player or (not player.playing and player.queue.is_empty):  # Check if there is no music playing or queued.
        return await ctx.send(embed=make_embed("Info", "ℹ️ No songs are playing or queued."))  # Inform the user if the queue is empty.
    queue_tracks = list(player.queue.copy())  # Copy the current queue to a list.
    total_tracks = len(queue_tracks)  # Get the total number of tracks in the queue.
    tracks_per_page = 10  # Define the number of tracks per page for pagination.
    pages_count = (total_tracks + tracks_per_page - 1) // tracks_per_page if total_tracks else 1  # Calculate total number of pages.
    pages = []  # Initialize a list to hold page descriptions.
    for page in range(pages_count):  # Iterate over each page.
        start_index = page * tracks_per_page  # Calculate the starting index for the page.
        end_index = start_index + tracks_per_page  # Calculate the ending index for the page.
        description = ""  # Initialize the page description.
        if page == 0 and player.playing and player.current:  # For the first page, include the currently playing track.
            description += f"**Now Playing:** {player.current.title} by {player.current.author}\n\n"  # Append current track info.
        description += f"**Up Next (Page {page+1}/{pages_count}):**\n"  # Append page header info.
        for i, track in enumerate(queue_tracks[start_index:end_index], start=start_index + 1):  # Enumerate tracks for this page.
            description += f"`{i}.` {track.title} by {track.author}\n"  # Append each track's info.
        pages.append(description)  # Add the page description to the pages list.
    embed = make_embed("Queue", pages[0])  # Create an embed with the first page of the queue.
    message = await ctx.send(embed=embed)  # Send the embed message.
    if pages_count > 1:  # If there are multiple pages, add pagination reactions.
        await message.add_reaction("◀️")  # Add the previous page reaction.
        await message.add_reaction("▶️")  # Add the next page reaction.
        current_page = 0  # Initialize the current page index.
        def check(reaction, user):  # Define a check function for reaction events.
            return (user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message.id == message.id)
        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)  # Wait for a valid reaction.
                if str(reaction.emoji) == "▶️" and current_page < pages_count - 1:  # If next page reaction and not on last page.
                    current_page += 1  # Increment the current page index.
                    new_embed = make_embed("Queue", pages[current_page])  # Create a new embed for the new page.
                    await message.edit(embed=new_embed)  # Edit the message with the new embed.
                    await message.remove_reaction(reaction, user)  # Remove the user's reaction.
                elif str(reaction.emoji) == "◀️" and current_page > 0:  # If previous page reaction and not on first page.
                    current_page -= 1  # Decrement the current page index.
                    new_embed = make_embed("Queue", pages[current_page])  # Create a new embed for the new page.
                    await message.edit(embed=new_embed)  # Edit the message with the new embed.
                    await message.remove_reaction(reaction, user)  # Remove the user's reaction.
                else:
                    await message.remove_reaction(reaction, user)  # Remove the reaction if it doesn't change the page.
            except Exception:
                break  # Exit the loop if waiting for a reaction times out.

##############################
# Command: np (Now Playing)
##############################
@bot.command(name="np", aliases=["current", "playing"], help="Show the current playing track.")
async def now_playing(ctx: commands.Context):
    player: wavelink.Player = ctx.voice_client  # Get the current voice client.
    if player and player.playing and player.current:  # Check if there is a current track playing.
        await ctx.send(embed=make_embed("Now Playing", f"🎶 **{player.current.title}** by **{player.current.author}**"))  # Send an embed with the current track info.
    else:
        await ctx.send(embed=make_embed("Info", "No track is currently playing."))  # Inform the user if no track is playing.

##############################
# Command: shuffle
##############################
@bot.command(name="shuffle", help="Shuffle the current queue.")
async def shuffle(ctx: commands.Context):
    player: wavelink.Player = ctx.voice_client  # Get the current voice client.
    if player and not player.queue.is_empty:  # Check if the queue is not empty.
        player.queue.shuffle()  # Shuffle the tracks in the queue.
        await ctx.send(embed=make_embed("Queue Shuffled", "🔀 Shuffled the queue."))  # Send a confirmation embed.
    else:
        await ctx.send(embed=make_embed("Error", "Not enough songs in the queue to shuffle.", discord.Color.red()))  # Inform the user if the queue cannot be shuffled.

##############################
# Command: clear_queue
##############################
@bot.command(name="clear_queue", aliases=["cq"], help="Clear all songs from the queue.")
async def clear_queue(ctx: commands.Context):
    player: wavelink.Player = ctx.voice_client  # Get the current voice client.
    if player:
        player.queue.clear()  # Clear all tracks from the queue.
        await ctx.send(embed=make_embed("Queue Cleared", "🗑️ Cleared the queue."))  # Send a confirmation embed.
    else:
        await ctx.send(embed=make_embed("Error", "Bot is not connected to a voice channel.", discord.Color.red()))  # Inform the user if the bot is not connected.

##############################
# Command: loop
##############################
@bot.command(name="loop", help="Toggle loop modes (repeat track or entire queue).")
async def loop(ctx: commands.Context):
    player: wavelink.Player = ctx.voice_client  # Get the current voice client.
    if not player:
        return await ctx.send(embed=make_embed("Error", "Bot is not connected to a voice channel.", discord.Color.red()))  # Inform the user if the bot is not connected.
    from wavelink import QueueMode  # Import QueueMode for loop mode options.
    current_mode = player.queue.mode  # Get the current loop mode.
    if current_mode == QueueMode.normal:
        player.queue.mode = QueueMode.loop  # Set loop mode to repeat the current track.
        await ctx.send(embed=make_embed("Loop Mode", "🔁 Now looping the current track."))  # Send a confirmation embed.
    elif current_mode == QueueMode.loop:
        player.queue.mode = QueueMode.loop_all  # Set loop mode to repeat the entire queue.
        await ctx.send(embed=make_embed("Loop Mode", "🔂 Now looping the entire queue."))  # Send a confirmation embed.
    elif current_mode == QueueMode.loop_all:
        player.queue.mode = QueueMode.normal  # Disable looping.
        await ctx.send(embed=make_embed("Loop Mode", "➡️ Looping disabled."))  # Send a confirmation embed.

# Run the bot
bot.run(DISCORD_TOKEN)  # Start the bot using the Discord token.