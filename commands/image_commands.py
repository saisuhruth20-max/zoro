"""
Image generation commands — !image and /image using Pollinations AI.
"""

import urllib.parse

import discord
from discord import app_commands
from discord.ext import commands

from config import Config
from utils.helpers import make_embed
from utils.logger import setup_logger

logger = setup_logger("image_commands")


def _build_image_url(prompt: str) -> str:
    """
    Build a Pollinations AI image URL for the given prompt.

    Args:
        prompt: The image generation prompt.

    Returns:
        A fully-qualified image URL string.
    """
    encoded = urllib.parse.quote(prompt)
    base = Config.POLLINATIONS_URL.format(prompt=encoded)
    return (
        f"{base}"
        f"?width={Config.IMAGE_WIDTH}"
        f"&height={Config.IMAGE_HEIGHT}"
        f"&model={Config.IMAGE_MODEL}"
        f"&nologo=true"
        f"&enhance=true"
    )


class ImageCommands(commands.Cog, name="Images"):
    """AI image generation commands via Pollinations."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── !image ─────────────────────────────────────────────────────────────────

    @commands.command(name="image", aliases=["img", "generate"], help="Generate an AI image.")
    @commands.cooldown(1, Config.COOLDOWN_IMAGE, commands.BucketType.user)
    async def image(self, ctx: commands.Context, *, prompt: str) -> None:
        """Prefix command: !image <prompt>"""
        async with ctx.typing():
            image_url = _build_image_url(prompt)

        embed = make_embed(
            title="🎨 Image Generated",
            description=f"**Prompt:** {prompt}",
            color=Config.COLOR_PRIMARY,
            image_url=image_url,
            footer=f"Requested by {ctx.author.display_name} • Powered by Pollinations AI",
        )
        embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.display_avatar.url,
        )

        await ctx.send(embed=embed)
        logger.info(f"Image generated for '{prompt}' by {ctx.author}")

    # ── /image (slash) ──────────────────────────────────────────────────────────

    @app_commands.command(name="image", description="Generate an AI image from a text prompt.")
    @app_commands.describe(prompt="Describe the image you want to generate")
    async def image_slash(self, interaction: discord.Interaction, prompt: str) -> None:
        """Slash command: /image prompt:<prompt>"""
        await interaction.response.defer(thinking=True)

        image_url = _build_image_url(prompt)

        embed = make_embed(
            title="🎨 Image Generated",
            description=f"**Prompt:** {prompt}",
            color=Config.COLOR_PRIMARY,
            image_url=image_url,
            footer=f"Requested by {interaction.user.display_name} • Powered by Pollinations AI",
        )
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.followup.send(embed=embed)
        logger.info(f"Image generated (slash) for '{prompt}' by {interaction.user}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ImageCommands(bot))
