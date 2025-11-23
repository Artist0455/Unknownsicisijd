from telethon import events, TelegramClient, Button
import logging
from telethon.tl.functions.users import GetFullUserRequest as us
import os
import re
import asyncio
import json
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

# Environment variables
API_ID = int(os.getenv('API_ID', 25136703))
API_HASH = os.getenv('API_HASH', "accfaf5ecd981c67e481328515c39f89")
BOT_TOKEN = os.getenv('BOT_TOKEN', "8521103806:AAHHQ2XL_EokOXmJCdElfkkSrnYAkr0IVB4")
ADMIN_ID = int(os.getenv('ADMIN_ID', 8272213732))

bot = TelegramClient(
    "WhisperBot",
    api_id=API_ID,
    api_hash=API_HASH
).start(bot_token=BOT_TOKEN)

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
    except:
        clone_stats = {}

def save_clone_stats():
    try:
        with open(CLONE_FILE, 'w') as f:
            json.dump(clone_stats, f)
    except:
        pass

def load_recent_users():
    global recent_users
    try:
        if os.path.exists(RECENT_USERS_FILE):
            with open(RECENT_USERS_FILE, 'r') as f:
                recent_users = json.load(f)
    except:
        recent_users = {}

def save_recent_users():
    try:
        with open(RECENT_USERS_FILE, 'w') as f:
            json.dump(recent_users, f)
    except:
        pass

load_clone_stats()
load_recent_users()

WELCOME_TEXT = """
╔══════════════════════╗
║     🎭 𝗦𝗛𝗥𝗜𝗕𝗢𝗧𝗦     ║ powered by
║    𝗪𝗛𝗜𝗦𝗣𝗘𝗥 𝗕𝗢𝗧    ║     Artist 
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

def cleanup_old_messages():
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
            print(f"🧹 Cleaned {len(keys_to_remove)} old messages")
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

def cleanup_old_recent_users():
    try:
        current_time = datetime.now()
        users_to_remove = []
        
        for user_id, user_data in recent_users.items():
            if 'last_used' in user_data:
                last_used = datetime.fromisoformat(user_data['last_used'])
                if current_time - last_used > timedelta(days=7):
                    users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            del recent_users[user_id]
        
        if users_to_remove:
            print(f"🧹 Cleaned {len(users_to_remove)} old recent users")
            save_recent_users()
    except Exception as e:
        print(f"❌ Recent users cleanup error: {e}")

def create_unique_message_id(sender_id, target_id):
    timestamp = int(datetime.now().timestamp())
    return f"msg_{sender_id}_{target_id}_{timestamp}"

def add_to_recent_users(sender_id, target_user_obj):
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
        print(f"❌ Error adding to recent users: {e}")

def get_recent_users_buttons(sender_id, max_users=5):
    try:
        cleanup_old_recent_users()
        user_recent = {}
        
        for key, data in recent_users.items():
            user_recent[key] = data
        
        sorted_users = sorted(user_recent.items(), 
                            key=lambda x: x[1].get('last_used', ''), 
                            reverse=True)
        
        buttons = []
        for user_key, user_data in sorted_users[:max_users]:
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
        print(f"❌ Error getting recent users: {e}")
        return []

@bot.on(events.NewMessage(pattern="^[!?/]start$"))
async def start_command(event):
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
            [Button.url("📢 Support Channel", "https://t.me/shribots"), 
             Button.url("👥 Support Group", "https://t.me/shribots")],
            [Button.switch_inline("🚀 Try Inline", query="")],
            [Button.inline("📖 Help", data="help"), 
             Button.inline("🔧 Clone Bot", data="clone_info")],
            [Button.inline("🤖 My Bots", data="my_bots")]
        ]
    )

@bot.on(events.NewMessage(pattern="^[!?/]help$"))
async def help_command(event):
    me = await bot.get_me()
    await event.reply(
        HELP_TEXT.format(me.username, me.username, me.username),
        buttons=[
            [Button.url("📢 Support Channel", "https://t.me/shribots")],
            [Button.switch_inline("🚀 Try Inline", query="")],
            [Button.inline("🔧 Clone Bot", data="clone_info")],
            [Button.inline("🤖 My Bots", data="my_bots")]
        ]
    )

@bot.on(events.NewMessage(pattern="^[!?/]mybots$"))
async def my_bots_command(event):
    user_id = event.sender.id
    user_clones = [k for k, v in clone_stats.items() if v.get('owner_id') == user_id]
    
    if not user_clones:
        await event.reply(
            "🤖 **You haven't cloned any bots yet!**\n\n"
            "Use /clone command to create your own whisper bot.",
            buttons=[
                [Button.inline("🔧 Clone Now", data="clone_info")]
            ]
        )
        return
    
    bot_list = "🤖 **Your Cloned Bots:**\n\n"
    for i, bot_token in enumerate(user_clones, 1):
        bot_info = clone_stats[bot_token]
        bot_list += f"{i}. @{bot_info.get('username', 'Unknown')}\n"
        bot_list += f"   📅 Created: {bot_info.get('created_at', 'Unknown')}\n"
        bot_list += f"   🆔 Token: `{bot_token[:10]}...`\n\n"
    
    bot_list += "Click below to manage your bots:"
    
    await event.reply(
        bot_list,
        buttons=[
            [Button.inline("🗑 Remove Bots", data="remove_bots")],
            [Button.inline("🔄 Refresh", data="my_bots")]
        ]
    )

@bot.on(events.NewMessage(pattern="^[!?/]stats$"))
async def stats_command(event):
    if event.sender.id != ADMIN_ID:
        await event.reply("❌ This command is for admin only!")
        return
    
    total_clones = len(clone_stats)
    active_bots = len(user_bots)
    
    stats_text = f"""
