import discord
from discord.ext import commands
import edge_tts
import tempfile
import os

VOICE = "ja-JP-NanamiNeural"  # Predefined voice

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="join", description="ボイスチャンネルに参加します")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            embed = discord.Embed(
                description="先にボイスチャンネルに参加してください。",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        voice_channel = interaction.user.voice.channel

        try:
            if interaction.guild.voice_client:
                await interaction.guild.voice_client.move_to(voice_channel)
            else:
                await voice_channel.connect()

            # Mute the bot
            voice_client = interaction.guild.voice_client
            await voice_client.guild.change_voice_state(channel=voice_client.channel, self_mute=True)

            embed = discord.Embed(
                description=f"✅ {voice_channel.name} に参加しました。",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
        except Exception as e:
            embed = discord.Embed(
                description=f"エラーが発生しました: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)

    @discord.app_commands.command(name="leave", description="ボイスチャンネルから退出します")
    async def leave(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client:
            embed = discord.Embed(
                description="ボイスチャンネルに参加していません。",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        try:
            await interaction.guild.voice_client.disconnect()
            embed = discord.Embed(
                description="👋 ボイスチャンネルから退出しました。",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
        except Exception as e:
            embed = discord.Embed(
                description=f"エラーが発生しました: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)

    @discord.app_commands.command(name="vc-tts", description="メッセージを読み上げます")
    async def vc_tts(self, interaction: discord.Interaction, message: str):
        if not interaction.user.voice:
            embed = discord.Embed(
                description="先にボイスチャンネルに参加してください。",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        voice_channel = interaction.user.voice.channel

        try:
            if not interaction.guild.voice_client:
                await voice_channel.connect()

            # Generate TTS audio using edge_tts
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
                temp_filename = temp_audio_file.name

            tts = edge_tts.Communicate(message, VOICE)
            await tts.save(temp_filename)

            # Play the audio in the voice channel
            voice_client = interaction.guild.voice_client
            voice_client.play(discord.FFmpegPCMAudio(temp_filename), after=lambda _: os.remove(temp_filename))

            embed = discord.Embed(
                description=f"📢 メッセージを読み上げました: {message}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
        except Exception as e:
            embed = discord.Embed(
                description=f"エラーが発生しました: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        del before, after  # Unused variables
        voice_client = member.guild.voice_client
        if voice_client:
            if len(voice_client.channel.members) == 1:  # ボットだけが残っている場合
                await voice_client.disconnect()

async def setup(bot):
    await bot.add_cog(Voice(bot))