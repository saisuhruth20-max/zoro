"""
on_voice_state_update event — handle member join/leave announcements
and bot disconnection recovery.
"""

import discord
from discord.ext import commands

from utils.logger import setup_logger
from voice.voice_manager import VoiceManager

logger = setup_logger("on_voice_state_update")


class VoiceStateEvents(commands.Cog):
    """Listens for voice state changes across all guilds."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """
        Fired whenever a member's voice state changes.

        Handles:
        1. Bot disconnected unexpectedly → trigger reconnect.
        2. Human member joined a VC that the bot is in → play join announcement.
        3. Human member left a VC that the bot is in → play leave announcement.
        """
        guild = member.guild
        manager = VoiceManager.get(guild.id)

        # ── 1. Bot was disconnected ────────────────────────────────────────────
        if member.id == self.bot.user.id:
            if before.channel is not None and after.channel is None:
                # Bot was forcibly disconnected
                logger.warning(
                    f"[Guild {guild.id}] Bot was disconnected from {before.channel.name}. "
                    "Scheduling reconnect…"
                )
                if manager:
                    await manager.handle_disconnect()
            return  # Don't announce bot's own moves

        # ── 2. Human member joined a channel the bot is in ─────────────────────
        if manager and manager.is_connected:
            bot_channel = manager.current_channel

            if after.channel and after.channel == bot_channel and before.channel != after.channel:
                phrase = manager.join_phrase(member)
                logger.info(f"[Guild {guild.id}] {member.display_name} joined VC → '{phrase}'")
                await manager.announce(phrase)

            # ── 3. Human member left a channel the bot is in ───────────────────
            elif before.channel and before.channel == bot_channel and after.channel != before.channel:
                phrase = manager.leave_phrase(member)
                logger.info(f"[Guild {guild.id}] {member.display_name} left VC → '{phrase}'")
                await manager.announce(phrase)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceStateEvents(bot))
