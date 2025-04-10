import os
import discord
import sys
from discord import ui
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp 
from state import SONG_QUEUES
from controls import MusicControls
from collections import deque 
from discord.ui import Button, View
import asyncio 

load_dotenv()
TOKEN = os.getenv("TOKEN")

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    test_guild = discord.Object(id="784509928747433995")
    # current_commands = bot.tree.get_commands(guild=test_guild)
    # for command in current_commands:
    #     await bot.tree.delete_command(command.name, guild=test_guild)
    await bot.tree.sync()  # Sync commands for the specific guild
    print(f"{bot.user} is online!")

@bot.tree.command(name="queue", description="View the current song queue.")
async def show_queue(interaction: discord.Interaction):
    await interaction.response.defer()
    guild_id_str = str(interaction.guild_id)
    if guild_id_str not in SONG_QUEUES or not SONG_QUEUES[guild_id_str]:
        return await interaction.followup.send("The queue is empty.")
    
    queue = SONG_QUEUES[guild_id_str]
    queue_list = "\n".join([f"{i + 1}. {title}" for i, (_, title, _) in enumerate(queue)])

    await interaction.response.send_message(f"Current queue:\n{queue_list}")



@bot.tree.command(name="skip", description="Skips the current playing song")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Skipped the current song.")
    else:
        await interaction.response.send_message("Not playing anything to skip.")


@bot.tree.command(name="pause", description="Pause the currently playing song.")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel.")

    if not voice_client.is_playing():
        return await interaction.response.send_message("Nothing is currently playing.")
    
    voice_client.pause()
    await interaction.response.send_message("Playback paused!")


@bot.tree.command(name="resume", description="Resume the currently paused song.")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel.")

    if not voice_client.is_paused():
        return await interaction.response.send_message("I’m not paused right now.")
    
    voice_client.resume()
    await interaction.response.send_message("Playback resumed!")


@bot.tree.command(name="stop", description="Stop playback and clear the queue.")
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()
    voice_client = interaction.guild.voice_client

    if not voice_client or not voice_client.is_connected():
        return await interaction.followup.send("I'm not connected to any voice channel.")

    guild_id_str = str(interaction.guild_id)
    if guild_id_str in SONG_QUEUES:
        SONG_QUEUES[guild_id_str].clear()

    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    stop_embed = discord.Embed(
        title="Playback Stopped",
    )
    stop_embed.add_field(value="Batty has left the channel. Stopping playback.", inline=True)
    stop_embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    


    await interaction.followup.send(embed=stop_embed, view=MusicControls())
    await voice_client.disconnect()


@bot.tree.command(name="play", description="Play a song or add it to the queue.")
@app_commands.describe(song_query="Search query")
async def play(interaction: discord.Interaction, song_query: str):
    
    await interaction.response.defer()

    voice_channel = interaction.user.voice.channel

    if voice_channel is None:
        await interaction.followup.send("You must be in a voice channel.")
        return

    voice_client = interaction.guild.voice_client

    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)

    ydl_options = {
        "format": "bestaudio[abr<=128]/bestaudio",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
    }

    query = "ytsearch1: " + song_query
    results = await search_ytdlp_async(query, ydl_options)
    tracks = results.get("entries", [])

    first_track = tracks[0]
    audio_url = first_track["url"]
    title = first_track.get("title", "Untitled")
    duration = first_track.get("duration", 0)  # duration in seconds
    webpage_url = first_track.get("webpage_url", "")
    thumbnail_url = first_track["thumbnails"][-1]["url"] if "thumbnails" in first_track else ""

    minutes = duration // 60
    seconds = duration % 60
    duration_str = f"{minutes}:{seconds:02}"

    if tracks is None:
        await interaction.followup.send("No results found.")
        return

    first_track = tracks[0]
    audio_url = first_track["url"]
    title = first_track.get("title", "Untitled")

    guild_id = str(interaction.guild_id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()

    SONG_QUEUES[guild_id].append((audio_url, title, duration))

    def format_duration(seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours:
            return f"{hours}:{minutes:02}:{secs:02}"
        return f"{minutes}:{secs:02}"
    
    queue = SONG_QUEUES[guild_id]
    total_seconds = sum(item[2] for item in queue)
    total_duration_str = format_duration(total_seconds)


    play_embed = discord.Embed(
        title="🎶 Now Playing",
        description=f"[{title}]({webpage_url})",
        color=discord.Color.purple()
    )
    play_embed.add_field(name="Duration", value=duration_str, inline=True)
    play_embed.set_thumbnail(url=thumbnail_url)
    play_embed.set_footer(text=f"Requested by {interaction.user.display_name}")

    queue_embed = discord.Embed(
        title="🎶 Added to Queue",
        description=f"[{title}]({webpage_url})",
        color=discord.Color.purple()
    )
    queue_embed.add_field(name="Duration", value=duration_str, inline=True)
    queue_embed.add_field(name="Position in Queue", value=len(SONG_QUEUES[guild_id]), inline=True)
    queue_embed.add_field(name="Total Duration", value=total_duration_str, inline=True)
    queue_embed.set_thumbnail(url=thumbnail_url)
    queue_embed.set_footer(text=f"Requested by {interaction.user.display_name}")


    if voice_client.is_playing() or voice_client.is_paused():
        await interaction.followup.send(embed=queue_embed, view=MusicControls())
    else:
        await interaction.followup.send(embed=play_embed, view=MusicControls())
        await play_next_song(voice_client, guild_id, interaction.channel)
    


async def play_next_song(voice_client, guild_id, channel):
    if SONG_QUEUES[guild_id]:
        audio_url, title, duration = SONG_QUEUES[guild_id].popleft()

        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k",
        }

        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable="ffmpeg")

        def after_play(error):
            if error:
                print(f"Error playing {title}: {error}")
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)

        voice_client.play(source, after=after_play)
    else:
        await voice_client.disconnect()
        SONG_QUEUES[guild_id] = deque()

bot.run(TOKEN)
