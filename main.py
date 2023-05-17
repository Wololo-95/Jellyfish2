import discord
from youtubesearchpython import Search
import asyncio
from discord.ext import commands
from discord.utils import get
from pytube import YouTube
import os
import subprocess
import sys
import time
import requests
import openai

'''
Jellyfish 2: A music-centered discord bot
https://github.com/Wololo-95/Jellyfish2.git
'''

# Retrieve Discord Token
TOKEN = os.getenv('DISCORD_TOKEN')

# Check for updates:
print("Checking for updates...")

# Location of the version file
VERSION_FILE = 'version.txt'

# URL of the Github repository
REPO_URL = 'https://github.com/Wololo-95/Jellyfish2.git'

# Get the current version of the code
with open(VERSION_FILE, 'r') as f:
    current_version = f.read().strip()

# Get the latest version from Github
response = requests.get(REPO_URL + '/raw/master/version.txt')
latest_version = response.text.strip()

# If the versions are different, update and restart
if latest_version != current_version:
    print("New version found. Pulling update from Github.")
    # Fetch the latest code from Github
    subprocess.run(['git', 'pull', REPO_URL])

    # Update the version file
    with open(VERSION_FILE, 'w') as f:
        f.write(latest_version)

    # Restart the bot with the updated code
    print("Update complete. Restarting.")
    python = sys.executable
    subprocess.run([python, 'main.py'])


clean = os.listdir(".")
print("Initiating cleanup check...")
clean_no = 0
song_queue = []

for item in clean:
    if item.endswith(".mp3") or item.endswith(".mp4"):
        clean_no += 1
        print(f"File: {item} removed.")
        os.remove(item)
print(f"Cleanup complete, {clean_no} items successfully removed.")

openai.api_key = "OPEN_AI_TOKEN"

# Create a new Discord client instance
intents = discord.Intents.default()
intents.members = True # Allows bot to recognize server members
intents.message_content = True # Allows bot to read channel messages
client = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    print('Jellyfish 2, up and running! Or... swimming. Gliding?')


@client.command() # Test command
async def ping(ctx):
    await ctx.send('Pong!')

@client.command()
async def play(ctx, *args: str):
    query = ' '.join(args)
    
    voice_channel = ctx.author.voice.channel # Define user voice channel as the target destination

    if ctx.voice_client is None:
        voice_client = await voice_channel.connect()
        # If the author is not in the voice channel, await connection
    else:
        voice_client = ctx.voice_client # Establish connection with the voice client

    if ctx.voice_client.is_playing():
        # Add the requested song to the queue
        song_queue.append(query)
        await ctx.send(f"{query} added to the queue.")
        print(f"{query} added to the queue, requested by user {ctx.author}")
        return
    
    try:
        if 'youtube.com/watch?' in query or 'youtu.be/' in query:
            # If the query is a valid YouTube video URL, extract the video ID from it
            if 'youtube.com/watch?' in query:
                video_id = query.split('v=')[1].split('&')[0]
            else:
                video_id = query.split('/')[-1]
            
            # Use the YouTube function to get the video information
            yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
            await ctx.send(f"Attempting to play {yt.title} \nFrom https://www.youtube.com/watch?v={video_id}")
            print(f"Attempting to play {yt.title} \nFrom https://www.youtube.com/watch?v={video_id}")
        else:
            search = Search(query, limit=1)

            if search.result():
                # Extract the video link from the search result dictionary
                video_link = search.result()['result'][0]['link']
                print(f"{video_link} retrieved.\n Request sent by user: {ctx.author}")
            else:
                print("No search results found.")
                await ctx.send("Sorry, no search results found.")

            # Download the audio file
            yt = YouTube(video_link)
            await ctx.send(f"Attempting to play {yt.title} \nFrom {video_link}")

        audio = yt.streams.filter(only_audio=True).first()
        audio_file = f"{yt.title}.mp3"
        audio.download(output_path=".", filename=audio_file) # Tells script where to load files to, and names it as the title of the video

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audio_file)) # Creates a source for discord to load the audio information

        voice_client.play(source) # Tells voice client to play the audio located within the source

        await ctx.send(f"Now Playing: {yt.title}, requested by {ctx.author}.")
        print(f"Playing {yt.title}, requested by {ctx.author}")

    except Exception as e: # Error handling printed to terminal and chat for thoroughness
        print(e)
        await ctx.send("An Error occurred while trying to play the audio! Sorry.")
        await ctx.send(str(e))

    # Check if there are any songs in the queue
    if song_queue:
        # Get the next song from the queue
        next_song = song_queue.pop(0)
        await play(ctx, next_song)

    while voice_client.is_playing() or voice_client.is_paused():
        await asyncio.sleep(1)
    
    voice_client.stop()

    os.remove(audio_file)
  
@client.command()
async def next(ctx):
    print(f"Next command issued by user {ctx.author}")
    # Check if there are any songs in the queue
    if song_queue:
        # stops the current song
        ctx.voice_client.stop()
        next_song = song_queue.pop(0)
        await play(ctx, next_song)
    else:
        await ctx.send("There are no songs in the queue. Use !play to request a track.")

@client.command()
async def stop(ctx):
    print(f"Stop command issued by {ctx.author}")
    song_queue.clear()
    if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
        ctx.voice_client.stop()
        await ctx.send("The playback has been stopped, and the current queue has been cleared.")
    else:
        await ctx.send("Nothing is playing! I can't fix what isn't broken.")

@client.command()
async def jellyhelp(ctx):
    await ctx.send(f"Hey there {ctx.author}, I am Jellyfish 2!\n\nI can currently do the following:\n!play 'query' -- search and play a song from YouTube; spotify compatibility is under construction. Also used to add songs to queue.\n!stop -- stops whatever is currently playing, and exit the voice channel.\n!next -- skip the current song, and move to the following in the queue.\n!queue -- View the current queue of songs.\n!pause -- Pauses the currently playing song.\n!resume -- Resumes playback on the current song.\n\nCurrently, the projects underway include: Spotify compatibility, Soundcloud support, and world domination.\n\n\n\nView #jelly-documentation for information")

@client.command
async def jellyfish(message):
    if message.author == client.user:
        return
    print("prompt received.")
    response = openai.Completion.create(
        engine="gpt-3.5-turbo",
        prompt=message.content,
        messages=[{"role": "system", "content": "You are an assistant, assist the user as best you can."}],
        max_tokens=50
    )
    await message.channel.send(response.choices[0].text)

@client.command()
async def queue(ctx):
    if song_queue:
        queue_list = "\n".join(song_queue)
        await ctx.send(f"Current Queue:\n{queue_list}")
    else:
        await ctx.send("There are no songs in the queue.")

@client.command()
async def pause(ctx):
    voice_client = ctx.voice_client
    if voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Playback paused.")
    else:
        await ctx.send("Unable to pause: nothing is playing.")

@client.command()
async def resume(ctx):
    voice_client = ctx.voice_client
    if voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Playback resumed.")
    else:
        await ctx.send("Can not resume playback; nothing is paused.")

@client.command()
# Manual update command
async def update(ctx):
    # Check for updates and restart the bot
    
    # Fetch the latest code from Github
    subprocess.run(["https://github.com/Wololo-95/Jellyfish2.git", "pull"])
    
    # Restart the bot with the updated code
    python = sys.executable
    subprocess.run([python, "main.py"])

# Start the bot
client.run(TOKEN)