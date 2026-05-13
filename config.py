"""
Configuration module — loads all environment variables and defines constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Bot core ──────────────────────────────────────────────────────────────
    PREFIX: str = "!"
    BOT_DESCRIPTION: str = "An AI-powered Discord bot with voice, chat, and image features."
    BOT_VERSION: str = "1.0.0"

    # ── Credentials ───────────────────────────────────────────────────────────
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # ── AI settings ───────────────────────────────────────────────────────────
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    AI_MAX_TOKENS: int = 1024
    AI_TEMPERATURE: float = 0.7
    AI_SYSTEM_PROMPT: str = (
        "You are a friendly, helpful, and witty AI assistant living inside a Discord bot. "
        "Keep responses concise and engaging. Use markdown formatting when appropriate. "
        "You are knowledgeable but approachable, and you have a good sense of humor."
    )
    # Maximum number of conversation turns to keep in memory per user
    MEMORY_MAX_TURNS: int = 10

    # ── Image generation ──────────────────────────────────────────────────────
    POLLINATIONS_URL: str = "https://image.pollinations.ai/prompt/{prompt}"
    IMAGE_WIDTH: int = 1024
    IMAGE_HEIGHT: int = 1024
    IMAGE_MODEL: str = "flux"

    # ── Voice / TTS ───────────────────────────────────────────────────────────
    TTS_LANGUAGE: str = "en"
    TTS_SLOW: bool = False
    TTS_AUDIO_DIR: str = "tts_audio"
    # Time in seconds before deleting a TTS file after playback
    TTS_CLEANUP_DELAY: float = 5.0
    # Seconds to wait before attempting a VC reconnect
    VC_RECONNECT_DELAY: float = 5.0

    # ── Personalized announcements ────────────────────────────────────────────
    # Maps Discord user ID (int) → (join_phrase, leave_phrase)
    USER_ANNOUNCEMENTS: dict[int, tuple[str, str]] = {
        # Example — replace with real user IDs and phrases:
        # 123456789012345678: ("Welcome back, Alex!", "Alex left the battlefield!"),
    }

    # ── Embed colours ─────────────────────────────────────────────────────────
    COLOR_PRIMARY: int = 0x5865F2    # Discord blurple
    COLOR_SUCCESS: int = 0x57F287    # Green
    COLOR_WARNING: int = 0xFEE75C    # Yellow
    COLOR_ERROR: int = 0xED4245      # Red
    COLOR_INFO: int = 0x5DADE2       # Blue

    # ── Cooldowns (seconds) ───────────────────────────────────────────────────
    COOLDOWN_AI: int = 5
    COOLDOWN_IMAGE: int = 15
    COOLDOWN_TTS: int = 3
