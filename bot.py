from telethon import events, TelegramClient, Button
import logging
import os
import re
import asyncio
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables with error handling
try:
    API_ID = int(os.getenv('API_ID', '25136703'))
    API_HASH = os.getenv('API_HASH', 'accfaf5ecd981c67e481328515c39f89')
    BOT_TOKEN = os.getenv('BOT_TOKEN', '8521103806:AAHHQ2XL_EokOXmJCdElfkkSrnYAkr0IVB4')
    ADMIN_ID = int(os.getenv('ADMIN_ID', '8272213732'))
except (ValueError, TypeError) as e:
    logger.error(f"Error loading environment variables: {e}")
    exit(1)

# Initialize bot
try:
    bot = TelegramClient(
        "WhisperBot",
        api_id=API_ID,
        api_hash=API_HASH
    ).start(bot_token=BOT_TOKEN)
    logger.info("Bot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}")
    exit(1)

# Data storage
db = {}
user_bots = {}
clone_stats = {}
recent_users = {}

# Data files
CLONE_FILE = "clone_stats.json"
RECENT_USERS_FILE = "recent_users.json"

def load_clone_stats():
    global clone_stats
    try:
        if os.path.exists(CLONE_FILE):
            with open(CLONE_FILE, 'r') as f:
                clone_stats = json.load(f)
            logger.info(f"Loaded {len(clone_stats)} clone stats")
    except Exception as e:
        logger.error(f"Error loading clone stats: {e}")
        clone_stats = {}

