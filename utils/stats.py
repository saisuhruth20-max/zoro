"""
Bot statistics tracker — thread-safe, shared between the async bot and the Flask dashboard.
"""

import threading
from collections import Counter, deque
from datetime import datetime, timezone
from typing import Any, Optional


class BotStats:
    """
    Thread-safe in-memory statistics store.

    The bot writes to this from the asyncio event loop (writes are GIL-safe for
    simple types). Flask reads from it in a separate thread.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.start_time: datetime = datetime.now(timezone.utc)

        # Command usage counters
        self.command_counts: Counter[str] = Counter()
        self.total_commands: int = 0

        # Recent activity log (last 50 entries)
        self.recent_commands: deque[dict[str, Any]] = deque(maxlen=50)

        # Bot reference — set after bot creation in main.py
        self.bot: Optional[Any] = None

    # ── Writers (called from bot event loop) ──────────────────────────────────

    def record_command(self, command_name: str, user: str, guild: str) -> None:
        """Record a command execution."""
        with self._lock:
            self.command_counts[command_name] += 1
            self.total_commands += 1
            self.recent_commands.appendleft(
                {
                    "command": command_name,
                    "user": user,
                    "guild": guild,
                    "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                }
            )

    # ── Readers (called from Flask thread) ────────────────────────────────────

    def get_uptime(self) -> str:
        """Return a human-readable uptime string."""
        delta = datetime.now(timezone.utc) - self.start_time
        hours, rem = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(rem, 60)
        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        return f"{minutes}m {seconds}s"

    def get_snapshot(self) -> dict[str, Any]:
        """Return a JSON-serialisable snapshot of all stats."""
        with self._lock:
            bot = self.bot
            guild_count = len(bot.guilds) if bot else 0
            member_count = sum(g.member_count or 0 for g in bot.guilds) if bot else 0
            latency = round(bot.latency * 1000) if bot else 0

            # Voice channels the bot is in
            voice_channels = []
            if bot:
                for vc in bot.voice_clients:
                    voice_channels.append(
                        {
                            "guild": vc.guild.name if vc.guild else "Unknown",
                            "channel": vc.channel.name if vc.channel else "Unknown",
                        }
                    )

            return {
                "online": bot is not None and not bot.is_closed(),
                "latency_ms": latency,
                "uptime": self.get_uptime(),
                "guild_count": guild_count,
                "member_count": member_count,
                "total_commands": self.total_commands,
                "top_commands": self.command_counts.most_common(10),
                "recent_commands": list(self.recent_commands)[:20],
                "voice_channels": voice_channels,
            }


# Module-level singleton
stats = BotStats()
