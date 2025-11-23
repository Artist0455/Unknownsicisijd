# 🤫 ShriBots Whisper Bot

A Telegram bot for sending anonymous secret messages with clone functionality.

## Features

- 🔒 Send anonymous secret messages
- 👤 Only intended recipient can read
- 🚀 Easy inline mode
- 🤖 Clone bot functionality
- 📊 Admin statistics
- 🧹 Auto-cleanup system

## Deployment on Render

1. Fork this repository
2. Go to [Render](https://render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Use these settings:
   - **Name**: `shribots-whisper-bot`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`

6. Add environment variables:
   - `API_ID`: Your Telegram API ID
   - `API_HASH`: Your Telegram API Hash
   - `BOT_TOKEN`: Your bot token from @BotFather
   - `ADMIN_ID`: Your Telegram user ID

7. Click "Create Web Service"

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_ID` | Telegram API ID | `25136703` |
| `API_HASH` | Telegram API Hash | `accfaf5ecd981c67e...` |
| `BOT_TOKEN` | Bot token from @BotFather | `123456:ABCdef...` |
| `ADMIN_ID` | Your Telegram user ID | `8272213732` |

## Bot Commands

- `/start` - Start the bot
- `/help` - Show help menu
- `/clone` - Clone this bot
- `/mybots` - View your cloned bots
- `/stats` - Admin statistics

## Support

- 📢 Channel: [@ShriBots](https://t.me/shribots)
- 👥 Group: [@ShriBots](https://t.me/shribots)

## License

MIT License
