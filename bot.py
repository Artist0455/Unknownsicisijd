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

# Environment variables
API_ID = int(os.getenv('API_ID', '25136703'))
API_HASH = os.getenv('API_HASH', 'accfaf5ecd981c67e481328515c39f89')
BOT_TOKEN = os.getenv('BOT_TOKEN', '8521103806:AAHHQ2XL_EokOXmJCdElfkkSrnYAkr0IVB4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '8272213732'))

# Initialize bot
bot = TelegramClient(
    "WhisperBot",
    api_id=API_ID,
    api_hash=API_HASH
).start(bot_token=BOT_TOKEN)

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
🤫 **Welcome to Secret Whisper Bot!**

🔒 Send anonymous secret messages
🚀 Only intended recipient can read  
🎯 Easy to use inline mode

**Create whispers that only specific users can unlock!**
"""

HELP_TEXT = """
🤖 **How to Use:**

**1. Inline Mode:**
   • Type `@{}` in any chat
   • Write your message  
   • Add @username or user ID at end
   • Send!

**2. Examples:**
   • `@{} Hello secret! @username`
   • `@{} I miss you 123456789`

**3. Commands:**
   • /start - Start the bot
   • /help - This help menu
   • /clone - Clone this bot
   • /mybots - Your cloned bots

📢 **Support:** @ShriBots
"""

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

@bot.on(events.NewMessage(pattern=r"^[!?/]start$"))
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
                    [Button.inline("📊 Stats", data="admin_stats")],
                    [Button.switch_inline("🚀 Try", query="")]
                ]
            )
            return
        
        await event.reply(
            WELCOME_TEXT,
            buttons=[
                [Button.url("📢 Support", "https://t.me/shribots")],
                [Button.switch_inline("🚀 Try Inline", query="")],
                [Button.inline("📖 Help", data="help"), 
                 Button.inline("🔧 Clone", data="clone_info")]
            ]
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")

@bot.on(events.NewMessage(pattern=r"^[!?/]help$"))
async def help_command(event):
    """Handle /help command"""
    try:
        me = await bot.get_me()
        await event.reply(
            HELP_TEXT.format(me.username, me.username, me.username),
            buttons=[
                [Button.url("📢 Support", "https://t.me/shribots")],
                [Button.switch_inline("🚀 Try", query="")]
            ]
        )
    except Exception as e:
        logger.error(f"Error in help command: {e}")

@bot.on(events.NewMessage(pattern=r"^[!?/]clone(?:\s+(\S+))?$"))
async def clone_command(event):
    """Handle /clone command"""
    try:
        input_token = event.pattern_match.group(1)
        
        if not input_token:
            clone_text = """
🔧 **Clone Bot**

**Create your own Whisper Bot!**

🤖 **Steps:**
1. Go to @BotFather
2. Create new bot with /newbot  
3. Get bot token
4. Send: `/clone your_bot_token`

**Example:**
`/clone 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

⚠️ **Keep token safe!**
            """
            await event.reply(
                clone_text,
                buttons=[
                    [Button.url("🤖 BotFather", "https://t.me/BotFather")],
                    [Button.inline("🔙 Back", data="back_to_start")]
                ]
            )
            return
        
        # Validate token format
        if not re.match(r'^\d+:[A-Za-z0-9_-]+$', input_token):
            await event.reply(
                "❌ **Invalid Token!**\n\n"
                "Format: `1234567890:ABCdefGHIjkl...`",
                buttons=[[Button.inline("🔄 Try Again", data="clone_info")]]
            )
            return
        
        # Check if already cloned
        if input_token in clone_stats:
            await event.reply(
                "❌ **Already cloned!**\n\nUse /mybots to manage.",
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
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        save_clone_stats()
        
        # Setup basic handlers for cloned bot
        @user_bot.on(events.NewMessage(pattern=r"^[!?/]start$"))
        async def user_start_command(event):
            await event.reply(
                WELCOME_TEXT,
                buttons=[
                    [Button.url("📢 Support", "https://t.me/shribots")],
                    [Button.switch_inline("🚀 Try", query="")]
                ]
            )
        
        @user_bot.on(events.InlineQuery())
        async def user_inline_handler(event):
            if len(event.text) == 0:
                me = (await user_bot.get_me()).username
                result = event.builder.article(
                    title="Whisper Bot",
                    description="Send secret messages",
                    text=f"Use: `@{me} message @username`",
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
                text=f"**🔐 Secret message for {user_obj.first_name}!**\n\n*Only they can open it.*",
                buttons=[[Button.inline("🔓 Show", data=message_id)]]
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
        
        await creating_msg.edit(
            f"✅ **Bot Cloned!**\n\n"
            f"🤖 **Your Bot:** @{user_bot_me.username}\n"
            f"🎉 Ready to use!\n\n"
            f"Try: `@{user_bot_me.username} message @username`",
            buttons=[
                [Button.switch_inline("🚀 Test", query="", same_peer=True)],
                [Button.inline("🤖 My Bots", data="my_bots")]
            ]
        )
        
    except Exception as e:
        logger.error(f"Clone error: {e}")
        await event.reply(
            f"❌ **Clone Failed!**\n\nError: {str(e)}",
            buttons=[[Button.inline("🔄 Try Again", data="clone_info")]]
        )

@bot.on(events.NewMessage(pattern=r"^[!?/]mybots$"))
async def my_bots_command(event):
    """Handle /mybots command"""
    try:
        user_id = event.sender.id
        user_clones = [k for k, v in clone_stats.items() if v.get('owner_id') == user_id]
        
        if not user_clones:
            await event.reply(
                "🤖 **No bots cloned yet!**\n\nUse /clone to create one.",
                buttons=[[Button.inline("🔧 Clone", data="clone_info")]]
            )
            return
        
        bot_list = "🤖 **Your Bots:**\n\n"
        for i, bot_token in enumerate(user_clones, 1):
            bot_info = clone_stats[bot_token]
            bot_list += f"{i}. @{bot_info.get('username', 'Unknown')}\n"
        
        await event.reply(
            bot_list,
            buttons=[
                [Button.inline("🗑 Remove", data="remove_bots")],
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
                "🔧 **Clone Bot**\n\nUse /clone with your bot token.",
                buttons=[[Button.inline("🔙 Back", data="back_to_start")]]
            )
        
        elif data == "my_bots":
            user_id = event.sender.id
            user_clones = [k for k, v in clone_stats.items() if v.get('owner_id') == user_id]
            
            if not user_clones:
                await event.edit("No bots cloned! Use /clone")
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
            
            # Remove bots
            removed = 0
            for token in user_clones[:3]:
                if token in user_bots:
                    try:
                        await user_bots[token].disconnect()
                    except:
                        pass
                    del user_bots[token]
                if token in clone_stats:
                    del clone_stats[token]
                    removed += 1
            
            save_clone_stats()
            await event.answer(f"✅ {removed} bots removed!", alert=True)
            await event.edit(f"✅ Removed {removed} bots.")
        
        elif data == "back_to_start":
            await event.edit(
                WELCOME_TEXT,
                buttons=[
                    [Button.url("📢 Support", "https://t.me/shribots")],
                    [Button.switch_inline("🚀 Try", query="")],
                    [Button.inline("📖 Help", data="help"), 
                     Button.inline("🔧 Clone", data="clone_info")]
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

@bot.on(events.InlineQuery())
async def inline_handler(event):
    """Handle inline queries"""
    try:
        if len(event.text) == 0:
            result_text = (
                "**🔒 Whisper Bot**\n\n"
                "**Send secret messages:**\n"
                "`message @username`\n\n"
                "**Examples:**\n"
                "• `Hello! @username`\n"  
                "• `I miss you 123456789`\n\n"
                "🔒 Only they can read!"
            )
            
            result = event.builder.article(
                title="🤫 Whisper Bot",
                description="Send secret messages",
                text=result_text,
                buttons=[[Button.switch_inline("🔐 Send", query="")]]
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
                user_obj = await bot.get_entity(int(target_user))
            else:
                user_obj = await bot.get_entity(target_user)
            
            add_to_recent_users(event.sender.id, user_obj)
            
        except Exception as e:
            logger.error(f"Error getting user: {e}")
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
            text=f"**🔐 Secret message for {user_obj.first_name}!**\n\n*Only they can open it.*",
            buttons=[[Button.inline("🔓 Show", data=message_id)]]
        )
        await event.answer([result])
        
    except Exception as e:
        logger.error(f"Error in inline handler: {e}")

async def main():
    """Main function"""
    me = await bot.get_me()
    logger.info(f"🎭 Whisper Bot Started: @{me.username}")
    logger.info(f"📊 Clones: {len(clone_stats)}")

if __name__ == "__main__":
    bot.loop.run_until_complete(main())
    logger.info("🤖 Bot is running...")
    bot.run_until_disconnected()