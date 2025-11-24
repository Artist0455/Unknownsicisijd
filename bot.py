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
BOT_TOKEN = os.getenv('BOT_TOKEN', '8445905664:AAHmtWOra4ME4Lj3N-KLwgbJBdrDMYmYR1Y')
ADMIN_ID = int(os.getenv('ADMIN_ID', '8272213732'))

# Force join channels
SUPPORT_CHANNEL = "@shribots"  # Replace with your channel
SUPPORT_GROUP = "@shribots"    # Replace with your group

# Initialize bot
bot = TelegramClient('whisper_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Storage
messages_db = {}
user_bots = {}
clone_stats = {}

# Data file
CLONE_FILE = "clone_stats.json"

def load_data():
    global clone_stats
    try:
        if os.path.exists(CLONE_FILE):
            with open(CLONE_FILE, 'r') as f:
                clone_stats = json.load(f)
    except Exception as e:
        logger.error(f"Error loading data: {e}")

def save_data():
    try:
        with open(CLONE_FILE, 'w') as f:
            json.dump(clone_stats, f, indent=2)
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

async def check_user_joined(user_id):
    """Check if user has joined both channel and group"""
    try:
        # Check channel
        channel_member = await bot.get_permissions(SUPPORT_CHANNEL, user_id)
        # Check group  
        group_member = await bot.get_permissions(SUPPORT_GROUP, user_id)
        
        return bool(channel_member) and bool(group_member)
    except:
        return False

async def send_join_message(event):
    """Send join required message"""
    join_text = f"""
❌ **Join Required!**

To use this bot, you must join our channels:

📢 **Channel:** {SUPPORT_CHANNEL}
👥 **Group:** {SUPPORT_GROUP}

Please join both and then send /start again.
"""
    await event.reply(
        join_text,
        buttons=[
            [Button.url("📢 Join Channel", f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
            [Button.url("👥 Join Group", f"https://t.me/{SUPPORT_GROUP[1:]}")],
            [Button.inline("🔄 Check Join", "check_join")]
        ]
    )

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    try:
        user_id = event.sender_id
        
        # Check if user has joined required channels
        if not await check_user_joined(user_id):
            await send_join_message(event)
            return
        
        # Send animation for all users
        try:
            await bot.send_file(
                event.chat_id,
                ANIMATION_URL,
                caption="🚀 **Starting your whisper experience...**"
            )
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Animation error: {e}")
        
        if user_id == ADMIN_ID:
            # Admin panel
            await event.reply(
                "👑 **Admin Panel**\n\n"
                "📊 View bot statistics\n"
                "👥 Manage cloned bots\n"
                "🚀 Bot controls",
                buttons=[
                    [Button.inline("📊 Statistics", data="admin_stats")],
                    [Button.inline("👥 Manage Bots", data="admin_manage")],
                    [Button.inline("📋 Clone List", data="clone_list")],
                    [Button.switch_inline("🚀 Try Inline", query="")]
                ]
            )
        else:
            # Normal user
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
            
    except Exception as e:
        logger.error(f"Start error: {e}")

@bot.on(events.NewMessage(pattern='/stats'))
async def stats_handler(event):
    """Stats command for admin"""
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
        stats_text += f"\n   📅 {info.get('created_at')}"
    
    await event.reply(stats_text)

@bot.on(events.NewMessage(pattern='/mybots'))
async def mybots_handler(event):
    """Show user's cloned bots"""
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
    """Remove user's bots"""
    user_id = event.sender_id
    user_clones = [k for k, v in clone_stats.items() if v.get('owner_id') == user_id]
    
    if not user_clones:
        await event.reply("❌ You have no bots to remove!")
        return
    
    # Remove user's bots
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
    """Show clone instructions"""
    clone_text = """
🔧 **Clone This Bot**

**Create your own Whisper Bot!**

🤖 **Steps:**
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
    """Handle clone with token"""
    try:
        user_id = event.sender_id
        
        # Check join status
        if not await check_user_joined(user_id):
            await send_join_message(event)
            return
        
        token = event.pattern_match.group(1)
        
        # Check if user already has a cloned bot
        user_clones = [k for k, v in clone_stats.items() if v.get('owner_id') == user_id]
        if user_clones:
            await event.reply(
                "❌ **You already have a cloned bot!**\n\n"
                "Each user can only clone one bot.\n"
                "Please use another account to clone again.",
                buttons=[[Button.inline("🤖 My Bot", data="my_bot")]]
            )
            return
        
        # Validate token format
        if not re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
            await event.reply(
                "❌ **Invalid Token Format!**\n\n"
                "Please check your bot token.\n"
                "Format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`",
                buttons=[[Button.inline("🔄 Try Again", data="clone_info")]]
            )
            return
        
        # Check if token already used
        if token in clone_stats:
            await event.reply(
                "❌ **This bot is already cloned!**\n\n"
                "Please use a different bot token.",
                buttons=[[Button.inline("🔄 Try Again", data="clone_info")]]
            )
            return
        
        creating_msg = await event.reply("🔄 **Creating your bot...**")
        
        # Create user bot
        user_bot = TelegramClient(f'user_bot_{user_id}', API_ID, API_HASH)
        await user_bot.start(bot_token=token)
        
        bot_me = await user_bot.get_me()
        user_bots[token] = user_bot
        
        # Store clone info
        clone_stats[token] = {
            'owner_id': user_id,
            'username': bot_me.username,
            'first_name': getattr(bot_me, 'first_name', ''),
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'token_preview': token[:10] + '...'
        }
        save_data()
        
        # Setup basic handlers for cloned bot
        @user_bot.on(events.NewMessage(pattern='/start'))
        async def user_start(event):
            # Send animation
            try:
                await user_bot.send_file(
                    event.chat_id,
                    ANIMATION_URL,
                    caption="🚀 **Welcome to your Whisper Bot!**"
                )
                await asyncio.sleep(2)
            except:
                pass
            
            welcome_text = """
🤫 **Your Whisper Bot**

🔒 Send secret messages
🚀 Only recipient can read  
🎯 Easy inline mode

**Usage:** `message @username`
**Example:** `Hello! @username`

🔒 Your messages are secure!
            """
            await event.reply(
                welcome_text,
                buttons=[
                    [Button.url("📢 Support Channel", f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
                    [Button.url("👥 Support Group", f"https://t.me/{SUPPORT_GROUP[1:]}")],
                    [Button.switch_inline("🚀 Try Now", query="")]
                ]
            )
        
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
        
        @user_bot.on(events.CallbackQuery())
        async def user_callback(event):
            data = event.data.decode('utf-8')
            if data in messages_db:
                msg_data = messages_db[data]
                await event.answer(msg_data['text'], alert=True)
        
        # Notify admin
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🆕 **New Bot Cloned!**\n\n"
                f"🤖 Bot: @{bot_me.username}\n"
                f"👤 User: {user_id}\n"
                f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"🔢 Total: {len(clone_stats)}"
            )
        except:
            pass
        
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
    """Help command"""
    help_text = """
📖 **How to Use Whisper Bot**

**1. Inline Mode:**
   • Type `@{}` in any chat
   • Write your message
   • Add @username at end
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

@bot.on(events.InlineQuery())
async def inline_handler(event):
    """Handle inline queries"""
    try:
        if not event.text:
            result = event.builder.article(
                title="🤫 Whisper Bot",
                description="Send secret messages",
                text="**Usage:** `your_message @username`\n\n**Example:** `Hello! @username`\n\n🔒 Only they can read!"
            )
            await event.answer([result])
            return
        
        text = event.text.strip()
        target_match = re.search(r'@(\w+)$', text)
        
        if not target_match:
            result = event.builder.article(
                title="❌ Missing @username",
                description="Add @username at end",
                text="**Usage:** `your_message @username`\n\n**Example:** `Hello! @username`"
            )
            await event.answer([result])
            return
        
        target_user = target_match.group(1)
        message_text = text.replace(f'@{target_user}', '').strip()
        
        if not message_text:
            result = event.builder.article(
                title="❌ Empty Message",
                description="Write message before @username",
                text="**Usage:** `your_message @username`\n\n**Example:** `Hello! @username`"
            )
            await event.answer([result])
            return
        
        message_id = f'msg_{event.sender_id}_{target_user}_{int(datetime.now().timestamp())}'
        messages_db[message_id] = {
            'text': message_text,
            'target': target_user,
            'sender': event.sender_id
        }
        
        result = event.builder.article(
            title="🔒 Secret Message",
            description=f"For {target_user}",
            text=f"**🔐 Secret message for {target_user}!**\n\n*Only they can open it.*",
            buttons=[Button.inline("🔓 Show Message", message_id)]
        )
        
        await event.answer([result])
        
    except Exception as e:
        logger.error(f"Inline error: {e}")

@bot.on(events.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8')
    
    if data == "help":
        await event.edit(
            "📖 **Help Guide**\n\nUse inline mode: `message @username`",
            buttons=[[Button.inline("🔙 Back", data="back_start")]]
        )
    
    elif data == "clone_info":
        await event.edit(
            "🔧 Use /clone command with your bot token",
            buttons=[[Button.inline("🔙 Back", data="back_start")]]
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
    
    elif data == "admin_stats":
        if event.sender_id != ADMIN_ID:
            await event.answer("Admin only!", alert=True)
            return
            
        total_clones = len(clone_stats)
        await event.edit(f"📊 Total Clones: {total_clones}")
    
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
        
        clone_list = "📋 **Clone List:**\n\n"
        for i, (token, info) in enumerate(list(clone_stats.items())[-10:], 1):
            clone_list += f"{i}. @{info['username']}\n"
            clone_list += f"   👤 User: {info['owner_id']}\n"
            clone_list += f"   📅 {info['created_at']}\n\n"
        
        await event.edit(clone_list[:4000])
    
    elif data == "check_join":
        if await check_user_joined(event.sender_id):
            await event.answer("✅ You have joined both!", alert=True)
            await event.edit(
                "✅ **Join Verified!**\n\nNow send /start to use the bot.",
                buttons=[[Button.inline("🚀 Start", data="back_start")]]
            )
        else:
            await event.answer("❌ Please join both channels!", alert=True)
    
    elif data == "back_start":
        user_id = event.sender_id
        
        if not await check_user_joined(user_id):
            await send_join_message(event)
            return
        
        if user_id == ADMIN_ID:
            await event.edit(
                "👑 **Admin Panel**",
                buttons=[
                    [Button.inline("📊 Stats", data="admin_stats")],
                    [Button.inline("👥 Manage", data="admin_manage")],
                    [Button.inline("📋 Clone List", data="clone_list")],
                    [Button.switch_inline("🚀 Try", query="")]
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
        await event.answer(msg_data['text'], alert=True)

async def main():
    me = await bot.get_me()
    logger.info(f"🎭 ShriBots Whisper Bot Started!")
    logger.info(f"🤖 Bot: @{me.username}")
    logger.info(f"👑 Admin: {ADMIN_ID}")
    logger.info(f"📊 Clones: {len(clone_stats)}")
    logger.info("🚀 Bot is ready!")

if __name__ == '__main__':
    bot.loop.run_until_complete(main())
    bot.run_until_disconnected()
