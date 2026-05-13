# Discord AI Bot

A production-ready Discord bot with AI chat (Groq), AI image generation (Pollinations), permanent voice channel presence, and personalized TTS announcements. Built for Railway deployment.

---

## Features

| Feature | Details |
|---|---|
| **AI Chat** | Groq LLaMA 3 70B, per-user conversation memory, `!ask` + `/ask` |
| **AI Images** | Pollinations AI (free, no key needed), `!image` + `/image` |
| **Permanent VC** | Auto-joins and reconnects 24/7, persists across restarts |
| **TTS Announcements** | gTTS voice announcements on member join/leave, custom per-user phrases |
| **TTS Command** | `!tts` — speak any text in the voice channel |
| **Slash Commands** | Full `/ask`, `/image`, `/tts`, `/help`, `/ping`, `/forget`, `/vcstatus` |
| **Modular Code** | Clean cog-based structure across `commands/`, `events/`, `voice/`, `utils/` |

---

## Project Structure

```
discord-bot/
├── main.py                        # Bot entry point & global error handling
├── config.py                      # All configuration and constants
├── requirements.txt               # Python dependencies
├── Procfile                       # Railway / Heroku process definition
├── runtime.txt                    # Python version pin
├── .env.example                   # Environment variable template
│
├── commands/
│   ├── general_commands.py        # !ping, !help, !info
│   ├── ai_commands.py             # !ask, /ask, !forget
│   ├── image_commands.py          # !image, /image
│   └── voice_commands.py          # !setvc, !joinvc, !leavevc, !tts
│
├── events/
│   ├── on_ready.py                # Startup: slash sync, status, VC rejoin
│   ├── on_voice_state_update.py   # VC join/leave announcements + reconnect
│   └── on_member_events.py        # Guild join/leave welcome messages
│
├── voice/
│   ├── tts_manager.py             # gTTS generation, audio queuing, playback
│   └── voice_manager.py           # Permanent VC state, reconnect, announcements
│
└── utils/
    ├── logger.py                  # Rotating file + console logger
    ├── helpers.py                 # Embed builder, text chunker, formatters
    └── memory.py                  # Per-user conversation memory store
```

---

## Quick Start (Local)

### Prerequisites

- Python 3.11+
- `ffmpeg` installed and available in `PATH` (required for voice/audio)
- A Discord bot token
- A Groq API key

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your values
```

### 3. Run the bot

```bash
python main.py
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | ✅ | Your bot token from the Discord Developer Portal |
| `GROQ_API_KEY` | ✅ | Your API key from [console.groq.com](https://console.groq.com) |

---

## Discord Bot Setup

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Create a new application → **Bot** tab → **Reset Token** → copy the token
3. Enable **Privileged Gateway Intents**: `SERVER MEMBERS INTENT`, `MESSAGE CONTENT INTENT`
4. **OAuth2 → URL Generator** — select scopes: `bot`, `applications.commands`
5. Bot permissions: `Send Messages`, `Embed Links`, `Connect`, `Speak`, `Use Voice Activity`, `Read Message History`
6. Invite the bot to your server using the generated URL

---

## Railway Deployment

### 1. Install the Railway CLI (optional)

```bash
npm install -g @railway/cli
railway login
```

### 2. Create a new project

```bash
railway new
railway link
```

### 3. Add environment variables in Railway dashboard

Go to your project → **Variables** and add:

```
DISCORD_TOKEN=your_discord_bot_token
GROQ_API_KEY=your_groq_api_key
```

### 4. Deploy

Railway will automatically detect `Procfile` and use:

```
worker: python main.py
```

Push your code to the linked GitHub repo (or use `railway up`) and Railway will deploy it.

> **Important:** The bot runs as a `worker` (not a web server). Make sure Railway is set to run the `worker` process, not `web`.

### 5. Add ffmpeg on Railway

Railway's nixpacks builder includes ffmpeg automatically. If you ever see audio errors, add this to a `nixpacks.toml` in your project root:

```toml
[phases.setup]
nixPkgs = ["ffmpeg"]
```

---

## Commands Reference

### Prefix commands (default prefix: `!`)

| Command | Description |
|---|---|
| `!ask <question>` | Ask the AI a question (remembers conversation) |
| `!forget` | Clear your AI conversation memory |
| `!image <prompt>` | Generate an AI image |
| `!setvc [#channel]` | Set and join a permanent voice channel |
| `!joinvc` | Join your current voice channel |
| `!leavevc` | Disconnect from the voice channel |
| `!tts <text>` | Speak text in the voice channel |
| `!ping` | Check bot latency |
| `!info` | Show bot information |
| `!help` | Display help menu |

### Slash commands

`/ask`, `/image`, `/tts`, `/forget`, `/vcstatus`, `/ping`, `/help`

---

## Personalized Voice Announcements

Edit `config.py` to add custom join/leave phrases per user:

```python
USER_ANNOUNCEMENTS: dict[int, tuple[str, str]] = {
    # Discord User ID: (join phrase, leave phrase)
    123456789012345678: ("Welcome back, Alex!", "Alex left the battlefield!"),
    987654321098765432: ("The legend arrives!", "See you later, Jordan!"),
}
```

Find a user's ID by enabling Developer Mode in Discord (Settings → Advanced → Developer Mode), then right-clicking their name and selecting **Copy User ID**.

---

## Permanent Voice Channel

1. Join a voice channel in your server
2. Run `!setvc` — the bot joins and saves the channel to `voice_state.json`
3. The bot will **automatically rejoin** this channel every time it restarts
4. If forcibly disconnected, it will **auto-reconnect** after 5 seconds
5. To clear the permanent VC, run `!leavevc`

---

## Tech Stack

| Component | Library |
|---|---|
| Discord | discord.py 2.x |
| AI Chat | Groq (LLaMA 3 70B) |
| Image Generation | Pollinations AI (free, no API key) |
| Text-to-Speech | gTTS + FFmpeg |
| Voice | discord.py voice + PyNaCl |
| Config | python-dotenv |
| Logging | Python standard logging (rotating files) |
