# Features
Lavalink Integration:
- Connects to a Lavalink node to handle efficient audio streaming. The bot connects to a specified node at startup and manages the connection lifecycle automatically.

Spotify Support:
- Converts Spotify track and playlist URLs into YouTube search queries, enabling playback of Spotify content through YouTube.

YouTube Search:
- Supports playing music via direct YouTube URL or by searching for tracks using keywords. Prepends ytsearch: for non-URL queries.

Queue Management:
- Adds tracks and playlists to a queue.
- Supports pagination for viewing the current queue.
- Features commands to shuffle, clear, or loop the queue.

Playback Controls:
- Provides commands for joining/leaving voice channels, playing, pausing, resuming, stopping, skipping tracks, and toggling loop modes.

Volume Persistence:
- Saves and loads volume settings per server using a JSON file, ensuring custom volume preferences are retained across sessions.

Rich Embeds:
- Uses sleek Discord embeds for a modern and clean UI in notifications and command responses.

# Installation
Prerequisites:
- Python 3.8 or higher
- Lavalink server running locally or on a remote server
- A Discord bot token. Create one from the Discord Developer Portal.
- Spotify API credentials (Client ID and Client Secret). Obtain these from the Spotify Developer Dashboard.

Dependencies:
- Install the required Python packages using pip:
  - pip install discord.py wavelink spotipy python-dotenv
- Environment Setup
  - Create a .env file in the project root.
- Add the following variables with your credentials:
  - DISCORD_TOKEN=your_discord_bot_token_here
  - SPOTIFY_CLIENT_ID=your_spotify_client_id_here
  - SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
 
# Commands
Basic Commands:
- b!join
  - Connects the bot to your current voice channel.
- b!leave
  - Clears the queue, stops playback, and disconnects the bot from the voice channel.
- b!play <query|URL>
  - Plays a song from a YouTube URL, a Spotify URL, or a search query. Supports both single tracks and playlists.
- b!pause
  - Pauses the current playback.
- b!resume
  - Resumes playback if paused.
- b!stop
  - Stops playback, clears the queue, and disconnects the bot.
- b!skip
  - Skips the current song.
- b!queue (or b!q)
  - Displays the current queue with pagination support.
- b!np (or b!current/b!playing)
  - Shows the track that is currently playing.
- b!volume <0-100>
  - Sets the playback volume for the server and saves the setting persistently.
- b!shuffle
  - Shuffles the current queue.
- b!clear_queue (or b!cq)
  - Clears all songs from the queue.
- b!loop
  - Toggles loop modes between repeating the current track, looping the entire queue, or disabling looping.
