from telethon import TelegramClient, events, Button
import logging
import os
import re
import asyncio
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
API_ID = int(os.getenv('API_ID', '25136703'))
API_HASH = os.getenv('API_HASH', 'accfaf5ecd981c67e481328515c39f89')
BOT_TOKEN = os.getenv('BOT_TOKEN', '8366493122:AAG7nl7a3BqXd8-oyTAHovAjc7UUuLeHb-4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '8027090675'))
PORT = int(os.environ.get('PORT', 10000))

# Support channels
SUPPORT_CHANNEL = "@shribots"
SUPPORT_GROUP = "@shribots"

# Initialize bot
bot = TelegramClient('whisper_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Storage
messages_db = {}
user_bots = {}
clone_stats = {}
recent_users = {}

# Data files
CLONE_FILE = "clone_stats.json"
RECENT_USERS_FILE = "recent_users.json"

def load_data():
    global clone_stats, recent_users
    try:
        if os.path.exists(CLONE_FILE):
            with open(CLONE_FILE, 'r') as f:
                clone_stats = json.load(f)
        
        if os.path.exists(RECENT_USERS_FILE):
            with open(RECENT_USERS_FILE, 'r') as f:
                recent_users = json.load(f)
    except Exception as e:
        logger.error(f"Error loading data: {e}")

def save_data():
    try:
        with open(CLONE_FILE, 'w') as f:
            json.dump(clone_stats, f, indent=2)
        
        with open(RECENT_USERS_FILE, 'w') as f:
            json.dump(recent_users, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

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
📌 clone Whisper to use @shribots now

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

async def send_welcome_with_animation(event, bot_instance=None, is_cloned_bot=False):
    """Send animation and welcome message"""
    if bot_instance is None:
        bot_instance = bot
    
    try:
        await bot_instance.send_file(
            event.chat_id,
            ANIMATION_URL,
            caption="🚀 **Starting your whisper experience...**"
        )
        await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"Animation error: {e}")
    
    if is_cloned_bot:
        await event.reply(
            WELCOME_TEXT,
            buttons=[
                [Button.url("📢 Support Channel", f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
                [Button.url("👥 Support Group", f"https://t.me/{SUPPORT_GROUP[1:]}")],
                [Button.switch_inline("🚀 Try Now", query="")],
                [Button.url("🔧 Clone Bot", "https://t.me/shribots"), Button.inline("📖 Help", data="help")]
            ]
        )
    elif event.sender_id == ADMIN_ID:
        await event.reply(
            WELCOME_TEXT,
            buttons=[
                [Button.url("📢 Support Channel", f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
                [Button.url("👥 Support Group", f"https://t.me/{SUPPORT_GROUP[1:]}")],
                [Button.switch_inline("🚀 Try Now", query="")],
                [Button.inline("📊 Statistics", data="admin_stats"), Button.inline("👥 Manage", data="admin_manage")],
                [Button.inline("📖 Help", data="help"), Button.inline("🔧 Clone", data="clone_info")]
            ]
        )
    else:
        await event.reply(
            WELCOME_TEXT,
            buttons=[
                [Button.url("📢 Support Channel", f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
                [Button.url("👥 Support Group", f"https://t.me/{SUPPORT_GROUP[1:]}")],
                [Button.switch_inline("🚀 Try Now", query="")],
                [Button.inline("📖 Help", data="help"), Button.inline("🔧 Clone", data="clone_info")],
                [Button.inline("🤖 My Bots", data="my_bots")]
            ]
        )

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    try:
        await send_welcome_with_animation(event)
    except Exception as e:
        logger.error(f"Start error: {e}")

@bot.on(events.NewMessage(pattern='/stats'))
async def stats_handler(event):
    if event.sender_id != ADMIN_ID:
        await event.reply("❌ Admin only command!")
        return
        
    total_clones = len(clone_stats)
    active_bots = len(user_bots)
    
    stats_text = f"""
📊 **Admin Statistics**

🤖 Total Clones: {total_clones}
⚡ Active Bots: {active_bots}

**Recent Clones:**
"""
    recent_clones = list(clone_stats.items())[-5:]
    for i, (token, info) in enumerate(recent_clones, 1):
        stats_text += f"\n{i}. @{info.get('username', 'Unknown')}"
        stats_text += f"\n   👤 User: {info.get('owner_id')}"
        stats_text += f"\n   👤 Name: {info.get('first_name', 'N/A')}"
        stats_text += f"\n   📅 {info.get('created_at')}"
    
    await event.reply(stats_text)

@bot.on(events.NewMessage(pattern='/mybots'))
async def mybots_handler(event):
    user_id = event.sender_id
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
        bot_list += f"   📅 Created: {bot_info.get('created_at', 'Unknown')}\n"
        bot_list += f"   🆔 Token: `{bot_token[:10]}...`\n\n"
    
    await event.reply(
        bot_list,
        buttons=[[Button.inline("🗑 Remove Bots", data="remove_bots")]]
    )

@bot.on(events.NewMessage(pattern='/remove'))
async def remove_handler(event):
    user_id = event.sender_id
    user_clones = [k for k, v in clone_stats.items() if v.get('owner_id') == user_id]
    
    if not user_clones:
        await event.reply("❌ You have no bots to remove!")
        return
    
    removed = 0
    for token in user_clones:
        if token in user_bots:
            try:
                await user_bots[token].disconnect()
                del user_bots[token]
            except:
                pass
        if token in clone_stats:
            del clone_stats[token]
            removed += 1
    
    save_data()
    await event.reply(f"✅ Removed {removed} of your bots!")

@bot.on(events.NewMessage(pattern='/clone'))
async def clone_handler(event):
    clone_text = """
🔧 **Clone Bot Commands**

🤖 **Create your own Whisper Bot:**

**Available Commands:**
• `/clone bot_token` - Clone a new bot
• `/mybots` - View your cloned bots  
• `/remove` - Remove your bots

**Steps:**
1. Go to @BotFather
2. Create new bot with /newbot
3. Get bot token
4. Send: `/clone your_bot_token`

**Example:**
`/clone 1234567890:ABCdefGHIjkl...`

⚠️ **Note:**
• One bot per user only
• Keep token safe
    """
    await event.reply(
        clone_text,
        buttons=[
            [Button.url("🤖 BotFather", "https://t.me/BotFather")],
            [Button.inline("🔙 Back", data="back_start")]
        ]
    )

@bot.on(events.NewMessage(pattern=r'/clone\s+(\S+)'))
async def clone_token_handler(event):
    try:
        user_id = event.sender_id
        token = event.pattern_match.group(1)
        
        user_clones = [k for k, v in clone_stats.items() if v.get('owner_id') == user_id]
        if user_clones:
            await event.reply(
                "❌ **You already have a cloned bot!**\n\n"
                "Each user can only clone one bot.\n"
                "Please use another account to clone again.",
                buttons=[[Button.inline("🤖 My Bot", data="my_bot")]]
            )
            return
        
        if not re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
            await event.reply(
                "❌ **Invalid Token Format!**\n\n"
                "Please check your bot token.\n"
                "Format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`",
                buttons=[[Button.inline("🔄 Try Again", data="clone_info")]]
            )
            return
        
        if token in clone_stats:
            await event.reply(
                "❌ **This bot is already cloned!**\n\n"
                "Please use a different bot token.",
                buttons=[[Button.inline("🔄 Try Again", data="clone_info")]]
            )
            return
        
        creating_msg = await event.reply("🔄 **Creating your bot...**")
        
        user_bot = TelegramClient(f'user_bot_{user_id}', API_ID, API_HASH)
        await user_bot.start(bot_token=token)
        
        bot_me = await user_bot.get_me()
        user_bots[token] = user_bot
        
        user_mention = f"[{event.sender.first_name}](tg://user?id={user_id})"
        
        clone_stats[token] = {
            'owner_id': user_id,
            'username': bot_me.username,
            'first_name': getattr(event.sender, 'first_name', ''),
            'mention': user_mention,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'token_preview': token[:10] + '...'
        }
        save_data()
        
        @user_bot.on(events.NewMessage(pattern='/start'))
        async def user_start(event):
            await send_welcome_with_animation(event, user_bot, is_cloned_bot=True)
        
        @user_bot.on(events.InlineQuery())
        async def user_inline(event):
            await handle_inline_query(event, user_bot)
        
        @user_bot.on(events.CallbackQuery())
        async def user_callback(event):
            data = event.data.decode('utf-8')
            
            if data == "help":
                await event.edit(
                    "📖 **Help Guide**\n\nUse inline mode: `message @username`",
                    buttons=[[Button.inline("🔙 Back", data="back_start")]]
                )
            
            elif data == "clone_info":
                await event.answer("🔧 Visit @shribots to clone more bots!", alert=True)
            
            elif data == "back_start":
                await send_welcome_with_animation(event, user_bot, is_cloned_bot=True)
            
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
            
            elif data in messages_db:
                msg_data = messages_db[data]
                if event.sender_id in [msg_data['user_id'], msg_data['sender_id']]:
                    await event.answer(msg_data['msg'], alert=True)
                else:
                    await event.answer("Not for you!", alert=True)
        
        try:
            mention_link = f"[{event.sender.first_name}](tg://user?id={user_id})"
            
            notification_text = f"""
🆕 **New Bot Cloned!**

🤖 **Bot:** @{bot_me.username}
👤 **User ID:** `{user_id}`
👤 **User Name:** {event.sender.first_name}
📌 **Mention:** {mention_link}
📅 **Time:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
🔢 **Total Clones:** {len(clone_stats)}
            """
            
            await bot.send_message(
                ADMIN_ID,
                notification_text,
                parse_mode='markdown'
            )
        except Exception as e:
            logger.error(f"Admin notification error: {e}")
        
        await creating_msg.edit(
            f"✅ **Bot Cloned Successfully!**\n\n"
            f"🤖 **Your Bot:** @{bot_me.username}\n"
            f"🎉 Now active with all features!\n\n"
            f"**Try your bot:**\n"
            f"`@{bot_me.username} message @username`",
            buttons=[
                [Button.switch_inline("🚀 Test Your Bot", query="", same_peer=True)],
                [Button.inline("🤖 My Bots", data="my_bots")]
            ]
        )
        
    except Exception as e:
        logger.error(f"Clone error: {e}")
        await event.reply(f"❌ **Clone Failed!**\n\nError: {str(e)}")

@bot.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    help_text = """
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
   • /clone - Create your bot
   • /mybots - Your cloned bots
   • /remove - Remove your bots

🔒 **Only the mentioned user can read your message!**
    """.format((await bot.get_me()).username, 
              (await bot.get_me()).username,
              (await bot.get_me()).username)
    
    await event.reply(
        help_text,
        buttons=[
            [Button.switch_inline("🚀 Try Now", query="")],
            [Button.inline("🔧 Clone Bot", data="clone_info")]
        ]
    )

async def handle_inline_query(event, client=None):
    """Handle inline queries with proper error handling"""
    if client is None:
        client = bot
    
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
                user_obj = await client.get_entity(int(target_user))
            else:
                if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{3,30}$', target_user):
                    result = event.builder.article(
                        title="❌ Invalid Username",
                        description="Username format is invalid",
                        text="**Valid username:**\n• Starts with letter\n• 4-31 characters\n• Letters, numbers, underscores"
                    )
                    await event.answer([result])
                    return
                user_obj = await client.get_entity(target_user)
            
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
    
    elif data == "clone_info":
        clone_text = """
🔧 **Clone Bot Commands**

**Available Commands:**
• `/clone bot_token` - Clone a new bot
• `/mybots` - View your cloned bots  
• `/remove` - Remove your bots

**Example:**
`/clone 1234567890:ABCdefGHIjkl...`
        """
        await event.edit(
            clone_text,
            buttons=[
                [Button.url("🤖 BotFather", "https://t.me/BotFather")],
                [Button.inline("🔙 Back", data="back_start")]
            ]
        )
    
    elif data == "my_bot" or data == "my_bots":
        user_id = event.sender_id
        user_clones = [k for k, v in clone_stats.items() if v.get('owner_id') == user_id]
        if user_clones:
            token = user_clones[0]
            info = clone_stats[token]
            await event.edit(
                f"🤖 **Your Bot:** @{info['username']}\n"
                f"📅 Created: {info['created_at']}",
                buttons=[[Button.inline("🔙 Back", data="back_start")]]
            )
        else:
            await event.answer("No bots found!", alert=True)
    
    elif data == "remove_bots":
        user_id = event.sender_id
        user_clones = [k for k, v in clone_stats.items() if v.get('owner_id') == user_id]
        
        if not user_clones:
            await event.answer("No bots to remove!", alert=True)
            return
        
        removed = 0
        for token in user_clones:
            if token in user_bots:
                try:
                    await user_bots[token].disconnect()
                    del user_bots[token]
                except:
                    pass
            if token in clone_stats:
                del clone_stats[token]
                removed += 1
        
        save_data()
        await event.answer(f"✅ {removed} bots removed!", alert=True)
        await event.edit(f"✅ Removed {removed} of your bots!")
    
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
    
    elif data == "admin_stats":
        if event.sender_id != ADMIN_ID:
            await event.answer("Admin only!", alert=True)
            return
            
        total_clones = len(clone_stats)
        active_bots = len(user_bots)
        
        stats_text = f"📊 **Admin Statistics**\n\n"
        stats_text += f"🤖 Total Clones: {total_clones}\n"
        stats_text += f"⚡ Active Bots: {active_bots}\n\n"
        
        if clone_stats:
            stats_text += "**Recent Clones:**\n"
            recent_clones = list(clone_stats.items())[-3:]
            for i, (token, info) in enumerate(recent_clones, 1):
                stats_text += f"\n{i}. @{info.get('username', 'Unknown')}"
                stats_text += f"\n   👤 User: {info.get('owner_id')}"
                stats_text += f"\n   👤 Name: {info.get('first_name', 'N/A')}"
                stats_text += f"\n   📅 {info.get('created_at')}"
        
        await event.edit(stats_text)
    
    elif data == "admin_manage":
        if event.sender_id != ADMIN_ID:
            await event.answer("Admin only!", alert=True)
            return
            
        await event.edit(
            "👥 **Manage Bots**\n\n"
            "Use commands:\n"
            "• /stats - View statistics\n"
            "• Check clone list below",
            buttons=[[Button.inline("📋 Clone List", data="clone_list")]]
        )
    
    elif data == "clone_list":
        if event.sender_id != ADMIN_ID:
            await event.answer("Admin only!", alert=True)
            return
            
        if not clone_stats:
            await event.edit("No clones yet!")
            return
        
        clone_list = "📋 **All Cloned Bots:**\n\n"
        for i, (token, info) in enumerate(clone_stats.items(), 1):
            clone_list += f"{i}. @{info['username']}\n"
            clone_list += f"   👤 User ID: {info['owner_id']}\n"
            clone_list += f"   👤 Name: {info.get('first_name', 'N/A')}\n"
            clone_list += f"   📅 {info['created_at']}\n"
            clone_list += f"   🔑 Token: {info['token_preview']}\n\n"
        
        await event.edit(clone_list[:4000])
    
    elif data == "back_start":
        user_id = event.sender_id
        
        if user_id == ADMIN_ID:
            await event.edit(
                WELCOME_TEXT,
                buttons=[
                    [Button.url("📢 Support Channel", f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
                    [Button.url("👥 Support Group", f"https://t.me/{SUPPORT_GROUP[1:]}")],
                    [Button.switch_inline("🚀 Try Now", query="")],
                    [Button.inline("📊 Statistics", data="admin_stats"), Button.inline("👥 Manage", data="admin_manage")],
                    [Button.inline("📖 Help", data="help"), Button.inline("🔧 Clone", data="clone_info")]
                ]
            )
        else:
            await event.edit(
                WELCOME_TEXT,
                buttons=[
                    [Button.url("📢 Support Channel", f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
                    [Button.url("👥 Support Group", f"https://t.me/{SUPPORT_GROUP[1:]}")],
                    [Button.switch_inline("🚀 Try Now", query="")],
                    [Button.inline("📖 Help", data="help"), Button.inline("🔧 Clone", data="clone_info")],
                    [Button.inline("🤖 My Bots", data="my_bots")]
                ]
            )
    
    elif data in messages_db:
        msg_data = messages_db[data]
        if event.sender_id in [msg_data['user_id'], msg_data['sender_id']]:
            await event.answer(msg_data['msg'], alert=True)
        else:
            await event.answer("Not for you!", alert=True)

async def main():
    
    # Bot info
    me = await bot.get_me()
    logger.info(f"🎭 ShriBots Whisper Bot Started!")
    logger.info(f"🤖 Bot: @{me.username}")
    logger.info(f"👑 Admin: {ADMIN_ID}")
    logger.info(f"📊 Clones: {len(clone_stats)}")
    logger.info(f"👥 Recent Users: {len(recent_users)}")
    logger.info("🚀 Bot is ready and working!")

if __name__ == '__main__':
    bot.loop.run_until_complete(main())
    bot.run_until_disconnected()
