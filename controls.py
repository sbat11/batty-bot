# controls.py
import discord
from collections import deque
from state import SONG_QUEUES  # careful: only import constants, not functions or bot itself

class MusicControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Resume", style=discord.ButtonStyle.success, custom_id="music_resume")
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("Resumed playback!", ephemeral=True)
        else:
            await interaction.response.send_message("Not paused.", ephemeral=True)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.primary, custom_id="music_skip")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            voice_client.stop()
            await interaction.response.send_message("Skipped the current song!", ephemeral=True)
        else:
            await interaction.response.send_message("Not playing anything to skip.", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, custom_id="music_stop")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        voice_client = interaction.guild.voice_client
        guild_id_str = str(interaction.guild_id)

        if guild_id_str in SONG_QUEUES:
            SONG_QUEUES[guild_id_str].clear()
        if voice_client:
            voice_client.stop()
            await voice_client.disconnect()

        await interaction.followup.send("Stopped playback and disconnected!", ephemeral=True)

    @discord.ui.button(label="Show Queue", style=discord.ButtonStyle.secondary, custom_id="music_queue")
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id_str = str(interaction.guild_id)
        if guild_id_str not in SONG_QUEUES or not SONG_QUEUES[guild_id_str]:
            return await interaction.response.send_message("The queue is empty.", ephemeral=True)
        
        queue = SONG_QUEUES[guild_id_str]
        queue_str = "\n".join([f"{i + 1}. {title}" for i, (_, title) in enumerate(queue)])
        await interaction.response.send_message(f"Current Queue:\n{queue_str}", ephemeral=True)
    @discord.ui.button(label="Pause", style=discord.ButtonStyle.secondary, custom_id="music_pause")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("Paused playback!", ephemeral=True)
        else:
            await interaction.response.send_message("Not playing anything to pause.", ephemeral=True)