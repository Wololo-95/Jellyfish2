# Jellyfish2
An updated and improved variant of the original Jellyfish Discord bot.

Jellyfish is designed primarily with music streaming in mind. The goal is to allow Jellyfish to receive a search query or a direct YouTube link, and find that video on YouTube, then stream the audio to a Discord Voice Channel.
Jellyfish takes advantage of asynchronous programming, allowing users to input various commands, and for Jellyfish to systematically issue them.

Music streaming is a fairly simple process; The command is received, the query is searched and verified to be valid, if a video is found with the given information, that video is downloaded and then played using the discord.py library features.

Upon completion of the track, or if the song is prematurely stopped, the track is deleted from the local filesystem. In the event that this does not happen automatically, Jellyfish periodically issues checks and attempts to clean the files automatically.

As of right now, Jellyfish DOES NOT support SoundCloud or Spotify, although these are desired and planned features. The reason being is that Spotify requires an account with Premium access to use its API. While I personally use Spotify premium,only one device may stream at a time, meaning if I was streaming from my personal phone, and a user issued a command for Jellyfish through Spotify, the playback would end on my end, or vice-versa. Additionally, SoundCloud, at the time of writing this, has closed registration access to their API, meaning it can not be incorporated at this time.

Currently, there are several commands Jellyfish can accept.

> !play 'query' - request download of a specific track. This can be a text description of the track you are seeking,or a direct link to a youtube video
> !stop - end the current song, and clear the queue
> !next - end the current song and begin playback of the next song
> !pause - Pause playback
> !resume - Resume paused playback
> !queue - View current queue
> !volume 'integer' - Take the value given as a percentage (0-100), and set the playback volume to that amount
> !devupdate - Manually tell Jellyfish to look for new GitHub commits, and apply them, then restart
> !debug - Enable debugging mode
