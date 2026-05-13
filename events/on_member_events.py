"""
Member join/leave guild events — sends a welcome embed to the system channel.
"""

import discord
from discord.ext import commands

from config import Config
from utils.helpers import make_embed
from utils.logger import setup_logger

logger = setup_logger("on_member_events")


class MemberEvents(commands.Cog):
    """Handles guild member join and leave events."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Send a welcome message to the guild's system channel when a new member joins."""
        channel = member.guild.system_channel
        if not channel:
            return

        embed = make_embed(
            title=f"👋 Welcome, {member.display_name}!",
            description=(
                f"Hey {member.mention}, welcome to **{member.guild.name}**!\n\n"
                f"You are member **#{member.guild.member_count}**.\n"
                f"Use `{Config.PREFIX}help` to see what this bot can do."
            ),
            color=Config.COLOR_SUCCESS,
            thumbnail=member.display_avatar.url,
        )
        try:
            await channel.send(embed=embed)
            logger.info(f"Sent welcome message for {member} in {member.guild.name}.")
        except discord.Forbidden:
            logger.warning(f"Missing permission to send welcome message in {channel}.")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Notify the system channel when a member leaves."""
        channel = member.guild.system_channel
        if not channel:
            return

        embed = make_embed(
            title="🚪 Member Left",
            description=f"**{member.display_name}** has left the server.",
            color=Config.COLOR_WARNING,
            thumbnail=member.display_avatar.url,
        )
        try:
            await channel.send(embed=embed)
            logger.info(f"{member} left {member.guild.name}.")
        except discord.Forbidden:
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MemberEvents(bot))
