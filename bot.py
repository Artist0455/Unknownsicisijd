import os
import sys
import logging
import re
import asyncio
import json
from datetime import datetime
from flask import Flask
import threading

# Configure logging for Docker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Environment variables
API_ID = int(os.getenv('API_ID', '25136703'))
API_HASH = os.getenv('API_HASH', 'accfaf5ecd981c67e481328515c39f89'))
BOT_TOKEN = os.getenv('BOT_TOKEN', '8366493122:AAG7nl7a3BqXd8-oyTAHovAjc7UUuLeHb-4'))
ADMIN_ID = int(os.getenv('ADMIN_ID', '8027090675'))
PORT = int(os.environ.get('PORT', 10000))

# Import Telethon after environment setup
from telethon import TelegramClient, events, Button

# Support channels
SUPPORT_CHANNEL = "shribots"
SUPPORT_GROUP = "shribots"

# Initialize bot
bot = TelegramClient('whisper_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Storage
messages_db = {}
recent_users = {}

# Data files
DATA_DIR = "/app/data"
RECENT_USERS_FILE = os.path.join(DATA_DIR, "recent_users.json")

def ensure_data_dir():
    """Ensure data directory exists"""
    os.makedirs(DATA_DIR, exist_ok=True)

def load_data():
    global recent_users
    ensure_data_dir()
    try:
        if os.path.exists(RECENT_USERS_FILE):
            with open(RECENT_USERS_FILE, 'r') as f:
                recent_users = json.load(f)
        logger.info("✅ Data loaded successfully")
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}")

def save_data():
    ensure_data_dir()
    try:
        with open(RECENT_USERS_FILE, 'w') as f:
            json.dump(recent_users, f, indent=2)
        logger.info("💾 Data saved successfully")
    except Exception as e:
        logger.error(f"❌ Error saving data: {e}")

# Load data on startup
load_data()

WELCOME_TEXT = """
╔══════════════════════╗
║     🎭 𝗦𝗛𝗥𝗜𝗕𝗢𝗧𝗦     ║ powered by
║    𝗪𝗛𝗜𝗦𝗣𝗘𝗥 𝗕𝗢𝗧    ║     Artist 
╚══════════════════════╝

🤫 Welcome to Secret Whisper Bot!

🔒 Send anonymous secret messages
🚀 Only intended recipient can read
🎯 Easy to use inline mode

Create whispers that only specific users can unlock!
"""

ANIMATION_URL = "https://files.catbox.moe/395dct.mp4"

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

async def send_welcome_with_animation(event):
    """Send animation and welcome message"""
    try:
        await bot.send_file(
            event.chat_id,
            ANIMATION_URL,
            caption="🚀 **Starting your whisper experience...**"
        )
        await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"Animation error: {e}")
    
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

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    try:
        logger.info(f"🚀 Start command from user: {event.sender_id}")
        await send_welcome_with_animation(event)
    except Exception as e:
        logger.error(f"Start error: {e}")

@bot.on(events.NewMessage(pattern='/stats'))
async def stats_handler(event):
    if event.sender_id != ADMIN_ID:
        await event.reply("❌ Admin only command!")
        return
        
    stats_text = f"""
📊 **Admin Statistics**

👥 Recent Users: {len(recent_users)}
💬 Total Messages: {len(messages_db)}

**Bot Status:** ✅ Running
**Environment:** 🐳 Docker
    """
    
    await event.reply(stats_text)

@bot.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    bot_username = (await bot.get_me()).username
    help_text = f"""
📖 **How to Use Whisper Bot**

**1. Inline Mode:**
   • Type `@{bot_username}` in any chat
   • Write your message
   • Add @username OR user ID at end
   • Send!

**2. Examples:**
   • `@{bot_username} Hello! @username`
   • `@{bot_username} I miss you 123456789`

**3. Commands:**
   • /start - Start bot
   • /help - Show help
   • /stats - Admin statistics

🔒 **Only the mentioned user can read your message!**
    """
    
    await event.reply(
        help_text,
        buttons=[
            [Button.switch_inline("🚀 Try Now", query="")],
            [Button.inline("🔙 Back", data="back_start")]
        ]
    )

