"""
AI commands — !ask, /ask, and !forget using Groq with per-user conversation memory.
"""

import os

import discord
from discord import app_commands
from discord.ext import commands
from groq import AsyncGroq

from config import Config
from utils.helpers import make_embed, chunk_text
from utils.logger import setup_logger
from utils.memory import memory

logger = setup_logger("ai_commands")


def _groq_client() -> AsyncGroq:
    """Create a new Groq async client using the configured API key."""
    api_key = os.getenv("GROQ_API_KEY") or Config.GROQ_API_KEY
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")
    return AsyncGroq(api_key=api_key)


async def _ask_groq(user_id: int, question: str) -> str:
    """
    Send a question to Groq, prepending the user's conversation history.

    Args:
        user_id:  Discord user ID (used to look up per-user memory).
        question: The user's current question/message.

    Returns:
        The model's response as a string.
    """
    client = _groq_client()

    # Build the message list: system prompt + conversation history + new question
    messages = [{"role": "system", "content": Config.AI_SYSTEM_PROMPT}]
    messages.extend(memory.get_history(user_id))
    messages.append({"role": "user", "content": question})

    response = await client.chat.completions.create(
        model=Config.GROQ_MODEL,
        messages=messages,  # type: ignore[arg-type]
        max_tokens=Config.AI_MAX_TOKENS,
        temperature=Config.AI_TEMPERATURE,
    )

    answer = response.choices[0].message.content or "(No response)"

    # Persist both sides of the conversation
    memory.add_user_message(user_id, question)
    memory.add_assistant_message(user_id, answer)

    return answer


class AICommands(commands.Cog, name="AI"):
    """AI chat commands powered by Groq."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── !ask ───────────────────────────────────────────────────────────────────

    @commands.command(name="ask", help="Ask the AI a question.")
    @commands.cooldown(1, Config.COOLDOWN_AI, commands.BucketType.user)
    async def ask(self, ctx: commands.Context, *, question: str) -> None:
        """Prefix command: !ask <question>"""
        async with ctx.typing():
            try:
                answer = await _ask_groq(ctx.author.id, question)
            except Exception as e:
                logger.error(f"Groq API error: {e}")
                await ctx.send(
                    embed=make_embed(
                        title="❌ AI Error",
                        description="Could not reach the AI. Please try again later.",
                        color=Config.COLOR_ERROR,
                    )
                )
                return

        # Send in chunks if the response is long
        chunks = chunk_text(answer, max_length=3900)
        for i, chunk in enumerate(chunks):
            embed = make_embed(
                title="🤖 AI Response" if i == 0 else "",
                description=chunk,
                color=Config.COLOR_PRIMARY,
                footer=f"Asked by {ctx.author.display_name} • Model: {Config.GROQ_MODEL}",
            )
            if i == 0:
                embed.set_author(
                    name=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                )
            await ctx.send(embed=embed)

    # ── /ask (slash) ────────────────────────────────────────────────────────────

    @app_commands.command(name="ask", description="Ask the AI a question.")
    @app_commands.describe(question="Your question for the AI")
    async def ask_slash(self, interaction: discord.Interaction, question: str) -> None:
        """Slash command: /ask question:<question>"""
        await interaction.response.defer(thinking=True)
        try:
            answer = await _ask_groq(interaction.user.id, question)
        except Exception as e:
            logger.error(f"Groq API error (slash): {e}")
            await interaction.followup.send(
                embed=make_embed(
                    title="❌ AI Error",
                    description="Could not reach the AI. Please try again later.",
                    color=Config.COLOR_ERROR,
                )
            )
            return

        chunks = chunk_text(answer, max_length=3900)
        for i, chunk in enumerate(chunks):
            embed = make_embed(
                title="🤖 AI Response" if i == 0 else "",
                description=chunk,
                color=Config.COLOR_PRIMARY,
                footer=f"Asked by {interaction.user.display_name} • Model: {Config.GROQ_MODEL}",
            )
            if i == 0:
                embed.set_author(
                    name=interaction.user.display_name,
                    icon_url=interaction.user.display_avatar.url,
                )
            await interaction.followup.send(embed=embed)

    # ── !forget ────────────────────────────────────────────────────────────────

    @commands.command(name="forget", help="Clear your AI conversation memory.")
    async def forget(self, ctx: commands.Context) -> None:
        memory.clear(ctx.author.id)
        embed = make_embed(
            title="🗑️ Memory Cleared",
            description="Your conversation history has been wiped. Fresh start!",
            color=Config.COLOR_SUCCESS,
        )
        await ctx.send(embed=embed)

    @app_commands.command(name="forget", description="Clear your AI conversation memory.")
    async def forget_slash(self, interaction: discord.Interaction) -> None:
        memory.clear(interaction.user.id)
        embed = make_embed(
            title="🗑️ Memory Cleared",
            description="Your conversation history has been wiped. Fresh start!",
            color=Config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AICommands(bot))
