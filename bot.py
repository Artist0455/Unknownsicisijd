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
BOT_TOKEN = os.getenv('BOT_TOKEN', '8314503581:AAEm5TvIs_-qn23VfOCnfVL1dTRwwDtpi8A')
ADMIN_ID = int(os.getenv('ADMIN_ID', '8272213732'))
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
SUPPORT_GROUP = "idxhelp"

# Initialize bot
try:
    bot = TelegramClient('whisper_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    logger.info("✅ Bot client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize bot: {e}")
    raise

# Storage - Fast in-memory storage
messages_db = {}
recent_users = {}
user_cooldown = {}
user_bots = {}
clone_stats = {}
user_recent_targets = {}  # New: Store recent targets per user

# Data files
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
RECENT_USERS_FILE = os.path.join(DATA_DIR, "recent_users.json")
USER_RECENT_TARGETS_FILE = os.path.join(DATA_DIR, "user_recent_targets.json")
CLONE_STATS_FILE = os.path.join(DATA_DIR, "clone_stats.json")

def load_data():
    global recent_users, clone_stats, user_recent_targets
    try:
        if os.path.exists(RECENT_USERS_FILE):
            with open(RECENT_USERS_FILE, 'r', encoding='utf-8') as f:
                recent_users = json.load(f)
            logger.info(f"✅ Loaded {len(recent_users)} recent users")
        
        if os.path.exists(USER_RECENT_TARGETS_FILE):
            with open(USER_RECENT_TARGETS_FILE, 'r', encoding='utf-8') as f:
                user_recent_targets = json.load(f)
            logger.info(f"✅ Loaded {sum(len(v) for v in user_recent_targets.values())} user recent targets")
        
        if os.path.exists(CLONE_STATS_FILE):
            with open(CLONE_STATS_FILE, 'r', encoding='utf-8') as f:
                clone_stats = json.load(f)
            logger.info(f"✅ Loaded {len(clone_stats)} clone stats")
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}")
        recent_users = {}
        clone_stats = {}
        user_recent_targets = {}

