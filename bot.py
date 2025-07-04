import logging
import requests
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import aiohttp
import time
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

CHANNEL_USERNAME = "@reelsaver"
CHANNEL_LINK = "https://t.me/reelsaver"
BOT_TOKEN = "7574513701:AAEIzqK-C-oPjY5hj7dwr1KCbsOa_P6h5cU"
API_BASE_URL = "http://142.93.120.151:8000/"

welcomed_users = {}

async def start(update, context):
    user_id = update.message.from_user.id
    first_name = update.message.from_user.first_name

    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)

        if chat_member.status in ['left', 'kicked']:
            keyboard = [[InlineKeyboardButton("Join Here", url=CHANNEL_LINK)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Hello {first_name},\n\n"
                "You need to join @reelsaver to use this bot. Please join and try again. 😇",
                reply_markup=reply_markup
            )
        else:
            if user_id not in welcomed_users:
                await update.message.reply_text(
                    f"Hello {first_name},\n\n"
                    "Thank you for joining the channel!\n\n"
                    "Now You're Ready To Use The Bot.\n\n"
                    "Just send a valid Instagram, Facebook, YouTube, TikTok, or Twitter reel link and I'll get to work! 😊.\n\n"
                    "Happy Detecting! 🕵️‍♂️"
                )
                welcomed_users[user_id] = True
            else:
                await update.message.reply_text(
                    f"Hello {first_name},\n\n"
                    "📥 Send any Instagram, Facebook, YouTube, TikTok, or Twitter reel link to download it fast and free—no watermark! 😊"
                )
    except Exception as e:
        await update.message.reply_text("There was an error checking your membership. Please try again later.")

async def handle_reel_link(update, context):
    if re.match(r"(https?://(www\.)?(instagram|facebook|youtube|tiktok|twitter|x)\.com/[^\s]+)", update.message.text):
        user_id = update.message.from_user.id
        try:
            chat_member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)

            if chat_member.status in ['left', 'kicked']:
                keyboard = [[InlineKeyboardButton("Join Here", url=CHANNEL_LINK)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "You need to join @reelsaver to use this bot. Please join and try again. 😇",
                    reply_markup=reply_markup
                )
                return

            url = update.message.text.strip()
            source = None
            if re.match(r"(https?://(www\.)?instagram\.com/[^\s]+)", url):
                source = "instagram"
            elif re.match(r"(https?://(www\.)?facebook\.com/[^\s]+)", url):
                source = "fb"
            elif re.match(r"(https?://(www\.)?(youtube\.com|youtu\.be)/(watch\?v=|shorts/|[^\s]+))", url):
                source = "youtube"
            elif re.match(r"(https?://(www\.)?tiktok\.com/[^\s]+)", url):
                source = "tiktok"
            elif re.match(r"(https?://(www\.)?x\.com/[^\s]+)", url):
                source = "twitter"

            if source:
                waiting_msg = await update.message.reply_text("Processing your request, please wait.... ⏳")
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
                api_url = f"{API_BASE_URL}?source={source}&url={url}"

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(api_url) as response:
                            if response.status == 200:
                                video_info = await response.json()
                                video_url = video_info['videoUrl']
                                description = video_info.get('description', "No description available.")

                                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_VIDEO)
                                await update.message.reply_video(
                                    video_url, caption=description
                                )
                                await waiting_msg.delete()
                            else:
                                await update.message.reply_text("Request failed. ❌ Make sure the account is public or try again.")
                                await waiting_msg.delete()

                except Exception as e:
                    #logger.error(f"Error calling API: {e}")
                    await update.message.reply_text(f"Sorry, I couldn't fetch the video. Please try again later.")
                    await waiting_msg.delete()
            else:
                await update.message.reply_text("Please send a valid Instagram, Facebook, YouTube, TikTok, or Twitter reel link to download it fast and free—no watermark! 😊")
        except Exception as e:
            await update.message.reply_text("There was an error checking your membership. Please try again later.")


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reel_link))
    application.run_polling()


if __name__ == '__main__':
    main()

