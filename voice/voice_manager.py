"""
Voice Manager — handles persistent VC connection, auto-reconnect, and announcements.
One VoiceManager per guild; stored on the bot instance.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Optional

import discord
from discord.ext import tasks

from config import Config
from utils.logger import setup_logger
from voice.tts_manager import TTSManager

logger = setup_logger("voice_manager")

# Path to persist the chosen VC channel ID across restarts
_STATE_FILE = Path("voice_state.json")


def _load_state() -> dict:
    if _STATE_FILE.exists():
        try:
            with open(_STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_state(state: dict) -> None:
    try:
        with open(_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save voice state: {e}")


class VoiceManager:
    """
    Manages a bot's permanent presence in a voice channel for one guild.

    Responsibilities:
    - Persist and restore the chosen VC channel across restarts.
    - Auto-reconnect when the bot is unexpectedly disconnected.
    - Provide TTS announcements for member join/leave events.
    - Expose helpers for the voice commands cog.
    """

    # Registry: guild_id → VoiceManager instance
    _instances: dict[int, "VoiceManager"] = {}

    def __init__(self, bot: discord.Client, guild: discord.Guild) -> None:
        self.bot = bot
        self.guild = guild
        self.voice_client: Optional[discord.VoiceClient] = None
        self.tts_manager: Optional[TTSManager] = None
        self._target_channel_id: Optional[int] = None
        self._reconnect_task: Optional[asyncio.Task] = None

        # Load persisted state
        state = _load_state()
        guild_state = state.get(str(guild.id), {})
        self._target_channel_id = guild_state.get("channel_id")

    # ── Class-level registry ───────────────────────────────────────────────────

    @classmethod
    def get_or_create(cls, bot: discord.Client, guild: discord.Guild) -> "VoiceManager":
        if guild.id not in cls._instances:
            cls._instances[guild.id] = cls(bot, guild)
        return cls._instances[guild.id]

    @classmethod
    def get(cls, guild_id: int) -> Optional["VoiceManager"]:
        return cls._instances.get(guild_id)

    # ── Persistence ────────────────────────────────────────────────────────────

    def _persist(self) -> None:
        state = _load_state()
        state[str(self.guild.id)] = {"channel_id": self._target_channel_id}
        _save_state(state)

    # ── Connection management ──────────────────────────────────────────────────

    async def connect(self, channel: discord.VoiceChannel) -> bool:
        """
        Connect (or move) to *channel* and mark it as the permanent VC.

        Returns:
            True on success, False on failure.
        """
        try:
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.move_to(channel)
            else:
                self.voice_client = await channel.connect(reconnect=True)

            self._target_channel_id = channel.id
            self._persist()

            if self.tts_manager:
                self.tts_manager.update_voice_client(self.voice_client)
            else:
                self.tts_manager = TTSManager(self.voice_client)

            logger.info(f"[Guild {self.guild.id}] Connected to VC: {channel.name}")
            return True
        except Exception as e:
            logger.error(f"[Guild {self.guild.id}] Failed to connect to VC: {e}")
            return False

    async def disconnect(self) -> None:
        """Manually disconnect and clear the stored permanent VC."""
        self._target_channel_id = None
        self._persist()
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect(force=True)
        self.voice_client = None
        self.tts_manager = None
        logger.info(f"[Guild {self.guild.id}] Disconnected from VC.")

    async def rejoin_on_startup(self) -> None:
        """
        Called on bot startup. Re-joins the previously saved permanent VC, if any.
        """
        if not self._target_channel_id:
            return

        channel = self.guild.get_channel(self._target_channel_id)
        if not isinstance(channel, discord.VoiceChannel):
            logger.warning(
                f"[Guild {self.guild.id}] Saved VC channel {self._target_channel_id} not found."
            )
            return

        logger.info(f"[Guild {self.guild.id}] Auto-rejoining VC: {channel.name}")
        await self.connect(channel)

    async def handle_disconnect(self) -> None:
        """
        Called when the bot is unexpectedly kicked from a VC.
        Schedules a reconnect attempt after a short delay.
        """
        if not self._target_channel_id:
            return  # Not a permanent VC — don't reconnect

        if self._reconnect_task and not self._reconnect_task.done():
            return  # Already reconnecting

        self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        """Keep trying to reconnect until successful."""
        while True:
            await asyncio.sleep(Config.VC_RECONNECT_DELAY)
            channel = self.guild.get_channel(self._target_channel_id)
            if not isinstance(channel, discord.VoiceChannel):
                logger.warning(f"[Guild {self.guild.id}] Target VC gone — stopping reconnect.")
                return
            logger.info(f"[Guild {self.guild.id}] Attempting VC reconnect...")
            success = await self.connect(channel)
            if success:
                logger.info(f"[Guild {self.guild.id}] Reconnect successful.")
                return

    # ── TTS helpers ────────────────────────────────────────────────────────────

    async def announce(self, text: str) -> None:
        """Speak *text* via TTS if connected."""
        if self.tts_manager and self.voice_client and self.voice_client.is_connected():
            await self.tts_manager.speak(text)

    # ── Announcement phrases ───────────────────────────────────────────────────

    @staticmethod
    def join_phrase(member: discord.Member) -> str:
        """Return the join announcement phrase for *member*."""
        custom = Config.USER_ANNOUNCEMENTS.get(member.id)
        if custom:
            return custom[0]
        name = member.display_name
        return f"Welcome, {name}!"

    @staticmethod
    def leave_phrase(member: discord.Member) -> str:
        """Return the leave announcement phrase for *member*."""
        custom = Config.USER_ANNOUNCEMENTS.get(member.id)
        if custom:
            return custom[1]
        name = member.display_name
        return f"{name} has left the channel."

    # ── State accessors ────────────────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return bool(self.voice_client and self.voice_client.is_connected())

    @property
    def current_channel(self) -> Optional[discord.VoiceChannel]:
        if self.voice_client and self.voice_client.channel:
            return self.voice_client.channel  # type: ignore[return-value]
        return None

    @property
    def target_channel(self) -> Optional[discord.VoiceChannel]:
        if self._target_channel_id:
            ch = self.guild.get_channel(self._target_channel_id)
            return ch if isinstance(ch, discord.VoiceChannel) else None
        return None