def save_data():
    try:
        with open(RECENT_USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(recent_users, f, indent=2, ensure_ascii=False)
        
        with open(USER_RECENT_TARGETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_recent_targets, f, indent=2, ensure_ascii=False)
        
        with open(CLONE_STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(clone_stats, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"❌ Error saving data: {e}")

# Load data on startup
load_data()

WELCOME_TEXT = """
╔══════════════════════╗
║     🎭 𝗦𝗛𝗥𝗜𝗕𝗢𝗧𝗦     ║ 𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐛𝐲
║    𝗪𝗛𝗜𝗦𝗣𝗘𝗥 𝗕𝗢𝗧    ║      𝐀𝐫𝐭𝐢𝐬𝐭
╚══════════════════════╝

🤫 Welcome to Secret Whisper Bot!

🔒 Send anonymous secret messages
🚀 Only intended recipient can read
🎯 Easy to use inline mode
🤖 Clone own bot to use @Shribots

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
   • /clone - Clone your own bot
   • /remove - Remove your cloned bot
   • /allbots - View all cloned bots (Admin)

🔒 **Only the mentioned user can read your message!**
"""

def add_to_recent_users(user_id, target_user_id, target_username=None, target_first_name=None):
    """Add user to recent users list - FAST VERSION"""
    try:
        user_key = str(target_user_id)
        recent_users[user_key] = {
            'user_id': target_user_id,
            'username': target_username,
            'first_name': target_first_name,
            'last_used': datetime.now().isoformat()
        }
        
        # Keep only last 20 users (increased from 10)
        if len(recent_users) > 20:
            oldest_key = min(recent_users.keys(), key=lambda k: recent_users[k]['last_used'])
            del recent_users[oldest_key]
        
        # Also add to user's personal recent targets
        user_id_str = str(user_id)
        if user_id_str not in user_recent_targets:
            user_recent_targets[user_id_str] = []
        
        # Remove if already exists
        user_recent_targets[user_id_str] = [t for t in user_recent_targets[user_id_str] 
                                          if t.get('user_id') != target_user_id]
        
        # Add to beginning
        user_recent_targets[user_id_str].insert(0, {
            'user_id': target_user_id,
            'username': target_username,
            'first_name': target_first_name,
            'last_used': datetime.now().isoformat()
        })
        
        # Keep only last 10 per user
        if len(user_recent_targets[user_id_str]) > 10:
            user_recent_targets[user_id_str] = user_recent_targets[user_id_str][:10]
        
        # Save in background without blocking
        asyncio.create_task(save_data_async())
        
    except Exception as e:
        logger.error(f"Error adding to recent users: {e}")

async def save_data_async():
    """Save data asynchronously without blocking"""
    try:
        # Save to files
        with open(RECENT_USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(recent_users, f, indent=2, ensure_ascii=False)
        
        with open(USER_RECENT_TARGETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_recent_targets, f, indent=2, ensure_ascii=False)
        
        with open(CLONE_STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(clone_stats, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Async save error: {e}")

def get_recent_users_buttons(user_id):
    """Get recent users buttons for inline suggestions - OPTIMIZED"""
    try:
        user_id_str = str(user_id)
        
        # First check user's personal recent targets
        if user_id_str in user_recent_targets and user_recent_targets[user_id_str]:
            recent_list = user_recent_targets[user_id_str]
        elif recent_users:
            # Fallback to global recent users
            sorted_users = sorted(recent_users.items(), 
                                key=lambda x: x[1].get('last_used', ''), 
                                reverse=True)
            recent_list = [user[1] for user in sorted_users[:5]]
        else:
            return []
        
        buttons = []
        for user_data in recent_list[:5]:  # Show max 5
            username = user_data.get('username')
            first_name = user_data.get('first_name', 'User')
            
            if username:
                display_text = f"@{username}"
                query_text = f"@{username}"
            else:
                display_text = f"{first_name}"
                query_text = f"{user_data.get('user_id')}"
            
            if len(display_text) > 15:
                display_text = display_text[:15] + "..."
            
            buttons.append([Button.switch_inline(
                f"🔒 {display_text}", 
                query=query_text,
                same_peer=True
            )])
        
        return buttons
    except Exception as e:
        logger.error(f"Error getting recent users: {e}")
        return []

def is_cooldown(user_id):
    """Check if user is in cooldown - OPTIMIZED"""
    now = datetime.now().timestamp()
    if user_id in user_cooldown:
        if now - user_cooldown[user_id] < 2:  # Reduced to 2 seconds
            return True
    user_cooldown[user_id] = now
    return False

# Improved user detection patterns
USER_PATTERNS = [
    r'@(\w+)$',  # Username at end
    r'(\d+)$',   # User ID at end  
    r'@(\w+)\s+', # Username anywhere
    r'(\d+)\s+',  # User ID anywhere
]

async def extract_target_user(text, client):
    """Improved user extraction with multiple patterns"""
    text = text.strip()
    
    for pattern in USER_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            for match in matches:
                try:
                    if match.isdigit():
                        user_obj = await client.get_entity(int(match))
                    else:
                        # Validate username format
                        if re.match(r'^[a-zA-Z][a-zA-Z0-9_]{3,30}$', match):
                            user_obj = await client.get_entity(match)
                        else:
                            continue
                    
                    if hasattr(user_obj, 'first_name'):
                        # Remove the matched pattern from message
                        message_text = re.sub(pattern.replace(r'(\w+)', match).replace(r'(\d+)', match), '', text).strip()
                        return user_obj, message_text
                        
                except Exception as e:
                    logger.debug(f"User extraction failed for {match}: {e}")
                    continue
    
    return None, text

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
                    [Button.switch_inline("🚀 Try Now", query="", same_peer=True)],
                    [Button.inline("📊 Statistics", data="admin_stats"), Button.inline("📖 Help", data="help")],
                    [Button.inline("🔧 Clone Bot", data="clone_info"), Button.inline("🤖 All Bots", data="all_bots")]
                ]
            )
        else:
            await event.reply(
                WELCOME_TEXT,
                buttons=[
                    [Button.url("📢 Support Channel", f"https://t.me/{SUPPORT_CHANNEL}")],
                    [Button.url("👥 Support Group", f"https://t.me/{SUPPORT_GROUP}")],
                    [Button.switch_inline("🚀 Try Now", query="", same_peer=True)],
                    [Button.inline("📖 Help", data="help"), Button.inline("🔧 Clone Bot", data="clone_info")]
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
                [Button.switch_inline("🚀 Try Now", query="", same_peer=True)],
                [Button.inline("🔙 Back", data="back_start")]
            ]
        )
    except Exception as e:
        logger.error(f"Help error: {e}")
        await event.reply("❌ An error occurred. Please try again.")

@bot.on(events.InlineQuery)
async def inline_handler(event):
    await handle_inline_query(event)

async def handle_inline_query(event, client=None):
    """Handle inline queries - OPTIMIZED VERSION"""
    if client is None:
        client = bot
    
    try:
        if is_cooldown(event.sender_id):
            await event.answer([])
            return

        # Get recent buttons quickly
        recent_buttons = get_recent_users_buttons(event.sender_id)
        
        if not event.text or not event.text.strip():
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
                    description="Usage: message @username",
                    text="**Usage:** `message @username`\n\n**Example:** `Hello! @username`\n\n🔒 Only they can read!",
                    buttons=[[Button.switch_inline("🚀 Try Now", query="", same_peer=True)]]
                )
            await event.answer([result])
            return
        
        text = event.text.strip()
        
        # Use improved user extraction
        target_user, message_text = await extract_target_user(text, client)
        
        if not target_user or not message_text:
            result = event.builder.article(
                title="❌ Invalid Format",
                description="Use: message @username OR message 123456789",
                text="**Usage:** `message @username`\n\n**Examples:**\n• `Hello! @username`\n• `I miss you 123456789`",
                buttons=[[Button.switch_inline("🔄 Try Again", query=text, same_peer=True)]]
            )
            await event.answer([result])
            return
        
        if len(message_text) > 1000:
            result = event.builder.article(
                title="❌ Message Too Long",
                description="Maximum 1000 characters allowed",
                text="❌ Your message is too long! Please keep it under 1000 characters."
            )
            await event.answer([result])
            return
        
        # Add to recent users (fast async)
        add_to_recent_users(
            event.sender_id, 
            target_user.id, 
            getattr(target_user, 'username', None),
            getattr(target_user, 'first_name', 'User')
        )
        
        # Create message
        message_id = f'msg_{event.sender_id}_{target_user.id}_{int(datetime.now().timestamp())}'
        messages_db[message_id] = {
            'user_id': target_user.id,
            'msg': message_text,
            'sender_id': event.sender_id,
            'timestamp': datetime.now().isoformat(),
            'target_name': getattr(target_user, 'first_name', 'User')
        }
        
        target_name = getattr(target_user, 'first_name', 'User')
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

# ... (rest of the code remains similar but with same_peer=True added to switch_inline buttons)

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
                    [Button.switch_inline("🚀 Try Now", query="", same_peer=True)],
                    [Button.inline("🔙 Back", data="back_start")]
                ]
            )
        
        elif data.startswith("recent_"):
            user_key = data.replace("recent_", "")
            if user_key in recent_users:
                user_data = recent_users[user_key]
                username = user_data.get('username')
                first_name = user_data.get('first_name', 'User')
                
                if username:
                    target_text = f"@{username}"
                    query_text = f"@{username}"
                else:
                    target_text = f"{first_name}"
                    query_text = f"{user_data.get('user_id')}"
                
                await event.edit(
                    f"🔒 **Send whisper to {target_text}**\n\n"
                    f"Now switch to inline mode and type your message for {target_text}",
                    buttons=[[Button.switch_inline(
                        f"💌 Message {target_text}", 
                        query=query_text,
                        same_peer=True
                    )]]
                )
            else:
                await event.answer("User not found in recent list!", alert=True)
        
        # ... (rest of callback handlers remain similar)

# Flask web server and other code remains the same...