📊 **Admin Statistics**

🤖 Total Clones: {total_clones}
⚡ Active Bots: {active_bots}
📅 Tracking Since: {datetime.now().strftime('%Y-%m-%d')}

**Clone Details:**
"""
    
    for i, (token, info) in enumerate(list(clone_stats.items())[:10], 1):
        stats_text += f"\n{i}. @{info.get('username', 'Unknown')}"
        stats_text += f"\n   👤 Owner: {info.get('owner_id', 'Unknown')}"
        stats_text += f"\n   📅 {info.get('created_at', 'Unknown')}"
    
    if total_clones > 10:
        stats_text += f"\n\n... and {total_clones - 10} more clones"
    
    await event.reply(
        stats_text,
        buttons=[
            [Button.inline("🔄 Refresh", data="admin_stats")],
            [Button.inline("🗑 Clean Inactive", data="clean_bots")]
        ]
    )

@bot.on(events.NewMessage(pattern="^[!?/]clone(?:\s+(\S+))?$"))
async def clone_command(event):
    input_token = event.pattern_match.group(1)
    
    if not input_token:
        clone_text = """
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
            clone_text,
            buttons=[
                [Button.url("🤖 Create Bot", "https://t.me/BotFather")],
                [Button.inline("🔙 Back", data="back_to_start")]
            ]
        )
        return
    
    if not re.match(r'^\d+:[A-Za-z0-9_-]+$', input_token):
        await event.reply(
            "❌ **Invalid Token Format!**\n\n"
            "Please check your bot token.\n"
            "Format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`",
            buttons=[[Button.inline("🔄 Try Again", data="clone_info")]]
        )
        return
    
    if input_token in clone_stats:
        await event.reply(
            "❌ **This bot is already cloned!**\n\n"
            "You can manage it with /mybots command.",
            buttons=[[Button.inline("🤖 My Bots", data="my_bots")]]
        )
        return
    
    try:
        creating_msg = await event.reply("🔄 **Creating your bot...**")
        
        user_bot = TelegramClient(
            f"user_bot_{event.sender.id}_{len(user_bots)}",
            api_id=API_ID,
            api_hash=API_HASH
        )
        
        await user_bot.start(bot_token=input_token)
        user_bot_me = await user_bot.get_me()
        
        user_bots[input_token] = user_bot
        clone_stats[input_token] = {
            'owner_id': event.sender.id,
            'username': user_bot_me.username,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'token_preview': input_token[:10] + '...'
        }
        save_clone_stats()
        
        await setup_user_bot_handlers(user_bot, input_token)
        
        if ADMIN_ID:
            try:
                await bot.send_message(
                    ADMIN_ID,
                    f"🆕 **New Bot Cloned!**\n\n"
                    f"🤖 Bot: @{user_bot_me.username}\n"
                    f"👤 Owner: {event.sender.id}\n"
                    f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                    f"🔢 Total Clones: {len(clone_stats)}"
                )
            except:
                pass
        
        await creating_msg.edit(
            f"✅ **Bot Cloned Successfully!**\n\n"
            f"🤖 **Your Bot:** @{user_bot_me.username}\n"
            f"🎉 Now active with all features!\n\n"
            f"**Commands for your bot:**\n"
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
        error_msg = f"❌ **Clone Failed!**\n\nError: {str(e)}"
        await event.reply(
            error_msg,
            buttons=[
                [Button.inline("🔄 Try Again", data="clone_info")],
                [Button.url("🤖 BotFather", "https://t.me/BotFather")]
            ]
        )

async def setup_user_bot_handlers(user_bot, token):
    @user_bot.on(events.NewMessage(pattern="^[!?/]start$"))
    async def user_start_command(event):
        await event.reply(
            WELCOME_TEXT,
            buttons=[
                [Button.url("📢 Support Channel", "https://t.me/shribots")],
                [Button.switch_inline("🚀 Try Inline", query="")],
                [Button.inline("📖 Help", data="user_help")]
            ]
        )
    
    @user_bot.on(events.NewMessage(pattern="^[!?/]help$"))
    async def user_help_command(event):
        me = await user_bot.get_me()
        await event.reply(
            HELP_TEXT.format(me.username, me.username, me.username),
            buttons=[
                [Button.url("📢 Support Channel", "https://t.me/shribots")],
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
        me = (await user_bot.get_me()).username
        
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
            text=f"**🔐 A secret message for {user_obj.first_name}!**\n\n*Note: Only {user_obj.first_name} can open this message.*",
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

@bot.on(events.CallbackQuery())
async def callback_handler(event):
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
        
        for token in user_clones[:3]:
            if token in user_bots:
                await user_bots[token].disconnect()
                del user_bots[token]
            if token in clone_stats:
                del clone_stats[token]
        
        save_clone_stats()
        await event.answer("✅ Bots removed!", alert=True)
        await event.edit("✅ Your cloned bots have been removed.")
    
    elif data == "admin_stats":
        if event.sender.id != ADMIN_ID:
            await event.answer("Admin only!", alert=True)
            return
        
        total = len(clone_stats)
        await event.edit(f"📊 Total Clones: {total}")
    
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

@bot.on(events.InlineQuery())
async def inline_handler(event):
    cleanup_old_messages()
    
    if len(event.text) == 0:
        me = (await bot.get_me()).username
        
        recent_buttons = get_recent_users_buttons(event.sender.id)
        
        result_text = f"**🔒 Whisper Bot**\n\n"
        
        if recent_buttons:
            result_text += "**Recent Users:**\nClick any user below to message them quickly!\n\n"
        
        result_text += (
            f"**Or type manually:**\n"
            f"`your_message @username`\n\n"
            f"**Examples:**\n"
            f"• `Hello! @username`\n"
            f"• `I miss you 123456789`\n\n"
            f"🔒 Only they can read your message!"
        )
        
        if recent_buttons:
            result = event.builder.article(
                title="🤫 Whisper Bot - Quick Send",
                description="Send to recent users or type manually",
                text=result_text,
                buttons=recent_buttons + [
                    [Button.switch_inline("✏️ Type Manually", query="")]
                ]
            )
        else:
            result = event.builder.article(
                title="🤫 Whisper Bot",
                description="Send secret messages",
                text=result_text,
                buttons=[[Button.switch_inline("🔐 Send Whisper", query="")]]
            )
        
        await event.answer([result])
        return
    
    query_text = event.text.strip()
    me = (await bot.get_me()).username
    
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
        title="🔒 Secret Message",
        description=f"For {user_obj.first_name}",
        text=f"**🔐 A secret message for {user_obj.first_name}!**\n\n*Note: Only {user_obj.first_name} can open this message.*",
        buttons=[[Button.inline("🔓 Show Message", data=message_id)]]
    )
    await event.answer([result])

async def main():
    me = await bot.get_me()
    print("🎭 ShriBots Whisper Bot Started!")
    print(f"🤖 Bot: @{me.username}")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"📊 Total Clones: {len(clone_stats)}")
    print(f"👥 Recent Users: {len(recent_users)}")
    print("🧹 Auto-cleanup enabled for old messages")

if __name__ == "__main__":
    bot.loop.run_until_complete(main())
    bot.run_until_disconnected()