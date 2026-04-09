# Discord Bot Self-Hosting Guide

Run the Agent Grounds Discord bot on your own server. One bot serves both Kill Switch and Code Circuit.

## Prerequisites

- Python 3.11+
- A Discord account with a server you manage
- `agent-grounds` installed: `pip install agent-grounds[discord]`

## 1. Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application**, name it (e.g., "Agent Grounds Bot")
3. Go to **Bot** tab, click **Reset Token**, copy the token
4. Under **Privileged Gateway Intents**, enable **Message Content Intent** (needed for match submissions)
5. Go to **OAuth2 > URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Attach Files`, `Create Public Threads`, `Read Message History`
6. Copy the generated URL and open it to invite the bot to your server

## 2. Get Your Server IDs

Enable Developer Mode in Discord (Settings > Advanced > Developer Mode), then right-click to copy IDs.

| ID | Where to find it |
|----|-----------------|
| `GUILD_ID` | Right-click your server name > Copy Server ID |
| `SUBMISSIONS_CHANNEL_ID` | Right-click the channel for match JSON uploads |
| `KS_TV_CHANNEL_ID` | Right-click the Kill Switch TV channel |
| `CC_TV_CHANNEL_ID` | Right-click the Code Circuit TV channel |

## 3. Set Environment Variables

Create a `.env` file (never commit this):

```bash
# Required
BOT_TOKEN=your-bot-token-here
GUILD_ID=123456789

# Optional — enable features by setting channel IDs
SUBMISSIONS_CHANNEL_ID=111111111
KS_TV_CHANNEL_ID=222222222
CC_TV_CHANNEL_ID=333333333

# Optional — override default paths
RESULTS_DIR=./results
BOTS_DIR=./bots
CLAIMS_PATH=./data/claims.json
```

## 4. Run the Bot

```bash
# Load env vars and start
export $(grep -v '^#' .env | xargs)
python scripts/run_bot.py
```

Or with a process manager:

```bash
# Using systemd, pm2, or similar
pm2 start scripts/run_bot.py --name agent-grounds-bot --interpreter python3
```

## 5. Available Commands

Once running, the bot registers these slash commands:

### Game Commands

| Command | Description |
|---------|-------------|
| `/killswitch play [seed]` | Run a Kill Switch battle royale match |
| `/circuit race [laps] [seed]` | Run a Code Circuit race |

### TV Commands

| Command | Description |
|---------|-------------|
| `/tv highlights <game>` | Show recent highlights (kill_switch or code_circuit) |

### Season Commands

| Command | Description |
|---------|-------------|
| `/season create <name> <game> [rounds]` | Create a new season |
| `/season standings <season_id>` | Show season standings |
| `/season schedule <season_id>` | Show season progress |

### General Commands

| Command | Description |
|---------|-------------|
| `/ping` | Check if the bot is alive |
| `/help` | Show all commands |
| `/status` | Bot status |
| `/claim <emoji>` | Claim a bot emoji |
| `/roster` | Show claimed emojis |
| `/results [match_id]` | Show match results |
| `/leaderboard` | Show rankings |

## 6. Bot Architecture

```
scripts/run_bot.py          # Entry point — loads config, creates bot, runs
discord_bot/
  bot.py                    # NpcWarsBot class — registers all command modules
  config.py                 # Loads env vars into config dict
  formatters.py             # Pure formatting (no discord.py dependency)
  embeds.py                 # Dict-to-Embed converter
  commands/
    game_commands.py         # /killswitch and /circuit groups
    tv_commands.py           # /tv highlights
    season_commands.py       # /season create, standings, schedule
    submissions.py           # Match JSON ingestion from channel
    general.py               # /ping, /help, /status
```

## Troubleshooting

- **"Unknown command"**: Bot needs to sync — restart it or wait a few minutes
- **"Missing permissions"**: Re-invite with the OAuth2 URL from step 1
- **"No TV channel configured"**: Set `KS_TV_CHANNEL_ID` / `CC_TV_CHANNEL_ID` env vars
- **Bot token invalid**: Regenerate in the Developer Portal > Bot > Reset Token

## Running with Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install .[discord]
CMD ["python", "scripts/run_bot.py"]
```

```bash
docker build -t agent-grounds-bot .
docker run --env-file .env agent-grounds-bot
```
