import discord
import asyncio
import os
import subprocess
import sys
import time
from datetime import timedelta
import openai
import git
import psutil
import threading
from urllib.parse import quote
from youtubesearchpython import Search
from discord.ext import commands
from discord.utils import get
from pytube import YouTube

'''
Jellyfish 2: A music-centered discord bot
https://github.com/Wololo-95/Jellyfish2.git
'''

# Globals
debug = False
ram_warning = False
song_queue = []

# Retrieve Tokens
TOKEN = os.getenv('DISCORD_TOKEN')
openai.api_key = "OPEN_AI_TOKEN"

def update_check():
    # initialize a GitPython Repo object for the current working directory
    repo = git.Repo('.')
    # check if there are any changes on the remote branch
    if repo.remotes.origin.fetch()[0].commit != repo.head.commit:
        print("Update found, applying...")
        # discard local changes
        repo.git.reset('--hard')

        # pull changes from the remote branch
        repo.remotes.origin.pull()
    else:
        print("Version already up to date. Continuing...")

def sys_clean():
    clean = os.listdir(".")
    print("Initiating cleanup check...")
    clean_no = 0
    for item in clean:
        if item.endswith(".mp3") or item.endswith(".mp4"):
            clean_no += 1
            print(f"File: {item} removed.")
            os.remove(item)
    print(f"Cleanup complete, {clean_no} items successfully removed.")

print("Checking for updates...")
update_check()
print("Attempting to clean operational directory...")
sys_clean()

def get_time_hh_mm_ss(sec):
    # create timedelta and convert it into string
    td_str = str(timedelta(seconds=sec))

    # split string into individual component
    x = td_str.split(':')
    print('Jellyfish 2 | Uptime Report: ', x[0], 'Hours', x[1], 'Minutes', x[2], 'Seconds')

# Create a new Discord client instance
intents = discord.Intents.default()
intents.members = True # Allows bot to recognize server members
intents.message_content = True # Allows bot to read channel messages
client = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    print('Jellyfish 2, up and running! Or... swimming. Gliding?')

@client.command()
async def play(ctx, *args: str):
    global debug

    query = ' '.join(args)

    if debug == True:
        await ctx.send(f"[Debug] Query received: {query} | async def play(crx, *args: str)")
    
    voice_channel = ctx.author.voice.channel # Define user voice channel as the target destination

    if ctx.voice_client is None:
        voice_client = await voice_channel.connect()
        if debug == True:
            await ctx.send(f"[Debug] User {ctx.author} not in voice channel. | voice_client = await voice_channel.connect()")
        
        # If the author is not in the voice channel, await connection
    else:
        voice_client = ctx.voice_client # Establish connection with the voice client
        if debug == True:
            await ctx.send(f"[Debug] Joining same channel as command issuer {ctx.author} | voice_client = ctx.voice_client")

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

            if debug == True:
                await ctx.send(f"[Debug] YouTube direct link received with video id {video_id} | video_id = query.split('v=')[1].split('&')[0]")
            
            # Use the YouTube function to get the video information
            yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')

            if debug == True:
                await ctx.send(f"[Debug] Query: https://www.youtube.com/watch?v={video_id} | yt = YouTube(f'https://www.youtube.com/watch?v={video_id}'")

            await ctx.send(f"Attempting to play {yt.title} \nFrom https://www.youtube.com/watch?v={video_id}")
            print(f"Attempting to play {yt.title} \nFrom https://www.youtube.com/watch?v={video_id}")

        else:
            search = Search(query, limit=1)

            if debug == True:
                await ctx.send(f"[Debug] Received non-direct query; searching YouTube for {query}, Search(query, limit=1)")

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

        if debug == True:
            await ctx.send(f"[Debug] source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audio_file))")

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
    global debug
    print(f"Next command issued by user {ctx.author}")
    # Check if there are any songs in the queue
    if song_queue:
        if debug == True:
            await ctx.send(f"First song in queue = {song_queue[0]}; Popping first item in list, awaiting play(ctx, next_song)")
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
    await ctx.send(f"Hey there {ctx.author}, I am Jellyfish 2!\n\nI can currently do the following:\n> !play 'query' -- search and play a song from YouTube; spotify compatibility is under construction. Also used to add songs to queue.\n> !stop -- stops whatever is currently playing, and exit the voice channel.\n> !next -- skip the current song, and move to the following in the queue.\n> !queue -- View the current queue of songs.\n> !pause -- Pauses the currently playing song.\n> !resume -- Resumes playback on the current song.\n> !volume -- control volume levels. Use an integer and no percent sign, I'll do the math.\n\nCurrently, the projects underway include: Spotify compatibility, Soundcloud support, and world domination.\n\n\n\nView #jelly-documentation for information")

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
async def volume(ctx, vol: int):
    if ctx.voice_client:
        if 0 <= vol <= 100:
            ctx.voice_client.source.volume = vol / 100
            await ctx.send(f"Volume set to {vol}%")
        else:
            await ctx.send("Volume should be between 0 and 100")
    else:
        await ctx.send("I am not connected to a voice channel.")

@client.command()
# Manual update command
async def devupdate(ctx):
    # Check for updates:
    print(f"MANUAL UPDATE REQUESTED BY: {ctx.author}...")
    await ctx.send(f"--Manual Update requested by {ctx.author}.\n\nSearching for updates...")
    # initialize a GitPython Repo object for the current working directory
    repo = git.Repo('.')

    # check if there are any changes on the remote branch
    if repo.remotes.origin.fetch()[0].commit != repo.head.commit:
        print("Update found, applying...")
        await ctx.send(f"Update found, applying.")
        # discard local changes
        repo.git.reset('--hard')
        await ctx.send(f"Update applied. Restarting, please wait.")

        # pull changes from the remote branch
        repo.remotes.origin.pull()
        # Restart the bot with the updated code
        python = sys.executable
        subprocess.run([python, "main.py"])
    else:
        print("Version already up to date. Continuing...")
        await ctx.send(f"Version already up to date. No updates are required at this time.")

@client.command()
async def debugging(ctx):
    global debug
    if debug == False:
        debug = True
        await ctx.send(f"DEBUGGING MODE ENABLED --- MAY BREAK COMMANDS --- DISABLE WITH !debugging")
    else:
        debug = False

def monitor_ram_usage():
    check_no = 0
    process = psutil.Process()
    warning_threshold_mb = 1000
    ANSI_RED = "\033[91m"

    while True:
        print("System Check. Monitoring RAM usage, reporting uptime.")
        tracked_time = time.time()
        difference_runtime = tracked_time - initiated_time
        get_time_hh_mm_ss(difference_runtime)
        check_no += 1
        print(f"\nRunning System util check - RAM || Check number: {check_no}\n")
        # Get the current RAM usage
        ram_info = process.memory_info()
        ram_used_mb = ram_info.rss / 1024 / 1024

        # Print the RAM usage

        print(f"RAM usage: ({ram_used_mb:.2f} MB)\n")

        # Check if RAM usage is close to the warning threshold
        if ram_used_mb >= warning_threshold_mb - 250:
            print(ANSI_RED + "CRITICAL WARNING: RAM usage approaching maximum cap; advising to avoid issuing further commands." + "\033[0m")
        else:
            print("RAM usage within acceptable thresholds...")

        # Sleep for a specific duration (e.g., 10 seconds)
        time.sleep(300)

ram_monitor_thread = threading.Thread(target=monitor_ram_usage)
ram_monitor_thread.start()
initiated_time = time.time()
# Start the bot
client.run(str(TOKEN))
