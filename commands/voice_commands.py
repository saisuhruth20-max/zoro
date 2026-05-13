"""
Voice commands — !setvc, !joinvc, !leavevc, !tts
"""

import discord
from discord import app_commands
from discord.ext import commands

from config import Config
from utils.helpers import make_embed
from utils.logger import setup_logger
from voice.voice_manager import VoiceManager

logger = setup_logger("voice_commands")


class VoiceCommands(commands.Cog, name="Voice"):
    """Voice channel management and TTS commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _get_manager(self, guild: discord.Guild) -> VoiceManager:
        """Return (or create) the VoiceManager for this guild."""
        return VoiceManager.get_or_create(self.bot, guild)

    # ── !setvc ─────────────────────────────────────────────────────────────────

    @commands.command(name="setvc", help="Set and join a permanent voice channel.")
    @commands.has_permissions(manage_channels=True)
    async def setvc(self, ctx: commands.Context, channel: discord.VoiceChannel = None) -> None:
        """
        Set the bot's permanent VC. If no channel is provided, uses the author's current VC.
        """
        if channel is None:
            if ctx.author.voice and ctx.author.voice.channel:
                channel = ctx.author.voice.channel
            else:
                await ctx.send(
                    embed=make_embed(
                        title="❌ No Channel",
                        description="Join a voice channel first, or specify one: `!setvc #channel`",
                        color=Config.COLOR_ERROR,
                    )
                )
                return

        manager = self._get_manager(ctx.guild)
        success = await manager.connect(channel)

        if success:
            await manager.announce(f"Permanent voice channel set to {channel.name}.")
            embed = make_embed(
                title="✅ Permanent VC Set",
                description=f"Now permanently connected to **{channel.mention}**.\nI will auto-reconnect if disconnected.",
                color=Config.COLOR_SUCCESS,
            )
        else:
            embed = make_embed(
                title="❌ Connection Failed",
                description="Could not connect to that voice channel.",
                color=Config.COLOR_ERROR,
            )
        await ctx.send(embed=embed)

    # ── !joinvc ────────────────────────────────────────────────────────────────

    @commands.command(name="joinvc", aliases=["join"], help="Join your current voice channel.")
    async def joinvc(self, ctx: commands.Context) -> None:
        """Join the author's current voice channel (without making it permanent)."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(
                embed=make_embed(
                    title="❌ Not in a VC",
                    description="You need to be in a voice channel first.",
                    color=Config.COLOR_ERROR,
                )
            )
            return

        channel = ctx.author.voice.channel
        manager = self._get_manager(ctx.guild)
        success = await manager.connect(channel)

        embed = make_embed(
            title="✅ Joined VC" if success else "❌ Join Failed",
            description=f"Joined **{channel.mention}**." if success else "Could not join the voice channel.",
            color=Config.COLOR_SUCCESS if success else Config.COLOR_ERROR,
        )
        await ctx.send(embed=embed)

    # ── !leavevc ───────────────────────────────────────────────────────────────

    @commands.command(name="leavevc", aliases=["leave", "disconnect"], help="Leave the voice channel.")
    @commands.has_permissions(manage_channels=True)
    async def leavevc(self, ctx: commands.Context) -> None:
        """Disconnect the bot from its current VC and clear the permanent VC setting."""
        manager = self._get_manager(ctx.guild)

        if not manager.is_connected:
            await ctx.send(
                embed=make_embed(
                    title="❌ Not Connected",
                    description="I'm not in a voice channel right now.",
                    color=Config.COLOR_WARNING,
                )
            )
            return

        channel_name = manager.current_channel.name if manager.current_channel else "Unknown"
        await manager.disconnect()

        embed = make_embed(
            title="👋 Left VC",
            description=f"Disconnected from **{channel_name}** and cleared the permanent VC setting.",
            color=Config.COLOR_SUCCESS,
        )
        await ctx.send(embed=embed)

    # ── !tts ───────────────────────────────────────────────────────────────────

    @commands.command(name="tts", help="Speak text via TTS in the voice channel.")
    @commands.cooldown(1, Config.COOLDOWN_TTS, commands.BucketType.user)
    async def tts(self, ctx: commands.Context, *, text: str) -> None:
        """Convert text to speech and play it in the bot's current VC."""
        manager = self._get_manager(ctx.guild)

        if not manager.is_connected:
            # Try to join the author's VC automatically
            if ctx.author.voice and ctx.author.voice.channel:
                await manager.connect(ctx.author.voice.channel)
            else:
                await ctx.send(
                    embed=make_embed(
                        title="❌ Not in a VC",
                        description="I'm not in a voice channel. Use `!joinvc` first.",
                        color=Config.COLOR_ERROR,
                    )
                )
                return

        await manager.announce(text)
        embed = make_embed(
            title="🔊 Speaking",
            description=f"**{ctx.author.display_name}:** {text}",
            color=Config.COLOR_INFO,
        )
        await ctx.send(embed=embed)
        logger.info(f"TTS queued for {ctx.author}: {text!r}")

    # ── /tts (slash) ────────────────────────────────────────────────────────────

    @app_commands.command(name="tts", description="Speak text via TTS in the voice channel.")
    @app_commands.describe(text="Text to speak aloud")
    async def tts_slash(self, interaction: discord.Interaction, text: str) -> None:
        manager = self._get_manager(interaction.guild)

        if not manager.is_connected:
            await interaction.response.send_message(
                embed=make_embed(
                    title="❌ Not in a VC",
                    description="Use `/joinvc` or `!joinvc` to connect me first.",
                    color=Config.COLOR_ERROR,
                ),
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await manager.announce(text)

        embed = make_embed(
            title="🔊 Speaking",
            description=f"**{interaction.user.display_name}:** {text}",
            color=Config.COLOR_INFO,
        )
        await interaction.followup.send(embed=embed)

    # ── /vcstatus (slash) ───────────────────────────────────────────────────────

    @app_commands.command(name="vcstatus", description="Show current voice channel status.")
    async def vcstatus(self, interaction: discord.Interaction) -> None:
        manager = self._get_manager(interaction.guild)

        if manager.is_connected:
            ch = manager.current_channel
            target = manager.target_channel
            desc = (
                f"**Currently in:** {ch.mention if ch else 'Unknown'}\n"
                f"**Permanent VC:** {target.mention if target else 'Not set'}"
            )
            color = Config.COLOR_SUCCESS
            title = "🔊 Voice Status"
        else:
            target = manager.target_channel
            desc = (
                f"Not currently connected.\n"
                f"**Permanent VC:** {target.mention if target else 'Not set'}"
            )
            color = Config.COLOR_WARNING
            title = "🔇 Voice Status"

        await interaction.response.send_message(
            embed=make_embed(title=title, description=desc, color=color)
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceCommands(bot))