def save_clone_stats():
    try:
        with open(CLONE_FILE, 'w') as f:
            json.dump(clone_stats, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving clone stats: {e}")

def load_recent_users():
    global recent_users
    try:
        if os.path.exists(RECENT_USERS_FILE):
            with open(RECENT_USERS_FILE, 'r') as f:
                recent_users = json.load(f)
            logger.info(f"Loaded {len(recent_users)} recent users")
    except Exception as e:
        logger.error(f"Error loading recent users: {e}")
        recent_users = {}

def save_recent_users():
    try:
        with open(RECENT_USERS_FILE, 'w') as f:
            json.dump(recent_users, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving recent users: {e}")

# Load data on startup
load_clone_stats()
load_recent_users()

WELCOME_TEXT = """
╔══════════════════════╗
║     🎭 𝗦𝗛𝗥𝗜𝗕𝗢𝗧𝗦     ║
║    𝗪𝗛𝗜𝗦𝗣𝗘𝗥 𝗕𝗢𝗧    ║
╚══════════════════════╝

🤫 **Welcome to Secret Whisper Bot!**

🔒 **Send anonymous secret messages**
🚀 **Only intended recipient can read**
🎯 **Easy to use inline mode**

**Create whispers that only specific users can unlock!**
"""

HELP_TEXT = """
╔══════════════════════╗
║     📖 𝗛𝗘𝗟𝗣 𝗠𝗘𝗡𝗨     ║
╚══════════════════════╝

🤖 **How to Use:**

**1. Inline Mode:**
   • Type `@{}` in any chat
   • Write your message
   • Add @username or user ID at end
   • Send!

**2. Examples:**
   • `@{} Hello secret! @username`
   • `@{} I miss you 123456789`

**3. Features:**
   • 🔒 End-to-end secret messages
   • 👤 Only recipient can read
   • ⚡ Fast and secure
   • 🎨 Easy to use

**4. Commands:**
   • /start - Start the bot
   • /help - This help menu
   • /clone - Clone this bot
   • /mybots - Your cloned bots

📢 **Support:** @ShriBots
"""

async def animated_welcome(event):
    """Welcome animation"""
    try:
        frames = [
            "🚀 **Starting Whisper Bot...**",
            "🎭 **Loading ShriBots...**",
            "🔒 **Initializing Security...**",
            "🤫 **Whisper Engine Ready!**"
        ]
        
        message = await event.reply("⚡ **Initializing...**")
        
        for frame in frames:
            await asyncio.sleep(0.8)
            await message.edit(frame)
        
        await asyncio.sleep(0.5)
        return message
    except Exception as e:
        logger.error(f"Error in animated welcome: {e}")
        return await event.reply(WELCOME_TEXT)

def cleanup_old_messages():
    """Clean up old messages"""
    try:
        current_time = datetime.now()
        keys_to_remove = []
        
        for key, value in db.items():
            if 'timestamp' in value:
                message_time = datetime.fromisoformat(value['timestamp'])
                if current_time - message_time > timedelta(hours=1):
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del db[key]
        
        if keys_to_remove:
            logger.info(f"Cleaned {len(keys_to_remove)} old messages")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

def create_unique_message_id(sender_id, target_id):
    """Create unique message ID"""
    timestamp = int(datetime.now().timestamp())
    return f"msg_{sender_id}_{target_id}_{timestamp}"

def add_to_recent_users(sender_id, target_user_obj):
    """Add user to recent users list"""
    try:
        user_key = str(target_user_obj.id)
        recent_users[user_key] = {
            'user_id': target_user_obj.id,
            'username': getattr(target_user_obj, 'username', None),
            'first_name': getattr(target_user_obj, 'first_name', 'User'),
            'last_used': datetime.now().isoformat()
        }
        save_recent_users()
    except Exception as e:
        logger.error(f"Error adding to recent users: {e}")

@bot.on(events.NewMessage(pattern="^[!?/]start$"))
async def start_command(event):
    """Handle /start command"""
    try:
        if event.sender.id == ADMIN_ID:
            await event.reply(
                "👑 **Admin Panel**\n\n"
                "📊 View clone statistics\n"
                "🔧 Manage cloned bots\n"
                "🚀 Bot controls",
                buttons=[
                    [Button.inline("📊 Clone Stats", data="admin_stats")],
                    [Button.inline("🔧 Manage Bots", data="admin_bots")],
                    [Button.switch_inline("🚀 Try Inline", query="")]
                ]
            )
            return
        
        welcome_msg = await animated_welcome(event)
        
        await welcome_msg.edit(
            WELCOME_TEXT,
            buttons=[
                [Button.url("📢 Support", "https://t.me/shribots")],
                [Button.switch_inline("🚀 Try Inline", query="")],
                [Button.inline("📖 Help", data="help"), 
                 Button.inline("🔧 Clone", data="clone_info")],
                [Button.inline("🤖 My Bots", data="my_bots")]
            ]
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await event.reply("❌ An error occurred. Please try again.")

@bot.on(events.NewMessage(pattern="^[!?/]help$"))
async def help_command(event):
    """Handle /help command"""
    try:
        me = await bot.get_me()
        await event.reply(
            HELP_TEXT.format(me.username, me.username, me.username),
            buttons=[
                [Button.url("📢 Support", "https://t.me/shribots")],
                [Button.switch_inline("🚀 Try Inline", query="")],
                [Button.inline("🔧 Clone Bot", data="clone_info")]
            ]
        )
    except Exception as e:
        logger.error(f"Error in help command: {e}")

@bot.on(events.NewMessage(pattern="^[!?/]clone(?:\s+(\S+))?$"))
async def clone_command(event):
    """Handle /clone command"""
    try:
        input_token = event.pattern_match.group(1)
        
        if not input_token:
            clone_text = """
🔧 **Clone Bot**

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
            """
            await event.reply(
                clone_text,
                buttons=[
                    [Button.url("🤖 Create Bot", "https://t.me/BotFather")],
                    [Button.inline("🔙 Back", data="back_to_start")]
                ]
            )
            return
        
        # Validate token format
        if not re.match(r'^\d+:[A-Za-z0-9_-]+$', input_token):
            await event.reply(
                "❌ **Invalid Token Format!**\n\n"
                "Please check your bot token.\n"
                "Format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`",
                buttons=[[Button.inline("🔄 Try Again", data="clone_info")]]
            )
            return
        
        # Check if already cloned
        if input_token in clone_stats:
            await event.reply(
                "❌ **This bot is already cloned!**\n\n"
                "You can manage it with /mybots command.",
                buttons=[[Button.inline("🤖 My Bots", data="my_bots")]]
            )
            return
        
        creating_msg = await event.reply("🔄 **Creating your bot...**")
        
        # Create user bot instance
        user_bot = TelegramClient(
            f"user_bot_{event.sender.id}",
            api_id=API_ID,
            api_hash=API_HASH
        )
        
        await user_bot.start(bot_token=input_token)
        user_bot_me = await user_bot.get_me()
        
        # Store bot data
        user_bots[input_token] = user_bot
        clone_stats[input_token] = {
            'owner_id': event.sender.id,
            'username': user_bot_me.username,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'token_preview': input_token[:10] + '...'
        }
        save_clone_stats()
        
        # Setup basic handlers for cloned bot
        @user_bot.on(events.NewMessage(pattern="^[!?/]start$"))
        async def user_start_command(event):
            await event.reply(
                WELCOME_TEXT,
                buttons=[
                    [Button.url("📢 Support", "https://t.me/shribots")],
                    [Button.switch_inline("🚀 Try Inline", query="")]
                ]
            )
        
        @user_bot.on(events.NewMessage(pattern="^[!?/]help$"))
        async def user_help_command(event):
            me = await user_bot.get_me()
            await event.reply(
                HELP_TEXT.format(me.username, me.username, me.username),
                buttons=[
                    [Button.url("📢 Support", "https://t.me/shribots")],
                    [Button.switch_inline("🚀 Try Inline", query="")]
                ]
            )
        
        @user_bot.on(events.InlineQuery())
        async def user_inline_handler(event):
            if len(event.text) == 0:
                me = (await user_bot.get_me()).username
                result = event.builder.article(
                    title="Whisper Bot",
                    description="Send secret messages",
                    text=f"**Usage:** `@{me} message @username`",
                    buttons=[[Button.switch_inline("Try", query="")]]
                )
                await event.answer([result])
                return
            
            query_text = event.text.strip()
            patterns = [r'@(\w+)$', r'(\d+)$']
            target_user = None
            message_text = query_text
            
            for pattern in patterns:
                match = re.search(pattern, query_text)
                if match:
                    if pattern == r'@(\w+)$':
                        target_user = match.group(1)
                        message_text = query_text.replace(f"@{target_user}", "").strip()
                    else:
                        target_user = match.group(1)
                        message_text = query_text.replace(target_user, "").strip()
                    break
            
            if not target_user or not message_text:
                await event.answer([], switch_pm="Format: Message @username")
                return
            
            try:
                if target_user.isdigit():
                    user_obj = await user_bot.get_entity(int(target_user))
                else:
                    user_obj = await user_bot.get_entity(target_user)
            except:
                await event.answer([], switch_pm="User not found!")
                return
            
            message_id = create_unique_message_id(event.sender.id, user_obj.id)
            db[message_id] = {
                "user_id": user_obj.id,
                "msg": message_text,
                "sender_id": event.sender.id,
                "timestamp": datetime.now().isoformat()
            }
            
            result = event.builder.article(
                title="Secret Message",
                description=f"For {user_obj.first_name}",
                text=f"**🔐 A secret message for {user_obj.first_name}!**\n\n*Only they can open it.*",
                buttons=[[Button.inline("🔓 Show Message", data=message_id)]]
            )
            await event.answer([result])
        
        @user_bot.on(events.CallbackQuery())
        async def user_callback_handler(event):
            data = event.data.decode('utf-8')
            if data in db:
                msg_data = db[data]
                if event.sender.id in [msg_data['user_id'], msg_data['sender_id']]:
                    await event.answer(msg_data['msg'], alert=True)
                else:
                    await event.answer("Not for you!", alert=True)
        
        # Notify admin
        if ADMIN_ID:
            try:
                await bot.send_message(
                    ADMIN_ID,
                    f"🆕 **New Bot Cloned!**\n\n"
                    f"🤖 Bot: @{user_bot_me.username}\n"
                    f"👤 Owner: {event.sender.id}\n"
                    f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
            except Exception as e:
                logger.error(f"Error notifying admin: {e}")
        
        await creating_msg.edit(
            f"✅ **Bot Cloned Successfully!**\n\n"
            f"🤖 **Your Bot:** @{user_bot_me.username}\n"
            f"🎉 Now active with all features!\n\n"
            f"**Try your bot:**\n"
            f"• /start - Start bot\n"
            f"• /help - Help menu\n"
            f"• Inline: `@{user_bot_me.username} message @username`",
            buttons=[
                [Button.switch_inline("🚀 Test Your Bot", query="", same_peer=True)],
                [Button.inline("🤖 My Bots", data="my_bots")],
                [Button.url("📢 Support", "https://t.me/shribots")]
            ]
        )
        
    except Exception as e:
        logger.error(f"Clone error: {e}")
        error_msg = f"❌ **Clone Failed!**\n\nError: {str(e)}"
        await event.reply(
            error_msg,
            buttons=[
                [Button.inline("🔄 Try Again", data="clone_info")],
                [Button.url("🤖 BotFather", "https://t.me/BotFather")]
            ]
        )

@bot.on(events.NewMessage(pattern="^[!?/]mybots$"))
async def my_bots_command(event):
    """Handle /mybots command"""
    try:
        user_id = event.sender.id
        user_clones = [k for k, v in clone_stats.items() if v.get('owner_id') == user_id]
        
        if not user_clones:
            await event.reply(
                "🤖 **You haven't cloned any bots yet!**\n\n"
                "Use /clone command to create your own whisper bot.",
                buttons=[[Button.inline("🔧 Clone Now", data="clone_info")]]
            )
            return
        
        bot_list = "🤖 **Your Cloned Bots:**\n\n"
        for i, bot_token in enumerate(user_clones, 1):
            bot_info = clone_stats[bot_token]
            bot_list += f"{i}. @{bot_info.get('username', 'Unknown')}\n"
            bot_list += f"   📅 Created: {bot_info.get('created_at', 'Unknown')}\n\n"
        
        await event.reply(
            bot_list,
            buttons=[
                [Button.inline("🗑 Remove Bots", data="remove_bots")],
                [Button.inline("🔄 Refresh", data="my_bots")]
            ]
        )
    except Exception as e:
        logger.error(f"Error in mybots command: {e}")

@bot.on(events.CallbackQuery())
async def callback_handler(event):
    """Handle callback queries"""
    try:
        data = event.data.decode('utf-8')
        
        if data == "help":
            me = await bot.get_me()
            await event.edit(HELP_TEXT.format(me.username, me.username, me.username))
        
        elif data == "clone_info":
            await event.edit(
                "🔧 **Clone Bot**\n\nUse /clone command with your bot token.",
                buttons=[[Button.inline("🔙 Back", data="back_to_start")]]
            )
        
        elif data == "my_bots":
            user_id = event.sender.id
            user_clones = [k for k, v in clone_stats.items() if v.get('owner_id') == user_id]
            
            if not user_clones:
                await event.edit("No bots cloned yet! Use /clone")
                return
            
            bot_list = "🤖 **Your Bots:**\n"
            for token in user_clones[:5]:
                info = clone_stats[token]
                bot_list += f"\n@{info['username']}\n"
            
            await event.edit(
                bot_list,
                buttons=[
                    [Button.inline("🗑 Remove", data="remove_bots")],
                    [Button.inline("🔙 Back", data="back_to_start")]
                ]
            )
        
        elif data == "remove_bots":
            user_id = event.sender.id
            user_clones = [k for k, v in clone_stats.items() if v.get('owner_id') == user_id]
            
            if not user_clones:
                await event.answer("No bots to remove!", alert=True)
                return
            
            # Remove first 3 bots
            for token in user_clones[:3]:
                if token in user_bots:
                    try:
                        await user_bots[token].disconnect()
                    except:
                        pass
                    del user_bots[token]
                if token in clone_stats:
                    del clone_stats[token]
            
            save_clone_stats()
            await event.answer("✅ Bots removed!", alert=True)
            await event.edit("✅ Your cloned bots have been removed.")
        
        elif data == "back_to_start":
            await event.edit(
                WELCOME_TEXT,
                buttons=[
                    [Button.url("📢 Support", "https://t.me/shribots")],
                    [Button.switch_inline("🚀 Try Inline", query="")],
                    [Button.inline("📖 Help", data="help"), 
                     Button.inline("🔧 Clone", data="clone_info")],
                    [Button.inline("🤖 My Bots", data="my_bots")]
                ]
            )
        
        elif data in db:
            msg_data = db[data]
            if event.sender.id in [msg_data['user_id'], msg_data['sender_id']]:
                await event.answer(msg_data['msg'], alert=True)
            else:
                await event.answer("Not for you!", alert=True)
                
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        await event.answer("❌ An error occurred", alert=True)

@bot.on(events.InlineQuery())
async def inline_handler(event):
    """Handle inline queries"""
    try:
        cleanup_old_messages()
        
        if len(event.text) == 0:
            result_text = (
                "**🔒 Whisper Bot**\n\n"
                "**Send secret messages:**\n"
                "`message @username`\n\n"
                "**Examples:**\n"
                "• `Hello! @username`\n"
                "• `I miss you 123456789`\n\n"
                "🔒 Only they can read your message!"
            )
            
            result = event.builder.article(
                title="🤫 Whisper Bot",
                description="Send secret messages",
                text=result_text,
                buttons=[[Button.switch_inline("🔐 Send Whisper", query="")]]
            )
            await event.answer([result])
            return
        
        query_text = event.text.strip()
        patterns = [r'@(\w+)$', r'(\d+)$']
        target_user = None
        message_text = query_text
        
        for pattern in patterns:
            match = re.search(pattern, query_text)
            if match:
                if pattern == r'@(\w+)$':
                    target_user = match.group(1)
                    message_text = query_text.replace(f"@{target_user}", "").strip()
                else:
                    target_user = match.group(1)
                    message_text = query_text.replace(target_user, "").strip()
                break
        
        if not target_user or not message_text:
            await event.answer([], switch_pm="Format: Message @username OR Message 123456789")
            return
        
        try:
            if target_user.isdigit():
                user_obj = await bot.get_entity(int(target_user))
            else:
                user_obj = await bot.get_entity(target_user)
            
            add_to_recent_users(event.sender.id, user_obj)
            
        except Exception as e:
            logger.error(f"Error getting user entity: {e}")
            await event.answer([], switch_pm="User not found!")
            return
        
        message_id = create_unique_message_id(event.sender.id, user_obj.id)
        db[message_id] = {
            "user_id": user_obj.id,
            "msg": message_text,
            "sender_id": event.sender.id,
            "timestamp": datetime.now().isoformat()
        }
        
        result = event.builder.article(
            title="🔒 Secret Message",
            description=f"For {user_obj.first_name}",
            text=f"**🔐 A secret message for {user_obj.first_name}!**\n\n*Note: Only {user_obj.first_name} can open this message.*",
            buttons=[[Button.inline("🔓 Show Message", data=message_id)]]
        )
        await event.answer([result])
        
    except Exception as e:
        logger.error(f"Error in inline handler: {e}")
        await event.answer([], switch_pm="An error occurred")

async def main():
    """Main function"""
    try:
        me = await bot.get_me()
        logger.info("🎭 ShriBots Whisper Bot Started!")
        logger.info(f"🤖 Bot: @{me.username}")
        logger.info(f"👑 Admin ID: {ADMIN_ID}")
        logger.info(f"📊 Total Clones: {len(clone_stats)}")
        logger.info("🚀 Bot is ready and running!")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        exit(1)

if __name__ == "__main__":
    # Start the bot
    bot.loop.run_until_complete(main())
    logger.info("🤖 Starting bot event loop...")
    bot.run_until_disconnected()