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
BOT_TOKEN = os.getenv('BOT_TOKEN', '8521103806:AAHHQ2XL_EokOXmJCdElfkkSrnYAkr0IVB4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '8272213732'))

# Initialize bot
bot = TelegramClient('whisper_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Storage
messages_db = {}
user_bots = {}

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

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle /start command"""
    await event.reply(
        WELCOME_TEXT,
        buttons=[
            [Button.switch_inline("🚀 Try Now", query="")],
            [Button.inline("📖 Help", data="help")],
            [Button.inline("🔧 Clone Bot", data="clone_info")]
        ]
    )

@bot.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Handle /help command"""
    help_text = """
╔══════════════════════╗
║     📖 𝗛𝗘𝗟𝗣 𝗠𝗘𝗡𝗨     ║
╚══════════════════════╝

**How to use:**

🤖 **Inline Mode:**
• Type `@{}` in any chat
• Write your message  
• Add @username at end
• Send!

📝 **Examples:**
• `@{} Hello! @username`
• `@{} Secret message 123456789`

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
    """.format((await bot.get_me()).username, (await bot.get_me()).username, (await bot.get_me()).username)
    
    await event.reply(
        help_text,
        buttons=[
            [Button.switch_inline("🚀 Try Now", query="")],
            [Button.url("📢 Support", "https://t.me/shribots")]
        ]
    )

@bot.on(events.NewMessage(pattern='/clone'))
async def clone_handler(event):
    """Handle /clone command"""
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

@bot.on(events.NewMessage(pattern=r'/clone\s+(\d+:[A-Za-z0-9_-]+)'))
async def clone_token_handler(event):
    """Handle clone with token"""
    try:
        token = event.pattern_match.group(1)
        await event.reply("🔄 Creating your bot...")
        
        # Create user bot
        user_bot = TelegramClient(f'user_bot_{event.sender_id}', API_ID, API_HASH)
        await user_bot.start(bot_token=token)
        
        bot_me = await user_bot.get_me()
        user_bots[token] = user_bot
        
        # Setup basic handlers
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
                await event.answer([result], switch_pm="How to use", switch_pm_param="start")
                return
            
            await handle_inline_query(event, user_bot)
        
        await event.reply(
            f"✅ **Bot Cloned Successfully!**\n\n"
            f"🤖 **Your Bot:** @{bot_me.username}\n"
            f"🎉 Now active with all features!\n\n"
            f"**Try your bot:**\n"
            f"• /start - Start bot\n"
            f"• Inline: `@{bot_me.username} message @username`",
            buttons=[
                [Button.switch_inline("🚀 Test Your Bot", query="", same_peer=True)],
                [Button.url("📢 Support", "https://t.me/shribots")]
            ]
        )
        
    except Exception as e:
        await event.reply(f"❌ **Clone Failed!**\n\nError: {str(e)}")

async def handle_inline_query(event, client=None):
    """Handle inline queries with proper error handling"""
    try:
        if client is None:
            client = bot
        
        text = event.text.strip()
        
        # Parse message and target user
        target_match = re.search(r'@(\w+)$', text)
        if not target_match:
            # No target user found, show help
            result = event.builder.article(
                title="❌ Missing Username",
                description="Add @username at the end",
                text="**Usage:** `your_message @username`\n\n**Example:** `Hello! @username`\n\n🔒 Only they can read your message!"
            )
            await event.answer([result], switch_pm="How to use", switch_pm_param="start")
            return
        
        target_user = target_match.group(1)
        message_text = text.replace(f'@{target_user}', '').strip()
        
        if not message_text:
            result = event.builder.article(
                title="❌ Empty Message",
                description="Write a message before @username",
                text="**Usage:** `your_message @username`\n\n**Example:** `Hello! @username`"
            )
            await event.answer([result], switch_pm="How to use", switch_pm_param="start")
            return
        
        # Validate username format
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{3,30}$', target_user):
            result = event.builder.article(
                title="❌ Invalid Username",
                description="Username format is invalid",
                text="**Valid username format:**\n• Starts with letter\n• 4-31 characters\n• Letters, numbers, underscores only"
            )
            await event.answer([result])
            return
        
        try:
            # Try to get user entity
            user_entity = await client.get_entity(target_user)
            display_name = getattr(user_entity, 'first_name', f'@{target_user}')
        except Exception as e:
            logger.warning(f"Could not resolve user @{target_user}: {e}")
            display_name = f'@{target_user}'
        
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
            description=f"For {display_name}",
            text=f"**🔐 A secret message for {display_name}!**\n\n*Note: Only {display_name} can open this message.*",
            buttons=[Button.inline("🔓 Show Message", message_id)]
        )
        
        await event.answer([result])
        
    except Exception as e:
        logger.error(f"Inline query error: {e}")
        result = event.builder.article(
            title="❌ Error",
            description="Something went wrong",
            text="❌ An error occurred. Please try again."
        )
        await event.answer([result])

@bot.on(events.InlineQuery())
async def inline_handler(event):
    """Handle inline queries"""
    await handle_inline_query(event)

@bot.on(events.CallbackQuery(pattern='help'))
async def help_callback(event):
    """Handle help callback"""
    help_text = """
╔══════════════════════╗
║     📖 𝗤𝗨𝗜𝗖𝗞 𝗛𝗘𝗟𝗣     ║
╚══════════════════════╝

**Quick Guide:**

🎯 **How to send whispers:**
1. Type `@{}` in any chat
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
    """.format((await bot.get_me()).username)
    
    await event.edit(
        help_text,
        buttons=[
            [Button.switch_inline("🚀 Try Now", query="")],
            [Button.inline("🔙 Back", data="back")]
        ]
    )

@bot.on(events.CallbackQuery(pattern='clone_info'))
async def clone_info_callback(event):
    """Handle clone info callback"""
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

@bot.on(events.CallbackQuery(pattern='back'))
async def back_callback(event):
    """Handle back callback"""
    await event.edit(
        WELCOME_TEXT,
        buttons=[
            [Button.switch_inline("🚀 Try Now", query="")],
            [Button.inline("📖 Help", data="help")],
            [Button.inline("🔧 Clone Bot", data="clone_info")]
        ]
    )

@bot.on(events.CallbackQuery())
async def callback_handler(event):
    """Handle all callbacks"""
    try:
        data = event.data.decode('utf-8')
        
        if data in messages_db:
            msg_data = messages_db[data]
            
            # Show the secret message
            await event.answer(
                f"🔓 **Secret Message:**\n\n{msg_data['text']}",
                alert=True
            )
        else:
            await event.answer("❌ Message not found or expired!", alert=True)
            
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await event.answer("❌ Error showing message!", alert=True)

async def main():
    """Main function"""
    me = await bot.get_me()
    logger.info(f"🎭 ShriBots Whisper Bot Started!")
    logger.info(f"🤖 Bot: @{me.username}")
    logger.info("🚀 Ready to receive messages!")

if __name__ == '__main__':
    bot.loop.run_until_complete(main())
    bot.run_until_disconnected()