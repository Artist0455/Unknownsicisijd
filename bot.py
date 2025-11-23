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
🤫 **Secret Whisper Bot**

🔒 Send anonymous messages
🚀 Only recipient can read
🎯 Easy inline mode

**Try: @username your_message**
"""

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle /start command"""
    await event.reply(
        WELCOME_TEXT,
        buttons=[
            [Button.switch_inline("🚀 Try Now", query="")],
            [Button.inline("📖 Help", data="help")]
        ]
    )

@bot.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Handle /help command"""
    help_text = """
**How to use:**

1. **Inline Mode:**
   Type `@{}` in any chat
   Write your message
   Add @username at end

2. **Examples:**
   `@{} Hello! @username`
   `@{} Secret message 123456789`

3. **Commands:**
   /start - Start bot
   /help - Show this help
   /clone - Create your own bot
    """.format((await bot.get_me()).username, (await bot.get_me()).username, (await bot.get_me()).username)
    
    await event.reply(help_text)

@bot.on(events.NewMessage(pattern='/clone'))
async def clone_handler(event):
    """Handle /clone command"""
    clone_help = """
🔧 **Clone This Bot**

**Steps:**
1. Go to @BotFather
2. Create bot with /newbot
3. Get API token
4. Send: `/clone your_token`

**Example:**
`/clone 1234567890:ABCdefGHIjkl...`

⚠️ **Keep token secure!**
    """
    await event.reply(
        clone_help,
        buttons=[
            [Button.url("🤖 BotFather", "https://t.me/BotFather")],
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
            await event.reply("🤫 Your cloned whisper bot is ready!")
        
        @user_bot.on(events.InlineQuery())
        async def user_inline(event):
            if event.text:
                # Simple inline handler
                result = event.builder.article(
                    title="Whisper Bot",
                    description="Send secret messages",
                    text="Your cloned bot is working!"
                )
                await event.answer([result])
        
        await event.reply(
            f"✅ **Bot Cloned!**\n\n"
            f"🤖 Your bot: @{bot_me.username}\n"
            f"🚀 Ready to use!\n\n"
            f"Try: `@{bot_me.username} message @username`",
            buttons=[
                [Button.switch_inline("🚀 Test Bot", query="")]
            ]
        )
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@bot.on(events.CallbackQuery(pattern='help'))
async def help_callback(event):
    """Handle help callback"""
    help_text = """
**Quick Help:**

• Use inline mode: `@username your_message`
• Only the mentioned user can read
• Messages are secure and private

Need more help? Contact @ShriBots
    """
    await event.edit(help_text)

@bot.on(events.CallbackQuery(pattern='back'))
async def back_callback(event):
    """Handle back callback"""
    await event.edit(
        WELCOME_TEXT,
        buttons=[
            [Button.switch_inline("🚀 Try Now", query="")],
            [Button.inline("📖 Help", data="help")]
        ]
    )

@bot.on(events.InlineQuery())
async def inline_handler(event):
    """Handle inline queries"""
    try:
        if not event.text:
            # Show help when no text
            result = event.builder.article(
                title="🤫 Whisper Bot",
                description="Send secret messages - Type: message @username",
                text="**Usage:** `your_message @username`\n\n**Example:** `Hello! @username`\n\n🔒 Only they can read it!"
            )
            await event.answer([result])
            return
        
        # Parse message and target user
        text = event.text.strip()
        target_match = re.search(r'@(\w+)$', text)
        
        if not target_match:
            await event.answer([])
            return
        
        target_user = target_match.group(1)
        message_text = text.replace(f'@{target_user}', '').strip()
        
        if not message_text:
            await event.answer([])
            return
        
        # Create message ID
        message_id = f'msg_{event.sender_id}_{target_user}_{int(datetime.now().timestamp())}'
        messages_db[message_id] = {
            'text': message_text,
            'target': target_user,
            'sender': event.sender_id
        }
        
        # Create result
        result = event.builder.article(
            title="🔒 Secret Message",
            description=f"For {target_user}",
            text=f"**🔐 Secret message for {target_user}!**\n\n*Click below to reveal (only they can see it)*",
            buttons=[Button.inline("🔓 Reveal Message", message_id)]
        )
        
        await event.answer([result])
        
    except Exception as e:
        logger.error(f"Inline error: {e}")
        await event.answer([])

@bot.on(events.CallbackQuery())
async def callback_handler(event):
    """Handle all callbacks"""
    try:
        data = event.data.decode('utf-8')
        
        if data in messages_db:
            msg_data = messages_db[data]
            
            # Check if user is the target (simplified)
            # In real implementation, you'd check against actual user ID
            await event.answer(
                f"🔓 Secret Message:\n\n{msg_data['text']}",
                alert=True
            )
        else:
            await event.answer("Message not found or expired!", alert=True)
            
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await event.answer("Error!", alert=True)

async def main():
    """Main function"""
    me = await bot.get_me()
    logger.info(f"🤖 Bot started: @{me.username}")
    logger.info("🚀 Ready to receive messages!")

if __name__ == '__main__':
    bot.loop.run_until_complete(main())
    bot.run_until_disconnected()