"""
Fun commands — 8ball, joke, quote, poll, flip, roll, meme.
"""

import random
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from config import Config
from utils.helpers import make_embed
from utils.logger import setup_logger

logger = setup_logger("fun_commands")

# ── Static data ────────────────────────────────────────────────────────────────

EIGHT_BALL_RESPONSES = [
    ("✅ It is certain.", Config.COLOR_SUCCESS),
    ("✅ It is decidedly so.", Config.COLOR_SUCCESS),
    ("✅ Without a doubt.", Config.COLOR_SUCCESS),
    ("✅ Yes, definitely.", Config.COLOR_SUCCESS),
    ("✅ You may rely on it.", Config.COLOR_SUCCESS),
    ("✅ As I see it, yes.", Config.COLOR_SUCCESS),
    ("✅ Most likely.", Config.COLOR_SUCCESS),
    ("✅ Outlook good.", Config.COLOR_SUCCESS),
    ("✅ Yes.", Config.COLOR_SUCCESS),
    ("✅ Signs point to yes.", Config.COLOR_SUCCESS),
    ("🤷 Reply hazy, try again.", Config.COLOR_WARNING),
    ("🤷 Ask again later.", Config.COLOR_WARNING),
    ("🤷 Better not tell you now.", Config.COLOR_WARNING),
    ("🤷 Cannot predict now.", Config.COLOR_WARNING),
    ("🤷 Concentrate and ask again.", Config.COLOR_WARNING),
    ("❌ Don't count on it.", Config.COLOR_ERROR),
    ("❌ My reply is no.", Config.COLOR_ERROR),
    ("❌ My sources say no.", Config.COLOR_ERROR),
    ("❌ Outlook not so good.", Config.COLOR_ERROR),
    ("❌ Very doubtful.", Config.COLOR_ERROR),
]

JOKES = [
    ("Why don't scientists trust atoms?", "Because they make up everything!"),
    ("What do you call a fake noodle?", "An Impasta!"),
    ("Why did the scarecrow win an award?", "He was outstanding in his field."),
    ("I told my wife she was drawing her eyebrows too high.", "She looked surprised."),
    ("Why don't skeletons fight each other?", "They don't have the guts."),
    ("What do you call cheese that isn't yours?", "Nacho cheese!"),
    ("Why can't you give Elsa a balloon?", "Because she'll let it go."),
    ("What do you call a fish without eyes?", "A fsh."),
    ("I'm reading a book about anti-gravity.", "It's impossible to put down."),
    ("Why did the bicycle fall over?", "Because it was two-tired."),
    ("What's a vampire's favourite fruit?", "A blood orange."),
    ("I used to hate facial hair…", "But then it grew on me."),
    ("Why do bees have sticky hair?", "Because they use a honeycomb."),
    ("What do you call a sleeping dinosaur?", "A dino-snore."),
    ("I asked my dog what 2 minus 2 is.", "He said nothing."),
]

QUOTES = [
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("Innovation distinguishes between a leader and a follower.", "Steve Jobs"),
    ("In the middle of every difficulty lies opportunity.", "Albert Einstein"),
    ("Life is what happens when you're busy making other plans.", "John Lennon"),
    ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("You miss 100% of the shots you don't take.", "Wayne Gretzky"),
    ("Whether you think you can or you think you can't, you're right.", "Henry Ford"),
    ("I have not failed. I've just found 10,000 ways that won't work.", "Thomas Edison"),
    ("The best time to plant a tree was 20 years ago. The second best time is now.", "Chinese Proverb"),
    ("An unexamined life is not worth living.", "Socrates"),
    ("Spread love everywhere you go.", "Mother Teresa"),
    ("When you reach the end of your rope, tie a knot in it and hang on.", "Franklin D. Roosevelt"),
    ("Always remember that you are absolutely unique. Just like everyone else.", "Margaret Mead"),
    ("Do not go where the path may lead; go instead where there is no path and leave a trail.", "Ralph Waldo Emerson"),
]


