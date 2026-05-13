"""
TTS Manager — handles gTTS audio generation, queuing, and playback in voice channels.
Prevents overlapping audio and cleans up temp files automatically.
"""

import asyncio
import os
import uuid
from pathlib import Path

import discord
from gtts import gTTS

from config import Config
from utils.logger import setup_logger

logger = setup_logger("tts_manager")


class TTSManager:
    """
    Manages TTS audio generation and queued playback for a single guild.

    Usage:
        manager = TTSManager(voice_client)
        await manager.speak("Hello, world!")
    """

    def __init__(self, voice_client: discord.VoiceClient) -> None:
        self.voice_client = voice_client
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._playing = False
        self._audio_dir = Path(Config.TTS_AUDIO_DIR)
        self._audio_dir.mkdir(exist_ok=True)

    # ── Public API ─────────────────────────────────────────────────────────────

    async def speak(self, text: str) -> None:
        """
        Generate TTS audio for *text* and add it to the playback queue.

        Args:
            text: The text to convert to speech.
        """
        if not text.strip():
            return

        audio_path = await asyncio.to_thread(self._generate_audio, text)
        if audio_path:
            await self._queue.put(audio_path)
            if not self._playing:
                asyncio.create_task(self._process_queue())

    def update_voice_client(self, voice_client: discord.VoiceClient) -> None:
        """Replace the internal voice client (called after reconnects)."""
        self.voice_client = voice_client

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _generate_audio(self, text: str) -> str | None:
        """
        Generate a gTTS MP3 file for *text* and return its path.
        Runs in a thread pool to avoid blocking the event loop.
        """
        try:
            filename = self._audio_dir / f"tts_{uuid.uuid4().hex}.mp3"
            tts = gTTS(text=text, lang=Config.TTS_LANGUAGE, slow=Config.TTS_SLOW)
            tts.save(str(filename))
            logger.debug(f"Generated TTS file: {filename}")
            return str(filename)
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None

    async def _process_queue(self) -> None:
        """Drain the audio queue one file at a time."""
        self._playing = True
        while not self._queue.empty():
            path = await self._queue.get()
            await self._play_file(path)
        self._playing = False

    async def _play_file(self, path: str) -> None:
        """Play a single audio file and wait for it to finish."""
        if not self.voice_client or not self.voice_client.is_connected():
            logger.warning("Voice client not connected — skipping TTS playback.")
            self._cleanup(path)
            return

        try:
            source = discord.FFmpegPCMAudio(path)
            done_event = asyncio.Event()

            def after_playback(error: Exception | None) -> None:
                if error:
                    logger.error(f"Playback error: {error}")
                self._cleanup(path)
                done_event.set()

            self.voice_client.play(source, after=after_playback)
            await done_event.wait()
            # Small gap between phrases
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Error playing TTS file {path}: {e}")
            self._cleanup(path)

    def _cleanup(self, path: str) -> None:
        """Delete a TTS audio file."""
        try:
            os.remove(path)
            logger.debug(f"Deleted TTS file: {path}")
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.warning(f"Could not delete TTS file {path}: {e}")