async def handle_inline_query(event):
    """Handle inline queries with proper error handling"""
    try:
        recent_buttons = get_recent_users_buttons(event.sender_id)
        
        if not event.text:
            if recent_buttons:
                result_text = "**Recent Users:**\nClick any user below to message them quickly!\n\nOr type manually: `message @username`"
                result = event.builder.article(
                    title="🤫 Whisper Bot - Quick Send",
                    description="Send to recent users or type manually",
                    text=result_text,
                    buttons=recent_buttons
                )
            else:
                result = event.builder.article(
                    title="🤫 Whisper Bot",
                    description="Send secret messages",
                    text="**Usage:** `your_message @username`\n\n**Example:** `Hello! @username`\n\n🔒 Only they can read!"
                )
            await event.answer([result])
            return
        
        text = event.text.strip()
        
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
            result = event.builder.article(
                title="❌ Invalid Format",
                description="Use: message @username OR message 123456789",
                text="**Usage:** `your_message @username`\n\n**Examples:**\n• `Hello! @username`\n• `I miss you 123456789`"
            )
            await event.answer([result])
            return
        
        try:
            if target_user.isdigit():
                user_obj = await bot.get_entity(int(target_user))
            else:
                if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{3,30}$', target_user):
                    result = event.builder.article(
                        title="❌ Invalid Username",
                        description="Username format is invalid",
                        text="**Valid username:**\n• Starts with letter\n• 4-31 characters\n• Letters, numbers, underscores"
                    )
                    await event.answer([result])
                    return
                user_obj = await bot.get_entity(target_user)
            
            if not hasattr(user_obj, 'first_name'):
                result = event.builder.article(
                    title="❌ Not a User",
                    description="You can only send to users",
                    text="This appears to be a channel or group. Please mention a user instead."
                )
                await event.answer([result])
                return
            
            add_to_recent_users(
                event.sender_id, 
                user_obj.id, 
                getattr(user_obj, 'username', None),
                getattr(user_obj, 'first_name', 'User')
            )
            
        except Exception as e:
            logger.error(f"Error getting user entity: {e}")
            result = event.builder.article(
                title="❌ User Not Found",
                description="User not found or invalid",
                text="❌ User not found! Please check the username or user ID and try again."
            )
            await event.answer([result])
            return
        
        message_id = f'msg_{event.sender_id}_{user_obj.id}_{int(datetime.now().timestamp())}'
        messages_db[message_id] = {
            'user_id': user_obj.id,
            'msg': message_text,
            'sender_id': event.sender_id,
            'timestamp': datetime.now().isoformat()
        }
        
        result = event.builder.article(
            title="🔒 Secret Message",
            description=f"For {user_obj.first_name}",
            text=f"**🔐 A secret message for {user_obj.first_name}!**\n\n*Note: Only {user_obj.first_name} can open this message.*",
            buttons=[[Button.inline("🔓 Show Message", message_id)]]
        )
        
        await event.answer([result])
        
    except Exception as e:
        logger.error(f"Inline error: {e}")
        result = event.builder.article(
            title="❌ Error",
            description="Something went wrong",
            text="❌ An error occurred. Please try again."
        )
        await event.answer([result])

@bot.on(events.InlineQuery())
async def inline_handler(event):
    await handle_inline_query(event)

@bot.on(events.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8')
    
    if data == "help":
        await event.edit(
            "📖 **Help Guide**\n\nUse inline mode: `message @username`",
            buttons=[[Button.inline("🔙 Back", data="back_start")]]
        )
    
    elif data == "admin_stats":
        if event.sender_id != ADMIN_ID:
            await event.answer("Admin only!", alert=True)
            return
            
        stats_text = f"📊 **Admin Statistics**\n\n"
        stats_text += f"👥 Recent Users: {len(recent_users)}\n"
        stats_text += f"💬 Total Messages: {len(messages_db)}\n"
        stats_text += f"🆔 Admin ID: {ADMIN_ID}\n"
        stats_text += f"🌐 Port: {PORT}\n"
        stats_text += f"🚀 Status: ✅ Running"
        
        await event.edit(stats_text)
    
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
                f"Now type your message and I'll send it to {target_text}",
                buttons=[[Button.switch_inline(
                    f"💌 Message {target_text}", 
                    query=f"@{username}" if username else first_name
                )]]
            )
    
    elif data == "back_start":
        user_id = event.sender_id
        
        if user_id == ADMIN_ID:
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
        if event.sender_id in [msg_data['user_id'], msg_data['sender_id']]:
            await event.answer(msg_data['msg'], alert=True)
        else:
            await event.answer("Not for you!", alert=True)

# Flask App for Render web server
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 ShriBots Whisper Bot is Running! 🚀"

@app.route('/health')
def health():
    return "✅ Bot Health: OK"

@app.route('/status')
def status():
    return {
        "status": "running",
        "recent_users": len(recent_users),
        "total_messages": len(messages_db),
        "environment": "docker"
    }

def run_flask():
    """Run Flask web server for Render"""
    logger.info(f"🌐 Starting Flask server on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# Start Flask in background thread
logger.info("🚀 Initializing Flask web server...")
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

async def main():
    """Main function to start the bot"""
    me = await bot.get_me()
    logger.info(f"🎭 ShriBots Whisper Bot Started!")
    logger.info(f"🤖 Bot: @{me.username}")
    logger.info(f"🆔 Bot ID: {me.id}")
    logger.info(f"👑 Admin: {ADMIN_ID}")
    logger.info(f"👥 Recent Users: {len(recent_users)}")
    logger.info(f"🌐 Web server running on port {PORT}")
    logger.info("🐳 Running in Docker container")
    logger.info("✅ Bot is ready and working!")
    logger.info("🔗 Use /start to begin")

if __name__ == '__main__':
    print("🐳 Starting ShriBots Whisper Bot in Docker...")
    print(f"📝 Environment: API_ID={API_ID}, PORT={PORT}")
    print("🚀 Initializing...")
    
    try:
        # Start the bot
        bot.start()
        bot.loop.run_until_complete(main())
        
        print("✅ Bot started successfully in Docker!")
        print("🔄 Bot is now running...")
        
        # Keep the bot running
        bot.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)