import os
import logging
import re
import asyncio
import json
from datetime import datetime
from flask import Flask
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
API_ID = int(os.getenv('API_ID', '25136703'))
API_HASH = os.getenv('API_HASH', 'accfaf5ecd981c67e481328515c39f89')
BOT_TOKEN = os.getenv('BOT_TOKEN', '8366493122:AAG7nl7a3BqXd8-oyTAHovAjc7UUuLeHb-4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '8027090675'))
PORT = int(os.environ.get('PORT', 10000))

# Import Telethon
try:
    from telethon import TelegramClient, events, Button
    from telethon.errors import SessionPasswordNeededError
except ImportError as e:
    logger.error(f"Telethon import error: {e}")
    raise

# Support channels
SUPPORT_CHANNEL = "shribots"
SUPPORT_GROUP = "shribots"

# Initialize bot
try:
    bot = TelegramClient('whisper_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    logger.info("✅ Bot client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize bot: {e}")
    raise

# Storage
messages_db = {}
recent_users = {}
user_cooldown = {}

# Data files
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
RECENT_USERS_FILE = os.path.join(DATA_DIR, "recent_users.json")

def load_data():
    global recent_users
    try:
        if os.path.exists(RECENT_USERS_FILE):
            with open(RECENT_USERS_FILE, 'r', encoding='utf-8') as f:
                recent_users = json.load(f)
            logger.info(f"✅ Loaded {len(recent_users)} recent users")
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}")
        recent_users = {}

def save_data():
    try:
        with open(RECENT_USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(recent_users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"❌ Error saving data: {e}")

# Load data on startup
load_data()

WELCOME_TEXT = """
╔══════════════════════╗
║     🎭 𝗦𝗛𝗥𝗜𝗕𝗢𝗧𝗦     ║
║    𝗪𝗛𝗜𝗦𝗣𝗘𝗥 𝗕𝗢𝗧    ║
╚══════════════════════╝

🤫 Welcome to Secret Whisper Bot!

🔒 Send anonymous secret messages
🚀 Only intended recipient can read
🎯 Easy to use inline mode

Create whispers that only specific users can unlock!
"""

HELP_TEXT = """
📖 **How to Use Whisper Bot**

**1. Inline Mode:**
   • Type `@{}` in any chat
   • Write your message  
   • Add @username OR user ID at end
   • Send!

**2. Examples:**
   • `@{} Hello! @username`
   • `@{} I miss you 123456789`

**3. Commands:**
   • /start - Start bot
   • /help - Show help
   • /stats - Admin statistics

🔒 **Only the mentioned user can read your message!**
"""

def add_to_recent_users(user_id, target_user_id, target_username=None, target_first_name=None):
    """Add user to recent users list"""
    try:
        user_key = str(target_user_id)
        recent_users[user_key] = {
            'user_id': target_user_id,
            'username': target_username,
            'first_name': target_first_name,
            'last_used': datetime.now().isoformat()
        }
        
        # Keep only last 10 users
        if len(recent_users) > 10:
            oldest_key = min(recent_users.keys(), key=lambda k: recent_users[k]['last_used'])
            del recent_users[oldest_key]
        
        save_data()
    except Exception as e:
        logger.error(f"Error adding to recent users: {e}")

def get_recent_users_buttons(user_id):
    """Get recent users buttons for inline suggestions"""
    try:
        if not recent_users:
            return []
        
        sorted_users = sorted(recent_users.items(), 
                            key=lambda x: x[1].get('last_used', ''), 
                            reverse=True)
        
        buttons = []
        for user_key, user_data in sorted_users[:5]:
            username = user_data.get('username')
            first_name = user_data.get('first_name', 'User')
            
            if username:
                display_text = f"@{username}"
            else:
                display_text = f"{first_name}"
            
            if len(display_text) > 15:
                display_text = display_text[:15] + "..."
            
            buttons.append([Button.inline(
                f"🔒 {display_text}", 
                data=f"recent_{user_key}"
            )])
        
        return buttons
    except Exception as e:
        logger.error(f"Error getting recent users: {e}")
        return []

def is_cooldown(user_id):
    """Check if user is in cooldown"""
    now = datetime.now().timestamp()
    if user_id in user_cooldown:
        if now - user_cooldown[user_id] < 5:  # 5 seconds cooldown
            return True
    user_cooldown[user_id] = now
    return False

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    try:
        logger.info(f"🚀 Start command from user: {event.sender_id}")
        
        # Welcome message with buttons
        if event.sender_id == ADMIN_ID:
            await event.reply(
                WELCOME_TEXT,
                buttons=[
                    [Button.url("📢 Support Channel", f"https://t.me/{SUPPORT_CHANNEL}")],
                    [Button.url("👥 Support Group", f"https://t.me/{SUPPORT_GROUP}")],
                    [Button.switch_inline("🚀 Try Now", query="")],
                    [Button.inline("📊 Statistics", data="admin_stats")],
                    [Button.inline("📖 Help", data="help")]
                ]
            )
        else:
            await event.reply(
                WELCOME_TEXT,
                buttons=[
                    [Button.url("📢 Support Channel", f"https://t.me/{SUPPORT_CHANNEL}")],
                    [Button.url("👥 Support Group", f"https://t.me/{SUPPORT_GROUP}")],
                    [Button.switch_inline("🚀 Try Now", query="")],
                    [Button.inline("📖 Help", data="help")]
                ]
            )
    except Exception as e:
        logger.error(f"Start error: {e}")
        await event.reply("❌ An error occurred. Please try again.")

@bot.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    try:
        bot_username = (await bot.get_me()).username
        help_text = HELP_TEXT.format(bot_username, bot_username, bot_username)
        
        await event.reply(
            help_text,
            buttons=[
                [Button.switch_inline("🚀 Try Now", query="")],
                [Button.inline("🔙 Back", data="back_start")]
            ]
        )
    except Exception as e:
        logger.error(f"Help error: {e}")
        await event.reply("❌ An error occurred. Please try again.")

@bot.on(events.NewMessage(pattern='/stats'))
async def stats_handler(event):
    if event.sender_id != ADMIN_ID:
        await event.reply("❌ Admin only command!")
        return
        
    try:
        stats_text = f"""
📊 **Admin Statistics**

👥 Recent Users: {len(recent_users)}
💬 Total Messages: {len(messages_db)}
🆔 Admin ID: {ADMIN_ID}
🌐 Port: {PORT}

**Bot Status:** ✅ Running
**Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
        """
        
        await event.reply(stats_text)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await event.reply("❌ Error fetching statistics.")

@bot.on(events.InlineQuery)
async def inline_handler(event):
    try:
        # Cooldown check
        if is_cooldown(event.sender_id):
            await event.answer([])
            return

        recent_buttons = get_recent_users_buttons(event.sender_id)
        
        if not event.text or not event.text.strip():
            # Show recent users or instructions
            if recent_buttons:
                result_text = "**Recent Users:**\nClick any user below to message them quickly!\n\nOr type: `message @username`"
                result = event.builder.article(
                    title="🤫 Whisper Bot - Quick Send",
                    description="Send to recent users or type manually",
                    text=result_text,
                    buttons=recent_buttons
                )
            else:
                result = event.builder.article(
                    title="🤫 Whisper Bot - Send Secret Messages",
                    description="Usage: your_message @username",
                    text="**Usage:** `your_message @username`\n\n**Example:** `Hello! @username`\n\n🔒 Only they can read!",
                    buttons=[[Button.switch_inline("🚀 Try Now", query="")]]
                )
            await event.answer([result])
            return
        
        text = event.text.strip()
        
        # Parse message and target user
        patterns = [r'@(\w+)$', r'(\d+)$']
        target_user = None
        message_text = text
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if pattern == r'@(\w+)$':
                    target_user = match.group(1)
                    message_text = text.replace(f"@{target_user}", "").strip()
                else:
                    target_user = match.group(1)
                    message_text = text.replace(target_user, "").strip()
                break
        
        if not target_user or not message_text:
            # Invalid format
            result = event.builder.article(
                title="❌ Invalid Format",
                description="Use: message @username OR message 123456789",
                text="**Usage:** `your_message @username`\n\n**Examples:**\n• `Hello! @username`\n• `I miss you 123456789`\n\nMake sure to include @username or user ID at the end!",
                buttons=[[Button.switch_inline("🔄 Try Again", query=text)]]
            )
            await event.answer([result])
            return
        
        # Validate message length
        if len(message_text) > 1000:
            result = event.builder.article(
                title="❌ Message Too Long",
                description="Maximum 1000 characters allowed",
                text="❌ Your message is too long! Please keep it under 1000 characters."
            )
            await event.answer([result])
            return
        
        try:
            # Get user entity
            if target_user.isdigit():
                user_obj = await bot.get_entity(int(target_user))
            else:
                # Validate username format
                if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{3,30}$', target_user):
                    result = event.builder.article(
                        title="❌ Invalid Username",
                        description="Username format is invalid",
                        text="**Valid username format:**\n• Starts with letter\n• 4-31 characters\n• Letters, numbers, underscores only"
                    )
                    await event.answer([result])
                    return
                
                user_obj = await bot.get_entity(target_user)
            
            # Validate it's a user
            if not hasattr(user_obj, 'first_name'):
                result = event.builder.article(
                    title="❌ Not a User",
                    description="You can only send to users",
                    text="This appears to be a channel or group. Please mention a user instead."
                )
                await event.answer([result])
                return
            
            # Add to recent users
            add_to_recent_users(
                event.sender_id, 
                user_obj.id, 
                getattr(user_obj, 'username', None),
                getattr(user_obj, 'first_name', 'User')
            )
            
        except ValueError as e:
            logger.error(f"ValueError getting user entity: {e}")
            result = event.builder.article(
                title="❌ Invalid User ID",
                description="User ID must be numeric",
                text="❌ Invalid user ID! Please check the ID and try again."
            )
            await event.answer([result])
            return
        except Exception as e:
            logger.error(f"Error getting user entity: {e}")
            result = event.builder.article(
                title="❌ User Not Found",
                description="User not found or invalid",
                text="❌ User not found! Please check:\n• Username spelling\n• User ID accuracy\n• User exists and isn't banned"
            )
            await event.answer([result])
            return
        
        # Create message ID and store message
        message_id = f'msg_{event.sender_id}_{user_obj.id}_{int(datetime.now().timestamp())}'
        messages_db[message_id] = {
            'user_id': user_obj.id,
            'msg': message_text,
            'sender_id': event.sender_id,
            'timestamp': datetime.now().isoformat(),
            'target_name': getattr(user_obj, 'first_name', 'User')
        }
        
        # Create result
        target_name = getattr(user_obj, 'first_name', 'User')
        result = event.builder.article(
            title=f"🔒 Secret Message for {target_name}",
            description=f"Click to send secret message",
            text=f"**🔐 A secret message for {target_name}!**\n\n*Note: Only {target_name} can open this message.*",
            buttons=[[Button.inline("🔓 Show Message", message_id)]]
        )
        
        await event.answer([result])
        
    except Exception as e:
        logger.error(f"Inline query error: {e}")
        result = event.builder.article(
            title="❌ Error",
            description="Something went wrong",
            text="❌ An error occurred. Please try again in a moment."
        )
        await event.answer([result])

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    try:
        data = event.data.decode('utf-8')
        
        if data == "help":
            bot_username = (await bot.get_me()).username
            help_text = HELP_TEXT.format(bot_username, bot_username, bot_username)
            
            await event.edit(
                help_text,
                buttons=[
                    [Button.switch_inline("🚀 Try Now", query="")],
                    [Button.inline("🔙 Back", data="back_start")]
                ]
            )
        
        elif data == "admin_stats":
            if event.sender_id != ADMIN_ID:
                await event.answer("❌ Admin only!", alert=True)
                return
                
            stats_text = f"📊 **Admin Statistics**\n\n"
            stats_text += f"👥 Recent Users: {len(recent_users)}\n"
            stats_text += f"💬 Total Messages: {len(messages_db)}\n"
            stats_text += f"🆔 Admin ID: {ADMIN_ID}\n"
            stats_text += f"🌐 Port: {PORT}\n"
            stats_text += f"🕒 Last Updated: {datetime.now().strftime('%H:%M:%S')}\n\n"
            stats_text += f"**Status:** ✅ Running"
            
            await event.edit(
                stats_text,
                buttons=[[Button.inline("🔙 Back", data="back_start")]]
            )
        
        elif data.startswith("recent_"):
            user_key = data.replace("recent_", "")
            if user_key in recent_users:
                user_data = recent_users[user_key]
                username = user_data.get('username')
                first_name = user_data.get('first_name', 'User')
                
                if username:
                    target_text = f"@{username}"
                else:
                    target_text = f"{first_name}"
                
                await event.edit(
                    f"🔒 **Send whisper to {target_text}**\n\n"
                    f"Now switch to inline mode and type your message for {target_text}",
                    buttons=[[Button.switch_inline(
                        f"💌 Message {target_text}", 
                        query=f"@{username}" if username else first_name
                    )]]
                )
            else:
                await event.answer("User not found in recent list!", alert=True)
        
        elif data == "back_start":
            if event.sender_id == ADMIN_ID:
                await event.edit(
                    WELCOME_TEXT,
                    buttons=[
                        [Button.url("📢 Support Channel", f"https://t.me/{SUPPORT_CHANNEL}")],
                        [Button.url("👥 Support Group", f"https://t.me/{SUPPORT_GROUP}")],
                        [Button.switch_inline("🚀 Try Now", query="")],
                        [Button.inline("📊 Statistics", data="admin_stats")],
                        [Button.inline("📖 Help", data="help")]
                    ]
                )
            else:
                await event.edit(
                    WELCOME_TEXT,
                    buttons=[
                        [Button.url("📢 Support Channel", f"https://t.me/{SUPPORT_CHANNEL}")],
                        [Button.url("👥 Support Group", f"https://t.me/{SUPPORT_GROUP}")],
                        [Button.switch_inline("🚀 Try Now", query="")],
                        [Button.inline("📖 Help", data="help")]
                    ]
                )
        
        elif data in messages_db:
            msg_data = messages_db[data]
            if event.sender_id == msg_data['user_id']:
                # Target user opening the message
                sender_info = ""
                try:
                    sender = await bot.get_entity(msg_data['sender_id'])
                    sender_name = getattr(sender, 'first_name', 'Someone')
                    sender_info = f"\n\n💌 From: {sender_name}"
                except:
                    sender_info = f"\n\n💌 From: Anonymous"
                
                await event.answer(
                    f"🔓 {msg_data['msg']}{sender_info}",
                    alert=True
                )
            elif event.sender_id == msg_data['sender_id']:
                # Sender viewing their own message
                await event.answer(
                    f"📝 Your message: {msg_data['msg']}\n\n👤 To: {msg_data.get('target_name', 'User')}",
                    alert=True
                )
            else:
                await event.answer("🔒 This message is not for you!", alert=True)
        
        else:
            await event.answer("❌ Invalid button!", alert=True)
            
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await event.answer("❌ An error occurred. Please try again.", alert=True)

# Flask web server for health checks
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ShriBots Whisper Bot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .status { background: #4CAF50; color: white; padding: 10px; border-radius: 5px; text-align: center; margin: 20px 0; }
            .info { background: #2196F3; color: white; padding: 15px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 ShriBots Whisper Bot</h1>
            <div class="status">✅ Bot is Running Successfully</div>
            <div class="info">
                <strong>📊 Statistics:</strong><br>
                Recent Users: {}<br>
                Total Messages: {}<br>
                Server Time: {}
            </div>
            <p>This bot allows you to send anonymous secret messages to Telegram users.</p>
            <p><strong>Usage:</strong> Use inline mode in any chat: <code>@{} your_message @username</code></p>
        </div>
    </body>
    </html>
    """.format(
        len(recent_users), 
        len(messages_db),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        (bot.get_me()).wait().username if bot.is_connected() else "bot_username"
    )

@app.route('/health')
def health():
    return json.dumps({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "recent_users": len(recent_users),
        "total_messages": len(messages_db),
        "bot_connected": bot.is_connected()
    })

@app.route('/status')
def status():
    return json.dumps({
        "status": "running",
        "service": "telegram-whisper-bot",
        "version": "1.0.0",
        "environment": "production"
    })

def run_flask():
    """Run Flask web server"""
    logger.info(f"🌐 Starting Flask server on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# Start Flask in background thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

async def main():
    """Main function to start the bot"""
    try:
        me = await bot.get_me()
        logger.info(f"🎭 ShriBots Whisper Bot Started!")
        logger.info(f"🤖 Bot: @{me.username}")
        logger.info(f"🆔 Bot ID: {me.id}")
        logger.info(f"👑 Admin: {ADMIN_ID}")
        logger.info(f"👥 Recent Users: {len(recent_users)}")
        logger.info(f"🌐 Web server running on port {PORT}")
        logger.info("✅ Bot is ready and working!")
        logger.info("🔗 Use /start to begin")
    except Exception as e:
        logger.error(f"❌ Error in main: {e}")
        raise

if __name__ == '__main__':
    print("🚀 Starting ShriBots Whisper Bot...")
    print(f"📝 Environment: API_ID={API_ID}, PORT={PORT}")
    
    try:
        # Start the bot
        bot.start()
        bot.loop.run_until_complete(main())
        
        print("✅ Bot started successfully!")
        print("🔄 Bot is now running...")
        
        # Keep the bot running
        bot.run_until_disconnected()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        print(f"❌ Error: {e}")
    finally:
        print("💾 Saving data before exit...")
        save_data()