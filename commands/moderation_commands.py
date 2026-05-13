"""
Moderation commands — clear, kick, ban, unban, mute, unmute, warn, warnings.
"""

from collections import defaultdict
from datetime import timedelta
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from config import Config
from utils.helpers import make_embed
from utils.logger import setup_logger

logger = setup_logger("moderation_commands")

# In-memory warning store: guild_id → user_id → list of reason strings
_warnings: dict[int, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))


class ModerationCommands(commands.Cog, name="Moderation"):
    """Server moderation tools."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── !clear ─────────────────────────────────────────────────────────────────

    @commands.command(name="clear", aliases=["purge", "prune"], help="Delete messages (1–100).")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, amount: int = 10) -> None:
        amount = max(1, min(amount, 100))
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command itself
        embed = make_embed(
            title="🧹 Messages Cleared",
            description=f"Deleted **{len(deleted) - 1}** message(s) in {ctx.channel.mention}.",
            color=Config.COLOR_SUCCESS,
        )
        msg = await ctx.send(embed=embed)
        # Auto-delete the confirmation after 5 seconds
        await msg.delete(delay=5)
        logger.info(f"{ctx.author} cleared {len(deleted)-1} messages in {ctx.guild}.")

    # ── !kick ──────────────────────────────────────────────────────────────────

    @commands.command(name="kick", help="Kick a member from the server.")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ) -> None:
        if member.top_role >= ctx.author.top_role:
            await ctx.send(
                embed=make_embed(
                    title="🚫 Insufficient Hierarchy",
                    description="You can't kick someone with an equal or higher role.",
                    color=Config.COLOR_ERROR,
                )
            )
            return

        try:
            await member.send(
                embed=make_embed(
                    title=f"⚠️ Kicked from {ctx.guild.name}",
                    description=f"**Reason:** {reason}",
                    color=Config.COLOR_WARNING,
                )
            )
        except discord.Forbidden:
            pass  # DMs disabled

        await member.kick(reason=reason)
        embed = make_embed(
            title="👢 Member Kicked",
            description=f"**{member.mention}** has been kicked.\n**Reason:** {reason}",
            color=Config.COLOR_SUCCESS,
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} kicked {member} from {ctx.guild}. Reason: {reason}")

    # ── !ban ───────────────────────────────────────────────────────────────────

    @commands.command(name="ban", help="Ban a member from the server.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ) -> None:
        if member.top_role >= ctx.author.top_role:
            await ctx.send(
                embed=make_embed(
                    title="🚫 Insufficient Hierarchy",
                    description="You can't ban someone with an equal or higher role.",
                    color=Config.COLOR_ERROR,
                )
            )
            return

        try:
            await member.send(
                embed=make_embed(
                    title=f"🔨 Banned from {ctx.guild.name}",
                    description=f"**Reason:** {reason}",
                    color=Config.COLOR_ERROR,
                )
            )
        except discord.Forbidden:
            pass

        await member.ban(reason=reason, delete_message_days=0)
        embed = make_embed(
            title="🔨 Member Banned",
            description=f"**{member.mention}** has been banned.\n**Reason:** {reason}",
            color=Config.COLOR_SUCCESS,
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} banned {member} from {ctx.guild}. Reason: {reason}")

    # ── !unban ─────────────────────────────────────────────────────────────────

    @commands.command(name="unban", help="Unban a user by ID.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user_id: int, *, reason: str = "No reason provided.") -> None:
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            embed = make_embed(
                title="✅ User Unbanned",
                description=f"**{user}** (`{user_id}`) has been unbanned.",
                color=Config.COLOR_SUCCESS,
            )
        except discord.NotFound:
            embed = make_embed(
                title="❌ Not Found",
                description=f"No banned user found with ID `{user_id}`.",
                color=Config.COLOR_ERROR,
            )
        await ctx.send(embed=embed)

    # ── !mute (timeout) ────────────────────────────────────────────────────────

    @commands.command(name="mute", aliases=["timeout"], help="Timeout a member (in minutes).")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: int = 10,
        *,
        reason: str = "No reason provided.",
    ) -> None:
        duration = max(1, min(duration, 40320))  # Discord max: 28 days in minutes
        until = discord.utils.utcnow() + timedelta(minutes=duration)
        await member.timeout(until, reason=reason)

        embed = make_embed(
            title="🔇 Member Muted",
            description=(
                f"**{member.mention}** has been timed out for **{duration} minute(s)**.\n"
                f"**Reason:** {reason}"
            ),
            color=Config.COLOR_SUCCESS,
        )
        await ctx.send(embed=embed)
        logger.info(f"{ctx.author} muted {member} for {duration}m in {ctx.guild}.")

    # ── !unmute ────────────────────────────────────────────────────────────────

    @commands.command(name="unmute", aliases=["untimeout"], help="Remove a member's timeout.")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member) -> None:
        await member.timeout(None)
        embed = make_embed(
            title="🔊 Timeout Removed",
            description=f"**{member.mention}** can speak again.",
            color=Config.COLOR_SUCCESS,
        )
        await ctx.send(embed=embed)

    # ── !warn ──────────────────────────────────────────────────────────────────

    @commands.command(name="warn", help="Issue a warning to a member.")
    @commands.has_permissions(manage_messages=True)
    async def warn(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str,
    ) -> None:
        _warnings[ctx.guild.id][member.id].append(reason)
        count = len(_warnings[ctx.guild.id][member.id])

        try:
            await member.send(
                embed=make_embed(
                    title=f"⚠️ Warning in {ctx.guild.name}",
                    description=f"**Reason:** {reason}\nYou now have **{count}** warning(s).",
                    color=Config.COLOR_WARNING,
                )
            )
        except discord.Forbidden:
            pass

        embed = make_embed(
            title="⚠️ Warning Issued",
            description=(
                f"**{member.mention}** has been warned.\n"
                f"**Reason:** {reason}\n"
                f"**Total warnings:** {count}"
            ),
            color=Config.COLOR_WARNING,
        )
        await ctx.send(embed=embed)

    # ── !warnings ──────────────────────────────────────────────────────────────

    @commands.command(name="warnings", help="View warnings for a member.")
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx: commands.Context, member: discord.Member) -> None:
        guild_warns = _warnings[ctx.guild.id][member.id]

        if not guild_warns:
            embed = make_embed(
                title="📋 No Warnings",
                description=f"**{member.display_name}** has no warnings.",
                color=Config.COLOR_SUCCESS,
            )
        else:
            warn_list = "\n".join(f"`{i+1}.` {r}" for i, r in enumerate(guild_warns))
            embed = make_embed(
                title=f"⚠️ Warnings for {member.display_name}",
                description=warn_list,
                color=Config.COLOR_WARNING,
                footer=f"Total: {len(guild_warns)} warning(s)",
            )
        await ctx.send(embed=embed)

    # ── !clearwarnings ─────────────────────────────────────────────────────────

    @commands.command(name="clearwarnings", aliases=["resetwarns"], help="Clear all warnings for a member.")
    @commands.has_permissions(administrator=True)
    async def clearwarnings(self, ctx: commands.Context, member: discord.Member) -> None:
        _warnings[ctx.guild.id][member.id].clear()
        embed = make_embed(
            title="✅ Warnings Cleared",
            description=f"All warnings for **{member.display_name}** have been removed.",
            color=Config.COLOR_SUCCESS,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModerationCommands(bot))
