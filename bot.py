from telethon import TelegramClient, events, Button
from flask import Flask
import logging
import os
import re
import asyncio
import json
from datetime import datetime
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
API_ID = int(os.getenv('API_ID', '25136703'))
API_HASH = os.getenv('API_HASH', 'accfaf5ecd981c67e481328515c39f89'))
BOT_TOKEN = os.getenv('BOT_TOKEN', '8521103806:AAHHQ2XL_EokOXmJCdElfkkSrnYAkr0IVB4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '8272213732'))

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "🎭 ShriBots Whisper Bot is Running!"

@app.route('/health')
def health():
    return {'status': 'healthy', 'bot': 'running'}

# Global variables
messages_db = {}
user_bots = {}
clone_stats = {}
broadcast_users = set()

# Data files
CLONE_FILE = "clone_stats.json"
BROADCAST_FILE = "broadcast_users.json"

def load_data():
    global clone_stats, broadcast_users
    try:
        if os.path.exists(CLONE_FILE):
            with open(CLONE_FILE, 'r') as f:
                clone_stats = json.load(f)
        
        if os.path.exists(BROADCAST_FILE):
            with open(BROADCAST_FILE, 'r') as f:
                broadcast_users = set(json.load(f))
    except Exception as e:
        logger.error(f"Error loading data: {e}")

def save_data():
    try:
        with open(CLONE_FILE, 'w') as f:
            json.dump(clone_stats, f, indent=2)
        
        with open(BROADCAST_FILE, 'w') as f:
            json.dump(list(broadcast_users), f)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

load_data()

# Initialize bot
def initialize_bot():
    try:
        bot = TelegramClient('whisper_bot', API_ID, API_HASH)
        bot.start(bot_token=BOT_TOKEN)
        logger.info("✅ Bot initialized successfully")
        return bot
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")
        return None

bot = initialize_bot()

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

ANIMATION_URL = "https://files.catbox.moe/395dct.mp4"

def setup_bot_handlers(bot_instance):
    
    async def send_animation(event):
        """Send animation if user is not admin"""
        if event.sender_id != ADMIN_ID:
            try:
                await bot_instance.send_file(
                    event.chat_id,
                    ANIMATION_URL,
                    caption="🚀 **Starting your whisper experience...**"
                )
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Animation error: {e}")

    @bot_instance.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        try:
            # Send animation for non-admin users
            if event.sender_id != ADMIN_ID:
                await send_animation(event)
            
            if event.sender_id == ADMIN_ID:
                # Admin panel
                await event.reply(
                    "👑 **Admin Panel**\n\n"
                    "📊 View bot statistics\n"
                    "👥 Manage cloned bots\n"
                    "📢 Send broadcast\n"
                    "🚀 Bot controls",
                    buttons=[
                        [Button.inline("📊 Statistics", data="admin_stats")],
                        [Button.inline("👥 Manage Bots", data="admin_bots")],
                        [Button.inline("📢 Broadcast", data="admin_broadcast")],
                        [Button.switch_inline("🚀 Try Inline", query="")]
                    ]
                )
            else:
                # Normal user
                await event.reply(
                    WELCOME_TEXT,
                    buttons=[
                        [Button.url("📢 Channel", "https://t.me/shribots")],
                        [Button.switch_inline("🚀 Try Now", query="")],
                        [Button.inline("📖 Help", data="help"), 
                         Button.inline("🔧 Clone", data="clone_info")]
                    ]
                )
                
        except Exception as e:
            logger.error(f"Start error: {e}")

    @bot_instance.on(events.NewMessage(pattern='/stats'))
    async def stats_handler(event):
        """Stats command for admin"""
        if event.sender_id != ADMIN_ID:
            await event.reply("❌ Admin only command!")
            return
            
        total_clones = len(clone_stats)
        active_bots = len(user_bots)
        total_users = len(broadcast_users)
        
        stats_text = f"""
📊 **Admin Statistics**

🤖 Total Clones: {total_clones}
⚡ Active Bots: {active_bots}
👥 Total Users: {total_users}

**Recent Clones:**
"""
        recent_clones = list(clone_stats.items())[-5:]
        for i, (token, info) in enumerate(recent_clones, 1):
            stats_text += f"\n{i}. @{info.get('username', 'Unknown')}"
            stats_text += f"\n   👤 User: {info.get('owner_id')}"
            stats_text += f"\n   📅 {info.get('created_at')}"
        
        await event.reply(
            stats_text,
            buttons=[
                [Button.inline("🔄 Refresh", data="admin_stats")],
                [Button.inline("🗑 Clean Bots", data="clean_bots")]
            ]
        )

    @bot_instance.on(events.NewMessage(pattern='/broadcast'))
    async def broadcast_handler(event):
        """Broadcast command for admin"""
        if event.sender_id != ADMIN_ID:
            await event.reply("❌ Admin only command!")
            return
            
        if not event.text.strip().startswith('/broadcast '):
            await event.reply(
                "📢 **Broadcast Message**\n\n"
                "Usage: `/broadcast your_message_here`\n\n"
                "Example: `/broadcast Hello everyone! New update available.`"
            )
            return
            
        message = event.text.split(' ', 1)[1]
        await event.reply(f"🔄 Broadcasting to {len(broadcast_users)} users...")
        
        success = 0
        failed = 0
        
        for user_id in list(broadcast_users):
            try:
                await bot_instance.send_message(user_id, f"📢 **Announcement:**\n\n{message}")
                success += 1
                await asyncio.sleep(0.1)  # Rate limit
            except Exception as e:
                failed += 1
                logger.error(f"Broadcast failed for {user_id}: {e}")
        
        await event.reply(
            f"✅ **Broadcast Complete!**\n\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}\n"
            f"👥 Total: {len(broadcast_users)}"
        )

    @bot_instance.on(events.NewMessage(pattern='/removebot'))
    async def remove_bot_handler(event):
        """Remove specific bot for admin"""
        if event.sender_id != ADMIN_ID:
            await event.reply("❌ Admin only command!")
            return
            
        if not event.text.strip().startswith('/removebot '):
            await event.reply(
                "🗑 **Remove Bot**\n\n"
                "Usage: `/removebot bot_token`\n\n"
                "Example: `/removebot 1234567890:ABCdef...`"
            )
            return
            
        token = event.text.split(' ', 1)[1]
        
        if token in user_bots:
            try:
                await user_bots[token].disconnect()
                del user_bots[token]
            except:
                pass
        
        if token in clone_stats:
            del clone_stats[token]
            save_data()
            await event.reply("✅ Bot removed successfully!")
        else:
            await event.reply("❌ Bot not found!")

    @bot_instance.on(events.NewMessage(pattern='/help'))
    async def help_handler(event):
        help_text = """
🤖 **How to Use Whisper Bot:**

**1. Inline Mode:**
   • Type `@{}` in any chat
   • Write your message
   • Add @username at end
   • Send!

**2. Examples:**
   • `@{} Hello! @username`
   • `@{} Secret message 123456789`

**3. Commands:**
   • /start - Start bot
   • /help - Show help
   • /clone - Create your bot

🔒 **Only the mentioned user can read your message!**
        """.format((await bot_instance.get_me()).username, 
                  (await bot_instance.get_me()).username,
                  (await bot_instance.get_me()).username)
        
        await event.reply(
            help_text,
            buttons=[
                [Button.switch_inline("🚀 Try Now", query="")],
                [Button.inline("🔧 Clone Bot", data="clone_info")]
            ]
        )

    @bot_instance.on(events.NewMessage(pattern=r'/clone\s+(\S+)'))
    async def clone_token_handler(event):
        """Handle clone with token"""
        try:
            user_id = event.sender_id
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
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'token_preview': token[:10] + '...'
            }
            save_data()
            
            # Add to broadcast list
            broadcast_users.add(user_id)
            save_data()
            
            # Setup basic handlers for cloned bot (ONLY WHISPER)
            @user_bot.on(events.NewMessage(pattern='/start'))
            async def user_start(event):
                welcome_text = """
🤫 **Whisper Bot**

🔒 Send secret messages
🚀 Only recipient can read
🎯 Easy inline mode

**Usage:** `message @username`
**Example:** `Hello! @username`

🔒 Your messages are secure!
                """
                await event.reply(welcome_text)
            
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
                    if event.sender_id in [msg_data['sender'], msg_data.get('target_id', '')]:
                        await event.answer(msg_data['text'], alert=True)
                    else:
                        await event.answer("Not for you!", alert=True)
            
            # Notify admin
            try:
                await bot_instance.send_message(
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
                f"🎉 Ready to use!\n\n"
                f"**Try it now:**\n"
                f"`@{bot_me.username} message @username`",
                buttons=[
                    [Button.switch_inline("🚀 Test Bot", query="", same_peer=True)],
                    [Button.url("📢 Support", "https://t.me/shribots")]
                ]
            )
            
        except Exception as e:
            logger.error(f"Clone error: {e}")
            await event.reply(f"❌ **Clone Failed!**\n\nError: {str(e)}")

    @bot_instance.on(events.NewMessage(pattern='/clone'))
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

    @bot_instance.on(events.InlineQuery())
    async def inline_handler(event):
        """Handle inline queries"""
        try:
            # Add user to broadcast list
            broadcast_users.add(event.sender_id)
            save_data()
            
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

    @bot_instance.on(events.CallbackQuery())
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
        
        elif data == "my_bot":
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
        
        elif data == "admin_stats":
            if event.sender_id != ADMIN_ID:
                await event.answer("Admin only!", alert=True)
                return
                
            total_clones = len(clone_stats)
            await event.edit(f"📊 Total Clones: {total_clones}")
        
        elif data == "admin_bots":
            if event.sender_id != ADMIN_ID:
                await event.answer("Admin only!", alert=True)
                return
                
            bot_list = "🤖 **Cloned Bots:**\n\n"
            for i, (token, info) in enumerate(list(clone_stats.items())[-10:], 1):
                bot_list += f"{i}. @{info['username']}\n"
                bot_list += f"   👤 {info['owner_id']}\n"
                bot_list += f"   🗑 `/removebot {token}`\n\n"
            
            await event.edit(bot_list[:4000])
        
        elif data == "admin_broadcast":
            if event.sender_id != ADMIN_ID:
                await event.answer("Admin only!", alert=True)
                return
                
            await event.edit(
                f"📢 **Broadcast**\n\nUsers: {len(broadcast_users)}\n\n"
                "Use: `/broadcast your_message`",
                buttons=[[Button.inline("🔙 Back", data="back_start")]]
            )
        
        elif data == "clean_bots":
            if event.sender_id != ADMIN_ID:
                await event.answer("Admin only!", alert=True)
                return
                
            # Clean inactive bots
            cleaned = 0
            for token in list(user_bots.keys()):
                if token not in clone_stats:
                    try:
                        await user_bots[token].disconnect()
                        del user_bots[token]
                        cleaned += 1
                    except:
                        pass
            
            await event.answer(f"🧹 Cleaned {cleaned} bots", alert=True)
            await event.edit(f"✅ Cleaned {cleaned} inactive bots")
        
        elif data == "back_start":
            if event.sender_id == ADMIN_ID:
                await event.edit(
                    "👑 **Admin Panel**",
                    buttons=[
                        [Button.inline("📊 Stats", data="admin_stats")],
                        [Button.inline("👥 Bots", data="admin_bots")],
                        [Button.inline("📢 Broadcast", data="admin_broadcast")],
                        [Button.switch_inline("🚀 Try", query="")]
                    ]
                )
            else:
                await event.edit(
                    WELCOME_TEXT,
                    buttons=[
                        [Button.url("📢 Channel", "https://t.me/shribots")],
                        [Button.switch_inline("🚀 Try", query="")],
                        [Button.inline("📖 Help", data="help"), 
                         Button.inline("🔧 Clone", data="clone_info")]
                    ]
                )
        
        elif data in messages_db:
            msg_data = messages_db[data]
            await event.answer(msg_data['text'], alert=True)

def run_bot():
    """Run the Telegram bot"""
    if bot:
        try:
            # Setup handlers
            setup_bot_handlers(bot)
            
            async def main():
                me = await bot.get_me()
                logger.info(f"🎭 ShriBots Whisper Bot Started!")
                logger.info(f"🤖 Bot: @{me.username}")
                logger.info(f"👑 Admin: {ADMIN_ID}")
                logger.info(f"📊 Clones: {len(clone_stats)}")
                logger.info(f"👥 Users: {len(broadcast_users)}")
            
            bot.loop.run_until_complete(main())
            bot.run_until_disconnected()
        except Exception as e:
            logger.error(f"Bot error: {e}")

def start_services():
    """Start both web server and bot"""
    # Start bot in background thread
    if bot:
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("🤖 Bot started in background")
    
    # Start Flask app
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    start_services()