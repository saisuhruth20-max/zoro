"""
Utility commands — serverinfo, userinfo, avatar, afk, remind.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from config import Config
from utils.helpers import make_embed, format_duration
from utils.logger import setup_logger

logger = setup_logger("utility_commands")

# AFK store: user_id → (reason, timestamp)
_afk_users: dict[int, tuple[str, datetime]] = {}


def _parse_time(time_str: str) -> Optional[int]:
    """
    Parse a time string like '10s', '5m', '2h' into seconds.

    Returns None if the format is invalid.
    """
    units = {"s": 1, "m": 60, "h": 3600}
    time_str = time_str.strip().lower()
    if not time_str:
        return None
    unit = time_str[-1]
    if unit not in units:
        return None
    try:
        value = int(time_str[:-1])
        return value * units[unit]
    except ValueError:
        return None


class UtilityCommands(commands.Cog, name="Utility"):
    """Useful utility commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── !serverinfo ────────────────────────────────────────────────────────────

    @commands.command(name="serverinfo", aliases=["guildinfo", "si"], help="Show server information.")
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context) -> None:
        guild = ctx.guild
        created = guild.created_at.strftime("%B %d, %Y")
        online = sum(
            1
            for m in guild.members
            if m.status != discord.Status.offline and not m.bot
        )

        embed = make_embed(
            title=f"🏠 {guild.name}",
            color=Config.COLOR_PRIMARY,
            thumbnail=guild.icon.url if guild.icon else None,
        )
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created", value=created, inline=True)
        embed.add_field(name="Region", value="Global", inline=True)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Online", value=str(online), inline=True)
        embed.add_field(name="Bots", value=str(sum(1 for m in guild.members if m.bot)), inline=True)
        embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Emojis", value=str(len(guild.emojis)), inline=True)
        embed.add_field(name="Boost Level", value=str(guild.premium_tier), inline=True)
        embed.add_field(name="Boosts", value=str(guild.premium_subscription_count), inline=True)
        embed.add_field(name="Server ID", value=str(guild.id), inline=True)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @app_commands.command(name="serverinfo", description="Show information about this server.")
    async def serverinfo_slash(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return
        created = guild.created_at.strftime("%B %d, %Y")
        embed = make_embed(
            title=f"🏠 {guild.name}",
            color=Config.COLOR_PRIMARY,
            thumbnail=guild.icon.url if guild.icon else None,
        )
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created", value=created, inline=True)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Boost Level", value=str(guild.premium_tier), inline=True)
        await interaction.response.send_message(embed=embed)

    # ── !userinfo ──────────────────────────────────────────────────────────────

    @commands.command(name="userinfo", aliases=["whois", "ui"], help="Show info about a user.")
    @commands.guild_only()
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None) -> None:
        member = member or ctx.author
        joined = member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown"
        created = member.created_at.strftime("%B %d, %Y")
        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        roles_str = " ".join(roles[-10:]) if roles else "None"  # show last 10

        embed = make_embed(
            title=f"👤 {member.display_name}",
            color=member.color if member.color.value else Config.COLOR_PRIMARY,
            thumbnail=member.display_avatar.url,
        )
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Bot", value="Yes" if member.bot else "No", inline=True)
        embed.add_field(name="Joined Server", value=joined, inline=True)
        embed.add_field(name="Account Created", value=created, inline=True)
        embed.add_field(name="Status", value=str(member.status).title(), inline=True)
        embed.add_field(name=f"Roles ({len(roles)})", value=roles_str or "None", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @app_commands.command(name="userinfo", description="Show information about a user.")
    @app_commands.describe(member="The member to inspect (defaults to you)")
    async def userinfo_slash(self, interaction: discord.Interaction, member: discord.Member = None) -> None:
        member = member or interaction.user
        joined = member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown"
        created = member.created_at.strftime("%B %d, %Y")
        embed = make_embed(
            title=f"👤 {member.display_name}",
            color=Config.COLOR_PRIMARY,
            thumbnail=member.display_avatar.url,
        )
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Joined", value=joined, inline=True)
        embed.add_field(name="Created", value=created, inline=True)
        await interaction.response.send_message(embed=embed)

    # ── !avatar ────────────────────────────────────────────────────────────────

    @commands.command(name="avatar", aliases=["av", "pfp"], help="Show a user's avatar.")
    async def avatar(self, ctx: commands.Context, member: discord.Member = None) -> None:
        member = member or ctx.author
        embed = make_embed(
            title=f"🖼️ {member.display_name}'s Avatar",
            color=Config.COLOR_PRIMARY,
            image_url=member.display_avatar.url,
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @app_commands.command(name="avatar", description="Show a user's avatar.")
    @app_commands.describe(member="The member whose avatar to show")
    async def avatar_slash(self, interaction: discord.Interaction, member: discord.Member = None) -> None:
        member = member or interaction.user
        embed = make_embed(
            title=f"🖼️ {member.display_name}'s Avatar",
            color=Config.COLOR_PRIMARY,
            image_url=member.display_avatar.url,
        )
        await interaction.response.send_message(embed=embed)

    # ── !afk ───────────────────────────────────────────────────────────────────

    @commands.command(name="afk", help="Set yourself as AFK with an optional reason.")
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK") -> None:
        _afk_users[ctx.author.id] = (reason, datetime.now(timezone.utc))
        embed = make_embed(
            title="💤 AFK Set",
            description=f"You're now AFK: *{reason}*",
            color=Config.COLOR_INFO,
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Clear AFK status when the user sends a message, and notify when an AFK user is pinged."""
        if message.author.bot:
            return

        # Clear AFK if the author was AFK
        if message.author.id in _afk_users:
            reason, since = _afk_users.pop(message.author.id)
            delta = datetime.now(timezone.utc) - since
            embed = make_embed(
                title="✅ AFK Cleared",
                description=f"Welcome back! You were AFK for `{format_duration(delta.total_seconds())}`.",
                color=Config.COLOR_SUCCESS,
            )
            await message.channel.send(embed=embed, delete_after=8)

        # Notify if an AFK user was mentioned
        for mentioned in message.mentions:
            if mentioned.id in _afk_users:
                reason, since = _afk_users[mentioned.id]
                delta = datetime.now(timezone.utc) - since
                embed = make_embed(
                    title="💤 User is AFK",
                    description=(
                        f"**{mentioned.display_name}** is AFK: *{reason}*\n"
                        f"Gone for `{format_duration(delta.total_seconds())}`."
                    ),
                    color=Config.COLOR_WARNING,
                )
                await message.channel.send(embed=embed, delete_after=10)

    # ── !remind ────────────────────────────────────────────────────────────────

    @commands.command(name="remind", aliases=["reminder"], help="Set a reminder. Time: 10s, 5m, 2h.")
    async def remind(self, ctx: commands.Context, time_str: str, *, reminder: str) -> None:
        seconds = _parse_time(time_str)
        if seconds is None or seconds <= 0:
            await ctx.send(
                embed=make_embed(
                    title="❌ Invalid Time",
                    description="Use a format like `10s`, `5m`, or `2h`.\nExample: `!remind 10m Take a break`",
                    color=Config.COLOR_ERROR,
                )
            )
            return

        max_seconds = 24 * 3600
        if seconds > max_seconds:
            await ctx.send(
                embed=make_embed(
                    title="❌ Too Long",
                    description="Maximum reminder duration is 24 hours.",
                    color=Config.COLOR_ERROR,
                )
            )
            return

        await ctx.send(
            embed=make_embed(
                title="⏰ Reminder Set",
                description=f"I'll remind you in **{format_duration(seconds)}**:\n*{reminder}*",
                color=Config.COLOR_SUCCESS,
            )
        )

        await asyncio.sleep(seconds)

        embed = make_embed(
            title="⏰ Reminder!",
            description=f"{ctx.author.mention}, you asked me to remind you:\n\n*{reminder}*",
            color=Config.COLOR_PRIMARY,
        )
        await ctx.send(content=ctx.author.mention, embed=embed)

    @app_commands.command(name="remind", description="Set a reminder (e.g. 10s, 5m, 2h).")
    @app_commands.describe(time="Duration, e.g. 10s, 5m, 2h", reminder="What to remind you about")
    async def remind_slash(self, interaction: discord.Interaction, time: str, reminder: str) -> None:
        seconds = _parse_time(time)
        if seconds is None or seconds <= 0 or seconds > 86400:
            await interaction.response.send_message(
                embed=make_embed(
                    title="❌ Invalid Time",
                    description="Use `10s`, `5m`, or `2h`. Maximum is 24h.",
                    color=Config.COLOR_ERROR,
                ),
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            embed=make_embed(
                title="⏰ Reminder Set",
                description=f"I'll remind you in **{format_duration(seconds)}**:\n*{reminder}*",
                color=Config.COLOR_SUCCESS,
            )
        )
        await asyncio.sleep(seconds)
        await interaction.followup.send(
            content=interaction.user.mention,
            embed=make_embed(
                title="⏰ Reminder!",
                description=f"You asked me to remind you:\n\n*{reminder}*",
                color=Config.COLOR_PRIMARY,
            ),
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UtilityCommands(bot))