class FunCommands(commands.Cog, name="Fun"):
    """Fun and entertainment commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── !8ball ─────────────────────────────────────────────────────────────────

    @commands.command(name="8ball", aliases=["eightball"], help="Ask the magic 8-ball a question.")
    async def eight_ball(self, ctx: commands.Context, *, question: str) -> None:
        response, color = random.choice(EIGHT_BALL_RESPONSES)
        embed = make_embed(
            title="🎱 Magic 8-Ball",
            color=color,
        )
        embed.add_field(name="❓ Question", value=question, inline=False)
        embed.add_field(name="🔮 Answer", value=response, inline=False)
        await ctx.send(embed=embed)

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question.")
    @app_commands.describe(question="Your yes/no question")
    async def eight_ball_slash(self, interaction: discord.Interaction, question: str) -> None:
        response, color = random.choice(EIGHT_BALL_RESPONSES)
        embed = make_embed(title="🎱 Magic 8-Ball", color=color)
        embed.add_field(name="❓ Question", value=question, inline=False)
        embed.add_field(name="🔮 Answer", value=response, inline=False)
        await interaction.response.send_message(embed=embed)

    # ── !joke ──────────────────────────────────────────────────────────────────

    @commands.command(name="joke", help="Get a random joke.")
    async def joke(self, ctx: commands.Context) -> None:
        setup_line, punchline = random.choice(JOKES)
        embed = make_embed(title="😂 Random Joke", color=Config.COLOR_PRIMARY)
        embed.add_field(name="Setup", value=setup_line, inline=False)
        embed.add_field(name="Punchline", value=f"||{punchline}||", inline=False)
        embed.set_footer(text="Click the spoiler to reveal the punchline!")
        await ctx.send(embed=embed)

    @app_commands.command(name="joke", description="Get a random joke.")
    async def joke_slash(self, interaction: discord.Interaction) -> None:
        setup_line, punchline = random.choice(JOKES)
        embed = make_embed(title="😂 Random Joke", color=Config.COLOR_PRIMARY)
        embed.add_field(name="Setup", value=setup_line, inline=False)
        embed.add_field(name="Punchline", value=f"||{punchline}||", inline=False)
        embed.set_footer(text="Click the spoiler to reveal the punchline!")
        await interaction.response.send_message(embed=embed)

    # ── !quote ─────────────────────────────────────────────────────────────────

    @commands.command(name="quote", aliases=["inspire"], help="Get an inspirational quote.")
    async def quote(self, ctx: commands.Context) -> None:
        text, author = random.choice(QUOTES)
        embed = make_embed(
            title="💬 Inspirational Quote",
            description=f'*"{text}"*\n\n— **{author}**',
            color=Config.COLOR_INFO,
        )
        await ctx.send(embed=embed)

    @app_commands.command(name="quote", description="Get a random inspirational quote.")
    async def quote_slash(self, interaction: discord.Interaction) -> None:
        text, author = random.choice(QUOTES)
        embed = make_embed(
            title="💬 Inspirational Quote",
            description=f'*"{text}"*\n\n— **{author}**',
            color=Config.COLOR_INFO,
        )
        await interaction.response.send_message(embed=embed)

    # ── !poll ──────────────────────────────────────────────────────────────────

    @commands.command(name="poll", help="Create a quick yes/no poll.")
    async def poll(self, ctx: commands.Context, *, question: str) -> None:
        embed = make_embed(
            title="📊 Poll",
            description=question,
            color=Config.COLOR_PRIMARY,
            footer=f"Poll by {ctx.author.display_name}",
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await msg.add_reaction("🤷")

    @app_commands.command(name="poll", description="Create a quick yes/no poll.")
    @app_commands.describe(question="The poll question")
    async def poll_slash(self, interaction: discord.Interaction, question: str) -> None:
        embed = make_embed(
            title="📊 Poll",
            description=question,
            color=Config.COLOR_PRIMARY,
            footer=f"Poll by {interaction.user.display_name}",
        )
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await msg.add_reaction("🤷")

    # ── !flip ──────────────────────────────────────────────────────────────────

    @commands.command(name="flip", aliases=["coinflip"], help="Flip a coin.")
    async def flip(self, ctx: commands.Context) -> None:
        result = random.choice([("Heads! 🪙", Config.COLOR_SUCCESS), ("Tails! 🪙", Config.COLOR_WARNING)])
        embed = make_embed(title="🪙 Coin Flip", description=result[0], color=result[1])
        await ctx.send(embed=embed)

    @app_commands.command(name="flip", description="Flip a coin.")
    async def flip_slash(self, interaction: discord.Interaction) -> None:
        result = random.choice([("Heads! 🪙", Config.COLOR_SUCCESS), ("Tails! 🪙", Config.COLOR_WARNING)])
        embed = make_embed(title="🪙 Coin Flip", description=result[0], color=result[1])
        await interaction.response.send_message(embed=embed)

    # ── !roll ──────────────────────────────────────────────────────────────────

    @commands.command(name="roll", aliases=["dice"], help="Roll a dice (default: 6 sides).")
    async def roll(self, ctx: commands.Context, sides: int = 6) -> None:
        sides = max(2, min(sides, 1000))
        result = random.randint(1, sides)
        embed = make_embed(
            title="🎲 Dice Roll",
            description=f"Rolling a **d{sides}**...\n\nYou rolled: **{result}**",
            color=Config.COLOR_INFO,
        )
        await ctx.send(embed=embed)

    @app_commands.command(name="roll", description="Roll a dice.")
    @app_commands.describe(sides="Number of sides on the dice (default: 6)")
    async def roll_slash(self, interaction: discord.Interaction, sides: int = 6) -> None:
        sides = max(2, min(sides, 1000))
        result = random.randint(1, sides)
        embed = make_embed(
            title="🎲 Dice Roll",
            description=f"Rolling a **d{sides}**...\n\nYou rolled: **{result}**",
            color=Config.COLOR_INFO,
        )
        await interaction.response.send_message(embed=embed)

    # ── !choose ────────────────────────────────────────────────────────────────

    @commands.command(name="choose", help="Choose between multiple options (separate with |).")
    async def choose(self, ctx: commands.Context, *, options: str) -> None:
        choices = [o.strip() for o in options.split("|") if o.strip()]
        if len(choices) < 2:
            await ctx.send(
                embed=make_embed(
                    title="❌ Not enough options",
                    description="Provide at least 2 options separated by `|`.\nExample: `!choose pizza | burger | sushi`",
                    color=Config.COLOR_ERROR,
                )
            )
            return
        picked = random.choice(choices)
        embed = make_embed(
            title="🎯 I Choose…",
            description=f"**{picked}**",
            color=Config.COLOR_SUCCESS,
            footer=f"Chosen from {len(choices)} options",
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FunCommands(bot))
