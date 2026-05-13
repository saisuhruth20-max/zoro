"""
General-purpose helper utilities used across the bot.
"""

import re
import textwrap
from typing import Optional

import discord


def make_embed(
    title: str = "",
    description: str = "",
    color: int = 0x5865F2,
    footer: Optional[str] = None,
    thumbnail: Optional[str] = None,
    image_url: Optional[str] = None,
    author_name: Optional[str] = None,
    author_icon: Optional[str] = None,
) -> discord.Embed:
    """
    Build a styled Discord Embed.

    Args:
        title:       Embed title.
        description: Embed description (supports markdown).
        color:       Sidebar colour as an integer (e.g. 0x5865F2).
        footer:      Optional footer text.
        thumbnail:   Optional thumbnail URL.
        image_url:   Optional large image URL.
        author_name: Optional author display name.
        author_icon: Optional author icon URL.

    Returns:
        Fully configured discord.Embed.
    """
    embed = discord.Embed(title=title, description=description, color=color)

    if footer:
        embed.set_footer(text=footer)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image_url:
        embed.set_image(url=image_url)
    if author_name:
        embed.set_author(name=author_name, icon_url=author_icon or discord.Embed.Empty)

    return embed


def chunk_text(text: str, max_length: int = 2000) -> list[str]:
    """
    Split a long string into chunks that fit within Discord's message limit.

    Args:
        text:       The text to split.
        max_length: Maximum length per chunk (default: 2000).

    Returns:
        List of string chunks.
    """
    if len(text) <= max_length:
        return [text]
    return textwrap.wrap(text, max_length, break_long_words=True, replace_whitespace=False)


def strip_mentions(text: str) -> str:
    """Remove Discord mention syntax from a string."""
    return re.sub(r"<@!?\d+>|<@&\d+>|<#\d+>", "", text).strip()


def format_duration(seconds: float) -> str:
    """Convert a duration in seconds into a human-readable string (e.g. '2m 30s')."""
    seconds = int(seconds)
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def user_display(member: discord.Member) -> str:
    """Return the best display name for a guild member."""
    return member.display_name or member.name
