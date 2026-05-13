"""
Discord AI Bot - Main Entry Point
Production-ready bot with AI chat, image generation, voice features, and web dashboard.
"""

import asyncio
import logging
import os
import sys
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import Config
from utils.logger import setup_logger
from utils.stats import stats
from web.dashboard import start_dashboard_thread

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger("main")


def create_bot() -> commands.Bot:
    """Create and configure the Discord bot instance."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.voice_states = True
    intents.guilds = True

    bot = commands.Bot(
        command_prefix=Config.PREFIX,
        intents=intents,
        help_command=None,  # We use a custom help command
        case_insensitive=True,
        description=Config.BOT_DESCRIPTION,
    )

    return bot


async def load_extensions(bot: commands.Bot) -> None:
    """Load all cog extensions."""
    extensions = [
        # Commands
        "commands.general_commands",
        "commands.ai_commands",
        "commands.image_commands",
        "commands.voice_commands",
        "commands.moderation_commands",
        "commands.fun_commands",
        "commands.utility_commands",
        # Events
        "events.on_ready",
        "events.on_voice_state_update",
        "events.on_member_events",
    ]

    for extension in extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f"Loaded extension: {extension}")
        except Exception as e:
            logger.error(f"Failed to load extension {extension}: {e}")
            traceback.print_exc()


async def main() -> None:
    """Main coroutine to run the bot."""
    bot = create_bot()

    # Give the stats tracker a reference to the bot
    stats.bot = bot

    # ── Command usage tracking ─────────────────────────────────────────────────
    @bot.event
    async def on_command(ctx: commands.Context) -> None:
        """Record every successful prefix command invocation."""
        guild_name = ctx.guild.name if ctx.guild else "DM"
        stats.record_command(
            command_name=ctx.command.name,
            user=str(ctx.author),
            guild=guild_name,
        )

    # ── Global error handler ───────────────────────────────────────────────────
    @bot.event
    async def on_error(event: str, *args, **kwargs) -> None:
        logger.error(f"Unhandled error in event '{event}':")
        traceback.print_exc()

    @bot.event
    async def on_command_error(ctx: commands.Context, error: Exception) -> None:
        """Global command error handler — provides user-friendly responses."""
        if isinstance(error, commands.CommandNotFound):
            return  # Silently ignore unknown commands
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                embed=discord.Embed(
                    title="❌ Missing Argument",
                    description=f"Missing required argument: `{error.param.name}`",
                    color=Config.COLOR_ERROR,
                )
            )
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                embed=discord.Embed(
                    title="⏳ Cooldown",
                    description=f"Command on cooldown. Try again in `{error.retry_after:.1f}s`.",
                    color=Config.COLOR_WARNING,
                )
            )
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=discord.Embed(
                    title="🚫 Missing Permissions",
                    description="You don't have permission to use this command.",
                    color=Config.COLOR_ERROR,
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=discord.Embed(
                    title="🤖 Bot Missing Permissions",
                    description=f"I need the following permissions: `{', '.join(error.missing_permissions)}`",
                    color=Config.COLOR_ERROR,
                )
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(
                    title="❌ Bad Argument",
                    description=str(error),
                    color=Config.COLOR_ERROR,
                )
            )
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                embed=discord.Embed(
                    title="❌ Server Only",
                    description="This command can only be used in a server.",
                    color=Config.COLOR_ERROR,
                )
            )
        else:
            logger.error(f"Unhandled command error in '{ctx.command}': {error}")
            await ctx.send(
                embed=discord.Embed(
                    title="❌ Unexpected Error",
                    description="An unexpected error occurred. Please try again later.",
                    color=Config.COLOR_ERROR,
                )
            )
            raise error

    async with bot:
        await load_extensions(bot)
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            logger.critical("DISCORD_TOKEN is not set. Exiting.")
            sys.exit(1)
        logger.info("Starting bot...")
        await bot.start(token)


if __name__ == "__main__":
    # Start the web dashboard in a background thread BEFORE the bot
    # so Railway's health check can hit /health immediately.
    start_dashboard_thread()
    logger.info("Web dashboard thread started.")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
