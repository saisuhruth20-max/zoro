"""
on_ready event — sync slash commands, set bot status, and rejoin permanent VCs.
"""

import discord
from discord.ext import commands

from config import Config
from utils.logger import setup_logger
from voice.voice_manager import VoiceManager

logger = setup_logger("on_ready")


class OnReadyEvents(commands.Cog):
    """Handles all bot startup logic."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        logger.info(f"Logged in as {self.bot.user} (ID: {self.bot.user.id})")
        logger.info(f"Connected to {len(self.bot.guilds)} guild(s).")

        # Sync slash commands globally
        try:
            synced = await self.bot.tree.sync()
            logger.info(f"Synced {len(synced)} slash command(s).")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

        # Set bot activity / status
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{Config.PREFIX}help | AI-powered bot",
        )
        await self.bot.change_presence(status=discord.Status.online, activity=activity)

        # Rejoin permanent VCs for each guild
        for guild in self.bot.guilds:
            manager = VoiceManager.get_or_create(self.bot, guild)
            await manager.rejoin_on_startup()

        logger.info("Bot is fully ready.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OnReadyEvents(bot))
