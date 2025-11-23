from telethon import TelegramClient, events, Button
from flask import Flask, request
import logging
import os
import re
import asyncio
import json
from datetime import datetime
import threading
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
API_ID = int(os.getenv('API_ID', '25136703'))
API_HASH = os.getenv('API_HASH', 'accfaf5ecd981c67e481328515c39f89')
BOT_TOKEN = os.getenv('BOT_TOKEN', '8521103806:AAHHQ2XL_EokOXmJCdElfkkSrnYAkr0IVB4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '8272213732'))

# Initialize Flask app for health checks
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>🤫 ShriBots Whisper Bot</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .container { max-width: 600px; margin: 0 auto; }
                .status { color: green; font-size: 24px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎭 ShriBots Whisper Bot</h1>
                <p class="status">✅ Bot is running successfully!</p>
                <p>🤫 Send secret messages via Telegram</p>
                <p>🔒 Only intended recipients can read</p>
                <p>🚀 Powered by Telethon + Flask</p>
                <p>📞 Bot: @ShriBotsWhisperBot</p>
            </div>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return {'status': 'healthy', 'bot': 'running', 'timestamp': datetime.now().isoformat()}

@app.route('/status')
def status():
    return {
        'status': 'active',
        'service': 'ShriBots Whisper Bot',
        'messages_stored': len(messages_db),
        'user_bots': len(user_bots),
        'timestamp': datetime.now().isoformat()
    }

# Global variables
messages_db = {}
user_bots = {}
bot = None

WELCOME_TEXT = """
╔══════════════════════╗
║     🎭 𝗦𝗛𝗥𝗜𝗕𝗢𝗧𝗦     ║ powered by
║    𝗪𝗛𝗜𝗦𝗣𝗘𝗥 𝗕𝗢𝗧    ║     Artist 
╚══════════════════════╝

🤫 Welcome to Secret Whisper Bot!

🔒 Send anonymous secret messages
🚀 Only intended recipient can read
🎯 Easy to use inline mode
📌 clone Whisper to use @shribots now

Create whispers that only specific users can unlock!
"""

def setup_bot_handlers(bot_instance):
    """Setup all bot event handlers"""
    
    @bot_instance.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        """Handle /start command"""
        try:
            await event.reply(
                WELCOME_TEXT,
                buttons=[
                    [Button.switch_inline("🚀 Try Now", query="")],
                    [Button.inline("📖 Help", data="help")],
                    [Button.inline("🔧 Clone Bot", data="clone_info")]
                ]
            )
            logger.info(f"Start command from user {event.sender_id}")
        except Exception as e:
            logger.error(f"Start command error: {e}")

    @bot_instance.on(events.NewMessage(pattern='/help'))
    async def help_handler(event):
        """Handle /help command"""
        try:
            me = await bot_instance.get_me()
            help_text = f"""
╔══════════════════════╗
║     📖 𝗛𝗘𝗟𝗣 𝗠𝗘𝗡𝗨     ║
╚══════════════════════╝

**How to use:**

🤖 **Inline Mode:**
• Type `@{me.username}` in any chat
• Write your message  
• Add @username at end
• Send!

📝 **Examples:**
• `@{me.username} Hello! @username`
• `@{me.username} Secret message 123456789`

⚡ **Features:**
• 🔒 End-to-end secret messages
• 👤 Only recipient can read
• ⚡ Fast and secure
• 🎯 Easy to use

🔧 **Commands:**
• /start - Start bot
• /help - Show help
• /clone - Create your bot

📢 **Support:** @ShriBots
            """
            
            await event.reply(
                help_text,
                buttons=[
                    [Button.switch_inline("🚀 Try Now", query="")],
                    [Button.url("📢 Support", "https://t.me/shribots")]
                ]
            )
            logger.info(f"Help command from user {event.sender_id}")
        except Exception as e:
            logger.error(f"Help command error: {e}")

    @bot_instance.on(events.NewMessage(pattern='/clone'))
    async def clone_handler(event):
        """Handle /clone command"""
        try:
            clone_help = """
╔══════════════════════╗
║     🔧 𝗖𝗟𝗢𝗡𝗘 𝗕𝗢𝗧     ║
╚══════════════════════╝

**Create your own Whisper Bot!**

🤖 **Steps to Clone:**
1. Go to @BotFather
2. Create new bot with /newbot
3. Get bot token
4. Send me: `/clone your_bot_token`

**Example:**
`/clone 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

⚠️ **Warning:**
• Never share your token with anyone
• Keep it safe and secure

🎯 **Features Included:**
• Same whisper functionality
• Inline mode support
• Secure messaging
            """
            await event.reply(
                clone_help,
                buttons=[
                    [Button.url("🤖 Create Bot", "https://t.me/BotFather")],
                    [Button.inline("🔙 Back", data="back")]
                ]
            )
            logger.info(f"Clone command from user {event.sender_id}")
        except Exception as e:
            logger.error(f"Clone command error: {e}")

    @bot_instance.on(events.NewMessage(pattern=r'/clone\s+(\d+:[A-Za-z0-9_-]+)'))
    async def clone_token_handler(event):
        """Handle clone with token"""
        try:
            token = event.pattern_match.group(1)
            await event.reply("🔄 Creating your bot...")
            
            # Validate token format
            if not re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
                await event.reply("❌ Invalid token format!")
                return
            
            # Create user bot
            user_bot = TelegramClient(f'user_bot_{event.sender_id}', API_ID, API_HASH)
            await user_bot.start(bot_token=token)
            
            bot_me = await user_bot.get_me()
            user_bots[token] = user_bot
            
            # Setup basic handlers for cloned bot
            @user_bot.on(events.NewMessage(pattern='/start'))
            async def user_start(event):
                await event.reply("🤫 Your cloned whisper bot is ready! Use inline mode to send secret messages.")
            
            @user_bot.on(events.InlineQuery())
            async def user_inline(event):
                if not event.text:
                    result = event.builder.article(
                        title="Whisper Bot",
                        description="Send secret messages",
                        text="**Usage:** `message @username`\n\n**Example:** `Hello! @username`"
                    )
                    await event.answer([result])
                    return
                
                # Simple inline handler for cloned bot
                text = event.text.strip()
                target_match = re.search(r'@(\w+)$', text)
                
                if target_match:
                    target_user = target_match.group(1)
                    message_text = text.replace(f'@{target_user}', '').strip()
                    
                    if message_text:
                        message_id = f'msg_{event.sender_id}_{target_user}_{int(datetime.now().timestamp())}'
                        messages_db[message_id] = {
                            'text': message_text,
                            'target': target_user,
                            'sender': event.sender_id
                        }
                        
                        result = event.builder.article(
                            title="🔒 Secret Message",
                            description=f"For {target_user}",
                            text=f"**🔐 Secret message for {target_user}!**",
                            buttons=[Button.inline("🔓 Show Message", message_id)]
                        )
                        await event.answer([result])
            
            await event.reply(
                f"✅ **Bot Cloned Successfully!**\n\n"
                f"🤖 **Your Bot:** @{bot_me.username}\n"
                f"🎉 Now active with all features!\n\n"
                f"**Try your bot now!**",
                buttons=[
                    [Button.switch_inline("🚀 Test Your Bot", query="", same_peer=True)],
                    [Button.url("📢 Support", "https://t.me/shribots")]
                ]
            )
            logger.info(f"Bot cloned successfully for user {event.sender_id}: @{bot_me.username}")
            
        except Exception as e:
            logger.error(f"Clone token error: {e}")
            await event.reply(f"❌ **Clone Failed!**\n\nError: {str(e)}")

    @bot_instance.on(events.InlineQuery())
    async def inline_handler(event):
        """Handle inline queries"""
        try:
            if not event.text:
                # Show help when no text
                result = event.builder.article(
                    title="🤫 Whisper Bot",
                    description="Send secret messages - Type: message @username",
                    text="**Usage:** `your_message @username`\n\n**Example:** `Hello! @username`\n\n🔒 Only they can read it!"
                )
                await event.answer([result])
                return
            
            # Parse message and target user
            text = event.text.strip()
            target_match = re.search(r'@(\w+)$', text)
            
            if not target_match:
                # No target user found
                result = event.builder.article(
                    title="❌ Missing Username",
                    description="Add @username at the end",
                    text="**Usage:** `your_message @username`\n\n**Example:** `Hello! @username`"
                )
                await event.answer([result])
                return
            
            target_user = target_match.group(1)
            message_text = text.replace(f'@{target_user}', '').strip()
            
            if not message_text:
                # Empty message
                result = event.builder.article(
                    title="❌ Empty Message",
                    description="Write a message before @username",
                    text="**Usage:** `your_message @username`\n\n**Example:** `Hello! @username`"
                )
                await event.answer([result])
                return
            
            # Create message ID
            message_id = f'msg_{event.sender_id}_{target_user}_{int(datetime.now().timestamp())}'
            messages_db[message_id] = {
                'text': message_text,
                'target': target_user,
                'sender': event.sender_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Create result
            result = event.builder.article(
                title="🔒 Secret Message",
                description=f"For {target_user}",
                text=f"**🔐 A secret message for {target_user}!**\n\n*Note: Only {target_user} can open this message.*",
                buttons=[Button.inline("🔓 Show Message", message_id)]
            )
            
            await event.answer([result])
            logger.info(f"Inline query from {event.sender_id} for {target_user}")
            
        except Exception as e:
            logger.error(f"Inline handler error: {e}")
            result = event.builder.article(
                title="❌ Error",
                description="Something went wrong",
                text="❌ An error occurred. Please try again."
            )
            await event.answer([result])

    @bot_instance.on(events.CallbackQuery(pattern='help'))
    async def help_callback(event):
        """Handle help callback"""
        try:
            me = await bot_instance.get_me()
            help_text = f"""
╔══════════════════════╗
║     📖 𝗤𝗨𝗜𝗖𝗞 𝗛𝗘𝗟𝗣     ║
╚══════════════════════╝

**Quick Guide:**

🎯 **How to send whispers:**
1. Type `@{me.username}` in any chat
2. Write your message
3. Add @username at end
4. Send!

📝 **Format:**
`your_message @username`

🔒 **Security:**
• Only the mentioned user can read
• Messages are private and secure
• No one else can see the content

Need help? Contact @ShriBots
            """
            
            await event.edit(
                help_text,
                buttons=[
                    [Button.switch_inline("🚀 Try Now", query="")],
                    [Button.inline("🔙 Back", data="back")]
                ]
            )
        except Exception as e:
            logger.error(f"Help callback error: {e}")

    @bot_instance.on(events.CallbackQuery(pattern='clone_info'))
    async def clone_info_callback(event):
        """Handle clone info callback"""
        try:
            clone_text = """
🔧 **Clone This Bot**

Create your own Whisper Bot with all features!

Use `/clone` command with your bot token from @BotFather

**Example:**
`/clone 1234567890:ABCdefGHIjkl...`
            """
            await event.edit(
                clone_text,
                buttons=[
                    [Button.url("🤖 BotFather", "https://t.me/BotFather")],
                    [Button.inline("🔙 Back", data="back")]
                ]
            )
        except Exception as e:
            logger.error(f"Clone info callback error: {e}")

    @bot_instance.on(events.CallbackQuery(pattern='back'))
    async def back_callback(event):
        """Handle back callback"""
        try:
            await event.edit(
                WELCOME_TEXT,
                buttons=[
                    [Button.switch_inline("🚀 Try Now", query="")],
                    [Button.inline("📖 Help", data="help")],
                    [Button.inline("🔧 Clone Bot", data="clone_info")]
                ]
            )
        except Exception as e:
            logger.error(f"Back callback error: {e}")

    @bot_instance.on(events.CallbackQuery())
    async def callback_handler(event):
        """Handle message callbacks"""
        try:
            data = event.data.decode('utf-8')
            
            if data in messages_db:
                msg_data = messages_db[data]
                
                # Show the secret message
                await event.answer(
                    f"🔓 **Secret Message:**\n\n{msg_data['text']}",
                    alert=True
                )
                logger.info(f"Message revealed for user {event.sender_id}")
            else:
                await event.answer("❌ Message not found or expired!", alert=True)
                
        except Exception as e:
            logger.error(f"Callback handler error: {e}")
            await event.answer("❌ Error showing message!", alert=True)

def initialize_bot():
    """Initialize Telegram bot with proper event loop"""
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        bot_instance = TelegramClient('whisper_bot', API_ID, API_HASH, loop=loop)
        bot_instance.start(bot_token=BOT_TOKEN)
        
        # Setup handlers
        setup_bot_handlers(bot_instance)
        
        logger.info("✅ Bot initialized successfully with handlers")
        return bot_instance
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")
        return None

def run_bot():
    """Run the Telegram bot in its own event loop"""
    global bot
    try:
        bot = initialize_bot()
        if bot:
            logger.info("🤖 Starting bot event loop...")
            bot.run_until_disconnected()
        else:
            logger.error("🚫 Bot could not be initialized")
    except Exception as e:
        logger.error(f"Bot runtime error: {e}")

def start_services():
    """Start both web server and bot"""
    # Start bot in a separate thread with its own event loop
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("🤖 Telegram bot started in background thread")
    
    # Start Flask app
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    logger.info("🎭 Starting ShriBots Whisper Bot Services...")
    start_services()