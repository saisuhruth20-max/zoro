"""
General commands — ping, help, info, and clear.
"""

import platform
import time
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from config import Config
from utils.helpers import make_embed
from utils.logger import setup_logger

logger = setup_logger("general_commands")


class GeneralCommands(commands.Cog, name="General"):
    """General-purpose bot commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._start_time = datetime.now(timezone.utc)

    # ── !ping ──────────────────────────────────────────────────────────────────

    @commands.command(name="ping", help="Check the bot's latency.")
    async def ping(self, ctx: commands.Context) -> None:
        start = time.perf_counter()
        msg = await ctx.send("Pinging…")
        end = time.perf_counter()

        api_latency = round(self.bot.latency * 1000)
        msg_latency = round((end - start) * 1000)

        embed = make_embed(
            title="🏓 Pong!",
            description=(
                f"**WebSocket latency:** `{api_latency}ms`\n"
                f"**Message latency:** `{msg_latency}ms`"
            ),
            color=Config.COLOR_SUCCESS,
        )
        await msg.edit(content=None, embed=embed)

    # Slash version
    @app_commands.command(name="ping", description="Check the bot's latency.")
    async def ping_slash(self, interaction: discord.Interaction) -> None:
        latency = round(self.bot.latency * 1000)
        embed = make_embed(
            title="🏓 Pong!",
            description=f"**WebSocket latency:** `{latency}ms`",
            color=Config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)

    # ── !help ──────────────────────────────────────────────────────────────────

    @commands.command(name="help", help="Show all available commands.")
    async def help_command(self, ctx: commands.Context) -> None:
        p = Config.PREFIX
        embed = make_embed(
            title="📚 Command Help",
            description=f"Prefix: `{p}` — Slash commands also supported (`/`)",
            color=Config.COLOR_PRIMARY,
        )

        embed.add_field(
            name="🤖 AI",
            value=(
                f"`{p}ask <question>` — Chat with the AI (memory enabled)\n"
                f"`{p}forget` — Clear your conversation memory\n"
                f"`/ask` `/forget` — Slash versions"
            ),
            inline=False,
        )
        embed.add_field(
            name="🎨 Images",
            value=(
                f"`{p}image <prompt>` — Generate an AI image\n"
                f"`/image` — Slash version"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔊 Voice",
            value=(
                f"`{p}setvc [#channel]` — Set permanent voice channel\n"
                f"`{p}joinvc` — Join your current voice channel\n"
                f"`{p}leavevc` — Disconnect and clear permanent VC\n"
                f"`{p}tts <text>` — Speak text via TTS\n"
                f"`/vcstatus` — Show voice channel status"
            ),
            inline=False,
        )
        embed.add_field(
            name="🎮 Fun",
            value=(
                f"`{p}8ball <question>` — Magic 8-ball\n"
                f"`{p}joke` — Random joke\n"
                f"`{p}quote` — Inspirational quote\n"
                f"`{p}poll <question>` — Create a poll\n"
                f"`{p}flip` — Flip a coin\n"
                f"`{p}roll [sides]` — Roll a dice\n"
                f"`{p}choose a | b | c` — Pick an option"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔧 Utility",
            value=(
                f"`{p}serverinfo` — Server information\n"
                f"`{p}userinfo [@user]` — User information\n"
                f"`{p}avatar [@user]` — Show avatar\n"
                f"`{p}afk [reason]` — Set AFK status\n"
                f"`{p}remind <10s/5m/2h> <msg>` — Set a reminder"
            ),
            inline=False,
        )
        embed.add_field(
            name="🛡️ Moderation",
            value=(
                f"`{p}clear <1-100>` — Delete messages\n"
                f"`{p}kick @user [reason]` — Kick a member\n"
                f"`{p}ban @user [reason]` — Ban a member\n"
                f"`{p}unban <user_id>` — Unban a user\n"
                f"`{p}mute @user [mins]` — Timeout a member\n"
                f"`{p}unmute @user` — Remove timeout\n"
                f"`{p}warn @user <reason>` — Issue a warning\n"
                f"`{p}warnings @user` — View warnings"
            ),
            inline=False,
        )
        embed.add_field(
            name="🛠️ General",
            value=(
                f"`{p}ping` — Check latency\n"
                f"`{p}info` — Bot information\n"
                f"`{p}help` — This menu"
            ),
            inline=False,
        )
        embed.set_footer(text=f"Bot v{Config.BOT_VERSION}")
        await ctx.send(embed=embed)

    # Slash version
    @app_commands.command(name="help", description="Show all available commands.")
    async def help_slash(self, interaction: discord.Interaction) -> None:
        # Re-use the same logic by creating a fake context-like response
        p = Config.PREFIX
        embed = make_embed(
            title="📚 Command Help",
            description=f"Prefix: `{p}` — Slash commands also supported (`/`)",
            color=Config.COLOR_PRIMARY,
        )
        embed.add_field(
            name="🤖 AI",
            value=f"`{p}ask` / `/ask` — Chat with AI\n`{p}forget` — Clear memory",
            inline=False,
        )
        embed.add_field(
            name="🎨 Images",
            value=f"`{p}image` / `/image` — Generate AI image",
            inline=False,
        )
        embed.add_field(
            name="🔊 Voice",
            value=f"`{p}setvc` `{p}joinvc` `{p}leavevc` `{p}tts`",
            inline=False,
        )
        embed.add_field(name="🛠️ General", value=f"`{p}ping` `{p}info` `{p}help`", inline=False)
        embed.set_footer(text=f"Bot v{Config.BOT_VERSION}")
        await interaction.response.send_message(embed=embed)

    # ── !info ──────────────────────────────────────────────────────────────────

    @commands.command(name="info", help="Display information about the bot.")
    async def info(self, ctx: commands.Context) -> None:
        uptime = datetime.now(timezone.utc) - self._start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        embed = make_embed(
            title="ℹ️ Bot Information",
            color=Config.COLOR_INFO,
        )
        embed.add_field(name="Version", value=Config.BOT_VERSION, inline=True)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Uptime", value=f"{hours}h {minutes}m {seconds}s", inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="discord.py", value=discord.__version__, inline=True)

        if self.bot.user and self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GeneralCommands(bot))
